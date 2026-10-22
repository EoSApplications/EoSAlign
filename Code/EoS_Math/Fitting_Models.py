# Load libraries
    # Load standard libraries
import inspect
    # Load third-party libraries
import numpy as np
    # Load local libraries
try:
    from ..Reference_Values_And_Units import Function_Information, Calibration_File_Variable_Information, Calibration_Key_To_Entry_Key
except ImportError:
    from Reference_Values_And_Units import Function_Information, Calibration_File_Variable_Information, Calibration_Key_To_Entry_Key
from .Create_List_Of_Functions_And_Variables import Load_List_Of_Functions_And_Variables
from .Build_Equation_Functions import Build_Equation_Function, Convert_Calibration_Keys_To_Entry_Keys





# Build the models that EoSFitting can fit, one per equation in Function_Information that has "Fitting_Information"
    # Nothing is typed in twice: the equation names come from Function_Information, the function and the
    # order of its arguments come from the EoS_Math functions (through List_Of_Functions_And_Variables),
    # the parameter symbols come from Calibration_File_Variable_Information, and only the starting guesses
    # and the positive-only parameters come from "Fitting_Information"



# Models that have already been built (one list per method)
Fitting_Models_By_Method = {}



# Find the symbol used to display a fitted parameter (for example V₀ for XRD, λ₀ for Luminescence, ν₀ for Raman)
def Get_Parameter_Symbol(Calibration_Key, Method):

    # Find the Calibration_File_Variable_Information entry for the parameter
    Entry_Key = Calibration_Key_To_Entry_Key.get(Calibration_Key)
    Entry = Calibration_File_Variable_Information.get(Entry_Key, {})
    Symbols = Entry.get('Unicode_Symbol')
    Methods = Entry.get('Method')

    # A list of symbols lines up with the list of methods; a single symbol applies to every method
    if isinstance(Symbols, list) and isinstance(Methods, list):
        if Method in Methods and Methods.index(Method) < len(Symbols):
            return Symbols[Methods.index(Method)]
    elif isinstance(Symbols, str) and Symbols:
        return Symbols

    # If the parameter has no symbol then fall back to its calibration file name
    return Calibration_Key



# Build one fitting model from one Function_Information entry
def Build_One_Fitting_Model(Function_Key, Function_Entry, List_Of_Functions_And_Variables):

    # Find the functions and variables for the equation
    Function_Group_Key = Function_Entry['Function_Name'][:-2]
    Equation_Entry = List_Of_Functions_And_Variables.get(Function_Group_Key)
    if Equation_Entry is None:
        raise ValueError(f"'{Function_Key}': no function was found for '{Function_Group_Key}' in List_Of_Functions_And_Variables.")
    Forward_Function = Equation_Entry['Forward_Function']
    Variable_Order = Equation_Entry['Forward_Variable_Order_For_The_Functions']

    # The first argument of the function is the measured value (volume, peak position or wavenumber), every
    # other argument lines up one-to-one with the variable order that the calibration files use
    Argument_Names = list(inspect.signature(Forward_Function).parameters)[1:]
    if len(Argument_Names) != len(Variable_Order):
        raise ValueError(f"'{Function_Key}': the function has {len(Argument_Names)} arguments after the measured value but {len(Variable_Order)} variables in its variable order.")

    # Sort every variable into a fitted parameter, the reference pressure or the atomic number
        # Constants (for example the temperature used by Datchi and Canny 2004) stay in the variable order and never change
    Fitted_Parameters = []
    Has_Reference_Pressure = False
    Has_Atomic_Number = False
    for Variable_Type, Variable_Value in Variable_Order:
        # Constants never change
        if Variable_Type == 'Constant':
            continue
        # The reference pressure is entered by the user rather than fitted
        elif Variable_Value == 'P0':
            Has_Reference_Pressure = True
        # The atomic number is entered by the user rather than fitted
        elif Variable_Value == 'atomic_number':
            Has_Atomic_Number = True
        else:
            Fitted_Parameters.append(Variable_Value)

    # Get the fitting information for the equation
    Fitting_Information = Function_Entry['Fitting_Information']
    Starting_Guesses = Fitting_Information['Starting_Guesses']
    Positive_Parameters = Fitting_Information.get('Positive_Parameters', [])

    # Every fitted parameter needs a starting guess and every starting guess needs a fitted parameter
    if set(Starting_Guesses) != set(Fitted_Parameters):
        raise ValueError(f"'{Function_Key}': Starting_Guesses {sorted(Starting_Guesses)} do not match the fitted parameters {sorted(Fitted_Parameters)}.")
    if not set(Positive_Parameters).issubset(Fitted_Parameters):
        raise ValueError(f"'{Function_Key}': Positive_Parameters {sorted(Positive_Parameters)} are not all fitted parameters {sorted(Fitted_Parameters)}.")

    # Build the list of parameters in the same order as the function's variables
    Method = Function_Entry['Method']
    Parameters = [
        {
            'name': Calibration_Key,
            'label': Get_Parameter_Symbol(Calibration_Key, Method),
            'default': Starting_Guesses[Calibration_Key],
            'positive_only': Calibration_Key in Positive_Parameters,
        }
        for Calibration_Key in Fitted_Parameters
    ]

    return {
        'name': Function_Entry['Display_Name'],
        'function_key': Function_Key,
        'fn': Forward_Function,
        'variable_order': Variable_Order,
        'params': Parameters,
        'has_P0': Has_Reference_Pressure,
        'needs_Z': Has_Atomic_Number,
    }



