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
    # Get the calibration file variable name for the order dictionary
    Order_Calibration_File_Variable_Name = Equation_Order_Dictionary.get("Calibration_File_Variable_Name")
    # Check if the calibration file variable name is a list or a single value
    List_Of_Calibration_File_Variable_Names_For_Order = (Order_Calibration_File_Variable_Name if isinstance(Order_Calibration_File_Variable_Name, list) else [Order_Calibration_File_Variable_Name])
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

    # Find the Function_Information entry for the equation and order pair from the calibration entry
    Function_Information_Entry = Equation_Entry_From_Calibration_Entry.get((Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order))
    # If nothing was found try setting the order to None
    if Function_Information_Entry is None and Calibration_File_Value_For_Order is not None:
        # Then the equation does not have an order
        Function_Information_Entry = Equation_Entry_From_Calibration_Entry.get((Calibration_File_Value_For_Equation, None))
    # If nothing was found search using case insensitive and ignore whitespace and comments
    if Function_Information_Entry is None and Calibration_File_Value_For_Equation:
        # Make the calibration file value for equation all lowercase
        Lowercase_Calibration_File_Value_For_Equation = Calibration_File_Value_For_Equation.lower()
        # Search through all the Function_Information entries
        for (Function_Information_Entry_Equation_Value, Function_Information_Entry_Order_Value), All_Function_Information_Entries in Equation_Entry_From_Calibration_Entry.items():
            # Check if the case insensitive Function_Information entry equation value matches the calibration file value for equation
            if Function_Information_Entry_Equation_Value is not None and str(Function_Information_Entry_Equation_Value).lower() == Lowercase_Calibration_File_Value_For_Equation:
                # Check if the Function_Information entry order value matches the calibration file value for order or if the calibration file value for order is None
                if Function_Information_Entry_Order_Value == Calibration_File_Value_For_Order or Function_Information_Entry_Order_Value is None:
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
        return Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, None, None, None

    # Get the Function_Information entry content for the entry assosiated with the calibration entry
    Function_Information_Entry_Content = Function_Information[Function_Information_Entry]
    # Get the List_Of_Functions_And_Variables entry for the Function_Information entry
        # Remove the trailing __ from the Function_Information entry "Function_Name" so it can later be matched to the correct function in the List_Of_Functions_And_Variables
    List_Of_Functions_And_Variables_Entry = Function_Information_Entry_Content['Function_Name'][:-2]

    return Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Function_Information_Entry, Function_Information_Entry_Content, List_Of_Functions_And_Variables_Entry



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



# Convert V0 (and optionally V0_unc) to the correct units for the corresponding equation.
    # This is only necessary for XRD equations.
        # Adaptive Polynomial (AP2) needs V0 to be in A^3/atom.
        # All other XRD equations need V0 to be in A^3/unit cell.
    # V0_unc is always in the same units as the V0 field it came from, so it receives
    # the identical conversion. Returns a (V0, V0_unc) tuple; V0_unc is None when not provided.
