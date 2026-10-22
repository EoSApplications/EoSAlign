# Load libraries
    # Load standard libraries
import os
import sys
    # Load local libraries
from .Load_Calibration_Files import *
try:
    from ..Reference_Values_And_Units import *
except ImportError:
    from Reference_Values_And_Units import *
from .Volume_Conversion_Functions import *
from .Create_List_Of_Functions_And_Variables import *
from .Build_Equation_Functions import Build_The_Functions_For_An_Equation
from .Custom_Reference import Check_The_Custom_Reference, Apply_The_Custom_Reference



# Controls whether user-edited and user-entered calibration data are included when building
    # all calibrations. Toggled by Set_Calibration_File_Settings() in Build_Dataframe.py (used by Settings.py).
Include_User_Edited_Calibration_Files = True
Include_User_Entered_Calibration_Files = True



# Get the equation information for a calibration entry and validate using the Function_Information dictionary
def Get_Equation_Information_For_A_Calibration_Entry(Calibration_Entry):

    # Get the equation entry from Calibration_File_Variable_Information
    Equation_Dictionary = Calibration_File_Variable_Information.get("Equation of State", {})
    # Get the calibration file variable name for the equation dictionary
    Equation_Calibration_File_Variable_Name = Equation_Dictionary.get("Calibration_File_Variable_Name")
    # Check if the calibration file variable name is a list or a single value
    List_Of_Equation_Calibration_File_Variable_Names = (Equation_Calibration_File_Variable_Name if isinstance(Equation_Calibration_File_Variable_Name, list) else [Equation_Calibration_File_Variable_Name])
    # Create a place to store the calibration file value for the equation
    Calibration_File_Value_For_Equation = ''
    # Check all calibration file variable names for the equation
    for List_Entry in List_Of_Equation_Calibration_File_Variable_Names:
        if List_Entry is None:
            # If the list entry is empty skip it
            continue
        # Get the calibration file value
        Calibration_File_Value = Calibration_Entry.get(List_Entry)
        # Check if there is an acutal value
        if Calibration_File_Value is not None:
            # Store the calibration file value
            Calibration_File_Value_For_Equation = str(Calibration_File_Value)
            break
    # Remove any comments and white space from this calibration file value
    if '#' in Calibration_File_Value_For_Equation:
        # Only use the part of the value before the #
        Calibration_File_Value_For_Equation = Calibration_File_Value_For_Equation[:Calibration_File_Value_For_Equation.index('#')]
    # Strip whitespace from the calibration file value
    Calibration_File_Value_For_Equation = Calibration_File_Value_For_Equation.strip()

    # Get the order entry from Calibration_File_Variable_Information
    Equation_Order_Dictionary = Calibration_File_Variable_Information.get("Order", {})
    # Get the method entry from Calibration_File_Variable_Information
    Equation_Method_Dictionary = Calibration_File_Variable_Information.get("Method", {})
    # Get the calibration file variable name for the order dictionary
    Order_Calibration_File_Variable_Name = Equation_Order_Dictionary.get("Calibration_File_Variable_Name")
    # Check if the calibration file variable name is a list or a single value
    List_Of_Calibration_File_Variable_Names_For_Order = (Order_Calibration_File_Variable_Name if isinstance(Order_Calibration_File_Variable_Name, list) else [Order_Calibration_File_Variable_Name])
    # Get the calibration file variable name for the method dictionary
    Method_Calibration_File_Variable_Name = Equation_Method_Dictionary.get("Calibration_File_Variable_Name")
    # Check if the calibration file variable name is a list or a single value
    List_Of_Calibration_File_Variable_Names_For_Method = (Method_Calibration_File_Variable_Name if isinstance(Method_Calibration_File_Variable_Name, list) else [Method_Calibration_File_Variable_Name])
    # Create a place to store the calibration file value for the order
    Calibration_File_Value_For_Order = ''
    # Check all calibration file variable names for the order
    for List_Entry in List_Of_Calibration_File_Variable_Names_For_Order:
        if List_Entry is None:
            # If the list entry is empty skip it
            continue
        # Get the calibration file value
        Calibration_File_Value = Calibration_Entry.get(List_Entry)
        # Check if there is an acutal value
        if Calibration_File_Value is not None:
            # Store the calibration file value
            Calibration_File_Value_For_Order = str(Calibration_File_Value)
            break
    # Check all calibration file variable names for the method
    Calibration_File_Value_For_Method = ''
    for List_Entry in List_Of_Calibration_File_Variable_Names_For_Method:
        if List_Entry is None:
            # If the list entry is empty skip it
            continue
        # Get the calibration file value
        Calibration_File_Value = Calibration_Entry.get(List_Entry)
        # Check if there is an acutal value
        if Calibration_File_Value is not None:
            # Store the calibration file value
            Calibration_File_Value_For_Method = str(Calibration_File_Value)
            break

    # Find the Function_Information entry for the equation and order pair from the calibration entry
    Function_Information_Entry = Equation_Entry_From_Calibration_Entry.get((Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Calibration_File_Value_For_Method))
    # If nothing was found try setting the order to None
    if Function_Information_Entry is None and Calibration_File_Value_For_Order is not None:
        # Then the equation does not have an order
        Function_Information_Entry = Equation_Entry_From_Calibration_Entry.get((Calibration_File_Value_For_Equation, None, Calibration_File_Value_For_Method))
    # If nothing was found search using case insensitive and ignore whitespace and comments
    if Function_Information_Entry is None and Calibration_File_Value_For_Equation:
        # Make the calibration file value for equation all lowercase
        Lowercase_Calibration_File_Value_For_Equation = Calibration_File_Value_For_Equation.lower()
        # Search through all the Function_Information entries
        for (Function_Information_Entry_Equation_Value, Function_Information_Entry_Order_Value, Function_Information_Entry_Method_Value), All_Function_Information_Entries in Equation_Entry_From_Calibration_Entry.items():
            # Check if the case insensitive Function_Information entry equation value matches the calibration file value for equation
            if Function_Information_Entry_Equation_Value is not None and str(Function_Information_Entry_Equation_Value).lower() == Lowercase_Calibration_File_Value_For_Equation:
                # Check if the Function_Information entry order value matches the calibration file value for order or if the calibration file value for order is None
                if Function_Information_Entry_Order_Value == Calibration_File_Value_For_Order or Function_Information_Entry_Order_Value is None:
                    # Check if the Function_Information entry method value matches the calibration file value for method (case insensitive), or if no method was provided
                        # This matters because multiple equations can share the same equation name and order but differ only by method (e.g. LinearShift for Luminescence vs Raman)
                    if (not Calibration_File_Value_For_Method) or (Function_Information_Entry_Method_Value is not None and str(Function_Information_Entry_Method_Value).lower() == Calibration_File_Value_For_Method.lower()):
                        # The matching Function_Information entry has been found
                        Function_Information_Entry = All_Function_Information_Entries
                        break
    # If no Function_Information entry was found for the equation and order pair from the calibration entry
    if Function_Information_Entry is None:
        # If the calibration entry had an equation value
        if Calibration_File_Value_For_Equation:
            # Send an error message that no corresponding equation was found for this calibration entry
            raise ValueError(f"Unknown equation '{Calibration_File_Value_For_Equation}' with order: {Calibration_File_Value_For_Order!r}")
        # There is no matching equation for this calibration entry
        return Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Calibration_File_Value_For_Method, None, None, None

    # Get the Function_Information entry content for the entry assosiated with the calibration entry
    Function_Information_Entry_Content = Function_Information[Function_Information_Entry]
    # Get the List_Of_Functions_And_Variables entry for the Function_Information entry
        # Remove the trailing __ from the Function_Information entry "Function_Name" so it can later be matched to the correct function in the List_Of_Functions_And_Variables
    List_Of_Functions_And_Variables_Entry = Function_Information_Entry_Content['Function_Name'][:-2]

    return Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Calibration_File_Value_For_Method, Function_Information_Entry, Function_Information_Entry_Content, List_Of_Functions_And_Variables_Entry



