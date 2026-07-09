# Load libraries
import os
import sys
import shutil
    # Load third-party libraries
import numpy as np
import yaml




# List of materials and their corresponding information
    # Display label
    # Formula units
    # Atoms per formula unit
    # Atomic number
Material_Information = {

    'Ag': {
        'Display_Label': 'Ag',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 47,
    },
    'Al': {
        'Display_Label': 'Al',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 13,
    },
    'Ar': {
        'Display_Label': 'Ar',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 18,
    },
    'Au': {
        'Display_Label': 'Au',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 79,
    },
    'Be': {
        'Display_Label': 'Be',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 4,
    },
    'Bi': {
        'Display_Label': 'Bi',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 83,
    },
    'Co-hcp': {
        'Display_Label': 'Co (hcp)',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 27,
    },
    'Cu': {
        'Display_Label': 'Cu',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 29,
    },
    # Parse_Calibration_Information.py canonicalizes "diamond" to "Diamond" within the Build_One_Calibration function
    'Diamond': {
        'Display_Label': 'Diamond',
        'Symmetry': ['Diamond cubic'],
        'Formula_Units': 8,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 6,
    },
    'Fe-bcc': {
        'Display_Label': 'Fe (bcc)',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 26,
    },
    'Fe-hcp': {
        'Display_Label': 'Fe (hcp)',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 26,
    },
    'He': {
        'Display_Label': 'He',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 2,
    },
    'Mo': {
        'Display_Label': 'Mo',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 42,
    },
    'Na': {
        'Display_Label': 'Na',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 11,
    },
    'Nb': {
        'Display_Label': 'Nb',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 41,
    },
    'Ne': {
        'Display_Label': 'Ne',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 10,
    },
    'Ni': {
        'Display_Label': 'Ni',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 28,
    },
    'Pd': {
        'Display_Label': 'Pd',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 46,
    },
    'Pt': {
        'Display_Label': 'Pt',
        'Symmetry': ['Face-centered cubic', 'FCC'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 78,
    },
    'Re': {
        'Display_Label': 'Re',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 75,
    },
    'Ta': {
        'Display_Label': 'Ta',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 73,
    },
    'W': {
        'Display_Label': 'W',
        'Symmetry': ['Body-centered cubic', 'BCC'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 74,
    },
    'Zn': {
        'Display_Label': 'Zn',
        'Symmetry': ['Hexagonal close-packed', 'HCP'],
        'Formula_Units': 2,
        'Atoms_Per_Formula_Unit': '',
        'Atomic_Number': 30,
    },
    'MgO': {
        'Display_Label': 'MgO',
        'Symmetry': ['Rock salt (B1)'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': 2,   # 1 Mg + 1 O
        'Atomic_Number': 10.0,   # (12 + 8) / 2
    },
    'cBN': {
        'Display_Label': 'cBN',
        'Symmetry': ['Cubic boron nitride'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': 2,   # 1 B + 1 N
        'Atomic_Number': 6.0,   # (5 + 7) / 2
    },
    'NaCl-B1': {
        'Display_Label': 'NaCl (B1)',
        'Symmetry': ['Rock salt (B1)'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': 2,   # 1 Na + 1 Cl
        'Atomic_Number': 14.0,   # (11 + 17) / 2
    },
    'NaCl-B2': {
        'Display_Label': 'NaCl (B2)',
        'Symmetry': ['CsCl-type (B2)'],
        'Formula_Units': 1,
        'Atoms_Per_Formula_Unit': 2,   # 1 Na + 1 Cl
        'Atomic_Number': 14.0,   # (11 + 17) / 2
    },
    'KCl-B2': {
        'Display_Label': 'KCl (B2)',
        'Symmetry': ['CsCl-type (B2)'],
        'Formula_Units': 1,
        'Atoms_Per_Formula_Unit': 2,   # 1 K + 1 Cl
        'Atomic_Number': 18.0,   # (19 + 17) / 2
    },
    'Al2O3': {
        'Display_Label': 'Al₂O₃',
        'Symmetry': ['Corundum'],
        'Formula_Units': 6,
        'Atoms_Per_Formula_Unit': 5,   # 2 Al + 3 O
        'Atomic_Number': 10.0,   # (2*13 + 3*8) / 5
    },
    'SrB4O7': {
        'Display_Label': 'SrB₄O₇',
        'Symmetry': ['Orthorhombic'],
        'Formula_Units': 4,
        'Atoms_Per_Formula_Unit': 12,  # 1 Sr + 4 B + 7 O
        'Atomic_Number': 10.25,   # (38 + 4*5 + 7*8) / 12
    },
    'YAG': {
        'Display_Label': 'YAG',
        'Symmetry': ['Cubic garnet'],
        'Formula_Units': 8,
        'Atoms_Per_Formula_Unit': 20,  # 3 Y + 5 Al + 12 O
        'Atomic_Number': 13.4,   # (3*39 + 5*13 + 12*8) / 20
    },
    'YAG-Y1': {
        'Display_Label': 'YAG-Y1',
        'Symmetry': ['Cubic garnet'],
        'Formula_Units': 8,
        'Atoms_Per_Formula_Unit': 20,  # 3 Y + 5 Al + 12 O
        'Atomic_Number': 13.4,   # (3*39 + 5*13 + 12*8) / 20
    },
    'YAG-Y2': {
        'Display_Label': 'YAG-Y2',
        'Symmetry': ['Cubic garnet'],
        'Formula_Units': 8,
        'Atoms_Per_Formula_Unit': 20,  # 3 Y + 5 Al + 12 O
        'Atomic_Number': 13.4,   # (3*39 + 5*13 + 12*8) / 20
    },

}






# List of materials and their corresponding display label
Material_Display_Labels = {
    'Ag': 'Ag',
    'Al': 'Al',
    'Ar': 'Ar',
    'Au': 'Au',
    'Be': 'Be',
    'Bi': 'Bi',
    'Co-hcp': 'Co (hcp)',
    'Cu': 'Cu',
    'diamond': 'Diamond',
    'Diamond': 'Diamond',
    'Fe-bcc': 'Fe (bcc)',
    'Fe-hcp': 'Fe (hcp)',
    'He': 'He',
    'Mo': 'Mo',
    'Na': 'Na',
    'Nb': 'Nb',
    'Ne': 'Ne',
    'Ni': 'Ni',
    'Pd': 'Pd',
    'Pt': 'Pt',
    'Re': 'Re',
    'Ta': 'Ta',
    'W': 'W',
    'Zn': 'Zn',
    'MgO': 'MgO',
    'cBN': 'cBN',
    'NaCl-B1': 'NaCl (B1)',
    'NaCl-B2': 'NaCl (B2)',
    'KCl-B2': 'KCl (B2)',
    'Al2O3': 'Al₂O₃',
    'SrB4O7': 'SrB₄O₇',
    'YAG': 'YAG',
    'YAG-Y1': 'YAG-Y1',
    'YAG-Y2': 'YAG-Y2',

}



# List of materials and their corresponding formula units used for volume calculations
Material_Formula_Units = {

    # Face-centered cubic (FCC), Z=4
    'Ag': 4,
    'Al': 4,          
    'Ar': 4,          
    'Au': 4,         
    'Cu': 4,          
    'Pt': 4,         
    'Ne': 4,          
    'NaCl-B1': 4,    
    'Pd': 4,          
    'cBN': 4,      

    # Hexagonal close-packed (HCP), Z=2
    'Be': 2,          
    'Fe-hcp': 2,      
    'Re': 2,          
    'Co-hcp': 2,
    'Ni': 2,
    'Zn': 2, 
    'He': 2,  

    # Body-centered cubic (BCC), Z=2
    'Mo': 2,          
    'Ta': 2,          
    'W': 2,           
    'Fe-bcc': 2,
    'Bi': 2,         
    'Nb': 2,     

    # Diamond cubic, Z=8
    'diamond': 8,     
    'Diamond': 8,

    # Rock salt (B1), Fm-3m, Z=4
    'MgO': 4,      

    # Ruby (corundum, Al2O3), R-3c, Z=6
    'Al2O3': 6,     

    # CsCl-type (B2), Pm-3m, Z=1
    'NaCl-B2': 1,    
    'KCl-B2': 1,    

    # Luminescence standards
    'SrB4O7': 4,      # Orthorhombic, Z=4
    'YAG': 8,         # Y3Al5O12, cubic garnet, Z=8
    'YAG-Y1': 8,
    'YAG-Y2': 8,

}



# List of materials and their corresponding number of atoms per formula unit
Material_Atoms_Per_Formula_Unit = {

    'cBN': 2,   # 1 B + 1 N
    'MgO': 2,   # 1 Mg + 1 O
    'NaCl-B1': 2,   # 1 Na + 1 Cl
    'NaCl-B2': 2,
    'KCl-B2': 2,   # 1 K + 1 Cl
    'Al2O3': 5,   # 2 Al + 3 O
    'SrB4O7': 12,  # 1 Sr + 4 B + 7 O

}



# List of materials and their corresponding atomic numbers
Material_Atomic_Numbers = {

    # Elemental solids
    'Ag': 47,
    'Al': 13,
    'Ar': 18,
    'Au': 79,
    'Be': 4,
    'Bi': 83,
    'Co-hcp': 27,
    'Cu': 29,
    'diamond': 6, 
    'Diamond': 6,
    'Fe-bcc': 26,
    'Fe-hcp': 26,
    'He': 2,
    'Mo': 42,
    'Na': 11,
    'Nb': 41,
    'Ne': 10,
    'Ni': 28,
    'Pd': 46,
    'Pt': 78,
    'Re': 75,
    'Ta': 73,
    'W': 74,
    'Zn': 30,

    # Compounds — effective Z per atom (mean atomic number)
    'MgO': 10.0,   # (12 + 8) / 2
    'cBN': 6.0,   # (5 + 7) / 2
    'NaCl-B1': 14.0,   # (11 + 17) / 2
    'NaCl-B2': 14.0,   # (11 + 17) / 2
    'KCl-B2': 18.0,   # (19 + 17) / 2
    'Al2O3': 10.0,   # (2*13 + 3*8) / 5

}



# List of possible units for volume
Volume_Units = [

    "Å³/unit cell",             # Standard unit cell volume
    "Å³/formula unit",          # Per formula unit (e.g. NaCl pair, MgO pair)
    "Å³/atom",                  # Per atom volume (elements; or truly per-atom for cBN)
    "cm³/mol",                  # Molar volume

]



# List of methods and their corresponding units
Method_Units = {
    "XRD": "Volume",
    "Raman": "Relative Wavenumbers (cm^-1)",
    "Luminescence": "Wavelength (nm)",
}



# This is the data the user will enter in the application
Input_Variable_Names = {
    'Volume',                           # XRD forward
    'Peak_Position_At_A_Pressure',      # Luminescence forward   #AP change to wavelength
    'Wavenumber',                       # Raman forward
    'Pressure',                         # All inverse functions
}



# Variables that have constant values
Constant_Variables = {
    'Temperature_Dependence': 300,  # Datchi 2004 cBN — always room temperature (300 K)
}



# A list of calibration file variables and their corresponding information
    # The display name of the variable is used as the key
        # Variable name used in the functions
        # calibration file variable name
        # method
        # unicode symbol
        # latex symbol
Calibration_File_Variable_Information = {



    ########################################
    # Information About The Paper
    ########################################


    "Study": {
        "Display_Name": "Study",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "study",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Composition": {
        "Display_Name": "Composition",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "composition",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Method": {
        "Display_Name": "Method",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "method",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Technique": {
        "Display_Name": "Technique",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "technique",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Catagory": {
        "Display_Name": "Category",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "category",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Atomic Number": {
        "Display_Name": "Atomic Number",
        "Variable_Name": "Atomic_Number",
        "Calibration_File_Variable_Name": "atomic_number",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": "Z",
        "Latex_Symbol": "Z",
    },
    "DOI": {
        "Display_Name": "DOI",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "doi",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Data Quality Notes": {
        "Display_Name": "Data Quality Notes",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "data_quality_notes",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Notes": {
        "Display_Name": "Notes",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": ["notes", "note"],
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Last Edited": {
        "Display_Name": "Last Edited",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "last_edited",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },



    ########################################
    # Equation of State and Conversion Equation Information
    ########################################

    "Equation of State": {
        "Display_Name": "Equation of State",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "eos",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Order": {
        "Display_Name": "Order",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "order",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Pressure": {
        "Display_Name": "Reference Pressure (P0, GPa)",
        "Variable_Name": ["Initial_Pressure", "P0"],
        "Calibration_File_Variable_Name": "P0",
        "Default_Value": 0,
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": "P₀",
        "Latex_Symbol": "P_{0}",
    },
    "Maximum Pressure": {
        "Display_Name": "Maximum Pressure (GPa)",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "max_pressure",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": "Pₘₐₓ",
        "Latex_Symbol": "P_{Max}",
    },
    "Full Equation": {
        "Display_Name": "Full Equation",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "equation_full",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },



    ########################################
    # Equation Variables
    ########################################

    "V0": {
        "Display_Name": ["Initial Volume (Å³/unit cell)", "Initial Peak Position (nm)", "Initial Raman Shift (cm^-1)"],
        "Variable_Name": ["Initial_Volume__Angstroms_Per_Unit_Cell", "Initial_Peak_Position__Nanometers", "Initial_Peak_Position__Wavenumber"],
        "Calibration_File_Variable_Name": ["V0", "lambda_0", "nu_0", "nu0"],
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": ["V₀", "λ₀", "ν₀"],
        "Latex_Symbol": ["V_{0}", "\\lambda_{0}", "\\nu_{0}"],
    },
    "V0 Uncertainty": { 
        "Display_Name": ["Initial Volume Uncertainty", "Initial Peak Position Uncertainty (nm)", "Initial Wavenumber Uncertainty (cm^-1)"],
        "Variable_Name": ["Initial_Volume__Angstroms_Per_Unit_Cell_Uncertainty", "Initial_Peak_Position__Nanometers_Uncertainty", "Initial_Peak_Position__Wavenumber_Uncertainty"],
        "Calibration_File_Variable_Name": ["V0_unc", "v0_unc"],
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": ["V₀ Uncertainty", "λ₀ Uncertainty", "ν₀ Uncertainty"],
        "Latex_Symbol": [],
    },
    "V0 per Formula Unit": {
        "Display_Name": "Initial Volume (Å³/formula unit)",
        "Variable_Name": "Initial_Volume__Angstroms_Per_Unit_Cell_per_Formula_Unit",  
        "Calibration_File_Variable_Name": "V0_per_formula_unit",
        "Method": "XRD",
        "Unicode_Symbol": "V₀",
        "Latex_Symbol": "",
    },
    "V0 per Atom": {
        "Display_Name": "Initial Volume (Å³/atom)",
        "Variable_Name": "Initial_Volume__Angstroms_Per_Unit_Cell_per_Atom",
        "Calibration_File_Variable_Name": "V0_per_atom",
        "Method": "XRD",
        "Unicode_Symbol": "V₀",
        "Latex_Symbol": "",
    },
    "V0 per Centimeter Cubed per Mole": {
        "Display_Name": "Initial Volume (cm³/mol)",
        "Variable_Name": "Initial_Volume__Angstroms_Per_Unit_Cell_per_cm3_per_mol",
        "Calibration_File_Variable_Name": "V0_cc_mole",
        "Method": "XRD",
        "Unicode_Symbol": "V₀",
        "Latex_Symbol": "",
    },
    "Initial Bulk Modulus": {
        "Display_Name": "Initial Bulk Modulus (K₀, GPa)", 
        "Variable_Name": "K0",
        "Calibration_File_Variable_Name": "K0",
        "Method": ["XRD", "Raman"],
        "Unicode_Symbol": "K₀",
        "Latex_Symbol": "K_{0}",
    },
    "Is The Initial Bulk Modulus Fixed?": {
        "Display_Name": "Is the Initial Bulk Modulus (K₀) Fixed?",
        "Variable_Name": "Is_K0_Fixed",
        "Calibration_File_Variable_Name": ["is_K0_fixed", "is_k0_fixed"],
        "Method": "XRD",
        "Unicode_Symbol": "",
        "Latex_Symbol": "",
    },
    "Initial Bulk Modulus Uncertainty": {
        "Display_Name": "Initial Bulk Modulus Uncertainty (GPa)",
        "Variable_Name": "K0_Uncertainty",
        "Calibration_File_Variable_Name": "K0_unc",
        "Method": "XRD",
        "Unicode_Symbol": "K₀ Uncertainty",
        "Latex_Symbol": "",
    },
    "First Pressure Derivative of the Bulk Modulus": {
        "Display_Name": "K₀'", 
        "Variable_Name": ["K0_Prime", "First_Pressure_Derivative_of_Bulk_Modulus", "First_Pressure_Derivative_Of_Bulk_Modulus", "First_Pressure_Derivative_of_the_K0"],
        "Calibration_File_Variable_Name": "K0_prime",
        "Method": ["XRD", "Raman"],
        "Unicode_Symbol": "K₀'",
        "Latex_Symbol": "K_{0}'",
    },
    "First Pressure Derivative of the Bulk Modulus Uncertainty": {
        "Display_Name": "K₀' Uncertainty",
        "Variable_Name": "K0_Prime_Uncertainty",
        "Calibration_File_Variable_Name": "K0_prime_unc",
        "Method": "XRD",
        "Unicode_Symbol": "K₀' Uncertainty",
        "Latex_Symbol": "",
    },
    "Second Pressure Derivative of the Bulk Modulus": {
        "Display_Name": "K₀''",
        "Variable_Name": ["K0_Double_Prime", "Second_Pressure_Derivative_of_Bulk_Modulus", "Second_Pressure_Derivative_of_the_K0"],
        "Calibration_File_Variable_Name": ["K0_dprime", "K0_double_prime", "K0_doubpe_prime"],
        "Method": "XRD",
        "Unicode_Symbol": "K₀''",
        "Latex_Symbol": "K_{0}''",
    },
    "Second Pressure Derivative of the Bulk Modulus Uncertainty": {
        "Display_Name": "K₀'' Uncertainty",
        "Variable_Name": "K0_Double_Prime_Uncertainty",
        "Calibration_File_Variable_Name": ["K0_dprime_unc", "K0_double_prime_unc", "K0_doubpe_prime_unc"],
        "Method": "XRD",
        "Unicode_Symbol": "K₀'' Uncertainty",
        "Latex_Symbol": "",
    },
    "Pressure Derivative of the Bulk Modulus at Infinite Pressure": {
        "Display_Name": "K'∞",
        "Variable_Name": "K_Infinity_Prime",
        "Calibration_File_Variable_Name": "K_infinity_prime",
        "Method": "XRD",
        "Unicode_Symbol": "K'∞",
        "Latex_Symbol": "K'_{\\infty}",
    },
    "Pressure Derivative of the Bulk Modulus at Infinite Pressure Uncertainty": {
        "Display_Name": "K'∞ Uncertainty",
        "Variable_Name": "K_Infinity_Prime_Uncertainty",
        "Calibration_File_Variable_Name": "K_infinity_prime_unc",
        "Method": "XRD",
        "Unicode_Symbol": "K'∞ Uncertainty",
        "Latex_Symbol": "",
    },
    "eta": {
        "Display_Name": "η", 
        "Variable_Name": "eta",
        "Calibration_File_Variable_Name": "eta",
        "Method": "XRD",
        "Unicode_Symbol": "η",
        "Latex_Symbol": "\\eta",
    },
    "eta Uncertainty": {
        "Display_Name": "η Uncertainty",
        "Variable_Name": "eta_Uncertainty",
        "Calibration_File_Variable_Name": "eta_unc",
        "Method": "XRD",
        "Unicode_Symbol": "η Uncertainty",
        "Latex_Symbol": "",
    },
    "beta": {
        "Display_Name": "β", 
        "Variable_Name": "beta",
        "Calibration_File_Variable_Name": "beta",
        "Method": "XRD",
        "Unicode_Symbol": "β",
        "Latex_Symbol": "\\beta",
    },
    "beta Uncertainty": {
        "Display_Name": "β Uncertainty",  
        "Variable_Name": "beta_Uncertainty",
        "Calibration_File_Variable_Name": "beta_unc",
        "Method": "XRD",
        "Unicode_Symbol": "β Uncertainty",
        "Latex_Symbol": "",
    },
    "psi": {
        "Display_Name": "ψ",   
        "Variable_Name": "psi",
        "Calibration_File_Variable_Name": "psi",
        "Method": "XRD",
        "Unicode_Symbol": "ψ",
        "Latex_Symbol": "\\psi",
    },
    "psi Uncertainty": {
        "Display_Name": "ψ Uncertainty", 
        "Variable_Name": "psi_Uncertainty",
        "Calibration_File_Variable_Name": "psi_unc",
        "Method": "XRD",
        "Unicode_Symbol": "ψ Uncertainty",
        "Latex_Symbol": "",
    },
    "gamma": {
        "Display_Name": "γ",   
        "Variable_Name": "gamma",
        "Calibration_File_Variable_Name": "gamma",
        "Default_Value": 0,
        "Method": "XRD",
        "Unicode_Symbol": "γ",
        "Latex_Symbol": "\\gamma",
    },
    # "Reference Wavelength (nm)": {
    #     "Display_Name": "Reference Wavelength (nm)",
    #     "Variable_Name": "Reference_Wavelength",
    #     "Calibration_File_Variable_Name": "lambda_0",
    #     "Method": ["Luminescence", "Raman"],
    #     "Unicode_Symbol": "λ₀",
    #     "Latex_Symbol": "\\lambda_{0}",
    # },
    "Reference Wavelength Uncertainty (nm)": {
        "Display_Name": "Reference Wavelength Uncertainty (nm)",
        "Variable_Name": "Reference_Wavelength_Uncertainty",
        "Calibration_File_Variable_Name": "lambda_0_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "λ₀ Uncertainty",
        "Latex_Symbol": "",
    },
    # "Reference Frequency": {
    #     "Display_Name": "Reference Frequency (cm⁻¹)", 
    #     "Variable_Name": "Reference_Frequency",
    #     "Calibration_File_Variable_Name": "nu_0",
    #     "Method": ["Luminescence", "Raman"],
    #     "Unicode_Symbol": "ν₀",
    #     "Latex_Symbol": "\\nu_{0}",
    # },
    "A": {
        "Display_Name": "A",
        "Variable_Name": [["Slope_Of_Peak_Position_Change_With_Pressure", "A__Fitting_Parameter"], "A__Fitting_Constant"],
        "Calibration_File_Variable_Name": "A",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "A",
        "Latex_Symbol": "A",
    },
    "A Uncertainty": {
        "Display_Name": "A Uncertainty",
        "Variable_Name": "A_Uncertainty",
        "Calibration_File_Variable_Name": "A_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "A Uncertainty",
        "Latex_Symbol": "",
    },
    "B": {
        "Display_Name": "B",
        "Variable_Name": ["B__Fitting_Parameter", "B__Fitting_Constant"],
        "Calibration_File_Variable_Name": "B",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "B",
        "Latex_Symbol": "B",
    },
    "B Uncertainty": {
        "Display_Name": "B Uncertainty",
        "Variable_Name": "B_Uncertainty",
        "Calibration_File_Variable_Name": "B_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "B Uncertainty",
        "Latex_Symbol": "",
    },
    "C": {
        "Display_Name": "C",
        "Variable_Name": ["C__Fitting_Parameter", "C__Fitting_Constant"],
        "Calibration_File_Variable_Name": "C",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "C",
        "Latex_Symbol": "C",
    },
    "C Uncertainty": {
        "Display_Name": "C Uncertainty",
        "Variable_Name": "C_Uncertainty",
        "Calibration_File_Variable_Name": "C_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "C Uncertainty",
        "Latex_Symbol": "",
    },
    "Initial C": {
        "Display_Name": "Initial C",
        "Variable_Name": "Initial_C",
        "Calibration_File_Variable_Name": "C0",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "C₀",
        "Latex_Symbol": "",
    },
    "Initial C Uncertainty": {
        "Display_Name": "Initial C Uncertainty",
        "Variable_Name": "Initial_C_Uncertainty",
        "Calibration_File_Variable_Name": "C0_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "C₀ Uncertainty",
        "Latex_Symbol": "",
    },
    "D": {
        "Display_Name": "D",
        "Variable_Name": "D__Fitting_Constant",
        "Calibration_File_Variable_Name": "D",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "D",
        "Latex_Symbol": "D",
    },
    "D Uncertainty": {
        "Display_Name": "D Uncertainty",
        "Variable_Name": "D_Uncertainty",
        "Calibration_File_Variable_Name": "D_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "D Uncertainty",
        "Latex_Symbol": "",
    },
    "E": {
        "Display_Name": "E",
        "Variable_Name": "E__Fitting_Constant",
        "Calibration_File_Variable_Name": "E",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "E",
        "Latex_Symbol": "E",
    },
    "E Uncertainty": {
        "Display_Name": "E Uncertainty",
        "Variable_Name": "E_Uncertainty",
        "Calibration_File_Variable_Name": "E_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "E Uncertainty",
        "Latex_Symbol": "",
    },
    "F": {
        "Display_Name": "F",
        "Variable_Name": "F__Fitting_Constant",
        "Calibration_File_Variable_Name": "F",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "F",
        "Latex_Symbol": "F",
    },
    "F Uncertainty": {
        "Display_Name": "F Uncertainty",
        "Variable_Name": "F_Uncertainty",
        "Calibration_File_Variable_Name": "F_unc",
        "Method": ["Luminescence", "Raman"],
        "Unicode_Symbol": "F Uncertainty",
        "Latex_Symbol": "",
    },



    ########################################
    # Reference Pressure Calibration Information
    ########################################

    "Reference Study": {
        "Display_Name": "Reference Study",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_name",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Composition": {
        "Display_Name": "Reference Composition",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_composition",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Method": {
        "Display_Name": "Reference Method",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_method",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Equation of State": {
        "Display_Name": "Reference Equation of State",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_eos",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Equation of State Order": {
        "Display_Name": "Reference Equation of State Order",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_order",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Maximum Pressure": {
        "Display_Name": "Reference Maximum Pressure",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_max_pressure",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Initial Bulk Modulus Fixed?": {
        "Display_Name": "Is the Initial Bulk Modulus Fixed in the Reference Calibration?",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_is_K0_fixed",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference's Reference": {
        "Display_Name": "Reference Study for the Reference Study",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "cal_to_cal",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },

    ########################################
    # Experimental Setup Information
    ########################################

    "Diamond Anvil Cell Type": {
        "Display_Name": "Diamond Anvil Cell Type",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "DAC_type",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Culet Size": {
        "Display_Name": "Culet Size",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "culet",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Gasket Material": {
        "Display_Name": "Gasket Material",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "gasket",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Pressure Transmitting Medium": {
        "Display_Name": "Pressure Transmitting Medium",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "PTM",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Synchrotron Facility": {
        "Display_Name": "Research Facility",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "synchrotron",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Peaks Used": {
        "Display_Name": "Peaks Used to Fit Sample",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "peaks_used_to_fit_sample",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Reference Temperature": {
        "Display_Name": "Reference Temperature",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": ["reference_temperature", "tempertaure"],
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Temperature Range": {
        "Display_Name": "Temperature Range",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "temperature_range",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Pressure Range": {
        "Display_Name": "Pressure Range",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "pressure_range",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },
    "Sample Heating": {
        "Display_Name": "Sample Heating",
        "Variable_Name": None,
        "Calibration_File_Variable_Name": "sample_heating",
        "Method": ["XRD", "Luminescence", "Raman"],
        "Unicode_Symbol": None,
        "Latex_Symbol": None,
    },

}


# A list of the Equation of State functions and conversion functions
    # The display name of the function is used as the key
        # Function name (before "Calculate_")
        # calibration file equation of state name
        # calibration file order
        # method
        # extra prep work
        # unicode equation
        # latex equation
Function_Information = {



    ########################################
    # XRD Functions
    ########################################


    ####################
    # Murnaghan
    ####################

    "First-Order Murnaghan": {
        "Display_Name": "First-Order Murnaghan",
        "Function_Name": "Murnaghan__First_Order__",
        "Calibration_File_EoS_Name": "Murnaghan",
        "Calibration_File_EoS_Order": "1",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = \frac{ K_{0} }{ K_{0}^{'} } \left( \left( \frac{ V_{0} }{ V } \right)^{K_{0}^{'}} - 1 \right)",
    },

    "Second-Order Murnaghan": {
        "Display_Name": "Second-Order Murnaghan",
        "Function_Name": "Murnaghan__Second_Order__",
        "Calibration_File_EoS_Name": "Murnaghan",
        "Calibration_File_EoS_Order": "2",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 2 K_{0} \frac{ { \left( \frac{ V_{0} }{ V } \right)^{q} - 1 } }{ q \left( \left( \frac{ V_{0} }{ V } \right)^{q} + 1 \right) - K_{0}^{'} \left( \left( \frac{ V_{0} }{ V } \right)^{q} - 1 \right) }",
    },


    #####################
    # Birch-Murnaghan
    ####################

    "Second-Order Birch-Murnaghan": {
        "Display_Name": "Second-Order Birch-Murnaghan",
        "Function_Name": "Birch_Murnaghan__Second_Order__",
        "Calibration_File_EoS_Name": "Birch-Murnaghan",
        "Calibration_File_EoS_Order": "2",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = \frac{ 3 }{ 2 } K_{0} \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 7 }{ 3 } } - \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 5 }{ 3 } } \right)",
    },

    "Third-Order Birch-Murnaghan": {
        "Display_Name": "Third-Order Birch-Murnaghan",
        "Function_Name": "Birch_Murnaghan__Third_Order__",
        "Calibration_File_EoS_Name": "Birch-Murnaghan",
        "Calibration_File_EoS_Order": "3",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = \frac{ 3 }{ 2 } K_{0} \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 7 }{ 3 } } - \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 5 }{ 3 } } \right) \left( 1 + \frac{ 3 }{ 4 } \left( K_{0}^{'} - 4 \right) \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 2 }{ 3 } } - 1 \right) \right)",
    },

    "Fourth-Order Birch-Murnaghan": {
        "Display_Name": "Fourth-Order Birch-Murnaghan",
        "Function_Name": "Birch_Murnaghan__Fourth_Order__",
        "Calibration_File_EoS_Name": "Birch-Murnaghan",
        "Calibration_File_EoS_Order": "4",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = \frac{ 3 }{ 2 } K_{0} \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 7 }{ 3 } } - \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 5 }{ 3 } } \right) \left( 1 + \frac{ 3 }{ 4 } \left( K_{0}^{'} - 4 \right) \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 2 }{ 3 } } - 1 \right) + \frac{ 3 }{ 8 } \left( K_{0} K_{0}^{''} + \left( K_{0}^{'} - 4 \right) \left( K_{0}^{'} - 3 \right) + \frac{ 35 }{ 9 } \right) \left( \left( \frac{ V_{0} }{ V } \right)^{ \frac{ 2 }{ 3 } } - 1 \right)^{ 2 } \right)",
    },


    ####################
    # Rydberg-Vinet
    ####################

    "Third-Order Rydberg-Vinet": {
        "Display_Name": "Third-Order Rydberg-Vinet",
        "Function_Name": "Rydberg_Vinet__Third_Order__",
        "Calibration_File_EoS_Name": "Rydberg-Vinet",
        "Calibration_File_EoS_Order": "3",
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \frac{ 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } }{ \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 2 }{ 3 } } } e^{ 1.5 \left( K_{0}^{'} - 1 \right) \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } \right) }",
    },

    "Extended Rydberg-Vinet": {
        "Display_Name": "Extended Rydberg-Vinet",
        "Function_Name": "Rydberg_Vinet__Extended__",
        "Calibration_File_EoS_Name": "Vinet-Extended",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \frac{ 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } }{ \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 2 }{ 3 } } } e^{ \eta \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } \right) + \beta \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } \right)^{ 2 } + \psi \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } \right)^{ 3 } + \gamma \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{ 1 }{ 3 } } \right)^{ 4 } }",
    },


    ####################
    # Adapted Polynomial
    ####################

    "Adapted Polynomial (AP2)": {
        "Display_Name": "Adapted Polynomial",
        "Function_Name": "Adapted_Polynomial__",
        "Calibration_File_EoS_Name": "AP2",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": "AP2",
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \frac{ 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } }{ \left( \frac{ V }{ V_{0} } \right)^{ \frac{5}{3} } } \left( 1 + \left( \frac{3}{2} \left( K_{0}^{'} - 3 \right) +  \ln{ \left( \frac{ 3 K_{0} }{2337} \right)} + \frac{5}{3} \ln{ \left( \frac{ V_{0} }{ Z } \right)} \right) \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) \right) e^{ \left( - \ln{ \left( \frac{ 3 K_{0} }{ 2.337 \cdot 10^{3} } \right)} - \frac{5}{3} \ln{ \left( \frac{ V_{0} }{ Z } \right)} \right) \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) }",
    },


    ####################
    # H02
    ####################

    "Holzapfel (H02)": {
        "Display_Name": "Holzapfel H02",
        "Function_Name": "Holzapfel_H02__",
        "Calibration_File_EoS_Name": "H02",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \frac{ 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } }{ \left( \frac{ V }{ V_{0} } \right)^{ \frac{5}{3} } } e^{ \frac{3}{2} \left( K_{0}^{'} - 3 \right) \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) }",
    },


    ####################
    # H12
    ####################

    "Holzapfel (H12)": {
        "Display_Name": "Holzapfel",
        "Function_Name": "Holzapfel_H12__",
        "Calibration_File_EoS_Name": "H12",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": "AP2",
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \frac{ 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } }{ \left( \frac{ V }{ V_{0} } \right)^{ \frac{5}{3} } } e^{ \left( - \ln{ \left( \frac{ 3 K_{0} }{ 2.337 \cdot 10^{3} } \right)} - \frac{5}{3} \ln{ \left( \frac{ V_{0} }{ Z } \right)} \right) \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) + \left( \frac{3}{2} \left( K_{0}^{'} - 3 \right) + \ln{ \left( \frac{ 3 K_{0} }{ 2.337 \cdot 10^{3} } \right)} + \frac{5}{3} \ln{ \left( \frac{ V_{0} }{ Z } \right)} \right) \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) }",
    },


    ####################
    # Keane
    ####################

    "Keane": {
        "Display_Name": "Keane",
        "Function_Name": "Keane__",
        "Calibration_File_EoS_Name": "Keane",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = K_{0} \left( \left( \frac{ K_{0}^{'} }{ {K_{ \infty }^{'}}^{2} } \right) \left( \left( \frac{ V_{0} }{ V } \right)^{ K_{ \infty }^{'} } - 1 \right) - \left( \frac{ K_{0}^{'} }{ K_{ \infty }^{'} } - 1 \right) \ln{ \left( \frac{ V_{0} }{ V } \right)} \right)",
    },


    ####################
    # Rydberg-Stacey
    ####################

    "Rydberg-Stacey": {
        "Display_Name": "Rydberg-Stacey",
        "Function_Name": "Rydberg_Stacey__",
        "Calibration_File_EoS_Name": "Rydberg-Stacey",
        "Calibration_File_EoS_Order": None,
        "Method": "XRD",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( V \right) = 3 K_{0} \left( \frac{ V }{ V_{0} } \right)^{ - K_{ \infty }^{'} } \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) e^{ \left( \frac{3}{2} K_{0}^{'} - 3 K_{ \infty }^{'} + \frac{1}{2} \right) \left( 1 - \left( \frac{ V }{ V_{0} } \right)^{ \frac{1}{3} } \right) }",
    },



    ########################################
    # Luminescence Functions
    ########################################


    ####################
    # Linear Scale
    ####################

    "Linear Scale - Luminescence": {
        "Display_Name": "Linear Scale",
        "Function_Name": "Linear_Scale__",
        "Calibration_File_EoS_Name": "LinearShift",
        "Calibration_File_EoS_Order": None,
        "Method": "Luminescence",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = \frac{ \lambda - \lambda_{0} }{ A }",
    },


    #####################
    # Power
    ####################

    "Power": {
        "Display_Name": "Power",
        "Function_Name": "Power__",
        "Calibration_File_EoS_Name": "Power",
        "Calibration_File_EoS_Order": None,
        "Method": "Luminescence",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = \frac{A}{B} \left( \left( \frac{ \lambda }{ \lambda_{0} } \right)^{B} - 1 \right)",
    },


    ####################
    # Second-Order Polynomial
    ####################

    "Second-Order Polynomial": {
        "Display_Name": "Second-Order Polynomial",
        "Function_Name": "Second_Order_Polynomial__",
        "Calibration_File_EoS_Name": "Polynomial",
        "Calibration_File_EoS_Order": "2",
        "Method": "Luminescence",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = A \cdot \frac{ \lambda - \lambda_{0} }{ \lambda_{0} } \cdot \left( 1 + B \cdot \frac{ \lambda - \lambda_{0} }{ \lambda_{0} } \right)",
    },


    ####################
    # Third-Order Modified Freud-Ingalls Form
    ####################

    "Third-Order Modified Freud-Ingalls Form": {
        "Display_Name": "Third-Order Modified Freud-Ingalls Form",
        "Function_Name": "Third_Order_Modified_Freud_Ingalls_Form__",
        "Calibration_File_EoS_Name": "HP02Ruby",
        "Calibration_File_EoS_Order": None,
        "Method": "Luminescence",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = \frac{ A }{ B + C } \left(e^{ \left( \frac{ B + C }{ C } \left( 1 - \frac{ \lambda }{ \lambda_{0} }^{ -C } \right) \right)} - 1 \right)",
    },


    ####################
    # SrB4O7
    ####################

    "SrB₄O₇ (Datchi 1997)": {
        "Display_Name": "SrB₄O₇ (Datchi 1997)",
        "Function_Name": "SrB4O7__",
        "Calibration_File_EoS_Name": "Datchi97_Equation",
        "Calibration_File_EoS_Order": None,
        "Method": "Luminescence",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = A \cdot \Delta \lambda \frac{ 1 + B \Delta \lambda }{ 1 + C \Delta \lambda }",
    },



    ########################################
    # Raman Functions
    ########################################


    ####################
    # Splitting of the Diamond Edge
    ####################

    ##########
    # Akahama and Kawamura, 2004 - Diamond - Polynomial
    ##########

    "Akahama & Kawamura 2004 (Diamond, Polynomial)": {
        "Display_Name": "Akahama & Kawamura 2004 (Diamond, Polynomial)",
        "Function_Name": "Akahama_and_Kawamura_2004__Diamond__Polynomial__",
        "Calibration_File_EoS_Name": "Akahama04_Equation",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = A + B \upsilon + C \upsilon^{2}",
    },

    "Akahama & Kawamura 2006 (Diamond, Finite Strain Approximation)": {
        "Display_Name": "Akahama & Kawamura 2006 (Diamond, Finite Strain Approximation)",
        "Function_Name": "Akahama_and_Kawamura_2006__Diamond__Finite_Strain_Approximation__",
        "Calibration_File_EoS_Name": "Akahama06_Equation",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = A \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right) \left( 1 + \frac{ \left( B - 1 \right) \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right) }{2} \right)",
    },

    "Akahama & Kawamura 2010 (Diamond)": {
        "Display_Name": "Akahama & Kawamura 2010 (Diamond)",
        "Function_Name": "Akahama_and_Kawamura_2010__Diamond__",
        "Calibration_File_EoS_Name": "Akahama10_Equation",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"\begin{aligned} P \left( \upsilon , \text{ if } < 200 \text{ GPa} \right) &= A \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right) \left( 1 + \frac{ \left( B - 1 \right) \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right) }{2} \right) \\ P \left( \upsilon , \text{ if } \geq 200 \text{ GPa} \right) &= C - D \upsilon + E \upsilon^{2} \end{aligned}",
    },

    "Eremets et al. 2023 (Diamond)": {
        "Display_Name": "Eremets et al. 2023 (Diamond)",
        "Function_Name": "Eremets_et_al_2023__Diamond__",
        "Calibration_File_EoS_Name": "Eremets_Equation",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = A \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right) + B \left( \frac{ \upsilon - \upsilon_{0} }{ \upsilon_{0} } \right)^{2}",
    },


    ####################
    # Linear Scale
    ####################

    "Linear Scale - Raman": {
        "Display_Name": "Linear Scale",
        "Function_Name": "Linear_Scale__",
        "Calibration_File_EoS_Name": "LinearShift",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \lambda \right) = \frac{ \lambda - \lambda_{0} }{ A }",
    },


    ####################
    # Study Specific
    ####################

    "Evans et al. 2005 (Beryllium, Polynomial)": {
        "Display_Name": "Evans et al. 2005 (Beryllium, Polynomial)",
        "Function_Name": "Evans_et_al_2005__Beryllium__Polynomial__",
        "Calibration_File_EoS_Name": "Raman_Polynomial",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"\upsilon \left( P \right) = A + B P + C P^{2}",
    },

    "Olijnyk et al. 2001 (Beryllium & Rhenium, Polynomial)": {
        "Display_Name": "Olijnyk et al. 2001 (Beryllium & Rhenium, Polynomial)",
        "Function_Name": "Olijnyk_et_al_2001__Beryllium_and_Rhenium__Polynomial__",
        "Calibration_File_EoS_Name": "Raman_Polynomial_OJ",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = \left( \frac{A}{B} \right) \left( {1 - \frac{ \upsilon }{ \upsilon_{0} } }^{- \frac{B}{A^{2}}} \right)",
    },

    "Pease et al. 2025 (Rhenium, Polynomial)": {
        "Display_Name": "Pease et al. 2025 (Rhenium, Polynomial)",
        "Function_Name": "Pease_et_al_2025__Rhenium__Polynomial__",
        "Calibration_File_EoS_Name": "Raman_Polynomial_AP",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = A \left( \upsilon - \upsilon_{0} \right) + B \left( \upsilon - \upsilon_{0} \right)^{2}",
    },

    "Goncharov et al. 2005 (Cubic Boron Nitride)": {
        "Display_Name": "Goncharov et al. 2005 (Cubic Boron Nitride)",
        "Function_Name": "Goncharov_et_al_2005__Cubic_Boron_Nitride__",
        "Calibration_File_EoS_Name": "Raman_Goncharov",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = \frac{ A }{ B } \left( \left( \frac{ \upsilon }{ \upsilon_{0} } \right)^{B} - 1 \right)",
    },

    "Datchi & Canny 2004 (Cubic Boron Nitride)": {
        "Display_Name": "Datchi & Canny 2004 (Cubic Boron Nitride)",
        "Function_Name": "Datchi_and_Canny_2004__Cubic_Boron_Nitride__",
        "Calibration_File_EoS_Name": "RamanDatchi04",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"\upsilon \left( P, T \right) = \upsilon_{0} + A T + B T^{2} + \left( C + D T + E T^{2} \right) P + F P^{2}",
    },

    "Ren et al. 2023 (Cubic Boron Nitride)": {
        "Display_Name": "Ren et al. 2023 (Cubic Boron Nitride)",
        "Function_Name": "Ren_et_al_2023__Cubic_Boron_Nitride__",
        "Calibration_File_EoS_Name": "RamanRen23",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"\upsilon \left( P \right) = \upsilon_{0} + A P + B P^{2}",
    },

    "Datchi et al. 2007 (Cubic Boron Nitride)": {
        "Display_Name": "Datchi et al. 2007 (Cubic Boron Nitride)",
        "Function_Name": "Datchi_et_al_2007__Cubic_Boron_Nitride__",
        "Calibration_File_EoS_Name": "Raman_Datchi",
        "Calibration_File_EoS_Order": None,
        "Method": "Raman",
        "Extra_Prep_Work": None,
        "Unicode_Equation": "",
        "Latex_Equation": r"P \left( \upsilon \right) = \frac{ A }{3.62} \left( \left( \frac{ \upsilon }{ \upsilon_{0} } \right)^{2.876} - 1 \right)",
    },

}



# A list of the form sections and the calibration file variable entry keys they display, in order
    # The section name is the key
        # Entry keys correspond to keys in Calibration_File_Variable_Information
        # Used by the YAML viewer/editor to build collapsible form sections
Calibration_Field_Sections = {

    "Study Information": [
        "Study", "Composition", "Method", "Technique", "Catagory",
        "Atomic Number", "DOI", "Data Quality Notes", "Notes", "Last Edited",
    ],

    "Equation of State": [
        "Equation of State", "Order",
        "Reference Pressure", "Maximum Pressure", "Full Equation",
    ],

    "Equation Variables": [
        "V0", "V0 Uncertainty",
        "V0 per Formula Unit", "V0 per Atom", "V0 per Centimeter Cubed per Mole",
        "Initial Bulk Modulus", "Is The Initial Bulk Modulus Fixed?",
        "Initial Bulk Modulus Uncertainty",
        "First Pressure Derivative of the Bulk Modulus",
        "First Pressure Derivative of the Bulk Modulus Uncertainty",
        "Second Pressure Derivative of the Bulk Modulus",
        "Second Pressure Derivative of the Bulk Modulus Uncertainty",
        "Pressure Derivative of the Bulk Modulus at Infinite Pressure",
        "Pressure Derivative of the Bulk Modulus at Infinite Pressure Uncertainty",
        "eta", "eta Uncertainty",
        "beta", "beta Uncertainty",
        "psi", "psi Uncertainty",
        "gamma",
        "Reference Wavelength Uncertainty (nm)",
        "A", "A Uncertainty",
        "B", "B Uncertainty",
        "C", "C Uncertainty",
        "Initial C", "Initial C Uncertainty",
        "D", "D Uncertainty",
        "E", "E Uncertainty",
        "F", "F Uncertainty",
    ],

    "Pressure Calibration Reference": [
        "Reference Study", "Reference Composition", "Reference Method",
        "Reference Equation of State", "Reference Equation of State Order",
        "Reference Maximum Pressure", "Reference Initial Bulk Modulus Fixed?",
        "Reference's Reference",
    ],

    "Experimental Setup": [
        "Diamond Anvil Cell Type", "Culet Size", "Gasket Material",
        "Pressure Transmitting Medium", "Synchrotron Facility", "Peaks Used",
        "Reference Temperature", "Temperature Range", "Pressure Range", "Sample Heating",
    ],

}



# A set of entry keys (from Calibration_File_Variable_Information) that use a multi-line text input
Calibration_Multiline_Fields = {
    "Data Quality Notes",
    "Notes",
    "Full Equation",
}



# Derived lookups — built automatically from Function_Information, never edit these directly
    # (display_name, order) → display_name  (for looking up from a calibration entry)
Equation_Entry_From_Calibration_Entry = {(e['Calibration_File_EoS_Name'], e['Calibration_File_EoS_Order'], e['Method']): display_name for display_name, e in Function_Information.items()}
    # display_name → group_key used by Create_List_Of_Functions_And_Variables  (strips the trailing __)
EoS_Group_Key = {display_name: e['Function_Name'][:-2] for display_name, e in Function_Information.items()}
    # (yaml_eos, yaml_order) → group_key  (direct replacement for YAML_EOS_TO_..._KEY)
EoS_Group_Key_From_Calibration = {(e['Calibration_File_EoS_Name'], e['Calibration_File_EoS_Order'], e['Method']): e['Function_Name'][:-2] for e in Function_Information.values()}
    # set of yaml_eos names that need special handling (e.g. AP2 volume unit conversion)
Equation_Required_Extra_Prep_Work = {e['Calibration_File_EoS_Name'] for e in Function_Information.values() if e['Extra_Prep_Work'] is not None}



# ── Derived lookups from Calibration_File_Variable_Information ──────────────────────
# Built automatically — never edit these directly
# Expansion rules:
#   - Method is a list of N → all other list fields have N items aligned by position
#   - A non-list field value applies to ALL method positions
#   - Variable_Name[i] can itself be a list → multiple param names for that method
#   - Calibration_File_Variable_Name as a list → alternative calibration keys to try in order (not per-method)

def Build_Variable_Lookups():

    Calibration_Key_To_Entry_Key_Local = {}   # any calibration file key → display entry key
    Variable_Name_To_Calibration_Keys_Local = {}   # function param name → [calibration file keys to try in order]
    Function_Variable_Names_And_Calibration_Key_Names_Local = {}   # function param name → primary calibration file key
                                                           # replaces the old Function_Variable_Names_And_Calibration_Key_Names

    for Entry_Key, Entry in Calibration_File_Variable_Information.items():

        # Normalize Method to a list of N methods
        Methods = Entry["Method"] if isinstance(Entry["Method"], list) else [Entry["Method"]]

        # Calibration_File_Variable_Name: list = alternatives to try in order; string = one key
        Raw_Yaml = Entry["Calibration_File_Variable_Name"]
        Calibration_Keys = Raw_Yaml if isinstance(Raw_Yaml, list) else [Raw_Yaml]
        Primary_Calibration_Key = Calibration_Keys[0] if Calibration_Keys else None

        # Variable_Name: if not a list, the single value applies to all method positions
        Raw_Variable_Name = Entry["Variable_Name"]
        Variable_Names_By_Method = [Raw_Variable_Name] * len(Methods) if not isinstance(Raw_Variable_Name, list) else list(Raw_Variable_Name)

        # Map every alternative calibration key back to this entry
        for Calibration_Key in Calibration_Keys:
            if Calibration_Key is not None:
                Calibration_Key_To_Entry_Key_Local[Calibration_Key] = Entry_Key

        # Expand variable names per method position
        for Method_Index in range(len(Methods)):
            Variable_Name_At_Index = Variable_Names_By_Method[Method_Index] if Method_Index < len(Variable_Names_By_Method) else Variable_Names_By_Method[0]
            # Variable_Name_At_Index may itself be a list (multiple param names at this method position)
            Variable_Names = Variable_Name_At_Index if isinstance(Variable_Name_At_Index, list) else ([Variable_Name_At_Index] if Variable_Name_At_Index is not None else [])
            for Variable_Name in Variable_Names:
                Variable_Name_To_Calibration_Keys_Local[Variable_Name] = Calibration_Keys
                if Primary_Calibration_Key is not None:
                    Function_Variable_Names_And_Calibration_Key_Names_Local[Variable_Name] = Primary_Calibration_Key

    return Calibration_Key_To_Entry_Key_Local, Variable_Name_To_Calibration_Keys_Local, Function_Variable_Names_And_Calibration_Key_Names_Local


Calibration_Key_To_Entry_Key, Variable_Name_To_Calibration_Keys, Function_Variable_Names_And_Calibration_Key_Names = Build_Variable_Lookups()
