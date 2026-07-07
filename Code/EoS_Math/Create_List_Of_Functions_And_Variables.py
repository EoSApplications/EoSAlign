# Load libraries
    # Load standard libraries
import os
import inspect
import importlib.util
import datetime
    # Load functions grouped by their file name
from . import XRD_Functions
from . import Luminescence_Functions
from . import Raman_Functions
from Reference_Values_And_Units import *





# Find the path to this file
Create_List_Of_Functions_And_Variables_File_Path = os.path.dirname(os.path.abspath(__file__))
# Define the name of the file that will store the list of functions and variables
List_Of_Functions_And_Variables_File_Name = 'List_Of_Functions_And_Variables.py'
# Set the path of the list of functions and variables file
List_Of_Functions_And_Variables_File = os.path.join(Create_List_Of_Functions_And_Variables_File_Path, List_Of_Functions_And_Variables_File_Name)

# Make a list of all files that contain Equation of State functions and calibration functions
Function_Files = [
    os.path.join(Create_List_Of_Functions_And_Variables_File_Path, 'XRD_Functions.py'),
    os.path.join(Create_List_Of_Functions_And_Variables_File_Path, 'Luminescence_Functions.py'),
    os.path.join(Create_List_Of_Functions_And_Variables_File_Path, 'Raman_Functions.py'),
]
# List a module (file) name for each of the files that contain Equation of State functions and calibration functions
Function_Modules = {
    'XRD_Functions': XRD_Functions,
    'Luminescence_Functions': Luminescence_Functions,
    'Raman_Functions': Raman_Functions,
}



# Check if the current lit of functions and variables file is newer than all the function files
def Check_If_The_Current_List_Of_Functions_And_Variables_Is_Valid():

    # Check if the list of functions and variables file exists
    if not os.path.exists(List_Of_Functions_And_Variables_File):
        # If the file does not exist it needs to be built
        return False
    try:
        # Check when the list of functions and variables file was last modified
        List_Of_Functions_And_Variables_File_Mtime = os.path.getmtime(List_Of_Functions_And_Variables_File)
        # Loop through each function file
        for File in Function_Files:
            # Check if the function file exists
            if os.path.exists(File):
                # Check if the function file was modified more recently than the list of functions and variables file
                if os.path.getmtime(File) > List_Of_Functions_And_Variables_File_Mtime:
                    # If any function file is newer than the list of functions and variables file then the list of functions and variables file is outdated and needs to be rebuilt
                    return False
        # If the list of functions and variables file is newer than all the function files then it is valid and does not need to be rebuilt
        return True
    except OSError:
        return False




# Find all functions in the function files
def Find_All_Calculate_Functions_Within_The_Function_Files(Function_Name):

    # Look for all functions with '__Calculate_' in the name
    Indicator = '__Calculate_'
    # Check if the function name contains the indicator
    if Indicator in Function_Name:
        # Return the part of the function name before the indicator as the group name
        return Function_Name[:Function_Name.index(Indicator)]
    else:
        # If the function name does not contain the indicator then it is not a function that we are looking for
        return None



# Find all functions that calculate pressure
    # These are the forward functions that take a measured value and return pressure
def Find_All_Forward_Functions_That_Calculate_Pressure(Function_Name):

    # Look for all functions with '__Calculate_' in the name
    Indicator = '__Calculate_'
    # Look for all functions with '__Calculate_Pressure' in the name
    Forward_Indicator = '__Calculate_Pressure'
    # Check if the function name contains the indicator
    if Indicator in Function_Name:
        # Check if the function name contains the forward indicator
        if Forward_Indicator in Function_Name:
            # If the function name contains both the indicator and the forward indicator then it is a forward function that calculates pressure
            return True
        else:
            # If the function name contains the indicator but does not contain the forward indicator then it is not a forward function that calculates pressure
            return False
    else:
        # If the function name does not contain the indicator then it is not a function that we are looking for
        return False



# Find all functions that calculate a measured value
    # These are the inverse functions that take pressure and return a measured value
def Find_All_Inverse_Functions_That_Calculate_A_Measured_Value(Function_Name):

    # Look for all functions with '__Calculate_' in the name
    Indicator = '__Calculate_'
    # Look for all functions with '_Calculate_Pressure' in the name
    Forward_Indicator = '__Calculate_Pressure'
    # Check if the function name contains the indicator
    if Indicator in Function_Name:
        # Check if the function name does not contain the forward indicator
        if Forward_Indicator not in Function_Name:
            # If the function name contains the indicator but does not contain the forward indicator then it is an inverse function that calculates a measured value
            return True
        else:
            # If the function name contains both the indicator and the forward indicator then it is not an inverse function that calculates a measured value
            return False
    else:
        # If the function name does not contain the indicator then it is not a function that we are looking for
        return False



