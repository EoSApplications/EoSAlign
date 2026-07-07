# Bridge between the EoSAlign app and the standalone figure generation scripts
    # Provides:
    #   Build_Dataset_From_App_Data  - converts app dataframe to figure-script dataset format
    #   AppFigureConfig              - minimal config_module compatible with figure scripts
    #   Start_Figure_Generation      - launches background PNG generation, cancels prior run
    #   Make_Figures_Dir             - deterministic temp directory for a given data configuration

# Load libraries
    # Load standard libraries
import importlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

    # Load third-party libraries
import numpy as np

    # Load local libraries
from Session_Paths import get_session_directory




Plots_Dir = Path(__file__).resolve().parent
Repo_Root = Plots_Dir.parent




# Path setup


# Add Plots/ and repo root to sys.path so figure scripts can import each other
def Local__Ensure_Paths():
    Plots_Str = str(Plots_Dir)
    Repo_Str = str(Repo_Root)
    # Only insert if not already present to avoid duplicate entries accumulating across calls
    if Plots_Str not in sys.path:
        sys.path.insert(0, Plots_Str)
    if Repo_Str not in sys.path:
        sys.path.insert(0, Repo_Str)




# Module and export constants


# Generation order: all figure modules that this app can produce
Default_Module_Names = [
    "Plot_Observable_Vs_Pressure",
    "Plot_All_EoS_Overlay_Absolute_Pressure_Difference",
    "Plot_All_EoS_Overlay_Percent_Pressure_Difference",
    "Plot_Pressure_Scale_Disagreement",
    "Plot_Individual_Absolute_Pressure_Difference",
    "Plot_Individual_Percent_Pressure_Difference",
    "Plot_Summary_Observable_Vs_Pressure_And_Overlay",
]

# Display order used by Plot_Window UI: summary before the individual panels for better load priority
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

# Human-readable section titles used in Plot_Window for labeling each figure type
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

Export_Theme_Labels = {
    "light": "Light Theme",
    "dark": "Dark Theme",
}

Export_Background_Labels = {
    "transparent": "Transparent Background",
    "white": "White Background",
    "black": "Black Background",
}

Export_Background_Colors = {
    "transparent": "none",
    "white": "#FFFFFF",
    "black": "#000000",
}

# Default set of export variants generated automatically alongside display PNGs
Auto_Export_Variants = (
    ("light", "transparent"),
    ("light", "white"),
    ("dark", "transparent"),
    ("dark", "black"),
)

# Filename used to store the generation signature in a figures directory
Local__Generation_Signature_Filename = "generation_signature.json"




# Study style helpers


# Return the default color for a comparison study at a given palette index
def Local__Default_Study_Color(Index):
    from Themes.Plot_Style_Options import AUTO_COLORS

    # Cycle the palette if there are more studies than colors
    if AUTO_COLORS:
        return AUTO_COLORS[Index % len(AUTO_COLORS)]
    # Fall back to a safe matplotlib blue when no palette is defined
    return "#1f77b4"


# Return the default marker for a comparison study at a given palette index
def Local__Default_Study_Marker(Index):
    from Themes.Plot_Style_Options import AUTO_MARKERS, DEFAULT_MARKER

    # Cycle the marker list if there are more studies than markers
    if AUTO_MARKERS:
        return AUTO_MARKERS[Index % len(AUTO_MARKERS)]
    # Fall back to the configured default marker
    return DEFAULT_MARKER


# Read any user-saved per-study color and marker from QSettings, falling back to palette defaults
def Local__Read_Saved_Study_Style(Calibration_Key, Study_Index, Settings_Store=None):
    from PySide6.QtCore import QSettings

    # Create a temporary store only if none was passed; reuse the caller's store when available
    Settings_Store = Settings_Store or QSettings("EoSAlign", "EoSAlignApp")

    # Only honour saved color/marker when the user explicitly chose them within this session.
    # Styles are cleared on plot-window close, so Is_User_Set is only True during an active session.
    Is_User_Set = Settings_Store.value(f"{Calibration_Key}_Style_Is_User_Set", False, type=bool)
    if Is_User_Set:
        Saved_Color  = (Settings_Store.value(f"{Calibration_Key}_Color",  "", type=str) or "").strip()
        Saved_Marker = (Settings_Store.value(f"{Calibration_Key}_Marker", "", type=str) or "").strip()
    else:
        Saved_Color  = ""
        Saved_Marker = ""

    # Return the user-saved style, or the palette default when no explicit choice has been made
    return {
        "color":  Saved_Color  or Local__Default_Study_Color(Study_Index),
        "marker": Saved_Marker or Local__Default_Study_Marker(Study_Index),
    }




# Generation preferences


