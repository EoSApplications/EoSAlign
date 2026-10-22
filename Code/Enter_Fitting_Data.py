# Load libraries
    # Load standard libraries
import os
import re
    # Load third party libraries
import numpy as np
from shiboken6 import isValid
from PySide6.QtCore import Signal, QEvent, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFileDialog, QHeaderView, QSizePolicy, QTableWidgetItem)
    # Load local functions from local files
from Collapsible_Sections import Dropdown
from Enter_Data import DraggableLineEdit, Read_Data_File_As_Text
from Message_Manager import Warning_Message
from Fitting_Data_File import Read_Columns_From_Text, Get_Column_Labels, Fitting_Data_File_Error
from Fitting_Data_Table import Fitting_Data_Table
from Fitting_Display_Helpers import Make_Secondary_Button, Make_A_Spacer, Group_Space
from Reference_Values_And_Units import Method_Units, Volume_Units
from Fitting_Models_And_Units import Get_Method_For_Unit





# The number of rows the tables start with and the number added at a time
Starting_Number_Of_Rows = 5
Number_Of_Rows_To_Add = 5

# The four values of the data, in the order of the table columns. The two uncertainties are only used when error propagation is enabled
Target_Names = {0: "Measurement", 1: "Measurement Uncertainty", 2: "Pressure (GPa)", 3: "Pressure (GPa) Uncertainty"}
Uncertainty_Columns = (1, 3)





# Get the abbreviation of a unit: a volume unit is only its abbreviation and other units have it in parentheses, e.g. "Wavelength (nm)"
def Get_Unit_Abbreviation(Unit):

    if Unit in Volume_Units:
        return Unit
    Match = re.search(r"\(([^)]*)\)\s*$", Unit)

    return Match.group(1) if Match else Unit





# The height of the row of column dropdowns when every name fits on one line (px)
Minimum_Row_Height = 32



# A row of dropdowns that line up with the columns of a table, so each dropdown sits above the column it chooses
class Column_Dropdown_Row(QWidget):
    def __init__(self, Table, Parent=None):
        super().__init__(Parent)

        self.Table = Table
        self.setFixedHeight(Minimum_Row_Height)
        # One dropdown for each column of the table
        self.Dropdowns = []
        for Column in range(Table.columnCount()):
            Column_Dropdown = Dropdown(self)
            Column_Dropdown.setObjectName("Dropdown")
            Column_Dropdown.setPlaceholderText("Select column...")
            # The column names come from the header of the file, so they can be long: show the whole name on more lines
            # instead of cutting it off, and make the row as tall as the tallest one (see Line_Up_With_The_Table)
            Column_Dropdown.Set_Wrap_Selected_Text(True)
            Column_Dropdown.currentTextChanged.connect(lambda _=None: self.Line_Up_With_The_Table())
            self.Dropdowns.append(Column_Dropdown)
        # Line up again whenever the table changes size or its columns are shown or hidden
        Table.installEventFilter(self)
        Table.horizontalHeader().sectionResized.connect(self.Line_Up_With_The_Table)
        Table.horizontalHeader().geometriesChanged.connect(self.Line_Up_With_The_Table)


    def eventFilter(self, Watched_Object, Event):

        if Watched_Object is self.Table and Event.type() in (QEvent.Resize, QEvent.Show, QEvent.LayoutRequest):
            QTimer.singleShot(0, self.Line_Up_With_The_Table)

        return False


    # Put each dropdown above its column, and hide the dropdowns of hidden columns
    def Line_Up_With_The_Table(self):

        # The table may already be deleted when its section is removed
        if not isValid(self.Table):
            return
        Header = self.Table.horizontalHeader()
        Left = self.Table.verticalHeader().width() + self.Table.frameWidth()
        # The row is as tall as the tallest wrapped column name, and never shorter than a one line dropdown
        Widths = {Column: max(Header.sectionSize(Column) - 4, 20) for Column in range(len(self.Dropdowns)) if not self.Table.isColumnHidden(Column)}
        Row_Height = max([Minimum_Row_Height] + [self.Dropdowns[Column].heightForWidth(Width) if self.Dropdowns[Column].hasHeightForWidth() else 0 for Column, Width in Widths.items()])
        if Row_Height != self.height():
            self.setFixedHeight(Row_Height)
        for Column, Column_Dropdown in enumerate(self.Dropdowns):
            if Column not in Widths:
                Column_Dropdown.hide()
                continue
            Column_Dropdown.setGeometry(Left + Header.sectionViewportPosition(Column) + 2, 0, Widths[Column], Row_Height)
            Column_Dropdown.show()