# Get variable information from the calibration files and the required variables from the functions and put the variables in the correct order to be used for the functions
def Get_Variable_Information_From_The_Calibration_Files_And_The_Functions(Function):

    # Create lists to store the variable information
    Calibration_File_Variable_Information = []
    Required_Variables_For_The_Functions = []
    Variable_Order_For_The_Functions = []

    # Find all the variables used in the functions
    for Variable_Name, Variable in inspect.signature(Function).parameters.items():
        # Check if the variable is an input variable
        if Variable_Name in Input_Variable_Names:
            # Skip the input variables
            continue
        # Check if the variable is a constant variable
        if Variable_Name in Constant_Variables:
            # Add the variable and the variable value to the variable order list for the functions
            Variable_Order_For_The_Functions.append(['Constant', Constant_Variables[Variable_Name]])
            continue
        # Find the corresponding YAML key for the variable name
        Calibration_Key = Function_Variable_Names_And_Calibration_Key_Names.get(Variable_Name, Variable_Name)
        # Add the YAML key to the variable information list and the variable order list for the functions
        Calibration_File_Variable_Information.append(Calibration_Key)
        # Add the YAML key to the variable order list for the functions
        Variable_Order_For_The_Functions.append(['calibration', Calibration_Key])
        # Check if the variable has a default value
        if Variable.default is inspect.Parameter.empty:
            # If the variable does not have a default value then it is a required variable for the function
            Required_Variables_For_The_Functions.append(Calibration_Key)

    return Calibration_File_Variable_Information, Required_Variables_For_The_Functions, Variable_Order_For_The_Functions



# Create the list of functions and variables by scanning the EoS modules
def Create_List_Of_Functions_And_Variables_From_Function_Files(*Modules):

    # Create lists to store the function and variable information
    List_Of_Functions_And_Variables = {}
    Unmapped_Variabled = set()

    # Find all the functions in the function files (modules)
    for Module in Modules:
        # Get the module name
        Module_Short_Name = Module.__name__.split('.')[-1]

        # Find all function names in the function file (module)
        for Function_Name, Function in inspect.getmembers(Module, inspect.isfunction):
            # Make sure the function is defined within the specific file (module)
            if inspect.getmodule(Function) is not Module:
                continue
            # Make sure the function is a forward or inverse function
            if not Find_All_Forward_Functions_That_Calculate_Pressure(Function_Name) and not Find_All_Inverse_Functions_That_Calculate_A_Measured_Value(Function_Name):
                continue

            # Find the equation name
            Equation_Name = Find_All_Calculate_Functions_Within_The_Function_Files(Function_Name)
            if Equation_Name is None:
                continue

            # Make sure the equation name is in the list of functions and variables
            if Equation_Name not in List_Of_Functions_And_Variables:
                List_Of_Functions_And_Variables[Equation_Name] = {}
            # Get the variable information for the equation
            Calibration_File_Variable_Information, Required_Variables_For_The_Functions, Variable_Order_For_The_Functions = Get_Variable_Information_From_The_Calibration_Files_And_The_Functions(Function)

            # Check if there are any variables that are required by a function but not included in the calibration key names
            for Variable_Name in inspect.signature(Function).parameters:
                if (Variable_Name not in Input_Variable_Names and Variable_Name not in Constant_Variables and Variable_Name not in Function_Variable_Names_And_Calibration_Key_Names):
                    Unmapped_Variabled.add(Variable_Name)

            # Store the function/equation information and the corresponding variable information
                # State the direction of the function (forward or inverse)
                    # Forward functions calculate pressure from a measured value
                    # Inverse functions calculate a measured value from pressure
            Direction = 'Forward' if Find_All_Forward_Functions_That_Calculate_Pressure(Function_Name) else 'Inverse'
                # Store the entire function name
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Function'] = Function
                # Store which file (module) the function is in
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Module'] = Module_Short_Name
                # Store the equation name
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Function_Name'] = Function_Name
                # Store the variable information that will come from the calibration files
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Calibration_File_Variable_Information'] = Calibration_File_Variable_Information
                # Store the required varaibles that the function needs in order to run
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Required_Variables_For_The_Functions'] = Required_Variables_For_The_Functions
                # Store the variable order information for the function
            List_Of_Functions_And_Variables[Equation_Name][f'{Direction}_Variable_Order_For_The_Functions'] = Variable_Order_For_The_Functions

    # Check that all equations have both a forward and inverse function
    Incomplete = [
        Equation for Equation, Entry in List_Of_Functions_And_Variables.items()
        if 'Forward_Function' not in Entry or 'Inverse_Function' not in Entry
    ]
    # If an equation is missing either a forward or inverse function send a warning
    if Incomplete:
        print(f"Warning: missing forward or inverse function")
        print(f"\t{Incomplete}")

    # If a variables is missing a calibration file key name send a warning
    if Unmapped_Variabled:
        print(f"Warning: equation varaible not in the calibration file key names")
        print(f"\t{Unmapped_Variabled}")

    # Return the function and variable information
    return List_Of_Functions_And_Variables



