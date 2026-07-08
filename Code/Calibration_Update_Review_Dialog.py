# Load libraries
    # Load standard libraries
import urllib.request
    # Load third party libraries
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)
from PySide6.QtGui import QIcon

from Loading_Message import Get_Resource_Path




# Store the user agent used when fetching a single calibration file's content for preview
Preview_User_Agent = "EoSAlign-calibration-preview"


# Fetch one calibration file's raw text content in the background so the dialog never blocks on network I/O
class Calibration_File_Preview_Worker(QThread):
    content_ready = Signal(str, str)  # (Filename, File_Text)
    content_failed = Signal(str, str)  # (Filename, Error_Message)

    def __init__(self, Filename, File_Url):
        super().__init__()
        self.Filename = Filename
        self.File_Url = File_Url

    def run(self):
        try:
            Request = urllib.request.Request(self.File_Url, headers={"User-Agent": Preview_User_Agent})
            with urllib.request.urlopen(Request, timeout=15) as Response:
                File_Text = Response.read().decode('utf-8')
            self.content_ready.emit(self.Filename, File_Text)
        except Exception as exc:
            # The preview fetch failed (offline, rate limited, file removed, etc.)
            self.content_failed.emit(self.Filename, str(exc))



# Let the user review, preview, and select which changed calibration files to actually download
class Calibration_Update_Review_Dialog(QDialog):

    def __init__(self, Parent, Changed_Files, Raw_Base_Url):
        super().__init__(Parent)
        # Give this dialog a full window title bar with minimize, maximize, and close buttons
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("Calibration Updates Available")
        self.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
        self.resize(700, 450)

        self.Changed_Files = Changed_Files
        self.Raw_Base_Url = Raw_Base_Url
        # Cache each fetched preview so re-selecting a file does not re-fetch it
        self.Preview_Text_By_Filename = {}
        # Keep a reference to the active preview fetch so it is not garbage collected mid-fetch
        self.Active_Preview_Worker = None

        self.Build_UI()
        self.Has_Shown_Once = False


    # Show without a white flash by appearing off-screen first
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


    # Build the list-of-changed-files-plus-preview layout
    def Build_UI(self):

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(16, 16, 16, 16)
        Layout.setSpacing(10)

        File_Count = len(self.Changed_Files)
        Instruction = QLabel(
            f"{File_Count} calibration file(s) have been added or updated.\n"
            "Select a file below to preview its contents. Only checked files will be downloaded."
        )
        Instruction.setWordWrap(True)
        Layout.addWidget(Instruction)

        Splitter = QSplitter(Qt.Horizontal)

        # Left side -- one checkable row per changed file
        self.File_List = QListWidget()
        self.Checked_Items_By_Filename = {}
        for Filename in sorted(self.Changed_Files):
            Item = QListWidgetItem(Filename)
            Item.setFlags(Item.flags() | Qt.ItemIsUserCheckable)
            Item.setCheckState(Qt.Checked)
            self.File_List.addItem(Item)
            self.Checked_Items_By_Filename[Filename] = Item
        self.File_List.currentItemChanged.connect(self.When_Selected_File_Changed)
        Splitter.addWidget(self.File_List)

        # Right side -- read-only raw-text preview of whichever file is selected
        self.Preview_Display = QTextBrowser()
        self.Preview_Display.setObjectName("SettingsText")
        # Match the monospace styling the calibration file editor already uses for YAML content
        self.Preview_Display.setStyleSheet("* { font-family: 'Noto Mono', monospace; }")
        self.Preview_Display.setPlaceholderText("Select a file on the left to preview its contents.")
        Splitter.addWidget(self.Preview_Display)

        Splitter.setStretchFactor(0, 1)
        Splitter.setStretchFactor(1, 2)
        Layout.addWidget(Splitter)

        # Preselect the first file so the dialog never opens with an empty preview
        if self.File_List.count() > 0:
            self.File_List.setCurrentRow(0)

        Bottom_Line = QFrame()
        Bottom_Line.setFrameShape(QFrame.HLine)
        Bottom_Line.setFrameShadow(QFrame.Sunken)
        Layout.addWidget(Bottom_Line)

        self.Suppress_Notifications_Checkbox = QCheckBox("Do not show this message again")
        Layout.addWidget(self.Suppress_Notifications_Checkbox)

        Action_Row = QHBoxLayout()
        Action_Row.addStretch()

        Download_Button = QPushButton("Download Selected")
        Download_Button.setObjectName("Primary_Button")
        Download_Button.setFixedHeight(32)
        Download_Button.clicked.connect(self.accept)
        Action_Row.addWidget(Download_Button)

        Cancel_Button = QPushButton("Cancel")
        Cancel_Button.setObjectName("Secondary_Button")
        Cancel_Button.setFixedHeight(32)
        Cancel_Button.clicked.connect(self.reject)
        Action_Row.addWidget(Cancel_Button)

        Layout.addLayout(Action_Row)


    # Fetch and show the selected file's contents, using a cached copy when already fetched
    def When_Selected_File_Changed(self, Current_Item, Previous_Item):

        # Nothing to preview when the list is empty or selection was cleared
        if Current_Item is None:
            return

        Filename = Current_Item.text()

        # Show a cached preview instantly instead of re-fetching it
        if Filename in self.Preview_Text_By_Filename:
            self.Preview_Display.setPlainText(self.Preview_Text_By_Filename[Filename])
            return

        self.Preview_Display.setPlainText("Loading preview...")
        File_Url = f"{self.Raw_Base_Url}/{Filename}"
        Worker = Calibration_File_Preview_Worker(Filename, File_Url)
        self.Active_Preview_Worker = Worker
        Worker.content_ready.connect(self.On_Preview_Content_Ready)
        Worker.content_failed.connect(self.On_Preview_Content_Failed)
        Worker.start()


    # Cache and display a successfully fetched preview
    def On_Preview_Content_Ready(self, Filename, File_Text):

        self.Preview_Text_By_Filename[Filename] = File_Text

        # Only update the display if the user has not already selected a different file
        Current_Item = self.File_List.currentItem()
        if Current_Item is not None and Current_Item.text() == Filename:
            self.Preview_Display.setPlainText(File_Text)


    # Show an error message in place of the preview when a fetch fails
    def On_Preview_Content_Failed(self, Filename, Error_Message):

        Current_Item = self.File_List.currentItem()
        if Current_Item is not None and Current_Item.text() == Filename:
            self.Preview_Display.setPlainText(f"Could not load preview:\n{Error_Message}")


    # Find every filename the user left checked
    def Get_Approved_Filenames(self):

        Approved_Filenames = [
            Filename for Filename, Item in self.Checked_Items_By_Filename.items()
            if Item.checkState() == Qt.Checked
        ]

        # Return the filenames the user approved for download
        return Approved_Filenames


    # Check whether the user asked to stop seeing calibration update notifications
    def Get_Suppress_Notifications_Checked(self):

        # Return whether the "do not show this message again" checkbox was checked
        return self.Suppress_Notifications_Checkbox.isChecked()



