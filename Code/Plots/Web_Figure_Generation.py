# Pyodide-safe bridge between the website's EoSAlign port and the standalone
# figure generation scripts (Plot_Observable_Vs_Pressure.py etc.) — mirrors
# Plots/Generate_Figures.py but with every Qt (QSettings) and threading/disk
# dependency removed, since the browser has neither. Figures are produced as
# in-memory PNG bytes instead of files.
#
# Per-study saved color/marker overrides (QSettings-backed on the desktop)
# are not supported here — the website always uses the auto color/marker
# palette, consistent with the rest of EoSAlign's website scope (no
# multi-run / custom-reference override either; see EoSAlign.js).

# Load standard libraries
import importlib
from io import BytesIO

# Load third-party libraries
import numpy as np




# Module and export constants


# Generation order: all figure modules this app can produce
Default_Module_Names = [
    "Plot_Observable_Vs_Pressure",
    "Plot_All_EoS_Overlay_Absolute_Pressure_Difference",
    "Plot_All_EoS_Overlay_Percent_Pressure_Difference",
    "Plot_Pressure_Scale_Disagreement",
    "Plot_Individual_Absolute_Pressure_Difference",
    "Plot_Individual_Percent_Pressure_Difference",
    "Plot_Summary_Observable_Vs_Pressure_And_Overlay",
]

# Display order: summary before the individual panels for better load priority
Ui_Module_Order = [
    "Plot_Observable_Vs_Pressure",
    "Plot_All_EoS_Overlay_Absolute_Pressure_Difference",
    "Plot_All_EoS_Overlay_Percent_Pressure_Difference",
    "Plot_Pressure_Scale_Disagreement",
    "Plot_Summary_Observable_Vs_Pressure_And_Overlay",
    "Plot_Individual_Absolute_Pressure_Difference",
    "Plot_Individual_Percent_Pressure_Difference",
]

# These figures are only meaningful when the input data is already in pressure units
Pressure_Only_Modules = {
    "Plot_All_EoS_Overlay_Absolute_Pressure_Difference",
    "Plot_All_EoS_Overlay_Percent_Pressure_Difference",
    "Plot_Pressure_Scale_Disagreement",
    "Plot_Individual_Absolute_Pressure_Difference",
    "Plot_Individual_Percent_Pressure_Difference",
    "Plot_Summary_Observable_Vs_Pressure_And_Overlay",
}

# Human-readable section titles for each figure type
Figure_Titles = {
    "observable_vs_pressure": "Measured Value vs Pressure",
    "all_eos_overlay_absolute_pressure_difference": "Pressure Difference (GPa) - All EoS",
    "all_eos_overlay_percent_pressure_difference": "Pressure Difference (%) - All EoS",
    "pressure_scale_disagreement": "Pressure Scale Disagreement",
    "individual_absolute_pressure_difference": "Individual EoS (Pdiff)",
    "individual_percent_pressure_difference": "Individual EoS (Pdiff %)",
    "summary_observable_vs_pressure_and_overlay": "Combined Summary",
}

# Valid export theme and background option identifiers
Export_Theme_Options = ("light", "dark")
Export_Background_Options = ("transparent", "white", "black")

Export_Background_Colors = {
    "transparent": "none",
    "white": "#FFFFFF",
    "black": "#000000",
}




# Study style helpers (no QSettings — always the auto palette)


# Return the default color for a comparison study at a given palette index
def Local__Default_Study_Color(Index):
    from Themes.Plot_Style_Options import AUTO_COLORS

    if AUTO_COLORS:
        return AUTO_COLORS[Index % len(AUTO_COLORS)]
    return "#1f77b4"


# Return the default marker for a comparison study at a given palette index
def Local__Default_Study_Marker(Index):
    from Themes.Plot_Style_Options import AUTO_MARKERS, DEFAULT_MARKER

    if AUTO_MARKERS:
        return AUTO_MARKERS[Index % len(AUTO_MARKERS)]
    return DEFAULT_MARKER




# AppFigureConfig class


