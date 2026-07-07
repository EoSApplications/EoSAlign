# Load libraries
    # Load standard libraries
import os
import sys
from uuid import uuid4
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QLineEdit, QSizePolicy, QMessageBox, QCheckBox)
from Collapsible_Sections import Dropdown
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
    # Load local functions from local files
from Reference_Values_And_Units import Method_Units, Volume_Units
from Message_Manager import Warning_Message
from Session_Paths import get_session_directory, hide_path_from_file_explorer





# Create the enter data content
class Enter_Data(QWidget):
    def __init__(self, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Path=None, Parent=None):
        super().__init__(Parent)

        # Save the input parameters
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Setup the variables to be tracked
        self.Current_Mode = None
        self.Error_Propagation_Current_Mode = None
        self.Uploaded_File_Data = None
        self.Manual_Entry_Token = uuid4().hex[:8]
        self.Delete_Manual_Entry_Data_Files()

        # Create the enter data layout
        self.Create_The_Enter_Data_Display()

        # Connect all signals to their respective functions
        self.Connect_Signals()

        # If a path was passed in show the file upload option with the file content loaded
        if Path:
            self.Upload_File_Edit.setText(Path)
            self.Select_The_File_Upload_Option()


    # Get the default directory used when opening a file browser
    def Get_The_Default_Browse_Directory(self):

        # Prefer the desktop when it exists, otherwise fall back to the home directory
        Home_Directory = os.path.expanduser("~")
        Desktop_Directory = os.path.join(Home_Directory, "Desktop")

        if os.path.isdir(Desktop_Directory):
            return Desktop_Directory

        return Home_Directory


    # Get the root folder used for app-managed user data
    def Get_The_User_Data_Folder(self):

        # Match the location used for user-entered and user-edited calibration files
        if sys.platform == "win32":
            return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "EoS")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/EoS")
        elif sys.platform == "linux":
            return os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "EoS")
        else:
            return os.path.expanduser("~/.local/share/EoS")


    # Hide a file or folder from the file explorer when the platform supports it
    def Hide_A_Path_From_File_Explorer(self, Path):
        hide_path_from_file_explorer(Path)


    # Get the hidden folder used for manual entry data files
    def Get_The_Manual_Entry_Data_Folder(self):

        # Store these files in a per-session, per-widget folder so different windows
        # and runs never delete or overwrite each other's temp data files.
        Folder = get_session_directory(".Manual_Entry_Data_Files", self.Manual_Entry_Token)
        self.Hide_A_Path_From_File_Explorer(Folder)
        return str(Folder)


    # Delete any existing manual entry data files so they are recreated only when needed
    def Delete_Manual_Entry_Data_Files(self):

        # Remove only this widget's temp files from its dedicated folder.
        Folder = self.Get_The_Manual_Entry_Data_Folder()
        try:
            for Existing_Filename in os.listdir(Folder):
                Existing_File_Path = os.path.join(Folder, Existing_Filename)
                if not os.path.isfile(Existing_File_Path):
                    continue
                try:
                    os.remove(Existing_File_Path)
                except Exception:
                    pass
        except Exception:
            pass



    # Reset the enter data section to the initial state
    def Reset(self):

        # Reset the mode to nothing selected
        self.Current_Mode = None
        self.Error_Propagation_Current_Mode = None
        # Uncheck both mode buttons
        self.Manual_Entry_Button.setChecked(False)
        self.Upload_File_Button.setChecked(False)
        # Clear any saved file data
        self.Uploaded_File_Data = None
        self.Delete_Manual_Entry_Data_Files()
        # Clear the file path displays
        self.Upload_File_Edit.clear()
        self.Uncertainty_Upload_File_Edit.clear()
        # Clear the text boxes
        self.Manual_Entry_Text_Box.clear()
        self.Uncertainty_Text_Box.clear()
        # Reset the unit dropdowns to the placeholder
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)
        # Uncheck the error propagation checkbox
        self.Error_Propagation_Checkbox.setChecked(False)
        # Hide the data entry container until a button is clicked again
        self.Enter_Data_Layout.hide()
        # Hide the continue button until a layout is selected
        self.Continue_Button.hide()
        # Update the continue button state
        self.Enable_Or_Disable_The_Continue_Button()


    # Get the current entered data
    def Get_The_Current_Entered_Data(self, Save_Manual_Entry_Files=False):

        # Get the selected units
        Units = self.Get_The_Selected_Units()

        # Get the volume unit if the units are volume
        Volume_Unit = None
        if Units and "Volume" in Units:
            Volume_Unit = self.Volume_Unit_Dropdown.currentText() or None

        # If the data was entered from an uploaded file
        if self.Current_Mode == "Upload File":
            # Read the raw text from the file preview text box
            Raw_Data = self.File_Preview_Text_Box.toPlainText().strip()
            Source_Type = "Upload File"
        # If the data was manually entered
        else:
            # Read the raw text from the manual entry text box
            Raw_Data = self.Manual_Entry_Text_Box.toPlainText().strip()
            Source_Type = "Manual Entry"

        # Parse the values from the entered text
        Data = self.Get_Data_From_Text(Raw_Data)

        # Get the uncertainty data
        Uncertainty_Data = self.Get_The_Current_Uncertainty_Data(Save_Manual_Entry_Files)

        if Source_Type == "Upload File":
            File_Path = self.Upload_File_Edit.text()
        elif Save_Manual_Entry_Files:
            File_Path = self.Save_Data_To_A_Temporary_File(Raw_Data, "Manual_Entry_Data_File.txt")
        else:
            File_Path = None

        return {"Data": Data, "Units": Units, "Volume Unit": Volume_Unit, "Source Type": Source_Type, "Raw Data": Raw_Data, "File_Path": File_Path, "Error Propagation Enabled": self.Error_Propagation_Checkbox.isChecked(), "Uncertainty Data": Uncertainty_Data}


    # Get the current uncertainty data
    def Get_The_Current_Uncertainty_Data(self, Save_Manual_Entry_File=False):

        # If error propagation is disabled
        if not self.Error_Propagation_Checkbox.isChecked():
            return {"Error Propagation Enabled": False, "Error Propagation Source Type": None, "Error Propagation Values": [],  "Error Propagation Path": None}

        # If error propagation is enabled
        if self.Error_Propagation_Current_Mode == "Manual Entry":
            Raw_Uncertainty = self.Uncertainty_Text_Box.toPlainText().strip()
            if Save_Manual_Entry_File:
                Uncertainty_Path = self.Save_Data_To_A_Temporary_File(Raw_Uncertainty, "Uncertainty_Manual_Entry_File.txt")
            else:
                Uncertainty_Path = None
            return {"Error Propagation Enabled": True, "Error Propagation Source Type": "Manual Entry", "Error Propagation Values": self.Get_Data_From_Text(Raw_Uncertainty), "Error Propagation Path": Uncertainty_Path}
        elif self.Error_Propagation_Current_Mode == "Upload File":
            Path = self.Uncertainty_Upload_File_Edit.text()
            Raw_Uncertainty = self.Uncertainty_File_Preview_Text_Box.toPlainText().strip()
            return {"Error Propagation Enabled": True, "Error Propagation Source Type": "Upload File", "Error Propagation Values": self.Get_Data_From_Text(Raw_Uncertainty), "Error Propagation Path": Path}
        else:
            # No values entered for error propagation
            return {"Error Propagation Enabled": True, "Error Propagation Source Type": None, "Error Propagation Values": [], "Error Propagation Path": None}



    # Create the enter data display
    def Create_The_Enter_Data_Display(self):

        # Setup the enter data layout
        self.setObjectName("CollapsibleContent")
        Enter_Data_Display = QVBoxLayout(self)
        Enter_Data_Display.setContentsMargins(5, 5, 5, 5)
        Enter_Data_Display.setSpacing(8)

        # Create the button display
        Button_Layout = QHBoxLayout()

        # Create the button for selecting "Manual Entry"
        self.Manual_Entry_Button = QPushButton("Manual Entry")
        self.Manual_Entry_Button.setObjectName("ModeButton")
        self.Manual_Entry_Button.setCheckable(True)
        self.Manual_Entry_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Manual_Entry_Button.setFixedHeight(32)
        Button_Layout.addWidget(self.Manual_Entry_Button)

        # Add some space between the buttons
        Button_Layout.addSpacing(20)

        # Create the button for selecting "Upload File"
        self.Upload_File_Button = QPushButton("Upload File")
        self.Upload_File_Button.setObjectName("ModeButton")
        self.Upload_File_Button.setCheckable(True)
        self.Upload_File_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Upload_File_Button.setFixedHeight(32)
        Button_Layout.addWidget(self.Upload_File_Button)

        # Add the buttons to the main layout (above the data entry container)
        Enter_Data_Display.addLayout(Button_Layout)

        # Create the enter data layout
        self.Enter_Data_Layout = QWidget()
        self.Enter_Data_Layout.setObjectName("CollapsibleSubContainer")
        Enter_Data_Layout = QVBoxLayout(self.Enter_Data_Layout)
        Enter_Data_Layout.setContentsMargins(0, 0, 0, 0)
        Enter_Data_Layout.setSpacing(8)
        # Start hidden - only shown after a button is clicked
        self.Enter_Data_Layout.hide()
        Enter_Data_Display.addWidget(self.Enter_Data_Layout)

        # Create the display for the manual entry option
        self.Manual_Entry_Text_Box = QTextEdit()
        self.Manual_Entry_Text_Box.setObjectName("TextEdit")
        self.Manual_Entry_Text_Box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.Manual_Entry_Text_Box.setMinimumHeight(120)
        self.Manual_Entry_Text_Box.setMaximumHeight(200)
        # Add some text to the manual entry text box as a place holder
        self.Manual_Entry_Text_Box.setPlaceholderText("Enter your values here (one per line or comma/space separated)...")
        # Start with the text box hidden until a enter data method button is clicked
        self.Manual_Entry_Text_Box.hide()
        # Add the manual entry text box to the data entry container
        Enter_Data_Layout.addWidget(self.Manual_Entry_Text_Box)

        # Create the display for the upload file option
        Upload_File_Layout = QHBoxLayout()
        self.Upload_File_Edit = DraggableLineEdit()
        self.Upload_File_Edit.setObjectName("LineEdit")
        self.Upload_File_Edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # Add some text to the upload file text box as a place holder
        self.Upload_File_Edit.setPlaceholderText("Drop file here or enter path...")
        # Create the button for uploading a file
        self.Upload_File_Browse_Button = QPushButton("Browse")
        self.Upload_File_Browse_Button.setObjectName("Secondary_Button")
        self.Upload_File_Browse_Button.setMinimumWidth(100)
        self.Upload_File_Browse_Button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.Upload_File_Browse_Button.setFixedHeight(32)
        # Add the upload file browse button to the upload file display
        Upload_File_Layout.addWidget(self.Upload_File_Edit)
        Upload_File_Layout.addWidget(self.Upload_File_Browse_Button)
        # Wrap the upload file layout in a widget so it can be shown/hidden
        self.Upload_File_Widget = QWidget()
        self.Upload_File_Widget.setObjectName("Upload_File_Widget")
        self.Upload_File_Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.Upload_File_Widget.setLayout(Upload_File_Layout)
        # Start with the upload file option hidden
        self.Upload_File_Widget.hide()
        # Add the upload file display to the data entry container
        Enter_Data_Layout.addWidget(self.Upload_File_Widget)

        # Create the file preview text box (shown only after a file is selected)
        # This appears below the upload file path and browse button
        self.File_Preview_Text_Box = QTextEdit()
        self.File_Preview_Text_Box.setObjectName("TextEdit")
        self.File_Preview_Text_Box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.File_Preview_Text_Box.setMinimumHeight(120)
        self.File_Preview_Text_Box.setMaximumHeight(200)
        # Make the file preview text box read only
        self.File_Preview_Text_Box.setReadOnly(True)
        self.File_Preview_Text_Box.setPlaceholderText("File contents will appear here after a file is selected")
        # Start hidden until a file is selected
        self.File_Preview_Text_Box.hide()
        # Add the file preview text box below the upload file widget
        Enter_Data_Layout.addWidget(self.File_Preview_Text_Box)

        # Create the dropdown for selecting the units of the data
        Select_Units_Dropdown_Layout = QHBoxLayout()
        Units_Label = QLabel("Units:")
        Units_Label.setObjectName("CollapsibleContentLabel")
        Select_Units_Dropdown_Layout.addWidget(Units_Label)
        # Get a list of possible units from Math.Shorthand.Calibrations, sorted alphabetically
        List_Of_Units = sorted(Method_Units.values())
        self.Unit_Dropdown_Display = Dropdown()
        self.Unit_Dropdown_Display.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Unit_Dropdown_Display.setPlaceholderText("Select units...")
        # Add all units (pressure first, then the rest alphabetically)
        self.Unit_Dropdown_Display.addItem("Pressure (GPa)")
        for Unit_Option in List_Of_Units:
            self.Unit_Dropdown_Display.addItem(Unit_Option)
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        Select_Units_Dropdown_Layout.addWidget(self.Unit_Dropdown_Display, stretch=1)
        # Add the units dropdown to the data entry container (below the text box)
        Enter_Data_Layout.addLayout(Select_Units_Dropdown_Layout)

        # Create the dropdown for selecting the volume units
        self.Select_Volume_Unit_Display = QWidget()
        self.Select_Volume_Unit_Display.setObjectName("CollapsibleSubContainer")
        Select_Volume_Units_Dropdown_Layout = QHBoxLayout(self.Select_Volume_Unit_Display)
        Select_Volume_Units_Dropdown_Layout.setContentsMargins(0, 0, 0, 0)
        Volume_Units_Label = QLabel("Volume Units:")
        Volume_Units_Label.setObjectName("CollapsibleContentLabel")
        Select_Volume_Units_Dropdown_Layout.addWidget(Volume_Units_Label)
        # Get a list of possible volume units from Math.Shorthand.Calibrations
        List_Of_Volume_Units = Volume_Units
        self.Volume_Unit_Dropdown = Dropdown()
        self.Volume_Unit_Dropdown.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Volume_Unit_Dropdown.setPlaceholderText("Select volume units...")
        # Add all volume units to the list of options
        for Volume_Unit_Option in List_Of_Volume_Units:
            self.Volume_Unit_Dropdown.addItem(Volume_Unit_Option)
        # Set the dropdown to have no selection initially
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)
        Select_Volume_Units_Dropdown_Layout.addWidget(self.Volume_Unit_Dropdown, stretch=1)
        # Initially hide the volume units dropdown
        self.Select_Volume_Unit_Display.hide()
        # Add the volume units dropdown to the data entry container (below the units dropdown)
        Enter_Data_Layout.addWidget(self.Select_Volume_Unit_Display)

        # Create the error propagation checkbox
        self.Error_Propagation_Checkbox = QCheckBox("Enable Error Propagation")
        self.Error_Propagation_Checkbox.setObjectName("Checkbox")
        # Start with the error propagation disabled
        self.Error_Propagation_Checkbox.setChecked(False)
        # Add the error propagation checkbox to the data entry container (below the units dropdown or volume units dropdown if shown)
        Enter_Data_Layout.addWidget(self.Error_Propagation_Checkbox)

        # Create the enter uncertainty display
        self.Enter_Uncertainty_Display = QWidget()
        self.Enter_Uncertainty_Display.setObjectName("CollapsibleSubContainer")
        Enter_Uncertainty_Layout = QVBoxLayout(self.Enter_Uncertainty_Display)
        Enter_Uncertainty_Layout.setContentsMargins(0, 10, 0, 0)
        Enter_Uncertainty_Layout.setSpacing(5)

        # Create a label for the enter uncertainty display
        Uncertainty_Label = QLabel("Enter Measurement Uncertainties:")
        Uncertainty_Label.setObjectName("Settings_Text")
        Enter_Uncertainty_Layout.addWidget(Uncertainty_Label)

        # Create the uncertainty manual entry option layout
        self.Uncertainty_Text_Box = QTextEdit()
        self.Uncertainty_Text_Box.setObjectName("TextEdit")
        self.Uncertainty_Text_Box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.Uncertainty_Text_Box.setMinimumHeight(80)
        self.Uncertainty_Text_Box.setMaximumHeight(150)
        # Add some text to the uncertainty manual entry text box as a place holder
        self.Uncertainty_Text_Box.setPlaceholderText("Enter uncertainty values here (one per line or comma/space separated)...")
        # Start with the uncertainty text box hidden - shown based on the current data entry mode
        self.Uncertainty_Text_Box.hide()
        Enter_Uncertainty_Layout.addWidget(self.Uncertainty_Text_Box)

        # Create the uncertainty file upload option layout
        Uncertainty_Upload_File_Layout = QHBoxLayout()
        self.Uncertainty_Upload_File_Edit = DraggableLineEdit()
        self.Uncertainty_Upload_File_Edit.setObjectName("LineEdit")
        self.Uncertainty_Upload_File_Edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # Add some text to the uncertainty upload file text box as a place holder
        self.Uncertainty_Upload_File_Edit.setPlaceholderText("Drop uncertainty file here or enter path...")
        # Create the button for browsing for an uncertainty file
        self.Uncertainty_Upload_File_Browse_Button = QPushButton("Browse")
        self.Uncertainty_Upload_File_Browse_Button.setObjectName("Secondary_Button")
        self.Uncertainty_Upload_File_Browse_Button.setMinimumWidth(100)
        self.Uncertainty_Upload_File_Browse_Button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.Uncertainty_Upload_File_Browse_Button.setFixedHeight(32)
        # Add the uncertainty upload file browse button to the uncertainty upload file display
        Uncertainty_Upload_File_Layout.addWidget(self.Uncertainty_Upload_File_Edit)
        Uncertainty_Upload_File_Layout.addWidget(self.Uncertainty_Upload_File_Browse_Button)
        # Wrap the uncertainty upload file layout in a widget so it can be shown/hidden
        self.Uncertainty_Upload_File_Widget = QWidget()
        self.Uncertainty_Upload_File_Widget.setObjectName("Upload_File_Widget")
        self.Uncertainty_Upload_File_Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.Uncertainty_Upload_File_Widget.setLayout(Uncertainty_Upload_File_Layout)
        # Start with the uncertainty upload file option hidden
        self.Uncertainty_Upload_File_Widget.hide()
        Enter_Uncertainty_Layout.addWidget(self.Uncertainty_Upload_File_Widget)

        # Create the uncertainty file preview text box (shown only after a file is selected)
        self.Uncertainty_File_Preview_Text_Box = QTextEdit()
        self.Uncertainty_File_Preview_Text_Box.setObjectName("TextEdit")
        self.Uncertainty_File_Preview_Text_Box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.Uncertainty_File_Preview_Text_Box.setMinimumHeight(80)
        self.Uncertainty_File_Preview_Text_Box.setMaximumHeight(150)
        # Make the uncertainty file preview text box read only
        self.Uncertainty_File_Preview_Text_Box.setReadOnly(True)
        self.Uncertainty_File_Preview_Text_Box.setPlaceholderText("File contents will appear here after a file is selected")
        # Start hidden until a file is selected
        self.Uncertainty_File_Preview_Text_Box.hide()
        Enter_Uncertainty_Layout.addWidget(self.Uncertainty_File_Preview_Text_Box)

        # Start with the uncertainty container hidden until the enable error propagation checkbox is checked
        self.Enter_Uncertainty_Display.hide()
        Enter_Data_Layout.addWidget(self.Enter_Uncertainty_Display)

        # Create the continue button
        self.Continue_Button = QPushButton("Continue")
        self.Continue_Button.setObjectName("Primary_Button")
        self.Continue_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Start with the continue button disabled
        self.Continue_Button.setEnabled(False)
        self.Continue_Button.setFixedHeight(32)
        # Always start hidden — shown by the Manual Entry / Upload File buttons
        self.Continue_Button.hide()
        # Add the continue button to the main layout
        Enter_Data_Display.addWidget(self.Continue_Button)
        # Absorb any extra vertical space so the section doesn't grow blank
        Enter_Data_Display.addStretch()


    # Connect the text boxes and buttons to their functions
    def Connect_Signals(self):

        # Connect the unit dropdown to the input changed handler
        self.Unit_Dropdown_Display.currentIndexChanged.connect(self.When_Units_Changed)
        # Connect the volume unit dropdown to the input changed handler
        self.Volume_Unit_Dropdown.currentIndexChanged.connect(self.When_The_Input_Information_Changes)
        # Connect the manual entry text box to the input changed handler
        self.Manual_Entry_Text_Box.textChanged.connect(self.When_The_Input_Information_Changes)
        # Connect the manual entry button to the manual entry option
        self.Manual_Entry_Button.clicked.connect(self.Select_The_Manual_Entry_Option)
        # Connect the upload file button to the file upload option
        self.Upload_File_Button.clicked.connect(self.Select_The_File_Upload_Option)
        # Connect the browse button and drag and drop line edit to the file path handler
        self.Upload_File_Browse_Button.clicked.connect(self.When_Browse_Button_Clicked)
        # Connect the file path line edit to the file path changed handler
        self.Upload_File_Edit.textChanged.connect(self.When_The_File_Path_Is_Changed)
        # Connect the continue button to the continue button clicked handler
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)
        # Connect the error propagation checkbox to the uncertainty container visibility
        self.Error_Propagation_Checkbox.stateChanged.connect(self.When_Error_Propagation_Checkbox_Changed)
        # Connect the uncertainty manual entry text box to the input changed handler
        self.Uncertainty_Text_Box.textChanged.connect(self.When_The_Input_Information_Changes)
        # Connect the uncertainty browse button to the uncertainty browse button clicked handler
        self.Uncertainty_Upload_File_Browse_Button.clicked.connect(self.When_Uncertainty_Browse_Button_Clicked)
        # Connect the uncertainty file path line edit to the uncertainty file path changed handler
        self.Uncertainty_Upload_File_Edit.textChanged.connect(self.When_The_Uncertainty_File_Path_Is_Changed)


    # Show the manual entry layout and hide the file upload layout
    def Select_The_Manual_Entry_Option(self):

        # Show the data entry container now that a button has been clicked
        self.Enter_Data_Layout.show()
        # Update the current mode
        self.Current_Mode = "Manual Entry"
        self.Error_Propagation_Current_Mode = "Manual Entry"
        # Mark the active button
        self.Manual_Entry_Button.setChecked(True)
        self.Upload_File_Button.setChecked(False)
        # Show the manual entry text box
        self.Manual_Entry_Text_Box.show()
        self.Manual_Entry_Text_Box.setReadOnly(False)
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)

        # Hide the file upload widget and file preview text box
        self.Upload_File_Widget.hide()
        self.File_Preview_Text_Box.hide()
        # Clear the text box so manual entry starts fresh
        self.Manual_Entry_Text_Box.clear()

        # Show the uncertainty text box if error propagation is enabled
        if self.Error_Propagation_Checkbox.isChecked():
            # Show the uncertainty manual entry text box
            self.Uncertainty_Text_Box.show()
            # Allow users to edit the text box
            self.Uncertainty_Text_Box.setReadOnly(False)
            # Hide the uncertainty file upload layout
            self.Uncertainty_Upload_File_Widget.hide()
            self.Uncertainty_File_Preview_Text_Box.hide()

        # Show the continue button
        if self.Show_Continue_Button:
            self.Continue_Button.show()
        # Update the continue button state
        self.When_The_Input_Information_Changes()


    # Show the file upload layout and hide the manual entry layout
    def Select_The_File_Upload_Option(self):

        # Show the data entry container now that a button has been clicked
        self.Enter_Data_Layout.show()
        # Update the current mode
        self.Current_Mode = "Upload File"
        self.Error_Propagation_Current_Mode = "Upload File"
        # Mark the active button
        self.Upload_File_Button.setChecked(True)
        self.Manual_Entry_Button.setChecked(False)
        # Show the file upload widget
        self.Upload_File_Widget.show()
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)

        # Hide the manual entry text box
        self.Manual_Entry_Text_Box.hide()
        # Show the uncertainty file upload widget if error propagation is enabled
        if self.Error_Propagation_Checkbox.isChecked():
            # Show the uncertainty file upload layout
            self.Uncertainty_Upload_File_Widget.show()
            # Hide the uncertainty manual entry text box
            self.Uncertainty_Text_Box.hide()
            self.Uncertainty_File_Preview_Text_Box.hide()

        # Show the continue button now that a layout has been selected
        if self.Show_Continue_Button:
            self.Continue_Button.show()
        # Update the continue button state
        self.When_The_Input_Information_Changes()



    # When the units dropdown is changed, show or hide the volume unit dropdown and update the continue button state
    def When_Units_Changed(self):

        # Get the current units
        Units = self.Get_The_Selected_Units()

        # Check if the units are volume
        Is_Volume = Units is not None and "Volume" in Units
        # Show or hide the volume unit dropdown
        self.Select_Volume_Unit_Display.setVisible(Is_Volume)
        # Set the dropdown to have no selection initially
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)

        # Update the input information
        self.When_The_Input_Information_Changes()


    # When the error propagation checkbox is changed, show or hide the uncertainty entry options based on the current data entry mode and update the continue button state
    def When_Error_Propagation_Checkbox_Changed(self, State):

        # Check if the error propagation box is checked
        Is_Checked = State == Qt.Checked.value
        self.Enter_Uncertainty_Display.setVisible(Is_Checked)

        # Have the uncertainty entry options match the current data entry mode
        if Is_Checked and self.Current_Mode == "Manual Entry":
            # Show the uncertainty manual entry text box
            self.Uncertainty_Text_Box.show()
            # Allow users to edit the text box
            self.Uncertainty_Text_Box.setReadOnly(False)

            # Hide the uncertainty file upload layout
            self.Uncertainty_Upload_File_Widget.hide()
            self.Uncertainty_File_Preview_Text_Box.hide()

            # Update the current error propagation mode
            self.Error_Propagation_Current_Mode = "Manual Entry"


        elif Is_Checked and self.Current_Mode == "Upload File":
            # Show the uncertainty file upload layout
            self.Uncertainty_Upload_File_Widget.show()

            # Hide the uncertainty manual entry text box
            self.Uncertainty_Text_Box.hide()
            self.Uncertainty_File_Preview_Text_Box.hide()

            # Update the current error propagation mode
            self.Error_Propagation_Current_Mode = "Upload File"

        # Update the continue button state
        self.When_The_Input_Information_Changes()


    # When the browse button is clicked, open a file dialog to select a file and set the file path in the line edit
    def When_Browse_Button_Clicked(self):

        # Open a file dialog to load data
        Path, _ = QFileDialog.getOpenFileName(self, "Open Data File", self.Get_The_Default_Browse_Directory(), "Text files (*.txt *.csv *.dat);;All files (*)")

        # If a file was not selected, return early
        if not Path:
            return
        
        # Update the file path in the line edit
        self.Upload_File_Edit.setText(Path)


    # When the file path is changed, read the file and display the content in the file preview text box
    def When_The_File_Path_Is_Changed(self, Path):

        # If the path is empty, return early
        if not Path:
            return
        # Try to read the file
        try:
            Content = Read_Data_File_As_Text(Path)
            # Save the file data
            self.Uploaded_File_Data = Content
            # Show the file preview text box and display the file content
            self.File_Preview_Text_Box.setPlainText(Content)
            self.File_Preview_Text_Box.show()

        # If there is an error reading the file, show a warning message box
        except Exception as Error:
            Warning_Message(self, "Could Not Read The Entered Data File", error=Error)

        # Update the input information
        self.When_The_Input_Information_Changes()


    # When the uncertainty browse button is clicked, open a file dialog to select an uncertainty file and set the file path in the line edit
    def When_Uncertainty_Browse_Button_Clicked(self):

        # Open a file dialog to load data
        Path, _ = QFileDialog.getOpenFileName(self, "Open Data File", self.Get_The_Default_Browse_Directory(), "Text files (*.txt *.csv *.dat);;All files (*)")

        # If a file was not selected, return early
        if not Path:
            return
        
        # Update the file path in the line edit
        self.Uncertainty_Upload_File_Edit.setText(Path)


    # When the uncertainty file path is changed (either by browsing or drag and drop), read the file and display the content in the uncertainty file preview text box
    def When_The_Uncertainty_File_Path_Is_Changed(self, Path):

        # If the path is empty, return early
        if not Path:
            return
        # Try to read the file
        try:
            Content = Read_Data_File_As_Text(Path)
            # Show the uncertainty file preview text box and display the file content
            self.Uncertainty_File_Preview_Text_Box.setPlainText(Content)
            self.Uncertainty_File_Preview_Text_Box.show()

        # If there is an error reading the file, show a warning message box
        except Exception as Error:
            Warning_Message(self, "Could Not Read The Entered Uncertainty File", error=Error)

        # Update the input information
        self.When_The_Input_Information_Changes()


    # When any of the input information changes, update the continue button state and send out the selection if in All-at-Once mode and the data is acceptable
    def When_The_Input_Information_Changes(self):

        # Update the continue button state
        self.Enable_Or_Disable_The_Continue_Button()

        # Send out the entered data immediately when valid
        if not self.Show_Continue_Button and self.Check_If_The_Entered_Data_Is_Acceptable():
            self.Send_Out_Entered_Data()


    # When the continue button is clicked, run validation and send out the selection if valid
    def When_The_Continue_Button_Is_Clicked(self):

        # Run all validation checks and show warnings before emitting
        if self.Validate_And_Warn():
            self.Send_Out_Entered_Data()



    # Check if the entered data is acceptable and formatted correctly
    def Check_If_The_Entered_Data_Is_Acceptable(self):

        # Must have a mode selected
        if self.Current_Mode is None:
            return False
        # Must have valid units and at least one data value
        Selection = self.Get_The_Current_Entered_Data()
        if not Selection["Units"] or not Selection["Data"]:
            return False
        # If volume units are selected must also have a volume unit selected
        if Selection["Units"] and "Volume" in Selection["Units"]:
            if not Selection["Volume Unit"]:
                return False
        # If error propagation is enabled must have uncertainty data
        if self.Error_Propagation_Checkbox.isChecked():
            if self.Error_Propagation_Current_Mode is None:
                return False
            if not Selection["Uncertainty Data"]["Error Propagation Values"]:
                return False
        return True


    # Run validation checks and show warnings if any checks fail
    def Validate_And_Warn(self):

        # Check if a data entry method was selected
        if self.Current_Mode is None:
            Warning_Message(self, "Missing Data Entry Method")
            return False

        # Get the current selection
        Selection = self.Get_The_Current_Entered_Data()

        # Check if there are any data values
        if not Selection["Data"]:
            Warning_Message(self, "Missing Data Values")
            return False

        # Check if units were selected
        if not Selection["Units"]:
            Warning_Message(self, "Missing Units Selection")
            return False

        # Check if a volume unit was selected when volume units are selected
        if Selection["Units"] and "Volume" in Selection["Units"]:
            if not Selection["Volume Unit"]:
                Warning_Message(self, "Missing Volume Units Selection")
                return False

        # Check error propagation if it is enabled
        if self.Error_Propagation_Checkbox.isChecked():

            # Check if there are any uncertainty values
            Uncertainty = Selection["Uncertainty Data"]
            if not Uncertainty["Error Propagation Values"]:
                Warning_Message(self, "Missing Uncertainty Values")
                return False

            # Check if the data and uncertainty lengths match
            if len(Selection["Data"]) != len(Uncertainty["Error Propagation Values"]):
                Warning_Message(
                    self,
                    "Entered Data Length And Entered Uncertanty Length Do Not Match",
                    data_count=len(Selection["Data"]),
                    uncertainty_count=len(Uncertainty["Error Propagation Values"]),
                )
                return False

        return True



    # Get the selected units, returning None if no valid selection is made
    def Get_The_Selected_Units(self):

        # Return the selected units string, or None if placeholder is shown
        Units_Text = self.Unit_Dropdown_Display.currentText()

        if not Units_Text or Units_Text.startswith("--"):
            return None

        return Units_Text


    # Enable or disable the continue button based on whether the current entered data is acceptable
    def Enable_Or_Disable_The_Continue_Button(self):

        # Always enable the continue button so the error messages will be shown
        self.Continue_Button.setEnabled(True)


    # Emit the current selection through the callback
    def Send_Out_Entered_Data(self):

        # Fire the callback with the current selection
        if self.Once_A_Change_Is_Made:
            try:
                self.Once_A_Change_Is_Made(self.Get_The_Current_Entered_Data(Save_Manual_Entry_Files=True))
            except Exception as Error:
                Warning_Message(self, "Save File Error", error=str(Error))


    # Save the given text to a hidden app-managed file and return the file path
    def Save_Data_To_A_Temporary_File(self, Text, Filename="Manual_Entry_Data_File.txt"):

        # Save the file in the same user-data location used for user calibration files
        Folder = self.Get_The_Manual_Entry_Data_Folder()
        File_Path = os.path.join(Folder, Filename)
        Stem, Ext = os.path.splitext(Filename)
        Temporary_Path = os.path.join(Folder, f".{Stem}_{uuid4().hex}.tmp")

        # Write to a temporary file first, then swap it into place. If the previous
        # file is transiently locked, fall back to a fresh uniquely named file so
        # the current run can still proceed.
        with open(Temporary_Path, "w", encoding="utf-8") as Temp_File:
            Temp_File.write(Text)

        try:
            os.replace(Temporary_Path, File_Path)
            Final_Path = File_Path
        except PermissionError:
            Final_Path = os.path.join(Folder, f"{Stem}_{uuid4().hex[:8]}{Ext or '.txt'}")
            os.replace(Temporary_Path, Final_Path)
        except Exception:
            try:
                if os.path.exists(Temporary_Path):
                    os.remove(Temporary_Path)
            except Exception:
                pass
            raise

        self.Hide_A_Path_From_File_Explorer(Final_Path)
        return Final_Path


    # Parse a string of text into a list of float values, ignoring non-numeric tokens
    def Get_Data_From_Text(self, text):

        # Return an empty list if there is no text
        if not text:
            return []

        # Replace common delimiters with spaces
        for Char in [",", ";", "\t", "\n"]:
            text = text.replace(Char, " ")

        # Parse each token into a float, skipping non-numeric tokens
        Values = []
        for Token in text.split():
            Token = Token.strip()
            if not Token:
                continue
            try:
                Values.append(float(Token))
            except ValueError:
                continue

        return Values


    # Parse values from a file by reading the file content and using the Get_Data_From_Text function, returning an empty list if the file cannot be read
    def Get_Data_From_A_File(self, Path):

        # Return an empty list if there is no path or the file does not exist
        if not Path or not os.path.exists(Path):
            return []
        
        try:
            return Enter_Data.Get_Data_From_Text(Read_Data_File_As_Text(Path))
        except Exception:
            return []


