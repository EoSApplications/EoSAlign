# Pyodide-safe bridge between the website's EoSFitting page (Website_Files/Assets/js/EoSFitting.js) and the fitting
# code the desktop app uses. It is the website's counterpart of the Qt sections of EoSFitting (Enter_Fitting_Data.py,
# Select_Fitting_Models.py, Show_Fit_Results.py, ...): the page draws the sections and collects what the user enters,
# and this file does everything that has to be calculated, using the same functions as the desktop app
# (Fitting_Runs.py, EoS_Math/Fitting_Functions.py, Plots/Plot_Fit_Results.py, ...).
#
# Every function takes and returns plain text (JSON, base64 PNGs or SVG) because that is all that moves easily between
# JavaScript and Python. The fitted results themselves (lmfit objects) stay here, in Runs, one entry for each fit.
#
# Nothing here depends on Qt (the browser has none), so the website runs it as it is.
# Like Plots/Web_Figure_Generation.py it is only used by the website; the desktop app never imports it.

# Load standard libraries
import base64
import json
import os
from io import BytesIO
from types import SimpleNamespace

# Load third-party libraries
import numpy as np

# Load local libraries
from Column_Labels import Get_Preview_Column_Labels, Get_Save_Column_Labels
from EoS_Math.Build_Dataframe import (
    Build_Dataframe, Calibration_Metadata, Calibration_List, All_Compositions, Get_Compositions_For_Method,
    Get_Methods_For_Composition, Set_Calibration_File_Settings, Translate_Pressure_Calibration_Study,
)
from Fitting_Data_File import Fitting_Data_File_Error, Get_Column_Labels, Read_Columns_From_Text
from Fitting_Exports import Build_Alignment_Dataframe, Build_Parameters_Dataframe
from Fitting_Models_And_Units import Get_Measurement_Axis_Label, Get_Method_For_Unit, Get_Models_For_Method
from Fitting_Runs import Run_Alignment, Run_Fits
from Plots import Plot_Fitting_Common
from Plots.Plot_Alignment_Results import Plot_Aligned_Study, Plot_Alignment_Summary
from Plots.Plot_Covariance_Ellipses import Get_Parameter_Pairs, Plot_Covariance_Ellipses
from Plots.Plot_Fit_Results import Plot_Fit_Results
from Reference_Values_And_Units import Function_Information, Material_Information, Method_Units, Volume_Units
from Warning_Messages import Get_Warning





# Use the calibrations that ship with the website only, never a visitor's own edited or entered ones (the same as EoSAlign's page)
Set_Calibration_File_Settings(False, False)

# The matplotlib that comes with the website's Python (Pyodide) is older than the desktop app's and has no Figure._get_renderer,
# which Plots/Plot_Fitting_Common.py uses to measure the legend. The renderer of the figure's canvas is the same thing
from matplotlib.figure import Figure as _Matplotlib_Figure
if not hasattr(_Matplotlib_Figure, "_get_renderer"):
    _Matplotlib_Figure._get_renderer = lambda Self: Self.canvas.get_renderer()

# The fits: run id -> the data, the fits, the alignment and the random generator of that fit (the page has one)
Runs = {}

# The theme colors the figures are drawn with (set by every function that draws, from the page's current light or dark theme)
Current_Theme_Overrides = {}





# The plot style of the figures: the same settings the desktop app starts with (its plot font sizes), and the page's theme colors
def Build_The_Plot_Style_Config():

    return SimpleNamespace(
        Theme_Overrides=dict(Current_Theme_Overrides),
        Ps_Overrides={
            "font_title": 12, "font_label": 10, "font_tick": 8, "font_legend_max": 8,
            "title_bold": False, "title_italic": False, "label_bold": False, "label_italic": False,
            "tick_bold": False, "tick_italic": False,
            # The figures are shown at the screen resolution and saved at a higher one
            "dpi": 100,
        },
        Show_Bands=True,
        Show_Error_Bars=False,
        Show_Grid=False,
    )


# The desktop app reads the plot style from its settings; there are none here, so the fitting plots use the style above
Plot_Fitting_Common.Plot_Style_Config_Provider = Build_The_Plot_Style_Config





