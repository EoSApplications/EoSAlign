# Load libraries
    # Load third-party libraries
import numpy as np
import pandas as pd
    # Load local libraries
try:
    from ..Reference_Values_And_Units import Method_Units, Volume_Units
except ImportError:
    from Reference_Values_And_Units import Method_Units, Volume_Units
from .Volume_Conversion_Functions import (
    Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Unit_Cell,
    Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell,
    Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Unit_Cell,
)
from . import Parse_Calibration_Information
from .Parse_Calibration_Information import Rebuild_One_Calibration_To_Use_A_User_Inputted_Reference_Value as Make_Calibration_With_Custom_Reference
from .Error_Propagation_Functions import Propagate_Forward, Propagate_Inverse
from .Create_The_Calibration_Cache import Load_All_Calibrations, Delete_Current_Calibration_Cache
from .Create_List_Of_Functions_And_Variables import Load_List_Of_Functions_And_Variables





# Load all calibrations from the calibration cache
(Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods) = Load_All_Calibrations()
# Load the list of functions and variables
List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
# List of valid input data units
    # Added pressure to the list of method units
Valid_Units = ["Pressure (GPa)"] + list(Method_Units.values())



# Load all calibrations from the cache into memory
def Load_The_Calibrations_Into_Memory():

    # Make sure the calibration cache is up to date
    global Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods
    # If the calibration cache is not up to date rebuild it
    Result = Load_All_Calibrations(Force_Rebuild=True)
    # Update the variables with the loaded calibration data
    Calibration_List.clear()
    Calibration_List.extend(Result[0])
    Label_To_Entry.clear()
    Label_To_Entry.update(Result[1])
    Calibration_Metadata.clear()
    Calibration_Metadata.update(Result[2])
    Calibration_Functions.clear()
    Calibration_Functions.update(Result[3])
    All_Compositions.clear()
    All_Compositions.extend(Result[4])
    All_Methods.clear()
    All_Methods.extend(Result[5])



# Toggle whether user-edited / user-entered calibration data are included, then rebuild
    # Used by Settings.py to control calibration visibility
    # The toggle is session-only: the on-disk cache is invalidated afterward so the
    # next launch always starts fresh from the True/True default, the same way the
    # toggle behaved under Math/Shorthand.
def Set_Calibration_File_Settings(Include_User_Edited, Include_User_Entered):

    # Update the module-level toggles that Build_All_Calibrations() checks
    Parse_Calibration_Information.Include_User_Edited_Calibration_Files = Include_User_Edited
    Parse_Calibration_Information.Include_User_Entered_Calibration_Files = Include_User_Entered
    # Rebuild the calibrations in memory using the new settings
    Load_The_Calibrations_Into_Memory()
    # Invalidate the on-disk cache so the next launch does not inherit this toggle
    Delete_Current_Calibration_Cache()



# Find every composition that has at least one calibration using the given method
def Get_Compositions_For_Method(Method):

    # Return the sorted, de-duplicated set of compositions whose metadata matches this method
    return sorted({
        Entry.get("Composition")
        for Entry in Calibration_Metadata.values()
        if Entry.get("Method") == Method and Entry.get("Composition")
    })



# Find every method that has at least one calibration using the given composition
def Get_Methods_For_Composition(Composition):

    # Return the sorted, de-duplicated set of methods whose metadata matches this composition
    return sorted({
        Entry.get("Method")
        for Entry in Calibration_Metadata.values()
        if Entry.get("Composition") == Composition and Entry.get("Method")
    })



