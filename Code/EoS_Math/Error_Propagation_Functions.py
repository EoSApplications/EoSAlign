# Load libraries
    # Load standard libraries
import numpy as np
import pandas as pd
    # Load local libraries
try:
    from ..Reference_Values_And_Units import Material_Information, Equation_Required_Extra_Prep_Work, Calibration_Key_To_Entry_Key, Calibration_File_Variable_Information
except ImportError:
    from Reference_Values_And_Units import Material_Information, Equation_Required_Extra_Prep_Work, Calibration_Key_To_Entry_Key, Calibration_File_Variable_Information
from .Parse_Calibration_Information import (
    Store_The_Forward_Or_Inverse_Function_For_An_Equation as _Build_Generic_Closure,
    Store_The_Forward_Or_Inverse_Function_For_The_Adaptive_Polynomial_Equation as _Build_AP2_Closure_Pair,
)





# Error propagation using the standard formula:
#   sigma_f = sqrt( (df/dx1)^2sigma_x1^2 + (df/dx2)^2sigma_x2^2 + ... )
# All derivatives are computed numerically with the central-difference method.
# Parameter uncertainties are taken from _unc fields in the calibration metadata.





# Convert values into floats
def Safe_Float(Value, Default_Value=0.0):

    # Check if the value exists
    if Value is None:
        # Return the default value
        return Default_Value
    # Check if the value is a number
    if isinstance(Value, (int, float)):
        # Return the value as a float
        return float(Value)
    # Check if the value is a stirng
    if isinstance(Value, str):
        # Try converting the string to a float
        try:
            # Return the value as a float
            return float(Value)
        # Otherwise return the default value
        except (ValueError, TypeError):
            return Default_Value
    # Otherwise return the default value
    return Default_Value



# Find the derivative of a function at a point using the central difference method
def Numerical_Derivative(Function, X, H=None, Lower_Bound=None, Upper_Bound=None):

    # Check if a step size was provided; use a minimum absolute step to avoid cancellation near zero
    if H is None:
        H = max(abs(X) * 1e-5, 1e-5)
    try:
        # If the lower probe would fall outside the valid domain use a forward difference
        if Lower_Bound is not None and (X - H) < Lower_Bound:
            Function_Value = Function(X)
            Function_Value_Plus = Function(X + H)
            if Function_Value is None or Function_Value_Plus is None:
                return np.nan
            return (Function_Value_Plus - Function_Value) / H
        # If the upper probe would fall outside the valid domain use a backward difference
        if Upper_Bound is not None and (X + H) > Upper_Bound:
            Function_Value = Function(X)
            Function_Value_Minus = Function(X - H)
            if Function_Value is None or Function_Value_Minus is None:
                return np.nan
            return (Function_Value - Function_Value_Minus) / H
        Function_Value_Plus = Function(X + H)
        Function_Value_Minus = Function(X - H)
        if Function_Value_Plus is None or Function_Value_Minus is None:
            return np.nan
        return (Function_Value_Plus - Function_Value_Minus) / (2 * H)
    except Exception as Exception_Message:
        print(f"[Error Propagation] Numerical_Derivative failed at x={X}: {Exception_Message}")
        return np.nan



# Find all (parameter_display_key, uncertainty_value) pairs from Calibration_Information.
# Uses Calibration_File_Variable_Information to discover every uncertainty field by its display key,
# then maps it back to the corresponding parameter display key via Calibration_Key_To_Entry_Key.
# All lookups use the normalised display keys from Calibration_File_Variable_Information — no raw
# YAML keys appear in Calibration_Information or in the returned pairs.
def _Get_Uncertainty_Pairs(Metadata):

    Pairs = []
    Seen_Param_Keys = set()
    for Entry_Key, Entry in Calibration_File_Variable_Information.items():
        # Identify uncertainty entries by their primary YAML key ending in '_unc'
        Raw_Yaml = Entry.get('Calibration_File_Variable_Name')
        Primary_Calibration_Key = (Raw_Yaml[0] if isinstance(Raw_Yaml, list) else Raw_Yaml) or ''
        if not isinstance(Primary_Calibration_Key, str) or not Primary_Calibration_Key.endswith('_unc'):
            continue
        # Check whether this calibration has a non-zero uncertainty for this field
        Uncertainty_Value = Safe_Float(Metadata.get(Entry_Key), 0.0)
        if Uncertainty_Value <= 0:
            continue
        # Resolve the parameter display key (strip '_unc' → raw param key → display key)
        Param_Display_Key = Calibration_Key_To_Entry_Key.get(Primary_Calibration_Key[:-4])
        if Param_Display_Key is None:
            continue
        # Make sure the parameter itself is present and deduplicate
        if Metadata.get(Param_Display_Key) is None or Param_Display_Key in Seen_Param_Keys:
            continue
        Seen_Param_Keys.add(Param_Display_Key)
        Pairs.append((Param_Display_Key, Uncertainty_Value))
    return Pairs