def Convert_V0_To_The_Correct_Units_For_The_Corresponding_Equation(Calibration_Information, Composition, Equation, V0_Unc=None):

    # Convert the uncertainty with the same function used for V0 (or return it unchanged when no conversion is needed)
    def _Convert_Unc(Converter=None, *Args):
        if V0_Unc is None:
            return None
        try:
            Unc = float(V0_Unc)
        except (TypeError, ValueError):
            return None
        if Unc <= 0:
            return None
        return Converter(Unc, *Args) if Converter is not None else Unc

    # Get the method from the calibration information
    Method = Calibration_Information.get('Method', '')

    # Check if the method is XRD
    if Method == 'XRD':

        # AP2/H12-like equations require V0 in A^3/atom
        if Equation in Equation_Required_Extra_Prep_Work:
            # Check if the volume is already in Angstroms cubed per atom
            if Calibration_Information.get('V0 per Atom') is not None:
                return float(Calibration_Information['V0 per Atom']), _Convert_Unc()
            # Check if the volume is in Angstroms cubed per unit cell
            if Calibration_Information.get('V0') is not None:
                return (Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom(Calibration_Information['V0'], Composition),
                        _Convert_Unc(Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom, Composition))
            # Check if the volume is in Angstroms cubed per formula unit
            if Calibration_Information.get('V0 per Formula Unit') is not None:
                return (Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Atom(Calibration_Information['V0 per Formula Unit'], Composition),
                        _Convert_Unc(Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Atom, Composition))
            # Check if the volume is in centimeters cubed per mole
            if Calibration_Information.get('V0 per Centimeter Cubed per Mole') is not None:
                return (Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Atom(Calibration_Information['V0 per Centimeter Cubed per Mole'], Composition),
                        _Convert_Unc(Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Atom, Composition))
            raise ValueError(f"AP2/H12 requires V0 in any form (A^3/unit cell, A^3/atom, A^3/formula unit, or cm^3/mol) for composition '{Composition}'")

        # All other XRD equations require V0 in A^3/unit cell
            # Check if the volume is already in Angstroms cubed per unit cell
        if Calibration_Information.get('V0') is not None:
            return float(Calibration_Information['V0']), _Convert_Unc()
            # Check if the volume is in Angstroms cubed per formula unit
        if Calibration_Information.get('V0 per Formula Unit') is not None:
            return (Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Unit_Cell(Calibration_Information['V0 per Formula Unit'], Composition),
                    _Convert_Unc(Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Unit_Cell, Composition))
            # Check if the volume is in Angstroms cubed per atom
        if Calibration_Information.get('V0 per Atom') is not None:
            return (Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell(Calibration_Information['V0 per Atom'], Composition),
                    _Convert_Unc(Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell, Composition))
            # Check if the volume is in centimeters cubed per mole
        if Calibration_Information.get('V0 per Centimeter Cubed per Mole') is not None:
            return (Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Unit_Cell(Calibration_Information['V0 per Centimeter Cubed per Mole'], Composition),
                    _Convert_Unc(Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Unit_Cell, Composition))
        # If no volume information was found for this XRD calibration send an error message
        raise ValueError(f"XRD calibration for '{Composition}' has no volume field")

    # For all other methods return V0 and V0_unc unchanged
    return Calibration_Information.get('V0'), _Convert_Unc()



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



# Store the corresponding forward or inverse function and variables for an equation
def Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_Entry_From_List_Of_Functions_And_Variables, Equation_Direction, Equation_Variables, Equation_Label):

    def _entry_get(*keys, default=None):
        for Key in keys:
            if Key in Equation_Entry_From_List_Of_Functions_And_Variables:
                return Equation_Entry_From_List_Of_Functions_And_Variables[Key]
        return default

    # Find the forward or inverse function for this equation
    Function = _entry_get(
        f'{Equation_Direction}_Function',
        f'{Equation_Direction.capitalize()}_Function',
    )
    # Check if the function exists
    if Function is None:
        # If the function does not exist return None
        return None
    # Get the variable order for the function
    Variable_Order_For_The_Function = _entry_get(
        f'{Equation_Direction}_Variable_Order_For_The_Function',
        f'{Equation_Direction}_Variable_Order_For_The_Functions',
        f'{Equation_Direction.capitalize()}_Variable_Order_For_The_Function',
        f'{Equation_Direction.capitalize()}_Variable_Order_For_The_Functions',
        default=[],
    )
    # Get the required variables for the function
    Required_Variables_For_The_Function = _entry_get(
        f'{Equation_Direction}_Required_Variables_For_The_Function',
        f'{Equation_Direction}_Required_Variables_For_The_Functions',
        f'{Equation_Direction.capitalize()}_Required_Variables_For_The_Function',
        f'{Equation_Direction.capitalize()}_Required_Variables_For_The_Functions',
        default=[],
    )

    # Make a place to store any missing variables
    Missing_Variables = []
    # Check if any of the required variables are missing from the equation variables
    for Required_Variable in Required_Variables_For_The_Function:
        # Find the value for the required variable
        Value = Equation_Variables.get(Calibration_Key_To_Entry_Key.get(Required_Variable, Required_Variable))
        # If the value does not exist
        if Value is None:
            # Add the required variable to the list of missing variables
            Missing_Variables.append(Required_Variable)
    # If any variables are missing
    if Missing_Variables:
        # Send an error message
        raise ValueError(f"The {Equation_Direction} {Equation_Label} function is missing the following required variables: {Missing_Variables}")

    # Store all the required variables in the correct order for the function
    Ordered_Required_Variables = []
    # Go through all the variables in order
    for (Variable_Type, Variable_Entry_Or_Value) in Variable_Order_For_The_Function:
        # Check if this variable comes from the calibration files
        if Variable_Type == 'calibration':
            # Find the corresponding calibration file entry label for this variable
            Calibration_File_Variable_Information_Entry_Label = Calibration_Key_To_Entry_Key.get(Variable_Entry_Or_Value, Variable_Entry_Or_Value)
            # Get the value stored in the calibration file entry for this variable
            Value = Equation_Variables.get(Calibration_File_Variable_Information_Entry_Label)
            # Check if the value exists
            if Value is not None:
                # Add the value to the list of ordered required variables
                Ordered_Required_Variables.append(float(Value))
        # Check if this variable is a constant
        elif Variable_Type == 'Constant':
            # Add the constant value to the list of ordered required variables
            Ordered_Required_Variables.append(Variable_Entry_Or_Value)

    # Store the corresponding forward or inverse function and variables for this equation
    return lambda Input_Values, Function_For_The_Equation=Function, Ordered_Required_Variables=Ordered_Required_Variables: Function_For_The_Equation(Input_Values, *Ordered_Required_Variables)