# Read numeric Data_Values from a file
def Read_Input_Data_From_A_File(File_Path):

    # Create a place to store the input values
    Values = []
    # Create a place to store any error message
    Error_Message = ""

    # Check if a file path was provided
    if not File_Path:
        # If no file path was provided then return an error message
        return Values, "No file Data_File_Path provided."
    # Try reading the file
    try:
        # Try reading the file as UTF-8 with BOM handling
        try:
            # Open the file with the utf-8-sig encoding
            with open(File_Path, 'r', encoding='utf-8-sig') as File:
                # Read the whole file as one string
                Content = File.read()
        # If the file is not valid utf-8-sig then fall back to latin-1
        except UnicodeDecodeError:
            # Open the file with the latin-1 encoding
            with open(File_Path, 'r', encoding='latin-1') as File:
                # Read the whole file as one string
                Content = File.read()

        # Normalize all common delimiters to spaces so split() handles everything
        for Delimiter in [',', ';', '\t', '\n']:
            # Replace the delimiter with a space
            Content = Content.replace(Delimiter, ' ')

        # Convert every whitespace-separated token into a float
        for Token in Content.split():
            # Try converting the token into a float
            try:
                Values.append(float(Token))
            # If the token cannot be converted into a float
            except ValueError:
                # Skip text headers and unit labels
                continue

        # Check that there is at least one value in the file
        if not Values:
            # If there are no values in the file then return an error message
            Error_Message = "File is empty or contains no valid numbers."
    # If there is an error reading the file then return an error message
    except Exception as Exception_Message:
        Error_Message = f"Error reading file:\n{Exception_Message}"

    # Return the values and any error message
    return Values, Error_Message



# Check whether a volume unit is already A^3/unit cell
def Check_If_The_Volume_Is_In_Angstroms_Cubed_Per_Unit_Cell(Volume_Unit):

    # Check if the volume unit is Angstroms cubed per unit cell
    return Volume_Unit == Volume_Units[0]



# Convert a list of volumes to A^3/unit cell using direct conversion helpers
def Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell(Volume_Values, Volume_Unit, Composition):
    
    # Check if the volume is Angstroms cubed per unit cell
    if Volume_Unit == Volume_Units[0]:
        return [float(Value) for Value in Volume_Values]
    if Volume_Unit == Volume_Units[1]:
        Converter = Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Unit_Cell
    elif Volume_Unit == Volume_Units[2]:
        Converter = Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell
    elif Volume_Unit == Volume_Units[3]:
        Converter = Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Unit_Cell
    else:
        raise ValueError(f"Unknown volume unit '{Volume_Unit}'. Expected one of: {Volume_Units}")

    # Return the converted volumes in Angstroms cubed per unit cell
    return [Converter(Value, Composition) for Value in Volume_Values]



# Get all information from the select pressure calibration study part of the workflow
def Translate_Pressure_Calibration_Study(Calibration_Study):

    # Check if the selected pressure calibration study is ready for the conversion
    if not isinstance(Calibration_Study, dict):
        return Calibration_Study
    # Check if the select pressure calibration study workflow is ready for the conversion
    if Calibration_Study.get("Workflow_Type"):
        return Calibration_Study
    # Get the workflow type from the user selections
    Workflow_Type_From_User_Selections = Calibration_Study.get("Workflow Type")
    # Check if the workflow is using the original composition and method
    if Workflow_Type_From_User_Selections == "Use a Pressure Calibration Study with the Original Composition and Method":
        return {"Workflow_Type": "use_original", "First_Study":   Calibration_Study.get("Selected Pressure Calibration Study"),}
    # Check if the workflow is using a different composition and method with an intermediate pressure conversion step
    elif Workflow_Type_From_User_Selections == "Use a Pressure Calibration Study with a Different Composition and Method":
        # Get the originally selected pressure calibration study
        Originally_Selected_Study = Calibration_Study.get("Originally Selected Pressure Calibration Study")
        # Get the selected pressure calibration study with a different composition and method
        Bridge_Study_Key = Calibration_Study.get("Different Pressure Calibration Study")
        # Get the different composition
        Different_Composition = Calibration_Study.get("Different Composition")
        # Get the different method
        Different_Method = Calibration_Study.get("Different Method")
        # Get the target pressure calibration study that uses the different composition and method
        Target_Study_Key = Calibration_Study.get("Target Pressure Calibration Study")
        # Check that a target pressure calibration study was selected
        if Target_Study_Key is None:
            # Find the calibration for the intermediate pressure calibration study
            Bridge_Study_Name = Calibration_Metadata.get(Bridge_Study_Key, {}).get("Study", "")
            for Calibration_Key, Calibration_Entry in Calibration_Metadata.items():
                if (Calibration_Entry.get("Study") == Bridge_Study_Name and Calibration_Entry.get("Composition") == Different_Composition and Calibration_Entry.get("Method") == Different_Method):
                    # Find the calibration for the selected pressure calibration study that uses a different composition and method
                    Target_Study_Key = Calibration_Key
                    break

        # Return all workflow information in a structured format for the conversion workflow to use
        return {"Workflow_Type": "convert_composition", "First_Study": Originally_Selected_Study, "intermediate_study_for_pressure_conversion": Bridge_Study_Key, "target_study_for_pressure_conversion": Target_Study_Key, "Target_Composition": Different_Composition, "Target_Method": Different_Method,}

    # Return none if the selections do not match any known workflow type
    return None



