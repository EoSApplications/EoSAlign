# Load libraries
    # Load standard libraries
import functools
import inspect
    # Load local libraries
try:
    from ..Reference_Values_And_Units import Calibration_Key_To_Entry_Key, Equation_Required_Extra_Prep_Work
except ImportError:
    from Reference_Values_And_Units import Calibration_Key_To_Entry_Key, Equation_Required_Extra_Prep_Work
from .Volume_Conversion_Functions import (
    Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom,
    Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell,
)





# Build the function for one equation of state (a forward function that calculates pressure or an inverse function that
# calculates the measured value). This is the one place that decides how the variables of an equation are given to its function.
    # Function: the function from the EoS_Math function files (for example Birch_Murnaghan__Third_Order__Calculate_Pressure_From_Input_Volume)
    # Variable_Order: the variables of the function after its input, in order, from the list of functions and variables
        # [['calibration', 'V0'], ['calibration', 'K0'], ['Constant', 300], ...]
    # Equation_Variables: the values of the 'calibration' variables, stored under their Calibration_File_Variable_Information entry keys
    # Free_Variables: the 'calibration' variables that are not given a value and stay arguments of the new function (for fitting)
    # Free_Variable_Defaults: the value each free variable has until it is given one (the starting guess when fitting)
    # Input_Conversion: converts the input before it is given to the function (for example volume per unit cell to volume per atom)
    # Output_Conversion: converts the output of the function (it is skipped if the function has no output)
    # Independent_Variable_Name: the name the input has when the new function is called with keywords (lmfit uses "x")
    #
    # When no variable is free the new function takes only the input (this is how every calibration is built):
        # Function(Input) calculates the output with every variable already stored in it
    # When variables are free the new function takes the input and the free variables as keywords:
        # Function(Input, V0=..., K0=...) and it can be given to lmfit.Model