# Read all current generation preferences from QSettings and the active theme, returning a dict
def Get_Current_Generation_Preferences(Selected_Keys=None):
    from PySide6.QtCore import QSettings
    from Themes.Theme import Get_Theme

    Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
    Show_Uncertainty = Settings_Store.value("Show_Uncertainty", True, type=bool)
    Uncertainty_Style = Settings_Store.value("Uncertainty_Style", "Bands", type=str)
    # Derive band/error-bar flags from the combined uncertainty style setting
    Show_Bands = Show_Uncertainty and Uncertainty_Style in ("Bands", "Both")
    Show_Error_Bars = Show_Uncertainty and Uncertainty_Style in ("Error Bars", "Both")
    Show_Grid = Settings_Store.value("Show_Grid_Lines", False, type=bool)
    Legend_Font_Size = int(Settings_Store.value("Legend Font Size", 8))

    # Collect per-element font and style overrides for Plot_Styling's preset system
    Ps_Overrides = {
        "font_title": int(Settings_Store.value("Plot Title Font Size", 12)),
        "font_label": int(Settings_Store.value("Axis Label Font Size", 10)),
        "font_tick": int(Settings_Store.value("Tick Mark Font Size", 8)),
        "font_legend_max": float(Legend_Font_Size),
        "spread_legend_font": float(Legend_Font_Size),
        "title_bold": Settings_Store.value("Plot Title Bold", False, type=bool),
        "title_italic": Settings_Store.value("Plot Title Italic", False, type=bool),
        "label_bold": Settings_Store.value("Axis Label Bold", False, type=bool),
        "label_italic": Settings_Store.value("Axis Label Italic", False, type=bool),
        "tick_bold": Settings_Store.value("Tick Mark Bold", False, type=bool),
        "tick_italic": Settings_Store.value("Tick Mark Italic", False, type=bool),
    }

    # Read the active theme's color dict; the first two return values are raw palettes not needed here
    Unused_Light_Palette, Unused_Dark_Palette, Colors = Get_Theme()
    Theme_Overrides = {
        "Primary_Text": Colors.get("Primary_Text", "#111111"),
        "Secondary_Text": Colors.get("Secondary_Text", "#212121"),
        "Primary_Color": Colors.get("Primary_Color", "#FABE60"),
        "Secondary_Background": Colors.get("Secondary_Background", "#FFFFFF"),
        "Primary_Background": Colors.get("Primary_Background", "#FFFFFF"),
    }

    Selected_Keys = list(Selected_Keys or [])
    # Build a complete signature dict used for cache invalidation comparison
    Signature = {
        "version": 1,
        "selected_keys": Selected_Keys,
        "show_bands": bool(Show_Bands),
        "show_error_bars": bool(Show_Error_Bars),
        "show_grid": bool(Show_Grid),
        "ps_overrides": dict(Ps_Overrides),
        "theme_overrides": dict(Theme_Overrides),
        "study_styles": {
            Key: Local__Read_Saved_Study_Style(Key, Index, Settings_Store=Settings_Store)
            for Index, Key in enumerate(Selected_Keys)
        },
    }

    # Return all preferences as a flat dict for the caller to pass into Start_Figure_Generation
    return {
        "show_bands": Show_Bands,
        "show_error_bars": Show_Error_Bars,
        "show_grid": Show_Grid,
        "ps_overrides": Ps_Overrides,
        "theme_overrides": Theme_Overrides,
        "signature": Signature,
    }




# Generation signature I/O


# Return the Path to the generation signature JSON file inside the given figures directory
def Local__Generation_Signature_Path(Figures_Dir):
    return Path(Figures_Dir) / Local__Generation_Signature_Filename


# Read and return the generation signature dict from disk, or None if absent or unreadable
def Read_Generation_Signature(Figures_Dir):
    # A None directory means no session has been created yet
    if Figures_Dir is None:
        return None

    Signature_Path = Local__Generation_Signature_Path(Figures_Dir)
    # Missing file means the directory was not yet generated with a tracked signature
    if not Signature_Path.exists():
        return None

    try:
        # Parse the JSON signature; returns None on any read or parse failure
        with open(Signature_Path, "r", encoding="utf-8") as Handle:
            return json.load(Handle)
    except Exception:
        return None


# Write the generation signature dict atomically to the figures directory
def Write_Generation_Signature(Figures_Dir, Signature):
    # A None directory means nowhere to write; silently skip
    if Figures_Dir is None:
        return

    Signature_Path = Local__Generation_Signature_Path(Figures_Dir)
    Signature_Path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file first so readers never see a partial signature
    Tmp_Path = Signature_Path.with_suffix(".tmp")
    with open(Tmp_Path, "w", encoding="utf-8") as Handle:
        json.dump(Signature, Handle, indent=2, sort_keys=True)
    # Atomic replace: either the old or the new file is visible, never a partial write
    os.replace(str(Tmp_Path), str(Signature_Path))




# AppFigureConfig class


