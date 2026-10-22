# Load libraries
    # Load standard libraries
import os
from uuid import uuid4
import numpy as np
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox)
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from Select_Composition import Select_Composition
from Select_Pressure_Calibration_Study import Select_Pressure_Calibration_Study, Summary_Of_Selected_Pressure_Calibration_Study
from Select_Studies_For_Comparison import Select_Studies_For_Comparison
from EoS_Math.Build_Dataframe import Get_Compositions_For_Method
from Session_Paths import get_session_directory, hide_path_from_file_explorer





# Delete the files written for a preview and empty the list that tracked them
def Delete_Preview_Files(File_Paths):

    for File_Path in File_Paths:
        try:
            os.remove(File_Path)
        except OSError:
            pass
    File_Paths.clear()





# Create the select alignment studies content: the composition, the pressure calibration study the data was
# measured with and the studies to align the pressures to, followed by the button that starts the alignment
class Select_Alignment_Studies(QWidget):
    def __init__(self, *, Get_Pressure_Data=None, Once_Alignment_Is_Requested=None, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        # Get_Pressure_Data() returns the entered pressures and their uncertainties
        self.Get_Pressure_Data = Get_Pressure_Data
        self.Once_Alignment_Is_Requested = Once_Alignment_Is_Requested

        # Store the user selections
        self.Method = None
        self.Composition = None
        self.Calibration = None
        self.Selected_Studies = []
        # Store the preview files so they can be replaced when the preview changes
        self.Preview_Token = uuid4().hex[:8]
        self.Preview_File_Paths = []
        # Delete the preview files when this section is destroyed
        self.destroyed.connect(lambda _=None, File_Paths=self.Preview_File_Paths: Delete_Preview_Files(File_Paths))

        # Create the select alignment studies display
        self.Create_The_Select_Alignment_Studies_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the select alignment studies section to its initial state
    def Reset(self):

        self.Select_Composition_Content.Reset()
        self.When_Composition_Is_Changed(None)


    # Refresh the select alignment studies section for a method
    def Refresh(self, *, Method=None, **context):

        self.Method = Method
        # Nothing can be selected until the units, and so the method, are known
        if Method is None:
            self.Reset()
            return
        Allowed_Compositions = set(Get_Compositions_For_Method(Method))
        # Show the method once a composition has been chosen
        if self.Composition:
            self.Method_Section.Set_The_Section_Title_Text(f"Method: {Method}")
            if self.Composition not in Allowed_Compositions:
                # The composition is no longer valid for the new method, so start over
                self.When_Composition_Is_Changed(None)
                self.Select_Composition_Content.Refresh(Allowed_Compositions=Allowed_Compositions)
            else:
                self.Select_Calibration_Content.Refresh(Composition=self.Composition, Method=Method)
        else:
            self.Select_Composition_Content.Refresh(Allowed_Compositions=Allowed_Compositions)


    # Get the selected pressure calibration study
    def Get_Selected_Calibration(self):

        return self.Calibration


    # Get the studies selected for comparison
    def Get_Selected_Studies(self):

        return self.Selected_Studies


    # Get the human readable label of each selected study, keyed by its calibration key
    def Get_Study_Label_Map(self):

        return {Study["Calibration Key"]: Study["Study Label"] for Study in self.Selected_Studies}



    # Create the select alignment studies display
    def Create_The_Select_Alignment_Studies_Display(self):

        # Create the select alignment studies display
        self.setObjectName("CollapsibleContent")
        Select_Alignment_Studies_Display = QVBoxLayout(self)
        Select_Alignment_Studies_Display.setContentsMargins(5, 5, 5, 5)
        Select_Alignment_Studies_Display.setSpacing(8)

        # Create the select alignment studies layout
        self.Select_Alignment_Studies_Layout = QWidget()
        self.Select_Alignment_Studies_Layout.setObjectName("CollapsibleSubContainer")
        Select_Alignment_Studies_Layout = QVBoxLayout(self.Select_Alignment_Studies_Layout)
        Select_Alignment_Studies_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Alignment_Studies_Layout.setSpacing(8)
        Select_Alignment_Studies_Display.addWidget(self.Select_Alignment_Studies_Layout)

        # The alignment is optional, so nothing is shown until the user chooses to align
        self.Start_Alignment_Button = QPushButton("Align to a Different Pressure Scale")
        self.Start_Alignment_Button.setObjectName("Primary_Button")
        self.Start_Alignment_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Start_Alignment_Button.setFixedHeight(32)
        Select_Alignment_Studies_Layout.addWidget(self.Start_Alignment_Button)
        # Everything else is in this container, which is hidden until the button is clicked
        self.Alignment_Options = QWidget()
        self.Alignment_Options.setObjectName("CollapsibleSubContainer")
        self.Alignment_Options.setVisible(False)
        Select_Alignment_Studies_Layout.addWidget(self.Alignment_Options)
        Select_Alignment_Studies_Layout = QVBoxLayout(self.Alignment_Options)
        Select_Alignment_Studies_Layout.setContentsMargins(0, 0, 0, 0)
        Select_Alignment_Studies_Layout.setSpacing(8)

        # Select composition
            # The compositions start out limited to the ones that have a calibration for the default method
        self.Select_Composition_Content = Select_Composition(Application="EoSFitting", Once_A_Change_Is_Made=self.When_Composition_Is_Changed, Show_Continue_Button=False, Parent=self)
        self.Select_Composition_Section = Collapsible_Content_Container("Select Composition of the Calibrant", self.Select_Composition_Content, Show_Container_Title=True)
        Select_Alignment_Studies_Layout.addWidget(self.Select_Composition_Section)

        # Method; it is set by the units of the data, so this section only shows it
        self.Method_Section = Collapsible_Content_Container("Method", QWidget(), Show_Container_Title=True)
        self.Method_Section.Expand_Or_Collapse_Section(False)
        self.Method_Section.setVisible(False)
        Select_Alignment_Studies_Layout.addWidget(self.Method_Section)

        # Select the pressure calibration study the data was measured with
        self.Select_Calibration_Content = Select_Pressure_Calibration_Study(Application="EoSFitting", Composition=None, Method=None, Once_A_Change_Is_Made=self.When_Calibration_Is_Changed, Show_Continue_Button=False, Parent=self)
        self.Select_Calibration_Section = Collapsible_Content_Container("Select Pressure Calibration Study", self.Select_Calibration_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Select_Calibration_Section.setVisible(False)
        Select_Alignment_Studies_Layout.addWidget(self.Select_Calibration_Section)

        # Select the studies to align the pressures to
        self.Select_Studies_Content = Select_Studies_For_Comparison(Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Show_Continue_Button=False, Show_Preview=True, Once_A_Change_Is_Made=self.When_Studies_Are_Changed, Parent=self)
        self.Hide_The_Custom_Reference_Options()
        self.Select_Studies_Section = Collapsible_Content_Container("Select Studies For Comparison", self.Select_Studies_Content, Show_Container_Title=True, Expanding_Content=True)
        self.Select_Studies_Section.setVisible(False)
        Select_Alignment_Studies_Layout.addWidget(self.Select_Studies_Section)

        # Create the align button; it is the step's continue button
        self.Align_Button = QPushButton("Align Pressures and Refit All Models")
        self.Align_Button.setObjectName("Primary_Button")
        self.Align_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Align_Button.setFixedHeight(32)
        Select_Alignment_Studies_Layout.addWidget(self.Align_Button)



    # Connect the align button to its function
    def Connect_Signals(self):

        self.Align_Button.clicked.connect(self.When_The_Align_Button_Is_Clicked)
        self.Start_Alignment_Button.clicked.connect(self.When_The_Start_Alignment_Button_Is_Clicked)



    # Replace the start button with the alignment options
    def When_The_Start_Alignment_Button_Is_Clicked(self):

        self.Start_Alignment_Button.setVisible(False)
        self.Alignment_Options.setVisible(True)



    # Fitting data has no custom reference, so hide the custom reference options of the studies section
    def Hide_The_Custom_Reference_Options(self):

        self.Select_Studies_Content.Custom_Ref_Button.setVisible(False)
        self.Select_Studies_Content.Custom_Ref_Container.setVisible(False)



    # When the composition is changed, show the method and the calibration section, and hide everything after it
    def When_Composition_Is_Changed(self, Composition):

        self.Composition = Composition if Composition else None
        # Everything after the composition has to be chosen again
        self.Calibration = None
        self.Selected_Studies = []
        if self.Composition:
            self.Select_Composition_Section.Set_The_Section_Title_Text(f"Composition of the Calibrant: {self.Composition}")
            self.Select_Composition_Section.Expand_Or_Collapse_Section(False)
            # Show the method, which is locked to the units of the data
            self.Method_Section.Set_The_Section_Title_Text(f"Method: {self.Method}")
            self.Method_Section.setVisible(True)
            self.Method_Section.Expand_Or_Collapse_Section(False)
            # Show the calibration section
            self.Select_Calibration_Content.Reset()
            self.Select_Calibration_Content.Refresh(Composition=self.Composition, Method=self.Method)
            self.Select_Calibration_Section.Set_The_Section_Title_Text("Select Pressure Calibration Study")
            self.Select_Calibration_Section.setVisible(True)
            self.Select_Calibration_Section.Expand_Or_Collapse_Section(True)
            self.Select_Studies_Content.Reset()
            self.Select_Studies_Section.setVisible(False)
        else:
            self.Select_Composition_Section.Set_The_Section_Title_Text("Select Composition of the Calibrant")
            self.Method_Section.setVisible(False)
            self.Select_Calibration_Section.setVisible(False)
            self.Select_Studies_Section.setVisible(False)


    # When the calibration is changed, show the studies that can be compared to it
    def When_Calibration_Is_Changed(self, Calibration):

        self.Calibration = Calibration
        if Calibration:
            self.Select_Calibration_Section.Set_The_Section_Title_Text(f"Pressure Calibration Study: {Summary_Of_Selected_Pressure_Calibration_Study(Calibration)}")
            self.Select_Calibration_Section.Expand_Or_Collapse_Section(False)
            # Passing "Pressure (GPa)" makes the section list every study for the composition and method except the source
            self.Select_Studies_Content.Refresh(Data=None, Units="Pressure (GPa)", Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=Calibration)
            self.Hide_The_Custom_Reference_Options()
            # Give the preview the entered pressures so it can convert them to each study
            Preview_Data, Preview_Units = self.Build_The_Preview_Data()
            if Preview_Data is not None:
                self.Select_Studies_Content.Data = Preview_Data
                self.Select_Studies_Content.Units = Preview_Units
            self.Select_Studies_Section.Set_The_Section_Title_Text("Select Studies For Comparison")
            self.Select_Studies_Section.setVisible(True)
            self.Select_Studies_Section.Expand_Or_Collapse_Section(True)
            self.Selected_Studies = self.Select_Studies_Content.Get_Current_Selected_Studies_For_Comparison()
        else:
            self.Select_Calibration_Section.Set_The_Section_Title_Text("Select Pressure Calibration Study")
            self.Select_Studies_Section.setVisible(False)
            self.Selected_Studies = []


    # When the selected studies change, update the title of the section
    def When_Studies_Are_Changed(self, Selected_Studies):

        self.Selected_Studies = Selected_Studies or []
        Number_Of_Studies = len(self.Selected_Studies)
        self.Select_Studies_Section.Set_The_Section_Title_Text(f"{Number_Of_Studies} studies selected for comparison" if Number_Of_Studies else "Select Studies For Comparison")



    # Write the entered pressures to files and return data in the form the pressure conversion preview reads.
    # The preview reads the files later, so the previous preview's files are only deleted when a new preview replaces them.
    def Build_The_Preview_Data(self):

        if self.Get_Pressure_Data is None:
            return None, None
        Pressure, Sigma_Pressure = self.Get_Pressure_Data()
        if len(Pressure) == 0:
            return None, None

        # Replace the previous preview's files
        Delete_Preview_Files(self.Preview_File_Paths)
        # Store the files with the other manual entry files so they are deleted when the application closes
        Folder = get_session_directory(".Manual_Entry_Data_Files", f"Fitting_Preview_{self.Preview_Token}")
        hide_path_from_file_explorer(Folder)
        try:
            Pressure_File_Path = self.Write_A_Preview_File(Folder, "Pressure.txt", Pressure)
            # Only write the uncertainties if there are any
            Has_Uncertainty = bool(np.any(Sigma_Pressure > 0))
            Uncertainty_File_Path = self.Write_A_Preview_File(Folder, "Pressure_Uncertainty.txt", Sigma_Pressure) if Has_Uncertainty else ""
        except Exception:
            return None, None

        Preview_Data = {
            "File_Path": Pressure_File_Path,
            "Units": "Pressure (GPa)",
            "Error Propagation Enabled": Has_Uncertainty,
            "Uncertainty Data": {
                "Error Propagation Enabled": Has_Uncertainty,
                "Error Propagation Path": Uncertainty_File_Path,
            },
        }

        return Preview_Data, "Pressure (GPa)"


    # Write one column of numbers to a preview file
    def Write_A_Preview_File(self, Folder, File_Name, Values):

        File_Path = os.path.join(str(Folder), File_Name)
        with open(File_Path, "w") as Preview_File:
            for Value in Values:
                Preview_File.write(f"{Value}\n")
        self.Preview_File_Paths.append(File_Path)

        return File_Path


    # When the align button is clicked, check the selections are complete and send them out
    def When_The_Align_Button_Is_Clicked(self):

        if not self.Calibration:
            QMessageBox.warning(self, "EoSFitting", "Please select the pressure calibration study the data was measured with.")
            return
        # Find the calibration the data was measured with
        Source_Calibration = self.Calibration.get("Target Pressure Calibration Study") or self.Calibration.get("Selected Pressure Calibration Study")
        if not Source_Calibration:
            QMessageBox.warning(self, "EoSFitting", "Could not determine source calibrant. Please complete the calibration selection.")
            return
        Target_Calibrations = [Study["Calibration Key"] for Study in self.Selected_Studies]
        if not Target_Calibrations:
            QMessageBox.warning(self, "EoSFitting", "Please select at least one study to align the pressures to.")
            return

        if self.Once_Alignment_Is_Requested:
            self.Once_Alignment_Is_Requested(Source_Calibration, Target_Calibrations)