# Get forward and inverse functions for a calibration
def Find_The_Functions_For_A_Calibration(Calibration_Label, Custom_Reference=None):

    # Check if a custom reference was provided
    if Custom_Reference is not None and Custom_Reference.get('value') is not None:
        # Return the functions for the calibration with the custom reference
        return Make_Calibration_With_Custom_Reference(Calibration_Label, Custom_Reference, Calibration_Metadata, List_Of_Functions_And_Variables)
    
    # Return the functions for the calibration
    return Calibration_Functions[Calibration_Label]



# Get the function entry for a calibration's equation
def Find_The_Function_Entry_For_A_Calibration(Calibration_Label):

    # Find the function's registry key from the calibration data
    Function_Entry_Key = Calibration_Metadata.get(Calibration_Label, {}).get('List_Of_Functions_And_Variables_Entry')
    # Check if the function entry key exists
    if Function_Entry_Key is None:
        # If the function entry key does not exist then return None
        return None
    
    # Return the function entry from the list of functions and variables
    return List_Of_Functions_And_Variables.get(Function_Entry_Key)



# Make sure that the inverse function does not return a pressure value that is less than the reference pressure value for the calibration
    # This is for when error propagation is off
def Force_The_Inverse_Function_To_Have_The_Pressure_Greater_Than_Or_Equal_To_The_Reference_Pressure(Pressure_Value, Calibration_Label, Inverse_Function):
    
    # Check if the pressure value exists
    if pd.isna(Pressure_Value):
        return np.nan
    # Get the reference pressure
    P0 = Calibration_Metadata.get(Calibration_Label, {}).get('P0', 0) or 0
    # Check if the pressure value is less than the reference pressure
    if Pressure_Value < P0:
        # If so return a nan pressure value
        return np.nan
    try:
        # Find the pressure value from the inverse function
        Result = Inverse_Function(Pressure_Value)
        # Check if the result exists
        if Result is not None:
            # Return the result
            return Result
        else:
            return np.nan
    except Exception:
        return np.nan