# Format variables in order so they can later be passed into functions
    # This is so the variable information can be saved to a file
def Format_Variable_Order_For_The_Functions(Variable_Order_For_The_Functions):

    # Create a place to store the formatted variable information
    Formatted_Variable_Information = []

    # For each variable in the order list
    for Variable_Type, Variable_Value in Variable_Order_For_The_Functions:
        # Reformat the variable type and variable value pair into a string
        Formatted_Variable = f'[{Variable_Type!r}, {Variable_Value!r}]'
        # Add the formatted variable information to the list
        Formatted_Variable_Information.append(Formatted_Variable)

    # Add all the variables together
    Variables_String = ', '.join(Formatted_Variable_Information)

    # Add brackets around the entire string to make it look like a list of lists
    Variables_String = f'[{Variables_String}]'

    return Variables_String



# Format a list of strings so they can be written and read from python files
    # This is so the variable information can be saved to a file
def Format_List_Of_Strings(List):

    # Create a place to store the formatted strings
    Formatted_Variable_Strings = []

    # For each variable in the list
    for Variable in List:
        # Use repr() to convert the string into a valid Python string
        Formatted_Variable_String = repr(Variable)
        # Add the formatted variable string to the list
        Formatted_Variable_Strings.append(Formatted_Variable_String)

    # Add all the formatted variable strings together with commas in between
    Variable_String = ', '.join(Formatted_Variable_Strings)

    # Add brackets around the entire string to make it look like a list
    Variables_List = '[' + Variable_String + ']'

    return Variables_List



# Save the list of functions and variables to a .py file
def Save_List_Of_Functions_And_Variables_To_File(List_Of_Functions_And_Variables, File_Path=None):

    # Check if a file path was inputed
    if File_Path is None:
        # Use the default file path if one is not provided
        File_Path = List_Of_Functions_And_Variables_File

    # Group the equations/function by which file (module) they are stored in
    Organize_By_Function_File = {}
    for Equation_Name, Entry in sorted(List_Of_Functions_And_Variables.items()):
        Module = Entry.get('Forward_Module') or Entry.get('Inverse_Module', 'Unknown')
        Organize_By_Function_File.setdefault(Module, []).append((Equation_Name, Entry))

    # Create a header that lists the files and when they were last modified
    Function_File_Mtimes = []
    # For each function file
    for Path in Function_Files:
        # Get the name of the file
        Name = os.path.basename(Path)
        try:
            # Get the last modified time of the file
            Mtime = datetime.datetime.fromtimestamp(os.path.getmtime(Path))
            Function_File_Mtimes.append(f'# {Name:<30} - (modified: {Mtime:%m/%d/%Y  %H:%M:%S})')
        except OSError:
            Function_File_Mtimes.append(f'# {Name:<30} - (not found)')
    # Add some information about the file creation
    File_Content = []
    File_Content.append(f"# Auto-generated by Create_List_Of_Functions_And_Variables.py")
    File_Content.append(f"# Do not edit manually — run Update_List_Of_Functions_And_Variables() to rebuild.")
    File_Content.append(f"# Generated on: {datetime.datetime.now():%m/%d/%Y  %H:%M:%S}")
    File_Content.append(f"")
    File_Content.append(f"# Source files scanned:")
    File_Content.append(f"{Function_File_Mtimes}")
    File_Content.append(f"")
    File_Content.append(f"List_Of_Functions_And_Variables_DATA = {{")

    # List the order in which the function files should be listed
    Module_Order = ['XRD_Functions', 'Luminescence_Functions', 'Raman_Functions']
    All_Modules  = Module_Order + [m for m in Organize_By_Function_File if m not in Module_Order]

    for Module_Name in All_Modules:
        Entries = Organize_By_Function_File.get(Module_Name)
        if not Entries:
            continue
        # Add a section header for the file (module) that the functions are stored in
        File_Content.append(f"")
        File_Content.append(f'# ──── {Module_Name} ──── ')
        File_Content.append(f"")
        # Add each equation/function that is stored in the file (module)
        for Equation_Name, Entry in Entries:
            File_Content.append(f'\t{Equation_Name!r}: {{')
            # Add the variable information for the forward and inverse functions
            for Direction in ('Forward', 'Inverse'):
                Module = Entry.get(f'{Direction}_Module', '')
                Function = Entry.get(f'{Direction}_Function_Name', '')
                Calibration_File_Variable_Information = Entry.get(f'{Direction}_Calibration_File_Variable_Information', [])
                Required_Variables_For_The_Function = Entry.get(f'{Direction}_Required_Variables_For_The_Functions', [])
                Variable_Order_For_The_Functions = Entry.get(f'{Direction}_Variable_Order_For_The_Functions', [])
                File_Content.append(f"\t\t'{Direction}_Module': {Module!r},")
                File_Content.append(f"\t\t'{Direction}_Function_Name': {Function!r},")
                File_Content.append(f"\t\t'{Direction}_Calibration_File_Variable_Information': {Format_List_Of_Strings(Calibration_File_Variable_Information)},")
                File_Content.append(f"\t\t'{Direction}_Required_Variables_For_The_Functions': {Format_List_Of_Strings(Required_Variables_For_The_Function)},")
                File_Content.append(f"\t\t'{Direction}_Variable_Order_For_The_Functions': {Format_Variable_Order_For_The_Functions(Variable_Order_For_The_Functions)},")
            File_Content.append('\t},')
    File_Content.append('')
    File_Content.append('}')
    File_Content.append('')

    # Save the file content to a temperary file
    Temperary_File_Path = File_Path + '.tmp'
    with open(Temperary_File_Path, 'w', encoding='utf-8') as Temperary_File:
        # Write the file content to the temperary file
        Temperary_File.write('\n'.join(File_Content))
    # Move the temperary file to the actual file path
    os.replace(Temperary_File_Path, File_Path)



