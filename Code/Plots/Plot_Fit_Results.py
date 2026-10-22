# Load libraries
    # Load standard libraries
import numpy as np
    # Load local functions from local files
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors, Get_Model_Color, Make_Fitting_Axes, Add_Fitting_Legend, Fit_The_Figure_Layout





# Plot the data and every fitted model as pressure vs the measurement
def Plot_Fit_Results(Figure, Fit_Results, Measurement, Sigma_Measurement, Pressure, Sigma_Pressure, Y_Label):

    Colors = Get_Fitting_Plot_Colors()
    Figure.clear()
    Ax = Make_Fitting_Axes(Figure, "Pressure (GPa)", Y_Label)

    # Plot the data, with error bars if there are any
    X_Error = Sigma_Pressure if np.any(Sigma_Pressure > 0) else None
    Y_Error = Sigma_Measurement if np.any(Sigma_Measurement > 0) else None
    Ax.errorbar(Pressure, Measurement, xerr=X_Error, yerr=Y_Error, fmt="o", color=Colors["Text"], alpha=0.7, zorder=3, capsize=3, markersize=5, label="Data")

    # Plot each fitted model with its uncertainty band
    for Model_Index, (Model_Name, Model_Fit) in enumerate(Fit_Results.items()):
        Color = Get_Model_Color(Model_Index)
        Pressure_Nominal = Model_Fit["p_nominal"]
        Pressure_Std = Model_Fit["p_std"]
        Measurement_Dense = Model_Fit["meas_dense"]
        Ax.plot(Pressure_Nominal, Measurement_Dense, color=Color, linewidth=1.8, label=Model_Name, zorder=4)
        if np.any(Pressure_Std > 0):
            Ax.fill_betweenx(Measurement_Dense, Pressure_Nominal - Pressure_Std, Pressure_Nominal + Pressure_Std, color=Color, alpha=0.15, zorder=2)

    Add_Fitting_Legend(Ax)
    Fit_The_Figure_Layout(Figure)