# Get the state of one fit, making it if it is new
def Get_Run(Run_Id):

    if Run_Id not in Runs:
        Runs[Run_Id] = {"random": np.random.default_rng(), "fit_results": {}, "aligned_results": {}, "study_labels": {}, "data": None}

    return Runs[Run_Id]


# Set the theme colors the next figures are drawn with
def Set_Theme(Theme_Overrides_Json):

    Current_Theme_Overrides.clear()
    Current_Theme_Overrides.update(json.loads(Theme_Overrides_Json or "{}"))





# Make a new empty figure. Figures are drawn on a plain Agg canvas, which is what draws them into a PNG
def Make_A_Figure(Width, Height):

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    New_Figure = Figure(figsize=(Width, Height), facecolor=Plot_Fitting_Common.Get_Fitting_Plot_Colors()["Background"])
    FigureCanvasAgg(New_Figure)

    return New_Figure


# Draw a figure to a PNG and return it as base64 text, saved at 150 dpi with the figure's own background
    # The whole figure is saved (not cropped to its contents with bbox_inches="tight") because the legend is kept out of the
    # automatic layout (Keep_Space_For_The_Legend), so a tight crop would cut the legend off. The layout already leaves room for it
def Figure_To_Base64_Png(Figure_To_Save):

    Png_Buffer = BytesIO()
    Figure_To_Save.savefig(Png_Buffer, format="png", dpi=150, facecolor=Figure_To_Save.get_facecolor())

    return base64.b64encode(Png_Buffer.getvalue()).decode("ascii")





# Write a number with the digits it needs and no more, e.g. 100.0, 4.0 or 0.00001, with no scientific notation
# (the same as Format_Number in Fitting_Display_Helpers.py, which has Qt in it)
def Format_Number(Value):

    return np.format_float_positional(float(Value), trim="0")


# Get the text for one fitted parameter: value +/- uncertainty, marked (fixed) if it was held
# (the same as Get_Parameter_Text in Fitting_Display_Helpers.py)
def Get_Parameter_Text(Parameter, Stderr):

    if not Parameter.vary:
        return f"{Parameter.value:.5g} ± {Stderr:.3g} (fixed)" if Stderr else f"{Parameter.value:.5g} (fixed)"
    if Stderr is not None:
        return f"{Parameter.value:.5g} ± {Stderr:.3g}"

    return f"{Parameter.value:.5g}"


# Get the names of every parameter across the fitted models, in the order they first appear
def Get_All_Parameter_Names(Fit_Results):

    All_Parameters = []
    for Model_Fit in Fit_Results.values():
        for Parameter_Name in Model_Fit["result"].params:
            if Parameter_Name not in All_Parameters:
                All_Parameters.append(Parameter_Name)

    return All_Parameters


# Get the cells of one model's column of a results table: every parameter, then reduced chi squared and R squared
# (the same as Fill_Result_Column in Fitting_Display_Helpers.py)
def Get_Result_Column(All_Parameters, Result, Stderr_Map):

    Cells = []
    for Parameter_Name in All_Parameters:
        if Parameter_Name in Result.params:
            Parameter = Result.params[Parameter_Name]
            Cells.append(Get_Parameter_Text(Parameter, Stderr_Map.get(Parameter_Name, Parameter.stderr)))
        else:
            Cells.append("—")
    Cells.append(f"{Result.redchi:.4g}")
    Cells.append(f"{Result.rsquared:.4f}" if np.isfinite(Result.rsquared) else "—")

    return Cells





# Get the warning the desktop app would show for a key, as {"title", "message"}
def Get_Warning_Message(Warning_Key, Format_Values_Json="{}"):

    Warning_Message = Get_Warning(Warning_Key, **json.loads(Format_Values_Json or "{}"))

    return json.dumps({"title": Warning_Message["Title"], "message": Warning_Message["Message"]})





# Describe one fitting model for the page
def Describe_A_Model(Model):

    # Matplotlib mathtext does not support some commands, so replace or remove them (the same as Render_Equation_Pixmap)
    Latex = Function_Information.get(Model["function_key"], {}).get("Latex_Equation", "")
    Clean_Latex = Latex.replace(r"\!", "").replace(r"\tfrac", r"\frac").replace(r"\mathcal{F}", r"F")

    return {
        "name": Model["name"],
        "latex": Clean_Latex,
        "has_P0": bool(Model.get("has_P0", False)),
        "needs_Z": bool(Model.get("needs_Z", False)),
        "params": [
            {"name": Parameter["name"], "label": Parameter["label"], "default": float(Parameter["default"]), "default_text": Format_Number(Parameter["default"]), "positive_only": bool(Parameter.get("positive_only", False))}
            for Parameter in Model["params"]
        ],
    }