# Load the list of functions and variables from the file and resolve function names back to actual function objects using Function_Modules
def Load_List_Of_Functions_And_Variables_From_File(File_Path=None):

    # Check if a file path was inputed
    if File_Path is None:
        # Use the default file path if one is not provided
        File_Path = List_Of_Functions_And_Variables_File

    # Load the .py file as a module without adding it to sys.modules
    File_Information = importlib.util.spec_from_file_location('List_Of_Functions_And_Variables', File_Path)
    Function = importlib.util.module_from_spec(File_Information)
    File_Information.loader.exec_module(Function)
    Information_From_Saved_File = Function.List_Of_Functions_And_Variables_DATA

    # Make a place to store the list of functions and variables with the function names resolved to actual function objects
    List_Of_Functions_And_Variables = {}

    # Find each equation/function from the file
    for Equation_Name, Entry in Information_From_Saved_File.items():
        List_Of_Functions_And_Variables[Equation_Name] = dict(Entry)
        # Get the forward function object from the module and function name
        Forward_Function = Function_Modules.get(Entry.get('Forward_Module', ''))
        if Forward_Function is not None:
            List_Of_Functions_And_Variables[Equation_Name]['Forward_Function'] = getattr(Forward_Function, Entry.get('Forward_Function_Name', ''), None)
        # Get the inverse function object from the module and function name
        Inverse_Function = Function_Modules.get(Entry.get('Inverse_Module', ''))
        if Inverse_Function is not None:
            List_Of_Functions_And_Variables[Equation_Name]['Inverse_Function'] = getattr(Inverse_Function, Entry.get('Inverse_Function_Name', ''), None)
    # Check if any equations/functions could not be found
    Missing_Functions = [
        Name for Name, Entry in List_Of_Functions_And_Variables.items()
        if Entry.get('Forward_Function') is None or Entry.get('Inverse_Function') is None
    ]
    # Send a warning for any equations/functions that could not be found
    if Missing_Functions:
        print(f"Warning: could not resolve function references for: {Missing_Functions}")

    return List_Of_Functions_And_Variables




# Load the list of functions and variables by loading the file or rebuilding the file
def Load_List_Of_Functions_And_Variables(Force_Rebuild=False):

    # Use the current list of functions and variables file if it is valid and a rebuild has not been forced
    if not Force_Rebuild and Check_If_The_Current_List_Of_Functions_And_Variables_Is_Valid():
        try:
            # Load the list of functions and variables from the file
            return Load_List_Of_Functions_And_Variables_From_File()
        except Exception:
            # The file is corrupted or unreadable
            pass

    # Rebuild the list of functions and variables by scanning the EoS modules
    List_Of_Functions_And_Variables = Create_List_Of_Functions_And_Variables_From_Function_Files(*Function_Modules.values())
    # Save the list of functions and variables to the file
    Save_List_Of_Functions_And_Variables_To_File(List_Of_Functions_And_Variables, List_Of_Functions_And_Variables_File)

    # Return the list of functions and variables
    return List_Of_Functions_And_Variables