# Parse the calibration entry values into a calibration information dictionary with each entry using the Calibration_File_Variable_Information display key as the key
def Parse_Calibration_Entry_Values_Into_Calibration_Information(Calibration_Entry, Calibration_File_Value_For_Method=None, Method=None):

    # Backwards compatibility for callers that pass Method=...
    if Calibration_File_Value_For_Method is None and Method is not None:
        Calibration_File_Value_For_Method = Method

    # If a calibration entry has multiple possible keys seach each key until a value is found
    def Search_Throug_Multiple_Keys(*List_Of_Calibration_File_Variable_Names, Default_Value=None):
        # Search through the list of calibration file variable names
        for Calibration_File_Variable_Name in List_Of_Calibration_File_Variable_Names:
            # Get the value for this calibration file variable name from the calibration entry
            Value = Calibration_Entry.get(Calibration_File_Variable_Name)
            # Check if a value was found
            if Value is not None:
                # Return the value
                return Value
        # If no value was found return the default value
        return Default_Value

    # Create a place to store the calibration information
    Calibration_Information = {}

    # Loop through all the Calibration_File_Variable_Information entries and get the corresponding value from the calibration entry for each entry
    for Calibration_File_Variable_Information_Entry_Label, Calibration_File_Variable_Information_Entry in Calibration_File_Variable_Information.items():
        # Check if a method is specified
        if Calibration_File_Value_For_Method is not None:
            # Get the calibration file variable information entry method
            Calibration_File_Variable_Information_Entry_Method = Calibration_File_Variable_Information_Entry.get('Method')
            # Check if the calibration file variable information entry method has a value
            if Calibration_File_Variable_Information_Entry_Method is None:
                # If there is no value move on
                continue
            # Check if the calibration file variable information entry method is a list or a single value
            if isinstance(Calibration_File_Variable_Information_Entry_Method, list):
                # If it is a list check if the calibration file value for method is in the list
                if Calibration_File_Value_For_Method not in Calibration_File_Variable_Information_Entry_Method:
                    # If the value is not in the list move on
                    continue
            # Then the value is a string
            else:
                # Check if the calibration file variable information entry method matches the calibration file value for method
                if Calibration_File_Variable_Information_Entry_Method != Calibration_File_Value_For_Method:
                    # If the value does not match move on
                    continue

        # Now look at all the calibration file variable names
        Calibration_File_Variable_Name = Calibration_File_Variable_Information_Entry['Calibration_File_Variable_Name']
        # Check if the calibration file variable name is a list or a single value
        List_Of_Calibration_File_Variable_Names = (Calibration_File_Variable_Name if isinstance(Calibration_File_Variable_Name, list) else [Calibration_File_Variable_Name])
        # Check that there is at least one calibration file variable name in the list
        if not List_Of_Calibration_File_Variable_Names or List_Of_Calibration_File_Variable_Names[0] is None:
            # If there are no calibration file variable names move on
            continue
        # Check if this calibration file variable information entry has a default value
        Default_Value = Calibration_File_Variable_Information_Entry.get('Default_Value')
        # Find the value for this calibration file variable information entry
        Calibration_Information[Calibration_File_Variable_Information_Entry_Label] = Search_Throug_Multiple_Keys(*List_Of_Calibration_File_Variable_Names, Default_Value=Default_Value)

    # Return the calibration information dictionary
    return Calibration_Information