# Read a text/csv/dat file and return its contents as a string.
# Uses utf-8-sig so that Windows BOM-encoded files don't corrupt the first token.
def Read_Data_File_As_Text(Path):
    try:
        with open(Path, "r", encoding="utf-8-sig") as File:
            return File.read()
    except UnicodeDecodeError:
        with open(Path, "r", encoding="latin-1") as File:
            return File.read()


# Enable a line edit to accept drag and drop of files
class DraggableLineEdit(QLineEdit):
    def __init__(self, Parent=None):
        super().__init__(Parent)
        self.setAcceptDrops(True)


    # When a file is dragged over the line edit, check if it contains a file path and accept the event if so
    def dragEnterEvent(self, Event: QDragEnterEvent):

        # Accept the drag event if it contains a file path
        if Event.mimeData().hasUrls():
            Event.acceptProposedAction()
        else:
            super().dragEnterEvent(Event)


    # When a file is dropped onto the line edit, get the file path and set it as the text of the line edit
    def dropEvent(self, Event: QDropEvent):

        # Get the file path from the dropped file
        File_Path = Event.mimeData().urls()
        if File_Path:
            # Set the text to the file path
            self.setText(File_Path[0].toLocalFile())
            Event.acceptProposedAction()

        else:
            super().dropEvent(Event)