# Get everything the page needs to build its choices: the units, the models of each method, and the compositions, methods and
# calibrations (the same as the data EoSAlign's page loads, so the alignment choices work the same way)
def Get_Reference():

    Methods = sorted(Method_Units.keys())
    Calibrations = []
    for Calibration_Label, _ in Calibration_List:
        Metadata = Calibration_Metadata[Calibration_Label]
        Calibrations.append({
            "key": Calibration_Label,
            "study": Metadata.get("Study", ""),
            "composition": Metadata.get("Composition", ""),
            "method": Metadata.get("Method", ""),
            "eos": Metadata.get("Equation of State", ""),
            "is_k0_fixed": Metadata.get("Is The Initial Bulk Modulus Fixed?"),
            "cal_to_name": Metadata.get("Reference Study", ""),
            "max_pressure": Metadata.get("Maximum Pressure"),
            "ptm": Metadata.get("Pressure Transmitting Medium", ""),
            "is_user_edited": bool(Metadata.get("is_user_edited", False)),
            "is_user_entered": bool(Metadata.get("is_user_entered", False)),
        })

    return json.dumps({
        # The units: a volume unit is chosen after "Volume"; every other method has one unit
        "unit_types": sorted(Method_Units.values()),
        "method_units": Method_Units,
        "volume_units": Volume_Units,
        "models_by_method": {Method: [Describe_A_Model(Model) for Model in Get_Models_For_Method(Method)] for Method in Methods},
        "compositions": All_Compositions,
        "compositions_for_method": {Method: Get_Compositions_For_Method(Method) for Method in Methods},
        "methods_for_composition": {Composition: Get_Methods_For_Composition(Composition) for Composition in All_Compositions},
        "material_display_names": {Composition: Material_Information.get(Composition, {}).get("Display_Name", Composition) for Composition in All_Compositions},
        "calibrations": Calibrations,
    })


# Draw an equation (LaTeX) as an SVG with the text color "currentColor" so it takes the color of the text around it (and so changes with the theme)
    # It is drawn with matplotlib's mathtext, the same as the desktop app draws its equations
_Equation_Color = "#010203"
def Render_Equation_Svg(Latex):

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    Equation_Figure = Figure(figsize=(0.1, 0.1))
    FigureCanvasAgg(Equation_Figure)
    Equation_Figure.text(0, 0, f"${Latex}$", fontsize=15, color=_Equation_Color)
    Svg_Buffer = BytesIO()
    Equation_Figure.savefig(Svg_Buffer, format="svg", bbox_inches="tight", pad_inches=0.02, transparent=True)
    Svg_Text = Svg_Buffer.getvalue().decode("utf-8")
    # Use the color of the text around the equation
    for Color_Text in (_Equation_Color, _Equation_Color.upper()):
        Svg_Text = Svg_Text.replace(Color_Text, "currentColor")
    # The svg starts with an xml declaration and a doctype, which cannot go inside a web page
    Svg_Start = Svg_Text.find("<svg")

    return Svg_Text[Svg_Start:] if Svg_Start >= 0 else Svg_Text





# Read the columns of the text of an uploaded data file
def Parse_Data_File(Text):

    try:
        Names, Data = Read_Columns_From_Text(Text)
    except Fitting_Data_File_Error as Error:
        Warning_Message = Get_Warning(Error.Warning_Key, **Error.Format_Values)
        return json.dumps({"ok": False, "title": Warning_Message["Title"], "message": Warning_Message["Message"]})
    except Exception as Error:
        Warning_Message = Get_Warning("Could Not Read The Entered Data File", error=Error)
        return json.dumps({"ok": False, "title": Warning_Message["Title"], "message": Warning_Message["Message"]})

    return json.dumps({"ok": True, "labels": Get_Column_Labels(Names, Data.shape[1]), "rows": Data.tolist()})