# Find the corresponding atomic number for a composition as is required for Adaptive Polynomial (AP2) functions
def Find_The_Corresponding_Atomic_Number_For_A_Composition(Calibration_Information, Composition, Equation_Type, File_Key):

    # Check if the atomic number was provided in the calibration entry
    Atomic_Number = Calibration_Information.get('Atomic Number')
    if Atomic_Number is None:
        Atomic_Number = (Material_Information.get(Composition) or {}).get('Atomic_Number')
    # If no atomic number was found and this is an Adaptive Polynomial (AP2) equation send a warning
    if Atomic_Number is None and Equation_Type in Equation_Required_Extra_Prep_Work:
        # Send a warning that no atomic number was found for this composition and that the Adaptive Polynomial (AP2) equation requires an atomic number
        raise ValueError(
            f"AP2 requires an atomic number (Z) for '{Composition}' but the calibration entry did not provide a value and a value was not found in the provided reference dictionary")

    # Return the atomic number
    return Atomic_Number



# Build the forward and inverse function pair for a single calibration
def Build_One_Calibration(Calibration_Entry, File_Key, Is_User_Edited=False, Is_User_Entered=False, List_Of_Functions_And_Variables=None):

    # Check if the list of functions and variables is provided
    if List_Of_Functions_And_Variables is None:
        # Load the list of functions and variables
        List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
    # Resolve EoS type, order, and equation entry all together
    Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Calibration_File_Value_For_Method, Function_Information_Entry, Function_Information_Entry_Content, List_Of_Functions_And_Variables_Entry = Get_Equation_Information_For_A_Calibration_Entry(Calibration_Entry)
    # Check if there is an equation entry for the provided calibration file information
    if List_Of_Functions_And_Variables_Entry is None:
        # If there is no equation entry for the provided calibration file information send an error message
        raise ValueError(f"No Function_Information entry found for eos='{Calibration_File_Value_For_Equation}', order={Calibration_File_Value_For_Order!r} (file: '{File_Key}'). Add it to Function_Information in Reference_Values_And_Units.py.")
    # Get the method from the equation entry
    Method = Function_Information_Entry_Content.get('Method', '')
    # Get the composition from the calibration entry
    Composition = (Calibration_Entry.get('composition') or '').strip()
    if Composition == 'diamond':
        Composition = 'Diamond'
    # Find the equation in the list of functions and variables
    Equation_From_List_Of_Functions_And_Variables = List_Of_Functions_And_Variables.get(List_Of_Functions_And_Variables_Entry)
    # Check if the equation was found in the list of functions and variables
    if Equation_From_List_Of_Functions_And_Variables is None:
        # If the equation was not found in the list of functions and variables send an error message
        raise ValueError(f"List_Of_Functions_And_Variables key '{List_Of_Functions_And_Variables_Entry}' not found (file: '{File_Key}'). Run Update_List_Of_Functions_And_Variables() to rebuild.")
    # Extract and normalize the calibration information
    Calibration_Information = Parse_Calibration_Entry_Values_Into_Calibration_Information(Calibration_Entry, Method=Method)
    # Store important flags directly in the calibration information for later use
    Calibration_Information['Equation of State'] = Calibration_File_Value_For_Equation
    Calibration_Information['Order'] = Calibration_File_Value_For_Order
    Calibration_Information['Method'] = Method
    Calibration_Information['Composition'] = Composition
    Calibration_Information['Function_Information_Entry'] = Function_Information_Entry
    Calibration_Information['Calibration_File_Key'] = File_Key
    Calibration_Information['is_user_edited'] = Is_User_Edited
    Calibration_Information['is_user_entered'] = Is_User_Entered
    Calibration_Information['List_Of_Functions_And_Variables_Entry'] = List_Of_Functions_And_Variables_Entry
    # Convert V0 and V0_unc together — both receive the identical unit conversion
    V0, V0_Unc = Convert_V0_To_The_Correct_Units_For_The_Corresponding_Equation(
        Calibration_Information, Composition, Calibration_File_Value_For_Equation,
        V0_Unc=Calibration_Information.get('V0 Uncertainty'))
    # Store converted values under their display keys (normalised per Calibration_File_Variable_Information)
    Calibration_Information['V0'] = V0
    Calibration_Information['V0 Uncertainty'] = V0_Unc
    # Find the corresponding atomic number for this composition
    Z = Find_The_Corresponding_Atomic_Number_For_A_Composition(Calibration_Information, Composition, Calibration_File_Value_For_Equation, File_Key)
    # Check if an atomic number was found
    if Z is not None:
        # Store the atomic number
        Calibration_Information['Atomic Number'] = float(Z)
    # Check if the atomic number looks reasonable for this composition
    if Z is not None and Calibration_File_Value_For_Equation in Equation_Required_Extra_Prep_Work and Material_Information.get(Composition, {}).get('Atomic_Number') is not None:
        # Find the atomic number for this composition from the reference dictionary
        Expected_Atomic_Number = Material_Information[Composition]['Atomic_Number']
        # Check if the provided atomic number is within 0.5 of the expected atomic number for this composition
        if abs(float(Z) - Expected_Atomic_Number) > 0.5 * Expected_Atomic_Number:
            # Send a warning that the provided atomic number looks unreasonable for this composition
            print(f"[Build Calibrations] Warning: AP2 atomic_number for '{Composition}' in '{File_Key}' is {Z}, but the expected per-atom mean Z is {Expected_Atomic_Number}. AP2 requires Z per atom, not per formula unit.")
    # Equation-specific compatibility aliases:
    # Some Akahama06 YAML entries encode K0 and K0' as A and B.
    if Calibration_File_Value_For_Equation == 'Akahama06_Equation':
        if Calibration_Information.get('Initial Bulk Modulus') is None and Calibration_Information.get('A') is not None:
            Calibration_Information['Initial Bulk Modulus'] = Calibration_Information.get('A')
        if Calibration_Information.get('First Pressure Derivative of the Bulk Modulus') is None and Calibration_Information.get('B') is not None:
            Calibration_Information['First Pressure Derivative of the Bulk Modulus'] = Calibration_Information.get('B')
    # Special case: 
        # LinearShift may store the reference as V0 instead of lambda_0
    if Calibration_File_Value_For_Equation == 'LinearShift' and Calibration_Information.get('Reference Wavelength (nm)') is None:
        Calibration_Information['Reference Wavelength (nm)'] = Calibration_Information.get('V0')
    # Build the forward and inverse functions for this equation
    Forward_Function, Inverse_Function = Build_The_Functions_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, Calibration_Information, Calibration_File_Value_For_Equation, Composition, File_Key)

    # Return the calibration file key, the calibration information, the formward function, and the inverse function for this calibration
    return File_Key, Calibration_Information, Forward_Function, Inverse_Function



