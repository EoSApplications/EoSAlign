# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QSizePolicy, QMessageBox)
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from Reference_Values_And_Units import Function_Information
from Fitting_Models_And_Units import Get_Models_For_Method
from Fitting_Display_Helpers import Equation_Label, Number_Box, Make_A_Spacer, Reveal_Container, Render_Equation_Pixmap





# The space between a label and its number box (px); about the width of one space in the label font
Label_To_Box_Space = 5





# Create the select fitting models content
class Select_Fitting_Models(QWidget):
    def __init__(self, *, Once_A_Fit_Is_Requested=None, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Once_A_Fit_Is_Requested = Once_A_Fit_Is_Requested

        # Track the widgets that are rebuilt every time the method changes
        self.Method = None
        self.Model_Checkboxes = {}      # model name -> checkbox
        self.Parameter_Panels = {}      # model name -> collapsible section holding that model's parameters
        self.Parameter_Widgets = {}     # model name -> {parameter name -> {"guess", "fix", "unc"}}
        self.Composition_Inputs = {}    # model name -> {"Z", "atoms"} for the AP2 and H12 models

        # Create the select fitting models display
        self.Create_The_Select_Fitting_Models_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the select fitting models section to its initial state
    def Reset(self):

        self.Reference_Pressure_Box.setValue(0.0)
        self.Refresh(Method=self.Method)


    # Rebuild the model list for a method
    def Refresh(self, *, Method=None, **context):

        self.Method = Method
        self.Rebuild_The_Model_List()



    # Create the select fitting models display
    def Create_The_Select_Fitting_Models_Display(self):

        # Create the select fitting models display
        self.setObjectName("CollapsibleContent")
        Select_Fitting_Models_Display = QVBoxLayout(self)
        Select_Fitting_Models_Display.setContentsMargins(5, 5, 5, 5)
        Select_Fitting_Models_Display.setSpacing(8)

        # Create the select fitting models layout
        self.Select_Fitting_Models_Layout = QWidget()
        self.Select_Fitting_Models_Layout.setObjectName("CollapsibleSubContainer")
        Select_Fitting_Models_Layout = QVBoxLayout(self.Select_Fitting_Models_Layout)
        Select_Fitting_Models_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Fitting_Models_Layout.setSpacing(8)
        Select_Fitting_Models_Display.addWidget(self.Select_Fitting_Models_Layout)

        # Create the reference pressure row (only shown for XRD)
        Reference_Pressure_Layout = QHBoxLayout()
        Reference_Pressure_Layout.setContentsMargins(0, 0, 0, 0)
        Reference_Pressure_Layout.setSpacing(Label_To_Box_Space)
        Reference_Pressure_Label = QLabel("P₀ (GPa) – reference pressure:")
        Reference_Pressure_Label.setObjectName("CollapsibleContentLabel")
        Reference_Pressure_Layout.addWidget(Reference_Pressure_Label)
        self.Reference_Pressure_Box = Number_Box(0.0)
        Reference_Pressure_Layout.addWidget(self.Reference_Pressure_Box)
        Reference_Pressure_Layout.addStretch()
        self.Reference_Pressure_Row = QWidget()
        self.Reference_Pressure_Row.setObjectName("CollapsibleSubContainer")
        self.Reference_Pressure_Row.setLayout(Reference_Pressure_Layout)
        Select_Fitting_Models_Layout.addWidget(self.Reference_Pressure_Row)
        # Leave space below the reference pressure; it is shown with the reference pressure
        self.Space_Below_Reference_Pressure = Make_A_Spacer()
        Select_Fitting_Models_Layout.addWidget(self.Space_Below_Reference_Pressure)

        # Create the place for the model checkboxes and parameter panels
        self.Model_List_Widget = QWidget()
        self.Model_List_Widget.setObjectName("CollapsibleSubContainer")
        self.Model_List_Layout = QVBoxLayout(self.Model_List_Widget)
        self.Model_List_Layout.setContentsMargins(0, 0, 0, 0)
        self.Model_List_Layout.setSpacing(4)
        Select_Fitting_Models_Layout.addWidget(self.Model_List_Widget)

        # Create the fit button; it is the step's continue button
        self.Fit_Button = QPushButton("Fit All Checked Models")
        self.Fit_Button.setObjectName("Primary_Button")
        self.Fit_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Fit_Button.setFixedHeight(32)
        Select_Fitting_Models_Layout.addWidget(self.Fit_Button)



    # Connect the fit button to its function
    def Connect_Signals(self):

        self.Fit_Button.clicked.connect(self.When_The_Fit_Button_Is_Clicked)



    # Remove the old model checkboxes and parameter panels
    def Clear_The_Model_List(self):

        for Index in reversed(range(self.Model_List_Layout.count())):
            Item = self.Model_List_Layout.itemAt(Index)
            if Item and Item.widget():
                Item.widget().deleteLater()
                self.Model_List_Layout.removeItem(Item)
        self.Model_Checkboxes.clear()
        self.Parameter_Panels.clear()
        self.Parameter_Widgets.clear()
        self.Composition_Inputs.clear()


    # Build a checkbox, the equation and the parameter panel for every model of the current method
    def Rebuild_The_Model_List(self):

        self.Clear_The_Model_List()
        # The reference pressure is only needed for XRD
        self.Reference_Pressure_Row.setVisible(self.Method == "XRD")
        self.Space_Below_Reference_Pressure.setVisible(self.Method == "XRD")

        for Model in Get_Models_For_Method(self.Method):
            Model_Name = Model["name"]

            # Create the checkbox row with the equation next to it
            Model_Row = QWidget()
            Model_Row.setObjectName("CollapsibleSubContainer")
            Model_Row_Layout = QHBoxLayout(Model_Row)
            Model_Row_Layout.setContentsMargins(0, 0, 0, 0)
            Model_Row_Layout.setSpacing(8)
            Model_Checkbox = QCheckBox(Model_Name)
            Model_Checkbox.setObjectName("Checkbox")
            self.Model_Checkboxes[Model_Name] = Model_Checkbox
            Model_Row_Layout.addWidget(Model_Checkbox)
            # The equation comes from Function_Information in Reference_Values_And_Units
            Model_Equation_Label = Equation_Label()
            Model_Equation_Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            Latex_Equation = Function_Information.get(Model["function_key"], {}).get("Latex_Equation", "")
            Equation_Pixmap = Render_Equation_Pixmap(Latex_Equation) if Latex_Equation else None
            if Equation_Pixmap is not None:
                Model_Equation_Label.Set_Equation(Equation_Pixmap)
            Model_Row_Layout.addWidget(Model_Equation_Label, stretch=1)
            self.Model_List_Layout.addWidget(Model_Row)

            # Create the parameter panel, which is shown while the model is checked
            Parameter_Panel = Collapsible_Content_Container("Parameters", self.Build_The_Parameter_Panel(Model_Name, Model), Initially_Show_Container=True, Expanding_Content=True)
            # The panel slides open when the model is checked and closed when it is unchecked
            Parameter_Reveal = Reveal_Container(Parameter_Panel)
            self.Parameter_Panels[Model_Name] = Parameter_Reveal
            self.Model_List_Layout.addWidget(Parameter_Reveal)
            Model_Checkbox.toggled.connect(Parameter_Reveal.Set_Revealed)


    # Build the inputs for one model's parameters
    def Build_The_Parameter_Panel(self, Model_Name, Model):

        Panel = QWidget()
        Panel.setObjectName("CollapsibleSubContainer")
        Panel_Layout = QVBoxLayout(Panel)
        Panel_Layout.setContentsMargins(4, 4, 4, 4)
        Panel_Layout.setSpacing(4)
        self.Parameter_Widgets[Model_Name] = {}

        # The AP2 and H12 models need two composition quantities entered by hand
        if Model.get("needs_Z", False):
            # Effective (mean) atomic number per atom
            Z_Layout = self.Make_A_Label_And_Box_Layout("Effective Z (mean atomic number):")
            Z_Box = Number_Box(10.0, Minimum=0.001, On_Nested_Card=True)
            Z_Box.setToolTip("Mean atomic number per atom = (sum of atomic numbers) / (atoms per formula unit).\nExample MgSiO₃: (12 + 14 + 3×8) / 5 = 10")
            Z_Layout.addWidget(Z_Box)
            Z_Layout.addStretch()
            Panel_Layout.addLayout(Z_Layout)
            # Atoms per measured volume unit, which converts the data to Å³/atom
            Atoms_Layout = self.Make_A_Label_And_Box_Layout("Atoms per volume unit (→ Å³/atom):")
            Atoms_Box = Number_Box(1, Integer=True, Minimum=1, On_Nested_Card=True)
            Atoms_Box.setToolTip("Number of atoms in one unit of the measured volume.\nÅ³/atom → 1   ·   Å³/formula unit → atoms per formula unit\nÅ³/unit cell → (formula units per cell) × (atoms per formula unit)")
            Atoms_Layout.addWidget(Atoms_Box)
            Atoms_Layout.addStretch()
            Panel_Layout.addLayout(Atoms_Layout)
            self.Composition_Inputs[Model_Name] = {"Z": Z_Box, "atoms": Atoms_Box}

        # One row per parameter: starting guess, fix checkbox and the uncertainty of a fixed value
        for Parameter in Model["params"]:
            Parameter_Layout = self.Make_A_Label_And_Box_Layout(f"{Parameter['label']}:")
            # The starting guess is shown with the digits it has in Reference_Values_And_Units; a parameter that must be positive cannot be zero
            Guess_Box = Number_Box(Parameter["default"], Minimum=0 if Parameter.get("positive_only") else None, Allow_Zero=not Parameter.get("positive_only"), On_Nested_Card=True)
            Parameter_Layout.addWidget(Guess_Box)
            Parameter_Layout.addSpacing(10)
            Fix_Checkbox = QCheckBox("Fix")
            Fix_Checkbox.setObjectName("Checkbox")
            Parameter_Layout.addWidget(Fix_Checkbox)
            # The uncertainty of a fixed parameter is only shown while Fix is checked
            Uncertainty_Container = QWidget()
            Uncertainty_Container.setObjectName("CollapsibleSubContainer")
            Uncertainty_Layout = QHBoxLayout(Uncertainty_Container)
            Uncertainty_Layout.setContentsMargins(0, 0, 0, 0)
            Uncertainty_Layout.setSpacing(Label_To_Box_Space)
            Uncertainty_Sign = QLabel("±")
            Uncertainty_Sign.setObjectName("CollapsibleContentLabel")
            # The sign and the container are only as wide as they need to be, so the box stays right next to the sign
            Uncertainty_Sign.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            Uncertainty_Container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            Uncertainty_Layout.addWidget(Uncertainty_Sign)
            Uncertainty_Box = Number_Box(0.0, Minimum=0, On_Nested_Card=True)
            Uncertainty_Layout.addWidget(Uncertainty_Box)
            Uncertainty_Container.setVisible(False)
            Parameter_Layout.addWidget(Uncertainty_Container)
            Parameter_Layout.addStretch()
            Fix_Checkbox.toggled.connect(lambda Checked, Container=Uncertainty_Container, Box=Uncertainty_Box: self.When_A_Parameter_Is_Fixed_Or_Unfixed(Container, Box, Checked))
            Parameter_Row = QWidget()
            Parameter_Row.setObjectName("CollapsibleSubContainer")
            Parameter_Row.setLayout(Parameter_Layout)
            Panel_Layout.addWidget(Parameter_Row)
            self.Parameter_Widgets[Model_Name][Parameter["name"]] = {"guess": Guess_Box, "fix": Fix_Checkbox, "unc": Uncertainty_Box}

        return Panel


    # Make a row that starts with a label, with one space between the label and the box that is added after it
    def Make_A_Label_And_Box_Layout(self, Label_Text):

        Row_Layout = QHBoxLayout()
        Row_Layout.setContentsMargins(0, 0, 0, 0)
        Row_Layout.setSpacing(Label_To_Box_Space)
        Label = QLabel(Label_Text)
        Label.setObjectName("CollapsibleContentLabel")
        Label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        Row_Layout.addWidget(Label)

        return Row_Layout


    # Show the uncertainty box for a fixed parameter and clear it for an unfixed one
    def When_A_Parameter_Is_Fixed_Or_Unfixed(self, Uncertainty_Container, Uncertainty_Box, Fixed):

        Uncertainty_Container.setVisible(Fixed)
        if not Fixed:
            Uncertainty_Box.setValue(0.0)



    # Get the models the user has checked
    def Get_Checked_Models(self):

        return [Model for Model in Get_Models_For_Method(self.Method) if self.Model_Checkboxes.get(Model["name"], QCheckBox()).isChecked()]


    # Get the reference pressure, which only applies to XRD
    def Get_Reference_Pressure(self):

        return self.Reference_Pressure_Box.value() if self.Method == "XRD" else 0.0


    # Read what the user set in a model's parameter panel: the starting guesses, the names of the fixed parameters and the uncertainty of each fixed parameter that has one
    def Read_Parameter_Widgets(self, Model_Name, Model):

        Guesses, Fixed, Fixed_Uncertainties = {}, set(), {}
        Widgets_By_Name = self.Parameter_Widgets.get(Model_Name, {})
        for Parameter in Model["params"]:
            Parameter_Name = Parameter["name"]
            Widgets = Widgets_By_Name.get(Parameter_Name, {})
            if "guess" in Widgets:
                Guesses[Parameter_Name] = Widgets["guess"].value()
            if "fix" in Widgets and Widgets["fix"].isChecked():
                Fixed.add(Parameter_Name)
                Uncertainty = Widgets["unc"].value() if "unc" in Widgets else 0.0
                if Uncertainty > 0:
                    Fixed_Uncertainties[Parameter_Name] = Uncertainty

        return Guesses, Fixed, Fixed_Uncertainties


    # Read the effective Z and atoms per volume unit of a model that needs them
    def Read_Composition_Inputs(self, Model):

        if Model.get("needs_Z", False) and Model["name"] in self.Composition_Inputs:
            Inputs = self.Composition_Inputs[Model["name"]]
            return float(Inputs["Z"].value()), float(Inputs["atoms"].value())

        return None, None



    # When the fit button is clicked, check a model has been checked and send out the checked models
    def When_The_Fit_Button_Is_Clicked(self):

        Checked_Models = self.Get_Checked_Models()
        if not Checked_Models:
            QMessageBox.warning(self, "EoSFitting", "Please check at least one model.")
            return

        if self.Once_A_Fit_Is_Requested:
            self.Once_A_Fit_Is_Requested(Checked_Models)



    # Get the reference pressure and checked models so a new fit can start from them
    def Get_Prefill(self):

        return {
            "ref_value": self.Reference_Pressure_Box.value(),
            "checked_models": [Name for Name, Checkbox in self.Model_Checkboxes.items() if Checkbox.isChecked()],
        }


    # Fill the reference pressure and checked models from a previous fit (the model list must already be built for the right method)
    def Apply_Prefill(self, Prefill):

        if "ref_value" in Prefill:
            self.Reference_Pressure_Box.setValue(Prefill["ref_value"])
        for Model_Name in Prefill.get("checked_models", []):
            if Model_Name in self.Model_Checkboxes:
                self.Model_Checkboxes[Model_Name].setChecked(True)
