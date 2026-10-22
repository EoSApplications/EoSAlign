# Load libraries
    # Load local functions from local files
from EoS_Math.Build_Dataframe import Calibration_Metadata
from Reference_Values_And_Units import Volume_Units, Pressure_Units


# Raw dataframe columns store the volume unit with "(" ")" removed, spaces as "_" and "/" as "_per_"
# (see Build_Dataframe.py). Map that sanitized form back to the unit as the user sees it.
Sanitized_Volume_Units = {Unit.replace("(", "").replace(")", "").replace(" ", "_").replace("/", "_per_"): Unit for Unit in Volume_Units}


# Turn a unit string into "Name (abbreviation)". Volume units like "Å³/unit cell" are only the
# abbreviation, so "Volume" is added. Other units (e.g. "Wavelength (nm)") already have both.
def Get_Unit_Display_Name(Unit_String):
    if Unit_String in Volume_Units:
        return f"Volume ({Unit_String})"
    return Unit_String


# Build the "Input:\n{Unit name (abbreviation)}" label, or "Input Uncertainty:\n{...}" for uncertainty columns
def Build_Input_Label(Unit_String, Is_Uncertainty, Prefix="Input"):
    Heading = f"{Prefix} Uncertainty:" if Is_Uncertainty else f"{Prefix}:"
    return f"{Heading}\n{Get_Unit_Display_Name(Unit_String)}"




# Add the abbreviation to the unit word of a "{Unit}_From_..." column. "Volume" from the method units
# has no abbreviation of its own, so the standard volume unit is added. Other units (e.g.
# "Wavelength (nm)") already include theirs.
def Get_Observable_Display_Name(Unit_Label):
    if Unit_Label == "Volume":
        return f"Volume ({Volume_Units[0]})"
    return Unit_Label


# Describe a calibration as "{Study} | {composition} | {method}" using the calibration metadata.
# With Include_Details the rest of the study information is added to the end (used for saved files).
def Describe_Study(Study_Key, Metadata_By_Calibration_Key, Include_Details=False):
    metadata = Metadata_By_Calibration_Key.get(Study_Key, {})
    Description = f"{metadata.get('Study', Study_Key)} | {metadata.get('Composition', '')} | {metadata.get('Method', '')}"
    if Include_Details and metadata:
        Description += Build_Study_Details_For_Save(Study_Key, Metadata_By_Calibration_Key, Include_Method=False)
    return Description


# Split a "{Unit}_From_{Study}" / "{Unit}_From_{Study}_({Comp}_{Method})" column name into (unit, study key)
def Split_From_Column_Name(Column_Name):
    unit_label, study_and_rest = Column_Name.split("_From_", 1)
    study = study_and_rest.rsplit("_(", 1)[0] if "_(" in study_and_rest else study_and_rest
    return unit_label, study