# Fit every checked model to the entered data (the same as EoSFitting__Workflow.Run_The_Fit) and return the results table,
# the figure and the pairs of parameters the covariance ellipses can show
    # Request: {run_id, theme, units, measurement, sigma_measurement, pressure, sigma_pressure, reference_pressure,
    #           models: [{name, guesses: {parameter: value}, fixed: [parameter], fixed_unc: {parameter: uncertainty}, z, atoms}]}
def Run_The_Fit(Request_Json):

    Request = json.loads(Request_Json)
    Set_Theme(json.dumps(Request.get("theme") or {}))
    Run = Get_Run(Request["run_id"])
    Units = Request["units"]
    Method = Get_Method_For_Unit(Units)
    Data = {
        "Units": Units,
        "Method": Method,
        "Measurement": np.array(Request["measurement"], dtype=float),
        "Sigma_Measurement": np.array(Request["sigma_measurement"], dtype=float),
        "Pressure": np.array(Request["pressure"], dtype=float),
        "Sigma_Pressure": np.array(Request["sigma_pressure"], dtype=float),
    }
    Run["data"] = Data
    Run["settings"] = {Model_Settings["name"]: Model_Settings for Model_Settings in Request["models"]}
    Run["reference_pressure"] = float(Request.get("reference_pressure") or 0.0) if Method == "XRD" else 0.0

    # Find the checked models
    Models_By_Name = {Model["name"]: Model for Model in Get_Models_For_Method(Method)}
    Checked_Models = [Models_By_Name[Model_Settings["name"]] for Model_Settings in Request["models"]]

    # Fit every checked model
    Fit_Results, Reports = Run_Fits(Checked_Models, Read_The_Parameters(Run), Read_The_Composition_Inputs(Run), Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], Run["reference_pressure"], Run["random"])
    Run["fit_results"] = Fit_Results
    # Any earlier alignment was done on the previous fit
    Run["aligned_results"] = {}
    Run["study_labels"] = {}

    # Fill the parameter comparison table with one column per model
    Model_Names = list(Fit_Results.keys())
    All_Parameters = Get_All_Parameter_Names(Fit_Results)
    Columns = [Get_Result_Column(All_Parameters, Fit_Results[Model_Name]["result"], Fit_Results[Model_Name].get("param_stderr") or {}) for Model_Name in Model_Names]

    return json.dumps({
        "model_names": Model_Names,
        "row_labels": All_Parameters + ["Reduced χ²", "R²"],
        "columns": Columns,
        "reports": "\n".join(Reports),
        "pairs": [[Parameter_A, Parameter_B] for Parameter_A, Parameter_B in Get_Parameter_Pairs(Fit_Results)],
        "figure": Draw_The_Fit_Figure(Run),
    })


# Read what the user set for a model's parameters (the same as Select_Fitting_Models.Read_Parameter_Widgets)
def Read_The_Parameters(Run):

    def Read_Parameters(Model_Name, Model):
        Settings = Run["settings"][Model_Name]
        Fixed_Uncertainties = {Name: float(Value) for Name, Value in (Settings.get("fixed_unc") or {}).items() if float(Value) > 0}
        return {Name: float(Value) for Name, Value in Settings["guesses"].items()}, set(Settings.get("fixed") or []), Fixed_Uncertainties

    return Read_Parameters


# Read the effective Z and atoms per volume unit of a model that needs them (the same as Select_Fitting_Models.Read_Composition_Inputs)
def Read_The_Composition_Inputs(Run):

    def Read_Composition_Inputs(Model):
        if Model.get("needs_Z", False):
            Settings = Run["settings"].get(Model["name"], {})
            if Settings.get("z") is not None and Settings.get("atoms") is not None:
                return float(Settings["z"]), float(Settings["atoms"])
        return None, None

    return Read_Composition_Inputs


# Draw the data and every fitted model as pressure vs the measurement (the same as Show_Fit_Results)
def Draw_The_Fit_Figure(Run):

    Data = Run["data"]
    Fit_Figure = Make_A_Figure(9, 5.2)
    Plot_Fit_Results(Fit_Figure, Run["fit_results"], Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], Get_Measurement_Axis_Label(Data["Units"]))

    return Figure_To_Base64_Png(Fit_Figure)