# Minimal config_module interface compatible with all standalone figure scripts
class AppFigureConfig:

    Save_Formats = ["png"]
    Isolate_Exports = False
    Individuals_Across = 4
    Individual_Panel_Gap__Inches = 0.90
    Individual_Render_Dpi = 500

    def __init__(self, Show_Bands=True, Show_Error_Bars=False, Show_Grid=False,
                 Theme_Overrides=None, Ps_Overrides=None, Save_Transparent=False,
                 Save_Face_Color="none"):
        self.Show_Bands = bool(Show_Bands)
        self.Show_Error_Bars = bool(Show_Error_Bars)
        self.Show_Grid = bool(Show_Grid)
        self.Theme_Overrides = dict(Theme_Overrides) if Theme_Overrides else {}
        self.Ps_Overrides = dict(Ps_Overrides) if Ps_Overrides else {}
        self.Save_Transparent = bool(Save_Transparent)
        self.Save_Face_Color = Save_Face_Color

    def Build_Inputs(self):
        return {}




# Dataset builder


# Return the y-axis label string for the observable measurement for a given method
def Observable_Label(Method):
    from Reference_Values_And_Units import Method_Units

    if Method == "XRD":
        return "Volume (Å³/unit cell)"
    return Method_Units.get(Method, "Observable")


# Parse a raw maximum pressure value into a (pressure_float, was_finite) pair
def Parse_Max_Pressure(Raw_Value):
    try:
        Parsed_Value = float(Raw_Value)
    except (TypeError, ValueError):
        return np.inf, False
    if np.isfinite(Parsed_Value):
        return Parsed_Value, True
    return np.inf, False


