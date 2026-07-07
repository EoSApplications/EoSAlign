from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QPushButton,
    QWidget, QSizePolicy, QApplication, QScrollArea, QFrame, QHBoxLayout, 
)
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings
from EoS_Math.Build_Dataframe import Calibration_Metadata
from Loading_Message import Get_Resource_Path
from MenuBar import MainMenuBar
from Banner import Banner
from Collapsible_Sections import Collapsible_Content_Container
from Plot_Study_Selection_Panel import Plot_Study_Selection_Panel
from Plots.Plot_Widgets import PNG_Display_Widget, PNG_Frame_Widget
from Plots.Generate_Figures import (
    Export_Background_Options, Export_Theme_Options, Figure_Titles,
    Pressure_Only_Modules, Ui_Module_Order, Cancel_Generation,
    Get_Current_Generation_Preferences, Get_Export_Variant_Key,
    Get_Export_Variant_Path, Get_Generation_Progress, Read_Generation_Signature,
    Start_Export_Variant_Generation, Start_Figure_Generation,
    Write_Generation_Signature,
)


Module_To_Basename = {
    "Plot_Observable_Vs_Pressure":                            "observable_vs_pressure",
    "Plot_All_EoS_Overlay_Absolute_Pressure_Difference":      "all_eos_overlay_absolute_pressure_difference",
    "Plot_All_EoS_Overlay_Percent_Pressure_Difference":       "all_eos_overlay_percent_pressure_difference",
    "Plot_Pressure_Scale_Disagreement":                       "pressure_scale_disagreement",
    "Plot_Individual_Absolute_Pressure_Difference":           "individual_absolute_pressure_difference",
    "Plot_Individual_Percent_Pressure_Difference":            "individual_percent_pressure_difference",
    "Plot_Summary_Observable_Vs_Pressure_And_Overlay":        "summary_observable_vs_pressure_and_overlay",
}
Basename_To_Module = {basename: module for module, basename in Module_To_Basename.items()}

Individual_Modules = {
    "Plot_Individual_Absolute_Pressure_Difference",
    "Plot_Individual_Percent_Pressure_Difference",
}
Regeneration_Debounce_Milliseconds = 500


