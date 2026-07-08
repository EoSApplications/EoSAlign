# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import Qt, QTimer, QEvent
    # Load local functions from local files
from Collapsible_Sections import Collapsible_Content_Container
from Enter_Data import Enter_Data
from Select_Composition import Select_Composition
from Select_Method import Select_Method
from Select_Pressure_Calibration_Study import Select_Pressure_Calibration_Study, Summary_Of_Selected_Pressure_Calibration_Study
from Select_Studies_For_Comparison import Select_Studies_For_Comparison
from Select_Final_Actions import Select_Final_Actions
from EoS_Math.Build_Dataframe import Get_Compositions_For_Method, Get_Methods_For_Composition




# Make the main content scrollable
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



# All steps layout for users who want to see all steps at once and jump between them in any order
class All_Steps_Layout(QWidget):
    def __init__(self):
        super().__init__()
        # Store the user selections
        self.Data = None
        self.Units = None
        self.Composition = None
        self.Method = None
        self.Calibration = None
        self.Selected_Studies = None
        # Create the collapsable sections for all steps
        self.Create_Collapsible_Sections_For_All_Steps()
        # Start with all sections disabled
        self.Enable_Or_Disable_Sections()


    # Create a collapsable section for each step
    def Create_Collapsible_Sections_For_All_Steps(self):

        # Create the collapsable section display
        Collapsible_Sections_Display = Make_Content_Layout_Scrollable()
        self.Collapsible_Sections_Layout = QVBoxLayout(Collapsible_Sections_Display)
        self.Collapsible_Sections_Layout.setContentsMargins(5, 0, 5, 0)
        self.Collapsible_Sections_Layout.setSpacing(5)
        self.Collapsible_Sections_Layout.setAlignment(Qt.AlignTop)

        # Enter Data
            # Get enter data content
        self.Enter_Data_Content = Enter_Data(Once_A_Change_Is_Made=self.When_Enter_Data_Is_Changed, Show_Continue_Button=False, Parent=self)
            # Add the enter data content to a collapsible section
        self.Enter_Data_Collapsible_Section = Collapsible_Content_Container("Enter Data", self.Enter_Data_Content, Show_Container_Title=True)
            # Add the enter data collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Enter_Data_Collapsible_Section)

        # Select composition
            # Get the select composition content
        self.Select_Composition_Content = Select_Composition(Application="EoSAlign", Once_A_Change_Is_Made=self.When_Select_Composition_Changed, Show_Continue_Button=False, Parent=self)
            # Add the select composition content to a collapsible section
        self.Select_Composition_Collapsible_Section = Collapsible_Content_Container("Select Composition", self.Select_Composition_Content, Show_Container_Title=True)
            # Add the select composition collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Composition_Collapsible_Section)

        # Select method
            # Get the select method content
        self.Select_Method_Content = Select_Method(Once_A_Change_Is_Made=self.When_Select_Method_Changed, Show_Continue_Button=False, Parent=self)
            # Add the select method content to a collapsible section
        self.Select_Method_Collapsible_Section = Collapsible_Content_Container("Select Method", self.Select_Method_Content, Show_Container_Title=True)
            # Add the select method collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Method_Collapsible_Section)

        # Select calibration - Only show if the units are pressure
            # Get the select calibration content
        self.Select_Calibration_Content = Select_Pressure_Calibration_Study(Application="EoSAlign", Composition=None, Method=None, Once_A_Change_Is_Made=self.When_Select_Calibration_Changed, Show_Continue_Button=False, Parent=self)
            # Add the select calibration content to a collapsible section
        self.Select_Calibration_Collapsible_Section = Collapsible_Content_Container("Select Calibration", self.Select_Calibration_Content, Show_Container_Title=True, Expanding_Content=True)
            # Add the select calibration collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Calibration_Collapsible_Section)

        # Select studies to convert
            # Get the select calibrations to convert content
        self.Select_Studies_For_Comparison_Content = Select_Studies_For_Comparison(Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Show_Continue_Button=False, Show_Preview=True, Once_A_Change_Is_Made=self.When_Select_Studies_For_Comparison_Changed, Parent=self)
            # Add the select calibrations to convert content to a collapsible section
        self.Select_Studies_For_Comparison_Collapsible_Section = Collapsible_Content_Container("Select Studies For Comparison", self.Select_Studies_For_Comparison_Content, Show_Container_Title=True, Expanding_Content=True)
            # Add the select calibrations to convert collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Select_Studies_For_Comparison_Collapsible_Section)

        # Final actions
            # Get the final actions content
        self.Final_Actions_Content = Select_Final_Actions(Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Selected_Studies=None, Show_Continue_Button=False, Show_Recalculate_Button=False, Show_Reset_Button=False, Run_Label="Run 1", Display_Run_Label="", Auto_Generate_Figures=False, Parent=self)
            # Add the final actions content to a collapsible section
        self.Final_Actions_Collapsible_Section = Collapsible_Content_Container("Actions", self.Final_Actions_Content, Show_Container_Title=True)
            # Add the final actions collapsible section to the layout
        self.Collapsible_Sections_Layout.addWidget(self.Final_Actions_Collapsible_Section)

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
        self.All_Collapsible_Sections = [ self.Enter_Data_Collapsible_Section, self.Select_Composition_Collapsible_Section, self.Select_Method_Collapsible_Section, self.Select_Calibration_Collapsible_Section, self.Select_Studies_For_Comparison_Collapsible_Section, self.Final_Actions_Collapsible_Section]


    # Update the user selections and propagate the change to the other sections
    def When_Enter_Data_Is_Changed(self, Data):

        # Save the previously selected units
        Previous_Units = self.Units
        # Update data
        self.Data = Data
        # Update units
        self.Units = Data.get("Units") if isinstance(Data, dict) else None
        # Auto-determine method from units; if pressure, method must be selected by user
        Auto_Method = self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data()
        if Auto_Method is not None:
            self.Method = Auto_Method
        elif self.Units != Previous_Units:
            self.Method = None
        # Check if the units have changed
        if self.Units != Previous_Units:
            # Propagate the changes from enter data
            self.Propagate_Changes_From_Enter_Data()
        else:
            # Units are the same so downstream selections remain valid, but propagate the new data reference so the studies section and final actions use the latest values
            if self.Check_If_There_Is_Enough_Information_To_Select_Studies_For_Comparison():
                self.Select_Studies_For_Comparison_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Calibration)
                self.Selected_Studies = self.Select_Studies_For_Comparison_Content.Get_Current_Selected_Studies_For_Comparison()
            self.Propagate_Changes_To_The_Final_Actions_Content()
        self.Enable_Or_Disable_Sections()


    # Update the user selections and propagate the changes to the other sections
    def When_Select_Composition_Changed(self, Composition):

        # Update composition
        self.Composition = Composition if Composition else None
        # Propagate the changes to the other sections
        self.Propagate_Changes_From_Select_Composition()
        self.Enable_Or_Disable_Sections()


    # Update the user selections and propagate the changes to the other sections
    def When_Select_Method_Changed(self, Method):

        # Ignore widget-driven changes when method is auto-determined from units
        if self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data() is not None:
            return
        # Update method
        self.Method = Method if Method else None
        # Propagate the changes to the other sections
        self.Propagate_Changes_From_Select_Method()
        self.Enable_Or_Disable_Sections()


    # Update the user selections and propagate the changes to the other sections
    def When_Select_Calibration_Changed(self, Calibration):

        # Update calibration
        self.Calibration = Calibration
        # Propagate the changes to the other sections
        self.Propagate_Changes_From_Select_Calibration()
        self.Enable_Or_Disable_Sections()


    # Update the user selections and propagate the changes to the other sections
    def When_Select_Studies_For_Comparison_Changed(self, Selected_Studies):
        
        # Update selected studies for comparison
        self.Selected_Studies = Selected_Studies
        # Propagate the changes to the other sections
        self.Propagate_Changes_To_The_Final_Actions_Content()
        self.Enable_Or_Disable_Sections()



    # Propagate changes to the other sections
    def Propagate_Changes_From_Enter_Data(self):

        # Filter compositions to those with calibrations for the auto-determined method;
        # for pressure units the user picks a method later so no filter is applied yet.
        Auto_Method = self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data()
        Allowed_Compositions = set(Get_Compositions_For_Method(Auto_Method)) if Auto_Method is not None else None
        self.Select_Composition_Content.Refresh(Data=self.Data, Units=self.Units, Allowed_Compositions=Allowed_Compositions)
        self.Propagate_Changes_From_Select_Composition()


    # Propagate changes to the other sections
    def Propagate_Changes_From_Select_Composition(self):

        # For pressure units the user picks a method — filter to methods that have calibrations
        # for the selected composition. For non-pressure the method is auto-determined and the
        # method section is hidden, so no filter is needed.
        if self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data() is None and self.Composition is not None:
            Allowed_Methods = set(Get_Methods_For_Composition(self.Composition))
        else:
            Allowed_Methods = None
        self.Select_Method_Content.Refresh(Composition=self.Composition, Allowed_Methods=Allowed_Methods)
        self.Propagate_Changes_From_Select_Method()



    # Propagate changes to the other sections
    def Propagate_Changes_From_Select_Method(self):

        # Only update the possible calibrations
        if self.Check_If_The_User_Should_Select_A_Calibration():
            self.Select_Calibration_Content.Refresh(Composition=self.Composition, Method=self.Method)
            self.Calibration = self.Select_Calibration_Content.Get_The_Current_Selected_Pressure_Calibration_Study()
        else:
            self.Calibration = None
            self.Select_Calibration_Content.Reset()
        self.Propagate_Changes_From_Select_Calibration()



    # Propagate changes to the other sections
    def Propagate_Changes_From_Select_Calibration(self):

        # Only update studies for selection
        if self.Check_If_There_Is_Enough_Information_To_Select_Studies_For_Comparison():
            self.Select_Studies_For_Comparison_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Calibration)
            self.Selected_Studies = self.Select_Studies_For_Comparison_Content.Get_Current_Selected_Studies_For_Comparison()
        else:
            self.Selected_Studies = None
            self.Select_Studies_For_Comparison_Content.Reset()
        self.Propagate_Changes_To_The_Final_Actions_Content()


    # Sent the current selections to the final actions content
    def Propagate_Changes_To_The_Final_Actions_Content(self):

        # Send the current selections to the final actions content
        self.Final_Actions_Content.Refresh(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=self.Calibration, Selected_Studies=self.Selected_Studies)



    # Enable or disable sections baised on the user inputs
    def Enable_Or_Disable_Sections(self):

        # Check what inputs have been provided
        Check_If_Data_Has_Been_Entered = self.Data is not None
        Check_If_Units_Are_Pressure = self.Units is not None and self.Units == "Pressure (GPa)"
        Check_If_A_Composition_Has_Been_Entered = self.Composition is not None
        Check_If_A_Method_Has_Been_Entered = self.Method is not None
        Check_If_A_Calibration_Has_Been_Selected = self.Calibration is not None
        Check_If_The_Select_Calibration_Section_Should_Be_Displayed = self.Check_If_The_User_Should_Select_A_Calibration()
        Check_If_A_Calibration_Has_Been_Selected_And_If_The_Select_Calibration_Section_Should_Be_Displayed = Check_If_A_Calibration_Has_Been_Selected if Check_If_The_Select_Calibration_Section_Should_Be_Displayed else True
        Check_If_Any_Studies_Have_Been_Selected_For_Comparison = (self.Selected_Studies is not None and len(self.Selected_Studies) > 0)
        # Always enable the enter data section
        self.Enable_Or_Disable_A_Section(self.Enter_Data_Collapsible_Section, True)
        # Only enable the select composition section if data has been entered
        self.Enable_Or_Disable_A_Section(self.Select_Composition_Collapsible_Section, Check_If_Data_Has_Been_Entered)
        # Hide the select method section when the method is auto-determined from the selected units and only show it when pressure units require the user to choose a method
        Check_If_Method_Is_Auto_Set = self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data() is not None
        self.Select_Method_Collapsible_Section.setVisible(not Check_If_Method_Is_Auto_Set)
        if not Check_If_Method_Is_Auto_Set:
            self.Enable_Or_Disable_A_Section(self.Select_Method_Collapsible_Section, Check_If_Data_Has_Been_Entered and Check_If_A_Composition_Has_Been_Entered)
        # Change the visibility of the select calibration section based on the units of the entered data
        self.Select_Calibration_Collapsible_Section.setVisible(Check_If_The_Select_Calibration_Section_Should_Be_Displayed)
        # Only enable the select calibration section if data has been entered, if a composition has been selected, if a method has been selected, and if the units of the entered data are pressure
        self.Enable_Or_Disable_A_Section(self.Select_Calibration_Collapsible_Section, Check_If_Data_Has_Been_Entered and Check_If_A_Composition_Has_Been_Entered and Check_If_A_Method_Has_Been_Entered)
        # Only enable the select studies for comparison section if data has been entered, if a composition has been selected, if a method has been selected, and if a calibration has been selected (if the select calibration section should be displayed)
        self.Enable_Or_Disable_A_Section(self.Select_Studies_For_Comparison_Collapsible_Section, Check_If_Data_Has_Been_Entered and Check_If_A_Composition_Has_Been_Entered and Check_If_A_Method_Has_Been_Entered and Check_If_A_Calibration_Has_Been_Selected_And_If_The_Select_Calibration_Section_Should_Be_Displayed)
        # Only enable the final actions section if data has been entered, if a composition has been selected, if a method has been selected, if a calibration has been selected (if the select calibration section should be displayed), and if any studies have been selected for comparison
        self.Enable_Or_Disable_A_Section(self.Final_Actions_Collapsible_Section, Check_If_Data_Has_Been_Entered and Check_If_A_Composition_Has_Been_Entered and Check_If_A_Method_Has_Been_Entered and Check_If_A_Calibration_Has_Been_Selected_And_If_The_Select_Calibration_Section_Should_Be_Displayed and Check_If_Any_Studies_Have_Been_Selected_For_Comparison)



    # Enable or disable a section
    def Enable_Or_Disable_A_Section(self, Section, Enabled):

        # setEnabled will automatically either enable the section or disable the section and grey it out
        Section.setEnabled(Enabled)


    # Expand a section and scroll it into view
    def Focus_On_Section(self, Section):

        Section.setVisible(True)
        Section.Expand_Or_Collapse_Section(True)
        self.Scroll_To_A_Specific_Section(Section)


    # Drive the existing section validations until final actions are ready for export
    def Prepare_Final_Actions_For_Menu_Save(self):

        self.Focus_On_Section(self.Enter_Data_Collapsible_Section)
        if not self.Enter_Data_Content.Validate_And_Warn():
            return False
        self.Enter_Data_Content.Send_Out_Entered_Data()

        if self.Composition is None:
            self.Focus_On_Section(self.Select_Composition_Collapsible_Section)
            self.Select_Composition_Content.When_The_Continue_Button_Is_Clicked()
            if self.Composition is None:
                return False

        if self.Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data() is None and self.Method is None:
            self.Focus_On_Section(self.Select_Method_Collapsible_Section)
            self.Select_Method_Content.When_The_Continue_Button_Is_Clicked()
            if self.Method is None:
                return False

        if self.Check_If_The_User_Should_Select_A_Calibration() and self.Calibration is None:
            self.Focus_On_Section(self.Select_Calibration_Collapsible_Section)
            self.Select_Calibration_Content.When_The_Continue_Button_Is_Clicked()
            if self.Calibration is None:
                return False

        if not self.Selected_Studies:
            self.Focus_On_Section(self.Select_Studies_For_Comparison_Collapsible_Section)
            self.Select_Studies_For_Comparison_Content.When_The_Continue_Button_Is_Clicked()

        self.Final_Actions_Content.Refresh(
            Data=self.Data,
            Units=self.Units,
            Composition=self.Composition,
            Method=self.Method,
            Pressure_Calibration_Study=self.Calibration,
            Selected_Studies=self.Selected_Studies,
        )
        self.Final_Actions_Content.Ensure_Figures_Are_Generated()
        self.Focus_On_Section(self.Final_Actions_Collapsible_Section)
        return True


    # Route File > Open to the enter-data upload flow
    def Handle_Menu_Open_Action(self):

        self.Focus_On_Section(self.Enter_Data_Collapsible_Section)
        self.Enter_Data_Content.Select_The_File_Upload_Option()
        self.Enter_Data_Content.When_Browse_Button_Clicked()


    # Route File > Save Data to the final-actions export flow
    def Handle_Menu_Save_Action(self):

        if not self.Prepare_Final_Actions_For_Menu_Save():
            return
        self.Final_Actions_Content.When_Export_Button_Is_Clicked()



    # Set the method baised on the selected units
    def Find_The_Method_Baised_On_The_User_Selected_Units_In_Enter_Data(self):

        # Check if any units have been selected
        if self.Units is None:
            return None
            # Load local functions from local files
        from Reference_Values_And_Units import Method_Units

        # Return the method that corresponds to the selected units
        return {Unit_Type: Method for Method, Unit_Type in Method_Units.items()}.get(self.Units)


    # Check if the user should select a calibration based on the units of the entered data
    def Check_If_The_User_Should_Select_A_Calibration(self):

        # Check if the units are pressure
        if self.Units == "Pressure (GPa)":
            return True
        else:
            return False
        

    # Check if we have enough context to show the select studies for comparison section
    def Check_If_There_Is_Enough_Information_To_Select_Studies_For_Comparison(self):

        # Check if data has been entered, a composition has been selection, and a method has been selected
        if not (self.Composition and self.Method and self.Data):
            return False
        # Check if the units of the entered data are pressure and if a calibration has been selected
        if self.Check_If_The_User_Should_Select_A_Calibration() and self.Calibration is None:
            return False
        
        return True