# Minimal config_module interface compatible with all standalone figure scripts
class AppFigureConfig:

    # Class-level defaults for layout parameters read by figure scripts via getattr
    Save_Formats = ["png"]
    Isolate_Exports = False
    Individuals_Across = 4
    Individual_Panel_Gap__Inches = 0.90
    Individual_Render_Dpi = 500

    # Build an instance config for one generation run with the given display and export settings
    def __init__(self, Figures_Dir, Show_Bands=True, Show_Error_Bars=False, Show_Grid=False,
                 Theme_Overrides=None, Ps_Overrides=None, Save_Transparent=False,
                 Save_Face_Color="none"):
        # Store the target directory as a string for downstream path construction
        self.Figures_Directory = str(Figures_Dir)
        # Uncertainty visualization flags read by Apply_Plot_Style via getattr
        self.Show_Bands = bool(Show_Bands)
        self.Show_Error_Bars = bool(Show_Error_Bars)
        self.Show_Grid = bool(Show_Grid)
        # Color and font override dicts read by Apply_Plot_Style via getattr
        self.Theme_Overrides = dict(Theme_Overrides) if Theme_Overrides else {}
        self.Ps_Overrides = dict(Ps_Overrides) if Ps_Overrides else {}
        # PNG save options used by Local__Save_Figure
        self.Save_Transparent = bool(Save_Transparent)
        self.Save_Face_Color = Save_Face_Color

    # Return an empty inputs dict; satisfies the figure-script config interface
    def Build_Inputs(self):
        return {}




# Dataset builder


# Return the y-axis label string for the observable measurement for a given method
def Observable_Label(Method):
    from Reference_Values_And_Units import Method_Units
    # XRD measures unit-cell volume, which needs a specialized label with units
    if Method == "XRD":
        return "Volume (Å³/unit cell)"
    # All other methods map through the global units dictionary
    Label = Method_Units.get(Method, "Observable")
    # Return the observable label for this method
    return Label


# Parse a raw maximum pressure value into a (pressure_float, was_finite) pair
def Parse_Max_Pressure(Raw_Value):
    try:
        # Convert the raw value to float; None or non-numeric strings will raise here
        Parsed_Value = float(Raw_Value)
    except (TypeError, ValueError):
        # Non-numeric input means no finite maximum pressure was specified
        return np.inf, False
    # A finite float is a real, user-specified pressure limit
    if np.isfinite(Parsed_Value):
        return Parsed_Value, True
    # A non-finite float (nan or inf passed in) is treated as unspecified
    return np.inf, False