# Store the forward and inverse functions and variables for the Adaptive Polynomial (AP2) equation
    # Volume is inputted as Angstroms cubed per unit cell
    # The volume for the forward function must be in Angstroms cubed per atom
    # The volume for the inverse function will output Angstroms cubed per atom
    # Then convert to Angstroms cubed per unit cell
def Store_The_Forward_Or_Inverse_Function_For_The_Adaptive_Polynomial_Equation(Equation_Entry_From_List_Of_Functions_And_Variables, Equation_Variables, Composition, Equation_Label):

    def _entry_get(*keys, default=None):
        for Key in keys:
            if Key in Equation_Entry_From_List_Of_Functions_And_Variables:
                return Equation_Entry_From_List_Of_Functions_And_Variables[Key]
        return default

    # Find the forward and inverse Adaptive Polynomial (AP2) functions
    Forward_Function = _entry_get('Forward_Function', 'forward_Function')
    Inverse_Function = _entry_get('Inverse_Function', 'inverse_Function')
    # Check that both the forward and inverse Adaptive Polynomial (AP2) functions exist
    if Forward_Function is None or Inverse_Function is None:
        # If either function is missing send an error message
        raise ValueError(
            "Either the AP2 forward or reverse functions are missing. Check that both functions are un-commented in XRD_Functions.py and run Update_List_Of_Functions_And_Variables().")
    # Validate required params for both Equation_Directions
    for Equation_Direction, Required_Variables_For_The_Function in [
        (
            'forward',
            _entry_get(
                'forward_required_params',
                'forward_Required_Variables_For_The_Functions',
                'Forward_Required_Variables_For_The_Functions',
                default=[],
            ),
        ),
        (
            'inverse',
            _entry_get(
                'inverse_required_params',
                'inverse_Required_Variables_For_The_Functions',
                'Inverse_Required_Variables_For_The_Functions',
                default=[],
            ),
        ),
    ]:
        # Add any missing required variables to a list of missing variables
        Missing_Variables = [Required_Variable for Required_Variable in Required_Variables_For_The_Function if Equation_Variables.get(Calibration_Key_To_Entry_Key.get(Required_Variable, Required_Variable)) is None]
        # If there are any missing required variables
        if Missing_Variables:
            # Send an error message with the missing variables
            raise ValueError(f"AP2 {Equation_Direction}: missing required params for '{Equation_Label}': {Missing_Variables}")
    # Store the required variables in order for a function direction
    def Build_Ordered_Required_Variables(Variable_Order_For_The_Function):
        Ordered_Required_Variables = []
        for (Variable_Type, Variable_Entry_Or_Value) in Variable_Order_For_The_Function:
            # Check if this variable comes from the calibration files
            if Variable_Type == 'calibration':
                # Translate calibration key to display key before looking up in Equation_Variables
                Calibration_File_Variable_Information_Entry_Label = Calibration_Key_To_Entry_Key.get(Variable_Entry_Or_Value, Variable_Entry_Or_Value)
                # Get the value stored in the calibration file entry for this variable
                Value = Equation_Variables.get(Calibration_File_Variable_Information_Entry_Label)
                # Check if the value exists
                if Value is not None:
                    # Add the value to the list of ordered required variables
                    Ordered_Required_Variables.append(float(Value))
            # Check if this variable is a constant
            else:
                # Add the constant value to the list of ordered required variables
                Ordered_Required_Variables.append(Variable_Entry_Or_Value)
        # Return the ordered required variables for this function direction
        return Ordered_Required_Variables
    # Get the variable order for the forward and inverse functions
    Forward_Variable_Order_For_The_Function = _entry_get(
        'Forward_Variable_Order_For_The_Functions',
        'forward_Variable_Order_For_The_Functions',
        'forward_Variable_Order_For_The_Function',
        default=[],
    )
    Ordered_Required_Variables_For_Forward = Build_Ordered_Required_Variables(Forward_Variable_Order_For_The_Function)
    Inverse_Variable_Order_For_The_Function = _entry_get(
        'Inverse_Variable_Order_For_The_Functions',
        'inverse_Variable_Order_For_The_Functions',
        'inverse_Variable_Order_For_The_Function',
        default=[],
    )
    Ordered_Required_Variables_For_Inverse = Build_Ordered_Required_Variables(Inverse_Variable_Order_For_The_Function)

    # Forward Function: volume arrives in A^3/unit cell, AP2 expects A^3/atom
    def AP2_Forward(Input_Values, Function_For_The_Equation=Forward_Function, Ordered_Required_Variables=Ordered_Required_Variables_For_Forward):
        Input_Values_Per_Atom = Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom(Input_Values, Composition)
        return Function_For_The_Equation(Input_Values_Per_Atom, *Ordered_Required_Variables)
    # Inverse Function: AP2 returns A^3/atom, convert back to A^3/unit cell
    def AP2_Inverse(Input_Values, Function_For_The_Equation=Inverse_Function, Ordered_Required_Variables=Ordered_Required_Variables_For_Inverse):
        Output_Values_Per_Atom = Function_For_The_Equation(Input_Values, *Ordered_Required_Variables)
        # Check if there is an output value
        if Output_Values_Per_Atom is not None:
            Output_Values_Per_Unit_Cell = Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell(Output_Values_Per_Atom, Composition) if Output_Values_Per_Atom is not None else None
            # Return the converted output value
            return Output_Values_Per_Unit_Cell
        # If there is no output value
        else:
            # Return None
            return None

    # Return the forward and inverse functions for the Adaptive Polynomial (AP2) equation
    return AP2_Forward, AP2_Inverse



