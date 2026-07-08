# Load libraries
    # Load standard libraries
import os
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal
    # Load local functions from local files
from EoS_Math.Build_Dataframe import Calibration_List, Calibration_Metadata
from Select_Composition import Select_Composition
from Select_Method import Select_Method
from Collapsible_Sections import Collapsible_Content_Container, Dropdown, WordWrapDelegate, IS_USER_CALIBRANT_ROLE
from View_Edit_And_Save_Calibration_Files_In_A_New_Window import View_Edit_And_Save_Calibration_Files_In_A_New_Window, Preview_Calibration_File_For_File_Path, Preview_Calibration_File_For_Dropdown
from Message_Manager import Warning_Message
from Themes.Theme import Get_Theme





# Create the select calibration content
class Select_Pressure_Calibration_Study(QWidget):
    Request_Scroll_To_Widget = Signal(object)

    def __init__(self, *, Application="EoSAlign", Composition=None, Method=None, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Application = Application
        self.Composition = Composition
        self.Method = Method
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Store internal selections separately
        self.Internal_Selections = {"Workflow Type": None, "Selected Pressure Calibration Study": None, "Different Composition": None, "Different Method": None, "Originally Selected Pressure Calibration Study": None, "Different Pressure Calibration Study": None, "Target Pressure Calibration Study": None, "Implementing A Secondary Pressure Conversion": False}

        # Store the sections that will be used for the select a different pressure calibration study display
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections = []

        # Add the select a different composition content
        self.Select_A_Different_Composition_Content = Select_Composition(Application=self.Application, Once_A_Change_Is_Made=self.When_A_Different_Composition_Is_Selected, Show_Continue_Button=self.Show_Continue_Button, Parent=self)
        self.Selected_Different_Composition = None

        # Add the select a different method content
        self.Select_A_Different_Method_Content = Select_Method(Application=self.Application, Once_A_Change_Is_Made=self.When_A_Different_Method_Is_Selected, Show_Continue_Button=self.Show_Continue_Button, Parent=self)
        self.Selected_Different_Method = None

        # Clear the select a different pressure calibration study dropdown selection
        self.Different_Pressure_Calibration_Study_Dropdown = None
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Final_Different_Pressure_Calibration_Study_Dropdown = None
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Bridge_Footnote = None
        self.Final_Footnote_Label = None

        # Create the select a pressure calibration study display
        self.Create_The_Select_Pressure_Calibration_Study_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the select calibration section to its initial state
    def Reset(self):

        # Reset the internal selections
        self.Internal_Selections = {"Workflow Type": None, "Selected Pressure Calibration Study": None, "Different Composition": None, "Different Method": None, "Originally Selected Pressure Calibration Study": None, "Different Pressure Calibration Study": None, "Target Pressure Calibration Study": None, "Implementing A Secondary Pressure Conversion": False}
        self.Composition = None
        self.Method = None

        # Reset the composition and method selectors
        self.Select_A_Different_Composition_Content.Reset()
        self.Selected_Different_Composition = None
        self.Select_A_Different_Method_Content.Reset()
        self.Selected_Different_Method = None

        # Clear the dropdown selection for select a different pressure calibration study
        self.Different_Pressure_Calibration_Study_Dropdown = None
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Final_Different_Pressure_Calibration_Study_Dropdown = None
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Bridge_Footnote = None
        self.Final_Footnote_Label = None

        # Clear the select a pressure calibration study dropdown options
        self.Pressure_Calibration_Studies_Dropdown_Display.clear()
        self.Main_Dropdown_Footnote.setVisible(False)

        # Hide the workflow displays
        self.Clear_Upcoming_Collapsible_Sections(-1)

        # Uncheck both workflow buttons
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setChecked(False)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setChecked(False)

        # Disable the preview button since no studies are currently selected
        self.Preview_Calibration_File_Button.setEnabled(False)

        # Reset the continue button appearance
        self.Enable_Or_Disable_The_Continue_Button()


    def Refresh(self, *, Composition=None, Method=None, **kwargs):
        if Composition is None or Method is None:
            self.Reset()
            return

        Previous_Selection = self.Internal_Selections.get("Selected Pressure Calibration Study")
        Previous_Workflow_Type = self.Internal_Selections.get("Workflow Type")

        self.Composition = Composition
        self.Method = Method

        self.Add_Relavent_Studies_To_The_Pressure_Calibration_Studies_Dropdown_Display()

        # Restore dropdown selection if still available
        if Previous_Selection is not None:
            Index = self.Pressure_Calibration_Studies_Dropdown_Display.findData(Previous_Selection)
            if Index >= 0:
                self.Pressure_Calibration_Studies_Dropdown_Display.setCurrentIndex(Index)
                self.Internal_Selections["Workflow Type"] = Previous_Workflow_Type
                self.Internal_Selections["Selected Pressure Calibration Study"] = Previous_Selection
            else:
                self.Reset()
                return

        self.Enable_Or_Disable_The_Continue_Button()



    # Find all studies with the same composition and method then update the dropdown options
    def Add_Relavent_Studies_To_The_Pressure_Calibration_Studies_Dropdown_Display(self):

        # Have the program wait a bit while the dropdown is being updated
        self.Pressure_Calibration_Studies_Dropdown_Display.blockSignals(True)

        # Clear the current dropdown options
        self.Pressure_Calibration_Studies_Dropdown_Display.clear()

        # Get a list of the possible studies with the selected composition and method
        List_Of_Studies = []
        for Calibration_Label, Calibration in Calibration_List:
            Metadata = Calibration_Metadata.get(Calibration_Label)
            Study_Composition = Metadata.get("Composition", "")
            Study_Method = Metadata.get("Method", "")
            if Study_Composition == self.Composition and Study_Method == self.Method:
                List_Of_Studies.append((Calibration_Label, Calibration))
        # Sort the studies alphabetically by study name
        List_Of_Studies.sort(key=lambda x: Calibration_Metadata.get(x[0]).get("Study", ""))
        # Add all relevant studies to the dropdown options
        for Calibration_Label, Calibration in List_Of_Studies:
            Metadata = Calibration_Metadata.get(Calibration_Label)
            is_user_edited = Metadata.get("is_user_edited", False)
            is_user_entered = Metadata.get("is_user_entered", False)
            Is_User_Calibrant = is_user_edited or is_user_entered
            prefix = "* " if Is_User_Calibrant else ""
            Study_Name = prefix + Metadata.get("Study", "Unknown")
            Study_Composition = Metadata.get("Composition", "")
            Study_Method = Metadata.get("Method", "")
            Study_Equation_of_State = Metadata.get("Equation of State", "")
            Study_is_K0_fixed = Metadata.get("Is The Initial Bulk Modulus Fixed?", "")
            Study_cal_to_Study_Name = Metadata.get("Reference Study", "")
            Study_Maximum_Pressure = Metadata.get("Maximum Pressure", "")
            Study_Pressure_Transmitting_Medium = Metadata.get("Pressure Transmitting Medium", "")
            Study_Label = (
                f"{Study_Name}"
                f" | "
                # f"Composition: {Study_Composition}"
                f"{Study_Composition}"
                f" | "
                # f"Method: {Study_Method}"
                f"{Study_Method}"
                f" | "
                # f"EoS: {Study_Equation_of_State}"
                f"{Study_Equation_of_State}"
                f" | "
                f"K0 Fixed: {Study_is_K0_fixed}"
                f" | "
                f"cal_to: {Study_cal_to_Study_Name}"
                f" | "
                f"Max Pressure: {Study_Maximum_Pressure} GPa"
                f" | "
                f"PTM: {Study_Pressure_Transmitting_Medium}"
            ).replace("\n", "").strip()
            # Add the dropdown option with the Calibration_Label as the data
            self.Pressure_Calibration_Studies_Dropdown_Display.addItem(Study_Label, Calibration_Label)
            # Flag the option so the popup shows a caution line under it
            self.Pressure_Calibration_Studies_Dropdown_Display.setItemData(
                self.Pressure_Calibration_Studies_Dropdown_Display.count() - 1, Is_User_Calibrant, IS_USER_CALIBRANT_ROLE
            )
        # Set the dropdown to have no selection initially
        self.Pressure_Calibration_Studies_Dropdown_Display.setCurrentIndex(-1)

        # Tell the program it is good to move on
        self.Pressure_Calibration_Studies_Dropdown_Display.blockSignals(False)

        # Disable the preview button since nothing is selected
        self.Preview_Calibration_File_Button.setEnabled(False)
        # No selection yet, so hide the caution footnote row
        self.Update_Main_Dropdown_Footnote()


    # Get the current selected pressure calibration study and its metadata
    def Get_The_Current_Selected_Pressure_Calibration_Study(self):

        # Check if a workflow type has been selected
        if not self.Internal_Selections.get("Workflow Type"):
            return None
        # Check if the workflow type is to use the pressure calibration study for the previously selected composition and method
        if self.Internal_Selections["Workflow Type"] == "Use a Pressure Calibration Study with the Original Composition and Method":
            if not self.Internal_Selections.get("Selected Pressure Calibration Study"):
                return None
            return self.Internal_Selections.copy()
        # Check if the workflow type is to use a different pressure calibration study
        elif self.Internal_Selections["Workflow Type"] == "Use a Pressure Calibration Study with a Different Composition and Method":
            if not (self.Internal_Selections.get("Originally Selected Pressure Calibration Study") and self.Internal_Selections.get("Different Pressure Calibration Study") and self.Internal_Selections.get("Target Pressure Calibration Study")):
                return None
            return self.Internal_Selections.copy()

        return None


    # Build a caution footnote label, styled to match the per-checkbox footnote used
    # in the comparison studies list. Hidden until a flagged option is selected.
    # Left_Margin lines the footnote text up with where the dropdown's own text starts:
    # the dropdown row's 20px left margin plus the combo box's ~9px internal text inset.
    def Build_Caution_Footnote_Label(self, *, Left_Margin=29):
        _, _, Theme_Colors = Get_Theme()
        Caution_Color = Theme_Colors.get("Caution_Text")
        Label = QLabel("* indicates user edited or entered calibrant")
        Label.setObjectName("CollapsibleContentLabel")
        Label.setStyleSheet(f"font-size: 8pt; color: {Caution_Color};")
        Label.setWordWrap(True)
        Label.setContentsMargins(Left_Margin, 0, 0, 0)
        Label.setVisible(False)
        return Label


    # Show or hide the main dropdown's caution footnote based on the current selection
    def Update_Main_Dropdown_Footnote(self):
        Calibration_Label = self.Pressure_Calibration_Studies_Dropdown_Display.currentData()
        Metadata = Calibration_Metadata.get(Calibration_Label) if Calibration_Label else None
        Is_User_Calibrant = bool(Metadata and (Metadata.get("is_user_edited") or Metadata.get("is_user_entered")))
        self.Main_Dropdown_Footnote.setVisible(Is_User_Calibrant)


    # Show or hide the bridge dropdown's caution footnote based on the current selection
    def Update_Bridge_Footnote(self):
        if self.Bridge_Footnote is None or self.Different_Pressure_Calibration_Study_Dropdown is None:
            return
        Calibration_Label = self.Different_Pressure_Calibration_Study_Dropdown.currentData()
        Metadata = Calibration_Metadata.get(Calibration_Label) if Calibration_Label else None
        Is_User_Calibrant = bool(Metadata and (Metadata.get("is_user_edited") or Metadata.get("is_user_entered")))
        self.Bridge_Footnote.setVisible(Is_User_Calibrant)


    # Show or hide the final dropdown's caution footnote based on the current selection
    def Update_Final_Footnote(self):
        if self.Final_Footnote_Label is None or self.Final_Different_Pressure_Calibration_Study_Dropdown is None:
            return
        Calibration_Label = self.Final_Different_Pressure_Calibration_Study_Dropdown.currentData()
        Metadata = Calibration_Metadata.get(Calibration_Label) if Calibration_Label else None
        Is_User_Calibrant = bool(Metadata and (Metadata.get("is_user_edited") or Metadata.get("is_user_entered")))
        self.Final_Footnote_Label.setVisible(Is_User_Calibrant)



    # Create the select calibration display
    def Create_The_Select_Pressure_Calibration_Study_Display(self):

        # Create the select calibration display
        self.setObjectName("CollapsibleContent")
        Select_Pressure_Calibration_Study_Display = QVBoxLayout(self)
        Select_Pressure_Calibration_Study_Display.setContentsMargins(5, 5, 5, 5)
        Select_Pressure_Calibration_Study_Display.setSpacing(8)

        # Create the select calibration layout
        self.Select_Pressure_Calibration_Study_Layout = QWidget()
        self.Select_Pressure_Calibration_Study_Layout.setObjectName("CollapsibleSubContainer")
        Select_Pressure_Calibration_Study_Layout = QVBoxLayout(self.Select_Pressure_Calibration_Study_Layout)
        Select_Pressure_Calibration_Study_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Pressure_Calibration_Study_Layout.setSpacing(8)
        Select_Pressure_Calibration_Study_Display.addWidget(self.Select_Pressure_Calibration_Study_Layout)
        Select_Initial_Pressure_Calibration_Study_Layout = QVBoxLayout()
        Select_Pressure_Calibration_Study_Label = QLabel("Select a Pressure Calibration Study:")
        Select_Pressure_Calibration_Study_Label.setObjectName("CollapsibleContentHeader")
        Select_Initial_Pressure_Calibration_Study_Layout.addWidget(Select_Pressure_Calibration_Study_Label)
        # Create a layout for the dropdown and the preview calibration file button
        Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout = QHBoxLayout()
        Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout.setContentsMargins(20, 0, 0, 0)
        Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout.setSpacing(5)
        # Create the main dropdown
        self.Pressure_Calibration_Studies_Dropdown_Display = Dropdown()
        self.Pressure_Calibration_Studies_Dropdown_Display.setObjectName("Dropdown")
        self.Pressure_Calibration_Studies_Dropdown_Display.setPlaceholderText("Select a pressure calibration study...")
        self.Pressure_Calibration_Studies_Dropdown_Display.setSizeAdjustPolicy(Dropdown.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.Pressure_Calibration_Studies_Dropdown_Display.view().setItemDelegate(WordWrapDelegate(self.Pressure_Calibration_Studies_Dropdown_Display.view(), self.Pressure_Calibration_Studies_Dropdown_Display))
        Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout.addWidget(self.Pressure_Calibration_Studies_Dropdown_Display, stretch=1)
        # Create the preview calibration file button for the select pressure calibration study dropdown
        self.Preview_Calibration_File_Button = QPushButton("Preview Calibrant")
        self.Preview_Calibration_File_Button.setObjectName("Preview_Calibration_Button")
        self.Preview_Calibration_File_Button.setFixedHeight(32)
        self.Preview_Calibration_File_Button.setEnabled(False)  # Disabled until a study is selected
        Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout.addWidget(self.Preview_Calibration_File_Button)
        # Add the dropdown and preview calibration file button to the select initial calibration layout
        Select_Initial_Pressure_Calibration_Study_Layout.addLayout(Select_A_Pressure_Calibration_Study_Dropdown_And_Preview_Calibration_File_Button_Layout)
        # Footnote row shown directly under the dropdown when the selected study is user-edited or user-entered
        self.Main_Dropdown_Footnote = self.Build_Caution_Footnote_Label()
        Select_Initial_Pressure_Calibration_Study_Layout.addWidget(self.Main_Dropdown_Footnote)

        # Add the select initial calibration layout to the main layout
        Select_Pressure_Calibration_Study_Layout.addLayout(Select_Initial_Pressure_Calibration_Study_Layout)

        # Add buttons for selecting the workflow (stacked vertically)
        Workflow_Buttons_Layout = QVBoxLayout()
        # Button for using the original composition and method (shown first / on top)
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button = QPushButton("Use a Pressure Calibration Study with the Original Composition and Method")
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setObjectName("ModeButton")
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setCheckable(True)
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setFixedHeight(32)
        Workflow_Buttons_Layout.addWidget(self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button)
        # Button for selecting a different composition and method (shown below)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button = QPushButton("Use a Pressure Calibration Study with a Different Composition and Method")
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setObjectName("ModeButtonSecondary")
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setCheckable(True)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setFixedHeight(32)
        Workflow_Buttons_Layout.addWidget(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button)

        # Add the workflow buttons to the main layout
        Select_Pressure_Calibration_Study_Layout.addLayout(Workflow_Buttons_Layout)

        # Create a collapsible section for selecting a different composition and method workflow
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Display = QWidget()
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Display.setObjectName("CollapsibleSubContainer")
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Layout = QVBoxLayout(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Display)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Layout.setContentsMargins(0, 0, 0, 0)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Layout.setSpacing(8)

        Select_Pressure_Calibration_Study_Layout.addWidget(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Display)




    # Connect the text boxes and buttons to their functions
    def Connect_Signals(self):

        # Connect the main dropdown selection change to enable/disable preview button
        self.Pressure_Calibration_Studies_Dropdown_Display.currentIndexChanged.connect(self.When_Pressure_Calibration_Studies_Dropdown_Selection_Is_Changed)
        # Connect the preview calibration file button to open the preview for the selected dropdown study
        self.Preview_Calibration_File_Button.clicked.connect(lambda _checked=False: Preview_Calibration_File_For_Dropdown(self, self.Pressure_Calibration_Studies_Dropdown_Display))
        # Connect the workflow buttons
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.clicked.connect(self.When_Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button_Is_Clicked)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.clicked.connect(self.When_Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button_Is_Clicked)


    # When the main dropdown selection changes
    def When_Pressure_Calibration_Studies_Dropdown_Selection_Is_Changed(self):

        # Find the currently selected pressure calibration study
        Selected_Pressure_Calibration_Study = (self.Pressure_Calibration_Studies_Dropdown_Display.currentIndex() >= 0 and self.Pressure_Calibration_Studies_Dropdown_Display.currentData() is not None)
        # Connect the preivew calibration file button to the selected pressure calibration study
        self.Preview_Calibration_File_Button.setEnabled(Selected_Pressure_Calibration_Study)
        # Show the caution footnote row when the selected study is user-edited or user-entered
        self.Update_Main_Dropdown_Footnote()



    # When the use original composition button is clicked
    def When_Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button_Is_Clicked(self):

        # Check if a calibration study has been selected
        if (self.Pressure_Calibration_Studies_Dropdown_Display.currentIndex() < 0 or self.Pressure_Calibration_Studies_Dropdown_Display.currentData() is None):
            Warning_Message(self, "Missing Pressure Calibration Study Selection")
            return

        # Clear any existing sub-sections
        self.Clear_Upcoming_Collapsible_Sections(-1)
        # Mark the active button
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setChecked(True)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setChecked(False)
        # Store the workflow type
        self.Internal_Selections["Workflow Type"] = "Use a Pressure Calibration Study with the Original Composition and Method"
        self.Internal_Selections["Implementing A Secondary Pressure Conversion"] = False
        # Store the first study selection
        Selected_Pressure_Calibration_Study_Label = self.Pressure_Calibration_Studies_Dropdown_Display.currentData()
        self.Internal_Selections["Selected Pressure Calibration Study"] = Selected_Pressure_Calibration_Study_Label

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()

        # Always send the selection — the button itself acts as the confirm/continue action
        self.Send_Out_The_Selected_Pressure_Calibration_Study()


    # When the select different composition button is clicked
    def When_Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button_Is_Clicked(self):

        # Check if a calibration study has been selected
        if (self.Pressure_Calibration_Studies_Dropdown_Display.currentIndex() < 0 or self.Pressure_Calibration_Studies_Dropdown_Display.currentData() is None):
            Warning_Message(self, "Missing Initial Pressure Calibration Study Selection")
            return

        # Clear any existing sub-sections
        self.Clear_Upcoming_Collapsible_Sections(-1)
        # Mark the active button
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Button.setChecked(True)
        self.Use_A_Pressure_Calibration_Study_With_The_Original_Composition_And_Method_Button.setChecked(False)
        # Store the workflow type
        self.Internal_Selections["Workflow Type"] = "Use a Pressure Calibration Study with a Different Composition and Method"
        self.Internal_Selections["Implementing A Secondary Pressure Conversion"] = True
        # Store the first study selection
        Selected_Pressure_Calibration_Study_Label = self.Pressure_Calibration_Studies_Dropdown_Display.currentData()
        self.Internal_Selections["Selected Pressure Calibration Study"] = Selected_Pressure_Calibration_Study_Label

        # Show the select a different composition collapsible section
        self.Select_A_Different_Composition()

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()


    # When the continue button is clicked
    def When_The_Continue_Button_Is_Clicked(self):

        # Find the currently selected pressure calibration study
        Current_Selected_Pressure_Calibration_Study = self.Get_The_Current_Selected_Pressure_Calibration_Study()

        # Show a warning if no pressure calibration study has been selected
        if not Current_Selected_Pressure_Calibration_Study:
            Warning_Message(self, "Incomplete Pressure Calibration Selection")
            return

        # Send out the selection from the select calibration section
        self.Send_Out_The_Selected_Pressure_Calibration_Study()


    # Enable or disable the continue button based on whether a valid selection is made
    def Enable_Or_Disable_The_Continue_Button(self):
        pass


    # Send out the current selection through the callback
    def Send_Out_The_Selected_Pressure_Calibration_Study(self):

        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Get_The_Current_Selected_Pressure_Calibration_Study())



    # Create the select a different composition collapsible section
    def Add_Workflow_Section(self, Workflow_Section):

        Workflow_Section.Section_Animation_Finished.connect(
            lambda Is_Expanded, section=Workflow_Section: self.When_Workflow_Section_Is_Expanded(section, Is_Expanded)
        )
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Layout.addWidget(Workflow_Section)
        self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections.append(Workflow_Section)
        self.Request_Scroll_To_Widget.emit(Workflow_Section)


    def When_Workflow_Section_Is_Expanded(self, Workflow_Section, Is_Expanded):

        if Is_Expanded:
            self.Request_Scroll_To_Widget.emit(Workflow_Section)


    # Create the select a different composition collapsible section
    def Select_A_Different_Composition(self):

        # Reset the composition content and selection
        self.Select_A_Different_Composition_Content.Reset()
        self.Selected_Different_Composition = None

        # Wrap the composition selector in a collapsible section
        Select_Composition_Collapsible_Section = Collapsible_Content_Container("Select A Different Composition", self.Select_A_Different_Composition_Content, Show_Container_Title=True, Initially_Show_Container=True, Drop_Shadow=8)
        # Re-show content after it was hidden by Clear_Upcoming_Collapsible_Sections
        self.Select_A_Different_Composition_Content.show()

        # Add the collapsible section to the use a pressure calibration study with a different composition and method workflow layout
        self.Add_Workflow_Section(Select_Composition_Collapsible_Section)


    # Create the select a different method collapsible section
    def Select_A_Different_Method(self):

        # Reset the method content and selection
        self.Select_A_Different_Method_Content.Reset()
        self.Selected_Different_Method = None

        # Wrap the method selector in a collapsible section
        Select_Method_Collapsible_Section = Collapsible_Content_Container("Select A Different Method", self.Select_A_Different_Method_Content, Show_Container_Title=True, Initially_Show_Container=True, Drop_Shadow=8)
        # Re-show content after it was hidden by Clear_Upcoming_Collapsible_Sections
        self.Select_A_Different_Method_Content.show()

        # Add the collapsible section to the use a pressure calibration study with a different composition and method workflow layout
        self.Add_Workflow_Section(Select_Method_Collapsible_Section)


    # Create the select a different pressure calibration study collapsible section
    def Select_A_Different_Pressure_Calibration_Study(self):

        # Create the widget for selecting a different pressure calibration study
        Select_A_Different_Pressure_Calibration_Study_Display = QWidget()
        Select_A_Different_Pressure_Calibration_Study_Display.setObjectName("CollapsibleContent")
        Select_A_Different_Pressure_Calibration_Study_Layout = QVBoxLayout(Select_A_Different_Pressure_Calibration_Study_Display)
        Select_A_Different_Pressure_Calibration_Study_Layout.setContentsMargins(0, 0, 0, 0)
        Select_A_Different_Pressure_Calibration_Study_Layout.setSpacing(8)

        # Show the originally selected pressure calibration study
        Selected_Study_Header_Label = QLabel("Study Selected For Pressure Conversion:")
        Selected_Study_Header_Label.setObjectName("CollapsibleContentHeader")
        Selected_Study_Header_Label.setWordWrap(True)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Selected_Study_Header_Label)
        # Get original study metadata
        Originally_Selected_Pressure_Calibration_Study_Label = self.Internal_Selections.get("Selected Pressure Calibration Study")
        Originally_Selected_Pressure_Calibration_Study_Metadata = Calibration_Metadata.get(Originally_Selected_Pressure_Calibration_Study_Label)
        Original_Is_User = (Originally_Selected_Pressure_Calibration_Study_Metadata.get("is_user_edited", False) or Originally_Selected_Pressure_Calibration_Study_Metadata.get("is_user_entered", False)) if Originally_Selected_Pressure_Calibration_Study_Metadata else False
        Original_Prefix = "* " if Original_Is_User else ""
        Originally_Selected_Pressure_Calibration_Study_Name = Original_Prefix + (Originally_Selected_Pressure_Calibration_Study_Metadata.get("Study", "Unknown") if Originally_Selected_Pressure_Calibration_Study_Metadata else "Unknown")
        Originally_Selected_Pressure_Calibration_Study_Composition = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Composition", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_Method = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Method", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_Equation_of_State = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Equation of State", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_is_K0_fixed = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Is The Initial Bulk Modulus Fixed?", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_cal_to_Study_Name = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Reference Study", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_Maximum_Pressure = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Maximum Pressure", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_Pressure_Transmitting_Medium = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Pressure Transmitting Medium", "") if Originally_Selected_Pressure_Calibration_Study_Metadata else ""
        Originally_Selected_Pressure_Calibration_Study_File_Path = Originally_Selected_Pressure_Calibration_Study_Metadata.get("file_path") if Originally_Selected_Pressure_Calibration_Study_Metadata else None
        Originally_Selected_Pressure_Calibration_Study_Display_Text = (
            f"{Originally_Selected_Pressure_Calibration_Study_Name}"
            f" | "
            # f"Composition: {Originally_Selected_Pressure_Calibration_Study_Composition}"
            f"{Originally_Selected_Pressure_Calibration_Study_Composition}"
            f" | "
            # f"Method: {Originally_Selected_Pressure_Calibration_Study_Method}"
            f"{Originally_Selected_Pressure_Calibration_Study_Method}"
            f" | "
            # f"EoS: {Originally_Selected_Pressure_Calibration_Study_Equation_of_State}"
            f"{Originally_Selected_Pressure_Calibration_Study_Equation_of_State}"
            f" | "
            f"K0 Fixed: {Originally_Selected_Pressure_Calibration_Study_is_K0_fixed}"
            f" | "
            f"cal_to: {Originally_Selected_Pressure_Calibration_Study_cal_to_Study_Name}"
            f" | "
            f"Max Pressure: {Originally_Selected_Pressure_Calibration_Study_Maximum_Pressure} GPa"
            f" | "
            f"PTM: {Originally_Selected_Pressure_Calibration_Study_Pressure_Transmitting_Medium}"
        ).replace("\n", "").strip()
        # Display the originally selected pressure calibration study
        Originally_Selected_Pressure_Calibration_Study_Layout = QHBoxLayout()
        Originally_Selected_Pressure_Calibration_Study_Layout.setContentsMargins(20, 0, 0, 0)
        Originally_Selected_Pressure_Calibration_Study_Layout.setSpacing(5)
        Originally_Selected_Pressure_Calibration_Study_Dropdown = Dropdown()
        Originally_Selected_Pressure_Calibration_Study_Dropdown.setObjectName("Dropdown")
        Originally_Selected_Pressure_Calibration_Study_Dropdown.setSizeAdjustPolicy(Dropdown.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        Originally_Selected_Pressure_Calibration_Study_Dropdown.view().setItemDelegate(
            WordWrapDelegate(
                Originally_Selected_Pressure_Calibration_Study_Dropdown.view(),
                Originally_Selected_Pressure_Calibration_Study_Dropdown,
            )
        )
        Originally_Selected_Pressure_Calibration_Study_Dropdown.addItem(
            Originally_Selected_Pressure_Calibration_Study_Display_Text,
            Originally_Selected_Pressure_Calibration_Study_Label,
        )
        Originally_Selected_Pressure_Calibration_Study_Dropdown.setCurrentIndex(0)
        Originally_Selected_Pressure_Calibration_Study_Dropdown.setEnabled(False)
        Originally_Selected_Pressure_Calibration_Study_Layout.addWidget(
            Originally_Selected_Pressure_Calibration_Study_Dropdown,
            stretch=1,
        )
        # Add a preview calibration file button for the originally selected pressure calibration study
        Preview_Originally_Selected_Pressure_Calibration_Study_YAML_File_Button = QPushButton("Preview Calibrant")
        Preview_Originally_Selected_Pressure_Calibration_Study_YAML_File_Button.setObjectName("Preview_Calibration_Button")
        Preview_Originally_Selected_Pressure_Calibration_Study_YAML_File_Button.setFixedHeight(32)
        # Capture File_Path in default argument to avoid late-binding issues
        Preview_Originally_Selected_Pressure_Calibration_Study_YAML_File_Button.clicked.connect(lambda _checked=False, fp=Originally_Selected_Pressure_Calibration_Study_File_Path: Preview_Calibration_File_For_File_Path(self, fp))
        # Add the preview calibration file button to the originally selected pressure calibration study layout
        Originally_Selected_Pressure_Calibration_Study_Layout.addWidget(Preview_Originally_Selected_Pressure_Calibration_Study_YAML_File_Button)

        # Add the originally selected pressure calibration study layout to the select a different pressure calibration study layout
        Select_A_Different_Pressure_Calibration_Study_Layout.addLayout(Originally_Selected_Pressure_Calibration_Study_Layout)
        # Footnote for the originally selected study label (this dropdown is disabled/fixed,
        # so the popup caution line never gets shown — keep the explicit footnote here)
        Original_Study_Footnote = self.Build_Caution_Footnote_Label()
        Original_Study_Footnote.setVisible(Original_Is_User)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Original_Study_Footnote)

        # Create the select a different pressure calibration study display
        Select_A_Different_Study_Header_Label = QLabel("Select A Pressure Calibration Study For Conversion:")
        Select_A_Different_Study_Header_Label.setObjectName("CollapsibleContentHeader")
        Select_A_Different_Study_Header_Label.setWordWrap(True)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Select_A_Different_Study_Header_Label)
        Explanation_Label = QLabel(
            f"The selected study for {self.Composition}/{self.Method} "
            f"will be set equal to the pressure for the selected study with "
            f"a composition of {self.Selected_Different_Composition} "
            f"and a method of {self.Selected_Different_Method}."
        )
        Explanation_Label.setObjectName("CollapsibleContentLabel")
        Explanation_Label.setContentsMargins(20, 0, 0, 0)
        Explanation_Label.setWordWrap(True)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Explanation_Label)
        # Create the select a different pressure calibration study dropdown layout
        Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout = QHBoxLayout()
        Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout.setContentsMargins(20, 0, 0, 0)
        Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout.setSpacing(5)
        # Create the dropdown for selecting a different pressure calibration study
        self.Different_Pressure_Calibration_Study_Dropdown = Dropdown()
        self.Different_Pressure_Calibration_Study_Dropdown.setObjectName("Dropdown")
        self.Different_Pressure_Calibration_Study_Dropdown.setPlaceholderText("Select A Pressure Calibration Study...")
        self.Different_Pressure_Calibration_Study_Dropdown.setSizeAdjustPolicy(Dropdown.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.Different_Pressure_Calibration_Study_Dropdown.view().setItemDelegate(WordWrapDelegate(self.Different_Pressure_Calibration_Study_Dropdown.view(), self.Different_Pressure_Calibration_Study_Dropdown))
        # Populate the dropdown with pressure calibration studies that have both the originally selected composition and method AND the different composition and method
        Valid_Studies = self.Find_List_Of_All_Studies_With_Compositions_And_Methods_That_Match_The_Original_Selections_And_Pressure_Calibration_Study_Selections()
        if not Valid_Studies:
            self.Different_Pressure_Calibration_Study_Dropdown.setPlaceholderText("There are no studies available for both compositions and methods")
            self.Different_Pressure_Calibration_Study_Dropdown.setEnabled(False)

            Error_Label = QLabel(
                f"No studies found that exist in both {self.Composition}/{self.Method} "
                f"and {self.Selected_Different_Composition}/{self.Selected_Different_Method}."
            )
            Error_Label.setWordWrap(True)
            Error_Label.setStyleSheet("color: red;")
            Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Error_Label)
        else:
            # Collect matching studies then sort alphabetically by study name (mirrors first dropdown)
            Different_Study_List = []
            Originally_Selected_Key = self.Internal_Selections.get("Selected Pressure Calibration Study")
            for Calibration_Label, Calibration in Calibration_List:
                Metadata = Calibration_Metadata.get(Calibration_Label)
                Study = Metadata.get("Study", "Unknown")
                Composition = Metadata.get("Composition", "")
                Method = Metadata.get("Method", "")
                if (Composition == self.Composition and Method == self.Method and Study in Valid_Studies and Calibration_Label != Originally_Selected_Key):
                    Different_Study_List.append((Calibration_Label, Calibration))
            Different_Study_List.sort(key=lambda x: Calibration_Metadata.get(x[0]).get("Study", ""))
            for Calibration_Label, Calibration in Different_Study_List:
                Metadata = Calibration_Metadata.get(Calibration_Label)
                is_user_edited = Metadata.get("is_user_edited", False)
                is_user_entered = Metadata.get("is_user_entered", False)
                Is_User_Calibrant = is_user_edited or is_user_entered
                Bridge_Prefix = "* " if Is_User_Calibrant else ""
                Study = Bridge_Prefix + Metadata.get("Study", "Unknown")
                Composition = Metadata.get("Composition", "")
                Method = Metadata.get("Method", "")
                Equation_of_State = Metadata.get("Equation of State", "")
                is_K0_fixed = Metadata.get("Is The Initial Bulk Modulus Fixed?", "")
                cal_to_Study_Name = Metadata.get("Reference Study", "")
                Maximum_Pressure = Metadata.get("Maximum Pressure", "")
                Pressure_Transmitting_Medium = Metadata.get("Pressure Transmitting Medium", "")
                Display = (
                    f"{Study}"
                    f" | "
                    # f"Composition: {Composition}"
                    f"{Composition}"
                    f" | "
                    # f"Method: {Method}"
                    f"{Method}"
                    f" | "
                    # f"EoS: {Equation_of_State}"
                    f"{Equation_of_State}"
                    f" | "
                    f"K0 Fixed: {is_K0_fixed}"
                    f" | "
                    f"cal_to: {cal_to_Study_Name}"
                    f" | "
                    f"Max Pressure: {Maximum_Pressure} GPa"
                    f" | "
                    f"PTM: {Pressure_Transmitting_Medium}"
                ).replace("\n", "").strip()
                self.Different_Pressure_Calibration_Study_Dropdown.addItem(Display, Calibration_Label)
                self.Different_Pressure_Calibration_Study_Dropdown.setItemData(
                    self.Different_Pressure_Calibration_Study_Dropdown.count() - 1, Is_User_Calibrant, IS_USER_CALIBRANT_ROLE
                )
        # Set the dropdown to have no selection initially
        self.Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(-1)
        Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout.addWidget(self.Different_Pressure_Calibration_Study_Dropdown, stretch=1)
        # Create preview calibration file button for the different study dropdown
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = QPushButton("Preview Calibrant")
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setObjectName("Preview_Calibration_Button")
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setFixedHeight(32)
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(False)
        # Connect preview button to preview the YAML for the different pressure calibration study dropdown
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.clicked.connect(lambda _checked=False: Preview_Calibration_File_For_Dropdown(self, self.Different_Pressure_Calibration_Study_Dropdown))
        # Connect dropdown change to enable/disable the preview button
        self.Different_Pressure_Calibration_Study_Dropdown.currentIndexChanged.connect(lambda: self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(self.Different_Pressure_Calibration_Study_Dropdown.currentData() is not None))
        # Connect dropdown change to show/hide the caution footnote row
        self.Different_Pressure_Calibration_Study_Dropdown.currentIndexChanged.connect(self.Update_Bridge_Footnote)
        # Add the preview button to the select a different pressure calibration study dropdown layout
        Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout.addWidget(self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button)

        # Add the select a different pressure calibration study dropdown layout to the select a different pressure calibration study layout
        Select_A_Different_Pressure_Calibration_Study_Layout.addLayout(Select_A_Different_Pressure_Calibration_Study_Dropdown_Layout)
        # Footnote row shown directly under the bridge dropdown when the selected study is user-edited or user-entered
        self.Bridge_Footnote = self.Build_Caution_Footnote_Label()
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(self.Bridge_Footnote)

        # Create the select a pressure calibration study for the different composition and method
        Select_A_Final_Pressure_Calibration_Study_Header_Label = QLabel("Select A Pressure Calibration Study For The Different Composition and Method:")
        Select_A_Final_Pressure_Calibration_Study_Header_Label.setObjectName("CollapsibleContentHeader")
        Select_A_Final_Pressure_Calibration_Study_Header_Label.setWordWrap(True)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Select_A_Final_Pressure_Calibration_Study_Header_Label)
        # Create the select a final pressure calibration study dropdown for the different composition and method layout
        Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout = QHBoxLayout()
        Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout.setContentsMargins(20, 0, 0, 0)
        Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout.setSpacing(5)
        # Create the dropdown for selecting a pressure calibration study for the different composition and method
        self.Final_Different_Pressure_Calibration_Study_Dropdown = Dropdown()
        self.Final_Different_Pressure_Calibration_Study_Dropdown.setObjectName("Dropdown")
        self.Final_Different_Pressure_Calibration_Study_Dropdown.setPlaceholderText("First select a bridge study above...")
        self.Final_Different_Pressure_Calibration_Study_Dropdown.setSizeAdjustPolicy(Dropdown.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.Final_Different_Pressure_Calibration_Study_Dropdown.view().setItemDelegate(WordWrapDelegate(self.Final_Different_Pressure_Calibration_Study_Dropdown.view(), self.Final_Different_Pressure_Calibration_Study_Dropdown))
        self.Final_Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(-1)
        self.Final_Different_Pressure_Calibration_Study_Dropdown.setEnabled(False)
        Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout.addWidget(self.Final_Different_Pressure_Calibration_Study_Dropdown, stretch=1)
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = QPushButton("Preview Calibrant")
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setObjectName("Preview_Calibration_Button")
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setFixedHeight(32)
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(False)
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.clicked.connect(lambda _checked=False: Preview_Calibration_File_For_Dropdown(self, self.Final_Different_Pressure_Calibration_Study_Dropdown))
        self.Final_Different_Pressure_Calibration_Study_Dropdown.currentIndexChanged.connect(lambda: self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(self.Final_Different_Pressure_Calibration_Study_Dropdown.currentData() is not None))
        # Connect dropdown change to show/hide the caution footnote row
        self.Final_Different_Pressure_Calibration_Study_Dropdown.currentIndexChanged.connect(self.Update_Final_Footnote)
        Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout.addWidget(self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button)
        Select_A_Different_Pressure_Calibration_Study_Layout.addLayout(Select_A_Final_Pressure_Calibration_Study_Dropdown_Layout)
        # Footnote row shown directly under the final dropdown when the selected study is user-edited or user-entered
        self.Final_Footnote_Label = self.Build_Caution_Footnote_Label()
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(self.Final_Footnote_Label)
        self.Different_Pressure_Calibration_Study_Dropdown.currentIndexChanged.connect(self.Update_Final_Different_Pressure_Calibration_Study_Dropdown)


        # Confirm button — always shown; acts as the continue trigger
        Confirm_Selection_Button = QPushButton("Confirm Pressure Conversion Selection")
        Confirm_Selection_Button.setObjectName("Primary_Button")
        Confirm_Selection_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        Confirm_Selection_Button.setFixedHeight(32)
        Confirm_Selection_Button.clicked.connect(self.When_A_Different_Pressure_Calibration_Study_Is_Selected)
        Select_A_Different_Pressure_Calibration_Study_Layout.addWidget(Confirm_Selection_Button)

        # Wrap all of this in a collapsible section
        Different_Study_Collapsible_Section = Collapsible_Content_Container("Select A Pressure Calibration Study", Select_A_Different_Pressure_Calibration_Study_Display, Show_Container_Title=True, Initially_Show_Container=True, Expanding_Content=True, Drop_Shadow=8)

        # Add the collapsible section to the use a pressure calibration study with a different composition and method workflow layout
        self.Add_Workflow_Section(Different_Study_Collapsible_Section)



    def Build_Study_Display_Text(self, Cal_Key):
        Metadata = Calibration_Metadata.get(Cal_Key, {})
        is_user_edited = Metadata.get("is_user_edited", False)
        is_user_entered = Metadata.get("is_user_entered", False)
        prefix = "* " if (is_user_edited or is_user_entered) else ""
        Study_Name = prefix + Metadata.get("Study", "Unknown")
        return (
            f"{Study_Name}"
            f" | "
            f"{Metadata.get('Composition', '')}"
            f" | "
            f"{Metadata.get('Method', '')}"
            f" | "
            f"{Metadata.get('Equation of State', '')}"
            f" | "
            f"K0 Fixed: {Metadata.get('is_K0_fixed', '')}"
            f" | "
            f"cal_to: {Metadata.get('cal_to_name', '')}"
            f" | "
            f"Max Pressure: {Metadata.get('Maximum Pressure', '')} GPa"
            f" | "
            f"PTM: {Metadata.get('PTM', '')}"
        ).replace("\n", "").strip()


    def Update_Final_Different_Pressure_Calibration_Study_Dropdown(self):
        if self.Final_Different_Pressure_Calibration_Study_Dropdown is None:
            return
        Bridge_Key = (self.Different_Pressure_Calibration_Study_Dropdown.currentData() if self.Different_Pressure_Calibration_Study_Dropdown is not None else None)
        self.Final_Different_Pressure_Calibration_Study_Dropdown.blockSignals(True)
        self.Final_Different_Pressure_Calibration_Study_Dropdown.clear()
        if Bridge_Key is None:
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setPlaceholderText("First select a specific entry...")
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setEnabled(False)
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(-1)
            self.Final_Different_Pressure_Calibration_Study_Dropdown.blockSignals(False)
            if self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button is not None:
                self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(False)
            self.Update_Final_Footnote()
            return
        Bridge_Study_Name = Calibration_Metadata.get(Bridge_Key, {}).get("Study", "")
        Target_List = []
        for Cal_Key, _ in Calibration_List:
            Meta = Calibration_Metadata.get(Cal_Key, {})
            if (Meta.get("Composition") == self.Selected_Different_Composition and Meta.get("Method") == self.Selected_Different_Method and Meta.get("Study") == Bridge_Study_Name):
                Target_List.append(Cal_Key)
        Target_List.sort(key=lambda k: Calibration_Metadata.get(k, {}).get("Study", ""))
        for Cal_Key in Target_List:
            Meta = Calibration_Metadata.get(Cal_Key, {})
            Is_User_Calibrant = bool(Meta.get("is_user_edited") or Meta.get("is_user_entered"))
            self.Final_Different_Pressure_Calibration_Study_Dropdown.addItem(self.Build_Study_Display_Text(Cal_Key), Cal_Key)
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setItemData(
                self.Final_Different_Pressure_Calibration_Study_Dropdown.count() - 1, Is_User_Calibrant, IS_USER_CALIBRANT_ROLE
            )
        if Target_List:
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setEnabled(True)
            if len(Target_List) == 1:
                self.Final_Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(0)
            else:
                self.Final_Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(-1)
        else:
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setPlaceholderText("No matching study in the different composition/method")
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setEnabled(False)
            self.Final_Different_Pressure_Calibration_Study_Dropdown.setCurrentIndex(-1)
        self.Final_Different_Pressure_Calibration_Study_Dropdown.blockSignals(False)
        if self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button is not None:
            self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button.setEnabled(self.Final_Different_Pressure_Calibration_Study_Dropdown.currentData() is not None)
        self.Update_Final_Footnote()


    # When a different composition is selected
    def When_A_Different_Composition_Is_Selected(self, Different_Composition):

        # Store the selected composition
        self.Selected_Different_Composition = Different_Composition
        self.Internal_Selections["Different Composition"] = Different_Composition

        # Update the collapsible section title and collapse it in Step-by-Step mode
        if (self.Show_Continue_Button and len(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections) >= 1):
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[0].Set_The_Section_Title_Text(f"Composition For The Pressure Calibration Study: {Different_Composition}")
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[0].Expand_Or_Collapse_Section(False)

        # Clear all upcoming collapsible sections
        self.Clear_Upcoming_Collapsible_Sections(0)

        # Clear the select a different pressure calibration study dropdown options
        self.Different_Pressure_Calibration_Study_Dropdown = None
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Final_Different_Pressure_Calibration_Study_Dropdown = None
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None

        # Show the select a different method collapsible section
        self.Select_A_Different_Method()

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()


    # When a different method is selected
    def When_A_Different_Method_Is_Selected(self, Different_Method):

        # Store the selected method
        self.Selected_Different_Method = Different_Method
        self.Internal_Selections["Different Method"] = Different_Method

        # Update the collapsible section title and collapse it in Step-by-Step mode
        if (self.Show_Continue_Button and len(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections) >= 2):
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[1].Set_The_Section_Title_Text(f"Method For The Pressure Calibration Study: {Different_Method}")
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[1].Expand_Or_Collapse_Section(False)

        # Clear all upcoming collapsible sections
        self.Clear_Upcoming_Collapsible_Sections(1)

        # Clear the select a different pressure calibration study dropdown options
        self.Different_Pressure_Calibration_Study_Dropdown = None
        self.Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None
        self.Final_Different_Pressure_Calibration_Study_Dropdown = None
        self.Final_Different_Pressure_Calibration_Study_Preview_Calibration_File_Button = None

        # Show the select a different pressure calibration study collapsible section
        self.Select_A_Different_Pressure_Calibration_Study()

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()



    # Get the valid studies that have calibrations for both the originally selected and different composition and method
    def Find_List_Of_All_Studies_With_Compositions_And_Methods_That_Match_The_Original_Selections_And_Pressure_Calibration_Study_Selections(self):

        # Get all studies for the originally selected composition and method
        Pressure_Calibration_Studies_With_The_Originally_Selected_Composition_And_Method = set()
        for Calibration_Label, Calibration in Calibration_List:
            Metadata = Calibration_Metadata.get(Calibration_Label)
            Composition = Metadata.get("Composition", "")
            Method = Metadata.get("Method", "")
            if Composition == self.Composition and Method == self.Method:
                Pressure_Calibration_Studies_With_The_Originally_Selected_Composition_And_Method.add(Metadata.get("Study", ""))

        # Get all studies for the different composition and method
        Pressure_Calibration_Studies_With_The_Different_Composition_And_Method = set()
        for Calibration_Label, Calibration in Calibration_List:
            Metadata = Calibration_Metadata.get(Calibration_Label)
            Composition = Metadata.get("Composition", "")
            Method = Metadata.get("Method", "")
            if Composition == self.Selected_Different_Composition and Method == self.Selected_Different_Method:
                Pressure_Calibration_Studies_With_The_Different_Composition_And_Method.add(Metadata.get("Study", ""))

        # Return the intersection of the two sets
        return Pressure_Calibration_Studies_With_The_Originally_Selected_Composition_And_Method.intersection(Pressure_Calibration_Studies_With_The_Different_Composition_And_Method)



    # Update the information that is sent out when the use a pressure calibration study with a different composition and method workflow is selected
    def When_A_Different_Pressure_Calibration_Study_Is_Selected(self):

        # Check that a bridge study has been selected
        if (self.Different_Pressure_Calibration_Study_Dropdown is None or self.Different_Pressure_Calibration_Study_Dropdown.currentData() is None):
            Warning_Message(self, "Missing Pressure Calibration Study With A Different Composition And Method Selection")
            return

        # Check that a target study has been selected
        if (self.Final_Different_Pressure_Calibration_Study_Dropdown is None or self.Final_Different_Pressure_Calibration_Study_Dropdown.currentData() is None):
            Warning_Message(self, "Missing Final Pressure Calibration Study Selection")
            return

        # Store all three calibration keys
        self.Internal_Selections["Originally Selected Pressure Calibration Study"] = self.Internal_Selections.get("Selected Pressure Calibration Study")
        self.Internal_Selections["Different Pressure Calibration Study"] = self.Different_Pressure_Calibration_Study_Dropdown.currentData()
        self.Internal_Selections["Target Pressure Calibration Study"] = self.Final_Different_Pressure_Calibration_Study_Dropdown.currentData()

        # Get study names for the section title
        Originally_Selected_Pressure_Calibration_Study_Metadata = Calibration_Metadata.get(self.Internal_Selections["Originally Selected Pressure Calibration Study"])
        Different_Pressure_Calibration_Study_Metadata = Calibration_Metadata.get(self.Internal_Selections["Different Pressure Calibration Study"])
        Originally_Selected_Pressure_Caibration_Study_Name = Originally_Selected_Pressure_Calibration_Study_Metadata.get("Study", "Unknown") if Originally_Selected_Pressure_Calibration_Study_Metadata else "Unknown"
        Different_Pressure_Calibration_Study_Name = Different_Pressure_Calibration_Study_Metadata.get("Study", "Unknown") if Different_Pressure_Calibration_Study_Metadata else "Unknown"

        # Update the collapsible section title and collapse it
        if (self.Show_Continue_Button and self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections):
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[-1].Set_The_Section_Title_Text(
                f"Pressure Conversion: {Originally_Selected_Pressure_Caibration_Study_Name} "
                f"({self.Composition}, {self.Method}) = "
                f"{Different_Pressure_Calibration_Study_Name} "
                f"({self.Selected_Different_Composition}, {self.Selected_Different_Method})"
            )
            self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections[-1].Expand_Or_Collapse_Section(False)

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()

        # Send out the selected pressure calibration study information
        self.Send_Out_The_Selected_Pressure_Calibration_Study()



    # Clear all upcoming collapsible sections
    def Clear_Upcoming_Collapsible_Sections(self, Index):

        # Re-parent reusable content widgets back to self so they are not
        # destroyed when their containing collapsible section is deleted.
        # setParent(self) is safe to call even if they are already children of self.
        self.Select_A_Different_Composition_Content.setParent(self)
        self.Select_A_Different_Composition_Content.hide()
        self.Select_A_Different_Method_Content.setParent(self)
        self.Select_A_Different_Method_Content.hide()

        # Find the upcoming collapsible sections
        while len(self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections) > Index + 1:
            # Remove the current collapsible section from the list of collapsible sections
            Current_Collapsible_Section = self.Use_A_Pressure_Calibration_Study_With_A_Different_Composition_And_Method_Workflow_Sections.pop()
            # Remove the current collapsible section
            Current_Collapsible_Section.setParent(None)
            # Delete the current collapsible section
            Current_Collapsible_Section.deleteLater()





# Summarize the choices made during select pressure calibration study section
def Summary_Of_Selected_Pressure_Calibration_Study(Selected_Pressure_Calibration_Study):

    # Check if a pressure calibration study is selected
    if Selected_Pressure_Calibration_Study is None:
        return "None"

    # If a calibration is selected, get its information
    if isinstance(Selected_Pressure_Calibration_Study, dict):
        Workflow_Type = Selected_Pressure_Calibration_Study.get("Workflow Type", "")
        Originally_Selected_Pressure_Calibration_Study = Selected_Pressure_Calibration_Study.get("Selected Pressure Calibration Study", "")
        # If the workflow is use the originally selected composition and method return the originally selected pressure calibration study
        if Workflow_Type == "Use a Pressure Calibration Study with the Original Composition and Method":
            try:
                return Calibration_Metadata.get(Originally_Selected_Pressure_Calibration_Study).get("Study", Originally_Selected_Pressure_Calibration_Study)
            except Exception:
                return str(Originally_Selected_Pressure_Calibration_Study)
        # If the workflow is use a pressure calibration study for a different composition and method send out the different pressure calibration study
        elif Workflow_Type == "Use a Pressure Calibration Study with a Different Composition and Method":
            Target_Composition = Selected_Pressure_Calibration_Study.get("Different Composition", "")
            Target_Method = Selected_Pressure_Calibration_Study.get("Different Method", "")
            return f"Use a Pressure Calibration Study with a Different Composition and Method:\nComposition: {Target_Composition} Method: {Target_Method}"

        return str(Originally_Selected_Pressure_Calibration_Study)
    return str(Selected_Pressure_Calibration_Study)