# Draw the fit figure again (for example when the page's theme is changed)
def Get_The_Fit_Figure(Run_Id, Theme_Overrides_Json):

    Set_Theme(Theme_Overrides_Json)

    return Draw_The_Fit_Figure(Get_Run(Run_Id))


# Draw the 1 sigma and 2 sigma ellipses of a parameter pair for every model (the same as Show_Covariance_Ellipses)
def Get_The_Covariance_Figure(Run_Id, Parameter_A, Parameter_B, Theme_Overrides_Json):

    Set_Theme(Theme_Overrides_Json)
    Run = Get_Run(Run_Id)
    Covariance_Figure = Make_A_Figure(9, 5.6)
    Plot_Covariance_Ellipses(Covariance_Figure, Run["fit_results"], (Parameter_A, Parameter_B) if Parameter_A else None)

    return Figure_To_Base64_Png(Covariance_Figure)





# Convert the pressures to each study, refit every model and return the results (the same as EoSFitting__Workflow.Run_The_Alignment)
    # Request: {run_id, theme, source_calibration, target_calibrations: [key], study_labels: {key: label}}
    # The data, the models and their settings are the ones of the last fit
def Run_The_Alignment(Request_Json):

    Request = json.loads(Request_Json)
    Set_Theme(json.dumps(Request.get("theme") or {}))
    Run = Get_Run(Request["run_id"])
    Data = Run["data"]

    Run["aligned_results"] = Run_Alignment(Run["fit_results"], Request["source_calibration"], Request["target_calibrations"], Read_The_Parameters(Run), Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], Run["reference_pressure"], Run["random"])
    Run["study_labels"] = Request.get("study_labels") or {}

    return Build_The_Alignment_Output(Run)


# Draw the alignment results again (for example when the page's theme is changed)
def Get_The_Alignment_Results(Run_Id, Theme_Overrides_Json):

    Set_Theme(Theme_Overrides_Json)

    return Build_The_Alignment_Output(Get_Run(Run_Id))


# Build the table and the figures of the alignment results (the same as Show_Alignment_Results)
def Build_The_Alignment_Output(Run):

    Fit_Results = Run["fit_results"]
    Aligned_Results = Run["aligned_results"]
    Study_Label_Map = Run["study_labels"]
    Data = Run["data"]
    Y_Label = Get_Measurement_Axis_Label(Data["Units"])
    Model_Names = list(Fit_Results.keys())
    All_Parameters = Get_All_Parameter_Names(Fit_Results)

    # Use the first two pipe separated segments of a study's label (Author | Material), which is short enough to be a header or a figure title
    def Get_Short_Label(Target_Label):
        Parts = [Part.strip() for Part in Study_Label_Map.get(Target_Label, Target_Label).split("|")]
        return " | ".join(Parts[:2]) if len(Parts) >= 2 else Parts[0]

    # The table has the original fits followed by the fits aligned to each study
    Column_Headers = [f"Original\n{Model_Name}" for Model_Name in Model_Names]
    for Target_Label in Aligned_Results.keys():
        for Model_Name in Model_Names:
            Column_Headers.append(f"{Get_Short_Label(Target_Label)}\n{Model_Name}")
    Columns = [Get_Result_Column(All_Parameters, Fit_Results[Model_Name]["result"], Fit_Results[Model_Name].get("param_stderr") or {}) for Model_Name in Model_Names]
    for Target_Label in Aligned_Results.keys():
        Aligned_Model_Results = Aligned_Results[Target_Label]["model_results"]
        for Model_Name in Model_Names:
            if Model_Name in Aligned_Model_Results:
                Aligned_Fit = Aligned_Model_Results[Model_Name]
                Columns.append(Get_Result_Column(All_Parameters, Aligned_Fit["result"], Aligned_Fit.get("param_stderr") or {}))
            else:
                Columns.append(["" for _ in range(len(All_Parameters) + 2)])

    # Draw one figure per study and a summary figure of all the fits
    Figures = []
    for Study_Index, (Target_Label, Aligned_Entry) in enumerate(Aligned_Results.items()):
        Study_Figure = Make_A_Figure(9, 5.6)
        # The full label of a study is longer than the figure is wide (the desktop's figure is stretched to its window), so the title is the short one
        Plot_Aligned_Study(Study_Figure, Get_Short_Label(Target_Label), Study_Index, Aligned_Entry, Model_Names, Data["Measurement"], Data["Sigma_Measurement"], Y_Label)
        Figures.append(Figure_To_Base64_Png(Study_Figure))
    Summary_Figure = Make_A_Figure(9, 5.6)
    Plot_Alignment_Summary(Summary_Figure, Fit_Results, Aligned_Results, Study_Label_Map, Model_Names, Y_Label)
    Figures.append(Figure_To_Base64_Png(Summary_Figure))

    return json.dumps({"column_headers": Column_Headers, "row_labels": All_Parameters + ["Reduced χ²", "R²"], "columns": Columns, "figures": Figures})





