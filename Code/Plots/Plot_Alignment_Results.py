# Load libraries
    # Load standard libraries
import numpy as np
    # Load local functions from local files
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors, Get_Model_Color, Get_Model_Line_Style, Make_Fitting_Axes, Add_Fitting_Legend, Fit_The_Figure_Layout





# Plot the data and the refitted models for one pressure calibration study the pressures were aligned to
def Plot_Aligned_Study(Figure, Study_Label, Study_Index, Aligned_Entry, Model_Names, Measurement, Sigma_Measurement, Y_Label):

    Colors = Get_Fitting_Plot_Colors()
    Ax = Make_Fitting_Axes(Figure, "Pressure (GPa)", Y_Label, f"Aligned to: {Study_Label}")

    # Plot the aligned data, with error bars if there are any
    Aligned_Pressure = Aligned_Entry["p_converted"]
    Aligned_Sigma_Pressure = Aligned_Entry["sp_converted"]
    X_Error = Aligned_Sigma_Pressure if np.any(Aligned_Sigma_Pressure > 0) else None
    Y_Error = Sigma_Measurement if np.any(Sigma_Measurement > 0) else None
    Ax.errorbar(Aligned_Pressure, Measurement, xerr=X_Error, yerr=Y_Error, fmt="s", color=Get_Model_Color(Study_Index), alpha=0.75, zorder=3, capsize=3, markersize=4, label="Aligned data")

    # Plot the aligned fit of each model; a model keeps the same color in every figure
    for Model_Index, Model_Name in enumerate(Model_Names):
        if Model_Name not in Aligned_Entry["model_results"]:
            continue
        Model_Fit = Aligned_Entry["model_results"][Model_Name]
        Color = Get_Model_Color(Model_Index)
        Ax.plot(Model_Fit["p_nominal"], Model_Fit["meas_dense"], color=Color, linewidth=1.9, linestyle="-", label=Model_Name, zorder=5)
        if np.any(Model_Fit["p_std"] > 0):
            Ax.fill_betweenx(Model_Fit["meas_dense"], Model_Fit["p_nominal"] - Model_Fit["p_std"], Model_Fit["p_nominal"] + Model_Fit["p_std"], color=Color, alpha=0.12, zorder=2)

    Add_Fitting_Legend(Ax)
    Fit_The_Figure_Layout(Figure)



# Plot every original and aligned fit on one figure, without the data
def Plot_Alignment_Summary(Figure, Fit_Results, Aligned_Results, Study_Label_Map, Model_Names, Y_Label):

    Colors = Get_Fitting_Plot_Colors()
    Ax = Make_Fitting_Axes(Figure, "Pressure (GPa)", Y_Label, "Summary: All Fits")

    # Original fits are neutral colored and told apart by line style
    for Model_Index, Model_Name in enumerate(Model_Names):
        Original_Fit = Fit_Results[Model_Name]
        Ax.plot(Original_Fit["p_nominal"], Original_Fit["meas_dense"], color=Colors["Text"], linewidth=1.2, linestyle=Get_Model_Line_Style(Model_Index), alpha=0.6, label=f"Original – {Model_Name}", zorder=3)

    # Aligned fits get one color per study and one line style per model
    for Study_Index, Target_Label in enumerate(Aligned_Results.keys()):
        Study_Name = Study_Label_Map.get(Target_Label, Target_Label).split("|")[0].strip()
        Aligned_Model_Results = Aligned_Results[Target_Label]["model_results"]
        for Model_Index, Model_Name in enumerate(Model_Names):
            if Model_Name not in Aligned_Model_Results:
                continue
            Model_Fit = Aligned_Model_Results[Model_Name]
            Ax.plot(Model_Fit["p_nominal"], Model_Fit["meas_dense"], color=Get_Model_Color(Study_Index), linewidth=1.9, linestyle=Get_Model_Line_Style(Model_Index), label=f"{Study_Name} – {Model_Name}", zorder=4)

    Add_Fitting_Legend(Ax)
    Fit_The_Figure_Layout(Figure)
