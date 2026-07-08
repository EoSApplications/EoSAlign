# Load libraries
    # Load standard libraries
import os
import html
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QSizePolicy, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt
from functools import partial
    # Load local functions from local files
from EoS_Math.Build_Dataframe import Calibration_Metadata, Build_Dataframe, Translate_Pressure_Calibration_Study
from Conversion_Window import Data_Preview_Dialog
from View_Edit_And_Save_Calibration_Files_In_A_New_Window import View_Edit_And_Save_Calibration_Files_In_A_New_Window, Preview_Calibration_File_For_File_Path, Preview_Calibration_File_For_Dropdown
from Collapsible_Sections import CheckboxRow
from Message_Manager import Warning_Message
from Themes.Theme import Get_Theme





# Create the Select Studies for Comparison content
class Select_Studies_For_Comparison(QWidget):
    def __init__(self, *, Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Show_Preview=True, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button
        self.Show_Preview = Show_Preview
        self.Data = Data
        self.Units = Units
        self.Composition = Composition
        self.Method = Method
        self.Pressure_Calibration_Study = Pressure_Calibration_Study
        self.List_Of_Checkboxes = []

        # Create the select studies for comparison display
        self.Create_The_Select_Studies_For_Comparison_Display()

        # Connect the signals
        self.Connect_Signals()

        # If composition and method were provided at init, populate immediately
        if self.Composition and self.Method:
            self.Populate_Checkboxes()



    # Reset the select studies for comparison section to its initial state
    def Reset(self):

        # Clear the list of checkboxes and any placeholder labels
        self.Clear_All_Study_Widgets()

        # Add the placeholder label
        self.Add_Text_To_The_Select_Studies_Checkbox_Display("Select a composition and method in order to see available studies")

        # Reset the continue button appearance
        self.Enable_Or_Disable_The_Continue_Button()


    # Refresh the select studies for comparison section and find all possible calibrations
    def Refresh(self, *, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Data=None, **kwargs):
        
        Previous_Selections = {Calibration_Key for Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata in self.List_Of_Checkboxes if Study_Option_Checkbox.isChecked()}

        # Save the custom reference
        Should_Preserve_Custom_Ref = (Method == self.Method and Method is not None and Units != "Pressure (GPa)")
        if Should_Preserve_Custom_Ref:
            Saved_Custom_Ref_Enabled = self.Custom_Ref_Enabled
            Saved_Custom_Ref_Value = self.Custom_Ref_Input.text()
            Saved_Custom_Ref_Unc = self.Custom_Ref_Unc_Input.text()

        self.Data = Data
        self.Units = Units
        self.Composition = Composition
        self.Method = Method
        self.Pressure_Calibration_Study = Pressure_Calibration_Study

        self.Update_Custom_Ref_Labels()

        if Should_Preserve_Custom_Ref:
            self.Custom_Ref_Input.setText(Saved_Custom_Ref_Value)
            self.Custom_Ref_Unc_Input.setText(Saved_Custom_Ref_Unc)
            self.Custom_Ref_Enabled = Saved_Custom_Ref_Enabled
            if Saved_Custom_Ref_Enabled:
                self.Custom_Ref_Button.setChecked(True)
                self.Custom_Ref_Container.setVisible(True)
                self.Custom_Ref_Button.setText(f"✓ Using Custom {self.Ref_Label}")

        self.Clear_All_Study_Widgets()

        if not (self.Composition and self.Method):
            self.Add_Text_To_The_Select_Studies_Checkbox_Display("Select a composition and method in order to see available studies")
            self.Enable_Or_Disable_The_Continue_Button()
            return

        self.Populate_Checkboxes(Previous_Selections=Previous_Selections)
        self.Selected_Studies = self.Get_Current_Selected_Studies_For_Comparison()
        self.Enable_Or_Disable_The_Continue_Button()


    # Populate the checkbox list with studies matching the current composition and method
    def Populate_Checkboxes(self, *, Previous_Selections=None):

        if Previous_Selections is None:
            Previous_Selections = set()

        # Find all studies that match the current composition and method
        List_Of_Relevant_Studies = []
        # Check if a pressure calibration study was selected
        if self.Units == "Pressure (GPa)" and self.Pressure_Calibration_Study is not None:
            # Check the workflow type from the pressure calibration study
            Pressure_Calibration_Study_Workflow_Type = self.Pressure_Calibration_Study.get("Workflow Type")
            # If the workflow type is use a pressure calibration study with the original composition and method
            if Pressure_Calibration_Study_Workflow_Type == "Use a Pressure Calibration Study with the Original Composition and Method":
                # Find the original composition and method
                Pressure_Calibration_Study_Composition = self.Composition
                Pressure_Calibration_Study_Method = self.Method
                Selected_Pressure_Calibration_Study = self.Pressure_Calibration_Study.get("Selected Pressure Calibration Study")
                # Loop through all studies
                for Calibration_Key, Calibration_Data in Calibration_Metadata.items():
                    Study_Composition = Calibration_Data.get("Composition", "")
                    Study_Method = Calibration_Data.get("Method", "")
                    # Check if the calibration has the selected composition and method
                    if Study_Composition == self.Composition and Study_Method == self.Method and Calibration_Key != Selected_Pressure_Calibration_Study:
                        # Add the calibration study to the list of relevant studies
                        List_Of_Relevant_Studies.append((Calibration_Key, Calibration_Data))
            # If the workflow type is use a pressure calibration study with a different composition and method
            elif Pressure_Calibration_Study_Workflow_Type == "Use a Pressure Calibration Study with a Different Composition and Method": 
                # Find the different composition and method
                Pressure_Calibration_Study_Composition = self.Pressure_Calibration_Study.get("Different Composition")
                Pressure_Calibration_Study_Method = self.Pressure_Calibration_Study.get("Different Method")
                Selected_Pressure_Calibration_Study = self.Pressure_Calibration_Study.get("Different Pressure Calibration Study")
                Target_Pressure_Calibration_Study = self.Pressure_Calibration_Study.get("Target Pressure Calibration Study")
                # Loop through all studies
                for Calibration_Key, Calibration_Data in Calibration_Metadata.items():
                    Study_Composition = Calibration_Data.get("Composition", "")
                    Study_Method = Calibration_Data.get("Method", "")
                    # Check if the calibration has the different selected composition and method
                    # Exclude both the bridge study and the target study used for composition conversion
                    if Study_Composition == Pressure_Calibration_Study_Composition and Study_Method == Pressure_Calibration_Study_Method and Calibration_Key != Selected_Pressure_Calibration_Study and Calibration_Key != Target_Pressure_Calibration_Study:
                        # Add the calibration study to the list of relevant studies
                        List_Of_Relevant_Studies.append((Calibration_Key, Calibration_Data))
        
        # If no pressure calibration study was selected
        elif self.Units != "Pressure (GPa)" and self.Pressure_Calibration_Study is None:
            # Loop through all studies
            for Calibration_Key, Calibration_Data in Calibration_Metadata.items():
                Study_Composition = Calibration_Data.get("Composition", "")
                Study_Method = Calibration_Data.get("Method", "")
                # Check if the calibration has the selected composition and method
                if Study_Composition == self.Composition and Study_Method == self.Method:
                    # Add the calibration study to the list of relevant studies
                    List_Of_Relevant_Studies.append((Calibration_Key, Calibration_Data))

        # Sort alphabetically by study name
        List_Of_Relevant_Studies.sort(key=lambda x: x[1].get("Study", "").lower())

        # Look up the caution colors used to flag user-edited/user-entered calibrants
        _, _, Theme_Colors = Get_Theme()
        Caution_Color = Theme_Colors.get("Caution_Text")
        Caution_Accent_Color = Theme_Colors.get("Caution_Text_Accent")

        # Create a checkbox for each matching study
        for Calibration_Key, Study_Metadata in List_Of_Relevant_Studies:
            is_user_edited = Study_Metadata.get("is_user_edited", False)
            is_user_entered = Study_Metadata.get("is_user_entered", False)
            Is_User_Calibrant = is_user_edited or is_user_entered
            prefix = "* " if Is_User_Calibrant else ""
            Study_Name = prefix + Study_Metadata.get("Study", Calibration_Key)
            Composition_Val = Study_Metadata.get("Composition", "")
            Method_Val = Study_Metadata.get("Method", "")
            Equation_Of_State = Study_Metadata.get("Equation of State", "")
            is_K0_fixed = Study_Metadata.get("is_K0_fixed", "")
            cal_to_Study_Name = Study_Metadata.get("cal_to_name", "")
            Maximum_Pressure = Study_Metadata.get("Maximum Pressure", "")
            Pressure_Transmitting_Medium = Study_Metadata.get("PTM", "")
            # Build a more detailed checkbox text
            Checkbox_Text = (
                f"{Study_Name}"
                f" | "
                # f"Composition: {Composition_Val}"
                f"{Composition_Val}"
                f" | "
                # f"Method: {Method_Val}"
                f"{Method_Val}"
                f" | "
                # f"Equation of State: {Equation_Of_State}"
                f"{Equation_Of_State}"
                f" | "
                f"K0 Fixed: {is_K0_fixed}"
                f" | "
                f"cal_to: {cal_to_Study_Name}"
                f" | "
                f"Max Pressure: {Maximum_Pressure} GPa"
                f" | "
                f"PTM: {Pressure_Transmitting_Medium}"
            )
            # Build the display label (used for tracking selections across refreshes)
            Study_Label_String = Checkbox_Text
            # Build HTML versions of the label so only the leading "*" is shown in the caution
            # color — a hover variant is also built so it can switch to the accent color on hover.
            Checkbox_Display_Html = html.escape(Checkbox_Text)
            Checkbox_Display_Html_Hover = Checkbox_Display_Html
            if Is_User_Calibrant:
                Checkbox_Display_Html = Checkbox_Display_Html.replace(
                    "*", f'<span style="color: {Caution_Color};">*</span>', 1
                )
                Checkbox_Display_Html_Hover = Checkbox_Display_Html_Hover.replace(
                    "*", f'<span style="color: {Caution_Accent_Color};">*</span>', 1
                )
            # Create a display for each study
            Study_Option_Checkbox_Display = CheckboxRow()
            Study_Option_Checkbox_Outer_Layout = QVBoxLayout()
            Study_Option_Checkbox_Outer_Layout.setContentsMargins(0, 0, 0, 0)
            Study_Option_Checkbox_Outer_Layout.setSpacing(0)
            Study_Option_Checkbox_Layout = QHBoxLayout()
            Study_Option_Checkbox_Layout.setContentsMargins(6, 4, 6, 4)
            Study_Option_Checkbox_Layout.setSpacing(6)
            # Create the checkbox indicator (no text — text is shown in the label)
            Study_Option_Checkbox = QCheckBox()
            Study_Option_Checkbox.setObjectName("Checkbox")
            Study_Option_Checkbox.stateChanged.connect(self.When_A_Checkbox_State_Is_Changed)
            Study_Option_Checkbox_Layout.addWidget(Study_Option_Checkbox)
            # Create the wrapping text label — clicking it toggles the checkbox
            Study_Text_Label = QLabel(Checkbox_Display_Html)
            Study_Text_Label.setObjectName("CollapsibleContentLabel")
            Study_Text_Label.setWordWrap(True)
            Study_Text_Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            Study_Text_Label.mousePressEvent = lambda _, cb=Study_Option_Checkbox: cb.setChecked(not cb.isChecked())
            Study_Option_Checkbox_Layout.addWidget(Study_Text_Label, stretch=1)
            # Create the preview YAML button
            Preview_Calibration_File_Button = QPushButton("Preview Calibrant")
            Preview_Calibration_File_Button.setObjectName("Preview_Calibration_Button")
            Preview_Calibration_File_Button.setFixedHeight(32)
            Preview_Calibration_File_Button.setToolTip(f"Preview the calibration YAML file for {Study_Label_String}")
            # Connect the preview button to preview calibration file for file path
            File_Path = Study_Metadata.get("file_path")
            Preview_Calibration_File_Button.clicked.connect(lambda _checked=False, fp=File_Path: Preview_Calibration_File_For_File_Path(self, fp))
            # Add the preview calibration file button to the layout for each study
            Study_Option_Checkbox_Layout.addWidget(Preview_Calibration_File_Button)

            # Add the checkbox row to the outer (per-study) layout
            Study_Option_Checkbox_Outer_Layout.addLayout(Study_Option_Checkbox_Layout)

            # Show a footnote directly under this checkbox when it is user-edited or user-entered
            if Is_User_Calibrant:
                Footnote_Style_Normal = f"font-size: 8pt; color: {Caution_Color};"
                Footnote_Style_Hover = f"font-size: 8pt; color: {Caution_Accent_Color};"
                Per_Checkbox_Footnote = QLabel("* indicates user edited or entered calibrant")
                Per_Checkbox_Footnote.setObjectName("CollapsibleContentLabel")
                Per_Checkbox_Footnote.setStyleSheet(Footnote_Style_Normal)
                Per_Checkbox_Footnote.setContentsMargins(60, 0, 6, 4)
                Study_Option_Checkbox_Outer_Layout.addWidget(Per_Checkbox_Footnote)

                # Swap the "*" and footnote to the accent color while this row is hovered
                def On_Checkbox_Row_Hover_Changed(
                    Is_Hovered,
                    Label=Study_Text_Label,
                    Normal_Html=Checkbox_Display_Html,
                    Hover_Html=Checkbox_Display_Html_Hover,
                    Footnote=Per_Checkbox_Footnote,
                    Normal_Style=Footnote_Style_Normal,
                    Hover_Style=Footnote_Style_Hover,
                ):
                    Label.setText(Hover_Html if Is_Hovered else Normal_Html)
                    Footnote.setStyleSheet(Hover_Style if Is_Hovered else Normal_Style)

                Study_Option_Checkbox_Display.Add_Hover_Callback(On_Checkbox_Row_Hover_Changed)

            # Add each study layout to the list of studies display
            Study_Option_Checkbox_Display.setLayout(Study_Option_Checkbox_Outer_Layout)
            self.List_Of_Studies_Layout.addWidget(Study_Option_Checkbox_Display)

            # Show or hide the preview button based on the setting
            Preview_Calibration_File_Button.setVisible(self.Show_Preview)
            # Track which checkboxes are selected
            self.List_Of_Checkboxes.append((Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata))

            # Restore previous selections if they are still available
            if Calibration_Key in Previous_Selections:
                Study_Option_Checkbox.setChecked(True)

        # If no studies were found, show a placeholder
        if not self.List_Of_Checkboxes:
            self.Add_Text_To_The_Select_Studies_Checkbox_Display(f"No studies available for a composition: {self.Composition} and method: {self.Method}")



    # Get the current selected studies for comparison
    def Get_Current_Selected_Studies_For_Comparison(self):

        # Create a list to store the currently selected studies for comparison
        Currently_Selected_Studies_For_Comparison = []

        # Loop through the list of checkboxes
        for Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata in self.List_Of_Checkboxes:
            # Check if the study is selected
            if Study_Option_Checkbox.isChecked():
                # If the study is selected, add it to the list
                Currently_Selected_Studies_For_Comparison.append({"Study Label": Study_Label_String, "Calibration Key": Calibration_Key, "Study Metadata": Study_Metadata})

        # Return the list of currently selected studies for comparison
        return Currently_Selected_Studies_For_Comparison


    # Create the select studies for comparison display
    def Create_The_Select_Studies_For_Comparison_Display(self):

        # Create the select studies for comparison display
        self.setObjectName("CollapsibleContent")
        Select_Studies_For_Comparison_Display = QVBoxLayout(self)
        Select_Studies_For_Comparison_Display.setContentsMargins(5, 5, 5, 5)
        Select_Studies_For_Comparison_Display.setSpacing(8)

        # Create the layout for the select all and deselect all buttons
        Button_Layout = QHBoxLayout()

        # Create the select all button
        self.Select_All_Checkboxes_Button = QPushButton("Select All")
        self.Select_All_Checkboxes_Button.setObjectName("Primary_Button")
        self.Select_All_Checkboxes_Button.setFixedHeight(32)
        Button_Layout.addWidget(self.Select_All_Checkboxes_Button)

        # Create the deselect all button
        self.Deselect_All_Checkboxes_Button = QPushButton("Deselect All")
        self.Deselect_All_Checkboxes_Button.setObjectName("Secondary_Button")
        self.Deselect_All_Checkboxes_Button.setFixedHeight(32)
        Button_Layout.addWidget(self.Deselect_All_Checkboxes_Button)

        # Add stretch to push the buttons to the left
        Button_Layout.addStretch()

        # Add the button layout to the main layout
        Select_Studies_For_Comparison_Display.addLayout(Button_Layout)

        # Create the container for the list of study checkboxes
        self.List_Of_Studies_Display = QWidget()
        self.List_Of_Studies_Display.setObjectName("CollapsibleSubContainer")
        self.List_Of_Studies_Layout = QVBoxLayout(self.List_Of_Studies_Display)
        self.List_Of_Studies_Layout.setContentsMargins(5, 5, 5, 5)
        self.List_Of_Studies_Layout.setSpacing(8)
        self.List_Of_Studies_Layout.setAlignment(Qt.AlignTop)

        # Show initial placeholder (no composition/method selected yet)
        self.Add_Text_To_The_Select_Studies_Checkbox_Display("Select a composition and method to see available studies")

        # Add the list of studies directly to the main layout (window handles scrolling)
        Select_Studies_For_Comparison_Display.addWidget(self.List_Of_Studies_Display)

        # Curstom reference
        Input_Volume_Unit = self.Data.get("Volume Unit", "") if self.Data else ""
        
        if self.Method == "XRD":
            Ref_Label = "V₀ (Initial Volume)"
            Ref_Unit = Input_Volume_Unit
        elif self.Method == "Luminescence":
            Ref_Label = "λ₀ (Initial Wavelength)"
            Ref_Unit = "nm"
        elif self.Method == "Raman":
            Ref_Label = "ν₀ (Initial Wavenumber)"
            Ref_Unit = "cm⁻¹"
        else:
            Ref_Label = "Reference Value"
            Ref_Unit = ""
        
        # Store reference info for later use
        self.Ref_Label = Ref_Label
        self.Ref_Unit = Ref_Unit
        self.Custom_Ref_Enabled = False
        
        # Custom reference toggle button
        self.Custom_Ref_Button = QPushButton(f"Use Custom {Ref_Label}")
        self.Custom_Ref_Button.setObjectName("Secondary_Button")
        self.Custom_Ref_Button.setCheckable(True)
        self.Custom_Ref_Button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.Custom_Ref_Button.setFixedHeight(32)
        self.Custom_Ref_Button.clicked.connect(self.Toggle_Custom_Ref_Section)
        Select_Studies_For_Comparison_Display.addWidget(self.Custom_Ref_Button)
        
        # Custom reference input container (hidden by default)
        self.Custom_Ref_Container = QWidget()
        self.Custom_Ref_Container.setObjectName("CollapsibleSubContainer")
        Custom_Ref_Layout = QVBoxLayout(self.Custom_Ref_Container)
        Custom_Ref_Layout.setContentsMargins(10, 10, 10, 10)
        Custom_Ref_Layout.setSpacing(8)

        # Info label
        self.Custom_Ref_Info_Label = QLabel(f"Override the calibration's {Ref_Label} with your own value.\nThis does not modify the YAML files.")
        self.Custom_Ref_Info_Label.setObjectName("CollapsibleContentLabel")
        self.Custom_Ref_Info_Label.setWordWrap(True)
        Custom_Ref_Layout.addWidget(self.Custom_Ref_Info_Label)

        # Value input row
        Value_Row = QHBoxLayout()
        self.Custom_Ref_Value_Label = QLabel(f"{Ref_Label} ({Ref_Unit}):")
        self.Custom_Ref_Value_Label.setObjectName("CollapsibleContentLabel")
        Value_Row.addWidget(self.Custom_Ref_Value_Label)

        self.Custom_Ref_Input = QLineEdit()
        self.Custom_Ref_Input.setObjectName("LineEdit")
        self.Custom_Ref_Input.setPlaceholderText(f"Enter {Ref_Label}...")
        self.Custom_Ref_Input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Custom_Ref_Input.setFixedHeight(28)
        Value_Row.addWidget(self.Custom_Ref_Input)
        Custom_Ref_Layout.addLayout(Value_Row)

        # Uncertainty input row
        Unc_Row = QHBoxLayout()
        self.Custom_Ref_Unc_Label = QLabel(f"Uncertainty ({Ref_Unit}):")
        self.Custom_Ref_Unc_Label.setObjectName("CollapsibleContentLabel")
        Unc_Row.addWidget(self.Custom_Ref_Unc_Label)
        
        self.Custom_Ref_Unc_Input = QLineEdit()
        self.Custom_Ref_Unc_Input.setObjectName("LineEdit")
        self.Custom_Ref_Unc_Input.setPlaceholderText("Enter uncertainty (optional)...")
        self.Custom_Ref_Unc_Input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Custom_Ref_Unc_Input.setFixedHeight(28)
        Unc_Row.addWidget(self.Custom_Ref_Unc_Input)
        Custom_Ref_Layout.addLayout(Unc_Row)
        
        self.Custom_Ref_Container.setVisible(False)
        Select_Studies_For_Comparison_Display.addWidget(self.Custom_Ref_Container)
        
        # Only show custom reference button for non-Pressure units
        if self.Units == "Pressure (GPa)":
            self.Custom_Ref_Button.setVisible(False)

        # Preview conversions button (optional)
        if self.Show_Preview:
            Preview_Button = QPushButton("Preview Conversions")
            Preview_Button.setObjectName("Primary_Button")
            Preview_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            Preview_Button.setFixedHeight(32)
            Select_Studies_For_Comparison_Display.addWidget(Preview_Button)
            Preview_Button.clicked.connect(self.Preview_Conversions)

        # Create the continue button
        self.Continue_Button = QPushButton("Continue")
        self.Continue_Button.setObjectName("Primary_Button")
        self.Continue_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Continue_Button.setEnabled(False)
        self.Continue_Button.setFixedHeight(32)
        if self.Show_Continue_Button:
            self.Continue_Button.show()
        else:
            self.Continue_Button.hide()

        # Add the continue button to the main layout
        Select_Studies_For_Comparison_Display.addWidget(self.Continue_Button)
        # Absorb extra vertical space so the section doesn't grow blank
        Select_Studies_For_Comparison_Display.addStretch()



    # Connect the text boxes and buttons to their functions
    def Connect_Signals(self):

        # Connect the select all to selecting all checkboxes
        self.Select_All_Checkboxes_Button.clicked.connect(self.Select_All_Checkboxes)
        # Connect the deselect all to deselecting all checkboxes
        self.Deselect_All_Checkboxes_Button.clicked.connect(self.Deselect_All_Checkboxes)
        # Connect the continue button to when the continue button is clicked
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)
        # Keep self.Data in sync as soon as the user edits the custom reference value/uncertainty,
        # instead of only when a study checkbox changes, Continue is clicked, or Preview is clicked
        self.Custom_Ref_Input.textChanged.connect(self.Apply_Custom_Reference_To_Data)
        self.Custom_Ref_Unc_Input.textChanged.connect(self.Apply_Custom_Reference_To_Data)



    # Clear ALL child widgets from the studies layout (checkboxes, preview buttons, and placeholder labels)
    def Clear_All_Study_Widgets(self):

        # First, disconnect and remove tracked checkboxes and their preview buttons
        for Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata in self.List_Of_Checkboxes:
            try:
                Study_Option_Checkbox.stateChanged.disconnect(self.When_A_Checkbox_State_Is_Changed)
            except RuntimeError:
                pass  # Already disconnected
        self.List_Of_Checkboxes.clear()

        # Remove all widgets from the layout (row widgets, placeholder labels, etc.)
        while self.List_Of_Studies_Layout.count() > 0:
            Item = self.List_Of_Studies_Layout.takeAt(0)
            Widget = Item.widget()
            if Widget is not None:
                Widget.setParent(None)
                Widget.deleteLater()



    # Display text in the list of studies checkbox layout
    def Add_Text_To_The_Select_Studies_Checkbox_Display(self, Message):

        # Add a placeholder label
        Placeholder_Label = QLabel(Message)
        Placeholder_Label.setStyleSheet("color: #999;")
        Placeholder_Label.setWordWrap(True)
        # Add the placeholder label to the list of studies checkbox layout
        self.List_Of_Studies_Layout.addWidget(Placeholder_Label)



    # When a study is selected or deselected, update the label and the continue button state
    def When_A_Checkbox_State_Is_Changed(self, State=None):

        # Find the currently selected studies for comparison
        List_Of_Currently_Selected_Studies_For_Comparison = self.Get_Current_Selected_Studies_For_Comparison()
        Number_Of_Studies_Currently_Selected = len(List_Of_Currently_Selected_Studies_For_Comparison)

        # Update the continue button state based on the new selection
        self.Enable_Or_Disable_The_Continue_Button()

        # Send out list of selected studies
        if not self.Show_Continue_Button:
            self.Send_Out_Selected_Studies_For_Comparison()



    # Check all checkboxes in the list of checkboxes
    def Select_All_Checkboxes(self):

        # Find all the checkboxes
        for Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata in self.List_Of_Checkboxes:
            # Check the checkbox
            Study_Option_Checkbox.setChecked(True)



    # Uncheck all checkboxes in the list of checkboxes
    def Deselect_All_Checkboxes(self):

        # Find all the checkboxes
        for Study_Option_Checkbox, Preview_Calibration_File_Button, Study_Label_String, Calibration_Key, Study_Metadata in self.List_Of_Checkboxes:
            # Uncheck the checkbox
            Study_Option_Checkbox.setChecked(False)



    # Update the custom reference button and inner labels to match the current method and units
    def Update_Custom_Ref_Labels(self):

        # Recompute label and unit based on the current method
        Input_Volume_Unit = self.Data.get("Volume Unit", "") if self.Data else ""

        if self.Method == "XRD":
            self.Ref_Label = "V₀ (Initial Volume)"
            self.Ref_Unit = Input_Volume_Unit
        elif self.Method == "Luminescence":
            self.Ref_Label = "λ₀ (Initial Wavelength)"
            self.Ref_Unit = "nm"
        elif self.Method == "Raman":
            self.Ref_Label = "ν₀ (Initial Wavenumber)"
            self.Ref_Unit = "cm⁻¹"
        else:
            self.Ref_Label = "Reference Value"
            self.Ref_Unit = ""

        # Reset enabled state and collapse the section
        self.Custom_Ref_Enabled = False
        self.Custom_Ref_Button.setChecked(False)
        self.Custom_Ref_Container.setVisible(False)
        self.Custom_Ref_Input.clear()
        self.Custom_Ref_Unc_Input.clear()

        # Update all label texts
        self.Custom_Ref_Button.setText(f"Use Custom {self.Ref_Label}")
        self.Custom_Ref_Info_Label.setText(f"Override the calibration's {self.Ref_Label} with your own value.\nThis does not modify the YAML files.")
        self.Custom_Ref_Value_Label.setText(f"{self.Ref_Label} ({self.Ref_Unit}):")
        self.Custom_Ref_Input.setPlaceholderText(f"Enter {self.Ref_Label}...")
        self.Custom_Ref_Unc_Label.setText(f"Uncertainty ({self.Ref_Unit}):")

        # Show or hide the button based on units (hidden for pressure input)
        self.Custom_Ref_Button.setVisible(self.Units != "Pressure (GPa)")


    # Toggle the custom reference value section visibility
    def Toggle_Custom_Ref_Section(self):
        self.Custom_Ref_Enabled = self.Custom_Ref_Button.isChecked()
        self.Custom_Ref_Container.setVisible(self.Custom_Ref_Enabled)

        # Update button text to indicate state
        if self.Custom_Ref_Enabled:
            self.Custom_Ref_Button.setText(f"✓ Using Custom {self.Ref_Label}")
        else:
            self.Custom_Ref_Button.setText(f"Use Custom {self.Ref_Label}")
            # Clear the inputs when disabled
            self.Custom_Ref_Input.clear()
            self.Custom_Ref_Unc_Input.clear()

        # Immediately reflect the toggle in self.Data instead of waiting for a
        # checkbox change, Continue click, or Preview click to pick it up
        self.Apply_Custom_Reference_To_Data()


    # Get the custom reference value and uncertainty if enabled
    def Get_Custom_Reference_Value(self):
        if not self.Custom_Ref_Enabled:
            return None
        
        Value_Text = self.Custom_Ref_Input.text().strip()
        if not Value_Text:
            return None
        
        try:
            Value = float(Value_Text)
        except ValueError:
            return None
        
        # Get uncertainty (optional)
        Unc_Text = self.Custom_Ref_Unc_Input.text().strip()
        Uncertainty = 0.0
        if Unc_Text:
            try:
                Uncertainty = float(Unc_Text)
            except ValueError:
                Uncertainty = 0.0
        
        # Determine the type based on method
        if self.Method == "XRD":
            Ref_Type = "V0"
        elif self.Method == "Luminescence":
            Ref_Type = "lambda_0"
        elif self.Method == "Raman":
            Ref_Type = "nu_0"
        else:
            Ref_Type = "unknown"
        
        return {'value': Value, 'uncertainty': Uncertainty, 'type': Ref_Type, 'method': self.Method}


    # Sync the current custom reference UI state into self.Data (set when enabled with a valid
    # value, cleared otherwise) so any downstream calculation always sees the latest state.
    def Apply_Custom_Reference_To_Data(self):
        if self.Data is None:
            return
        Custom_Ref = self.Get_Custom_Reference_Value()
        if Custom_Ref is not None:
            self.Data['custom_reference'] = Custom_Ref
        else:
            self.Data.pop('custom_reference', None)


    # Preview conversions with selected studies
    def Preview_Conversions(self):
        Selected_Studies = self.Get_Current_Selected_Studies_For_Comparison()
        if not Selected_Studies:
            Warning_Message(self, "No Studies Selected For Preview")
            return

        # Get custom reference if enabled
        self.Apply_Custom_Reference_To_Data()

        # Build dataframe with selected studies (extract string keys from study dicts)
        Selected_Study_Keys = [study["Calibration Key"] for study in Selected_Studies]
        File_Ok, Units_Ok, Error_Msg, DF = Build_Dataframe(self.Data, self.Units, self.Composition, self.Method, Translate_Pressure_Calibration_Study(self.Pressure_Calibration_Study), Selected_Study_Keys)
        
        if not File_Ok or not Units_Ok or DF is None or DF.empty:
            Warning_Message(self, "Preview CSV Error", message=Error_Msg or "No data to preview.")
            return
        
        def _export_preview():
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, "Export Converted Pressures", "", "CSV (*.csv)")
            if path:
                DF.to_csv(path, index=False, encoding="utf-8-sig")

        Preview_Dialog = Data_Preview_Dialog(DF, self, Export_Callback=_export_preview)
        Preview_Dialog.show()



    # When the continue button is clicked, check if any studies have been selected
    def When_The_Continue_Button_Is_Clicked(self):

        # Check if composition and method have been selected
        if not (self.Composition and self.Method):
            Warning_Message(self, "Missing Composition Or Method Selection")
            return

        # Find the currently selected studies for comparison
        List_Of_Currently_Selected_Studies = self.Get_Current_Selected_Studies_For_Comparison()

        if List_Of_Currently_Selected_Studies:
            # Send out the selection
            self.Send_Out_Selected_Studies_For_Comparison()
        else:
            # Show a warning with Yes/No options
            Reply = Warning_Message(
                self,
                "Continue Without Studies",
                Buttons=QMessageBox.Yes | QMessageBox.No,
                Default_Button=QMessageBox.No,
            )
            if Reply == QMessageBox.Yes:
                self.Send_Out_Selected_Studies_For_Comparison()



    # Enable or disable the continue button based on whether a valid selection is made
    def Enable_Or_Disable_The_Continue_Button(self):

        # Always enable so the user can click and get error messages
        self.Continue_Button.setEnabled(True)



    # Send out the current selection through the callback
    def Send_Out_Selected_Studies_For_Comparison(self):

        if self.Once_A_Change_Is_Made:
            # Apply or clear the custom reference on self.Data for this session only
            self.Apply_Custom_Reference_To_Data()

            # Send out the current list of selected studies
            self.Once_A_Change_Is_Made(self.Get_Current_Selected_Studies_For_Comparison())




