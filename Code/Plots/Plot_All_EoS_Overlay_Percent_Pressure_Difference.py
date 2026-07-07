# Load libraries
    # Load third-party libraries
import matplotlib.pyplot as plt

    # Load local libraries
import Plot_Styling
import Plot_Utilities
from EoS_Math.Build_Dataframe import Calibration_Metadata




Figure_Basename = "all_eos_overlay_percent_pressure_difference"




# Figure builder


# Build the all-EoS overlay figure showing percent pressure difference and return it
def Create_Figure(Dataset, Config_Module):
    # Unpack the original-input pressure axis and metadata from the pre-built dataset
    P_Input__GPa = Dataset["p_input"]
    First_Key = Dataset.get("first_key") or None
    First_Label = Dataset["first_label"]
    X_Pressure_Label = Dataset.get("x_pressure_label", "Input Pressure (GPa)")

    # Separate the reference (last pressure-calibration) study, if any, from the comparisons
    Reference_Eos = next((Eos for Eos in Dataset["eos_list"] if First_Key and Eos["key"] == First_Key), None)
    Eos_Plot_List = [Eos for Eos in Dataset["eos_list"] if Eos is not Reference_Eos]
    # Legend list: reference study first (if any), then all comparison studies in order
    Eos_Labels = ([First_Label] if Reference_Eos is not None else []) + [Eos["label"] for Eos in Eos_Plot_List]

    # Create overlay layout sized to the number of comparison studies
    Figure, Ax_Plot, Ax_Legend, Marker_Size, Font_Pt, Wrapped, Num_Cols = Plot_Styling.Make_Overlay_Figure(Eos_Labels)
    # Derive consistent line and open-circle dimensions from the resolved marker size
    Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Marker_Size)
    # Reference line is drawn heavier than comparison curves for visual hierarchy
    Reference_Line_Width = float(max(Curve_Style["line_lw"] * 2.0, 1.2))
    Handles = []

    # Draw the reference/last pressure-calibration study first: a thick black/white line with no
    # symbols, solid where its pressure is known (within its rated maximum) and dashed where it
    # is extrapolated beyond that maximum.
    if Reference_Eos is not None:
        Handles.append(plt.Line2D([0], [0], color=Plot_Styling.Theme["Primary_Text"], linewidth=Reference_Line_Width))
        Plot_Utilities.Plot_Eos_Curve(
            Ax_Plot,
            P_Input__GPa,
            Reference_Eos["data"],
            Reference_Eos["p_max"],
            Plot_Styling.Theme["Primary_Text"],
            "",
            None,
            Marker_Size=Marker_Size,
            Line_Width=Reference_Line_Width,
            Z_Order=3,
            Mode="pct",
            Curve_Cache=Reference_Eos["curve_cache"],
            P0__GPa=Reference_Eos.get("p0"),
        )

    # Draw each comparison study's percent pressure-difference curve
    for Eos_Index, Eos in enumerate(Eos_Plot_List):
        # Use per-study color/marker overrides if present, otherwise cycle the palette
        Curve_Color = Eos.get("color", Plot_Styling.Get_Color_At_Index(Eos_Index))
        Curve_Marker = Eos.get("marker", Plot_Styling.Get_Marker_At_Index(Eos_Index))
        Plot_Utilities.Plot_Eos_Curve(
            Ax_Plot,
            P_Input__GPa,
            Eos["data"],
            Eos["p_max"],
            Curve_Color,
            Curve_Marker,
            None,
            Marker_Size=Marker_Size,
            Line_Width=Curve_Style["line_lw"],
            Mode="pct",
            Curve_Cache=Eos["curve_cache"],
            P0__GPa=Eos.get("p0"),
        )
        Handles.append(Plot_Utilities.Make_Line_Handle(Curve_Color, Curve_Marker, Marker_Size, Eos["p_max_specified"]))

    # Draw a dashed zero-difference reference line across the full pressure range
    Plot_Utilities.Draw_Horizontal_Reference_Line(
        Ax_Plot,
        0.0,
        X_Values=P_Input__GPa,
        Color=Plot_Styling.Theme["Secondary_Text"],
        Line_Style="--",
        Line_Width=Curve_Style["open_lw"],
        Z_Order=0,
    )

    # Build the y-axis label including the reference study name when available
    First_Study = Calibration_Metadata.get(First_Key, {}).get("Study", First_Key or "")
    Y_Label = f"Pdiff/{First_Study}*100 (%)" if First_Study else "Pdiff/P_input*100 (%)"

    # Apply axis labels and tick styling
    Plot_Styling.Style_Ax(Ax_Plot, X_Pressure_Label, Y_Label, "")
    # Populate the legend column with all collected handles
    Plot_Styling.Draw_Overlay_Legend(Ax_Legend, Handles, Wrapped, Font_Pt, Num_Cols)

    # Return the completed figure for downstream PNG export
    return Figure