# Convert the app's precomputed dataframe to the dataset format expected by all figure scripts
def Build_Dataset_From_App_Data(Df, Composition, Method, Reference_Key, Selected_Keys, Input_Mode, Original_Study_Key=None):
    Local__Ensure_Paths()

    from EoS_Math.Build_Dataframe import Calibration_Metadata, Calibration_Functions
    from Reference_Values_And_Units import Method_Units
    from Plot_Utilities import Build_Eos_Curve_Cache
    from PySide6.QtCore import QSettings

    # Locate the observable (measured-value) column; prefer "Input", then fall back to "Measured"
    Input_Cols = [Col for Col in Df.columns if "Input" in Col and "_Unc" not in Col]
    if not Input_Cols:
        Input_Cols = [Col for Col in Df.columns if "Measured" in Col and "_Unc" not in Col]
    Input_Col = Input_Cols[0] if Input_Cols else Df.columns[0]

    # The literal, originally-entered values. This is the x-axis for every pressure-difference
    # and percent-difference plot, regardless of how many calibration studies are chained
    # together to get from here to a final comparison pressure.
    P_Input__GPa = np.asarray(Df[Input_Col].values, dtype=float)
    Input_Unc_Col = f"{Input_Col}_Unc"
    P_Input_Unc__GPa = np.asarray(Df[Input_Unc_Col].values, dtype=float) if Input_Unc_Col in Df.columns else None

    # The pressure associated with the LAST pressure-calibration study (Reference_Key). For a
    # single-study calibration (same composition/method as the entered data) this is identical
    # to the original input. For a different-composition/method conversion this is the
    # "assumed-equal" pressure on the new composition's scale. It is used as the x-axis for the
    # measured-value-vs-pressure plot and as the reference study's own "data"/curve value in the
    # difference and percent plots.
    P_Ref__GPa = None
    P_Ref_Unc__GPa = None
    if Reference_Key:
        P_Ref_Col = f"Pressure_{Reference_Key}"
        if P_Ref_Col in Df.columns:
            P_Ref__GPa = np.asarray(Df[P_Ref_Col].values, dtype=float)
        P_Ref_Unc_Col = f"P_Unc_{Reference_Key}"
        if P_Ref_Unc_Col in Df.columns:
            P_Ref_Unc__GPa = np.asarray(Df[P_Ref_Unc_Col].values, dtype=float)

    # Fall back to the original input when no separate reference-pressure column exists; this is
    # always true for the single-study/same-composition workflow, where the reference study's
    # own pressure IS the input by construction.
    if P_Ref__GPa is None:
        P_Ref__GPa = P_Input__GPa
    if P_Ref_Unc__GPa is None:
        P_Ref_Unc__GPa = P_Input_Unc__GPa

    # For non-pressure inputs, the observable IS the input column
    if Input_Mode != "Pressure (GPa)":
        Observable = np.asarray(Df[Input_Col].values, dtype=float)
        # The observable uncertainty is simply the input measured-value uncertainty
        Obs_Unc_Col = f"{Input_Col}_Unc"
        Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float) if Obs_Unc_Col in Df.columns else None
    # For pressure inputs, recover the observable by inverting the reference calibration
    else:
        Method_Unit = Method_Units.get(Method, "")
        Obs_Col = None
        Obs_Unc = None
        # Try to find a pre-computed observable column derived from the reference calibration.
        # A different-composition/method conversion chain suffixes this column with
        # "_(<composition>_<method>)", so match by prefix rather than requiring an exact name.
        if Reference_Key and Method_Unit:
            Candidate_Prefix = f"{Method_Unit}_From_{Reference_Key}"
            Matches = [Col for Col in Df.columns if Col == Candidate_Prefix or Col.startswith(Candidate_Prefix + "_")]
            if Matches:
                Obs_Col = Matches[0]
        if Obs_Col:
            Observable = np.asarray(Df[Obs_Col].values, dtype=float)
            # Pressure-input workflows store the inverse-calculated observable uncertainty under
            # the reference study's V_Unc_<key> column, even for non-XRD methods.
            Obs_Unc_Col = f"V_Unc_{Reference_Key}" if Reference_Key else ""
            if Obs_Unc_Col and Obs_Unc_Col in Df.columns:
                Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float)
            else:
                Fallback_Obs_Unc_Col = f"{Obs_Col}_Unc"
                Obs_Unc = np.asarray(Df[Fallback_Obs_Unc_Col].values, dtype=float) if Fallback_Obs_Unc_Col in Df.columns else None
        # Fall back to numerical inversion of the reference EoS
        elif Reference_Key and Reference_Key in Calibration_Functions:
            Unused_Forward_Func, Inverse_Func = Calibration_Functions[Reference_Key]
            Observable = np.array(
                [float(Inverse_Func(P__GPa)) if np.isfinite(P__GPa) and P__GPa > 0 else np.nan for P__GPa in P_Ref__GPa],
                dtype=float,
            )
            Obs_Unc_Col = f"V_Unc_{Reference_Key}"
            Obs_Unc = np.asarray(Df[Obs_Unc_Col].values, dtype=float) if Obs_Unc_Col in Df.columns else None
        # No inversion available; use the pressure axis directly as a stand-in
        else:
            Observable = P_Ref__GPa.copy()
            Obs_Unc = None

    Eos_List = []

    # Insert the reference (last pressure-calibration) study as the first entry so figure
    # scripts can draw it separately as the thick black/white reference line.
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

    # Append each comparison study, reading per-study color/marker from QSettings
    Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
    Comparison_Index = 0
    for Key in (Selected_Keys or []):
        # Skip the reference study; it was already inserted above
        if Key == Reference_Key:
            continue
        P_Col = f"Pressure_{Key}"
        # Skip any key whose pressure column is absent from the dataframe
        if P_Col not in Df.columns:
            continue
        Meta = Calibration_Metadata.get(Key, {})
        P_Max__GPa, P_Max_Specified = Parse_Max_Pressure(Meta.get("Maximum Pressure"))
        Pmax_Label = f"{P_Max__GPa:.0f} GPa" if P_Max_Specified else "N/A"
        P_Eos__GPa = np.asarray(Df[P_Col].values, dtype=float)
        P_Unc_Col = f"P_Unc_{Key}"
        P_Unc = np.asarray(Df[P_Unc_Col].values, dtype=float) if P_Unc_Col in Df.columns else None
        Study_Style = Local__Read_Saved_Study_Style(Key, Comparison_Index, Settings_Store=Settings_Store)
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
            "color": Study_Style["color"],
            "marker": Study_Style["marker"],
            "pressure_unc": P_Unc,
            "curve_cache": Build_Eos_Curve_Cache(P_Input__GPa, P_Eos__GPa, P_Max__GPa, P_Max_Specified, P_Unc=P_Unc, X_Unc=P_Input_Unc__GPa),
        })
        Comparison_Index += 1

    # Determine the reference/first key and build its label. Unlike the old fallback, a missing
    # Reference_Key (the non-pressure-units case, where no single study is "the" calibration)
    # means there is no special reference study at all — every selected study is a plain
    # comparison curve, so First_Key stays empty rather than arbitrarily picking one.
    First_Key = Reference_Key
    if First_Key:
        First_Meta = Calibration_Metadata.get(First_Key, {})
        Fp_Max__GPa, Fp_Specified = Parse_Max_Pressure(First_Meta.get("Maximum Pressure"))
        Fp_Label = f"{Fp_Max__GPa:.0f} GPa" if Fp_Specified else "N/A"
        First_Label = f"{First_Meta.get('Study', First_Key)} | {First_Meta.get('Equation of State', '')} | {Fp_Label}"
    else:
        First_Label = ""

    # The x-axis for the difference/percent plots is the original input pressure.
    # Label it with the name of the study that ESTABLISHED that pressure scale — always the
    # originally-selected pressure calibration study (Original_Study_Key), which equals
    # Reference_Key for single-study (same composition) runs but differs from it for the
    # different-composition workflow where Reference_Key is the final target study.
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

    # Label for the reference/last calibration study's own pressure axis.
    # This is the x-axis for the measured-value-vs-pressure (observable) plot's left panel
    # in the Combined Summary figure, and wherever p_ref is shown on an x-axis.
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

    # Compute the inputs dict from the finite-valued input pressure range
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

    # Return the complete dataset dict used by all figure scripts
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