# Build the preview label for every column in a dataframe. Returns {raw_column_name: preview_label}.
# This is the single place base column labels are created. Labels may contain "\n" so they wrap in
# the preview table's headers. Raw names come from EoS_Math/Build_Dataframe.py, so the parsing below
# must stay in sync with how that file names its columns.
def Get_Preview_Column_Labels(Columns, Metadata_By_Calibration_Key=None, Include_Study_Details=False):

    if Metadata_By_Calibration_Key is None:
        Metadata_By_Calibration_Key = Calibration_Metadata

    Column_Set = set(Columns)
    # Look through the columns for the conversion steps so uncertainty columns, whose raw names do
    # not include the study details, can be matched to the value column they belong to
    Observable_From_Studies = {}   # study key -> unit of its "{Unit}_From_{Study}" column
    Pressure_From_Studies = set()
    Assumed_Studies = None         # (intermediate study key, target study key)
    for Column_Name in Columns:
        if Column_Name.startswith("Pressure_From_"):
            Pressure_From_Studies.add(Split_From_Column_Name(Column_Name)[1])
        elif "_From_" in Column_Name:
            Unit_Label, Study_Key = Split_From_Column_Name(Column_Name)
            Observable_From_Studies[Study_Key] = Unit_Label
        elif Column_Name.startswith("Assumed_Equal_Pressure_"):
            Parts = Column_Name.replace("Assumed_Equal_Pressure_", "").split("_=_")
            if len(Parts) == 2:
                Assumed_Studies = (Parts[0], Parts[1])

    Preview_Labels = {}
    for Column_Name in Columns:

        if Column_Name.startswith("Measured_") or Column_Name.startswith("Input_Pressure_"):
            # Input values as entered (pressure, or non-pressure units that did not need conversion)
            Is_Uncertainty = Column_Name.endswith("_Unc")
            if Column_Name.startswith("Input_Pressure_"):
                Unit_String = Pressure_Units[0]
            else:
                Unit_String = Column_Name[len("Measured_"):].removesuffix("_Unc").removesuffix("_Input")
            Preview_Labels[Column_Name] = Build_Input_Label(Unit_String, Is_Uncertainty)

        elif "_From_" in Column_Name and not Column_Name.startswith("Pressure_From_"):
            # Intermediate observable: "{Unit}_From_{Study}" or "{Unit}_From_{Study}_({Comp}_{Method})"
            Unit_Label, Study_Key = Split_From_Column_Name(Column_Name)
            Preview_Labels[Column_Name] = f"{Get_Observable_Display_Name(Unit_Label)} From:\n{Describe_Study(Study_Key, Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Column_Name.startswith("Pressure_From_") and "(" in Column_Name:
            # Pressure conversion steps with composition/method info
            Study_Key = Split_From_Column_Name(Column_Name)[1]
            Preview_Labels[Column_Name] = f"{Pressure_Units[0]} From:\n{Describe_Study(Study_Key, Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Column_Name.startswith("Assumed_Equal_Pressure_"):
            # Assumption step showing pressure equality between two studies
            Parts = Column_Name.replace("Assumed_Equal_Pressure_", "").split("_=_")
            if len(Parts) == 2:
                Study_1 = Describe_Study(Parts[0], Metadata_By_Calibration_Key, Include_Study_Details)
                Study_2 = Describe_Study(Parts[1], Metadata_By_Calibration_Key, Include_Study_Details)
                Preview_Labels[Column_Name] = f"Assumption:\n{Pressure_Units[0]} = {Pressure_Units[0]}\n{Study_1} = {Study_2}"
            else:
                Preview_Labels[Column_Name] = Column_Name.replace("_", " ")

        elif Assumed_Studies is not None and Column_Name == f"Pressure_{Assumed_Studies[1]}":
            # The assumed pressure saved again under the target study's name (right after the assumption columns)
            Preview_Labels[Column_Name] = f"{Pressure_Units[0]} From:\n{Describe_Study(Assumed_Studies[1], Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Assumed_Studies is not None and Column_Name == f"P_Unc_{Assumed_Studies[1]}":
            Preview_Labels[Column_Name] = f"{Pressure_Units[0]} Uncertainty From:\n{Describe_Study(Assumed_Studies[1], Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Column_Name.startswith("Pressure_") and not Column_Name.startswith("Pressure_From_"):
            # Output pressure columns -- look up study display name from metadata
            cal_name = Column_Name[len("Pressure_"):]
            metadata = Metadata_By_Calibration_Key.get(cal_name, {})
            study = metadata.get("Study", cal_name)
            composition = metadata.get("Composition", "")
            Study_Text = Describe_Study(cal_name, Metadata_By_Calibration_Key, True) if Include_Study_Details and metadata else f"{study} | {composition}"
            Preview_Labels[Column_Name] = f"Output:\n{Pressure_Units[0]}\n{Study_Text}"

        elif Column_Name.startswith("P_Unc_") and f"Pressure_{Column_Name[len('P_Unc_'):]}" in Column_Set:
            # Uncertainty of an output pressure column (has a matching Pressure_<cal> column)
            cal_name = Column_Name[len("P_Unc_"):]
            metadata = Metadata_By_Calibration_Key.get(cal_name, {})
            study = metadata.get("Study", cal_name)
            composition = metadata.get("Composition", "")
            Study_Text = Describe_Study(cal_name, Metadata_By_Calibration_Key, True) if Include_Study_Details and metadata else f"{study} | {composition}"
            Preview_Labels[Column_Name] = f"Output Uncertainty:\n{Pressure_Units[0]}\n{Study_Text}"

        elif Column_Name == "P_Unc_Assumed" and Assumed_Studies is not None:
            # Uncertainty of the assumed-equal pressure column
            Study_1 = Describe_Study(Assumed_Studies[0], Metadata_By_Calibration_Key, Include_Study_Details)
            Study_2 = Describe_Study(Assumed_Studies[1], Metadata_By_Calibration_Key, Include_Study_Details)
            Preview_Labels[Column_Name] = f"Assumption Uncertainty:\n{Pressure_Units[0]} Uncertainty = {Pressure_Units[0]} Uncertainty\n{Study_1} = {Study_2}"

        elif Column_Name.startswith("P_Unc_") and Column_Name[len("P_Unc_"):] in Pressure_From_Studies:
            # Uncertainty of a "Pressure_From_<study>" conversion step
            Study_Key = Column_Name[len("P_Unc_"):]
            Preview_Labels[Column_Name] = f"{Pressure_Units[0]} Uncertainty From:\n{Describe_Study(Study_Key, Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Column_Name.startswith("V_Unc_") and Column_Name[len("V_Unc_"):] in Observable_From_Studies:
            # Uncertainty of a "{Unit}_From_<study>" conversion step
            Study_Key = Column_Name[len("V_Unc_"):]
            Preview_Labels[Column_Name] = f"{Get_Observable_Display_Name(Observable_From_Studies[Study_Key])} Uncertainty From:\n{Describe_Study(Study_Key, Metadata_By_Calibration_Key, Include_Study_Details)}"

        elif Column_Name.startswith("Output: "):
            Label = Column_Name[len("Output: "):]
            if Label.endswith("_Unc"):
                Preview_Labels[Column_Name] = f"Output Unc:\n{Label[:-4]}"
            else:
                Preview_Labels[Column_Name] = f"Output:\n{Label}"

        elif Column_Name in ('Volume_A3_UnitCell', 'Volume_A3_UnitCell_Unc'):
            # The user's input after conversion to Å³/unit cell (this is the column used for calculations)
            Is_Uncertainty = Column_Name.endswith("_Unc")
            Preview_Labels[Column_Name] = Build_Input_Label("Å³/unit cell", Is_Uncertainty, Prefix="Converted Input")

        elif Column_Name.startswith("Input_") and not Column_Name.startswith("Input_Pressure_"):
            # Input values as the user typed them, before conversion to Å³/unit cell (e.g. cm³/mol)
            Is_Uncertainty = Column_Name.endswith("_Unc")
            Sanitized_Unit = Column_Name[len("Input_"):].removesuffix("_Unc")
            Unit_String = Sanitized_Volume_Units.get(Sanitized_Unit, Sanitized_Unit.replace("_per_", "/").replace("_", " "))
            Preview_Labels[Column_Name] = Build_Input_Label(Unit_String, Is_Uncertainty)

        else:
            # Default formatting: replace underscores with spaces
            if " | " in Column_Name:
                Parts = Column_Name.split(" | ")
                Preview_Labels[Column_Name] = "\n".join(Parts)
            else:
                Preview_Labels[Column_Name] = Column_Name.replace("_", " ")

    # Return the preview labels for use as table headers
    return Preview_Labels


# Build the {Pressure_<key> -> Pressure_<study> | <comp> | <method> | ...} rename map used by the
# CSV export, from a dataframe's own columns and the loaded Calibration_Metadata. Kept as its own
# module-level function so it can be unit-tested against a synthetic dataframe + metadata dict
# without needing a live Qt widget -- see tests/export/.
def Build_Pressure_Column_Rename_Map(DataFrame_Columns, Metadata_By_Calibration_Key):

    Rename_Map = {}
    for col in DataFrame_Columns:
        if col.startswith("Pressure_") and not col.startswith("Pressure_From_"):
            cal_name = col[len("Pressure_"):]
            meta = Metadata_By_Calibration_Key.get(cal_name, {})
            if meta:
                study = meta.get("Study", cal_name)
                comp = meta.get("Composition", "")
                method = meta.get("Method", "")
                eos = meta.get("Equation of State", "")
                k0_fixed = meta.get("Is The Initial Bulk Modulus Fixed?", "")
                cal_to = meta.get("Reference Study", "")
                max_p = meta.get("Maximum Pressure", "")
                ptm = meta.get("Pressure Transmitting Medium", "")
                Rename_Map[col] = f"Pressure_{study} | {comp} | {method} | {eos} | K0 Fixed: {k0_fixed} | cal_to: {cal_to} | Max Pressure: {max_p} | PTM: {ptm}"
    # Return the column rename map for use with DataFrame.rename(columns=...)
    return Rename_Map


# Build the extra study information that is added to the end of a study's description in saved files
def Build_Study_Details_For_Save(Study_Key, Metadata_By_Calibration_Key, Include_Method=True):
    meta = Metadata_By_Calibration_Key.get(Study_Key, {})
    method = meta.get("Method", "")
    eos = meta.get("Equation of State", "")
    k0_fixed = meta.get("Is The Initial Bulk Modulus Fixed?", "")
    cal_to = meta.get("Reference Study", "")
    max_p = meta.get("Maximum Pressure", "")
    ptm = meta.get("Pressure Transmitting Medium", "")
    Method_Text = f" | {method}" if Include_Method else ""
    return f"{Method_Text} | {eos} | K0 Fixed: {k0_fixed} | cal_to: {cal_to} | Max Pressure: {max_p} | PTM: {ptm}"


# Build the save label for every column in a dataframe. Returns {raw_column_name: save_label} for
# use with DataFrame.rename(columns=...). Each save label is the preview label with the full study
# information wherever a study is listed, and with every "\n" replaced by a space.
def Get_Save_Column_Labels(Columns, Metadata_By_Calibration_Key=None):

    if Metadata_By_Calibration_Key is None:
        Metadata_By_Calibration_Key = Calibration_Metadata

    Columns = list(Columns)
    Preview_Labels = Get_Preview_Column_Labels(Columns, Metadata_By_Calibration_Key, Include_Study_Details=True)

    # Return the save labels
    return {Column_Name: Preview_Labels[Column_Name].replace("\n", " ") for Column_Name in Columns}