# Get the table of fitted parameters as CSV text (the same as Show_Fit_Results.When_Save_Csv_Is_Clicked)
def Get_The_Parameters_Csv(Run_Id):

    return Build_Parameters_Dataframe(Get_Run(Run_Id)["fit_results"]).to_csv(index=False)


# Get the table of original and aligned fits as CSV text (the same as Show_Alignment_Results.When_Save_Csv_Is_Clicked)
def Get_The_Alignment_Csv(Run_Id):

    Run = Get_Run(Run_Id)

    return Build_Alignment_Dataframe(Run["fit_results"], Run["aligned_results"], Run["study_labels"]).to_csv(index=False)





# Convert the entered pressures to the selected studies and return the table (the same as Select_Studies_For_Comparison.Preview_Conversions)
    # Request: {run_id, pressure, sigma_pressure, composition, method, pressure_calibration_study, selected_keys}
    # pressure_calibration_study is the selection made in the page, in the same form as the desktop's Select_Pressure_Calibration_Study
def Build_The_Conversion_Preview(Request_Json):

    Request = json.loads(Request_Json)
    Pressure = np.array(Request["pressure"], dtype=float)
    Sigma_Pressure = np.array(Request["sigma_pressure"], dtype=float)

    # Build_Dataframe reads the pressures from files, so write them the way EoSFitting's preview does (one value on each line)
    Folder = f"/tmp/eosfitting_preview_{Request['run_id']}"
    os.makedirs(Folder, exist_ok=True)
    Pressure_File_Path = os.path.join(Folder, "Pressure.txt")
    with open(Pressure_File_Path, "w") as Preview_File:
        Preview_File.write("".join(f"{Value}\n" for Value in Pressure))
    # Only write the uncertainties if there are any
    Has_Uncertainty = bool(np.any(Sigma_Pressure > 0))
    Uncertainty_File_Path = ""
    if Has_Uncertainty:
        Uncertainty_File_Path = os.path.join(Folder, "Pressure_Uncertainty.txt")
        with open(Uncertainty_File_Path, "w") as Preview_File:
            Preview_File.write("".join(f"{Value}\n" for Value in Sigma_Pressure))
    Data = {
        "File_Path": Pressure_File_Path,
        "Units": "Pressure (GPa)",
        "Error Propagation Enabled": Has_Uncertainty,
        "Uncertainty Data": {"Error Propagation Enabled": Has_Uncertainty, "Error Propagation Path": Uncertainty_File_Path},
    }

    File_Ok, Units_Ok, Error_Message, Dataframe = Build_Dataframe(Data, "Pressure (GPa)", Request["composition"], Request["method"], Translate_Pressure_Calibration_Study(Request["pressure_calibration_study"]), Request["selected_keys"])
    if not File_Ok or not Units_Ok or Dataframe is None or Dataframe.empty:
        return json.dumps({"ok": False, "message": Error_Message or "No data to preview."})

    # The table shows the short labels, and its download uses the same save labels as EoSAlign's export
    Export_Dataframe = Dataframe.rename(columns=Get_Save_Column_Labels(Dataframe.columns, Calibration_Metadata))
    Preview_Labels = Get_Preview_Column_Labels(list(Dataframe.columns), Calibration_Metadata)

    return json.dumps({
        "ok": True,
        "preview": {"columns": [Preview_Labels[Column_Name] for Column_Name in Dataframe.columns], "rows": Export_Dataframe.astype(object).where(Export_Dataframe.notnull(), None).values.tolist()},
        "export": {"columns": list(Export_Dataframe.columns), "rows": Export_Dataframe.astype(object).where(Export_Dataframe.notnull(), None).values.tolist()},
    })