# Rebuild the forward and inverse functions for an existing calibration, overriding the reference value with a user specified value
def Rebuild_One_Calibration_To_Use_A_User_Inputted_Reference_Value(File_Key, Custom_Reference, Calibration_Information, List_Of_Functions_And_Variables=None):

    # Check if the calibration exists in the current calibration information
    if File_Key not in Calibration_Information:
        # If the calibration does not exist send an error message
        raise ValueError(f"Calibration '{File_Key}' not found")
    # Check that the custom reference can be used
    Reference_Type = Check_The_Custom_Reference(Custom_Reference)
    # Create a seperate copy of the calibration information so the original calibration information is not modified
    Calibration_Information = dict(Calibration_Information[File_Key])
    # Get the equation of state for the calibration
    Equation_Of_State = Calibration_Information.get('Equation of State', '')
    # Get the composition for the calibration
    Composition = (Calibration_Information.get('Composition') or '').strip()
    # Store the custom reference in the copy of the calibration information (the original is not changed)
    Apply_The_Custom_Reference(Calibration_Information, Reference_Type, Custom_Reference.get('value'))
    # Check if the list of functions and variables is provided
    if List_Of_Functions_And_Variables is None:
        # Load the list of functions and variables
        List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
    # Find the corresponding entry in the list of functions and variables for this calibration
    List_Of_Functions_And_Variables_Entry = Calibration_Information.get('List_Of_Functions_And_Variables_Entry')
    # Find the equation in the list of functions and variables
    Equation_From_List_Of_Functions_And_Variables = List_Of_Functions_And_Variables.get(List_Of_Functions_And_Variables_Entry)
    # Check if the equation was found in the list of functions and variables
    if Equation_From_List_Of_Functions_And_Variables is None:
        # If the equation was not found in the list of functions and variables send an error message
        raise ValueError(f"Registry key '{List_Of_Functions_And_Variables_Entry}' not found - run Update_List_Of_Functions_And_Variables() to rebuild the registry.")

    # Update the stored forward and inverse functions for this calibration with the new reference value
    Forward_Function, Inverse_Function = Build_The_Functions_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, Calibration_Information, Equation_Of_State, Composition, File_Key)

    # Return the forward and inverse functions for this calibration with the user inputted reference value
    return Forward_Function, Inverse_Function