class Plot_Window(QMainWindow):

    def __init__(self, Dataframe, Composition, Method, Input_Mode,
                 Pressure_Calibration_Study, parent=None,
                 Selected_Studies=None, Figures_Dir=None, Run_Label=None, Display_Run_Label=None):
        super().__init__(parent)
        self.Run_Label = Run_Label or ""
        self.Display_Run_Label = self.Run_Label if Display_Run_Label is None else Display_Run_Label
        window_title = "EoSAlign - Plots"
        if self.Display_Run_Label:
            window_title = f"{window_title} - {self.Display_Run_Label}"
        self.setWindowTitle(window_title)
        self.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoSAlign_With_Sun.png")))
        # Set palette background so Windows uses the theme color during maximize/restore.
        from Themes.Theme import Get_Theme
        from PySide6.QtGui import QPalette, QColor
        _, _, Colors = Get_Theme()
        Background_Color = Colors.get('Primary_Background', '#ffffff')
        Palette = self.palette()
        Palette.setColor(QPalette.Window, QColor(Background_Color))
        self.setPalette(Palette)

        self.Dataframe        = Dataframe
        self.Input_Mode       = Input_Mode
        self.Selected_Studies = Selected_Studies or []
        self.Figures_Dir      = Path(Figures_Dir) if Figures_Dir else None

        # Purge all persisted per-study style overrides at session start so every plot
        # window always opens with clean auto-assigned colors/markers, never stale ones.
        _Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        for _Key in Calibration_Metadata:
            _Settings_Store.remove(f"{_Key}_Color")
            _Settings_Store.remove(f"{_Key}_Marker")
            _Settings_Store.remove(f"{_Key}_Style_Is_User_Set")
        _Settings_Store.sync()

        # Unpack calibration-study dict. The "reference" / pressure-calibration-study key
        # depends on the workflow, same as Select_Final_Actions.Start_Figure_Generation:
        #   - same composition/method: the single study selected ("Selected Pressure
        #     Calibration Study")
        #   - different composition/method: the LAST study in the conversion chain (the
        #     Target study) — NOT the originally selected study, and NOT the bridge study
        #     ("Different Pressure Calibration Study").
        if isinstance(Pressure_Calibration_Study, dict):
            self.Workflow_Type       = Pressure_Calibration_Study.get("Workflow Type")
            self.Target_Composition  = Pressure_Calibration_Study.get("Different Composition")
            self.Target_Method       = Pressure_Calibration_Study.get("Different Method")
            self.Original_Study_Key  = Pressure_Calibration_Study.get("Selected Pressure Calibration Study")
            if self.Workflow_Type == "Use a Pressure Calibration Study with a Different Composition and Method":
                self.Reference_Study_Key = Pressure_Calibration_Study.get("Target Pressure Calibration Study")
                self.Target_Study_Key    = Pressure_Calibration_Study.get("Target Pressure Calibration Study")
            else:
                self.Reference_Study_Key = Pressure_Calibration_Study.get("Selected Pressure Calibration Study")
                self.Target_Study_Key    = None
        else:
            self.Workflow_Type       = None
            self.Reference_Study_Key = None
            self.Target_Study_Key    = None
            self.Target_Composition  = None
            self.Target_Method       = None
            self.Original_Study_Key  = None

        if (self.Workflow_Type == "Use a Pressure Calibration Study with a Different Composition and Method"
                and self.Target_Composition):
            self.Plot_Composition = self.Target_Composition
            self.Plot_Method      = self.Target_Method
        else:
            self.Plot_Composition = Composition
            self.Plot_Method      = Method

        # ── Active module list (UI order, pressure-only filtered) ─────────────
        self.Active_Modules = [
            m for m in Ui_Module_Order
            if not (m in Pressure_Only_Modules and self.Input_Mode != "Pressure (GPa)")
        ]

        # ── Outer shell ───────────────────────────────────────────────────────
        Central_Widget = QWidget()
        self.setCentralWidget(Central_Widget)
        Outer_Layout = QVBoxLayout(Central_Widget)
        Outer_Layout.setContentsMargins(0, 0, 0, 0)
        Outer_Layout.setSpacing(0)

        self.Menu_Bar = MainMenuBar(self)
        self.Menu_Bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        Outer_Layout.addWidget(self.Menu_Bar)

        self.Banner = Banner("", Get_Resource_Path("Graphics/EoSAlign_With_Sun.png"))
        Outer_Layout.addWidget(self.Banner)

        Export_Bar = QWidget()
        Export_Bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        Export_Bar_Layout = QHBoxLayout(Export_Bar)
        Export_Bar_Layout.setContentsMargins(10, 4, 10, 4)
        Export_Bar_Layout.addStretch()
        Export_Button = QPushButton("Export Figures")
        Export_Button.setObjectName("Primary_Button")
        Export_Button.setFixedHeight(32)
        Export_Button.clicked.connect(self.Open_Export_Dialog)
        Export_Bar_Layout.addWidget(Export_Button)
        Export_Bar_Layout.addStretch()
        Outer_Layout.addWidget(Export_Bar)

        Scroll_Area = QScrollArea()
        Scroll_Area.setWidgetResizable(True)
        Scroll_Area.setFrameShape(QFrame.NoFrame)
        Scroll_Content = QWidget()
        Scroll_Content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.Main_Layout = QVBoxLayout(Scroll_Content)
        self.Main_Layout.setContentsMargins(10, 10, 10, 10)
        self.Main_Layout.setSpacing(8)
        self.Main_Layout.setAlignment(Qt.AlignTop)
        Scroll_Area.setWidget(Scroll_Content)
        Outer_Layout.addWidget(Scroll_Area, stretch=1)

        # ── Study selection panel (starts collapsed) ──────────────────────────
        self.Study_Panel = Plot_Study_Selection_Panel(
            Selected_Studies=self.Selected_Studies,
            Reference_Study_Key=self.Reference_Study_Key,
        )
        Study_Panel_Section = Collapsible_Content_Container(
            "Study Selection", self.Study_Panel,
            Initially_Show_Container=False,
            Expanding_Content=True,
        )
        self.Main_Layout.addWidget(Study_Panel_Section)

        # ── PNG figure sections ───────────────────────────────────────────────
        # Summary is first (Ui_Module_Order) and starts expanded.
        # All individual plots start collapsed.
        self.Png_Widgets       = {}   # basename → PNG_Display_Widget
        self.Widget_Modules    = {}   # basename → module name
        self.Ordered_Widgets   = []   # same order, for sequential chain

        for module_name in self.Active_Modules:
            basename = Module_To_Basename[module_name]
            png_path = (self.Figures_Dir / f"{basename}.png") if self.Figures_Dir else None

            display = PNG_Display_Widget(
                str(png_path) if png_path else None,
                Deferred=True,
                Reload_Callback=lambda b=basename: self.Reload_Specific_Figure(b),
            )
            frame = PNG_Frame_Widget(
                display,
                Width_Only=(module_name in Individual_Modules),
            )

            # Transparent wrapper — inherits the collapsible section's background
            Plot_Container = QWidget()
            Plot_Container.setStyleSheet("background: transparent;")
            Plot_Container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            Container_Layout = QVBoxLayout(Plot_Container)
            Container_Layout.setContentsMargins(0, 8, 0, 8)
            Container_Layout.setSpacing(0)
            Container_Layout.addWidget(frame, alignment=Qt.AlignHCenter)

            section_title = Figure_Titles.get(basename, basename)
            section = Collapsible_Content_Container(
                section_title, Plot_Container,
                Initially_Show_Container=(module_name not in Individual_Modules),
                Expanding_Content=True,
            )
            self.Main_Layout.addWidget(section)
            self.Png_Widgets[basename]      = display
            self.Widget_Modules[basename]   = module_name
            self.Ordered_Widgets.append(display)

        # ── Regeneration debounce timer ───────────────────────────────────────
        self.Regeneration_Timer = QTimer(self)
        self.Regeneration_Timer.setSingleShot(True)
        self.Regeneration_Timer.setInterval(Regeneration_Debounce_Milliseconds)
        self.Regeneration_Timer.timeout.connect(self.Do_Figure_Regeneration)

        # ── Settings (lazy — created on first menu access) ────────────────────
        self.Settings_Dialog = None
        self.Queue_Connected = set()   # widgets with Advance_Loading_Queue connected

        # ── Study-panel connection ────────────────────────────────────────────
        self.Study_Panel.Selection_Changed.connect(self.Schedule_Figure_Regeneration)

        # ── Window geometry ───────────────────────────────────────────────────
        Screen = self.screen() or QApplication.primaryScreen()
        Screen_Geometry = Screen.availableGeometry()
        Initial_Width  = int(Screen_Geometry.width()  * 0.6)
        Initial_Height = int(Screen_Geometry.height() * 0.7)
        Center_X = (Screen_Geometry.width()  - Initial_Width)  // 2 + Screen_Geometry.x()
        Center_Y = (Screen_Geometry.height() - Initial_Height) // 2 + Screen_Geometry.y()
        self.setGeometry(Center_X, Center_Y, Initial_Width, Initial_Height)
        self.setMinimumSize(500, 400)
        self.Target_Position = QPoint(Center_X, Center_Y)
        self.Is_First_Show = True

        # ── Start sequential loading on first event-loop tick ─────────────────
        QTimer.singleShot(0, self.Start_Sequential_Loading)

    # ── Flash-free window show ────────────────────────────────────────────────

    def show(self):
        """Show the window without any white flash or position flicker."""
        if self.Is_First_Show:
            self.Is_First_Show = False
            self.setAttribute(Qt.WA_DontShowOnScreen, True)
            super().show()
            QApplication.processEvents()
            self.hide()
            self.setAttribute(Qt.WA_DontShowOnScreen, False)
            self.move(self.Target_Position)
            super().show()
        else:
            super().show()

    # ── Settings dialog (shared with MenuBar) ─────────────────────────────────

    def Get_Settings_Dialog(self):
        if self.Settings_Dialog is None:
            from Settings import Settings
            # parent=None → true top-level window, minimises to taskbar normally.
            self.Settings_Dialog = Settings(None)
            self.Settings_Dialog.Plot_Settings_Changed.connect(
                self.Schedule_Figure_Regeneration
            )
        return self.Settings_Dialog

    def Get_Current_Generation_Options(self):
        return Get_Current_Generation_Preferences(Selected_Keys=self.Selected_Studies)

    def Start_Generation(self, *, module_names, export_variants=None, include_display=True, preferences=None):
        Preferences = preferences or self.Get_Current_Generation_Options()
        Active_Studies = self.Study_Panel.Get_Active_Studies()

        if include_display:
            Start_Figure_Generation(
                Df=self.Dataframe,
                Composition=self.Plot_Composition,
                Method=self.Plot_Method,
                Input_Mode=self.Input_Mode,
                Reference_Key=self.Reference_Study_Key,
                Original_Study_Key=self.Original_Study_Key,
                Selected_Keys=Active_Studies,
                Figures_Dir=self.Figures_Dir,
                Show_Bands=Preferences["show_bands"],
                Show_Error_Bars=Preferences["show_error_bars"],
                Show_Grid=Preferences["show_grid"],
                Ps_Overrides=Preferences["ps_overrides"],
                Theme_Overrides=Preferences["theme_overrides"],
                Module_Names=module_names,
            )
        else:
            Start_Export_Variant_Generation(
                Df=self.Dataframe,
                Composition=self.Plot_Composition,
                Method=self.Plot_Method,
                Input_Mode=self.Input_Mode,
                Reference_Key=self.Reference_Study_Key,
                Original_Study_Key=self.Original_Study_Key,
                Selected_Keys=Active_Studies,
                Figures_Dir=self.Figures_Dir,
                Export_Variants=export_variants or [],
                Show_Bands=Preferences["show_bands"],
                Show_Error_Bars=Preferences["show_error_bars"],
                Show_Grid=Preferences["show_grid"],
                Ps_Overrides=Preferences["ps_overrides"],
                Theme_Overrides=Preferences["theme_overrides"],
                Module_Names=module_names,
            )

    def Ensure_Export_Variants_Built(self, export_requests):
        if self.Figures_Dir is None:
            return False

        missing_basenames = []
        missing_variants = []
        seen_basenames = set()
        seen_variants = set()

        for request in export_requests or []:
            src_path = request.get("Src_Path")
            if src_path and Path(src_path).exists():
                continue

            basename = request.get("Basename")
            theme_name = request.get("Theme")
            background_name = request.get("Background")
            if not basename or not theme_name or not background_name:
                continue

            if basename not in seen_basenames:
                seen_basenames.add(basename)
                module_name = Basename_To_Module.get(basename)
                if module_name in self.Active_Modules:
                    missing_basenames.append(basename)

            variant_key = (theme_name, background_name)
            if variant_key not in seen_variants:
                seen_variants.add(variant_key)
                missing_variants.append(variant_key)

        if not missing_basenames or not missing_variants:
            return True

        module_names = [
            Basename_To_Module[basename]
            for basename in missing_basenames
            if basename in Basename_To_Module
        ]
        if not module_names:
            return False

        self.Start_Generation(
            module_names=module_names,
            export_variants=missing_variants,
            include_display=False,
        )
        return True

    def Get_Export_Build_Progress(self):
        if self.Figures_Dir is None:
            return None
        return Get_Generation_Progress(self.Figures_Dir)

    def Cancel_Export_Build(self):
        if self.Figures_Dir is not None:
            Cancel_Generation(self.Figures_Dir)

    # ── Sequential loading chain ──────────────────────────────────────────────

    def Start_Sequential_Loading(self):
        """Initialise the loading queue and start the first widget."""
        if self.Ensure_Figure_Cache_Is_Current():
            return
        self.Queue_Connected = set()
        self.Loading_Queue = list(self.Ordered_Widgets)
        self.Advance_Loading_Queue()

    def Advance_Loading_Queue(self):
        """Start the next widget's loading; chain its finished signal to continue."""
        # Disconnect whichever widget's finished signal triggered this call.
        # Queue_Connected tracks the live connection so we never call disconnect
        # on a cold signal (which would print a libpyside RuntimeWarning).
        for w in list(self.Queue_Connected):
            w.Finished.disconnect(self.Advance_Loading_Queue)
        self.Queue_Connected.clear()

        if not self.Loading_Queue:
            return
        widget = self.Loading_Queue.pop(0)
        if self.Loading_Queue:
            widget.Finished.connect(self.Advance_Loading_Queue)
            self.Queue_Connected.add(widget)
        widget.Start_Loading()

    # ── Figure regeneration ───────────────────────────────────────────────────

    def Schedule_Figure_Regeneration(self):
        self.Regeneration_Timer.start()

    def Ensure_Figure_Cache_Is_Current(self):
        if self.Figures_Dir is None:
            return False

        Preferences = self.Get_Current_Generation_Options()
        Cached_Signature = Read_Generation_Signature(self.Figures_Dir)
        if Cached_Signature == Preferences["signature"]:
            return False

        self.Do_Figure_Regeneration(preferences=Preferences)
        return True

    def Reload_Specific_Figure(self, basename):
        if self.Figures_Dir is None:
            return

        module_name = self.Widget_Modules.get(basename)
        widget = self.Png_Widgets.get(basename)
        if module_name not in self.Active_Modules or widget is None:
            return

        try:
            png_path = self.Figures_Dir / f"{basename}.png"
            if png_path.exists():
                png_path.unlink()
            export_root = self.Figures_Dir / "export_variants"
            if export_root.exists():
                for variant_path in export_root.rglob(f"{basename}.png"):
                    try:
                        variant_path.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

        widget.Start_Loading()
        self.Start_Generation(
            module_names=[module_name],
            include_display=True,
        )

    def Do_Figure_Regeneration(self, preferences=None):
        if self.Figures_Dir is None:
            return

        Preferences = preferences or self.Get_Current_Generation_Options()
        Cancel_Generation(self.Figures_Dir)

        # Delete stale display/export PNGs so widgets never pick up an old image
        try:
            for png in self.Figures_Dir.glob("*.png"):
                try:
                    png.unlink()
                except Exception:
                    pass
            export_dir = self.Figures_Dir / "export_variants"
            if export_dir.exists():
                for png in export_dir.rglob("*.png"):
                    try:
                        png.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

        # Stop any running chain and reset all widgets
        self.Loading_Queue = []
        for w in list(self.Queue_Connected):
            w.Finished.disconnect(self.Advance_Loading_Queue)
        self.Queue_Connected.clear()
        for widget in self.Ordered_Widgets:
            widget.Reset()

        Write_Generation_Signature(self.Figures_Dir, Preferences["signature"])
        self.Start_Generation(
            module_names=self.Active_Modules,
            include_display=True,
            preferences=Preferences,
        )

        # Restart the sequential loading chain from the beginning
        self.Loading_Queue = list(self.Ordered_Widgets)
        self.Advance_Loading_Queue()

    # ── Export ────────────────────────────────────────────────────────────────

    def Get_Export_Entries(self):
        """Return figure entries plus cached theme/background export variants."""
        from Themes.Theme import Get_Theme

        entries = []
        current_theme_name, _, _ = Get_Theme()
        current_theme_key = "dark" if current_theme_name == "Dark" else "light"
        title_prefix = f"{self.Display_Run_Label} - " if self.Display_Run_Label else ""

        for basename in self.Png_Widgets:
            png_path = (self.Figures_Dir / f"{basename}.png") if self.Figures_Dir else None
            display_path = str(png_path) if (png_path and png_path.exists()) else None
            variants = {}

            for theme_name in Export_Theme_Options:
                for background_name in Export_Background_Options:
                    variant_path = None
                    if self.Figures_Dir is not None:
                        candidate = Get_Export_Variant_Path(
                            self.Figures_Dir, basename, theme_name, background_name
                        )
                        if candidate.exists():
                            variant_path = str(candidate)

                    # The live plot-window image is already the current theme with a
                    # transparent outer background, so expose it immediately as the
                    # matching export option even while background caching continues.
                    if (variant_path is None and display_path is not None
                            and theme_name == current_theme_key
                            and background_name == "transparent"):
                        variant_path = display_path

                    variants[Get_Export_Variant_Key(theme_name, background_name)] = {
                        "Theme": theme_name,
                        "Background": background_name,
                        "Path": variant_path,
                    }

            entries.append({
                "Basename": basename,
                "Title": f"{title_prefix}{Figure_Titles.get(basename, basename)}",
                "Path": display_path,
                "Variants": variants,
            })

        return entries

    def Open_Export_Dialog(self):
        from Export_Figures_Dialog import Export_Figures_Dialog
        # Reuse an existing open dialog rather than stacking multiple windows.
        existing = getattr(self, 'Export_Dialog', None)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return
        # parent=None → true top-level window, minimises to taskbar normally.
        Dialog = Export_Figures_Dialog(self.Get_Export_Entries(), parent=None, Owner_Window=self)
        self.Export_Dialog = Dialog  # strong reference
        Dialog.show()
        Dialog.raise_()
        Dialog.activateWindow()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if hasattr(self, "Regeneration_Timer") and self.Regeneration_Timer is not None:
            self.Regeneration_Timer.stop()
        if hasattr(self, "Settings_Dialog") and self.Settings_Dialog is not None:
            try:
                self.Settings_Dialog.Plot_Settings_Changed.disconnect(
                    self.Schedule_Figure_Regeneration
                )
            except Exception:
                pass
        if hasattr(self, "Study_Panel") and self.Study_Panel is not None:
            try:
                self.Study_Panel.Selection_Changed.disconnect(self.Schedule_Figure_Regeneration)
            except Exception:
                pass
        for w in list(getattr(self, "Queue_Connected", set())):
            try:
                w.Finished.disconnect(self.Advance_Loading_Queue)
            except Exception:
                pass
        # Clear all per-study style overrides so the next session always starts from
        # auto-assigned colors/markers rather than stale saved values.
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        for Key in Calibration_Metadata:
            Settings_Store.remove(f"{Key}_Color")
            Settings_Store.remove(f"{Key}_Marker")
            Settings_Store.remove(f"{Key}_Style_Is_User_Set")
        Settings_Store.sync()
        super().closeEvent(event)
