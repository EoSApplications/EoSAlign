# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox, QVBoxLayout)
from PySide6.QtCore import Qt
    # Load local functions from local files
from EoS_Math.Build_Dataframe import All_Compositions
from Collapsible_Sections import Dropdown
from Reference_Values_And_Units import Material_Information
from Message_Manager import Warning_Message





# Create the Select Composition content
class Select_Composition(QWidget):
    def __init__(self, *, Application="EoSAlign", Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Application = Application
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Create the select composition display
        self.Create_The_Select_Composition_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the select composition section to its initial state
    def Reset(self):

        # Set the dropdown to have no selection initially
        self.Composition_Dropdown_Display.setCurrentIndex(-1)
        # Reset the continue button appearance
        self.Enable_Or_Disable_The_Continue_Button()


    # Refresh the select composition section, optionally filtering to Allowed_Compositions
    def Refresh(self, *, Allowed_Compositions=None, **context):
        Current_Selection = self.Get_Current_Selected_Composition()

        # Rebuild the dropdown (filtered or full list), then restore the previous selection silently
        Compositions_To_Show = sorted((c for c in All_Compositions if c in Allowed_Compositions) if Allowed_Compositions is not None else All_Compositions, key=lambda c: Material_Information.get(c, {}).get('Display_Name', c))
        self.Composition_Dropdown_Display.blockSignals(True)
        self.Composition_Dropdown_Display.clear()
        for Composition_Option in Compositions_To_Show:
            Display_Label = Material_Information.get(Composition_Option, {}).get('Display_Name', Composition_Option)
            self.Composition_Dropdown_Display.addItem(Display_Label, Composition_Option)
        if Current_Selection:
            Index = self.Composition_Dropdown_Display.findData(Current_Selection)
            self.Composition_Dropdown_Display.setCurrentIndex(Index if Index >= 0 else -1)
        else:
            self.Composition_Dropdown_Display.setCurrentIndex(-1)
        self.Composition_Dropdown_Display.blockSignals(False)

        self.Enable_Or_Disable_The_Continue_Button()


    # Get the current selected composition
    def Get_Current_Selected_Composition(self):

        # Return the composition key stored as item data (not the display label)
        if self.Composition_Dropdown_Display.currentIndex() < 0:
            return None

        return self.Composition_Dropdown_Display.currentData() or None



    # Create the select composition display
    def Create_The_Select_Composition_Display(self):

        # Create the select composition display
        self.setObjectName("CollapsibleContent")
        Select_Composition_Display = QVBoxLayout(self)
        Select_Composition_Display.setContentsMargins(5, 5, 5, 5)
        Select_Composition_Display.setSpacing(8)

        # Create the select composition layout
        self.Select_Composition_Layout = QWidget()
        self.Select_Composition_Layout.setObjectName("CollapsibleSubContainer")
        Select_Composition_Layout = QVBoxLayout(self.Select_Composition_Layout)
        Select_Composition_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Composition_Layout.setSpacing(8)
        Select_Composition_Display.addWidget(self.Select_Composition_Layout)

        # Create the dropdown for selecting the composition
        Select_Composition_Dropdown_Layout = QHBoxLayout()
        Select_Composition_Label = QLabel("Select Composition:")
        Select_Composition_Label.setObjectName("CollapsibleContentLabel")
        Select_Composition_Dropdown_Layout.addWidget(Select_Composition_Label)
        # Get a list of possible compositions sorted by their display label
        List_Of_Compositions = sorted(All_Compositions, key=lambda c: Material_Information.get(c, {}).get('Display_Name', c))
        self.Composition_Dropdown_Display = Dropdown()
        self.Composition_Dropdown_Display.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Composition_Dropdown_Display.setPlaceholderText("Select a composition...")
        # Add each composition using its display label as visible text and the key as item data
        for Composition_Option in List_Of_Compositions:
            Display_Label = Material_Information.get(Composition_Option, {}).get('Display_Name', Composition_Option)
            self.Composition_Dropdown_Display.addItem(Display_Label, Composition_Option)
        # Set the dropdown to have no selection initially
        self.Composition_Dropdown_Display.setCurrentIndex(-1)
        Select_Composition_Dropdown_Layout.addWidget(self.Composition_Dropdown_Display, stretch=1)

        # Add the composition dropdown to the select composition display
        Select_Composition_Layout.addLayout(Select_Composition_Dropdown_Layout)

        # Create the continue button
        self.Continue_Button = QPushButton("Continue")
        self.Continue_Button.setObjectName("Primary_Button")
        self.Continue_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Start with the continue button disabled
        self.Continue_Button.setEnabled(False)
        self.Continue_Button.setFixedHeight(32)
        # Show or hide the continue button based on the Show_Continue_Button flag
        if self.Show_Continue_Button:
            self.Continue_Button.show()
        else:
            self.Continue_Button.hide()

        # Add the continue button to the select composition display
        Select_Composition_Layout.addWidget(self.Continue_Button)



    # Connect the text boxes and buttons to their functions
    def Connect_Signals(self):

        # Connect the composition dropdown to when the selected composition is changed
        self.Composition_Dropdown_Display.currentIndexChanged.connect(self.When_Selected_Composition_Is_Changed)
        # Connect the continue button to when the continue button is clicked
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)



    # When the selected composition is changed check if it is a valid selection and enable the continue button
    def When_Selected_Composition_Is_Changed(self):

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()

        # In All-at-Once Application, update the selected composition immediately
        if not self.Show_Continue_Button and self.Get_Current_Selected_Composition() is not None:
            self.Send_Out_Selected_Composition()


    # When the continue button is clicked, check if a composition has been selected
    def When_The_Continue_Button_Is_Clicked(self):

        # Find the currently selected composition
        Current_Selected_Composition = self.Get_Current_Selected_Composition()

        # Show a warning if no composition has been selected
        if not Current_Selected_Composition:
            Warning_Message(self, "Missing Composition Selection")
            return

        # Send out the selection from the select composition section
        self.Send_Out_Selected_Composition()


    # Enable or disable the continue button based on whether a valid selection is made
    def Enable_Or_Disable_The_Continue_Button(self):

        # Always enable the continue button so the error messages will be shown
        self.Continue_Button.setEnabled(True)


    # Send out the current selection through the callback
    def Send_Out_Selected_Composition(self):

        # Fire the callback with the current selection
        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Get_Current_Selected_Composition())




