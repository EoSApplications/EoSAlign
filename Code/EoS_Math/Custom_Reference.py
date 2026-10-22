# Load libraries
    # Load local libraries
from .Volume_Conversion_Functions import (
    Convert_V0_To_The_Correct_Units_For_The_Corresponding_Equation,
    Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell,
)





# A custom reference replaces the reference value stored in a calibration (for example V0) with a value the user enters
    # It is a dictionary: {'type': ..., 'value': ..., 'uncertainty': ...}
    # This is the one place that decides what a custom reference means:
        # Check_The_Custom_Reference: is the custom reference usable?
        # Convert_The_Custom_Reference_To_Unit_Cell_Volume: change a custom V0 from the user's volume unit to volume per unit cell
        # Apply_The_Custom_Reference: store the custom reference in a copy of a calibration's information



# The types of custom reference
    # V0: a reference volume (XRD)
    # lambda_0: a reference wavelength (Luminescence)
    # nu_0: a reference wavenumber (Raman)
    # P0: a reference pressure
Supported_Custom_Reference_Types = ['V0', 'lambda_0', 'nu_0', 'P0']

# The type of custom reference the user is asked for with each method (the user interface only offers a reference value for these)
Custom_Reference_Type_For_Each_Method = {
    'XRD': 'V0',
    'Luminescence': 'lambda_0',
    'Raman': 'nu_0',
}



# Check that a custom reference can be used and return its type as a clean string
def Check_The_Custom_Reference(Custom_Reference):

    # Check if the custom reference input is a dictionary
    if not isinstance(Custom_Reference, dict):
        # If the custom reference input is not a dictionary send an error message
        raise ValueError("Custom reference must be a dictionary with keys 'type' and 'value'")
    # Check if the custom reference value exists
    if Custom_Reference.get('value') is None:
        # If the custom reference value does not exist send an error message
        raise ValueError("Custom reference must have a 'value'")
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
    # Check if the custom reference type is a supported option
    if Reference_Type not in Supported_Custom_Reference_Types:
        # If the custom reference type is not one of the supported options send an error message
        raise ValueError(f"Unsupported custom reference type '{Reference_Type}'. Expected one of: {', '.join(Supported_Custom_Reference_Types)}")

    return Reference_Type



# Change a custom V0 (and its uncertainty) from the volume unit the data was entered in to volume per unit cell
    # Any other custom reference is returned as it was, and the custom reference that was given is never changed
def Convert_The_Custom_Reference_To_Unit_Cell_Volume(Custom_Reference, Volume_Unit, Composition):

    # Only a reference volume has a volume unit
    if Custom_Reference is None or Custom_Reference.get('type') != 'V0':
        return Custom_Reference
    Custom_V0 = Custom_Reference.get('value')
    if Custom_V0 is None:
        return Custom_Reference

    # Convert the reference volume
    Converted_Custom_Reference = dict(Custom_Reference)
    Converted_Custom_Reference['value'] = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell([Custom_V0], Volume_Unit, Composition)[0]
    # Convert its uncertainty the same way
    Custom_V0_Uncertainty = Custom_Reference.get('uncertainty', 0)
    if Custom_V0_Uncertainty:
        Converted_Custom_Reference['uncertainty'] = Convert_All_Volumes_To_Angstroms_Cubed_Per_Unit_Cell([Custom_V0_Uncertainty], Volume_Unit, Composition)[0]

    return Converted_Custom_Reference



# Store a custom reference in a copy of a calibration's information
    # Calibration_Information: a copy of the calibration's information (it is changed and returned, so give it a copy)
    # Reference_Type: the type of the custom reference, after Check_The_Custom_Reference
    # Value, Uncertainty: the custom reference value and its uncertainty (0.0 if it has none)
    # A reference volume (V0) is changed to the units its equation needs (volume per unit cell, or per atom for AP2 and H12)
    # A reference wavelength or wavenumber (lambda_0, nu_0) is stored in the V0 slot, because that is where the equations keep it
    # A reference pressure (P0) is stored as the reference pressure
def Apply_The_Custom_Reference(Calibration_Information, Reference_Type, Value, Uncertainty=0.0):

    if Reference_Type == 'V0':
        # Make sure the custom reference volume is the only reference value provided for this calibration
        Calibration_Information['V0'] = Value
        Calibration_Information['V0 per Atom'] = None
        Calibration_Information['V0 per Formula Unit'] = None
        Calibration_Information['V0 per Centimeter Cubed per Mole'] = None
        # Make sure the reference volume and its uncertainty are in the correct units for the corresponding equation
        Composition = (Calibration_Information.get('Composition') or '').strip()
        V0, V0_Uncertainty = Convert_V0_To_The_Correct_Units_For_The_Corresponding_Equation(
            Calibration_Information, Composition, Calibration_Information.get('Equation of State', ''), V0_Unc=Uncertainty)
        Calibration_Information['V0'] = V0
        Calibration_Information['V0 Uncertainty'] = V0_Uncertainty or 0.0
    elif Reference_Type == 'P0':
        # Store both user-facing and calibration-key style versions for compatibility
        Calibration_Information['Reference Pressure'] = Value
        Calibration_Information['P0'] = Value
    else:
        # lambda_0 and nu_0 are stored in the V0 slot
        Calibration_Information['V0'] = Value
        Calibration_Information['V0 Uncertainty'] = Uncertainty

    return Calibration_Information
