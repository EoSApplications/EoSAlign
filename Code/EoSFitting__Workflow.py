# Load libraries
    # Load standard libraries
import numpy as np
    # Load third party libraries
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer, QPoint
    # Load local functions from local files
from Enter_Fitting_Data import Enter_Fitting_Data
from Select_Fitting_Models import Select_Fitting_Models
from Show_Fit_Results import Show_Fit_Results
from Show_Covariance_Ellipses import Show_Covariance_Ellipses
from Select_Alignment_Studies import Select_Alignment_Studies
from Show_Alignment_Results import Show_Alignment_Results
from Fitting_Models_And_Units import Get_Method_For_Unit, Get_Measurement_Axis_Label
from Fitting_Runs import Run_Fits, Run_Alignment





# The parts of the EoSFitting workflow that are the same in the step by step layout and the all steps layout:
# creating the content of every section, running the fit and the alignment, and starting a new fit from an old one.
# The two layouts decide how the sections are arranged, shown and enabled, and use the Continue_From_ and After_The_ functions below.
# Layouts using this must set Current_Scroll_Location (the scroll area) and All_Collapsible_Sections (the ordered sections).
class Fitting_Workflow:

    # Create the content of every section
    def Create_The_Fitting_Content(self, Show_Continue_Buttons):

        # Store the results
        self.Data = None
        self.Fit_Results = {}
        self.Aligned_Results = {}
        self.Random_Generator = np.random.default_rng()

        # Enter data
        self.Enter_Data_Content = Enter_Fitting_Data(Once_A_Change_Is_Made=self.Continue_From_Enter_Data, Show_Continue_Button=Show_Continue_Buttons, Parent=self)
        # Select models
        self.Select_Models_Content = Select_Fitting_Models(Once_A_Fit_Is_Requested=self.Run_The_Fit, Parent=self)
        # Fit results
        self.Fit_Results_Content = Show_Fit_Results(Once_A_Change_Is_Made=self.Continue_From_Fit_Results, Show_Continue_Button=Show_Continue_Buttons, Parent=self)
        # Covariance ellipses
        self.Covariance_Content = Show_Covariance_Ellipses(Once_A_Change_Is_Made=self.Continue_From_Covariance, Show_Continue_Button=Show_Continue_Buttons, Parent=self)
        # Pressure alignment
        self.Alignment_Studies_Content = Select_Alignment_Studies(Get_Pressure_Data=self.Get_Pressure_Data, Once_Alignment_Is_Requested=self.Run_The_Alignment, Parent=self)
        # Alignment results
        self.Alignment_Results_Content = Show_Alignment_Results(Parent=self)

        # Keep the models and alignment sections in step with the units
        self.Enter_Data_Content.Units_Changed.connect(self.When_The_Units_Are_Changed)
        self.Update_The_Content_For_The_Units(self.Enter_Data_Content.Get_The_Selected_Units())



    # Update the sections that depend on the units of the data
    def Update_The_Content_For_The_Units(self, Units):

        # No units are selected until the user chooses them
        Method = Get_Method_For_Unit(Units or None)
        self.Select_Models_Content.Refresh(Method=Method)
        self.Alignment_Studies_Content.Refresh(Method=Method)


    # When the units are changed update the sections that depend on them
    def When_The_Units_Are_Changed(self, Units):

        self.Update_The_Content_For_The_Units(Units)
        self.After_The_Units_Are_Changed()


    # Get the entered pressures and their uncertainties
    def Get_Pressure_Data(self):

        _, _, Pressure, Sigma_Pressure = self.Enter_Data_Content.Read_Table_Data()

        return Pressure, Sigma_Pressure



    # Fit the checked models to the entered data and show the results
    def Run_The_Fit(self, Checked_Models):

        # Check the data
        if not self.Enter_Data_Content.Validate_And_Warn():
            return
        Data = self.Enter_Data_Content.Get_Current_Entered_Data()
        self.Data = Data

        # Fit every checked model
        self.Fit_Results, Reports = Run_Fits(Checked_Models, self.Select_Models_Content.Read_Parameter_Widgets, self.Select_Models_Content.Read_Composition_Inputs, Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], self.Select_Models_Content.Get_Reference_Pressure(), self.Random_Generator)

        # Show the results
        Y_Label = Get_Measurement_Axis_Label(Data["Units"])
        self.Fit_Results_Content.Refresh(Fit_Results=self.Fit_Results, Reports=Reports, Data=Data, Y_Label=Y_Label)
        self.Covariance_Content.Refresh(Fit_Results=self.Fit_Results)
        # Any earlier alignment was done on the previous fit
        self.Aligned_Results = {}
        self.Alignment_Results_Content.Reset()

        self.After_The_Fit_Is_Run()


    # Align the pressures to the selected studies, refit every model and show the results
    def Run_The_Alignment(self, Source_Calibration, Target_Calibrations):

        if not self.Fit_Results:
            QMessageBox.warning(self, "EoSFitting", "Please fit the models first.")
            return
        if not self.Enter_Data_Content.Validate_And_Warn():
            return
        Data = self.Enter_Data_Content.Get_Current_Entered_Data()

        # Align the pressures and refit every model
        self.Aligned_Results = Run_Alignment(self.Fit_Results, Source_Calibration, Target_Calibrations, self.Select_Models_Content.Read_Parameter_Widgets, Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], self.Select_Models_Content.Get_Reference_Pressure(), self.Random_Generator)

        # Show the results
        self.Alignment_Results_Content.Refresh(Fit_Results=self.Fit_Results, Aligned_Results=self.Aligned_Results, Study_Label_Map=self.Alignment_Studies_Content.Get_Study_Label_Map(), Data=Data, Y_Label=Get_Measurement_Axis_Label(Data["Units"]))

        self.After_The_Alignment_Is_Run()



    # The layouts replace these to show, hide, enable or expand sections as the user moves through the workflow
    def Continue_From_Enter_Data(self, Data):
        pass

    def Continue_From_Fit_Results(self, Fit_Results):
        pass

    def Continue_From_Covariance(self, Fit_Results):
        pass

    def After_The_Units_Are_Changed(self):
        pass

    def After_The_Fit_Is_Run(self):
        pass

    def After_The_Alignment_Is_Run(self):
        pass



    # Get the units, data, reference pressure and checked models so a new fit can start from them
    def Get_Prefill(self):

        return {**self.Enter_Data_Content.Get_Prefill(), **self.Select_Models_Content.Get_Prefill()}


    # Fill the data and models from a previous fit
    def Apply_Prefill(self, Prefill):

        # The units have to be set first because they decide which models are listed
        self.Enter_Data_Content.Apply_Prefill(Prefill)
        self.Select_Models_Content.Apply_Prefill(Prefill)



    # Find the closest visible section above a section
    def Find_The_Previous_Visible_Section(self, Section):

        try:
            Section_Index = self.All_Collapsible_Sections.index(Section)
        except ValueError:
            return None
        for Previous_Section in reversed(self.All_Collapsible_Sections[:Section_Index]):
            if Previous_Section.isVisible():
                return Previous_Section

        return None


    # Scroll to a specific section
    def Scroll_To_A_Specific_Section(self, Section, Align_Top_To_Viewport_Midpoint=False):

        def Do_Scroll():
            Scroll_Widget = self.Current_Scroll_Location.widget()
            Target_Y = Section.mapTo(Scroll_Widget, QPoint(0, 0)).y() - 12
            # Keep the end of the previous section in view so tall sections do not hide what came before
            if Align_Top_To_Viewport_Midpoint:
                Previous_Section = self.Find_The_Previous_Visible_Section(Section)
                if Previous_Section is not None:
                    Target_Y = Previous_Section.mapTo(Scroll_Widget, QPoint(0, 0)).y()
            Scroll_Bar = self.Current_Scroll_Location.verticalScrollBar()
            Scroll_Bar.setValue(max(0, min(Target_Y, Scroll_Bar.maximum())))

        QTimer.singleShot(50, Do_Scroll)


    # Expand a section and scroll it into view
    def Focus_On_Section(self, Section):

        Section.setVisible(True)
        Section.Expand_Or_Collapse_Section(True)
        self.Scroll_To_A_Specific_Section(Section)
