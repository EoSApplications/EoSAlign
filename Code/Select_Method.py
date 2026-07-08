# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox, QVBoxLayout)
from PySide6.QtCore import Qt
    # Load local functions from local files
from Reference_Values_And_Units import Method_Units
from Collapsible_Sections import Dropdown
from Message_Manager import Warning_Message





# Create the select method content
class Select_Method(QWidget):
    def __init__(self, *, Application="EoSAlign", Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Application = Application
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Create the select method display
        self.Create_The_Select_Method_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the select method section to its initial state
    def Reset(self):

        # Set the dropdown to have no selection initially
        self.Method_Dropdown_Display.setCurrentIndex(-1)
        # Reset the continue button appearance
        self.Enable_Or_Disable_The_Continue_Button()


    # Refresh the select method section, optionally filtering to Allowed_Methods
    def Refresh(self, *, Allowed_Methods=None, **context):
        Current_Selection = self.Get_Current_Selected_Method()

        # Rebuild the dropdown (filtered or full list), then restore the previous selection silently
        Methods_To_Show = sorted((m for m in Method_Units.keys() if m in Allowed_Methods) if Allowed_Methods is not None else Method_Units.keys())
        self.Method_Dropdown_Display.blockSignals(True)
        self.Method_Dropdown_Display.clear()
        for Method_Option in Methods_To_Show:
            self.Method_Dropdown_Display.addItem(Method_Option)
        if Current_Selection:
            Index = self.Method_Dropdown_Display.findText(Current_Selection)
            self.Method_Dropdown_Display.setCurrentIndex(Index if Index >= 0 else -1)
        else:
            self.Method_Dropdown_Display.setCurrentIndex(-1)
        self.Method_Dropdown_Display.blockSignals(False)

        self.Enable_Or_Disable_The_Continue_Button()


    # Get the current selected method
    def Get_Current_Selected_Method(self):

        # Find the current selected method
        Current_Selected_Method = self.Method_Dropdown_Display.currentText()
        # If no selection has been made, make no changes
        if not Current_Selected_Method or self.Method_Dropdown_Display.currentIndex() < 0:
            return None

        # Return the current selected method
        return Current_Selected_Method



    # Create the select method display
    def Create_The_Select_Method_Display(self):

        # Create the select method display
        self.setObjectName("CollapsibleContent")
        Select_Method_Display = QVBoxLayout(self)
        Select_Method_Display.setContentsMargins(5, 5, 5, 5)
        Select_Method_Display.setSpacing(8)

        # Create the select method layout
        self.Select_Method_Layout = QWidget()
        self.Select_Method_Layout.setObjectName("CollapsibleSubContainer")
        Select_Method_Layout = QVBoxLayout(self.Select_Method_Layout)
        Select_Method_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Method_Layout.setSpacing(8)
        Select_Method_Display.addWidget(self.Select_Method_Layout)

        # Create the dropdown for selecting the method
        Select_Method_Dropdown_Layout = QHBoxLayout()
        Select_Method_Label = QLabel("Select Method:")
        Select_Method_Label.setObjectName("CollapsibleContentLabel")
        Select_Method_Dropdown_Layout.addWidget(Select_Method_Label)
        # Get a list of possible methods
        List_Of_Methods = sorted(Method_Units.keys())
        self.Method_Dropdown_Display = Dropdown()
        self.Method_Dropdown_Display.setObjectName("Dropdown")
        # Set the default text for the dropdown display
        self.Method_Dropdown_Display.setPlaceholderText("Select a method...")
        # Add all other methods to the list of options
        for Method_Option in List_Of_Methods:
            self.Method_Dropdown_Display.addItem(Method_Option)
        # Set the dropdown to have no selection initially
        self.Method_Dropdown_Display.setCurrentIndex(-1)
        Select_Method_Dropdown_Layout.addWidget(self.Method_Dropdown_Display, stretch=1)

        # Add the method dropdown to the select method display
        Select_Method_Layout.addLayout(Select_Method_Dropdown_Layout)

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

        # Add the continue button to the select method display
        Select_Method_Layout.addWidget(self.Continue_Button)



    # Connect the text boxes and buttons to their functions
    def Connect_Signals(self):

        # Connect the method dropdown to when the selected method is changed
        self.Method_Dropdown_Display.currentIndexChanged.connect(self.When_Selected_Method_Is_Changed)
        # Connect the continue button to when the continue button is clicked
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)



    # When the selected method is changed check if it is a valid selection and enable the continue button
    def When_Selected_Method_Is_Changed(self):

        # Update the continue button
        self.Enable_Or_Disable_The_Continue_Button()

        # In All-at-Once Application, update the selected method immediately
        if not self.Show_Continue_Button and self.Get_Current_Selected_Method() is not None:
            self.Sent_Out_Selected_Method()


    # When the continue button is clicked, check if a method has been selected
    def When_The_Continue_Button_Is_Clicked(self):

        # Find the currently selected method
        Current_Selected_Method = self.Get_Current_Selected_Method()

        # Show a warning if no method has been selected
        if not Current_Selected_Method:
            Warning_Message(self, "Missing Method Selection")
            return

        # Send out the selection from the select method section
        self.Sent_Out_Selected_Method()


    # Enable or disable the continue button based on whether a valid selection is made
    def Enable_Or_Disable_The_Continue_Button(self):

        # Always enable the continue button so the error messages will be shown
        self.Continue_Button.setEnabled(True)


    # Send out the current selection through the callback
    def Sent_Out_Selected_Method(self):

        # Fire the callback with the current selection
        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Get_Current_Selected_Method())