# Override the ambient reference value and its uncertainty in a metadata dict copy
def _Apply_Custom_Reference(Metadata, Custom_Reference):
    # Mutate (in-place) a metadata dict copy to reflect a user-supplied reference override
    Reference_Type = Custom_Reference.get('type')
    Custom_Value = Custom_Reference.get('value')
    Custom_Uncertainty = Safe_Float(Custom_Reference.get('uncertainty'), 0.0)
    if Custom_Value is None:
        return Metadata

    Equation_Type = Metadata.get('Equation of State', '')
    Composition = (Metadata.get('Composition') or '').strip()

    # All reference values are stored under their Calibration_File_Variable_Information display keys.
    # 'V0' is the display key for V0 (XRD), lambda_0 (Luminescence), and nu_0 (Raman).
    # 'V0 Uncertainty' is the corresponding uncertainty display key.
    if Reference_Type == 'V0':
        if Equation_Type in Equation_Required_Extra_Prep_Work:
            Atoms_Per_Unit_Cell = ((Material_Information.get(Composition) or {}).get('Formula_Units', 1) * ((Material_Information.get(Composition) or {}).get('Atoms_Per_Formula_Unit', None) or 1))
            Metadata['V0'] = Custom_Value / Atoms_Per_Unit_Cell
            Metadata['V0 Uncertainty'] = Custom_Uncertainty / Atoms_Per_Unit_Cell
        else:
            Metadata['V0'] = Custom_Value
            Metadata['V0 Uncertainty'] = Custom_Uncertainty
    elif Reference_Type == 'lambda_0':
        Metadata['V0'] = Custom_Value
        Metadata['V0 Uncertainty'] = Custom_Uncertainty
    else:
        Metadata['V0'] = Custom_Value
        Metadata['V0 Uncertainty'] = Custom_Uncertainty

    return Metadata


# Find the reference pressure used as the lower bound for inverse calculations
def _Get_Reference_Pressure(Metadata):

    Reference_Pressure = Safe_Float(Metadata.get('Reference Pressure', Metadata.get('P0', 0)), 0)
    # Return the reference pressure
    return Reference_Pressure


# Rebuild a forward or inverse closure with a perturbed single parameter
def _Rebuild_Forward(Registry_Entry, Metadata, Equation_Type, Composition, Label='perturbed'):
    if Equation_Type in Equation_Required_Extra_Prep_Work:
        Forward_Function, _ = _Build_AP2_Closure_Pair(Registry_Entry, Metadata, Composition, Label)
        return Forward_Function
    return _Build_Generic_Closure(Registry_Entry, 'forward', Metadata, Label)


# Rebuild an inverse closure with a perturbed single parameter
def _Rebuild_Inverse(Registry_Entry, Metadata, Equation_Type, Composition, Label='perturbed'):
    if Equation_Type in Equation_Required_Extra_Prep_Work:
        _, Inverse_Function = _Build_AP2_Closure_Pair(Registry_Entry, Metadata, Composition, Label)
        return Inverse_Function
    return _Build_Generic_Closure(Registry_Entry, 'inverse', Metadata, Label)



# Central-difference derivative of an EoS output w.r.t. one EoS parameter.
# Display_Key is the Calibration_File_Variable_Information display key for the parameter
# (e.g. 'Initial Bulk Modulus'). The EoS rebuild looks up parameters by display key,
# so perturbing only the display key is sufficient.
def _Compute_Parameter_Derivative(X, Registry_Entry, Metadata, Display_Key,
                                   Rebuild_Function, Equation_Type, Composition, Step_Fraction=1e-4,
                                   Lower_Bound=None, Upper_Bound=None):
    Parameter_Value = Safe_Float(Metadata.get(Display_Key), None)
    if Parameter_Value is None:
        return 0.0
    Step_Size = abs(Parameter_Value) * Step_Fraction or 1e-8

    Function_Plus = Rebuild_Function(Registry_Entry, {**Metadata, Display_Key: Parameter_Value + Step_Size}, Equation_Type, Composition)
    Function_Minus = Rebuild_Function(Registry_Entry, {**Metadata, Display_Key: Parameter_Value - Step_Size}, Equation_Type, Composition)

    if Function_Plus is None or Function_Minus is None:
        return 0.0
    try:
        # If the lower probe would fall outside the valid domain use a forward difference
        if Lower_Bound is not None and (X - Step_Size) < Lower_Bound:
            Function_Value = Rebuild_Function(Registry_Entry, dict(Metadata), Equation_Type, Composition)
            if Function_Value is None:
                return 0.0
            Value = Function_Value(X)
            Value_Plus = Function_Plus(X)
            if Value is None or Value_Plus is None or np.isnan(Value) or np.isnan(Value_Plus):
                return 0.0
            return (Value_Plus - Value) / Step_Size
        # If the upper probe would fall outside the valid domain use a backward difference
        if Upper_Bound is not None and (X + Step_Size) > Upper_Bound:
            Function_Value = Rebuild_Function(Registry_Entry, dict(Metadata), Equation_Type, Composition)
            if Function_Value is None:
                return 0.0
            Value = Function_Value(X)
            Value_Minus = Function_Minus(X)
            if Value is None or Value_Minus is None or np.isnan(Value) or np.isnan(Value_Minus):
                return 0.0
            return (Value - Value_Minus) / Step_Size
        Value_Plus = Function_Plus(X)
        Value_Minus = Function_Minus(X)
        if Value_Plus is None or Value_Minus is None or np.isnan(Value_Plus) or np.isnan(Value_Minus):
            return 0.0
        return (Value_Plus - Value_Minus) / (2 * Step_Size)
    except Exception:
        return 0.0



