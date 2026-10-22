# Load libraries
    # Load third party libraries
from matplotlib.patches import Ellipse
    # Load local functions from local files
from EoS_Math.Fitting_Functions import Calculate_Covariance_Ellipse
from Plots import Plot_Styling
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors, Get_Model_Color, Make_Fitting_Axes, Add_Fitting_Legend, Fit_The_Figure_Layout





# Get the pairs of varied parameters that have a covariance in at least one model
def Get_Parameter_Pairs(Fit_Results):

    Pairs = []
    for Model_Fit in Fit_Results.values():
        Result = Model_Fit["result"]
        if Result.covar is None:
            continue
        Varied_Parameters = [Name for Name in Result.params if Result.params[Name].vary]
        for Index, Parameter_A in enumerate(Varied_Parameters):
            for Parameter_B in Varied_Parameters[Index + 1:]:
                if (Parameter_A, Parameter_B) not in Pairs:
                    Pairs.append((Parameter_A, Parameter_B))

    return Pairs



# Plot the 1 sigma and 2 sigma confidence ellipses of a parameter pair for every model
def Plot_Covariance_Ellipses(Figure, Fit_Results, Parameter_Pair):

    Colors = Get_Fitting_Plot_Colors()
    Figure.clear()
    Ax = Make_Fitting_Axes(Figure)

    # Nothing to draw until there is a pair and a fit
    if Parameter_Pair is None or not Fit_Results:
        return
    Parameter_A, Parameter_B = Parameter_Pair
    Ax.set_xlabel(Parameter_A, color=Colors["Text"], **Plot_Styling.Label_Font_Kwargs())
    Ax.set_ylabel(Parameter_B, color=Colors["Text"], **Plot_Styling.Label_Font_Kwargs())

    # Draw the ellipses for each model that varied both parameters
    Models_Drawn = 0
    for Model_Index, (Model_Name, Model_Fit) in enumerate(Fit_Results.items()):
        Result = Model_Fit["result"]
        if Result.covar is None:
            continue
        Varied_Parameters = [Name for Name in Result.params if Result.params[Name].vary]
        if Parameter_A not in Varied_Parameters or Parameter_B not in Varied_Parameters:
            continue
        Index_A = Varied_Parameters.index(Parameter_A)
        Index_B = Varied_Parameters.index(Parameter_B)
        Value_A = Result.params[Parameter_A].value
        Value_B = Result.params[Parameter_B].value
        Variance_A = Result.covar[Index_A, Index_A]
        Variance_B = Result.covar[Index_B, Index_B]
        Covariance = Result.covar[Index_A, Index_B]
        Color = Get_Model_Color(Model_Index)
        # Draw the 1 sigma and 2 sigma ellipses
        for Number_Of_Sigma, Alpha, Line_Width in ((1, 0.25, 1.5), (2, 0.10, 1.0)):
            Width, Height, Angle = Calculate_Covariance_Ellipse(Variance_A, Variance_B, Covariance, Number_Of_Sigma)
            Ax.add_patch(Ellipse(xy=(Value_A, Value_B), width=Width, height=Height, angle=Angle, linewidth=Line_Width, edgecolor=Color, facecolor=Color, alpha=Alpha, zorder=2))
        Ax.plot(Value_A, Value_B, "o", color=Color, markersize=6, zorder=3, label=Model_Name)
        Models_Drawn += 1

    Ax.autoscale_view()
    if Models_Drawn:
        Add_Fitting_Legend(Ax)
    Ax.set_title("1σ / 2σ confidence ellipses", color=Colors["Text"], fontsize=9)
    Fit_The_Figure_Layout(Figure)