# Thread state


# Generation token lock and state; each figures directory tracks its own active generation token
Local__Token_Lock = threading.Lock()
Local__Dir_Tokens = {}
Local__Token_Counter = 0

# Progress state lock; maps normalized figures-directory path to the latest progress dict
Local__Progress_Lock = threading.Lock()
Local__Dir_Progress = {}




# Token management


# Return the normalized (resolved) string path key for a figures directory
def Local__Normalize_Token_Key(Figures_Dir):
    try:
        return str(Path(Figures_Dir).resolve())
    except Exception:
        return str(Path(Figures_Dir))


# Increment the global token counter and assign the new token to this directory
def Local__Assign_Generation_Token(Figures_Dir):
    global Local__Token_Counter

    Token_Key = Local__Normalize_Token_Key(Figures_Dir)
    with Local__Token_Lock:
        # Atomically increment and capture so the token is unique and monotonically increasing
        Local__Token_Counter += 1
        Token = Local__Token_Counter
        Local__Dir_Tokens[Token_Key] = Token
    # Return both so the caller can check liveness throughout the run
    return Token_Key, Token


# Return True if this token is still the active generation token for its directory
def Local__Is_Current_Generation(Token_Key, Token):
    with Local__Token_Lock:
        return Local__Dir_Tokens.get(Token_Key) == Token




# Progress tracking


# Initialize the progress entry for a new generation run
def Local__Initialize_Progress(Token_Key, Token, *, Total_Steps, Current_Step, Mode):
    Now = time.monotonic()
    with Local__Progress_Lock:
        Local__Dir_Progress[Token_Key] = {
            "token": Token,
            "running": True,
            "mode": Mode,
            "completed_steps": 0,
            "total_steps": max(int(Total_Steps), 1),
            "current_step": Current_Step,
            "started_at": Now,
            "updated_at": Now,
            "canceled": False,
            "failed": False,
        }


# Merge arbitrary keyword updates into the progress dict if the token is still current
def Local__Set_Progress(Token_Key, Token, **Updates):
    with Local__Progress_Lock:
        Current = dict(Local__Dir_Progress.get(Token_Key, {}))
        # Silently discard updates for stale (superseded) tokens
        if Current and Current.get("token") != Token:
            return
        Current.update(Updates)
        Current["token"] = Token
        Current["updated_at"] = time.monotonic()
        Local__Dir_Progress[Token_Key] = Current


# Increment the completed-steps counter and optionally update the current-step label
def Local__Advance_Progress(Token_Key, Token, *, Current_Step=None):
    with Local__Progress_Lock:
        Current = dict(Local__Dir_Progress.get(Token_Key, {}))
        # Silently discard advances for stale tokens
        if not Current or Current.get("token") != Token:
            return
        Current["completed_steps"] = int(Current.get("completed_steps", 0)) + 1
        if Current_Step is not None:
            Current["current_step"] = Current_Step
        Current["updated_at"] = time.monotonic()
        Local__Dir_Progress[Token_Key] = Current


# Mark the generation run as finished, canceled, or failed
def Local__Finish_Progress(Token_Key, Token, *, Canceled=False, Failed=False, Current_Step=None):
    with Local__Progress_Lock:
        Current = dict(Local__Dir_Progress.get(Token_Key, {}))
        # Silently discard finish calls for stale tokens
        if not Current or Current.get("token") != Token:
            return
        if Current_Step is not None:
            Current["current_step"] = Current_Step
        Current["running"] = False
        Current["canceled"] = bool(Canceled)
        Current["failed"] = bool(Failed)
        # On success, set completed_steps to total so percent reads 100
        if not Canceled and not Failed:
            Current["completed_steps"] = int(Current.get("total_steps", Current.get("completed_steps", 0)))
        Current["updated_at"] = time.monotonic()
        Local__Dir_Progress[Token_Key] = Current




# Generation control


# Return the latest progress snapshot for the given figures directory
def Get_Generation_Progress(Figures_Dir):
    Token_Key = Local__Normalize_Token_Key(Figures_Dir)
    with Local__Progress_Lock:
        Current = dict(Local__Dir_Progress.get(Token_Key, {}))

    # No progress entry means this directory has never started a generation run
    if not Current:
        return {
            "running": False,
            "completed_steps": 0,
            "total_steps": 0,
            "percent": 100,
            "eta_seconds": 0.0,
            "current_step": "",
            "canceled": False,
            "failed": False,
            "mode": "",
        }

    # Compute the percentage and ETA from elapsed time and completed steps
    Completed = int(Current.get("completed_steps", 0))
    Total = max(int(Current.get("total_steps", 0)), 1)
    Percent = min(100, int((Completed / Total) * 100))
    Eta_Seconds = None
    Started_At = Current.get("started_at")
    if Started_At is not None and Completed > 0 and Completed < Total:
        Elapsed = max(0.001, time.monotonic() - Started_At)
        Eta_Seconds = (Elapsed / Completed) * (Total - Completed)
    elif Completed >= Total:
        Eta_Seconds = 0.0

    Current["percent"] = Percent
    Current["eta_seconds"] = Eta_Seconds
    # Return the dict with percent and ETA annotations added
    return Current


