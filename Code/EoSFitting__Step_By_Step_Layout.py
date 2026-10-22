# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from EoSAlign__Step_By_Step_Layout import Make_Content_Layout_Scrollable
from EoSFitting__Workflow import Fitting_Workflow





# The workflow for the step by step layout for EoSFitting; one of these is shown in each fit tab
class Fitting_Step_By_Step_Layout_Content(QWidget, Fitting_Workflow):
    def __init__(self, Prefill=None):
        super().__init__()

        # Create the content of every step
        self.Create_The_Fitting_Content(Show_Continue_Buttons=True)
        # Create the collapsable sections for all steps
        self.Create_Collapsible_Sections_For_All_Steps()

        # Start from the data and models of a previous fit
        if Prefill:
            self.Apply_Prefill(Prefill)


    # Create a collapsable section for each step
    def Create_Collapsible_Sections_For_All_Steps(self):

        # Create the collapsable section display
        Collapsible_Sections_Display = Make_Content_Layout_Scrollable()
        self.Collapsible_Sections_Layout = QVBoxLayout(Collapsible_Sections_Display)
        self.Collapsible_Sections_Layout.setContentsMargins(12, 12, 12, 12)
        self.Collapsible_Sections_Layout.setSpacing(8)
        self.Collapsible_Sections_Layout.setAlignment(Qt.AlignTop)

        # Enter data
        self.Enter_Data_Collapsible_Section = Collapsible_Content_Container("Enter Data", self.Enter_Data_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Enter_Data_Collapsible_Section)

        # Select models
        self.Select_Models_Collapsible_Section = Collapsible_Content_Container("Select Models & Parameters", self.Select_Models_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Select_Models_Collapsible_Section)

        # Fit results
        self.Fit_Results_Collapsible_Section = Collapsible_Content_Container("Fit Results", self.Fit_Results_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Fit_Results_Collapsible_Section)

        # Covariance ellipses
        self.Covariance_Collapsible_Section = Collapsible_Content_Container("Parameter Covariance Ellipses", self.Covariance_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Covariance_Collapsible_Section)

        # Pressure alignment
        self.Alignment_Studies_Collapsible_Section = Collapsible_Content_Container("Pressure-Scale Alignment", self.Alignment_Studies_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Alignment_Studies_Collapsible_Section)

        # Alignment results
        self.Alignment_Results_Collapsible_Section = Collapsible_Content_Container("Alignment Results", self.Alignment_Results_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Alignment_Results_Collapsible_Section)

        self.Collapsible_Sections_Layout.addStretch()

        # Make the collapsible sections layout scrollable
        Scroll_Collapsible_Sections_Display = QScrollArea()
        Scroll_Collapsible_Sections_Display.setWidgetResizable(True)
        Scroll_Collapsible_Sections_Display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        Scroll_Collapsible_Sections_Display.setFrameShape(QFrame.Shape.NoFrame)
        Scroll_Collapsible_Sections_Display.setWidget(Collapsible_Sections_Display)
        # Place the scrollable collapsible sections display in the main display
        Step_By_Step_Layout_Display = QVBoxLayout(self)
        Step_By_Step_Layout_Display.setContentsMargins(0, 0, 0, 0)
        Step_By_Step_Layout_Display.addWidget(Scroll_Collapsible_Sections_Display)
        # Keep a reference for scrolling
        self.Current_Scroll_Location = Scroll_Collapsible_Sections_Display
        # Ordered list of all sections for convenience
        self.All_Collapsible_Sections = [self.Enter_Data_Collapsible_Section, self.Select_Models_Collapsible_Section, self.Fit_Results_Collapsible_Section, self.Covariance_Collapsible_Section, self.Alignment_Studies_Collapsible_Section, self.Alignment_Results_Collapsible_Section]

        # Initially hide every section except the first
        self.Hide_Upcoming_Sections(self.Select_Models_Collapsible_Section)



    # Move from enter data section to select models section
    def Continue_From_Enter_Data(self, Data):

        # Summarize the data in the title of the enter data section and collapse it
        self.Enter_Data_Collapsible_Section.Set_The_Section_Title_Text(f"Enter Data: {len(Data['Measurement'])} values  |  {Data['Units']}")
        self.Enter_Data_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Unhide and expand the select models section
        self.Select_Models_Collapsible_Section.setVisible(True)
        self.Select_Models_Collapsible_Section.Expand_Or_Collapse_Section(True)
        self.Select_Models_Collapsible_Section.Set_The_Section_Title_Text("Select Models & Parameters")
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Fit_Results_Collapsible_Section)
        # Scroll to the select models section
        self.Scroll_To_A_Specific_Section(self.Select_Models_Collapsible_Section)


    # Move from fit results section to covariance ellipses section
    def Continue_From_Fit_Results(self, Fit_Results):

        # Collapse the fit results section
        self.Fit_Results_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Unhide and expand the covariance ellipses section
        self.Covariance_Collapsible_Section.setVisible(True)
        self.Covariance_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Alignment_Studies_Collapsible_Section)
        # Scroll to the covariance ellipses section
        self.Scroll_To_A_Specific_Section(self.Covariance_Collapsible_Section)


    # Move from covariance ellipses section to pressure alignment section
    def Continue_From_Covariance(self, Fit_Results):

        # Collapse the covariance ellipses section
        self.Covariance_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Unhide and expand the pressure alignment section
        self.Alignment_Studies_Collapsible_Section.setVisible(True)
        self.Alignment_Studies_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Alignment_Results_Collapsible_Section)
        # Scroll to the pressure alignment section
        self.Scroll_To_A_Specific_Section(self.Alignment_Studies_Collapsible_Section, Align_Top_To_Viewport_Midpoint=True)



    # When the units are changed the models are different, so the data has to be continued from again
    def After_The_Units_Are_Changed(self):

        self.Enter_Data_Collapsible_Section.Set_The_Section_Title_Text("Enter Data")
        self.Hide_Upcoming_Sections(self.Select_Models_Collapsible_Section)


    # When the models have been fitted, show the fit results
    def After_The_Fit_Is_Run(self):

        # Summarize the fitted models in the title of the select models section and collapse it
        self.Select_Models_Collapsible_Section.Set_The_Section_Title_Text(self.Get_The_Models_Title())
        self.Select_Models_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Unhide and expand the fit results section
        self.Fit_Results_Collapsible_Section.setVisible(True)
        self.Fit_Results_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Covariance_Collapsible_Section)
        # Scroll to the fit results section
        self.Scroll_To_A_Specific_Section(self.Fit_Results_Collapsible_Section)


    # When the pressures have been aligned, show the alignment results
    def After_The_Alignment_Is_Run(self):

        # Summarize the alignment in the title of the pressure alignment section and collapse it
        self.Alignment_Studies_Collapsible_Section.Set_The_Section_Title_Text(f"Pressure-Scale Alignment: {len(self.Aligned_Results)} studies")
        self.Alignment_Studies_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Unhide and expand the alignment results section
        self.Alignment_Results_Collapsible_Section.setVisible(True)
        self.Alignment_Results_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Scroll to the alignment results section
        self.Scroll_To_A_Specific_Section(self.Alignment_Results_Collapsible_Section, Align_Top_To_Viewport_Midpoint=True)



    # Hide all the upcoming sections
    def Hide_Upcoming_Sections(self, Upcoming_Section):

        # Start with the section unhidden
        Hide_Section = False
        for Section in self.All_Collapsible_Sections:
            if Section is Upcoming_Section:
                Hide_Section = True
            if Hide_Section:
                Section.setVisible(False)


    # Get the title of the select models section once models have been fitted; a long list of models would make the page wider than the window, so it is a count
    def Get_The_Models_Title(self):

        Model_Names = list(self.Fit_Results.keys())
        if not Model_Names:
            return "Select Models & Parameters"
        if len(Model_Names) == 1:
            return f"Model: {Model_Names[0]}"

        return f"{len(Model_Names)} models fitted"
