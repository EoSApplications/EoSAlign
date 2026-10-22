# Load libraries
# Load standard libraries
import os
import sys
# Load third-party libraries
import numpy as np
# Load local libraries
try:
    from ..Reference_Values_And_Units import *
except ImportError:
    from Reference_Values_And_Units import *





# Conversion constants
Avogadros_Number = 6.022e23
Centimeters_Cubed__To__Angstroms_Cubed = 1e24



# Convert a volume to Angstroms cubed per unit cell

    # Convert a volume from Angstroms cubed per formula unit to Angstroms cubed per unit cell
def Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Unit_Cell(V0_Per_Formula_Unit, Composition):
    
    # Get the number of formula units for the given composition
    Formula_Units = (Material_Information.get(Composition) or {}).get('Formula_Units')
    # Check if this composition has formula unit information available
    if Formula_Units is None:
        # If not then the conversion cannot be done
        raise ValueError(f"Unknown composition '{Composition}' - no formula unit information available.")
    # Convert the volume to Angstroms cubed per unit cell
    Angstroms_Cubed_Per_Unit_Cell = float(V0_Per_Formula_Unit) * Formula_Units

    # Return the converted volume in Angstroms cubed per unit cell
    return Angstroms_Cubed_Per_Unit_Cell
 

    # Convert a volume from Angstroms cubed per atom to Angstroms cubed per unit cell
def Convert_Angstroms_Cubed_Per_Atom__To__Angstroms_Cubed_Per_Unit_Cell(V0_Per_Atom, Composition):
    
    # Get the number of formula units for the given composition
    Formula_Units = (Material_Information.get(Composition) or {}).get('Formula_Units')
    # Check if this composition has formula unit information available
    if Formula_Units is None:
        # If not then the conversion cannot be done
        raise ValueError(f"Unknown composition '{Composition}' - no formula unit information available.")
    # Get the number of atoms per formula unit for the given composition
    Atoms_Per_Formula_Unit = (Material_Information.get(Composition) or {}).get('Atoms_Per_Formula_Unit') or 1
    # Convert the volume to Angstroms cubed per unit cell
    Angstroms_Cubed_Per_Unit_Cell = float(V0_Per_Atom) * Formula_Units * Atoms_Per_Formula_Unit
    
    # Return the converted volume in Angstroms cubed per unit cell
    return Angstroms_Cubed_Per_Unit_Cell


    # Convert a volume from centimeters cubed per mole to Angstroms cubed per unit cell
def Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Unit_Cell(V0_Per_Cm3_Per_Mol, Composition):
    
    # Get the number of formula units for the given composition
    Formula_Units = (Material_Information.get(Composition) or {}).get('Formula_Units')
    # Check if this composition has formula unit information available
    if Formula_Units is None:
        # If not then the conversion cannot be done
        raise ValueError(f"Unknown composition '{Composition}' - no formula unit information available.")
    # Convert the volume from centimeters cubed per mole to Angstroms cubed per mole
    Angstroms_Cubed_Per_Mole = float(V0_Per_Cm3_Per_Mol) * Centimeters_Cubed__To__Angstroms_Cubed
    # Convert the volume from Angstroms cubed per mole to Angstroms cubed per formula unit
    Angstroms_Cubed_Per_Formula_Unit = Angstroms_Cubed_Per_Mole / Avogadros_Number
    # Convert the volume from Angstroms cubed per formula unit to Angstroms cubed per unit cell
    Angstroms_Cubed_Per_Unit_Cell = Angstroms_Cubed_Per_Formula_Unit * Formula_Units
    
    # Return the converted volume in Angstroms cubed per unit cell
    return Angstroms_Cubed_Per_Unit_Cell



# Convert a volume to Angstroms cubed per atom

    # Convert a volume from Angstroms cubed per unit cell to Angstroms cubed per atom
def Convert_Angstroms_Cubed_Per_Unit_Cell__To__Angstroms_Cubed_Per_Atom(V0_Per_Unit_Cell, Composition):
    
    # Get the number of formula units for the given composition
    Formula_Units = (Material_Information.get(Composition) or {}).get('Formula_Units')
    # Check if this composition has formula unit information available
    if Formula_Units is None:
        # If not then the conversion cannot be done
        raise ValueError(f"Unknown composition '{Composition}' - no formula unit information available.")
    # Get the number of atoms per formula unit for the given composition
    Atoms_Per_Formula_Unit = (Material_Information.get(Composition) or {}).get('Atoms_Per_Formula_Unit') or 1
    # Convert the volume to the number of atoms per unit cell
    Atoms_Per_Unit_Cell = Formula_Units * Atoms_Per_Formula_Unit
    # Convert the volume to Angstroms cubed per atom
    Angstroms_Cubed_Per_Atom = float(V0_Per_Unit_Cell) / Atoms_Per_Unit_Cell

    # Return the converted volume in Angstroms cubed per atom
    return Angstroms_Cubed_Per_Atom


    # Convert a volume from Angstroms cubed per formula unit to Angstroms cubed per atom
def Convert_Angstroms_Cubed_Per_Formula_Unit__To__Angstroms_Cubed_Per_Atom(V0_Per_Formula_Unit, Composition):
    
    # Get the number of formula units for the given composition
    Formula_Units = (Material_Information.get(Composition) or {}).get('Formula_Units')
    # Check if this composition has formula unit information available
    if Formula_Units is None:
        # If not then the conversion cannot be done
        raise ValueError(f"Unknown composition '{Composition}' - no formula unit information available.")
    # Get the number of atoms per formula unit for the given composition
    Atoms_Per_Formula_Unit = (Material_Information.get(Composition) or {}).get('Atoms_Per_Formula_Unit') or 1
    # Convert the volume to Angstroms cubed per atom
    Angstroms_Cubed_Per_Atom = float(V0_Per_Formula_Unit) / Atoms_Per_Formula_Unit

    # Return the converted volume in Angstroms cubed per atom
    return Angstroms_Cubed_Per_Atom


    # Convert a volume from centimeters cubed per mole to Angstroms cubed per atom
def Convert_Centimeters_Cubed_Per_Mole__To__Angstroms_Cubed_Per_Atom(V0_Per_Cm3_Per_Mol, Composition):

    # Get the number of atoms per formula unit for the given composition
    Atoms_Per_Formula_Unit = (Material_Information.get(Composition) or {}).get('Atoms_Per_Formula_Unit') or 1
    # Convert the volume to Angstroms cubed per mole
    Angstroms_Cubed_Per_Mole = float(V0_Per_Cm3_Per_Mol) * Centimeters_Cubed__To__Angstroms_Cubed
    # Convert the volume from Angstroms cubed per mole to Angstroms cubed per formula unit
    Angstroms_Cubed_Per_Formula_Unit = Angstroms_Cubed_Per_Mole / Avogadros_Number
    # Convert the volume from Angstroms cubed per formula unit to Angstroms cubed per atom
    Angstroms_Cubed_Per_Atom = Angstroms_Cubed_Per_Formula_Unit / Atoms_Per_Formula_Unit

    # Return the converted volume in Angstroms cubed per atom
    return Angstroms_Cubed_Per_Atom



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