# Build all calibrations from the loaded calibration files and the list of functions and variables
def Build_All_Calibrations(Calibration_Files_Data=None, List_Of_Functions_And_Variables=None):

    # Check if the calibration files data is provided
    if Calibration_Files_Data is None:
        # Load the calibration files data
        Calibration_Files_Data = Load_All_Calibration_Files()
    # Check if the list of functions and variables is provided
    if List_Of_Functions_And_Variables is None:
        # Load the list of functions and variables
        List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
    # Create places to store all built calibration information and functions
    Calibration_List = []
    All_Calibration_Information = {}
    Calibration_Functions = {}
    # Loop through all the loaded calibration files and build the calibration
    for Calibration_File_Key, Calibration_File_Information in Calibration_Files_Data.items():
        # Get this calibration file entry
        Calibration_File_Entry = (
            Calibration_File_Information.get('data')
            if isinstance(Calibration_File_Information, dict)
            else None
        )
        if Calibration_File_Entry is None and isinstance(Calibration_File_Information, dict):
            Calibration_File_Entry = Calibration_File_Information.get('Calibration File Contents')
        # Find whether this entry was user edited or user entered
        Is_User_Edited = Calibration_File_Information.get('is_user_edited', Calibration_File_Information.get('Calibration File Has Been Edited By User', False))
        Is_User_Entered = Calibration_File_Information.get('is_user_entered', Calibration_File_Information.get('Calibration File Has Been Entered By User', False))
        # Skip this entry if its source is currently toggled off via Set_Calibration_File_Settings()
        if Is_User_Edited and not Include_User_Edited_Calibration_Files:
            continue
        if Is_User_Entered and not Include_User_Entered_Calibration_Files:
            continue
        # Check if this calibration entry is empty
        if Calibration_File_Entry is None:
            # Send a warning message and skip this file
            print(f"[Build Calibrations] Warning: empty YAML file '{Calibration_File_Key}' - skipped")
            continue
        # Build one calibration from this calibration entry
        try:
            File_Key, One_Calibration_Information, Forward_Function, Inverse_Function = Build_One_Calibration(Calibration_File_Entry, Calibration_File_Key, Is_User_Edited, Is_User_Entered, List_Of_Functions_And_Variables)
        except ValueError as exc:
            # Send an error message and skip this file
            print(f"[Build Calibrations] ERROR loading '{Calibration_File_Key}': {exc}")
            continue
        except Exception as exc:
            # Send an unexpected error message and skip this file
            print(f"[Build Calibrations] Unexpected error loading '{Calibration_File_Key}': {exc}")
            continue

        # Store the source calibration file path for this calibration entry
        One_Calibration_Information['file_path'] = Calibration_File_Information.get('file_path', Calibration_File_Information.get('Calibration File Path', ''))
        # Store this calibration using Calibration_File_Key as the unique identifier
        Calibration_List.append((Calibration_File_Key, Calibration_File_Entry))
        All_Calibration_Information[Calibration_File_Key] = One_Calibration_Information
        Calibration_Functions[Calibration_File_Key] = (Forward_Function, Inverse_Function)

    # Find all unique compositions from built calibration information
    All_Compositions = sorted({(Calibration_Entry.get('Composition') or '').strip() for Calibration_Entry in All_Calibration_Information.values() if (Calibration_Entry.get('Composition') or '').strip()})
    # Find all unique methods from built calibration information
    All_Methods = sorted({(Calibration_Entry.get('Method') or '').strip() for Calibration_Entry in All_Calibration_Information.values() if (Calibration_Entry.get('Method') or '').strip()})

    # Print a summary of loaded calibration information
    print(f"[Build Calibrations] Loaded {len(Calibration_Functions)} calibrations ({len(All_Compositions)} compositions, {len(All_Methods)} methods)")

    # Return all built calibration data
    return (Calibration_List, All_Calibration_Information, Calibration_Functions, All_Compositions, All_Methods)