# Store the provided parameter values in their corresponding functions
def Store_Provided_Variables_For_An_Equation(Equation_Entry_From_The_List_Of_Functions, Direction, Metadata, Label):
    return Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_Entry_From_The_List_Of_Functions, Direction, Metadata, Label)
def Store_Provided_Variables_For_The_Forward_And_Inverse_Adaptive_Polynomial_Equations(Equation_Entry_From_The_List_Of_Functions, Metadata, Composition, Label):
    return Store_The_Forward_Or_Inverse_Function_For_The_Adaptive_Polynomial_Equation(Equation_Entry_From_The_List_Of_Functions, Metadata, Composition, Label)



# Build the forward and inverse function pair for a single calibration
def Build_One_Calibration(Calibration_Entry, File_Key, Is_User_Edited=False, Is_User_Entered=False, List_Of_Functions_And_Variables=None):

    # Check if the list of functions and variables is provided
    if List_Of_Functions_And_Variables is None:
        # Load the list of functions and variables
        List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
    # Resolve EoS type, order, and equation entry all together
    Calibration_File_Value_For_Equation, Calibration_File_Value_For_Order, Function_Information_Entry, Function_Information_Entry_Content, List_Of_Functions_And_Variables_Entry = Get_Equation_Information_For_A_Calibration_Entry(Calibration_Entry)
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
        # The Adaptive Polynomial is a special case
    if Calibration_File_Value_For_Equation in Equation_Required_Extra_Prep_Work:
        Forward_Function, Inverse_Function = Store_The_Forward_Or_Inverse_Function_For_The_Adaptive_Polynomial_Equation(Equation_From_List_Of_Functions_And_Variables, Calibration_Information, Composition, File_Key)
    else:
        Forward_Function = Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, 'forward', Calibration_Information, File_Key)
        Inverse_Function = Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, 'inverse', Calibration_Information, File_Key)

    # Return the calibration file key, the calibration information, the formward function, and the inverse function for this calibration
    return File_Key, Calibration_Information, Forward_Function, Inverse_Function