# Cancel the active generation run for the given figures directory by advancing its token
def Cancel_Generation(Figures_Dir):
    global Local__Token_Counter

    Token_Key = Local__Normalize_Token_Key(Figures_Dir)
    # Advancing the token causes any running worker to detect it is no longer current
    with Local__Token_Lock:
        Local__Token_Counter += 1
        Local__Dir_Tokens[Token_Key] = Local__Token_Counter

    # Also mark the progress entry as canceled so the UI can reflect it immediately
    with Local__Progress_Lock:
        Current = dict(Local__Dir_Progress.get(Token_Key, {}))
        if Current:
            Current["running"] = False
            Current["canceled"] = True
            Current["updated_at"] = time.monotonic()
            Local__Dir_Progress[Token_Key] = Current




# Export variant helpers


# Return the string key used to identify a theme+background export variant
def Get_Export_Variant_Key(Theme_Name, Background_Name):
    return f"{Theme_Name}__{Background_Name}"


# Return the human-readable label for a theme+background export variant
def Get_Export_Variant_Label(Theme_Name, Background_Name):
    return f"{Export_Theme_Labels[Theme_Name]} | {Export_Background_Labels[Background_Name]}"


# Return the directory where export variant PNGs are stored for a figures directory
def Get_Export_Variants_Dir(Figures_Dir):
    return Path(Figures_Dir) / "export_variants"


# Return the full path for a specific export variant PNG
def Get_Export_Variant_Path(Figures_Dir, Basename, Theme_Name, Background_Name):
    return Get_Export_Variants_Dir(Figures_Dir) / (
        f"{Basename}__{Get_Export_Variant_Key(Theme_Name, Background_Name)}.png"
    )


# Deduplicate and normalize a list of (theme_name, background_name) pairs
def Local__Normalize_Export_Variants(Export_Variants):
    Normalized = []
    Seen = set()
    for Theme_Name, Background_Name in Export_Variants or []:
        Item = (str(Theme_Name).lower(), str(Background_Name).lower())
        # Skip duplicates that would overwrite the same output file
        if Item in Seen:
            continue
        Seen.add(Item)
        Normalized.append(Item)
    # Return the deduplicated list in its original order
    return Normalized


# Build a theme-override dict for a given export theme+background combination
def Local__Build_Export_Theme_Overrides(Theme_Name, Background_Name):
    from Themes.Theme import DARK_COLORS, LIGHT_COLORS

    # Select the appropriate color palette for this theme
    Theme_Palette = LIGHT_COLORS if Theme_Name == "light" else DARK_COLORS
    # Return a theme dict formatted for Apply_Plot_Style
    return {
        "Primary_Text": Theme_Palette.get("Primary_Text", "#111111"),
        "Secondary_Text": Theme_Palette.get("Secondary_Text", "#212121"),
        "Primary_Color": Theme_Palette.get("Primary_Color", "#FABE60"),
        "Secondary_Background": Theme_Palette.get("Secondary_Background", "#FFFFFF"),
        "Primary_Background": Export_Background_Colors[Background_Name],
    }




# Figure I/O


# Save a matplotlib figure to a PNG file atomically, creating parent directories as needed
def Local__Save_Figure(Fig, Output_Path, *, Transparent, Facecolor):
    Output_Path = Path(Output_Path)
    Output_Path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a .tmp file first so readers never observe a partial write
    Tmp_Path = Output_Path.with_suffix(".tmp.png")
    Fig.savefig(
        str(Tmp_Path),
        format="png",
        dpi="figure",
        transparent=bool(Transparent),
        facecolor=Facecolor,
        pil_kwargs={"compress_level": 0},
    )
    # Replace atomically: old file or new file is visible, never a partial write
    os.replace(str(Tmp_Path), str(Output_Path))


# Render all modules in Module_Names into PNGs using the given config; returns False if canceled
def Local__Render_Module_Set(Dataset, Config, Module_Names, Output_Path_For_Module, Module_Cache,
                              Token_Key, Token, *, Step_Label_Factory):
    import matplotlib.pyplot as plt
    import Plot_Styling

    # Apply the theme, font sizes, and grid settings from this config before generating
    Plot_Styling.Apply_Plot_Style(Config)

    for Module_Name in Module_Names:
        # Stop immediately when this generation run has been superseded
        if not Local__Is_Current_Generation(Token_Key, Token):
            return False

        Step_Label = Step_Label_Factory(Module_Name)
        Local__Set_Progress(Token_Key, Token, current_step=Step_Label)
        try:
            Module = Module_Cache[Module_Name]
            # Call the renamed Create_Figure entry point on each figure module
            Fig = Module.Create_Figure(Dataset, Config)
            Local__Save_Figure(
                Fig,
                Output_Path_For_Module(Module),
                Transparent=Config.Save_Transparent,
                Facecolor=Config.Save_Face_Color,
            )
            plt.close(Fig)
        except Exception as Exc:
            print(f"[Generate_Figures] {Module_Name} failed: {Exc}")
        finally:
            # Always close all figures to release GPU/memory resources, even on failure
            try:
                plt.close("all")
            except Exception:
                pass
        Local__Advance_Progress(Token_Key, Token)

    # Return True only when all modules completed without cancellation
    return True