# Propagate the uncertainty through the forward function
def Propagate_Forward(Measured_Value, Measured_Uncertainty, Forward_Function, Metadata=None, Registry_Entry=None, Custom_Reference=None):
    if pd.isna(Measured_Value):
        return np.nan, np.nan

    try:
        if Custom_Reference is not None and Metadata is not None:
            Metadata = _Apply_Custom_Reference(dict(Metadata), Custom_Reference)

        Pressure = Forward_Function(Measured_Value)
        if Pressure is None or pd.isna(Pressure):
            return np.nan, np.nan

        Variance = 0.0

        # Term 1: uncertainty from the measured input
        if Measured_Uncertainty is not None and not pd.isna(Measured_Uncertainty) and Measured_Uncertainty > 0:
            Pressure_Derivative = Numerical_Derivative(Forward_Function, Measured_Value)
            if not np.isnan(Pressure_Derivative):
                Variance += (Pressure_Derivative * Measured_Uncertainty) ** 2

        # Term 2: uncertainty from individual EoS parameters
        if Metadata is not None and Registry_Entry is not None:
            Equation_Type = Metadata.get('Equation of State', '')
            Composition = (Metadata.get('Composition') or '').strip()
            for Display_Key, Uncertainty_Value in _Get_Uncertainty_Pairs(Metadata):
                Parameter_Derivative = _Compute_Parameter_Derivative(
                    Measured_Value, Registry_Entry, Metadata, Display_Key,
                    _Rebuild_Forward, Equation_Type, Composition)
                if Parameter_Derivative and not np.isnan(Parameter_Derivative):
                    Variance += (Parameter_Derivative * Uncertainty_Value) ** 2

        return Pressure, np.sqrt(Variance)

    except Exception as Exception_Message:
        print(f"[Error Propagation] Propagate_Forward failed: {Exception_Message}")
        return np.nan, np.nan



# Propagate the uncertainty through the inverse function
def Propagate_Inverse(Pressure_Value, Pressure_Uncertainty, Inverse_Function, Metadata=None, Registry_Entry=None, Custom_Reference=None):
    
    if pd.isna(Pressure_Value):
        return np.nan, np.nan

    try:
        if Custom_Reference is not None and Metadata is not None:
            Metadata = _Apply_Custom_Reference(dict(Metadata), Custom_Reference)
        elif Metadata is not None:
            Metadata = dict(Metadata)

        if Metadata is not None:
            Reference_Pressure = _Get_Reference_Pressure(Metadata)
            if Pressure_Value < Reference_Pressure:
                return np.nan, np.nan

        Measured_Value = Inverse_Function(Pressure_Value)
        if Measured_Value is None or pd.isna(Measured_Value):
            return np.nan, np.nan

        Variance = 0.0

        # Term 1: uncertainty from the pressure input
        if Pressure_Uncertainty is not None and not pd.isna(Pressure_Uncertainty) and Pressure_Uncertainty > 0:
            Lower_Bound = _Get_Reference_Pressure(Metadata) if Metadata is not None else None
            Value_Derivative = Numerical_Derivative(Inverse_Function, Pressure_Value, Lower_Bound=Lower_Bound)
            if not np.isnan(Value_Derivative):
                Variance += (Value_Derivative * Pressure_Uncertainty) ** 2

        # Term 2: uncertainty from individual EoS parameters
        if Metadata is not None and Registry_Entry is not None:
            Equation_Type = Metadata.get('Equation of State', '')
            Composition = (Metadata.get('Composition') or '').strip()
            Lower_Bound = _Get_Reference_Pressure(Metadata)
            for Display_Key, Uncertainty_Value in _Get_Uncertainty_Pairs(Metadata):
                Parameter_Derivative = _Compute_Parameter_Derivative(
                    Pressure_Value, Registry_Entry, Metadata, Display_Key,
                    _Rebuild_Inverse, Equation_Type, Composition, Lower_Bound=Lower_Bound)
                if Parameter_Derivative and not np.isnan(Parameter_Derivative):
                    Variance += (Parameter_Derivative * Uncertainty_Value) ** 2

        return Measured_Value, np.sqrt(Variance)

    except Exception as Exception_Message:
        print(f"[Error Propagation] Propagate_Inverse failed: {Exception_Message}")
        return np.nan, np.nan
