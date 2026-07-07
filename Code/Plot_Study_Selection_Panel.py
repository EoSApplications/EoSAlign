# Load libraries
    # Load standard libraries
import html
from functools import partial
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QSizePolicy, QColorDialog)
from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtGui import QColor
from PySide6.QtCore import QSettings
    # Load local functions from local files
from EoS_Math.Build_Dataframe import Calibration_Metadata
from Collapsible_Sections import CheckboxRow, Dropdown
from Themes.Plot_Style_Options import PLOT_MARKER_OPTIONS, PLOT_COLOR_PALETTE, DEFAULT_MARKER, AUTO_COLORS, AUTO_MARKERS
from Themes.Theme import Get_Theme
from View_Edit_And_Save_Calibration_Files_In_A_New_Window import Preview_Calibration_File_For_File_Path





# For each study allow the user to toggle the visibility, select the marker, select the color, and preview the calibration file
class Plot_Study_Selection_Panel(QWidget):

    # Emitted whenever a checkbox, color, or marker changes
    Selection_Changed = Signal()

    def __init__(self, Selected_Studies=None, Reference_Study_Key=None, *, Parent=None):
        super().__init__(Parent)
        self.setObjectName("CollapsibleContent")

        # Store the input parameters
        self.Selected_Studies = Selected_Studies or []
        self.Reference_Study_Key = Reference_Study_Key

        # {calibration_key: {"Checkbox": QCheckBox, "Color_Button": QPushButton,
        #                    "Marker_Dropdown": Dropdown}}
        self.Study_Row_Widgets = {}

        # Build the static header area (Select All / Deselect All + column headers)
        self.Build_Panel()

        # Populate one row per study
        self.Populate_Study_Rows()



    # Build the static header area of the panel
    def Build_Panel(self):

        Panel_Layout = QVBoxLayout(self)
        Panel_Layout.setContentsMargins(5, 5, 5, 5)
        Panel_Layout.setSpacing(8)

        # Select All / Deselect All buttons
        Button_Row = QHBoxLayout()
        self.Select_All_Button = QPushButton("Select All")
        self.Select_All_Button.setObjectName("Primary_Button")
        self.Select_All_Button.setFixedHeight(32)
        self.Select_All_Button.clicked.connect(self.Select_All)
        Button_Row.addWidget(self.Select_All_Button)

        self.Deselect_All_Button = QPushButton("Deselect All")
        self.Deselect_All_Button.setObjectName("Secondary_Button")
        self.Deselect_All_Button.setFixedHeight(32)
        self.Deselect_All_Button.clicked.connect(self.Deselect_All)
        Button_Row.addWidget(self.Deselect_All_Button)

        self.Reset_Styles_Button = QPushButton("Reset All Styles")
        self.Reset_Styles_Button.setObjectName("Secondary_Button")
        self.Reset_Styles_Button.setFixedHeight(32)
        self.Reset_Styles_Button.setToolTip("Clear all saved colors and markers so every study reverts to its automatic assignment.")
        self.Reset_Styles_Button.clicked.connect(self.Reset_All_Styles)
        Button_Row.addWidget(self.Reset_Styles_Button)

        Button_Row.addStretch()
        Panel_Layout.addLayout(Button_Row)

        # Container that holds the dynamically generated study rows
        self.Studies_Container = QWidget()
        self.Studies_Container.setObjectName("CollapsibleSubContainer")
        self.Studies_Layout = QVBoxLayout(self.Studies_Container)
        self.Studies_Layout.setContentsMargins(5, 5, 5, 5)
        self.Studies_Layout.setSpacing(4)
        self.Studies_Layout.setAlignment(Qt.AlignTop)
        Panel_Layout.addWidget(self.Studies_Container)



    # Clear existing rows and rebuild one row per study in self.Selected_Studies
    def Populate_Study_Rows(self):

        # Remove all previously built rows
        while self.Studies_Layout.count() > 0:
            Item = self.Studies_Layout.takeAt(0)
            Widget = Item.widget()
            if Widget:
                Widget.setParent(None)
                Widget.deleteLater()
        self.Study_Row_Widgets.clear()

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")

        # Look up the caution colors used to flag user-edited/user-entered calibrants
        _, _, Theme_Colors = Get_Theme()
        Caution_Color = Theme_Colors.get("Caution_Text")
        Caution_Accent_Color = Theme_Colors.get("Caution_Text_Accent")

        for Study_Index, Calibration_Key in enumerate(self.Selected_Studies):

            Metadata = Calibration_Metadata.get(Calibration_Key, {})
            Is_User_Calibrant = bool(Metadata.get("is_user_edited", False) or Metadata.get("is_user_entered", False))
            Study_Name = ("* " if Is_User_Calibrant else "") + Metadata.get("Study", Calibration_Key)
            Equation_Of_State = Metadata.get("Equation of State", "")
            Maximum_Pressure = Metadata.get("Maximum Pressure", "")
            File_Path = Metadata.get("file_path")

            # Build the display label shown next to the checkbox
            Label_Parts = [Study_Name]
            if Equation_Of_State:
                Label_Parts.append(Equation_Of_State)
            if Maximum_Pressure:
                Label_Parts.append(f"Max P: {Maximum_Pressure} GPa")
            Label_Text = " | ".join(Label_Parts)

            # Build HTML versions of the label so only the leading "*" is shown in the caution
            # color — a hover variant is also built so it can switch to the accent color on hover.
            Label_Html = html.escape(Label_Text)
            Label_Html_Hover = Label_Html
            if Is_User_Calibrant:
                Label_Html = Label_Html.replace("*", f'<span style="color: {Caution_Color};">*</span>', 1)
                Label_Html_Hover = Label_Html_Hover.replace("*", f'<span style="color: {Caution_Accent_Color};">*</span>', 1)

            # ── Row widget ───────────────────────────────────────────────────
            Row = CheckboxRow()
            Row_Outer_Layout = QVBoxLayout()
            Row_Outer_Layout.setContentsMargins(0, 0, 0, 0)
            Row_Outer_Layout.setSpacing(0)
            Row_Layout = QHBoxLayout()
            Row_Layout.setContentsMargins(6, 4, 6, 4)
            Row_Layout.setSpacing(6)

            # Checkbox — signal connected after initial state is set
            Checkbox = QCheckBox()
            Checkbox.setObjectName("Checkbox")
            Checkbox.setChecked(True)
            Row_Layout.addWidget(Checkbox)

            # Study label — clicking the label toggles the checkbox
            Study_Label = QLabel(Label_Html)
            Study_Label.setObjectName("CollapsibleContentLabel")
            Study_Label.setWordWrap(True)
            Study_Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            Study_Label.mousePressEvent = lambda _, cb=Checkbox: cb.setChecked(not cb.isChecked())
            Row_Layout.addWidget(Study_Label, stretch=1)

            # Marker shape dropdown
            Marker_Dropdown = Dropdown()
            Marker_Dropdown.setFixedWidth(130)
            for Option in PLOT_MARKER_OPTIONS:
                Marker_Dropdown.addItem(Option["Display_Name"], userData=Option["Matplotlib_Code"])
            # Only assign an automatic default when the study has not been styled yet.
            Saved_Marker = (Settings_Store.value(f"{Calibration_Key}_Marker", "", type=str) or "").strip()
            if not Saved_Marker:
                Saved_Marker = AUTO_MARKERS[Study_Index % len(AUTO_MARKERS)] if AUTO_MARKERS else DEFAULT_MARKER
                # Do NOT save auto-assigned defaults to QSettings — only persist explicit user choices.
                # Saving here would permanently stamp a position-based color/marker that can collide
                # with another study that happens to land at the same index in a different session.
            for Index in range(Marker_Dropdown.count()):
                if Marker_Dropdown.itemData(Index) == Saved_Marker:
                    Marker_Dropdown.setCurrentIndex(Index)
                    break
            Row_Layout.addWidget(Marker_Dropdown)

            # Color swatch button — inline stylesheet shows the saved color
            Saved_Color = (Settings_Store.value(f"{Calibration_Key}_Color", "", type=str) or "").strip()
            if not Saved_Color:
                Saved_Color = AUTO_COLORS[Study_Index % len(AUTO_COLORS)] if AUTO_COLORS else ""
                # Do NOT save auto-assigned defaults to QSettings — only persist explicit user choices.
            Color_Button = QPushButton()
            Color_Button.setObjectName("Color_Swatch_Button")
            Color_Button.setFixedSize(44, 26)
            Color_Button.setToolTip("Click to pick a line color.\nLeave as 'Auto' to use the automatic gradient.")
            self.Apply_Color_To_Button(Color_Button, Saved_Color)
            Row_Layout.addWidget(Color_Button)

            # Preview YAML button
            Preview_Button = QPushButton("Preview Calibrant")
            Preview_Button.setObjectName("Preview_Calibration_Button")
            Preview_Button.setFixedHeight(32)
            if File_Path:
                Preview_Button.setToolTip(f"Preview the YAML calibration file for {Study_Name}")
            else:
                Preview_Button.setEnabled(False)
                Preview_Button.setToolTip("No YAML file path available for this study")
            Row_Layout.addWidget(Preview_Button)

            Row_Outer_Layout.addLayout(Row_Layout)

            # Show a footnote directly under this row when it is user-edited or user-entered
            if Is_User_Calibrant:
                Footnote_Style_Normal = f"font-size: 8pt; color: {Caution_Color};"
                Footnote_Style_Hover = f"font-size: 8pt; color: {Caution_Accent_Color};"
                Row_Footnote = QLabel("* indicates user edited or entered calibrant")
                Row_Footnote.setObjectName("CollapsibleContentLabel")
                Row_Footnote.setStyleSheet(Footnote_Style_Normal)
                Row_Footnote.setContentsMargins(60, 0, 6, 4)
                Row_Outer_Layout.addWidget(Row_Footnote)

                # Swap the "*" and footnote to the accent color while this row is hovered
                def On_Row_Hover_Changed(
                    Is_Hovered,
                    Label=Study_Label,
                    Normal_Html=Label_Html,
                    Hover_Html=Label_Html_Hover,
                    Footnote=Row_Footnote,
                    Normal_Style=Footnote_Style_Normal,
                    Hover_Style=Footnote_Style_Hover,
                ):
                    Label.setText(Hover_Html if Is_Hovered else Normal_Html)
                    Footnote.setStyleSheet(Hover_Style if Is_Hovered else Normal_Style)

                Row.Add_Hover_Callback(On_Row_Hover_Changed)

            Row.setLayout(Row_Outer_Layout)
            self.Studies_Layout.addWidget(Row)

            # Track the interactive widgets for this study
            self.Study_Row_Widgets[Calibration_Key] = {
                "Checkbox":       Checkbox,
                "Color_Button":   Color_Button,
                "Marker_Dropdown": Marker_Dropdown,
            }

            # Connect signals after initial state is set to avoid spurious redraws
            Checkbox.stateChanged.connect(self.On_Selection_Changed)
            Marker_Dropdown.currentIndexChanged.connect(
                partial(self.On_Marker_Changed, Calibration_Key, Marker_Dropdown)
            )
            Color_Button.clicked.connect(
                partial(self.Pick_Color, Calibration_Key, Color_Button)
            )
            if File_Path:
                Preview_Button.clicked.connect(
                    lambda Checked=False, fp=File_Path: Preview_Calibration_File_For_File_Path(self, fp)
                )

        # Show a placeholder message if the study list is empty
        if not self.Study_Row_Widgets:
            Placeholder = QLabel("No comparison studies available.")
            Placeholder.setObjectName("CollapsibleContentLabel")
            Placeholder.setWordWrap(True)
            self.Studies_Layout.addWidget(Placeholder)



    # Apply a hex color to a color swatch button
        # If the color string is empty, the button shows "Auto" (gradient default)
        # The inline stylesheet intentionally overrides theme QSS for this swatch
    @staticmethod
    def Apply_Color_To_Button(Button, Hex_Color):
        if Hex_Color and Hex_Color.strip():
            Button.setStyleSheet(
                f"background-color: {Hex_Color}; "
                f"border: 1px solid #888888; "
                f"border-radius: 3px; "
                f"color: transparent;"
            )
            Button.setText("")
        else:
            Button.setStyleSheet(
                "border: 1px solid #888888; "
                "border-radius: 3px;"
            )
            Button.setText("Auto")



    # Open a color picker dialog and save the result to QSettings
    def Pick_Color(self, Calibration_Key, Color_Button):

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        Current_Color_Hex = Settings_Store.value(f"{Calibration_Key}_Color", "")
        Initial_Color = QColor(Current_Color_Hex) if Current_Color_Hex else QColor(Qt.white)

        Picked_Color = QColorDialog.getColor(Initial_Color, self, "Pick Line Color")
        if Picked_Color.isValid():
            Hex = Picked_Color.name()
            Settings_Store.setValue(f"{Calibration_Key}_Color", Hex)
            Settings_Store.setValue(f"{Calibration_Key}_Style_Is_User_Set", True)
            self.Apply_Color_To_Button(Color_Button, Hex)
            self.Selection_Changed.emit()



    # Save the marker selection to QSettings and emit the change signal
    def On_Marker_Changed(self, Calibration_Key, Marker_Dropdown, Index):

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        Settings_Store.setValue(f"{Calibration_Key}_Marker", Marker_Dropdown.currentData())
        Settings_Store.setValue(f"{Calibration_Key}_Style_Is_User_Set", True)
        self.Selection_Changed.emit()



    # Emit the change signal when a study checkbox is toggled
    def On_Selection_Changed(self):
        self.Selection_Changed.emit()



    # Return the list of calibration keys whose checkboxes are currently checked
    def Get_Active_Studies(self):
        return [
            Key for Key, Widgets in self.Study_Row_Widgets.items()
            if Widgets["Checkbox"].isChecked()
        ]



    # Return the saved hex color string for a study, or empty string if none is set
    @staticmethod
    def Get_Study_Color(Calibration_Key):
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        return Settings_Store.value(f"{Calibration_Key}_Color", "")



    # Return the saved matplotlib marker code for a study
    @staticmethod
    def Get_Study_Marker(Calibration_Key):
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        return Settings_Store.value(f"{Calibration_Key}_Marker", DEFAULT_MARKER)



    # Clear the saved color for a study and reset its swatch button to Auto
    def Clear_Study_Color(self, Calibration_Key):

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        Settings_Store.remove(f"{Calibration_Key}_Color")
        if Calibration_Key in self.Study_Row_Widgets:
            self.Apply_Color_To_Button(
                self.Study_Row_Widgets[Calibration_Key]["Color_Button"], ""
            )
        self.Selection_Changed.emit()



    # Refresh the marker dropdowns and color swatches from QSettings without
    # disturbing the current checkbox selections.
    def Refresh_Styles(self):

        for Study_Index, Calibration_Key in enumerate(self.Selected_Studies):
            Widgets = self.Study_Row_Widgets.get(Calibration_Key)
            if Widgets is None:
                continue

            Saved_Color = (self.Get_Study_Color(Calibration_Key) or "").strip()
            if not Saved_Color and AUTO_COLORS:
                Saved_Color = AUTO_COLORS[Study_Index % len(AUTO_COLORS)]
            self.Apply_Color_To_Button(Widgets["Color_Button"], Saved_Color)

            Saved_Marker = (self.Get_Study_Marker(Calibration_Key) or "").strip()
            if not Saved_Marker:
                Saved_Marker = AUTO_MARKERS[Study_Index % len(AUTO_MARKERS)] if AUTO_MARKERS else DEFAULT_MARKER

            Marker_Dropdown = Widgets["Marker_Dropdown"]
            Blocker = QSignalBlocker(Marker_Dropdown)
            try:
                for Index in range(Marker_Dropdown.count()):
                    if Marker_Dropdown.itemData(Index) == Saved_Marker:
                        Marker_Dropdown.setCurrentIndex(Index)
                        break
            finally:
                del Blocker



    # Clear every saved color and marker for all known calibration keys, then refresh the panel
    def Reset_All_Styles(self):
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        for Key in Calibration_Metadata:
            Settings_Store.remove(f"{Key}_Color")
            Settings_Store.remove(f"{Key}_Marker")
            Settings_Store.remove(f"{Key}_Style_Is_User_Set")
        Settings_Store.sync()
        # Rebuild rows so the UI immediately shows the fresh auto-assigned defaults
        self.Populate_Study_Rows()
        self.Selection_Changed.emit()


    # Check all study checkboxes
    def Select_All(self):
        for Widgets in self.Study_Row_Widgets.values():
            Widgets["Checkbox"].setChecked(True)



    # Uncheck all study checkboxes
    def Deselect_All(self):
        for Widgets in self.Study_Row_Widgets.values():
            Widgets["Checkbox"].setChecked(False)



    # Rebuild the panel with a new list of selected studies
        # Call this when the upstream study selection changes (e.g. when
        # Select_Studies_For_Comparison sends a new list)
    def Refresh(self, Selected_Studies=None, Reference_Study_Key=None):
        self.Selected_Studies = Selected_Studies or []
        self.Reference_Study_Key = Reference_Study_Key
        self.Populate_Study_Rows()