# Rebuild the forward and inverse functions for an existing calibration, overriding the reference value with a user specified value
def Rebuild_One_Calibration_To_Use_A_User_Inputted_Reference_Value(File_Key, Custom_Reference, Calibration_Information, List_Of_Functions_And_Variables=None):

    # Check if the calibration exists in the current calibration information
    if File_Key not in Calibration_Information:
        # If the calibration does not exist send an error message
        raise ValueError(f"Calibration '{File_Key}' not found")
    # Check if the custom reference input is a dictionary
    if not isinstance(Custom_Reference, dict):
        # If the custom reference input is not a dictionary send an error message
        raise ValueError("Custom reference must be a dictionary with keys 'type' and 'value'")
    # Get the custom reference value
    Custom_Reference_Value = Custom_Reference.get('value')
    # Check if the custom reference value exists
    if Custom_Reference_Value is None:
        # If the custom reference value does not exist send an error message
        raise ValueError("Custom reference must have a 'value'")
    # Create a seperate copy of the calibration information so the original calibration information is not modified
    Calibration_Information = dict(Calibration_Information[File_Key])
    # Get the equation of state for the calibration
    Equation_Of_State = Calibration_Information.get('Equation of State', '')
    # Get the composition for the calibration
    Composition = (Calibration_Information.get('Composition') or '').strip()
    # Get the reference type for the custom reference
    Reference_Type = Custom_Reference.get('type')
    # Check if the custom reference type exists
    if Reference_Type is None:
        # If the custom reference type does not exist send an error message
        raise ValueError("Custom reference must have a 'type'")
    # Convert the custom reference type to a clean string
    Reference_Type = str(Reference_Type).strip()
    # Check if the custom reference type is empty
    if Reference_Type == '':
        # If the custom reference type is empty send an error message
        raise ValueError("Custom reference 'type' is empty. Expected one of: V0, lambda_0, nu_0, P0")
    # Check if the custom reference type is a supported selected option
    Supported_Reference_Types = ['V0', 'lambda_0', 'nu_0', 'P0']
    if Reference_Type not in Supported_Reference_Types:
        # If the custom reference type is not one of the supported options send an error message
        raise ValueError(f"Unsupported custom reference type '{Reference_Type}'. Expected one of: {', '.join(Supported_Reference_Types)}")
    # Check if the user provided a reference volume
    if Reference_Type == 'V0':
        # Make sure the the custon reference volume is the only reference value provided for this calibration
            # Note: this is only changing the copy of the calibration information not the original calibration information
        Calibration_Information['V0'] = Custom_Reference_Value
        Calibration_Information['V0 per Atom'] = None
        Calibration_Information['V0 per Formula Unit'] = None
        Calibration_Information['V0 per Centimeter Cubed per Mole'] = None
        # Make sure the provided reference volume is in the correct units for the corresponding equation
        # V0_unc is already in correct units from Build_One_Calibration and must not be re-converted
        V0, _ = Convert_V0_To_The_Correct_Units_For_The_Corresponding_Equation(Calibration_Information, Composition, Equation_Of_State)
        Calibration_Information['V0'] = V0
    # Check if the user provided a reference wavelength
    elif Reference_Type == 'lambda_0':
        # For Luminescence closures this is stored in the V0 slot
        Calibration_Information['V0'] = Custom_Reference_Value
    # Check if the user provided a reference frequency/wavenumber
    elif Reference_Type == 'nu_0':
        # For Raman/luminescence closures this is stored in the V0 slot
        Calibration_Information['V0'] = Custom_Reference_Value
    # Check if the user provided a reference pressure
    elif Reference_Type == 'P0':
        # Store both user-facing and calibration-key style versions for compatibility
        Calibration_Information['Reference Pressure'] = Custom_Reference_Value
        Calibration_Information['P0'] = Custom_Reference_Value
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
        # The Adaptive Polynomial is a special case
    if Equation_Of_State in Equation_Required_Extra_Prep_Work:
        Forward_Function, Inverse_Function = Store_The_Forward_Or_Inverse_Function_For_The_Adaptive_Polynomial_Equation(Equation_From_List_Of_Functions_And_Variables, Calibration_Information, Composition, File_Key)
    else:
        Forward_Function = Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, 'forward', Calibration_Information, File_Key)
        Inverse_Function = Store_The_Forward_Or_Inverse_Function_For_An_Equation(Equation_From_List_Of_Functions_And_Variables, 'inverse', Calibration_Information, File_Key)

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




