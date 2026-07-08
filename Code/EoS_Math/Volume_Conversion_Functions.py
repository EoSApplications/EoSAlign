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



