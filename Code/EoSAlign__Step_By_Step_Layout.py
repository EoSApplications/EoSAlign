# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QApplication
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint, Signal
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from Enter_Data import Enter_Data
from Select_Composition import Select_Composition
from Select_Method import Select_Method
from Select_Pressure_Calibration_Study import Select_Pressure_Calibration_Study, Summary_Of_Selected_Pressure_Calibration_Study
from Select_Studies_For_Comparison import Select_Studies_For_Comparison
from Select_Final_Actions import Select_Final_Actions
from Reference_Values_And_Units import Volume_Units
from EoS_Math.Build_Dataframe import Get_Compositions_For_Method, Get_Methods_For_Composition
from Message_Manager import Warning_Message





# Constrains the scroll-area content widget to its natural height using heightForWidth()
# so word-wrapped labels are measured correctly and no blank stretch space appears.
class Make_Content_Layout_Scrollable(QWidget):

    def event(self, e):
        result = super().event(e)
        if e.type() == QEvent.Type.LayoutRequest and self.layout():
            self.Update_Max_Height()
        return result

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.layout():
            self.Update_Max_Height()

    def Update_Max_Height(self):
        layout = self.layout()
        w = self.width()
        if w > 0 and layout.hasHeightForWidth():
            h = layout.heightForWidth(w)
        else:
            h = layout.sizeHint().height()
        if h > 0:
            self.setMaximumHeight(h)