# Background generation worker


# Worker function that runs in a daemon thread to generate all requested figures
def Local__Run_Generation(Df, Composition, Method, Input_Mode, Reference_Key, Selected_Keys,
                           Figures_Dir, Show_Bands, Show_Error_Bars, Show_Grid, Ps_Overrides,
                           Theme_Overrides, Module_Names, Export_Variants, Include_Display,
                           Token_Key, Token, Mode, Original_Study_Key=None):
    Local__Ensure_Paths()

    import matplotlib
    # Agg must be active before any figure creation; the daemon thread sets it here
    matplotlib.use("Agg")

    Export_Variants = Local__Normalize_Export_Variants(Export_Variants)
    # Total step count drives the progress bar: display + N export variants per figure
    Total_Steps = len(Module_Names) * (len(Export_Variants) + (1 if Include_Display else 0))
    Local__Initialize_Progress(
        Token_Key,
        Token,
        Total_Steps=Total_Steps,
        Current_Step="Preparing figure generation...",
        Mode=Mode,
    )

    try:
        # Build the shared dataset once; all figure modules and all variants consume it
        Dataset = Build_Dataset_From_App_Data(
            Df, Composition, Method, Reference_Key, Selected_Keys, Input_Mode, Original_Study_Key
        )
    except Exception as Exc:
        print(f"[Generate_Figures] Dataset build failed: {Exc}")
        Local__Finish_Progress(
            Token_Key,
            Token,
            Failed=True,
            Current_Step=f"Failed to build figure dataset: {Exc}",
        )
        return

    Path(Figures_Dir).mkdir(parents=True, exist_ok=True)
    # Cache all module imports up-front so each render loop can skip the import overhead
    Module_Cache = {
        Module_Name: importlib.import_module(Module_Name)
        for Module_Name in Module_Names
    }

    # Generate the display PNGs (transparent, used by the app's PNG_Display_Widget)
    if Include_Display:
        Display_Config = AppFigureConfig(
            Figures_Dir=Figures_Dir,
            Show_Bands=Show_Bands,
            Show_Error_Bars=Show_Error_Bars,
            Show_Grid=Show_Grid,
            Ps_Overrides=Ps_Overrides,
            Theme_Overrides=Theme_Overrides,
            Save_Transparent=True,
            Save_Face_Color="none",
        )

        Display_Ok = Local__Render_Module_Set(
            Dataset,
            Display_Config,
            Module_Names,
            # Figure_Basename is the renamed module-level constant in each figure script
            lambda Module: Path(Figures_Dir) / f"{Module.Figure_Basename}.png",
            Module_Cache,
            Token_Key,
            Token,
            Step_Label_Factory=lambda Module_Name: f"Building display figure: {Module_Name}",
        )
        if not Display_Ok:
            Local__Finish_Progress(
                Token_Key,
                Token,
                Canceled=True,
                Current_Step="Figure generation canceled.",
            )
            return

    # Generate each requested export variant with its own theme and background settings
    for Theme_Name, Background_Name in Export_Variants:
        if not Local__Is_Current_Generation(Token_Key, Token):
            Local__Finish_Progress(
                Token_Key,
                Token,
                Canceled=True,
                Current_Step="Figure generation canceled.",
            )
            return

        Export_Config = AppFigureConfig(
            Figures_Dir=Figures_Dir,
            Show_Bands=Show_Bands,
            Show_Error_Bars=Show_Error_Bars,
            Show_Grid=Show_Grid,
            Ps_Overrides=Ps_Overrides,
            Theme_Overrides=Local__Build_Export_Theme_Overrides(Theme_Name, Background_Name),
            Save_Transparent=(Background_Name == "transparent"),
            Save_Face_Color=Export_Background_Colors[Background_Name],
        )

        Variants_Ok = Local__Render_Module_Set(
            Dataset,
            Export_Config,
            Module_Names,
            lambda Module, Theme_Name_Capture=Theme_Name, Background_Name_Capture=Background_Name: Get_Export_Variant_Path(
                Figures_Dir, Module.Figure_Basename, Theme_Name_Capture, Background_Name_Capture
            ),
            Module_Cache,
            Token_Key,
            Token,
            Step_Label_Factory=lambda Module_Name, Theme_Name_Capture=Theme_Name, Background_Name_Capture=Background_Name: (
                f"Building export figure: {Module_Name} [{Get_Export_Variant_Label(Theme_Name_Capture, Background_Name_Capture)}]"
            ),
        )
        if not Variants_Ok:
            Local__Finish_Progress(
                Token_Key,
                Token,
                Canceled=True,
                Current_Step="Figure generation canceled.",
            )
            return

    Local__Finish_Progress(
        Token_Key,
        Token,
        Current_Step="Figure generation complete.",
    )




# Public start / cancel API