# Convert the app's computed dataframe to the dataset format expected by all figure scripts.
# Identical to Generate_Figures.Build_Dataset_From_App_Data except per-study color/marker
# always comes from the auto palette (no QSettings-backed per-study overrides on the website).
def Build_Dataset_From_App_Data(Df, Composition, Method, Reference_Key, Selected_Keys, Input_Mode, Original_Study_Key=None):
    from EoS_Math.Build_Dataframe import Calibration_Metadata, Calibration_Functions
    from Reference_Values_And_Units import Method_Units
    from Plot_Utilities import Build_Eos_Curve_Cache

    Input_Cols = [Col for Col in Df.columns if "Input" in Col and "_Unc" not in Col]
    if not Input_Cols:
        Input_Cols = [Col for Col in Df.columns if "Measured" in Col and "_Unc" not in Col]
    Input_Col = Input_Cols[0] if Input_Cols else Df.columns[0]

    P_Input__GPa = np.asarray(Df[Input_Col].values, dtype=float)
    Input_Unc_Col = f"{Input_Col}_Unc"
    P_Input_Unc__GPa = np.asarray(Df[Input_Unc_Col].values, dtype=float) if Input_Unc_Col in Df.columns else None

    P_Ref__GPa = None
    P_Ref_Unc__GPa = None
    if Reference_Key:
        P_Ref_Col = f"Pressure_{Reference_Key}"
        if P_Ref_Col in Df.columns:
            P_Ref__GPa = np.asarray(Df[P_Ref_Col].values, dtype=float)
        P_Ref_Unc_Col = f"P_Unc_{Reference_Key}"
        if P_Ref_Unc_Col in Df.columns:
            P_Ref_Unc__GPa = np.asarray(Df[P_Ref_Unc_Col].values, dtype=float)

    if P_Ref__GPa is None:
        P_Ref__GPa = P_Input__GPa
    if P_Ref_Unc__GPa is None:
        P_Ref_Unc__GPa = P_Input_Unc__GPa

    if Input_Mode != "Pressure (GPa)":
        Observable = np.asarray(Df[Input_Col].values, dtype=float)
        Obs_Unc_Col = f"{Input_Col}_Unc"
        Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float) if Obs_Unc_Col in Df.columns else None
    else:
        Method_Unit = Method_Units.get(Method, "")
        Obs_Col = None
        Obs_Unc = None
        if Reference_Key and Method_Unit:
            Candidate_Prefix = f"{Method_Unit}_From_{Reference_Key}"
            Matches = [Col for Col in Df.columns if Col == Candidate_Prefix or Col.startswith(Candidate_Prefix + "_")]
            if Matches:
                Obs_Col = Matches[0]
        if Obs_Col:
            Observable = np.asarray(Df[Obs_Col].values, dtype=float)
            Obs_Unc_Col = f"V_Unc_{Reference_Key}" if Reference_Key else ""
            if Obs_Unc_Col and Obs_Unc_Col in Df.columns:
                Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float)
            else:
                Fallback_Obs_Unc_Col = f"{Obs_Col}_Unc"
                Obs_Unc = np.asarray(Df[Fallback_Obs_Unc_Col].values, dtype=float) if Fallback_Obs_Unc_Col in Df.columns else None
        elif Reference_Key and Reference_Key in Calibration_Functions:
            Unused_Forward_Func, Inverse_Func = Calibration_Functions[Reference_Key]
            Observable = np.array(
                [float(Inverse_Func(P__GPa)) if np.isfinite(P__GPa) and P__GPa > 0 else np.nan for P__GPa in P_Ref__GPa],
                dtype=float,
            )
            Obs_Unc_Col = f"V_Unc_{Reference_Key}"
            Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float) if Obs_Unc_Col in Df.columns else None
        else:
            Observable = P_Ref__GPa.copy()
            Obs_Unc = None

    Eos_List = []

    if Reference_Key and Reference_Key in Calibration_Metadata:
        Ref_Meta = Calibration_Metadata.get(Reference_Key, {})
        Ref_P_Max__GPa, Ref_P_Max_Specified = Parse_Max_Pressure(Ref_Meta.get("Maximum Pressure"))
        Ref_Pmax_Label = f"{Ref_P_Max__GPa:.0f} GPa" if Ref_P_Max_Specified else "N/A"
        Eos_List.append({
            "key": Reference_Key,
            "data": P_Ref__GPa.copy(),
            "author": Ref_Meta.get("Study", Reference_Key),
            "form": Ref_Meta.get("Equation of State", ""),
            "K0_fixed": str(Ref_Meta.get("is_K0_fixed", False)),
            "p_max": Ref_P_Max__GPa,
            "ptm": Ref_Meta.get("PTM", ""),
            "cal_to": Ref_Meta.get("cal_to_name", ""),
            "label": (
                f"{Ref_Meta.get('Study', Reference_Key)} | "
                f"{Ref_Meta.get('Equation of State', '')} | {Ref_Pmax_Label}"
            ),
            "p_max_specified": Ref_P_Max_Specified,
            "p0": Ref_Meta.get("P0"),
            "pressure_unc": P_Ref_Unc__GPa,
            "curve_cache": Build_Eos_Curve_Cache(P_Input__GPa, P_Ref__GPa, Ref_P_Max__GPa, Ref_P_Max_Specified, P_Unc=P_Ref_Unc__GPa, X_Unc=P_Input_Unc__GPa),
        })

    Comparison_Index = 0
    for Key in (Selected_Keys or []):
        if Key == Reference_Key:
            continue
        P_Col = f"Pressure_{Key}"
        if P_Col not in Df.columns:
            continue
        Meta = Calibration_Metadata.get(Key, {})
        P_Max__GPa, P_Max_Specified = Parse_Max_Pressure(Meta.get("Maximum Pressure"))
        Pmax_Label = f"{P_Max__GPa:.0f} GPa" if P_Max_Specified else "N/A"
        P_Eos__GPa = np.asarray(Df[P_Col].values, dtype=float)
        P_Unc_Col = f"P_Unc_{Key}"
        P_Unc = np.asarray(Df[P_Unc_Col].values, dtype=float) if P_Unc_Col in Df.columns else None
        Eos_List.append({
            "key": Key,
            "data": P_Eos__GPa,
            "author": Meta.get("Study", Key),
            "form": Meta.get("Equation of State", ""),
            "K0_fixed": str(Meta.get("is_K0_fixed", False)),
            "p_max": P_Max__GPa,
            "ptm": Meta.get("PTM", ""),
            "cal_to": Meta.get("cal_to_name", ""),
            "label": f"{Meta.get('Study', Key)} | {Meta.get('Equation of State', '')} | {Pmax_Label}",
            "p_max_specified": P_Max_Specified,
            "p0": Meta.get("P0"),
            "color": Local__Default_Study_Color(Comparison_Index),
            "marker": Local__Default_Study_Marker(Comparison_Index),
            "pressure_unc": P_Unc,
            "curve_cache": Build_Eos_Curve_Cache(P_Input__GPa, P_Eos__GPa, P_Max__GPa, P_Max_Specified, P_Unc=P_Unc, X_Unc=P_Input_Unc__GPa),
        })
        Comparison_Index += 1

    First_Key = Reference_Key
    if First_Key:
        First_Meta = Calibration_Metadata.get(First_Key, {})
        Fp_Max__GPa, Fp_Specified = Parse_Max_Pressure(First_Meta.get("Maximum Pressure"))
        Fp_Label = f"{Fp_Max__GPa:.0f} GPa" if Fp_Specified else "N/A"
        First_Label = f"{First_Meta.get('Study', First_Key)} | {First_Meta.get('Equation of State', '')} | {Fp_Label}"
    else:
        First_Label = ""

    Label_Source_Key = Original_Study_Key or First_Key
    if Label_Source_Key:
        Input_Label_Meta = Calibration_Metadata.get(Label_Source_Key, {})
        Input_Label_Study = Input_Label_Meta.get("Study", Label_Source_Key)
        Input_Label_Comp = Input_Label_Meta.get("Composition", "").strip()
        if Input_Label_Comp:
            X_Pressure_Label = f"Input Pressure ({Input_Label_Study}, {Input_Label_Comp}) (GPa)"
        else:
            X_Pressure_Label = f"Input Pressure ({Input_Label_Study}) (GPa)"
    else:
        X_Pressure_Label = "Input Pressure (GPa)"

    if First_Key:
        Ref_Label_Meta = Calibration_Metadata.get(First_Key, {})
        Ref_Label_Study = Ref_Label_Meta.get("Study", First_Key)
        Ref_Label_Comp = Ref_Label_Meta.get("Composition", "").strip()
        if Ref_Label_Comp:
            Ref_Pressure_Label = f"Pressure ({Ref_Label_Study}, {Ref_Label_Comp}) (GPa)"
        else:
            Ref_Pressure_Label = f"Pressure ({Ref_Label_Study}) (GPa)"
    else:
        Ref_Pressure_Label = "Pressure (GPa)"

    Finite_P__GPa = P_Input__GPa[np.isfinite(P_Input__GPa)]
    Inputs = {
        "composition": Composition,
        "method": Method,
        "first_study_key": First_Key,
        "p_min": float(np.nanmin(Finite_P__GPa)) if Finite_P__GPa.size else 0.0,
        "p_max": float(np.nanmax(Finite_P__GPa)) if Finite_P__GPa.size else 200.0,
        "p_step": 1.0,
        "pressure_file": None,
    }

    return {
        "inputs": Inputs,
        "material": f"{Composition}_{Method}",
        "study_keys": [Entry["key"] for Entry in Eos_List],
        "p_input": P_Input__GPa,
        "p_input_unc": P_Input_Unc__GPa,
        "p_ref": P_Ref__GPa,
        "observable": Observable,
        "obs_unc": Obs_Unc,
        "obs_label": Observable_Label(Method),
        "eos_list": Eos_List,
        "first_key": First_Key or "",
        "first_label": First_Label,
        "x_pressure_label": X_Pressure_Label,
        "ref_pressure_label": Ref_Pressure_Label,
    }




