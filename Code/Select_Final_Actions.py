# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox)
from PySide6.QtCore import Signal
import os
from pathlib import Path
from uuid import uuid4
    # Load local functions from local files
from Settings import Settings
from Plot_Window import Plot_Window
from Conversion_Window import Data_Preview_Dialog
from EoS_Math.Build_Dataframe import Build_Dataframe, Translate_Pressure_Calibration_Study, Calibration_Metadata
from Message_Manager import Warning_Message, Success_Message





# Build the {Pressure_<key> -> Pressure_<study> | <comp> | <method> | ...} rename map used by
# CSV export, from a dataframe's own columns and the loaded Calibration_Metadata. Pulled out to
# a module-level function (rather than inlined in When_Export_Button_Is_Clicked) so it can be
# unit-tested against a synthetic dataframe + metadata dict without needing a live Qt widget --
# see tests/export/.
def Build_Pressure_Column_Rename_Map(DataFrame_Columns, Metadata_By_Calibration_Key):

    Rename_Map = {}
    for col in DataFrame_Columns:
        if col.startswith("Pressure_") and not col.startswith("Pressure_From_"):
            cal_name = col[len("Pressure_"):]
            meta = Metadata_By_Calibration_Key.get(cal_name, {})
            if meta:
                study = meta.get("Study", cal_name)
                comp = meta.get("Composition", "")
                method = meta.get("Method", "")
                eos = meta.get("Equation of State", "")
                k0_fixed = meta.get("Is The Initial Bulk Modulus Fixed?", "")
                cal_to = meta.get("Reference Study", "")
                max_p = meta.get("Maximum Pressure", "")
                ptm = meta.get("Pressure Transmitting Medium", "")
                Rename_Map[col] = f"Pressure_{study} | {comp} | {method} | {eos} | K0 Fixed: {k0_fixed} | cal_to: {cal_to} | Max Pressure: {max_p} | PTM: {ptm}"
    # Return the column rename map for use with DataFrame.rename(columns=...)
    return Rename_Map


# Build the "_solved_pressures.csv" subset: the measured column plus every renamed pressure
# column, with the measured column itself relabeled. Returns None when there are no renamed
# pressure columns to include (mirrors the "no pressures solved" branch in the export flow).
def Build_Solved_Pressures_Dataframe(Export_DataFrame, Display_Units):

    Measured_Col = Export_DataFrame.columns[0]
    Pressure_Cols = [col for col in Export_DataFrame.columns if col.startswith("Pressure_") and " | " in col]
    if not Pressure_Cols:
        return None
    Pressures_Only = Export_DataFrame[[Measured_Col] + Pressure_Cols].copy()
    # Return the relabeled solved-pressures subset
    return Pressures_Only.rename(columns={Measured_Col: f"Input_{Display_Units}, STUDIES USED:"})