def Build_Equation_Function(Function, Variable_Order, Equation_Variables, Free_Variables=None, Free_Variable_Defaults=None,
                            Input_Conversion=None, Output_Conversion=None, Independent_Variable_Name='x'):

    Free_Variables = list(Free_Variables or [])
    Equation_Variables = Equation_Variables or {}

    # Make sure every free variable is a variable of this equation
    Calibration_Variables = [Variable_Value for Variable_Type, Variable_Value in Variable_Order if Variable_Type == 'calibration']
    Unknown_Free_Variables = [Variable for Variable in Free_Variables if Variable not in Calibration_Variables]
    if Unknown_Free_Variables:
        raise ValueError(f"{Unknown_Free_Variables} can not be free because they are not variables of this equation. Its variables are {Calibration_Variables}.")

    # Go through all the variables in order and store each one as a value or as a free variable
        # Each item is (True, the name of a free variable) or (False, the value)
    Variable_Slots = []
    for (Variable_Type, Variable_Entry_Or_Value) in Variable_Order:
        # Check if this variable comes from the calibration files
        if Variable_Type == 'calibration':
            # A free variable is not given a value
            if Variable_Entry_Or_Value in Free_Variables:
                Variable_Slots.append((True, Variable_Entry_Or_Value))
                continue
            # Find the corresponding calibration file entry label for this variable
            Calibration_File_Variable_Information_Entry_Label = Calibration_Key_To_Entry_Key.get(Variable_Entry_Or_Value, Variable_Entry_Or_Value)
            # Get the value stored in the calibration file entry for this variable
            Value = Equation_Variables.get(Calibration_File_Variable_Information_Entry_Label)
            # Check if the value exists
            if Value is not None:
                # Add the value to the variable slots
                Variable_Slots.append((False, float(Value)))
        # Check if this variable is a constant
        elif Variable_Type == 'Constant':
            # Add the constant value to the variable slots
            Variable_Slots.append((False, Variable_Entry_Or_Value))

    # Path 1:
        # Every variable has a value
    if not Free_Variables:
        Ordered_Required_Variables = [Value for _, Value in Variable_Slots]

        # Check if the input or output needs to be converted
        if Input_Conversion is None and Output_Conversion is None:
            # Store the corresponding function and variables for this equation
            return lambda Input_Values, Function_For_The_Equation=Function, Ordered_Required_Variables=Ordered_Required_Variables: Function_For_The_Equation(Input_Values, *Ordered_Required_Variables)

        # Convert the input and the output around the function
        def Equation_Function_With_Conversions(Input_Values, Function_For_The_Equation=Function, Ordered_Required_Variables=Ordered_Required_Variables,
                                               Input_Conversion=Input_Conversion, Output_Conversion=Output_Conversion):
            # Convert the input
            if Input_Conversion is not None:
                Input_Values = Input_Conversion(Input_Values)
            # Calculate the output
            Output_Values = Function_For_The_Equation(Input_Values, *Ordered_Required_Variables)
            # Convert the output if there is an output
            if Output_Conversion is not None and Output_Values is not None:
                Output_Values = Output_Conversion(Output_Values)
            return Output_Values
        return Equation_Function_With_Conversions

    # Path 2:
        # Some variables are free
    # The free variables are in the order the function uses them
    Free_Variables_In_Order = [Value for Is_Free, Value in Variable_Slots if Is_Free]
    Free_Variable_Defaults = Free_Variable_Defaults or {}
    Variables_With_Defaults = [Variable for Variable in Free_Variables_In_Order if Variable in Free_Variable_Defaults]
    if Variables_With_Defaults and len(Variables_With_Defaults) != len(Free_Variables_In_Order):
        raise ValueError("Give a default for every free variable or for none of them.")

    # The function lmfit uses: the input is the first argument, the free variables are keywords
    def Equation_Function_With_Free_Variables(*Positional_Arguments, **Keyword_Arguments):
        # The input is the first positional argument or the independent variable keyword
        if len(Positional_Arguments) > 1:
            raise TypeError(f"The input is the only positional argument, the free variables {Free_Variables_In_Order} are keywords.")
        if Positional_Arguments:
            Input_Values = Positional_Arguments[0]
        else:
            Input_Values = Keyword_Arguments.pop(Independent_Variable_Name)
        # A free variable that was not given a value has its default
        Free_Values = {**Free_Variable_Defaults, **Keyword_Arguments}
        # Put the free variables where they belong in the order of the variables
        Ordered_Variables = [Free_Values[Value] if Is_Free else Value for Is_Free, Value in Variable_Slots]
        # Convert the input
        if Input_Conversion is not None:
            Input_Values = Input_Conversion(Input_Values)
        # Calculate the output
        Output_Values = Function(Input_Values, *Ordered_Variables)
        # Convert the output if there is an output
        if Output_Conversion is not None and Output_Values is not None:
            Output_Values = Output_Conversion(Output_Values)
        return Output_Values

    # Show the input and the free variables by name so lmfit can find them
    Signature_Parameters = [inspect.Parameter(Independent_Variable_Name, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    for Variable in Free_Variables_In_Order:
        if Variable in Free_Variable_Defaults:
            Signature_Parameters.append(inspect.Parameter(Variable, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=Free_Variable_Defaults[Variable]))
        else:
            Signature_Parameters.append(inspect.Parameter(Variable, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    Equation_Function_With_Free_Variables.__signature__ = inspect.Signature(Signature_Parameters)

    return Equation_Function_With_Free_Variables


# Build the forward and/or inverse function of an equation from its entry in the list of functions and variables
    # This is how every calibration is built, rebuilt with a custom reference, and rebuilt with one parameter changed for error propagation
    # Equation_Entry: the equation's entry in the list of functions and variables
    # Equation_Variables: the calibration information that holds the values of the equation's variables
    # Equation_Type: the equation of state name from the calibration (the Adaptive Polynomial equations, AP2 and H12, are a special case)
    # Composition: the composition of the calibration (the Adaptive Polynomial equations use it to change volumes between unit cell and atom)
    # Equation_Label: the calibration the functions are for (only used in error messages)
    # Directions: 'forward' and/or 'inverse', the functions to build
    # Returns (the forward function, the inverse function), a direction that was not asked for is None
    # The Adaptive Polynomial (AP2) equations:
        # Volume is inputted as Angstroms cubed per unit cell
        # The volume for the forward function must be in Angstroms cubed per atom
        # The volume for the inverse function will output Angstroms cubed per atom
        # Then convert to Angstroms cubed per unit cell
        # Both functions must exist and have every required variable, even if only one direction was asked for
def Build_The_Functions_For_An_Equation(Equation_Entry, Equation_Variables, Equation_Type, Composition, Equation_Label, Directions=('forward', 'inverse')):

    # Find the variables a direction needs that have no value
    def Find_Missing_Required_Variables(Direction):
        Required_Variables = Equation_Entry.get(f'{Direction.capitalize()}_Required_Variables_For_The_Functions', [])
        return [Required_Variable for Required_Variable in Required_Variables
                if Equation_Variables.get(Calibration_Key_To_Entry_Key.get(Required_Variable, Required_Variable)) is None]

    # Check if this is an Adaptive Polynomial (AP2) equation
    Is_Adaptive_Polynomial = Equation_Type in Equation_Required_Extra_Prep_Work
    Conversions = {}
    if Is_Adaptive_Polynomial:
        # Check that both the forward and inverse functions exist
        if Equation_Entry.get('Forward_Function') is None or Equation_Entry.get('Inverse_Function') is None:
            # If either function is missing send an error message
            raise ValueError(
                "Either the AP2 forward or reverse functions are missing. Check that both functions are un-commented in XRD_Functions.py and run Update_List_Of_Functions_And_Variables().")
        # Check that both directions have every required variable
        for Direction in ('forward', 'inverse'):
            Missing_Variables = Find_Missing_Required_Variables(Direction)
            # If there are any missing required variables send an error message with the missing variables
            if Missing_Variables:
                raise ValueError(f"AP2 {Direction}: missing required params for '{Equation_Label}': {Missing_Variables}")
        # Forward Function: volume arrives in A^3/unit cell, AP2 expects A^3/atom
        # Inverse Function: AP2 returns A^3/atom, convert back to A^3/unit cell
        Conversions = {
            'forward': {'Input_Conversion': functools.partial(Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom, Composition=Composition)},
            'inverse': {'Output_Conversion': functools.partial(Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell, Composition=Composition)},
        }

    # Build each direction that was asked for
    Built_Functions = {'forward': None, 'inverse': None}
    for Direction in Directions:
        # Find the function for this direction
        Function = Equation_Entry.get(f'{Direction.capitalize()}_Function')
        # If the function does not exist then there is nothing to build
        if Function is None:
            continue
        # Check that every required variable has a value (the Adaptive Polynomial equations were checked above)
        if not Is_Adaptive_Polynomial:
            Missing_Variables = Find_Missing_Required_Variables(Direction)
            if Missing_Variables:
                raise ValueError(f"The {Direction} {Equation_Label} function is missing the following required variables: {Missing_Variables}")
        # Build the function
        Built_Functions[Direction] = Build_Equation_Function(
            Function, Equation_Entry.get(f'{Direction.capitalize()}_Variable_Order_For_The_Functions', []), Equation_Variables,
            **Conversions.get(Direction, {}))

    return Built_Functions['forward'], Built_Functions['inverse']


# Change values that are stored under calibration variable names (V0, K0, K0_prime, ...) to the entry keys that
# Equation_Variables uses ('V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus', ...)
def Convert_Calibration_Keys_To_Entry_Keys(Values_By_Calibration_Key):

    return {Calibration_Key_To_Entry_Key.get(Calibration_Key, Calibration_Key): Value for Calibration_Key, Value in Values_By_Calibration_Key.items()}