# Launch a background generation run that builds display PNGs then all default export variants
def Start_Figure_Generation(Df, Composition, Method, Input_Mode, Reference_Key,
                             Selected_Keys, Figures_Dir, Show_Bands=True,
                             Show_Error_Bars=False, Show_Grid=False,
                             Ps_Overrides=None, Theme_Overrides=None, Module_Names=None,
                             Original_Study_Key=None):
    Token_Key, Token = Local__Assign_Generation_Token(Figures_Dir)

    # Default to all modules; exclude pressure-only figures when the input is not in pressure units
    if Module_Names is None:
        Module_Names = list(Default_Module_Names)
        if Input_Mode != "Pressure (GPa)":
            Module_Names = [M for M in Module_Names if M not in Pressure_Only_Modules]

    Worker = threading.Thread(
        target=Local__Run_Generation,
        args=(
            Df,
            Composition,
            Method,
            Input_Mode,
            Reference_Key,
            Selected_Keys,
            Figures_Dir,
            Show_Bands,
            Show_Error_Bars,
            Show_Grid,
            Ps_Overrides or {},
            Theme_Overrides or {},
            Module_Names,
            Auto_Export_Variants,
            True,
            Token_Key,
            Token,
            "automatic",
            Original_Study_Key,
        ),
        daemon=True,
    )
    Worker.start()
    # Return the thread so callers can join it if needed
    return Worker


# Launch a background generation run that builds only the explicitly requested export variants
def Start_Export_Variant_Generation(Df, Composition, Method, Input_Mode, Reference_Key,
                                     Selected_Keys, Figures_Dir, Export_Variants,
                                     Show_Bands=True, Show_Error_Bars=False, Show_Grid=False,
                                     Ps_Overrides=None, Theme_Overrides=None, Module_Names=None,
                                     Original_Study_Key=None):
    Token_Key, Token = Local__Assign_Generation_Token(Figures_Dir)

    # Default to all modules; exclude pressure-only figures when the input is not in pressure units
    if Module_Names is None:
        Module_Names = list(Default_Module_Names)
        if Input_Mode != "Pressure (GPa)":
            Module_Names = [M for M in Module_Names if M not in Pressure_Only_Modules]

    Worker = threading.Thread(
        target=Local__Run_Generation,
        args=(
            Df,
            Composition,
            Method,
            Input_Mode,
            Reference_Key,
            Selected_Keys,
            Figures_Dir,
            Show_Bands,
            Show_Error_Bars,
            Show_Grid,
            Ps_Overrides or {},
            Theme_Overrides or {},
            Module_Names,
            Export_Variants,
            False,
            Token_Key,
            Token,
            "export",
            Original_Study_Key,
        ),
        daemon=True,
    )
    Worker.start()
    # Return the thread so callers can join it if needed
    return Worker




# Directory helpers


# Return the user-data root; same as Math.Shorthand.Calibration_Cache for user YAML files
def Local__User_Data_Root():
    return get_session_directory(".figures", create=False).parent.parent


# Sanitize an arbitrary string into a safe filesystem path component
def Local__Safe_Path_Component(Value):
    Text = str(Value or "").strip()
    # Replace any character not safe for all filesystems with an underscore
    Text = re.sub(r"[^A-Za-z0-9._-]+", "_", Text)
    Text = Text.strip("._")
    # Always return at least "run" so the path component is never empty
    return Text or "run"


# Return (and create) the hidden directory for storing intermediate PNGs for this run
def Make_Figures_Dir(Composition, Method, Reference_Key, Selected_Keys, Run_Label=None,
                     Run_Token=None):
    # Location: <user-data-root>/.figures/<session-id>/<run-label>__<run-token>/
    #   The session-id layer isolates different EoSAlign windows from each other
    Figures_Root = Local__User_Data_Root() / ".figures"
    Figures_Root.mkdir(parents=True, exist_ok=True)

    # On Windows, mark the root .figures directory as hidden
    if sys.platform == "win32":
        try:
            import ctypes

            Kernel32 = ctypes.windll.kernel32
            Invalid_Attribute = 0xFFFFFFFF
            File_Attribute_Hidden = 0x02
            Existing_Attributes = Kernel32.GetFileAttributesW(str(Figures_Root))
            if Existing_Attributes != Invalid_Attribute:
                Kernel32.SetFileAttributesW(str(Figures_Root), Existing_Attributes | File_Attribute_Hidden)
        except Exception:
            pass
    # On macOS, use chflags to set the hidden flag
    elif sys.platform == "darwin":
        try:
            import subprocess

            subprocess.run(["chflags", "hidden", str(Figures_Root)], check=False, capture_output=True)
        except Exception:
            pass

    # Build the run-specific subdirectory name from the optional label and token parts
    Run_Parts = []
    if Run_Label:
        Run_Parts.append(Local__Safe_Path_Component(Run_Label))
    if Run_Token:
        Run_Parts.append(Local__Safe_Path_Component(Run_Token))

    Figures_Dir = get_session_directory(
        ".figures",
        "__".join(Run_Parts) if Run_Parts else "default",
    )
    Figures_Dir.mkdir(parents=True, exist_ok=True)
    # Return the fully constructed figures directory path
    return Figures_Dir




