# Load libraries
    # Load third-party libraries
import matplotlib.pyplot as plt

    # Load local libraries
import Plot_Styling
import Plot_Utilities




Figure_Basename = "observable_vs_pressure"




# Figure builder


# Build the observable-vs-pressure overlay figure and return it
def Create_Figure(Dataset, Config_Module):
    # Unpack axis arrays and display labels from the pre-built dataset
    P_Ref__GPa = Dataset["p_ref"]
    Observable = Dataset["observable"]
    Y_Label = Dataset["obs_label"]
    First_Label = Dataset["first_label"]
    First_Key = Dataset.get("first_key") or None

    # A reference (pressure-calibration) study only exists when the entered data is itself in
    # pressure units. For non-pressure data there is no single study to single out — every
    # selected study is a plain comparison curve with its own color and marker.
    Reference_Eos = next((Eos for Eos in Dataset["eos_list"] if First_Key and Eos["key"] == First_Key), None)
    Eos_Plot_List = [Eos for Eos in Dataset["eos_list"] if Eos is not Reference_Eos]
    # Legend list: reference study first (if any), then all comparison studies in order
    Eos_Labels = ([First_Label] if Reference_Eos is not None else []) + [Eos["label"] for Eos in Eos_Plot_List]

    # Optional observable uncertainty array; None when not supplied by the caller
    Obs_Unc = Dataset.get("obs_unc")
    # The original input-pressure uncertainty is only present for pressure-input workflows
    P_Input_Unc__GPa = Dataset.get("p_input_unc")

    # Create overlay layout: data panel + right-hand legend column sized to fit the labels
    Figure, Ax_Plot, Ax_Legend, Marker_Size, Font_Pt, Wrapped, Num_Cols = Plot_Styling.Make_Overlay_Figure(Eos_Labels)
    # Derive consistent line and open-circle dimensions from the resolved marker size
    Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Marker_Size)
    # Reference line is drawn heavier than comparison curves for visual hierarchy
    Reference_Line_Width = float(max(Curve_Style["line_lw"] * 2.0, 1.2))

    Handles = []
    if Reference_Eos is not None:
        # Seed the handle list with the reference study's solid line (no markers)
        Handles.append(plt.Line2D([0], [0], color=Plot_Styling.Theme["Primary_Text"], linewidth=Reference_Line_Width))
        # Draw the reference study's observable curve in the primary text color
        Ax_Plot.plot(
            P_Ref__GPa, Observable,
            color=Plot_Styling.Theme["Primary_Text"],
            linestyle="-",
            linewidth=Reference_Line_Width,
            zorder=1,
        )
        # Error bars on the reference curve, using the same calculated uncertainties as every
        # other curve. For pressure-input workflows, the x uncertainty is the input-pressure
        # uncertainty and the y uncertainty is the inverse-calculated observable uncertainty.
        if Plot_Styling.Show_Error_Bars and (P_Input_Unc__GPa is not None or Obs_Unc is not None):
            Ax_Plot.errorbar(
                P_Ref__GPa, Observable,
                xerr=P_Input_Unc__GPa,
                yerr=Obs_Unc,
                fmt="none",
                ecolor=Plot_Styling.Theme["Primary_Text"],
                alpha=0.5,
                capsize=2,
                zorder=0,
            )

    # Draw each comparison study and collect its legend handle
    for Eos_Index, Eos in enumerate(Eos_Plot_List):
        # Use per-study color/marker overrides if present, otherwise cycle the palette
        Curve_Color = Eos.get("color", Plot_Styling.Get_Color_At_Index(Eos_Index))
        Curve_Marker = Eos.get("marker", Plot_Styling.Get_Marker_At_Index(Eos_Index))
        Plot_Utilities.Plot_Observable_Curve(
            Ax_Plot,
            Eos["data"],
            Observable,
            Eos["p_max"],
            Eos["p_max_specified"],
            Curve_Color,
            Curve_Marker,
            Label=None,
            Marker_Size=Marker_Size,
            Line_Width=Curve_Style["line_lw"],
            P0__GPa=Eos.get("p0"),
            X_Errors=P_Input_Unc__GPa if Reference_Eos is not None else Eos.get("pressure_unc"),
            Y_Errors=Obs_Unc,
        )
        Handles.append(Plot_Utilities.Make_Line_Handle(Curve_Color, Curve_Marker, Marker_Size, Eos["p_max_specified"]))

    # Apply axis labels and tick styling
    Plot_Styling.Style_Ax(Ax_Plot, "Pressure (GPa)", Y_Label, "")
    # Populate the legend column with all collected handles
    Plot_Styling.Draw_Overlay_Legend(Ax_Legend, Handles, Wrapped, Font_Pt, Num_Cols)

    # Return the completed figure for downstream PNG export
    return Figure