# Build the dataframe that will hold all input and output values baised on the user selections
def Build_Dataframe(Data, Units, Composition, Method, Pressure_Calibration_Study, Selected_Studies_For_Comparison):

    # Check if the user selected any studies for comparison
    if Selected_Studies_For_Comparison is None:
        # Make a place to store the selected studies for comparison
        Selected_Studies_For_Comparison = []
    # Get the error propagation values
    Error_Propagation = Data.get("Error Propagation Enabled", Data.get("Error_Propagation", False))
    # Get the uncertainty values
    Uncertainty_Data = Data.get("Uncertainty Data", Data.get("Uncertainty_Data", {}))
    # Get the custom reference information
    Custom_Reference = Data.get("Custom_Reference", None)
    # Make a place to store the select pressure calibration information
    First_Study = None
    Intermediate_Study_For_Conversion = None
    Target_Study_For_Conversion = None
    Original_Composition = Composition
    Original_Method = Method
    Workflow_Type = None
    Target_Composition = None
    Target_Method = None
    # Get the select pressure calibration information
    Calibration_Selection = Pressure_Calibration_Study
    if Calibration_Selection is None:
        First_Study = None
    elif isinstance(Calibration_Selection, list):
        First_Study = Calibration_Selection[0] if Calibration_Selection else None
    elif isinstance(Calibration_Selection, dict):
        Workflow_Type = Calibration_Selection.get("Workflow_Type")
        First_Study = Calibration_Selection.get("First_Study")
        Intermediate_Study_For_Conversion = Calibration_Selection.get("intermediate_study_for_pressure_conversion")
        Target_Study_For_Conversion = Calibration_Selection.get("target_study_for_pressure_conversion")
        Target_Composition = Calibration_Selection.get("Target_Composition")
        Target_Method = Calibration_Selection.get("Target_Method")
    else:
        First_Study = Calibration_Selection

    # Read the input data from the file and check for errors
    File_OK = True
    Units_OK = True
    Error_Message = ""
    Data_File_Path = Data.get("File_Path", "")
    Data_Values, Read_Error = Read_Input_Data_From_A_File(Data_File_Path)
    if Read_Error:
        File_OK   = False
        Error_Message = Read_Error
    # Read the input uncertainty data from the file and check for errors
    Uncertainty_Values = []
    if Error_Propagation and Uncertainty_Data.get("Error Propagation Enabled", Uncertainty_Data.get("enabled", False)):
        Uncertainty_File_Path = Uncertainty_Data.get("Error Propagation Path", Uncertainty_Data.get("File_Path", ""))
        if Uncertainty_File_Path:
            Uncertainty_Values, Uncertainty_Read_Error = Read_Input_Data_From_A_File(Uncertainty_File_Path)
            if Uncertainty_Read_Error:
                File_OK   = False
                Error_Message = f"Uncertainty file error: {Uncertainty_Read_Error}"
            elif len(Uncertainty_Values) != len(Data_Values):
                File_OK = False
                Error_Message = (f"Uncertainty data size ({len(Uncertainty_Values)}) does not match input data size ({len(Data_Values)}). They must be equal.")
        else:
            Uncertainty_Values = [0.0] * len(Data_Values)
    else:
        Uncertainty_Values = [0.0] * len(Data_Values)

    # Check the input data units
    Input_Units = Data.get("Units", Units)
    Volume_Unit = Data.get("Volume Unit", None)
    if "Volume" in str(Input_Units) and Volume_Unit is not None and Volume_Unit not in Volume_Units:
        Units_OK = False
        Error_Message = f"Volume unit is invalid. Expected one of: {Volume_Units}"
    if Input_Units not in Valid_Units:
        Units_OK  = False
        Error_Message = "Units are missing or invalid."
    # Check if the volume units need to be converted
    Original_Values = Data_Values
    Original_Uncertainty_Values = Uncertainty_Values
    Needs_Conversion = (File_OK and "Volume" in str(Input_Units) and Volume_Unit is not None and not Check_If_The_Volume_Is_In_Angstroms_Cubed_Per_Unit_Cell(Volume_Unit))
    if Needs_Conversion:
        try:
            Data_Values = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell(Data_Values, Volume_Unit, Composition)
            if Error_Propagation and any(Uncertainty_Value != 0 for Uncertainty_Value in Uncertainty_Values):
                Uncertainty_Values = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell(Uncertainty_Values, Volume_Unit, Composition)
            if Custom_Reference is not None and Custom_Reference.get('type') == 'V0':
                Custom_V0 = Custom_Reference.get('value')
                Custom_V0_Uncertainty = Custom_Reference.get('uncertainty', 0)
                if Custom_V0 is not None:
                    Converted_V0 = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell([Custom_V0], Volume_Unit, Composition)
                    Custom_Reference = dict(Custom_Reference)
                    Custom_Reference['value'] = Converted_V0[0]
                    if Custom_V0_Uncertainty:
                        Converted_V0_Uncertainty = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell([Custom_V0_Uncertainty], Volume_Unit, Composition)
                        Custom_Reference['uncertainty'] = Converted_V0_Uncertainty[0]
        except ValueError as Exception_Message:
            File_OK = False
            Error_Message = f"Volume conversion error: {Exception_Message}"

    

    # Start filling the dataframe with the conversions
    Dataframe_Output = None
    if File_OK and Units_OK:


        # Path 1:
            # Input units are not pressure
        if Input_Units != "Pressure (GPa)":
            # Store both the original and converted values as columns in the dataframe
            if Needs_Conversion:
                Unit_Label = (Volume_Unit.replace("(", "").replace(")", "").replace(" ", "_").replace("/", "_per_"))
                Measured_Column = 'Volume_A3_UnitCell'
                Data_Dictionary = {f'Input_{Unit_Label}':Original_Values, Measured_Column:Data_Values}
                # Add the uncertainty values to the dataframe if error propagation is on
                if Error_Propagation:
                    Data_Dictionary[f'Input_{Unit_Label}_Unc'] = Original_Uncertainty_Values
                    Data_Dictionary[f'{Measured_Column}_Unc'] = Uncertainty_Values
            else:
                if "Volume" in str(Input_Units) and Volume_Unit is not None:
                    Measured_Column = f'Measured_{Volume_Unit}_Input'
                else:
                    Measured_Column = f'Measured_{Input_Units}_Input'
                Data_Dictionary = {Measured_Column: Data_Values}
                if Error_Propagation:
                    Data_Dictionary[f'{Measured_Column}_Unc'] = Uncertainty_Values
            for Calibration_Name in Selected_Studies_For_Comparison:
                if Calibration_Name not in Calibration_Functions:
                    continue
                Forward_Function, _ = Find_The_Functions_For_A_Calibration(Calibration_Name, Custom_Reference)
                if Error_Propagation:
                    Metadata_Entry = Calibration_Metadata.get(Calibration_Name)
                    Registry_Entry = Find_The_Function_Entry_For_A_Calibration(Calibration_Name)
                    Pressures, Pressure_Uncertainties = [], []
                    for Value, Value_Uncertainty in zip(Data_Values, Uncertainty_Values):
                        Pressure_Value, Pressure_Uncertainty = Propagate_Forward(Value, Value_Uncertainty, Forward_Function, Metadata=Metadata_Entry, Registry_Entry=Registry_Entry, Custom_Reference=Custom_Reference)
                        Pressures.append(Pressure_Value)
                        Pressure_Uncertainties.append(Pressure_Uncertainty)
                    Data_Dictionary[f'Pressure_{Calibration_Name}'] = Pressures
                    Data_Dictionary[f'P_Unc_{Calibration_Name}'] = Pressure_Uncertainties
                else:
                    Data_Dictionary[f'Pressure_{Calibration_Name}'] = [Forward_Function(Value) for Value in Data_Values]

            # Store all the conversions in the dataframe
            Dataframe_Output = pd.DataFrame(Data_Dictionary)


        # Path 2:
            # Input units are pressure
        else:

            # Path 2a:
                # Input pressure is converted to volume using the first study
                    # Then converted back to pressure for the selected studies for comparison
            if Workflow_Type == "use_original":
                if First_Study and First_Study in Calibration_Functions:
                    Forward_Function_First, Inverse_Function_First = Calibration_Functions[First_Study]
                    Input_Column = "Input_Pressure_(GPa)"
                    Data_Dictionary = {Input_Column: Data_Values}
                    if Error_Propagation:
                        Data_Dictionary[f'{Input_Column}_Unc'] = Uncertainty_Values
                    Study_Method = Calibration_Metadata.get(First_Study, {}).get("Method", "XRD")
                    Observable_Unit = Method_Units.get(Study_Method, "Volume")
                    Volume_Column = f"{Observable_Unit}_From_{First_Study}"
                    if Error_Propagation:
                        Metadata_First = Calibration_Metadata.get(First_Study)
                        Registry_Entry_First = Find_The_Function_Entry_For_A_Calibration(First_Study)
                        Volumes, Volume_Uncertainties = [], []
                        for Value, Value_Uncertainty in zip(Data_Values, Uncertainty_Values):
                            Volume_Value, Volume_Uncertainty = Propagate_Inverse(Value, Value_Uncertainty, Inverse_Function_First, Metadata=Metadata_First, Registry_Entry=Registry_Entry_First)
                            Volumes.append(Volume_Value)
                            Volume_Uncertainties.append(Volume_Uncertainty)
                        Data_Dictionary[Volume_Column] = Volumes
                        Data_Dictionary[f'V_Unc_{First_Study}'] = Volume_Uncertainties
                    else:
                        Volumes = [Force_The_Inverse_Function_To_Have_The_Pressure_Greater_Than_Or_Equal_To_The_Reference_Pressure(Value, First_Study, Inverse_Function_First) for Value in Data_Values]
                        Data_Dictionary[Volume_Column] = Volumes
                        Volume_Uncertainties = [0.0] * len(Data_Values)
                    for Calibration_Name in Selected_Studies_For_Comparison:
                        if Calibration_Name not in Calibration_Functions:
                            continue
                        Forward_Function, _ = Find_The_Functions_For_A_Calibration(Calibration_Name, Custom_Reference)
                        if Error_Propagation:
                            Metadata_Entry = Calibration_Metadata.get(Calibration_Name)
                            Registry_Entry = Find_The_Function_Entry_For_A_Calibration(Calibration_Name)
                            Pressures, P_Uncertainties = [], []
                            for Volume_Value, Volume_Uncertainty in zip(Volumes, Volume_Uncertainties):
                                if not pd.isna(Volume_Value):
                                    Pressure_Value, Pressure_Uncertainty = Propagate_Forward(Volume_Value, Volume_Uncertainty, Forward_Function, Metadata=Metadata_Entry, Registry_Entry=Registry_Entry, Custom_Reference=Custom_Reference)
                                else:
                                    Pressure_Value, Pressure_Uncertainty = np.nan, np.nan
                                Pressures.append(Pressure_Value)
                                P_Uncertainties.append(Pressure_Uncertainty)
                            Data_Dictionary[f'Pressure_{Calibration_Name}'] = Pressures
                            Data_Dictionary[f'P_Unc_{Calibration_Name}'] = P_Uncertainties
                        else:
                            Data_Dictionary[f'Pressure_{Calibration_Name}'] = [Forward_Function(Volume_Value) if not pd.isna(Volume_Value) else np.nan for Volume_Value in Volumes]
                    Dataframe_Output = pd.DataFrame(Data_Dictionary)
                else:
                    Input_Column = "Input_Pressure_(GPa)"
                    Data_Dictionary = {Input_Column: Data_Values}
                    if Error_Propagation:
                        Data_Dictionary[f'{Input_Column}_Unc'] = Uncertainty_Values
                    Dataframe_Output = pd.DataFrame(Data_Dictionary)

            # Path 2b:
                # Input pressure is converted to volume using the first study
                    # Then converted back to pressure for an intermediate study with a different composition
                        # Then converted to volume for a target study with the different composition
                            # Then converted back to pressure for the selected studies for comparison
            elif Workflow_Type == "convert_composition":
                All_Studies_Are_Present = (First_Study and First_Study in Calibration_Functions and Intermediate_Study_For_Conversion and Intermediate_Study_For_Conversion in Calibration_Functions and Target_Study_For_Conversion and Target_Study_For_Conversion in Calibration_Functions)
                if All_Studies_Are_Present:
                    _, Inverse_Function_First = Calibration_Functions[First_Study]
                    Forward_Function_Intermediate, _ = Calibration_Functions[Intermediate_Study_For_Conversion]
                    _, Inverse_Function_Target = Calibration_Functions[Target_Study_For_Conversion]
                    Input_Column = "Input_Pressure_(GPa)"
                    Data_Dictionary = {Input_Column: Data_Values}
                    if Error_Propagation:
                        Data_Dictionary[f'{Input_Column}_Unc'] = Uncertainty_Values

                    # Step 2: P -> V1 (first study)
                    Original_Observable_Unit = Method_Units.get(Original_Method, "Volume")
                    V1_Column = (f"{Original_Observable_Unit}_From_{First_Study}_({Original_Composition}_{Original_Method})")
                    if Error_Propagation:
                        Metadata_1 = Calibration_Metadata.get(First_Study)
                        Registry_Entry_1 = Find_The_Function_Entry_For_A_Calibration(First_Study)
                        V1_Values, V1_Uncertainties = [], []
                        for Value, Value_Uncertainty in zip(Data_Values, Uncertainty_Values):
                            Volume_Value, Volume_Uncertainty = Propagate_Inverse(Value, Value_Uncertainty, Inverse_Function_First, Metadata=Metadata_1, Registry_Entry=Registry_Entry_1)
                            V1_Values.append(Volume_Value)
                            V1_Uncertainties.append(Volume_Uncertainty)
                        Data_Dictionary[V1_Column] = V1_Values
                        Data_Dictionary[f'V_Unc_{First_Study}'] = V1_Uncertainties
                    else:
                        V1_Values = [Force_The_Inverse_Function_To_Have_The_Pressure_Greater_Than_Or_Equal_To_The_Reference_Pressure(Value, First_Study, Inverse_Function_First) for Value in Data_Values]
                        Data_Dictionary[V1_Column] = V1_Values
                        V1_Uncertainties  = [0.0] * len(Data_Values)

                    # Step 3: V1 -> P2 (intermediate study)
                    P2_Column = (f"Pressure_From_{Intermediate_Study_For_Conversion}_({Original_Composition}_{Original_Method})")
                    if Error_Propagation:
                        Metadata_2 = Calibration_Metadata.get(Intermediate_Study_For_Conversion)
                        Registry_Entry_2 = Find_The_Function_Entry_For_A_Calibration(Intermediate_Study_For_Conversion)
                        P2_Values, P2_Uncertainties = [], []
                        for Volume_Value, Volume_Uncertainty in zip(V1_Values, V1_Uncertainties):
                            if not pd.isna(Volume_Value):
                                Pressure_Value, Pressure_Uncertainty = Propagate_Forward(Volume_Value, Volume_Uncertainty, Forward_Function_Intermediate, Metadata=Metadata_2, Registry_Entry=Registry_Entry_2)
                            else:
                                Pressure_Value, Pressure_Uncertainty = np.nan, np.nan
                            P2_Values.append(Pressure_Value)
                            P2_Uncertainties.append(Pressure_Uncertainty)
                        Data_Dictionary[P2_Column] = P2_Values
                        Data_Dictionary[f'P_Unc_{Intermediate_Study_For_Conversion}'] = P2_Uncertainties
                    else:
                        P2_Values = [Forward_Function_Intermediate(Volume_Value) if not pd.isna(Volume_Value) else np.nan for Volume_Value in V1_Values]
                        Data_Dictionary[P2_Column] = P2_Values
                        P2_Uncertainties = [0.0] * len(Data_Values)

                    # Step 4: Assume P2 = P_target (equal pressure assumption)
                    Assumed_Pressure_Column = (f"Assumed_Equal_Pressure_{Intermediate_Study_For_Conversion}_=_{Target_Study_For_Conversion}")
                    Data_Dictionary[Assumed_Pressure_Column] = P2_Values
                    if Error_Propagation:
                        Data_Dictionary['P_Unc_Assumed'] = P2_Uncertainties

                    # Alias the assumed-equal pressure under the target study's standard
                    # "Pressure_<key>" / "P_Unc_<key>" column names. The target study is the
                    # LAST pressure calibration study in this conversion chain — by the equal-
                    # pressure assumption, its own pressure reading IS this assumed value. This
                    # lets downstream plotting code (which looks up "Pressure_<Reference_Key>")
                    # find the target study's pressure the same way it would for a single-study
                    # (same composition/method) pressure calibration.
                    Data_Dictionary[f'Pressure_{Target_Study_For_Conversion}'] = P2_Values
                    if Error_Propagation:
                        Data_Dictionary[f'P_Unc_{Target_Study_For_Conversion}'] = P2_Uncertainties

                    # Step 5: P2 -> V2 (target study)
                    Target_Observable_Unit = Method_Units.get(Target_Method, "Volume")
                    V2_Column = (f"{Target_Observable_Unit}_From_{Target_Study_For_Conversion}_({Target_Composition}_{Target_Method})")
                    if Error_Propagation:
                        Metadata_3 = Calibration_Metadata.get(Target_Study_For_Conversion)
                        Registry_Entry_3 = Find_The_Function_Entry_For_A_Calibration(Target_Study_For_Conversion)
                        V2_Values, V2_Uncertainties = [], []
                        for Pressure_Value, Pressure_Uncertainty in zip(P2_Values, P2_Uncertainties):
                            if not pd.isna(Pressure_Value):
                                Volume_Value, Volume_Uncertainty = Propagate_Inverse(Pressure_Value, Pressure_Uncertainty, Inverse_Function_Target, Metadata=Metadata_3, Registry_Entry=Registry_Entry_3)
                            else:
                                Volume_Value, Volume_Uncertainty = np.nan, np.nan
                            V2_Values.append(Volume_Value)
                            V2_Uncertainties.append(Volume_Uncertainty)
                        Data_Dictionary[V2_Column] = V2_Values
                        Data_Dictionary[f'V_Unc_{Target_Study_For_Conversion}'] = V2_Uncertainties
                    else:
                        V2_Values = [Force_The_Inverse_Function_To_Have_The_Pressure_Greater_Than_Or_Equal_To_The_Reference_Pressure(Pressure_Value, Target_Study_For_Conversion, Inverse_Function_Target)
                               for Pressure_Value in P2_Values]
                        Data_Dictionary[V2_Column] = V2_Values
                        V2_Uncertainties = [0.0] * len(Data_Values)

                    # Step 6: V2 -> P (selected comparison studies)
                    for Calibration_Name in Selected_Studies_For_Comparison:
                        if Calibration_Name not in Calibration_Functions:
                            continue
                        Forward_Function, _ = Find_The_Functions_For_A_Calibration(Calibration_Name, Custom_Reference)
                        if Error_Propagation:
                            Metadata_Entry = Calibration_Metadata.get(Calibration_Name)
                            Registry_Entry = Find_The_Function_Entry_For_A_Calibration(Calibration_Name)
                            Pressures, P_Uncertainties = [], []
                            for Volume_Value, Volume_Uncertainty in zip(V2_Values, V2_Uncertainties):
                                if not pd.isna(Volume_Value):
                                    Pressure_Value, Pressure_Uncertainty = Propagate_Forward(Volume_Value, Volume_Uncertainty, Forward_Function, Metadata=Metadata_Entry, Registry_Entry=Registry_Entry, Custom_Reference=Custom_Reference)
                                else:
                                    Pressure_Value, Pressure_Uncertainty = np.nan, np.nan
                                Pressures.append(Pressure_Value)
                                P_Uncertainties.append(Pressure_Uncertainty)
                            Data_Dictionary[f'Pressure_{Calibration_Name}'] = Pressures
                            Data_Dictionary[f'P_Unc_{Calibration_Name}'] = P_Uncertainties
                        else:
                            Data_Dictionary[f'Pressure_{Calibration_Name}'] = [Forward_Function(Volume_Value) if not pd.isna(Volume_Value) else np.nan for Volume_Value in V2_Values]
                    Dataframe_Output = pd.DataFrame(Data_Dictionary)
                else:
                    Input_Column = "Input_Pressure_(GPa)"
                    Data_Dictionary = {Input_Column: Data_Values}
                    if Error_Propagation:
                        Data_Dictionary[f'{Input_Column}_Unc'] = Uncertainty_Values
                    Dataframe_Output = pd.DataFrame(Data_Dictionary)
            else:
                Input_Column = "Input_Pressure_(GPa)"
                Data_Dictionary = {Input_Column: Data_Values}
                if Error_Propagation:
                    Data_Dictionary[f'{Input_Column}_Unc'] = Uncertainty_Values
                Dataframe_Output = pd.DataFrame(Data_Dictionary)

    return File_OK, Units_OK, Error_Message, Dataframe_Output