# Create the select final actions content
class Select_Final_Actions(QWidget):

    # Signals emitted when user wants to recalculate or reset
    Recalculate_Requested = Signal()
    Reset_Application_Requested = Signal()

    def __init__(self, *, Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Selected_Studies=None, Show_Continue_Button=False, Show_Recalculate_Button=True, Show_Reset_Button=True, Run_Label=None, Display_Run_Label=None, Auto_Generate_Figures=True, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Show_Continue_Button = Show_Continue_Button
        self.Show_Recalculate_Button = Show_Recalculate_Button
        self.Show_Reset_Button = Show_Reset_Button
        self.Auto_Generate_Figures = Auto_Generate_Figures
        self.Settings = Settings
        self.Data = Data
        self.Units = Units
        self.Composition = Composition
        self.Method = Method
        self.Pressure_Calibration_Study = Pressure_Calibration_Study
        self.Selected_Studies = Selected_Studies
        self.Run_Label = Run_Label or "Run"
        self.Display_Run_Label = self.Run_Label if Display_Run_Label is None else Display_Run_Label
        self.DataFrame = None
        self.File_Ok = False
        self.Units_Ok = False
        self.Error_Msg = ""
        self.Figures_Dir = None
        self.Figure_Run_Token = uuid4().hex[:8]

        # Create the select final actions display
        self.Create_The_Select_Final_Actions_Display()

        # Connect the signals
        self.Connect_Signals()

        # Build the dataframe immediately
        self.Build_DataFrame()

        # Enable or disable the final action buttons based on the current state of inputs and results
        self.Enable_The_Final_Action_Buttons()


    # Stop any in-flight figure generation, delete cached PNGs for the current dataframe, and clear the figures directory handle
    def Invalidate_Figure_Cache(self):
        # Nothing to invalidate when no directory has been created yet
        if self.Figures_Dir is None:
            return

        try:
            from Plots.Generate_Figures import Cancel_Generation

            # Cancel any active worker tied to the current figures directory before deleting files
            Cancel_Generation(self.Figures_Dir)
        except Exception:
            pass

        try:
            Figures_Path = Path(self.Figures_Dir)

            # Delete all cached display PNGs and the cached generation signature
            for Cached_File in Figures_Path.glob("*"):
                if Cached_File.is_file():
                    try:
                        Cached_File.unlink()
                    except Exception:
                        pass

            # Delete all cached export-variant PNGs, then remove empty directories
            Export_Dir = Figures_Path / "export_variants"
            if Export_Dir.exists():
                for Cached_File in Export_Dir.rglob("*"):
                    if Cached_File.is_file():
                        try:
                            Cached_File.unlink()
                        except Exception:
                            pass
                for Cached_Dir in sorted(Export_Dir.rglob("*"), reverse=True):
                    if Cached_Dir.is_dir():
                        try:
                            Cached_Dir.rmdir()
                        except Exception:
                            pass
                try:
                    Export_Dir.rmdir()
                except Exception:
                    pass
        except Exception:
            pass

        # Clear the current directory handle so any future plot request forces a fresh build
        self.Figures_Dir = None


    # Advance the figure run token so the next dataframe build writes to a fresh figures directory
    def Start_A_New_Figure_Run(self):
        # The directory name includes this token, so changing it guarantees a new cache location
        self.Figure_Run_Token = uuid4().hex[:8]


    # Reset the select final actions display to its initial state
    def Reset(self):
        # Discard any cached figures tied to the previous run before clearing state
        self.Invalidate_Figure_Cache()

        # Clear the input parameters
        self.Data = None
        self.Units = None
        self.Composition = None
        self.Method = None
        self.Pressure_Calibration_Study = None
        self.Selected_Studies = None
        self.DataFrame = None
        self.File_Ok = False
        self.Units_Ok = False
        self.Error_Msg = ""
        self.Figures_Dir = None

        # Enable or disable the final action buttons based on the current state of inputs and results
        self.Enable_The_Final_Action_Buttons()


    # Get the default directory used when exporting a file
    def Get_The_Default_Export_Directory(self):

        Home_Directory = os.path.expanduser("~")
        Desktop_Directory = os.path.join(Home_Directory, "Desktop")

        if os.path.isdir(Desktop_Directory):
            return Desktop_Directory

        return Home_Directory


    # Refresh the select final actions display
    def Refresh(self, *, Data=None, Units=None, Composition=None, Method=None, Pressure_Calibration_Study=None, Selected_Studies=None, Show_Continue_Button=False):

        # Get the input parameters
        self.Data = Data
        self.Units = Units
        self.Composition = Composition
        self.Method = Method
        self.Pressure_Calibration_Study = Pressure_Calibration_Study
        self.Selected_Studies = Selected_Studies

        # Build the dataframe immediately with new parameters
        self.Build_DataFrame()

        # Enable or disable the final action buttons based on the current state of inputs and results
        self.Enable_The_Final_Action_Buttons()

        self.Check_If_All_Previous_Selections_Are_Complete()


    # Create the select final actions display
    def Create_The_Select_Final_Actions_Display(self):

        # Create the select final actions display
        self.setObjectName("CollapsibleContent")
        Select_Final_Actions_Display = QVBoxLayout(self)
        Select_Final_Actions_Display.setContentsMargins(5, 5, 5, 5)
        Select_Final_Actions_Display.setSpacing(8)

        # Create a layout for the action buttons
        Possible_Actions = QWidget()
        Possible_Actions.setObjectName("CollapsibleSubContainer")
        Possible_Actions_Layout = QVBoxLayout(Possible_Actions)

        # Plot results button
        Button_Row_1 = QHBoxLayout()
        self.Plot_Results_Button = QPushButton("Plot Results")
        self.Plot_Results_Button.setFixedHeight(36)
        self.Plot_Results_Button.setObjectName("Primary_Button")
        Button_Row_1.addWidget(self.Plot_Results_Button)
        Possible_Actions_Layout.addLayout(Button_Row_1)

        # Preview and Export buttons
        Button_Row_2 = QHBoxLayout()
        
        self.Preview_Data_Button = QPushButton("Preview CSV Data")
        self.Preview_Data_Button.setFixedHeight(32)
        self.Preview_Data_Button.setObjectName("Primary_Button")
        Button_Row_2.addWidget(self.Preview_Data_Button)

        self.Export_Results_Button = QPushButton("Export Results")
        self.Export_Results_Button.setFixedHeight(32)
        self.Export_Results_Button.setObjectName("Primary_Button")
        Button_Row_2.addWidget(self.Export_Results_Button)

        Possible_Actions_Layout.addLayout(Button_Row_2)

        # Recalculate and Reset buttons
        if self.Show_Recalculate_Button or self.Show_Reset_Button:
            Button_Row_3 = QHBoxLayout()

            if self.Show_Recalculate_Button:
                self.Recalculate_Button = QPushButton("Recalculate")
                self.Recalculate_Button.setFixedHeight(32)
                self.Recalculate_Button.setObjectName("Secondary_Button")
                Button_Row_3.addWidget(self.Recalculate_Button)

            if self.Show_Reset_Button:
                self.Reset_Application_Button = QPushButton("Reset Application")
                self.Reset_Application_Button.setFixedHeight(32)
                self.Reset_Application_Button.setObjectName("Secondary_Button")
                Button_Row_3.addWidget(self.Reset_Application_Button)

            Possible_Actions_Layout.addLayout(Button_Row_3)

        # Add the possible actions group box to the main layout
        Select_Final_Actions_Display.addWidget(Possible_Actions)


    # Connect the text boxes and buttons to their respective functions
    def Connect_Signals(self):
        self.Plot_Results_Button.clicked.connect(self.When_Plot_Button_Is_Clicked)
        self.Preview_Data_Button.clicked.connect(self.When_Preview_Button_Is_Clicked)
        self.Export_Results_Button.clicked.connect(self.When_Export_Button_Is_Clicked)
        if self.Show_Recalculate_Button and hasattr(self, 'Recalculate_Button'):
            self.Recalculate_Button.clicked.connect(self.Recalculate_Requested.emit)
        if self.Show_Reset_Button and hasattr(self, 'Reset_Application_Button'):
            self.Reset_Application_Button.clicked.connect(self.When_Reset_Application_Button_Is_Clicked)

    # Confirm and emit the reset signal
    def When_Reset_Application_Button_Is_Clicked(self):
        Confirm = Warning_Message(
            self,
            "Reset Application",
            Buttons=QMessageBox.Yes | QMessageBox.No,
            Default_Button=QMessageBox.No,
        )
        if Confirm == QMessageBox.Yes:
            self.Reset_Application_Requested.emit()


    # Check if all required inputs are present to enable the actions
    def Check_If_All_Previous_Selections_Are_Complete(self):

        # Check for inputs
        return (self.Data is not None and self.Composition is not None and self.Method is not None and self.Selected_Studies is not None and len(self.Selected_Studies) > 0)


    # Get the selected calibration keys from selected studies
    def Get_Selected_Calibration_Keys(self):

        # Return empty list if no studies selected
        if self.Selected_Studies is None or len(self.Selected_Studies) == 0:
            return []

        # Extract calibration keys from selected studies
        Selected_Calibration_Keys = [study['Calibration Key'] for study in self.Selected_Studies]

        return Selected_Calibration_Keys


    # Build the dataframe from selected studies
    def Build_DataFrame(self):

        if self.Data is None:
            self.Invalidate_Figure_Cache()
            self.DataFrame = None
            self.File_Ok = False
            self.Units_Ok = False
            self.Error_Msg = "Incomplete selection. Please complete all previous steps."
            return

        # Handle case where Pressure_Calibration_Study is None (non-pressure units)
        Pressure_Calibration_Study = self.Pressure_Calibration_Study
        if Pressure_Calibration_Study is None or (isinstance(Pressure_Calibration_Study, list) and len(Pressure_Calibration_Study) == 0):
            Pressure_Calibration_Study = None
        elif isinstance(Pressure_Calibration_Study, list):
            # If it's a list with one item, extract it
            Pressure_Calibration_Study = Pressure_Calibration_Study[0] if len(Pressure_Calibration_Study) > 0 else None

        # Translate UI key names into the format build_dataframe expects
        Pressure_Calibration_Study = Translate_Pressure_Calibration_Study(Pressure_Calibration_Study)

        # Any dataframe rebuild invalidates the previous figure cache, even when the user has not
        # opened the plot window yet. This prevents stale PNGs from surviving selection changes.
        self.Invalidate_Figure_Cache()

        # Build the dataframe
        self.File_Ok, self.Units_Ok, self.Error_Msg, self.DataFrame = Build_Dataframe(Data=self.Data, Units=self.Units, Composition=self.Composition, Method=self.Method, Pressure_Calibration_Study=Pressure_Calibration_Study, Selected_Studies_For_Comparison=self.Get_Selected_Calibration_Keys())

        # Start background figure generation immediately so PNGs are ready by
        # the time the user opens the Plot Window.
        if self.File_Ok and self.Units_Ok and self.DataFrame is not None and not self.DataFrame.empty:
            # Use a fresh run token so every valid dataframe change writes to a new cache directory
            self.Start_A_New_Figure_Run()
            if self.Auto_Generate_Figures:
                self.Start_Figure_Generation()
            else:
                self.Figures_Dir = None


    # Kick off background PNG generation for the current dataframe / selections
    def Start_Figure_Generation(self):
        try:
            from Plots.Generate_Figures import (
                Get_Current_Generation_Preferences, Make_Figures_Dir,
                Ui_Module_Order, Pressure_Only_Modules,
                Start_Figure_Generation, Write_Generation_Signature,
            )

            # Extract the reference calibration key from Pressure_Calibration_Study.
            # The "reference" / pressure-calibration-study key depends on the workflow:
            #   - "use_original": the single study selected (same composition/method as the data)
            #   - "convert_composition": the LAST study in the conversion chain (the Target study,
            #     which has the different composition/method) — NOT the originally selected study.
            pcs = self.Pressure_Calibration_Study
            if isinstance(pcs, list):
                pcs = pcs[0] if pcs else None
            reference_key = None
            original_study_key = None
            dataset_composition = self.Composition
            dataset_method = self.Method
            if isinstance(pcs, dict):
                original_study_key = pcs.get("Selected Pressure Calibration Study")
                if pcs.get("Workflow Type") == "Use a Pressure Calibration Study with a Different Composition and Method":
                    reference_key = pcs.get("Target Pressure Calibration Study")
                    dataset_composition = pcs.get("Different Composition") or self.Composition
                    dataset_method = pcs.get("Different Method") or self.Method
                else:
                    reference_key = pcs.get("Selected Pressure Calibration Study")

            selected_keys = self.Get_Selected_Calibration_Keys()
            input_mode    = self.Data.get("Units", self.Units) if self.Data else self.Units

            self.Figures_Dir = Make_Figures_Dir(
                self.Composition or "",
                self.Method       or "",
                reference_key     or "",
                selected_keys,
                Run_Label=self.Run_Label,
                Run_Token=self.Figure_Run_Token,
            )

            # Generate in UI display order (summary first) and filter pressure-only
            # modules when the input is not already in GPa.
            module_names = [
                m for m in Ui_Module_Order
                if not (m in Pressure_Only_Modules and input_mode != "Pressure (GPa)")
            ]

            generation_preferences = Get_Current_Generation_Preferences(Selected_Keys=selected_keys)
            Write_Generation_Signature(self.Figures_Dir, generation_preferences["signature"])

            Start_Figure_Generation(
                Df=self.DataFrame,
                Composition=dataset_composition,
                Method=dataset_method,
                Input_Mode=input_mode,
                Reference_Key=reference_key,
                Original_Study_Key=original_study_key,
                Selected_Keys=selected_keys,
                Figures_Dir=self.Figures_Dir,
                Show_Bands=generation_preferences["show_bands"],
                Show_Error_Bars=generation_preferences["show_error_bars"],
                Show_Grid=generation_preferences["show_grid"],
                Ps_Overrides=generation_preferences["ps_overrides"],
                Theme_Overrides=generation_preferences["theme_overrides"],
                Module_Names=module_names,
            )
        except Exception as exc:
            print(f"[Select_Final_Actions] Figure pre-generation failed: {exc}")


    def Ensure_Figures_Are_Generated(self):

        # Only generate figures for a valid dataframe.
        if self.Auto_Generate_Figures and self.File_Ok and self.Units_Ok and self.DataFrame is not None and not self.DataFrame.empty:
            self.Start_Figure_Generation()


    # Enable or disable the final action buttons based on the current state of inputs and results
    def Enable_The_Final_Action_Buttons(self):

        # Check if the dataframe is valid
        DataFrame_Is_Valid = (self.File_Ok and self.Units_Ok and self.DataFrame is not None and not self.DataFrame.empty)

        # Enable buttons based on dataframe validity
        self.Plot_Results_Button.setEnabled(DataFrame_Is_Valid)
        self.Preview_Data_Button.setEnabled(DataFrame_Is_Valid)
        self.Export_Results_Button.setEnabled(DataFrame_Is_Valid)


    # When the preview button is clicked
    def When_Preview_Button_Is_Clicked(self):

        # Check if dataframe is valid
        if self.DataFrame is None or self.DataFrame.empty:
            Warning_Message(self, "Preview CSV Error", message=self.Error_Msg or "No data available to preview.")
            return
        
        # Create and show the preview dialog
        Preview_Dialog = Data_Preview_Dialog(
            self.DataFrame,
            self,
            Export_Callback=self.When_Export_Button_Is_Clicked,
        )
        Preview_Dialog.show()


    # When the plot button is clicked
    def When_Plot_Button_Is_Clicked(self):

        # Check if dataframe is valid
        if self.DataFrame is None or self.DataFrame.empty:
            Warning_Message(self, "Plot Error", message=self.Error_Msg or "No data available to plot.")
            return

        # Generate figures now if they haven't been pre-generated (e.g. All Steps layout)
        if self.Figures_Dir is None:
            self.Start_Figure_Generation()

        try:
            # Get the units from data or use stored units
            Units = self.Data.get("Units", self.Units) if self.Data else self.Units
            
            # Initialize list to track open plot windows
            if not hasattr(self, 'Open_Plot_Windows'):
                self.Open_Plot_Windows = []
            
            # Create and show the plot window (pass pre-built figures directory).
            # parent=None makes this a fully independent top-level window so it
            # stays open when EoSAlign is minimised or rearranged.
            Plot_Window_Instance = Plot_Window(
                self.DataFrame, self.Composition, self.Method, Units,
                self.Pressure_Calibration_Study, parent=None,
                Selected_Studies=self.Get_Selected_Calibration_Keys(),
                Figures_Dir=getattr(self, "Figures_Dir", None),
                Run_Label=self.Run_Label,
                Display_Run_Label=self.Display_Run_Label,
            )
            Plot_Window_Instance.show()
            self.Open_Plot_Windows.append(Plot_Window_Instance)

            # Remove window from list when closed
            Plot_Window_Instance.destroyed.connect(lambda: self.Open_Plot_Windows.remove(Plot_Window_Instance) if Plot_Window_Instance in self.Open_Plot_Windows else None)

        except Exception as e:
            Warning_Message(self, "Plot Creation Failed", error=str(e))


    # When the export button is clicked
    def When_Export_Button_Is_Clicked(self):

        # Check if dataframe is valid
        if self.DataFrame is None or self.DataFrame.empty:
            Warning_Message(self, "Export Error", message=self.Error_Msg or "No data available to export.")
            return
        
        # Open file save dialog
        Default_Filename = os.path.join(self.Get_The_Default_Export_Directory(), "comparison.csv")
        Filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", Default_Filename, "CSV Files (*.csv)")
        
        if not Filename:
            return

        try:
            # Build rename map for output pressure columns
            Rename_Map = Build_Pressure_Column_Rename_Map(self.DataFrame.columns, Calibration_Metadata)

            # Save the main dataframe (with renamed columns)
            Export_DF = self.DataFrame.rename(columns=Rename_Map)
            Export_DF.to_csv(Filename, index=False)

            # Get the units from data or use stored units
            Units = self.Data.get("Units", self.Units) if self.Data else self.Units
            # For volume methods, use the specific sub-unit (e.g. "Å³/unit cell") not just "Volume"
            Volume_Unit = self.Data.get("Volume Unit", None) if self.Data else None
            Display_Units = Volume_Unit if (Volume_Unit and "Volume" in str(Units)) else Units

            # If non-pressure units, also save solved pressures
            if Units != "Pressure (GPa)":
                Pressures_Only = Build_Solved_Pressures_Dataframe(Export_DF, Display_Units)

                if Pressures_Only is not None:
                    Base, Ext = os.path.splitext(Filename)
                    Pressures_Filename = f"{Base}_solved_pressures.csv"
                    Pressures_Only.to_csv(Pressures_Filename, index=False)

                    Success_Message(self, "CSV Save Success", filename=Filename, pressures_filename=Pressures_Filename)
                else:
                    Success_Message(self, "CSV Save Success Without Solved Pressures", filename=Filename)
            else:
                Success_Message(self, "Pressure-Units Save Success", filename=Filename)

        except Exception as e:
            Warning_Message(self, "Save File Error", error=str(e))




            