# Figure rendering — synchronous, in-memory (no threads, no disk)


# Render one figure module against the given dataset/config and return its PNG bytes
def Generate_Figure_Png_Bytes(Dataset, Module_Name, Config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import Plot_Styling

    Plot_Styling.Apply_Plot_Style(Config)

    Module = importlib.import_module(Module_Name)
    Fig = Module.Create_Figure(Dataset, Config)
    try:
        Buffer = BytesIO()
        # The desktop app uses compress_level=0 (no compression) because it
        # writes these to a local disk cache where write speed matters and
        # size doesn't. Here the PNG has to cross the JS/Python bridge as a
        # base64 string, so an uncompressed 500-dpi figure (tens of MB) would
        # be far too slow/heavy — compress_level=6 (PIL's own default) cuts
        # that by ~100x with no visible quality loss, since PNG compression
        # is lossless either way.
        Fig.savefig(
            Buffer,
            format="png",
            dpi="figure",
            transparent=bool(Config.Save_Transparent),
            facecolor=Config.Save_Face_Color,
            pil_kwargs={"compress_level": 6},
        )
        return Buffer.getvalue()
    finally:
        plt.close(Fig)
        plt.close("all")


# Return the default module list for a given input mode (pressure-only modules
# dropped when the input is not already in pressure units)
def Get_Module_Names_For_Input_Mode(Input_Mode):
    Module_Names = list(Ui_Module_Order)
    if Input_Mode != "Pressure (GPa)":
        Module_Names = [M for M in Module_Names if M not in Pressure_Only_Modules]
    return Module_Names
