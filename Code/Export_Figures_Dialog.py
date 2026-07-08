# Load libraries
#     Load standard libraries
import os
import shutil

#     Load third party libraries
from PySide6.QtCore import QEventLoop, QSettings, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon

from Loading_Message import Get_Resource_Path
from Message_Manager import Warning_Message
from Plots.Generate_Figures import (
    Export_Background_Labels,
    Export_Background_Options,
    Export_Theme_Labels,
    Export_Theme_Options,
    Get_Export_Variant_Key,
    Get_Export_Variant_Label,
)
from Themes.Theme import Get_Theme


class Export_Figures_Dialog(QDialog):

    def __init__(self, Figure_Entries, parent=None, Owner_Window=None):
        super().__init__(parent)
        # Give this dialog a full window title bar with minimize, maximize, and close.
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("Export Figures")
        self.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
        self.setMinimumWidth(500)
        self.Figure_Entries = Figure_Entries
        self.Owner_Window = Owner_Window if Owner_Window is not None else parent
        self.Current_Theme_Key = self.Get_Current_Theme_Key()

        self.Build_UI()
        self.Load_Saved_Selections()
        self.Has_Shown_Once = False


    # Show without a white flash by appearing off-screen first.
    def show(self):
        if not self.Has_Shown_Once:
            self.Has_Shown_Once = True
            screen = QApplication.primaryScreen()
            sg = screen.availableGeometry()
            w = max(self.width(), self.minimumWidth())
            h = max(self.height(), self.minimumHeight(), 400)
            cx = (sg.width() - w) // 2 + sg.x()
            cy = (sg.height() - h) // 2 + sg.y()
            self.setAttribute(Qt.WA_DontShowOnScreen, True)
            super().show()
            QApplication.processEvents()
            self.hide()
            self.setAttribute(Qt.WA_DontShowOnScreen, False)
            self.move(cx, cy)
            super().show()
        else:
            super().show()


    def Build_UI(self):

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(16, 16, 16, 16)
        Layout.setSpacing(10)

        Instruction = QLabel(
            "Select figures, themes, and background colors.\n"
            "Transparent works with any theme. Light pairs automatically with white, and dark pairs automatically with black.\n"
            "Light + black and dark + white are built only when they are the only selected theme/background pair."
        )
        Instruction.setWordWrap(True)
        Layout.addWidget(Instruction)

        Figure_Button_Row = QHBoxLayout()
        Select_All_Button = QPushButton("Select All Figures")
        Select_All_Button.setObjectName("Primary_Button")
        Select_All_Button.setFixedHeight(32)
        Select_All_Button.clicked.connect(self.Select_All_Figures)
        Figure_Button_Row.addWidget(Select_All_Button)

        Deselect_All_Button = QPushButton("Deselect All Figures")
        Deselect_All_Button.setObjectName("Secondary_Button")
        Deselect_All_Button.setFixedHeight(32)
        Deselect_All_Button.clicked.connect(self.Deselect_All_Figures)
        Figure_Button_Row.addWidget(Deselect_All_Button)
        Figure_Button_Row.addStretch()
        Layout.addLayout(Figure_Button_Row)

        Top_Line = QFrame()
        Top_Line.setFrameShape(QFrame.HLine)
        Top_Line.setFrameShadow(QFrame.Sunken)
        Layout.addWidget(Top_Line)

        Scroll = QScrollArea()
        Scroll.setWidgetResizable(True)
        Scroll.setFrameShape(QFrame.NoFrame)
        Scroll.setMaximumHeight(320)
        Checkbox_Container = QWidget()
        Checkbox_Layout = QVBoxLayout(Checkbox_Container)
        Checkbox_Layout.setContentsMargins(4, 4, 4, 4)
        Checkbox_Layout.setSpacing(6)

        self.Figure_Checkboxes = {}
        for Entry in self.Figure_Entries:
            Title = Entry["Title"]
            Ready = self.Entry_Has_Ready_Output(Entry)
            Checkbox = QCheckBox(Title)
            Checkbox.setObjectName("Checkbox")
            Checkbox.setChecked(Ready)
            if not Ready:
                Checkbox.setToolTip("This figure will be built before export.")
            Checkbox_Layout.addWidget(Checkbox)
            self.Figure_Checkboxes[Title] = Checkbox

        Checkbox_Layout.addStretch()
        Scroll.setWidget(Checkbox_Container)
        Layout.addWidget(Scroll)

        Theme_Line = QFrame()
        Theme_Line.setFrameShape(QFrame.HLine)
        Theme_Line.setFrameShadow(QFrame.Sunken)
        Layout.addWidget(Theme_Line)

        Theme_Label = QLabel("Themes")
        Layout.addWidget(Theme_Label)

        self.Theme_Checkboxes = {}
        Theme_Row = QHBoxLayout()
        for Theme_Key in Export_Theme_Options:
            Checkbox = QCheckBox(Export_Theme_Labels[Theme_Key])
            Checkbox.setObjectName("Checkbox")
            Checkbox.setChecked(Theme_Key == self.Current_Theme_Key)
            Theme_Row.addWidget(Checkbox)
            self.Theme_Checkboxes[Theme_Key] = Checkbox
        Theme_Row.addStretch()
        Layout.addLayout(Theme_Row)

        Background_Label = QLabel("Background Colors")
        Layout.addWidget(Background_Label)

        self.Background_Checkboxes = {}
        Background_Row = QHBoxLayout()
        for Background_Key in Export_Background_Options:
            Checkbox = QCheckBox(Export_Background_Labels[Background_Key])
            Checkbox.setObjectName("Checkbox")
            Checkbox.setChecked(Background_Key == "transparent")
            Background_Row.addWidget(Checkbox)
            self.Background_Checkboxes[Background_Key] = Checkbox
        Background_Row.addStretch()
        Layout.addLayout(Background_Row)

        Bottom_Line = QFrame()
        Bottom_Line.setFrameShape(QFrame.HLine)
        Bottom_Line.setFrameShadow(QFrame.Sunken)
        Layout.addWidget(Bottom_Line)

        Action_Row = QHBoxLayout()
        Action_Row.addStretch()

        Export_Button = QPushButton("Export Selected...")
        Export_Button.setObjectName("Primary_Button")
        Export_Button.setFixedHeight(32)
        Export_Button.clicked.connect(self.Export_Selected)
        Action_Row.addWidget(Export_Button)

        Cancel_Button = QPushButton("Cancel")
        Cancel_Button.setObjectName("Secondary_Button")
        Cancel_Button.setFixedHeight(32)
        Cancel_Button.clicked.connect(self.reject)
        Action_Row.addWidget(Cancel_Button)

        Layout.addLayout(Action_Row)

    def Load_Saved_Selections(self):

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        if not Settings_Store.value("Remember_Export_Selections", False, type=bool):
            return

        for Title, Checkbox in self.Figure_Checkboxes.items():
            Key = f"Export_Selected_Figure_{Title.replace(' ', '_')}"
            if Settings_Store.contains(Key):
                Checkbox.setChecked(Settings_Store.value(Key, True, type=bool))

        for Theme_Key, Checkbox in self.Theme_Checkboxes.items():
            Key = f"Export_Selected_Theme_{Theme_Key}"
            if Settings_Store.contains(Key):
                Checkbox.setChecked(
                    Settings_Store.value(Key, Theme_Key == self.Current_Theme_Key, type=bool)
                )

        for Background_Key, Checkbox in self.Background_Checkboxes.items():
            Key = f"Export_Selected_Background_{Background_Key}"
            if Settings_Store.contains(Key):
                Checkbox.setChecked(
                    Settings_Store.value(Key, Background_Key == "transparent", type=bool)
                )

    def Save_Selections(self):

        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        if not Settings_Store.value("Remember_Export_Selections", False, type=bool):
            return

        for Title, Checkbox in self.Figure_Checkboxes.items():
            Key = f"Export_Selected_Figure_{Title.replace(' ', '_')}"
            Settings_Store.setValue(Key, Checkbox.isChecked())

        for Theme_Key, Checkbox in self.Theme_Checkboxes.items():
            Settings_Store.setValue(f"Export_Selected_Theme_{Theme_Key}", Checkbox.isChecked())

        for Background_Key, Checkbox in self.Background_Checkboxes.items():
            Settings_Store.setValue(
                f"Export_Selected_Background_{Background_Key}",
                Checkbox.isChecked(),
            )

    def Select_All_Figures(self):
        for Checkbox in self.Figure_Checkboxes.values():
            if Checkbox.isEnabled():
                Checkbox.setChecked(True)

    def Deselect_All_Figures(self):
        for Checkbox in self.Figure_Checkboxes.values():
            if Checkbox.isEnabled():
                Checkbox.setChecked(False)

    @staticmethod
    def Safe_Filename(title):
        return (
            title.replace("/", "-")
            .replace("\\", "-")
            .replace(":", "-")
            .replace("*", "-")
            .replace("?", "")
            .replace('"', "")
            .replace("<", "")
            .replace(">", "")
            .replace("|", "-")
            .strip()
        )

    @staticmethod
    def Initial_Export_Directory():
        Home_Directory = os.path.expanduser("~")
        Desktop_Directory = os.path.join(Home_Directory, "Desktop")
        if os.path.isdir(Desktop_Directory):
            return Desktop_Directory
        return Home_Directory

    @staticmethod
    def Get_Current_Theme_Key():
        Current_Theme_Name, _, _ = Get_Theme()
        return "dark" if Current_Theme_Name == "Dark" else "light"

    @staticmethod
    def Path_Is_Ready(Path_Value):
        return bool(Path_Value) and os.path.exists(Path_Value)

    @staticmethod
    def Format_Eta(eta_seconds):
        if eta_seconds is None:
            return "Estimating..."

        eta_seconds = max(0, int(round(float(eta_seconds))))
        hours, remainder = divmod(eta_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def Entry_Has_Ready_Output(self, Entry):
        if self.Path_Is_Ready(Entry.get("Path")):
            return True
        for Variant in (Entry.get("Variants") or {}).values():
            if self.Path_Is_Ready(Variant.get("Path")):
                return True
        return False

    def Get_Selected_Figure_Entries(self):
        return [
            Entry for Entry in self.Figure_Entries
            if self.Figure_Checkboxes.get(Entry["Title"]) is not None
            and self.Figure_Checkboxes[Entry["Title"]].isChecked()
        ]

    def Refresh_Figure_Entries(self):
        Parent = self.Owner_Window
        if Parent is None or not hasattr(Parent, "Get_Export_Entries"):
            return
        self.Figure_Entries = Parent.Get_Export_Entries()

    def Lookup_Current_Request_Path(self, Request):
        Basename = Request.get("Basename")
        Theme_Key = Request.get("Theme")
        Background_Key = Request.get("Background")
        if not Basename or not Theme_Key or not Background_Key:
            return Request.get("Src_Path")

        for Entry in self.Figure_Entries:
            if Entry.get("Basename") != Basename:
                continue
            Variant_Key = Get_Export_Variant_Key(Theme_Key, Background_Key)
            Variant_Info = (Entry.get("Variants") or {}).get(Variant_Key) or {}
            return Variant_Info.get("Path")

        return Request.get("Src_Path")

    def Refresh_Request_Paths(self, Requests):
        Refreshed = []
        for Request in Requests or []:
            Updated_Request = dict(Request)
            Updated_Request["Src_Path"] = self.Lookup_Current_Request_Path(Request)
            Refreshed.append(Updated_Request)
        return Refreshed

    def Get_Selected_Themes(self):
        return [
            Theme_Key for Theme_Key, Checkbox in self.Theme_Checkboxes.items()
            if Checkbox.isChecked()
        ]

    def Get_Selected_Backgrounds(self):
        return [
            Background_Key for Background_Key, Checkbox in self.Background_Checkboxes.items()
            if Checkbox.isChecked()
        ]

    def Resolve_Selected_Variant_Pairs(self, Selected_Themes, Selected_Backgrounds):
        Variant_Pairs = []

        if "transparent" in Selected_Backgrounds:
            for Theme_Key in Selected_Themes:
                Variant_Pairs.append((Theme_Key, "transparent"))

        if "light" in Selected_Themes and "white" in Selected_Backgrounds:
            Variant_Pairs.append(("light", "white"))

        if "dark" in Selected_Themes and "black" in Selected_Backgrounds:
            Variant_Pairs.append(("dark", "black"))

        if len(Selected_Themes) == 1 and len(Selected_Backgrounds) == 1:
            Theme_Key = Selected_Themes[0]
            Background_Key = Selected_Backgrounds[0]
            if Theme_Key == "light" and Background_Key == "black":
                Variant_Pairs.append(("light", "black"))
            elif Theme_Key == "dark" and Background_Key == "white":
                Variant_Pairs.append(("dark", "white"))

        Unique_Pairs = []
        Seen = set()
        for Pair in Variant_Pairs:
            if Pair in Seen:
                continue
            Seen.add(Pair)
            Unique_Pairs.append(Pair)
        return Unique_Pairs

    def Build_Export_List(self, Selected_Entries, Variant_Pairs):
        Ready_To_Export = []
        Missing = []

        for Entry in Selected_Entries:
            Variants = Entry.get("Variants") or {}
            for Theme_Key, Background_Key in Variant_Pairs:
                Variant_Key = Get_Export_Variant_Key(Theme_Key, Background_Key)
                Variant_Info = Variants.get(Variant_Key) or {}
                Src_Path = Variant_Info.get("Path")
                Variant_Label = Get_Export_Variant_Label(Theme_Key, Background_Key)

                Request = {
                    "Basename": Entry.get("Basename"),
                    "Title": Entry["Title"],
                    "Theme": Theme_Key,
                    "Background": Background_Key,
                    "Variant_Label": Variant_Label,
                    "Src_Path": Src_Path,
                }
                if self.Path_Is_Ready(Src_Path):
                    Ready_To_Export.append(Request)
                else:
                    Missing.append(Request)

        return Ready_To_Export, Missing

    def Wait_For_Build(self):
        Parent = self.Owner_Window
        if Parent is None or not hasattr(Parent, "Get_Export_Build_Progress"):
            Warning_Message(
                self,
                "Error Exporting Figures",
                errors="The export dialog could not find the plot window that builds figure files.",
            )
            return False

        Wait_Dialog = QProgressDialog(
            "Building selected export figures...",
            "Cancel",
            0,
            100,
            self,
        )
        Wait_Dialog.setWindowTitle("Preparing Export")
        Wait_Dialog.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
        Wait_Dialog.setWindowModality(Qt.WindowModal)
        Wait_Dialog.setMinimumDuration(0)
        Wait_Dialog.setAutoClose(False)
        Wait_Dialog.setAutoReset(False)

        Loop = QEventLoop(self)
        Poll_Timer = QTimer(self)
        Poll_Timer.setInterval(150)
        Result = {"Canceled": False, "Completed": False, "Progress": None}

        def Finish_Wait():
            Poll_Timer.stop()
            try:
                Wait_Dialog.canceled.disconnect(Cancel_Wait)
            except Exception:
                pass
            Wait_Dialog.close()
            Loop.quit()

        def Poll_Progress():
            Progress = Parent.Get_Export_Build_Progress()
            Result["Progress"] = Progress
            if not Progress:
                return

            Total = max(int(Progress.get("total_steps", 0)), 1)
            Completed = min(int(Progress.get("completed_steps", 0)), Total)
            Wait_Dialog.setMaximum(Total)
            Wait_Dialog.setValue(Completed)
            Wait_Dialog.setLabelText(
                f"{Progress.get('current_step', 'Building export figures...')}\n"
                f"Estimated time remaining: {self.Format_Eta(Progress.get('eta_seconds'))}"
            )

            if not Progress.get("running", False):
                if not Progress.get("canceled", False) and not Progress.get("failed", False):
                    Result["Completed"] = True
                    Wait_Dialog.setValue(Total)
                Finish_Wait()

        def Cancel_Wait():
            if Result.get("Completed"):
                return
            Result["Canceled"] = True
            if hasattr(Parent, "Cancel_Export_Build"):
                Parent.Cancel_Export_Build()
            Finish_Wait()

        Poll_Timer.timeout.connect(Poll_Progress)
        Wait_Dialog.canceled.connect(Cancel_Wait)
        Poll_Timer.start()
        Poll_Progress()
        Loop.exec()
        return not Result["Canceled"]

    def Ensure_Missing_Exports_Are_Built(self, Missing):
        if not Missing:
            return True

        Parent = self.Owner_Window
        if Parent is None or not hasattr(Parent, "Ensure_Export_Variants_Built"):
            Warning_Message(
                self,
                "Error Exporting Figures",
                errors="The export dialog could not find the plot window that builds missing export variants.",
            )
            return False

        if not Parent.Ensure_Export_Variants_Built(Missing):
            Warning_Message(
                self,
                "Error Exporting Figures",
                errors="The selected export figure variants could not be queued for building.",
            )
            return False

        if not self.Wait_For_Build():
            return False

        self.Refresh_Figure_Entries()
        return True

    def Export_Request_List(self, Export_Requests, Last_Dir, Exported_Count, Errors):
        Export_Requests = self.Refresh_Request_Paths(Export_Requests)
        Total_Requests = len(Export_Requests)

        for Index, Export_Entry in enumerate(Export_Requests, start=1):
            Title = Export_Entry["Title"]
            Variant_Label = Export_Entry["Variant_Label"]
            Src_Path = Export_Entry["Src_Path"]

            if not self.Path_Is_Ready(Src_Path):
                Errors.append(f"{Title} [{Variant_Label}]: figure is not ready to save.")
                continue

            Safe_Title = self.Safe_Filename(Title)
            Safe_Theme = self.Safe_Filename(
                Export_Theme_Labels[Export_Entry["Theme"]]
            ).replace(" ", "_").lower()
            Safe_Background = self.Safe_Filename(
                Export_Background_Labels[Export_Entry["Background"]]
            ).replace(" ", "_").lower()
            Suggested_Path = os.path.join(
                Last_Dir,
                f"{Safe_Title}__{Safe_Theme}__{Safe_Background}.png",
            )

            Dest_Path, _ = QFileDialog.getSaveFileName(
                self,
                f"Save image {Index} of {Total_Requests}: {Title} [{Variant_Label}]",
                Suggested_Path,
                "PNG Image (*.png);;All Files (*)",
            )

            if not Dest_Path:
                if Index < Total_Requests:
                    Reply = Warning_Message(
                        self,
                        "Export Figure Skip Or Stop",
                        title=f"{Title} [{Variant_Label}]",
                        Buttons=QMessageBox.Yes | QMessageBox.No,
                        Default_Button=QMessageBox.Yes,
                    )
                    if Reply == QMessageBox.No:
                        return Last_Dir, Exported_Count, False
                continue

            if not Dest_Path.lower().endswith(".png"):
                Dest_Path += ".png"

            Last_Dir = os.path.dirname(Dest_Path)

            try:
                shutil.copy2(Src_Path, Dest_Path)
                Exported_Count += 1
            except Exception as exc:
                Errors.append(f"{Title} [{Variant_Label}]: {exc}")

        return Last_Dir, Exported_Count, True

    def Export_Selected(self):

        self.Refresh_Figure_Entries()
        Selected_Entries = self.Get_Selected_Figure_Entries()
        Selected_Themes = self.Get_Selected_Themes()
        Selected_Backgrounds = self.Get_Selected_Backgrounds()

        Variant_Pairs = self.Resolve_Selected_Variant_Pairs(
            Selected_Themes,
            Selected_Backgrounds,
        )
        if not Selected_Entries or not Variant_Pairs:
            Warning_Message(self, "Nothing Ready To Export")
            return

        Ready_To_Export, Missing = self.Build_Export_List(Selected_Entries, Variant_Pairs)
        Missing = self.Refresh_Request_Paths(Missing)
        if not Ready_To_Export and not Missing:
            Warning_Message(self, "Nothing Ready To Export")
            return

        self.Save_Selections()

        Last_Dir = self.Initial_Export_Directory()

        Exported_Count = 0
        Errors = []

        if Ready_To_Export:
            Last_Dir, Exported_Count, Continue_Export = self.Export_Request_List(
                Ready_To_Export,
                Last_Dir,
                Exported_Count,
                Errors,
            )
            if not Continue_Export:
                if Errors:
                    Warning_Message(self, "Error Exporting Figures", errors="\n".join(Errors))
                if Exported_Count:
                    self.accept()
                return

        if Missing:
            if not self.Ensure_Missing_Exports_Are_Built(Missing):
                return
            Missing = self.Refresh_Request_Paths(Missing)
            Newly_Ready = [
                Entry for Entry in Missing
                if self.Path_Is_Ready(Entry.get("Src_Path"))
            ]
            Missing = [
                Entry for Entry in Missing
                if not self.Path_Is_Ready(Entry.get("Src_Path"))
            ]
            Already_Exported = {
                (
                    entry["Title"],
                    entry["Theme"],
                    entry["Background"],
                )
                for entry in Ready_To_Export
            }
            Remaining_To_Export = [
                entry for entry in Newly_Ready
                if (entry["Title"], entry["Theme"], entry["Background"]) not in Already_Exported
            ]

            if Remaining_To_Export:
                Last_Dir, Exported_Count, Continue_Export = self.Export_Request_List(
                    Remaining_To_Export,
                    Last_Dir,
                    Exported_Count,
                    Errors,
                )
                if not Continue_Export:
                    if Errors:
                        Warning_Message(self, "Error Exporting Figures", errors="\n".join(Errors))
                    if Exported_Count:
                        self.accept()
                    return

        if Missing:
            self.Refresh_Figure_Entries()
            Missing = self.Refresh_Request_Paths(Missing)
            Still_Missing = [
                f"{Entry['Title']} [{Entry['Variant_Label']}]"
                for Entry in Missing
                if not self.Path_Is_Ready(Entry.get("Src_Path"))
            ]
            if Still_Missing:
                Preview = Still_Missing[:12]
                if len(Still_Missing) > 12:
                    Preview.append(f"... and {len(Still_Missing) - 12} more")
                Errors.append("Some requested figures were not ready:\n" + "\n".join(Preview))

        if Errors:
            Warning_Message(self, "Error Exporting Figures", errors="\n".join(Errors))

        if Exported_Count:
            self.accept()