# Create the enter fitting data content
class Enter_Fitting_Data(QWidget):

    # Emitted with the new units (an empty string if none are selected) when the units are changed
    Units_Changed = Signal(str)

    def __init__(self, *, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Setup the variables to be tracked
        self.Current_Mode = None
        # How an uploaded file is used: "One File" or "Multiple Files"
        self.Upload_Layout = None
        # The files that have been loaded: "One" for the single file, or the number of the value for multiple files
        self.Loaded_Files = {}

        # Create the enter fitting data display
        self.Create_The_Enter_Fitting_Data_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the enter fitting data section to its initial state
    def Reset(self):

        # Reset the mode to nothing selected
        self.Current_Mode = None
        self.Manual_Entry_Button.setChecked(False)
        self.Upload_File_Button.setChecked(False)
        # Clear the table and the uploaded files
        self.Clear_The_Manual_Entry_Table()
        self.Clear_The_Uploaded_Files()
        self.Upload_Layout = None
        self.One_File_Button.setChecked(False)
        self.Multiple_Files_Button.setChecked(False)
        self.Space_After_Upload_Options.hide()
        self.One_File_Widget.hide()
        self.Multiple_Files_Widget.hide()
        # Reset the units to the placeholder
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        # Hide the data entry container until a button is clicked again
        self.Enter_Data_Layout.hide()
        self.Show_Or_Hide_The_Continue_Button(False)



    # Get the selected units, or None if the units are not completely selected
    # When volume is selected the units are the selected volume unit
    def Get_The_Selected_Units(self):

        if self.Unit_Dropdown_Display.currentIndex() < 0:
            return None
        Units_Text = self.Unit_Dropdown_Display.currentText()
        if Method_Units.get("XRD") == Units_Text:
            if self.Volume_Unit_Dropdown.currentIndex() < 0:
                return None
            return self.Volume_Unit_Dropdown.currentText() or None

        return Units_Text or None


    # Check if volume is selected as the units
    def Volume_Is_Selected(self):

        return self.Unit_Dropdown_Display.currentIndex() >= 0 and self.Unit_Dropdown_Display.currentText() == Method_Units.get("XRD")



    # Get the measurement method for the currently selected units, or None if no units are selected
    def Get_Current_Method(self):

        return Get_Method_For_Unit(self.Get_The_Selected_Units())


    # Show or hide the continue button and the space above it
    def Show_Or_Hide_The_Continue_Button(self, Visible):

        self.Continue_Button.setVisible(Visible)
        self.Space_Before_Continue_Button.setVisible(Visible)


    # Get the numbers of the values that are used: the uncertainties are only used when error propagation is enabled
    def Get_The_Used_Targets(self):

        return [0, 1, 2, 3] if self.Error_Propagation_Checkbox.isChecked() else [0, 2]



    # Create the enter fitting data display
    def Create_The_Enter_Fitting_Data_Display(self):

        # Setup the enter fitting data layout
        self.setObjectName("CollapsibleContent")
        Enter_Fitting_Data_Display = QVBoxLayout(self)
        Enter_Fitting_Data_Display.setContentsMargins(5, 5, 5, 5)
        Enter_Fitting_Data_Display.setSpacing(8)

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
        Enter_Fitting_Data_Display.addLayout(Button_Layout)

        # Create the enter data layout
        self.Enter_Data_Layout = QWidget()
        self.Enter_Data_Layout.setObjectName("CollapsibleSubContainer")
        Enter_Data_Layout = QVBoxLayout(self.Enter_Data_Layout)
        Enter_Data_Layout.setContentsMargins(0, 0, 0, 0)
        Enter_Data_Layout.setSpacing(8)
        # Start hidden - only shown after a button is clicked
        self.Enter_Data_Layout.hide()
        Enter_Fitting_Data_Display.addWidget(self.Enter_Data_Layout)

        # Create the display for the manual entry option: the table and the button that adds rows
        self.Manual_Entry_Widget = QWidget()
        self.Manual_Entry_Widget.setObjectName("CollapsibleSubContainer")
        Manual_Entry_Layout = QVBoxLayout(self.Manual_Entry_Widget)
        Manual_Entry_Layout.setContentsMargins(0, 0, 0, 0)
        Manual_Entry_Layout.setSpacing(8)
        self.Data_Table = self.Make_A_Data_Table(Read_Only=False)
        Manual_Entry_Layout.addWidget(self.Data_Table)
        Add_Rows_Layout = QHBoxLayout()
        Add_Rows_Layout.addStretch()
        self.Add_Rows_Button = Make_Secondary_Button(f"+ {Number_Of_Rows_To_Add} Rows")
        Add_Rows_Layout.addWidget(self.Add_Rows_Button)
        Add_Rows_Layout.addStretch()
        Manual_Entry_Layout.addLayout(Add_Rows_Layout)
        # Start with the manual entry option hidden until a enter data method button is clicked
        self.Manual_Entry_Widget.hide()
        Enter_Data_Layout.addWidget(self.Manual_Entry_Widget)

        # Create the display for the upload file option
        self.Upload_Widget = QWidget()
        self.Upload_Widget.setObjectName("CollapsibleSubContainer")
        Upload_Layout = QVBoxLayout(self.Upload_Widget)
        # Leave 5 times the usual space (8 px) above the one file and multiple files buttons, on top of the space already there
        Upload_Layout.setContentsMargins(0, Group_Space - 8, 0, 0)
        Upload_Layout.setSpacing(8)
        # Create the buttons for choosing whether the values are in one file or in multiple files
        # They are the middle half of the Manual Entry and Upload File buttons: each is half the width of the button above it and
        # they have the same space between them, so the outer half of each button is cut off
        Upload_Option_Layout = QHBoxLayout()
        Upload_Option_Layout.addStretch(1)
        self.One_File_Button = QPushButton("One File")
        self.One_File_Button.setObjectName("ModeButtonSecondary")
        self.One_File_Button.setCheckable(True)
        self.One_File_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.One_File_Button.setFixedHeight(32)
        Upload_Option_Layout.addWidget(self.One_File_Button, 1)
        Upload_Option_Layout.addSpacing(20)
        self.Multiple_Files_Button = QPushButton("Multiple Files")
        self.Multiple_Files_Button.setObjectName("ModeButtonSecondary")
        self.Multiple_Files_Button.setCheckable(True)
        self.Multiple_Files_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Multiple_Files_Button.setFixedHeight(32)
        Upload_Option_Layout.addWidget(self.Multiple_Files_Button, 1)
        Upload_Option_Layout.addStretch(1)
        Upload_Layout.addLayout(Upload_Option_Layout)
        # Leave space between the buttons and the files; it is shown once an option has been chosen
        self.Space_After_Upload_Options = Make_A_Spacer()
        self.Space_After_Upload_Options.hide()
        Upload_Layout.addWidget(self.Space_After_Upload_Options)
        # Create the display for one file
        self.One_File_Widget = QWidget()
        self.One_File_Widget.setObjectName("CollapsibleSubContainer")
        One_File_Layout = QVBoxLayout(self.One_File_Widget)
        One_File_Layout.setContentsMargins(0, 0, 0, 0)
        One_File_Layout.setSpacing(8)
        One_File_Source_Row = self.Make_A_File_Source_Row("One", Label_Text=None)
        One_File_Layout.addWidget(One_File_Source_Row)
        self.One_File_Widget.hide()
        Upload_Layout.addWidget(self.One_File_Widget)
        # Create the display for multiple files: a file and the column to use for each value
        self.Multiple_Files_Widget = QWidget()
        self.Multiple_Files_Widget.setObjectName("CollapsibleSubContainer")
        Multiple_Files_Layout = QVBoxLayout(self.Multiple_Files_Widget)
        Multiple_Files_Layout.setContentsMargins(0, 0, 0, 0)
        Multiple_Files_Layout.setSpacing(8)
        self.Source_Rows = {}
        for Target in Target_Names:
            self.Source_Rows[Target] = self.Make_A_File_Source_Row(Target, Label_Text=f"{Target_Names[Target]}:")
            Multiple_Files_Layout.addWidget(self.Source_Rows[Target])
        self.Multiple_Files_Widget.hide()
        Upload_Layout.addWidget(self.Multiple_Files_Widget)
        # Leave space between the files and the table; it is shown with the table
        self.Space_Before_Preview = Make_A_Spacer()
        self.Space_Before_Preview.hide()
        Upload_Layout.addWidget(self.Space_Before_Preview)
        # Create the preview table, which shows the data that will be used and cannot be edited
        self.Preview_Table = self.Make_A_Data_Table(Read_Only=True)
        # For one file the column of the file for each value is chosen in a row of dropdowns above the table
        self.Column_Choice_Row = Column_Dropdown_Row(self.Preview_Table)
        self.Column_Choice_Row.hide()
        Upload_Layout.addWidget(self.Column_Choice_Row)
        Upload_Layout.addWidget(self.Preview_Table)
        self.Preview_Table.hide()
        # Start with the upload file option hidden
        self.Upload_Widget.hide()
        Enter_Data_Layout.addWidget(self.Upload_Widget)

        # Leave space between the data and the units
        Enter_Data_Layout.addWidget(Make_A_Spacer())

        # Create the dropdown for selecting the units of the data
        Select_Units_Dropdown_Layout = QHBoxLayout()
        Units_Label = QLabel("Units:")
        Units_Label.setObjectName("CollapsibleContentLabel")
        Select_Units_Dropdown_Layout.addWidget(Units_Label)
        self.Unit_Dropdown_Display = Dropdown()
        self.Unit_Dropdown_Display.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Unit_Dropdown_Display.setPlaceholderText("Select units...")
        # Add all units alphabetically
        for Unit_Option in sorted(Method_Units.values()):
            self.Unit_Dropdown_Display.addItem(Unit_Option)
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        Select_Units_Dropdown_Layout.addWidget(self.Unit_Dropdown_Display, stretch=1)
        # Add the units dropdown to the data entry container (below the data)
        Enter_Data_Layout.addLayout(Select_Units_Dropdown_Layout)

        # Create the dropdown for selecting the volume units
        self.Select_Volume_Unit_Display = QWidget()
        self.Select_Volume_Unit_Display.setObjectName("CollapsibleSubContainer")
        Select_Volume_Units_Dropdown_Layout = QHBoxLayout(self.Select_Volume_Unit_Display)
        Select_Volume_Units_Dropdown_Layout.setContentsMargins(0, 0, 0, 0)
        Volume_Units_Label = QLabel("Volume Units:")
        Volume_Units_Label.setObjectName("CollapsibleContentLabel")
        Select_Volume_Units_Dropdown_Layout.addWidget(Volume_Units_Label)
        self.Volume_Unit_Dropdown = Dropdown()
        self.Volume_Unit_Dropdown.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Volume_Unit_Dropdown.setPlaceholderText("Select volume units...")
        for Volume_Unit_Option in Volume_Units:
            self.Volume_Unit_Dropdown.addItem(Volume_Unit_Option)
        # Set the dropdown to have no selection initially
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)
        Select_Volume_Units_Dropdown_Layout.addWidget(self.Volume_Unit_Dropdown, stretch=1)
        # Initially hide the volume units dropdown
        self.Select_Volume_Unit_Display.hide()
        Enter_Data_Layout.addWidget(self.Select_Volume_Unit_Display)

        # Leave space between the units and error propagation
        Enter_Data_Layout.addWidget(Make_A_Spacer())

        # Create the error propagation checkbox, which adds the uncertainty columns
        self.Error_Propagation_Checkbox = QCheckBox("Enable Error Propagation")
        self.Error_Propagation_Checkbox.setObjectName("Checkbox")
        # Start with the error propagation disabled
        self.Error_Propagation_Checkbox.setChecked(False)
        Enter_Data_Layout.addWidget(self.Error_Propagation_Checkbox)
        # Label the table columns and show only the columns that are needed
        self.Set_The_Column_Headers()
        self.Show_Or_Hide_The_Uncertainty_Columns()

        # Leave space above the continue button; it is shown with the continue button
        self.Space_Before_Continue_Button = Make_A_Spacer()
        self.Space_Before_Continue_Button.hide()
        Enter_Fitting_Data_Display.addWidget(self.Space_Before_Continue_Button)
        # Create the continue button
        self.Continue_Button = QPushButton("Continue")
        self.Continue_Button.setObjectName("Primary_Button")
        self.Continue_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Continue_Button.setFixedHeight(32)
        # Always start hidden - shown by the Manual Entry / Upload File buttons
        self.Continue_Button.hide()
        Enter_Fitting_Data_Display.addWidget(self.Continue_Button)
        # Absorb any extra vertical space so the section doesn't grow blank
        Enter_Fitting_Data_Display.addStretch()


    # Make a table with the four columns of the data
    def Make_A_Data_Table(self, Read_Only):

        Table = Fitting_Data_Table(Starting_Number_Of_Rows, 4, Read_Only=Read_Only)
        Table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        Table.setMinimumHeight(220)
        Table.setMaximumHeight(350)

        return Table


    # Make a row for choosing a file and the column of the file to use
    # Target is "One" for the single file, or the number of the value the file is for
    def Make_A_File_Source_Row(self, Target, Label_Text):

        Row = QWidget()
        Row.setObjectName("CollapsibleSubContainer")
        Row_Layout = QHBoxLayout(Row)
        Row_Layout.setContentsMargins(0, 0, 0, 0)
        Row_Layout.setSpacing(8)
        # Label the value the file is for
        if Label_Text:
            Label = QLabel(Label_Text)
            Label.setObjectName("CollapsibleContentLabel")
            Label.setMinimumWidth(230)
            Row_Layout.addWidget(Label)
        # The file path, which also accepts a dropped file
        File_Edit = DraggableLineEdit()
        File_Edit.setObjectName("LineEdit")
        File_Edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        File_Edit.setPlaceholderText("Drop file here or enter path...")
        Row_Layout.addWidget(File_Edit, stretch=1)
        # The button for choosing a file
        Browse_Button = Make_Secondary_Button("Browse")
        Row_Layout.addWidget(Browse_Button)
        # The column of the file to use for this value
        if Target != "One":
            Column_Dropdown = Dropdown()
            Column_Dropdown.setObjectName("Dropdown")
            Column_Dropdown.setPlaceholderText("Select column...")
            Column_Dropdown.setMinimumWidth(190)
            # The column names come from the header of the file, so they can be long: show the whole name on more lines
            Column_Dropdown.Set_Wrap_Selected_Text(True)
            Row_Layout.addWidget(Column_Dropdown)
            Column_Dropdown.currentIndexChanged.connect(self.Update_The_Preview_Table)
        else:
            Column_Dropdown = None
        # Keep the widgets so they can be connected and read
        Row.File_Edit = File_Edit
        Row.Browse_Button = Browse_Button
        Row.Column_Dropdown = Column_Dropdown
        Row.Target = Target

        return Row



    # Connect the buttons and inputs to their functions
    def Connect_Signals(self):

        # Connect the manual entry button to the manual entry option
        self.Manual_Entry_Button.clicked.connect(self.Select_The_Manual_Entry_Option)
        # Connect the upload file button to the file upload option
        self.Upload_File_Button.clicked.connect(self.Select_The_File_Upload_Option)
        # Connect the one file and multiple files buttons to their options
        self.One_File_Button.clicked.connect(self.Select_The_One_File_Option)
        self.Multiple_Files_Button.clicked.connect(self.Select_The_Multiple_Files_Option)
        # Connect the add rows button to adding rows
        self.Add_Rows_Button.clicked.connect(self.Add_Rows_To_The_Table)
        # Connect each file row to choosing and loading a file
        for Source_Row in self.Get_All_Source_Rows():
            Source_Row.Browse_Button.clicked.connect(lambda _=False, Row=Source_Row: self.When_Browse_Button_Clicked(Row))
            Source_Row.File_Edit.textChanged.connect(lambda Path, Row=Source_Row: self.When_The_File_Path_Is_Changed(Row, Path))
        # Connect the column choices of the one file to the preview
        for Column_Dropdown in self.Column_Choice_Row.Dropdowns:
            Column_Dropdown.currentIndexChanged.connect(self.Update_The_Preview_Table)
        # Connect the unit dropdowns to the units changed handlers
        self.Unit_Dropdown_Display.currentIndexChanged.connect(self.When_The_Unit_Type_Changes)
        self.Volume_Unit_Dropdown.currentIndexChanged.connect(self.When_Units_Changed)
        # Connect the error propagation checkbox to the uncertainty columns
        self.Error_Propagation_Checkbox.stateChanged.connect(self.When_Error_Propagation_Checkbox_Changed)
        # Connect the continue button to the continue button clicked handler
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)


    # Get the row for the single file and the rows for each value of multiple files
    def Get_All_Source_Rows(self):

        return [self.One_File_Widget.layout().itemAt(0).widget()] + list(self.Source_Rows.values())



    # Show the manual entry layout and hide the file upload layout
    def Select_The_Manual_Entry_Option(self):

        # Choosing the option that is already selected changes nothing
        if self.Current_Mode == "Manual Entry":
            self.Manual_Entry_Button.setChecked(True)
            return
        # Show the data entry container now that a button has been clicked
        self.Enter_Data_Layout.show()
        # Update the current mode
        self.Current_Mode = "Manual Entry"
        # Mark the active button
        self.Manual_Entry_Button.setChecked(True)
        self.Upload_File_Button.setChecked(False)
        # Show the manual entry table, which starts fresh
        self.Clear_The_Manual_Entry_Table()
        self.Manual_Entry_Widget.show()
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        # Hide the file upload widget
        self.Upload_Widget.hide()
        # Show the continue button
        if self.Show_Continue_Button:
            self.Show_Or_Hide_The_Continue_Button(True)


    # Show the file upload layout and hide the manual entry layout
    def Select_The_File_Upload_Option(self):

        # Choosing the option that is already selected changes nothing
        if self.Current_Mode == "Upload File":
            self.Upload_File_Button.setChecked(True)
            return
        # Show the data entry container now that a button has been clicked
        self.Enter_Data_Layout.show()
        # Update the current mode
        self.Current_Mode = "Upload File"
        # Mark the active button
        self.Upload_File_Button.setChecked(True)
        self.Manual_Entry_Button.setChecked(False)
        # Show the file upload widget, which starts by asking whether the values are in one file or in multiple files
        self.Upload_Widget.show()
        # Set the dropdown to have no selection initially
        self.Unit_Dropdown_Display.setCurrentIndex(-1)
        # Hide the manual entry table
        self.Manual_Entry_Widget.hide()
        # Show the continue button now that a layout has been selected
        if self.Show_Continue_Button:
            self.Show_Or_Hide_The_Continue_Button(True)


    # Choose one file that has all the values
    def Select_The_One_File_Option(self):

        # Choosing the option that is already selected changes nothing
        if self.Upload_Layout == "One File":
            self.One_File_Button.setChecked(True)
            return
        self.Start_A_New_Upload_Layout("One File")
        self.One_File_Button.setChecked(True)
        self.Multiple_Files_Button.setChecked(False)
        self.One_File_Widget.show()
        self.Multiple_Files_Widget.hide()
        self.Space_After_Upload_Options.show()
        # The column choices appear once a file has been loaded
        self.Update_The_Preview_Table()


    # Choose a file for each value
    def Select_The_Multiple_Files_Option(self):

        # Choosing the option that is already selected changes nothing
        if self.Upload_Layout == "Multiple Files":
            self.Multiple_Files_Button.setChecked(True)
            return
        self.Start_A_New_Upload_Layout("Multiple Files")
        self.Multiple_Files_Button.setChecked(True)
        self.One_File_Button.setChecked(False)
        self.Multiple_Files_Widget.show()
        self.One_File_Widget.hide()
        self.Space_After_Upload_Options.show()
        self.Column_Choice_Row.hide()
        self.Show_Or_Hide_The_Uncertainty_Columns()


    # Start over with the files when the way the files are used changes
    def Start_A_New_Upload_Layout(self, Upload_Layout):

        self.Clear_The_Uploaded_Files()
        self.Upload_Layout = Upload_Layout
        self.Preview_Table.hide()



    # Label the columns of the tables, with the abbreviation of the selected units on the measurement columns
    def Set_The_Column_Headers(self):

        Units = self.Get_The_Selected_Units()
        Unit_Text = f"\n({Get_Unit_Abbreviation(Units)})" if Units else ""
        Labels = [f"Measurement{Unit_Text}", f"Measurement Uncertainty{Unit_Text}", "Pressure (GPa)", "Pressure (GPa) Uncertainty"]
        for Table in (self.Data_Table, self.Preview_Table):
            Table.setHorizontalHeaderLabels(Labels)
            Table.horizontalHeader().setFixedHeight(50)


    # Show the uncertainty columns only when error propagation is enabled
    def Show_Or_Hide_The_Uncertainty_Columns(self):

        Is_Checked = self.Error_Propagation_Checkbox.isChecked()
        for Table in (self.Data_Table, self.Preview_Table):
            for Column in Uncertainty_Columns:
                Table.setColumnHidden(Column, not Is_Checked)
        # The files for the uncertainties are only needed when error propagation is enabled
        for Target in Uncertainty_Columns:
            self.Source_Rows[Target].setVisible(Is_Checked)
        self.Column_Choice_Row.Line_Up_With_The_Table()


    # When the error propagation checkbox is changed, show or hide the uncertainty columns
    def When_Error_Propagation_Checkbox_Changed(self):

        self.Show_Or_Hide_The_Uncertainty_Columns()
        # The columns of a file that is already loaded have to be chosen again for the values that are now used
        self.Choose_The_Default_Columns()
        self.Update_The_Preview_Table()


    # When the unit type is changed, show the volume units if volume is selected and tell the other sections
    def When_The_Unit_Type_Changes(self):

        self.Select_Volume_Unit_Display.setVisible(self.Volume_Is_Selected())
        # The volume units have to be chosen again
        self.Volume_Unit_Dropdown.blockSignals(True)
        self.Volume_Unit_Dropdown.setCurrentIndex(-1)
        self.Volume_Unit_Dropdown.blockSignals(False)
        self.When_Units_Changed()


    # When the units are changed update the tables and tell the other sections
    def When_Units_Changed(self):

        self.Set_The_Column_Headers()
        self.Units_Changed.emit(self.Get_The_Selected_Units() or "")


    # Clear the manual entry table and go back to the starting number of rows
    def Clear_The_Manual_Entry_Table(self):

        self.Data_Table.clearContents()
        self.Data_Table.setRowCount(Starting_Number_Of_Rows)


    # Add rows to the manual entry table
    def Add_Rows_To_The_Table(self):

        self.Data_Table.setRowCount(self.Data_Table.rowCount() + Number_Of_Rows_To_Add)


    # Clear every uploaded file
    def Clear_The_Uploaded_Files(self):

        self.Loaded_Files = {}
        for Source_Row in self.Get_All_Source_Rows():
            self.Clear_A_Source_Row(Source_Row)
        for Column_Dropdown in self.Column_Choice_Row.Dropdowns:
            self.Fill_A_Column_Dropdown(Column_Dropdown, None, 0, None)
        self.Update_The_Preview_Table()


    # Clear the file and column of one row
    def Clear_A_Source_Row(self, Source_Row):

        self.Loaded_Files.pop(Source_Row.Target, None)
        Source_Row.File_Edit.blockSignals(True)
        Source_Row.File_Edit.clear()
        Source_Row.File_Edit.blockSignals(False)
        if Source_Row.Column_Dropdown is not None:
            self.Fill_A_Column_Dropdown(Source_Row.Column_Dropdown, None, 0, None)



    # When a browse button is clicked, open a file dialog to select a file and set the file path in the line edit
    def When_Browse_Button_Clicked(self, Source_Row=None):

        # The menu opens the single file
        if Source_Row is False or Source_Row is None:
            Source_Row = self.Get_All_Source_Rows()[0]
        # Open a file dialog to load data
        Path, _ = QFileDialog.getOpenFileName(self, "Open Data File", self.Get_The_Default_Browse_Directory(), "Text files (*.txt *.csv *.dat);;All files (*)")

        # If a file was not selected, return early
        if not Path:
            return

        # Update the file path in the line edit
        Source_Row.File_Edit.setText(Path)


    # Get the default directory used when opening a file browser
    def Get_The_Default_Browse_Directory(self):

        # Prefer the desktop when it exists, otherwise fall back to the home directory
        Home_Directory = os.path.expanduser("~")
        Desktop_Directory = os.path.join(Home_Directory, "Desktop")

        return Desktop_Directory if os.path.isdir(Desktop_Directory) else Home_Directory


    # When the file path of a row is changed, read the file, check it and fill the column choices
    def When_The_File_Path_Is_Changed(self, Source_Row, Path):

        # If the path is empty, forget the file
        if not Path:
            self.Loaded_Files.pop(Source_Row.Target, None)
            if Source_Row.Column_Dropdown is not None:
                self.Fill_A_Column_Dropdown(Source_Row.Column_Dropdown, None, 0, None)
            self.Update_The_Preview_Table()
            return
        try:
            Names, Data = Read_Columns_From_Text(Read_Data_File_As_Text(Path))
        # If the file cannot be used, show a warning and clear it
        except Fitting_Data_File_Error as Error:
            Warning_Message(self, Error.Warning_Key, **Error.Format_Values)
            self.Clear_A_Source_Row(Source_Row)
            self.Update_The_Preview_Table()
            return
        except Exception as Error:
            Warning_Message(self, "Could Not Read The Entered Data File", error=Error)
            self.Clear_A_Source_Row(Source_Row)
            self.Update_The_Preview_Table()
            return

        # Store the file
        self.Loaded_Files[Source_Row.Target] = {"Path": Path, "Names": Names, "Data": Data}
        if Source_Row.Target == "One":
            # A file with 4 or more columns has uncertainties, so turn on error propagation; this also chooses the columns
            Has_Uncertainties = Data.shape[1] >= 4
            Is_Changed = self.Error_Propagation_Checkbox.isChecked() != Has_Uncertainties
            self.Error_Propagation_Checkbox.setChecked(Has_Uncertainties)
            if not Is_Changed:
                self.Choose_The_Default_Columns()
        else:
            self.Choose_The_Default_Columns()
        self.Update_The_Preview_Table()


    # Fill a dropdown with the columns of a file: the names from the header if there are any, otherwise the column numbers
    def Fill_A_Column_Dropdown(self, Column_Dropdown, Names, Number_Of_Columns, Selected_Column):

        Column_Dropdown.blockSignals(True)
        Column_Dropdown.clear()
        for Column, Label in enumerate(Get_Column_Labels(Names, Number_Of_Columns)):
            Column_Dropdown.addItem(Label, Column)
        Column_Dropdown.setCurrentIndex(Selected_Column if Selected_Column is not None else -1)
        Column_Dropdown.blockSignals(False)


    # Choose the columns of the loaded files for each value
    def Choose_The_Default_Columns(self):

        Targets = self.Get_The_Used_Targets()
        # One file: the columns are in the order of the values, 2 columns are the measurement and the pressure
        One_File = self.Loaded_Files.get("One")
        if One_File is not None:
            Number_Of_Columns = One_File["Data"].shape[1]
            if len(Targets) == 4 and Number_Of_Columns >= 4:
                Choices = {0: 0, 1: 1, 2: 2, 3: 3}
            else:
                Choices = {0: 0, 2: min(1, Number_Of_Columns - 1)}
            for Target, Column_Dropdown in enumerate(self.Column_Choice_Row.Dropdowns):
                self.Fill_A_Column_Dropdown(Column_Dropdown, One_File["Names"], Number_Of_Columns, Choices.get(Target))
        # Multiple files: the first column is the value, and if there is a second column it is assumed to be the uncertainty
        for Target, Source_Row in self.Source_Rows.items():
            Loaded_File = self.Loaded_Files.get(Target)
            if Loaded_File is None:
                continue
            Number_Of_Columns = Loaded_File["Data"].shape[1]
            Column = 1 if Target in Uncertainty_Columns and Number_Of_Columns >= 2 else 0
            self.Fill_A_Column_Dropdown(Source_Row.Column_Dropdown, Loaded_File["Names"], Number_Of_Columns, Column)



    # Get the file, the column of the file and the path of the file used for a value, or None if they have not been chosen
    def Get_The_Source_Of_A_Value(self, Target):

        if self.Upload_Layout == "One File":
            Loaded_File = self.Loaded_Files.get("One")
            Column = self.Column_Choice_Row.Dropdowns[Target].currentData()
        elif self.Upload_Layout == "Multiple Files":
            Loaded_File = self.Loaded_Files.get(Target)
            Column = self.Source_Rows[Target].Column_Dropdown.currentData()
        else:
            return None
        if Loaded_File is None or Column is None:
            return None

        return Loaded_File["Data"][:, Column], Loaded_File["Path"], Column


    # Get the uploaded values that are used, one array for each
    # Raises Fitting_Data_File_Error if a file or column has not been chosen, the same column is chosen twice, or the columns are not the same length
    def Get_The_Uploaded_Columns(self):

        if self.Upload_Layout is None:
            raise Fitting_Data_File_Error("Missing Fitting File Layout")
        Columns, Sources = {}, {}
        for Target in self.Get_The_Used_Targets():
            Source = self.Get_The_Source_Of_A_Value(Target)
            if Source is None:
                raise Fitting_Data_File_Error("Fitting File Not Selected", column_name=Target_Names[Target])
            # The same column of the same file cannot be two different values
            for Other_Target, Other_Source in Sources.items():
                if Other_Source == Source[1:]:
                    raise Fitting_Data_File_Error("Fitting Same Column Selected", first_name=Target_Names[Other_Target], second_name=Target_Names[Target])
            Columns[Target] = Source[0]
            Sources[Target] = Source[1:]
        # Every value has to have the same number of entries
        if len({len(Column) for Column in Columns.values()}) > 1:
            Details = "\n".join(f"\t{Target_Names[Target]}: {len(Column)} values" for Target, Column in Columns.items())
            raise Fitting_Data_File_Error("Fitting File Column Lengths Differ", details=Details)

        return Columns


    # Show the data that is chosen in the preview table, which cannot be edited
    # Anything that is not chosen yet is left empty so the table shows as much as it can
    def Update_The_Preview_Table(self):

        Columns = {}
        if self.Upload_Layout is not None:
            for Target in self.Get_The_Used_Targets():
                Source = self.Get_The_Source_Of_A_Value(Target)
                if Source is not None:
                    Columns[Target] = Source[0]
        Number_Of_Rows = max([len(Column) for Column in Columns.values()] + [0])
        self.Preview_Table.clearContents()
        self.Preview_Table.setRowCount(max(Number_Of_Rows, Starting_Number_Of_Rows))
        for Target, Column in Columns.items():
            for Row, Value in enumerate(Column):
                self.Preview_Table.setItem(Row, Target, QTableWidgetItem(f"{Value:.10g}"))
        # Only show the table once a file has been loaded
        self.Preview_Table.setVisible(bool(self.Loaded_Files) and self.Upload_Layout is not None)
        self.Space_Before_Preview.setVisible(self.Preview_Table.isVisibleTo(self.Upload_Widget))
        self.Column_Choice_Row.setVisible(bool(self.Loaded_Files) and self.Upload_Layout == "One File")
        self.Column_Choice_Row.Line_Up_With_The_Table()



    # Get the entered rows as (measurement, measurement uncertainty, pressure, pressure uncertainty) text, with an empty uncertainty where there is none
    # Raises Fitting_Data_File_Error if the uploaded files cannot be used
    def Get_The_Entered_Rows(self):

        Rows = []
        if self.Current_Mode == "Upload File":
            Columns = self.Get_The_Uploaded_Columns()
            for Index in range(len(Columns[0])):
                Rows.append(tuple(str(Columns[Target][Index]) if Target in Columns else "" for Target in range(4)))
        elif self.Current_Mode == "Manual Entry":
            for Row in range(self.Data_Table.rowCount()):
                Cells = [self.Get_Cell_Text(Row, Column) for Column in range(4)]
                # Only rows that have a measurement and a pressure that are numbers are data
                try:
                    float(Cells[0])
                    float(Cells[2])
                except ValueError:
                    continue
                Rows.append(tuple(Cells))
            # The uncertainties are only used when error propagation is enabled
            if not self.Error_Propagation_Checkbox.isChecked():
                Rows = [(Row[0], "", Row[2], "") for Row in Rows]

        return Rows


    # Read the text of a cell of the manual entry table
    def Get_Cell_Text(self, Row, Column):

        Item = self.Data_Table.item(Row, Column)

        return Item.text().strip() if Item else ""


    # Read the entered data as arrays: measurement, measurement uncertainty, pressure, pressure uncertainty
    def Read_Table_Data(self):

        try:
            Rows = self.Get_The_Entered_Rows()
        except Fitting_Data_File_Error:
            Rows = []
        # An uncertainty that was not entered is zero
        Columns = [np.array([float(Row[Column] or 0.0) for Row in Rows]) for Column in range(4)]

        return Columns[0], Columns[1], Columns[2], Columns[3]


    # Get the data and units the user has entered
    def Get_Current_Entered_Data(self):

        Measurement, Sigma_Measurement, Pressure, Sigma_Pressure = self.Read_Table_Data()

        return {
            "Units": self.Get_The_Selected_Units(),
            "Method": self.Get_Current_Method(),
            "Source Type": self.Current_Mode,
            "Measurement": Measurement,
            "Sigma_Measurement": Sigma_Measurement,
            "Pressure": Pressure,
            "Sigma_Pressure": Sigma_Pressure,
        }



    # Run validation checks and show warnings if any checks fail
    def Validate_And_Warn(self):

        # Check if a data entry method was selected
        if self.Current_Mode is None:
            Warning_Message(self, "Missing Data Entry Method")
            return False
        # Check if units were selected
        if self.Get_The_Selected_Units() is None:
            Warning_Message(self, "Missing Volume Units Selection" if self.Volume_Is_Selected() else "Missing Units Selection")
            return False

        # Check that every column of the typed values has the same number of values
        if self.Current_Mode == "Manual Entry" and not self.Check_The_Manual_Entries():
            return False

        # Check the data
        try:
            Rows = self.Get_The_Entered_Rows()
        except Fitting_Data_File_Error as Error:
            Warning_Message(self, Error.Warning_Key, **Error.Format_Values)
            return False
        if len(Rows) < 2:
            Warning_Message(self, "Not Enough Fitting Data")
            return False

        # With error propagation enabled each uncertainty column must have a value for every row or for no rows, at least one column must have values, and every value must be above zero
        if self.Error_Propagation_Checkbox.isChecked():
            Number_Of_Columns_With_Values = 0
            for Column in Uncertainty_Columns:
                Column_Name = Target_Names[Column]
                Values = [Row[Column] for Row in Rows if Row[Column]]
                for Value in Values:
                    try:
                        Is_Valid = float(Value) > 0
                    except ValueError:
                        Is_Valid = False
                    if not Is_Valid:
                        Warning_Message(self, "Fitting Uncertainty Not Valid", column_name=Column_Name)
                        return False
                if 0 < len(Values) < len(Rows):
                    Warning_Message(self, "Fitting Uncertainty Missing Values", column_name=Column_Name, entered_count=len(Values), row_count=len(Rows))
                    return False
                Number_Of_Columns_With_Values += 1 if Values else 0
            if Number_Of_Columns_With_Values == 0:
                Warning_Message(self, "Fitting Uncertainty Not Entered")
                return False

        return True


    # Check the values typed into the table, and show a warning if they do not line up
    # Every value must be a number, and every column that is used must have the same number of values (in the same rows).
    # The two uncertainty columns are the exception: one of them may be left empty (for example when only the pressures have uncertainties),
    # but an uncertainty column that has any values has to have as many as the measurement and the pressure
    # Without this a row that is missing its measurement or its pressure is left out of the fit without telling the user
    def Check_The_Manual_Entries(self):

        Used_Targets = self.Get_The_Used_Targets()
        Number_Of_Rows = self.Data_Table.rowCount()
        # Find the rows that have something typed in each column
        Filled_Rows = {Target: [Row for Row in range(Number_Of_Rows) if self.Get_Cell_Text(Row, Target)] for Target in Used_Targets}

        # Every value has to be a number
        for Row in range(Number_Of_Rows):
            for Target in Used_Targets:
                Text = self.Get_Cell_Text(Row, Target)
                if Text:
                    try:
                        float(Text)
                    except ValueError:
                        Warning_Message(self, "Fitting Value Not A Number", row_number=Row + 1, column_name=Target_Names[Target], value=Text)
                        return False

        # The columns that are used: the measurement and pressure always, and an uncertainty column if it has values
        Active_Targets = [Target for Target in Used_Targets if Target not in Uncertainty_Columns or Filled_Rows[Target]]
        if len({len(Filled_Rows[Target]) for Target in Active_Targets}) > 1:
            Details = "\n".join(f"\t{Target_Names[Target]}: {len(Filled_Rows[Target])} values" for Target in Active_Targets)
            Warning_Message(self, "Fitting Columns Have Different Numbers Of Values", details=Details)
            return False

        # The same number of values is not enough: the values of a row have to be in the same row
        for Row in range(Number_Of_Rows):
            Filled = [Target for Target in Active_Targets if Row in Filled_Rows[Target]]
            if Filled and len(Filled) < len(Active_Targets):
                Missing = [Target for Target in Active_Targets if Target not in Filled]
                Warning_Message(self, "Fitting Row Is Incomplete", row_number=Row + 1, filled_names=", ".join(Target_Names[Target] for Target in Filled), missing_names=", ".join(Target_Names[Target] for Target in Missing))
                return False

        return True



    # When the continue button is clicked, check the data and send it out
    def When_The_Continue_Button_Is_Clicked(self):

        if self.Validate_And_Warn():
            self.Send_Out_Entered_Data()


    # Send out the entered data through the callback
    def Send_Out_Entered_Data(self):

        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Get_Current_Entered_Data())



    # Get the table contents and units so a new fit can start from them
    def Get_Prefill(self):

        # Manual entry keeps exactly what was typed; uploaded files are carried over as the rows they contain
        if self.Current_Mode == "Manual Entry":
            Table_Data = [[self.Get_Cell_Text(Row, Column) for Column in range(4)] for Row in range(self.Data_Table.rowCount())]
        else:
            try:
                Table_Data = [list(Row) for Row in self.Get_The_Entered_Rows()]
            except Fitting_Data_File_Error:
                Table_Data = []

        return {"unit": self.Get_The_Selected_Units(), "table_data": Table_Data, "error_propagation": self.Error_Propagation_Checkbox.isChecked()}


    # Fill the table and units from a previous fit
    def Apply_Prefill(self, Prefill):

        Rows = Prefill.get("table_data") or []
        if Rows:
            # The data is always placed in the manual entry table
            self.Select_The_Manual_Entry_Option()
            self.Error_Propagation_Checkbox.setChecked(bool(Prefill.get("error_propagation")))
            self.Data_Table.setRowCount(max(self.Data_Table.rowCount(), len(Rows)))
            for Row, Row_Values in enumerate(Rows):
                for Column, Value in enumerate(Row_Values[:4]):
                    if Value:
                        self.Data_Table.setItem(Row, Column, QTableWidgetItem(Value))
        # The units are set after the mode, because choosing a mode clears them
        Unit = Prefill.get("unit")
        if Unit:
            Unit_Type = Method_Units["XRD"] if Unit in Volume_Units else Unit
            Index = self.Unit_Dropdown_Display.findText(Unit_Type)
            if Index >= 0:
                self.Unit_Dropdown_Display.setCurrentIndex(Index)
                if Unit in Volume_Units:
                    self.Volume_Unit_Dropdown.setCurrentIndex(self.Volume_Unit_Dropdown.findText(Unit))
