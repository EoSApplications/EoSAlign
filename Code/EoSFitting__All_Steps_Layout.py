# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import Qt
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from EoSAlign__All_Steps_Layout import Make_Content_Layout_Scrollable
from EoSFitting__Workflow import Fitting_Workflow




# All steps layout for users who want to see all steps at once and jump between them in any order
class Fitting_All_Steps_Layout(QWidget, Fitting_Workflow):
    def __init__(self):
        super().__init__()

        # Create the content of every step
        self.Create_The_Fitting_Content(Show_Continue_Buttons=False)
        # Create the collapsable sections for all steps
        self.Create_Collapsible_Sections_For_All_Steps()
        # Start with the sections that need results disabled
        self.Enable_Or_Disable_Sections()


    # Create a collapsable section for each step
    def Create_Collapsible_Sections_For_All_Steps(self):

        # Create the collapsable section display
        Collapsible_Sections_Display = Make_Content_Layout_Scrollable()
        self.Collapsible_Sections_Layout = QVBoxLayout(Collapsible_Sections_Display)
        self.Collapsible_Sections_Layout.setContentsMargins(5, 0, 5, 0)
        self.Collapsible_Sections_Layout.setSpacing(5)
        self.Collapsible_Sections_Layout.setAlignment(Qt.AlignTop)

        # Enter data
        self.Enter_Data_Collapsible_Section = Collapsible_Content_Container("Enter Data", self.Enter_Data_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Enter_Data_Collapsible_Section)

        # Select models
        self.Select_Models_Collapsible_Section = Collapsible_Content_Container("Select Models & Parameters", self.Select_Models_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Select_Models_Collapsible_Section)

        # Fit results
        self.Fit_Results_Collapsible_Section = Collapsible_Content_Container("Fit Results", self.Fit_Results_Content, Show_Container_Title=True, Initially_Show_Container=False, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Fit_Results_Collapsible_Section)

        # Covariance ellipses
        self.Covariance_Collapsible_Section = Collapsible_Content_Container("Parameter Covariance Ellipses", self.Covariance_Content, Show_Container_Title=True, Initially_Show_Container=False, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Covariance_Collapsible_Section)

        # Pressure alignment
        self.Alignment_Studies_Collapsible_Section = Collapsible_Content_Container("Pressure-Scale Alignment", self.Alignment_Studies_Content, Show_Container_Title=True, Initially_Show_Container=False, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Alignment_Studies_Collapsible_Section)

        # Alignment results
        self.Alignment_Results_Collapsible_Section = Collapsible_Content_Container("Alignment Results", self.Alignment_Results_Content, Show_Container_Title=True, Initially_Show_Container=False, Expanding_Content=True)
        self.Collapsible_Sections_Layout.addWidget(self.Alignment_Results_Collapsible_Section)

        self.Collapsible_Sections_Layout.addStretch()
        # Make the collapsible sections layout scrollable
        Scroll_Collapsible_Sections_Display = QScrollArea()
        Scroll_Collapsible_Sections_Display.setWidgetResizable(True)
        Scroll_Collapsible_Sections_Display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        Scroll_Collapsible_Sections_Display.setWidget(Collapsible_Sections_Display)
        # Add the scrollable collapsible sections display to the main layout
        All_Steps_Layout_Display = QVBoxLayout(self)
        All_Steps_Layout_Display.setContentsMargins(0, 0, 0, 0)
        All_Steps_Layout_Display.addWidget(Scroll_Collapsible_Sections_Display)
        # Keep a reference for scrolling
        self.Current_Scroll_Location = Scroll_Collapsible_Sections_Display
        # Ordered list of all sections for convenience
        self.All_Collapsible_Sections = [self.Enter_Data_Collapsible_Section, self.Select_Models_Collapsible_Section, self.Fit_Results_Collapsible_Section, self.Covariance_Collapsible_Section, self.Alignment_Studies_Collapsible_Section, self.Alignment_Results_Collapsible_Section]



    # Enable or disable sections based on what has been run
    def Enable_Or_Disable_Sections(self):

        # Check what has been run
        Check_If_The_Models_Have_Been_Fitted = bool(self.Fit_Results)
        Check_If_The_Pressures_Have_Been_Aligned = bool(self.Aligned_Results)
        # Always enable entering the data and selecting the models
        self.Enable_Or_Disable_A_Section(self.Enter_Data_Collapsible_Section, True)
        self.Enable_Or_Disable_A_Section(self.Select_Models_Collapsible_Section, True)
        # Only enable the sections that use the fit once the models have been fitted
        self.Enable_Or_Disable_A_Section(self.Fit_Results_Collapsible_Section, Check_If_The_Models_Have_Been_Fitted)
        self.Enable_Or_Disable_A_Section(self.Covariance_Collapsible_Section, Check_If_The_Models_Have_Been_Fitted)
        self.Enable_Or_Disable_A_Section(self.Alignment_Studies_Collapsible_Section, Check_If_The_Models_Have_Been_Fitted)
        # Only enable the alignment results once the pressures have been aligned
        self.Enable_Or_Disable_A_Section(self.Alignment_Results_Collapsible_Section, Check_If_The_Pressures_Have_Been_Aligned)


    # Enable or disable a section
    def Enable_Or_Disable_A_Section(self, Section, Enabled):

        # setEnabled will automatically either enable the section or disable the section and grey it out
        Section.setEnabled(Enabled)



    # When the models have been fitted enable the sections that use the fit and show the results
    def After_The_Fit_Is_Run(self):

        self.Enable_Or_Disable_Sections()
        self.Focus_On_Section(self.Fit_Results_Collapsible_Section)


    # When the pressures have been aligned enable the results and show them
    def After_The_Alignment_Is_Run(self):

        self.Enable_Or_Disable_Sections()
        self.Focus_On_Section(self.Alignment_Results_Collapsible_Section)