# Get the models EoSFitting can fit for one method ("XRD", "Luminescence" or "Raman")
def Get_Fitting_Models_For_Method(Method):

    # Build the models for this method the first time they are asked for
    if Method not in Fitting_Models_By_Method:
        List_Of_Functions_And_Variables = Load_List_Of_Functions_And_Variables()
        Fitting_Models_By_Method[Method] = [
            Build_One_Fitting_Model(Function_Key, Function_Entry, List_Of_Functions_And_Variables)
            for Function_Key, Function_Entry in Function_Information.items()
            if Function_Entry['Method'] == Method and 'Fitting_Information' in Function_Entry
        ]
        # EoSFitting identifies a model by its display name, so two models can not share one
        Model_Names = [Fitting_Model['name'] for Fitting_Model in Fitting_Models_By_Method[Method]]
        Repeated_Names = sorted({Name for Name in Model_Names if Model_Names.count(Name) > 1})
        if Repeated_Names:
            del Fitting_Models_By_Method[Method]
            raise ValueError(f"More than one {Method} fitting model has the display name {Repeated_Names}.")

    return Fitting_Models_By_Method[Method]



# Get the values the user enters for a model, stored under the calibration variable names
    # the reference pressure P0 (XRD models) and the atomic number (AP2 and H12)
def Get_Fixed_Variable_Values(Fitting_Model, Reference_Pressure, Atomic_Number=None):

    Values = {}
    if Fitting_Model.get('has_P0', False):
        Values['P0'] = float(Reference_Pressure)
    if Fitting_Model.get('needs_Z', False) and Atomic_Number is not None:
        Values['atomic_number'] = float(Atomic_Number)
    return Values



# Get the number the measured volume is divided by to get volume per atom
    # AP2 and H12 are written per atom, so the measured volume is divided by the number of atoms in one unit of that volume
    # (this matches EoSAlign's volume / atoms per unit cell). Every other model uses 1.0
def Get_Atoms_Divisor(Fitting_Model, Atoms_Per_Unit):

    if Fitting_Model.get('needs_Z', False) and Atoms_Per_Unit and Atoms_Per_Unit > 1:
        return Atoms_Per_Unit
    return 1.0



# Build the function lmfit fits for a model
    # It is the EoS_Math function with the reference pressure, the atomic number and the model's constants stored in it
    # and every fitted parameter left free (named, with its starting guess as the default) so lmfit can find and vary them
    # AP2 and H12 need two quantities the user enters for their composition:
        # Atomic_Number: the mean atomic number per atom (for a compound, the sum of the atomic numbers divided by the atoms per formula unit)
            # for example MgSiO3 is (12 + 14 + 3 * 8) / 5 = 10
        # Atoms_Per_Unit: the number of atoms in one unit of the measured volume, used to change the measured volume to volume per atom
            # for example data in volume per unit cell with 4 formula units of MgSiO3 per cell is 4 * 5 = 20, and data already in volume per atom is 1
    # V0 should be given in volume per atom for these models
def Build_Model_Function(Fitting_Model, Reference_Pressure, Atomic_Number=None, Atoms_Per_Unit=None):

    Atoms_Divisor = Get_Atoms_Divisor(Fitting_Model, Atoms_Per_Unit)
    return Build_Equation_Function(
        Fitting_Model['fn'], Fitting_Model['variable_order'],
        Convert_Calibration_Keys_To_Entry_Keys(Get_Fixed_Variable_Values(Fitting_Model, Reference_Pressure, Atomic_Number)),
        Free_Variables=[Parameter['name'] for Parameter in Fitting_Model['params']],
        Free_Variable_Defaults={Parameter['name']: Parameter['default'] for Parameter in Fitting_Model['params']},
        Input_Conversion=None if Atoms_Divisor == 1.0 else (lambda Input_Values, Divisor=float(Atoms_Divisor): Input_Values / Divisor))



# Calculate the pressure a model gives for each measurement
    # Parameter_Values: the value of each fitted parameter, by parameter name
    # Fixed_Variable_Values: what Get_Fixed_Variable_Values returned for this model
    # Atoms_Divisor: what Get_Atoms_Divisor returned for this model
def Evaluate_Model_Pressures(Fitting_Model, Fixed_Variable_Values, Measurements, Parameter_Values, Atoms_Divisor=1.0):

    Values = dict(Fixed_Variable_Values)
    Values.update({Parameter['name']: Parameter_Values[Parameter['name']] for Parameter in Fitting_Model['params'] if Parameter['name'] in Parameter_Values})
    Model_Function = Build_Equation_Function(
        Fitting_Model['fn'], Fitting_Model['variable_order'], Convert_Calibration_Keys_To_Entry_Keys(Values),
        Input_Conversion=None if Atoms_Divisor == 1.0 else (lambda Input_Values, Divisor=Atoms_Divisor: Input_Values / Divisor))
    return np.array([Model_Function(Measurement) for Measurement in Measurements])