# The workflow for the step by step layout for EoSAlign
class Step_By_Step_Layout_Content(QWidget):

    # Emitted (with current selections dict) when user clicks Recalculate
    Add_New_Run = Signal(dict)
    # Emitted when user clicks Reset — tells the parent layout to clear all tabs
    Request_Reset_All = Signal()

    def __init__(self, Disabled_Collapsible_Section_Selections=None, Run_Label="Run 1"):
        super().__init__()

        # Store the user selections
        self.Data = None
        self.Units = None
        self.Composition = None
        self.Method = None
        self.Pressure_Calibration_Study = None
        self.Selected_Studies = None
        self.Disabled_Mode = False
        self.Preset_Units = None
        self.Run_Label = Run_Label

        # Create the collapsable sections for all steps
        self.Create_Collapsible_Sections_For_All_Steps()

        # Populate disabled collapsible sections with the previous user selections
        if Disabled_Collapsible_Section_Selections:
            self.Fill_Disabled_Collapsible_Section_Seceltions(Disabled_Collapsible_Section_Selections)


    # Create a collapsable section for each step
    def Create_Collapsible_Sections_For_All_Steps(self):

        # Create the collapsable section display
        Collapsible_Sections_Display = Make_Content_Layout_Scrollable()
        self.Collapsible_Sections_Layout = QVBoxLayout(Collapsible_Sections_Display)
        self.Collapsible_Sections_Layout.setContentsMargins(12, 12, 12, 12)
        self.Collapsible_Sections_Layout.setSpacing(8)
        self.Collapsible_Sections_Layout.setAlignment(Qt.AlignTop)

        # Enter data
            # Get the enter data content
        self.Enter_Data_Content = Enter_Data(Once_A_Change_Is_Made=self.Continue_From_Enter_Data, Show_Continue_Button=True, Parent=self)
            # Add the enter data content to a collapsable section
        self.Enter_Data_Collapsible_Section = Collapsible_Content_Container("Enter Data", self.Enter_Data_Content, Show_Container_Title=True)
            # Add the enter data collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Enter_Data_Collapsible_Section)

        # Select composition
            # Get the select composition content
        self.Select_Composition_Content = Select_Composition(Application="EoSAlign", Once_A_Change_Is_Made=self.Continue_From_Select_Composition, Show_Continue_Button=True, Parent=self)
            # Add the select composition content to a collapsable section
        self.Select_Composition_Collapsible_Section = Collapsible_Content_Container("Select Composition", self.Select_Composition_Content, Show_Container_Title=True)
            # Initially hide the select composition section
        self.Select_Composition_Collapsible_Section.setVisible(False)
            # Add the select composition collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Composition_Collapsible_Section)

        # Select method
            # Get the select method content
        self.Select_Method_Content = Select_Method(Once_A_Change_Is_Made=self.Continue_From_Select_Method, Show_Continue_Button=True, Parent=self)
            # Add the select method content to a collapsable section
        self.Select_Method_Collapsible_Section = Collapsible_Content_Container("Select Method", self.Select_Method_Content, Show_Container_Title=True)
            # Initially hide the select method section
        self.Select_Method_Collapsible_Section.setVisible(False)
            # Add the select method collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Method_Collapsible_Section)

        # Select calibration - Only show if the units are pressure
            # Get the select calibration content
        self.Select_Pressure_Calibration_Study_Content = Select_Pressure_Calibration_Study(Application="EoSAlign", Composition=None, Method=None, Once_A_Change_Is_Made=self.Continue_From_Select_Pressure_Calibration_Study, Show_Continue_Button=True, Parent=self)
            # Add the select calibration content to a collapsible section
        self.Select_Pressure_Calibration_Study_Collapsible_Section = Collapsible_Content_Container("Select Pressure Calibration Study", self.Select_Pressure_Calibration_Study_Content, Show_Container_Title=True, Expanding_Content=True)
            # Initially hide the select calibration section
        self.Select_Pressure_Calibration_Study_Collapsible_Section.setVisible(False)
            # Add the select calibration collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Pressure_Calibration_Study_Collapsible_Section)

        # Select studies for comparison
            # Get the select studies for comparison content
        self.Select_Studies_For_Comparison_Content = Select_Studies_For_Comparison(Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Show_Continue_Button=True, Show_Preview=True, Once_A_Change_Is_Made=self.Continue_From_Select_Studies_For_Comparison, Parent=self)
            # Add the select studies for comparison content to a collapsible section
        self.Select_Studies_For_Comparison_Collapsible_Section = Collapsible_Content_Container("Select Studies For Comparison", self.Select_Studies_For_Comparison_Content, Show_Container_Title=True, Expanding_Content=True)
            # Initially hide the select studies for comparison section
        self.Select_Studies_For_Comparison_Collapsible_Section.setVisible(False)
            # Add the select studies for comparison collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Studies_For_Comparison_Collapsible_Section)

        # Final actions
            # Get the final actions content
        self.Final_Actions_Content = Select_Final_Actions(Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Selected_Studies=None, Show_Continue_Button=True, Show_Recalculate_Button=True, Show_Reset_Button=True, Run_Label=self.Run_Label, Parent=self)
            # Add the final actions content to a collapsible section
        self.Final_Actions_Collapsible_Section = Collapsible_Content_Container("Step 6: Actions", self.Final_Actions_Content, Show_Container_Title=True)
            # Initially hide the final actions section
        self.Final_Actions_Collapsible_Section.setVisible(False)
            # Add the final actions collapsable section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Final_Actions_Collapsible_Section)
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
        self.All_Collapsible_Sections = [self.Enter_Data_Collapsible_Section, self.Select_Composition_Collapsible_Section, self.Select_Method_Collapsible_Section, self.Select_Pressure_Calibration_Study_Collapsible_Section, self.Select_Studies_For_Comparison_Collapsible_Section, self.Final_Actions_Collapsible_Section,]
        # Middle sections that get locked in non-Run-1 tabs
        self.List_Of_Middle_Collapsible_Sections = [self.Select_Composition_Collapsible_Section, self.Select_Method_Collapsible_Section, self.Select_Pressure_Calibration_Study_Collapsible_Section, self.Select_Studies_For_Comparison_Collapsible_Section,]
        # Connect recalculate and reset signals from final actions
        self.Final_Actions_Content.Recalculate_Requested.connect(self.Recalculate)
        self.Final_Actions_Content.Reset_Application_Requested.connect(self.Reset_Application)
        self.Select_Pressure_Calibration_Study_Content.Request_Scroll_To_Widget.connect(self.Scroll_To_A_Pressure_Calibration_Subsection)


    # Populate disabled collapsible sections with the previous user selections
    def Fill_Disabled_Collapsible_Section_Seceltions(self, Disabled_Collapsible_Section_Selections):

        # Set the user selections
        self.Disabled_Mode = True
        self.Preset_Units = Disabled_Collapsible_Section_Selections.get("Units")
        self.Composition = Disabled_Collapsible_Section_Selections.get("Composition")
        self.Method = Disabled_Collapsible_Section_Selections.get("Method")
        self.Pressure_Calibration_Study = Disabled_Collapsible_Section_Selections.get("Pressure_Calibration_Study")
        self.Selected_Studies = Disabled_Collapsible_Section_Selections.get("Selected_Studies")

        # Show composition section collapsed with preset title
        if self.Composition:
            self.Select_Composition_Collapsible_Section.Set_The_Section_Title_Text(f"Composition: {self.Composition}")
            self.Select_Composition_Collapsible_Section.Expand_Or_Collapse_Section(False)
            self.Select_Composition_Collapsible_Section.setVisible(True)

        # Show method section collapsed with preset title
        if self.Method:
            self.Select_Method_Collapsible_Section.Set_The_Section_Title_Text(f"Method: {self.Method}")
            self.Select_Method_Collapsible_Section.Expand_Or_Collapse_Section(False)
            self.Select_Method_Collapsible_Section.setVisible(True)

        # Show calibration section collapsed with preset title (if applicable)
        if self.Pressure_Calibration_Study:
            Cal_Summary = Summary_Of_Selected_Pressure_Calibration_Study(self.Pressure_Calibration_Study)
            self.Select_Pressure_Calibration_Study_Collapsible_Section.Set_The_Section_Title_Text(f"Pressure Calibration Study: {Cal_Summary}")
            self.Select_Pressure_Calibration_Study_Collapsible_Section.Expand_Or_Collapse_Section(False)
            self.Select_Pressure_Calibration_Study_Collapsible_Section.setVisible(True)

        # Show studies section collapsed with preset title
        if self.Selected_Studies:
            N = len(self.Selected_Studies)
            self.Select_Studies_For_Comparison_Collapsible_Section.Set_The_Section_Title_Text(f"{N} studies selected for comparison")
            self.Select_Studies_For_Comparison_Collapsible_Section.Expand_Or_Collapse_Section(False)
            self.Select_Studies_For_Comparison_Collapsible_Section.setVisible(True)


    # Move from enter data section to select composition section
    def Continue_From_Enter_Data(self, Data):

        # Store the data
        self.Data = Data
        # Store the units
        self.Units = Data.get("Units") if isinstance(Data, dict) else None
        # Build a summary string for the enter data section title
        Source_Type = Data.get("Source_Type", "")
        Units = Data.get("Units", "")
        Number_Of_Values = len(Data.get("Data", []))
        Enter_Data_Summary = f"{Source_Type}  |  {Number_Of_Values} values  |  {Units}"
        self.Enter_Data_Collapsible_Section.Set_The_Section_Title_Text(f"Enter Data: {Enter_Data_Summary}")
        self.Enter_Data_Collapsible_Section.Expand_Or_Collapse_Section(False)
        if self.Disabled_Mode:
            # Check whether the unit change is acceptable
            if self.Preset_Units and self.Units != self.Preset_Units:
                Both_Are_Volume = (self.Preset_Units in Volume_Units and self.Units in Volume_Units)
                if not Both_Are_Volume:
                    Warning_Message(
                        self,
                        "Units Mismatch On Recalculation",
                        previous_units=self.Preset_Units,
                        new_units=self.Units,
                    )
                    # Re-expand Enter Data so the user can fix their selection
                    self.Enter_Data_Collapsible_Section.Expand_Or_Collapse_Section(True)
                    return
            # Skip straight to Final Actions using the preset composition/method/calibration/studies
            self.Final_Actions_Content.Reset()
            self.Final_Actions_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Pressure_Calibration_Study, Selected_Studies=self.Selected_Studies,)
            self.Final_Actions_Collapsible_Section.setVisible(True)
            self.Final_Actions_Collapsible_Section.Expand_Or_Collapse_Section(True)
            self.Final_Actions_Collapsible_Section.Set_The_Section_Title_Text("Final Actions")
            self.Scroll_To_A_Specific_Section(self.Final_Actions_Collapsible_Section)
            return
        # Normal flow: reset downstream and proceed to composition selection
        self.Composition = None
        self.Method = None
        self.Pressure_Calibration_Study = None
        self.Selected_Studies = None
        self.Select_Composition_Content.Reset()
        # Filter compositions to those that have calibrations for the auto-determined method;
        # for pressure units the user will pick a method later so no filter is applied yet.
        Auto_Method = self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data()
        Allowed_Compositions = set(Get_Compositions_For_Method(Auto_Method)) if Auto_Method is not None else None
        self.Select_Composition_Content.Refresh(Allowed_Compositions=Allowed_Compositions)
        # Unhide the select composition collapsible section
        self.Select_Composition_Collapsible_Section.setVisible(True)
        # Expand the select composition collapsible section
        self.Select_Composition_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Set the title of the select composition collapsible section
        self.Select_Composition_Collapsible_Section.Set_The_Section_Title_Text("Select Composition")
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Select_Method_Collapsible_Section)
        # Scroll to the select composition collapsible section
        self.Scroll_To_A_Specific_Section(self.Select_Composition_Collapsible_Section)


    # Move from select composition section to select method section (or skip it if auto-determined)
    def Continue_From_Select_Composition(self, Composition):

        # In preset mode the middle sections are read-only
        if self.Disabled_Mode:
            return
        # Reset all upcoming sections
        if not Composition:
            return
        self.Composition = Composition
        self.Method = None
        self.Pressure_Calibration_Study = None
        self.Select_Studies = None
        # Set the select composition section title to the selected composition
        self.Select_Composition_Collapsible_Section.Set_The_Section_Title_Text(f"Composition: {Composition}")
        # Collapse the select composition section
        self.Select_Composition_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Check if the method is auto-determined from the selected units
        Auto_Method = self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data()
        if Auto_Method is not None:
            # Method is determined by units — skip the select method section entirely
            self.Method = Auto_Method
            self.Clear_Focus_If_It_Is_Within(self.Select_Composition_Collapsible_Section)
            self.Select_Method_Collapsible_Section.setVisible(False)
            self.Select_Pressure_Calibration_Study_Content.Reset()
            self.Select_Studies_For_Comparison_Content.Reset()
            # Populate and show the select studies section (calibration never applies for non-pressure)
            self.Select_Studies_For_Comparison_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=None)
            # Hide final actions, then show studies
            self.Hide_Upcoming_Sections(self.Final_Actions_Collapsible_Section)
            self.Select_Studies_For_Comparison_Collapsible_Section.setVisible(True)
            self.Select_Studies_For_Comparison_Collapsible_Section.Expand_Or_Collapse_Section(True)
            self.Select_Studies_For_Comparison_Collapsible_Section.Set_The_Section_Title_Text("Select Studies For Comparison")
            self.Scroll_To_A_Specific_Section(self.Select_Studies_For_Comparison_Collapsible_Section, Align_Top_To_Viewport_Midpoint=True)
        else:
            # Pressure units — method must be selected by the user
            self.Select_Method_Content.Reset()
            # Filter methods to those that have calibrations for the selected composition
            Allowed_Methods = set(Get_Methods_For_Composition(Composition))
            self.Select_Method_Content.Refresh(Allowed_Methods=Allowed_Methods)
            # Unhide the select method collapsible section
            self.Select_Method_Collapsible_Section.setVisible(True)
            # Expand the select method collapsible section
            self.Select_Method_Collapsible_Section.Expand_Or_Collapse_Section(True)
            # Set the title of the select method collapsible section
            self.Select_Method_Collapsible_Section.Set_The_Section_Title_Text("Select Method")
            # Hide all upcoming sections
            self.Hide_Upcoming_Sections(self.Select_Pressure_Calibration_Study_Collapsible_Section)
            # Scroll to the select method collapsible section
            self.Scroll_To_A_Specific_Section(self.Select_Method_Collapsible_Section)


    # Move from select method section to select calibration section (if pressure) or select conversions section (if non-pressure)
    def Continue_From_Select_Method(self, Method):

        # In preset mode the middle sections are read-only
        if self.Disabled_Mode:
            return
        # Reset all upcoming sections
        if not Method:
            return
        self.Method = Method
        self.Pressure_Calibration_Study = None
        self.Selected_Studies = None
        self.Select_Pressure_Calibration_Study_Content.Reset()
        self.Select_Studies_For_Comparison_Content.Reset()
        # Set the select method section title to the selected method
        self.Select_Method_Collapsible_Section.Set_The_Section_Title_Text(f"Method: {Method}")
        # Collapse the select method section
        self.Select_Method_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Check the enter data units to determine the next section
        if self.Check_If_The_Data_Units_Are_Pressure():
            # Show the select calibration collapsible section
            self.Select_Pressure_Calibration_Study_Content.Refresh(Composition=self.Composition, Method=self.Method)
            # Unhide the select calibration collapsible section
            self.Select_Pressure_Calibration_Study_Collapsible_Section.setVisible(True)
            # Expand the select calibration collapsible section
            self.Select_Pressure_Calibration_Study_Collapsible_Section.Expand_Or_Collapse_Section(True)
            # Set the title of the select calibration collapsible section
            self.Select_Pressure_Calibration_Study_Collapsible_Section.Set_The_Section_Title_Text("Select Pressure Calibration Study")
            # Hide all upcoming sections
            self.Hide_Upcoming_Sections(self.Select_Studies_For_Comparison_Collapsible_Section)
            # Scroll to the select calibration collapsible section
            self.Scroll_To_A_Specific_Section(self.Select_Pressure_Calibration_Study_Collapsible_Section)
        else:
            # Reset the calibration selection
            self.Pressure_Calibration_Study = None
            self.Clear_Focus_If_It_Is_Within(self.Select_Method_Collapsible_Section)
            # Hide the select calibration collapsible section
            self.Select_Pressure_Calibration_Study_Collapsible_Section.setVisible(False)
            # Update the selections
            self.Select_Studies_For_Comparison_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=None)
            # Unhide the select studies for comparison collapsible section
            self.Select_Studies_For_Comparison_Collapsible_Section.setVisible(True)
            # Expand the select studies for comparison collapsible section
            self.Select_Studies_For_Comparison_Collapsible_Section.Expand_Or_Collapse_Section(True)
            # Set the title of the select studies for comparison collapsible section
            self.Select_Studies_For_Comparison_Collapsible_Section.Set_The_Section_Title_Text("Select Studies For Comparison")
            # Hide all upcoming sections
            self.Hide_Upcoming_Sections(self.Final_Actions_Collapsible_Section)
            # Scroll to the select studies for comparison collapsible section
            self.Scroll_To_A_Specific_Section(self.Select_Studies_For_Comparison_Collapsible_Section, Align_Top_To_Viewport_Midpoint=True)


    # Move from select calibration section to select conversions section
        # This section has multiple steps
    def Continue_From_Select_Pressure_Calibration_Study(self, Pressure_Calibration_Study):

        # In preset mode the middle sections are read-only
        if self.Disabled_Mode:
            return
        # Reset all upcoming sections
        self.Pressure_Calibration_Study = Pressure_Calibration_Study
        self.Select_Studies = None
        self.Select_Studies_For_Comparison_Content.Reset()
        # Get the relevant information from the selected pressure calibration study
        Workflow_Type = Pressure_Calibration_Study.get("Workflow Type")
        Originally_Selected_Calibration = Pressure_Calibration_Study.get("Selected Pressure Calibration Study")
        Originally_Selected_Composition = self.Composition
        Originally_Selected_Method = self.Method
        Different_Composition = Pressure_Calibration_Study.get("Different Composition")
        Different_Method = Pressure_Calibration_Study.get("Different Method")
        Different_Pressure_Calibration_Study = Pressure_Calibration_Study.get("Different Pressure Calibration Study")
        Is_Secondary_Conversion = Pressure_Calibration_Study.get("Implementing A Secondary Pressure Conversion", False)
        # Summarize the choices made in the select pressure calibration study section
        Pressure_Calibration_Study_Summary = Summary_Of_Selected_Pressure_Calibration_Study(Pressure_Calibration_Study)
        # Set the title of the select calibration section
        self.Select_Pressure_Calibration_Study_Collapsible_Section.Set_The_Section_Title_Text(f"Pressure Calibration Study: {Pressure_Calibration_Study_Summary}")
        self.Clear_Focus_If_It_Is_Within(self.Select_Pressure_Calibration_Study_Collapsible_Section)
        # Collapse the select calibration section
        self.Select_Pressure_Calibration_Study_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Update the selections with the pressure calibration study info
        self.Select_Studies_For_Comparison_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Pressure_Calibration_Study)
        # Unhide the select studies for comparison collapsible section
        self.Select_Studies_For_Comparison_Collapsible_Section.setVisible(True)
        # Expand the select studies for comparison collapsible section
        self.Select_Studies_For_Comparison_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Set the title of the select studies for comparison collapsible section
        self.Select_Studies_For_Comparison_Collapsible_Section.Set_The_Section_Title_Text("Select Studies For Comparison")
        # Hide all upcoming sections
        self.Hide_Upcoming_Sections(self.Final_Actions_Collapsible_Section)
        # Scroll to the select studies for comparison collapsible section
        self.Scroll_To_A_Specific_Section(self.Select_Studies_For_Comparison_Collapsible_Section, Align_Top_To_Viewport_Midpoint=True)


    # Move from select studies for comparison section to final actions section
    def Continue_From_Select_Studies_For_Comparison(self, Selected_Studies):

        # In preset mode the middle sections are read-only
        if self.Disabled_Mode:
            return
        # Reset all upcoming sections
        self.Selected_Studies = Selected_Studies
        self.Final_Actions_Content.Reset()
        # Count the number of selected studies
        Number_Of_Selected_Studies = len(Selected_Studies) if Selected_Studies else 0
        # Set the title of the select studies for comparison section
        self.Select_Studies_For_Comparison_Collapsible_Section.Set_The_Section_Title_Text(f"{Number_Of_Selected_Studies} studies selected for comparison")
        # Collapse the select studies for comparison section
        self.Select_Studies_For_Comparison_Collapsible_Section.Expand_Or_Collapse_Section(False)
        # Save all the section outputs
        self.Final_Actions_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Pressure_Calibration_Study, Selected_Studies=self.Selected_Studies)
        # Unhide the final actions section
        self.Final_Actions_Collapsible_Section.setVisible(True)
        # Expand the final actions section
        self.Final_Actions_Collapsible_Section.Expand_Or_Collapse_Section(True)
        # Set the title of the final actions section
        self.Final_Actions_Collapsible_Section.Set_The_Section_Title_Text(f"Final Actions")
        # Scroll to the final actions section
        self.Scroll_To_A_Specific_Section(self.Final_Actions_Collapsible_Section)


    # Set the method baised on the selected units
    def Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data(self):

        # Check if any units have been selected
        if self.Units is None:
            return None
            # Load local functions from local files
        from Reference_Values_And_Units import Method_Units

        # Return the method that corresponds to the selected units
        return {Unit_Type: Method for Method, Unit_Type in Method_Units.items()}.get(self.Units)


    # Check if the units are pressure
    def Check_If_The_Data_Units_Are_Pressure(self):

        if self.Units == "Pressure (GPa)":
            return True
        elif self.Units != "Pressure (GPa)":
            return False


    # Hide all the upcoming sections
    def Hide_Upcoming_Sections(self, Upcoming_Section):

        # Start with the section unhidden
        Hide_Section = False
        for Section in self.All_Collapsible_Sections:
            if Section is Upcoming_Section:
                Hide_Section = True
            if Hide_Section:
                Section.setVisible(False)


    def Clear_Focus_If_It_Is_Within(self, Section):

        Focus_Widget = QApplication.focusWidget()
        if Focus_Widget is None:
            return
        if Focus_Widget is Section or Section.isAncestorOf(Focus_Widget):
            Focus_Widget.clearFocus()


    # Scroll to a specific section
    def Find_The_Previous_Visible_Section(self, Section):

        try:
            Section_Index = self.All_Collapsible_Sections.index(Section)
        except ValueError:
            return None

        for Previous_Section in reversed(self.All_Collapsible_Sections[:Section_Index]):
            if Previous_Section.isVisible():
                return Previous_Section

        return None


    # Find the parent run-tab container so scroll targets can align with its separator
    def Find_The_Run_Tab_Container(self):

        Parent = self.parentWidget()
        while Parent is not None:
            if hasattr(Parent, "_Sep"):
                return Parent
            Parent = Parent.parentWidget()

        return None


    # Measure how far below the scroll viewport top the run-tab separator sits
    def Get_The_Run_Tab_Separator_Offset(self):

        Run_Tab_Container = self.Find_The_Run_Tab_Container()
        if Run_Tab_Container is None:
            return 0

        Viewport = self.Current_Scroll_Location.viewport()
        Separator_Bottom_Global_Y = Run_Tab_Container._Sep.mapToGlobal(QPoint(0, Run_Tab_Container._Sep.height())).y()
        Viewport_Top_Global_Y = Viewport.mapToGlobal(QPoint(0, 0)).y()
        return Separator_Bottom_Global_Y - Viewport_Top_Global_Y


    # Scroll to a specific section
    def Scroll_To_A_Specific_Section(self, Section, Align_To_Previous_Gap_Midpoint=False, Align_Top_To_Run_Tab_Bottom=False, Align_Top_To_Viewport_Midpoint=False):

        def Do_Scroll():
            scroll_widget = self.Current_Scroll_Location.widget()
            Section_Top = Section.mapTo(scroll_widget, QPoint(0, 0)).y()
            Target_Y = Section_Top - 12

            if Align_To_Previous_Gap_Midpoint:
                Previous_Section = self.Find_The_Previous_Visible_Section(Section)
                if Previous_Section is not None:
                    Previous_Section_Bottom = Previous_Section.mapTo(scroll_widget, QPoint(0, Previous_Section.height())).y()
                    Target_Y = round((Previous_Section_Bottom + Section_Top) / 2) - self.Get_The_Run_Tab_Separator_Offset()
            elif Align_Top_To_Run_Tab_Bottom:
                Target_Y = Section_Top - self.Get_The_Run_Tab_Separator_Offset()
            elif Align_Top_To_Viewport_Midpoint:
                Previous_Section = self.Find_The_Previous_Visible_Section(Section)
                if Previous_Section is not None:
                    Target_Y = Previous_Section.mapTo(scroll_widget, QPoint(0, 0)).y()

            Scroll_Bar = self.Current_Scroll_Location.verticalScrollBar()
            Scroll_Bar.setValue(max(0, min(Target_Y, Scroll_Bar.maximum())))

        QTimer.singleShot(50, Do_Scroll)


    def Scroll_To_A_Pressure_Calibration_Subsection(self, Section):

        if not self.Select_Pressure_Calibration_Study_Collapsible_Section.isVisible():
            return
        if not self.Select_Pressure_Calibration_Study_Collapsible_Section.Section_Is_Expanded():
            return
        if Section is None:
            return

        self.Scroll_To_A_Specific_Section(Section)


    # Expand a section and scroll it into view
    def Focus_On_Section(self, Section):

        Section.setVisible(True)
        Section.Expand_Or_Collapse_Section(True)
        self.Scroll_To_A_Specific_Section(Section)


    # Check whether new enter-data units are compatible with a recalculation run
    def Entered_Data_Matches_This_Run(self):

        if not self.Disabled_Mode or not self.Preset_Units or not self.Units:
            return True

        if self.Units == self.Preset_Units:
            return True

        return self.Preset_Units in Volume_Units and self.Units in Volume_Units


    # Check whether the current enter-data widget differs from the saved run state
    def Enter_Data_Has_Unsaved_Changes(self):

        Current_Data = self.Enter_Data_Content.Get_The_Current_Entered_Data()
        Saved_Data = self.Data or {}

        if Current_Data.get("Data") != Saved_Data.get("Data"):
            return True
        if Current_Data.get("Units") != Saved_Data.get("Units"):
            return True
        if Current_Data.get("Volume Unit") != Saved_Data.get("Volume Unit"):
            return True
        if Current_Data.get("Source Type") != Saved_Data.get("Source Type"):
            return True
        if Current_Data.get("Raw Data") != Saved_Data.get("Raw Data"):
            return True
        if Current_Data.get("Error Propagation Enabled") != Saved_Data.get("Error Propagation Enabled"):
            return True

        Current_Uncertainty = Current_Data.get("Uncertainty Data", {})
        Saved_Uncertainty = Saved_Data.get("Uncertainty Data", {})
        return (
            Current_Uncertainty.get("Error Propagation Enabled") != Saved_Uncertainty.get("Error Propagation Enabled")
            or Current_Uncertainty.get("Error Propagation Source Type") != Saved_Uncertainty.get("Error Propagation Source Type")
            or Current_Uncertainty.get("Error Propagation Values") != Saved_Uncertainty.get("Error Propagation Values")
        )


    # Drive the existing section workflows until final actions are ready for export
    def Prepare_Final_Actions_For_Menu_Save(self):

        self.Focus_On_Section(self.Enter_Data_Collapsible_Section)
        if self.Data is None or self.Enter_Data_Has_Unsaved_Changes():
            if not self.Enter_Data_Content.Validate_And_Warn():
                return False
            self.Enter_Data_Content.Send_Out_Entered_Data()

        if self.Disabled_Mode:
            if not self.Entered_Data_Matches_This_Run():
                return False
        else:
            Current_Composition = self.Select_Composition_Content.Get_Current_Selected_Composition()
            if self.Composition is None or Current_Composition != self.Composition:
                self.Focus_On_Section(self.Select_Composition_Collapsible_Section)
                self.Select_Composition_Content.When_The_Continue_Button_Is_Clicked()
                if self.Composition is None:
                    return False

            if self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data() is None:
                Current_Method = self.Select_Method_Content.Get_Current_Selected_Method()
                if self.Method is None or Current_Method != self.Method:
                    self.Focus_On_Section(self.Select_Method_Collapsible_Section)
                    self.Select_Method_Content.When_The_Continue_Button_Is_Clicked()
                    if self.Method is None:
                        return False

            if self.Check_If_The_Data_Units_Are_Pressure():
                Current_Calibration = self.Select_Pressure_Calibration_Study_Content.Get_The_Current_Selected_Pressure_Calibration_Study()
                if self.Pressure_Calibration_Study is None or Current_Calibration != self.Pressure_Calibration_Study:
                    self.Focus_On_Section(self.Select_Pressure_Calibration_Study_Collapsible_Section)
                    self.Select_Pressure_Calibration_Study_Content.When_The_Continue_Button_Is_Clicked()
                    if self.Pressure_Calibration_Study is None:
                        return False

            Current_Selected_Studies = self.Select_Studies_For_Comparison_Content.Get_Current_Selected_Studies_For_Comparison()
            if self.Selected_Studies != Current_Selected_Studies:
                self.Focus_On_Section(self.Select_Studies_For_Comparison_Collapsible_Section)
                self.Select_Studies_For_Comparison_Content.When_The_Continue_Button_Is_Clicked()
            elif self.Selected_Studies is None:
                self.Focus_On_Section(self.Select_Studies_For_Comparison_Collapsible_Section)
                self.Select_Studies_For_Comparison_Content.When_The_Continue_Button_Is_Clicked()

        self.Final_Actions_Content.Refresh(
            Data=self.Data,
            Units=self.Units,
            Composition=self.Composition,
            Method=self.Method,
            Pressure_Calibration_Study=self.Pressure_Calibration_Study,
            Selected_Studies=self.Selected_Studies,
        )
        self.Final_Actions_Content.Ensure_Figures_Are_Generated()
        self.Focus_On_Section(self.Final_Actions_Collapsible_Section)
        return True


    # Route File > Open to the enter-data upload flow for this run
    def Handle_Menu_Open_Action(self):

        self.Focus_On_Section(self.Enter_Data_Collapsible_Section)
        self.Enter_Data_Content.Select_The_File_Upload_Option()
        self.Enter_Data_Content.When_Browse_Button_Clicked()


    # Route File > Save Data to the final-actions export flow for this run
    def Handle_Menu_Save_Action(self):

        if not self.Prepare_Final_Actions_For_Menu_Save():
            return
        self.Final_Actions_Content.When_Export_Button_Is_Clicked()


    # Collapse and disable the middle sections
    def Disable_The_Middle_Collapsible_Sections(self, Disabled: bool):

        # Check if the collapsible section is a middle section
        for Section in self.List_Of_Middle_Collapsible_Sections:
            # Check if the section is disabled
            if Disabled:
                Section.Expand_Or_Collapse_Section(False)
            # Disable the collapsible section
            Section.Disable_Collapsible_Section(Disabled)


    # Create a new run tab with the same user selections
    def Recalculate(self):

        # Send out the current user selections
        self.Add_New_Run.emit({"Composition": self.Composition, "Method": self.Method, "Pressure_Calibration_Study": self.Pressure_Calibration_Study, "Selected_Studies": self.Selected_Studies, "Units": self.Units})


    # Clear all run tabs and start fresh
    def Reset_Application(self):

        # Send out the reset signal
        self.Request_Reset_All.emit()




