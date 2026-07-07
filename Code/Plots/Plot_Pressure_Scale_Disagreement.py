# Load libraries
    # Load third-party libraries
import numpy as np

    # Load local libraries
import Plot_Styling
import Plot_Utilities




Figure_Basename = "pressure_scale_disagreement"




# Figure builder


# Build the pressure-scale disagreement figure (range and std deviation) and return it
def Create_Figure(Dataset, Config_Module):
    # Unpack the original-input pressure axis and dataset entries from the pre-built dataset
    P_Input__GPa = Dataset["p_input"]
    First_Key = Dataset["first_key"]
    X_Pressure_Label = Dataset.get("x_pressure_label", "Input Pressure (GPa)")

    # Exclude the reference study; disagreement is computed only across comparison studies
    Eos_Plot_List = [Eos for Eos in Dataset["eos_list"] if Eos["key"] != First_Key]

    # At least one comparison EoS is required to compute spread statistics
    if not Eos_Plot_List:
        raise ValueError("Pressure scale disagreement plot requires at least one comparison EoS.")

    # Stack all comparison-study pressure differences column-wise for vectorized stats
    All_Dp__GPa = np.column_stack([Eos["data"] - P_Input__GPa for Eos in Eos_Plot_List])
    # Range is max minus min across studies at each pressure point
    P_Range__GPa = np.nanmax(All_Dp__GPa, axis=1) - np.nanmin(All_Dp__GPa, axis=1)
    P_Std__GPa = np.nanstd(All_Dp__GPa, axis=1)
    # Mask out near-zero input pressures to avoid division-by-zero in the relative panel
    Valid_Mask = P_Input__GPa > 0.1

    # Create the two-panel spread layout and resolve the marker size for this figure size
    Figure, Ax_Left, Ax_Right, Marker_Size = Plot_Styling.Make_Spread_Disagreement_Figure()
    Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Marker_Size)
    Legend_Font = Plot_Styling.Ps["spread_legend_font"]

    # Force a canvas render so that axis pixel extents are available for the padding helper
    Figure.canvas.draw()
    Renderer = Figure.canvas.get_renderer()

    # Convert an inch-based legend edge padding to fractional axis coordinates for this axis
    def Compute_Legend_Pad_From_Inches(Ax, Pad__Inches):
        # Get the axis bounding box in inches using the live renderer
        Bbox__Inches = Ax.get_window_extent(renderer=Renderer).transformed(Figure.dpi_scale_trans.inverted())
        # Normalize the inch padding by the axis size in each dimension
        Pad_X = Pad__Inches / max(float(Bbox__Inches.width), 1e-9)
        Pad_Y = Pad__Inches / max(float(Bbox__Inches.height), 1e-9)
        # Return non-negative fractions so the legend never overlaps the axis frame
        return float(max(0.0, Pad_X)), float(max(0.0, Pad_Y))

    # Compute per-panel padding fractions from the shared inch value in the preset
    Pad__Inches = float(Plot_Styling.Ps.get("spread_legend_edge_pad_in", 0.13))
    Left_Padding = Compute_Legend_Pad_From_Inches(Ax_Left, max(0.0, Pad__Inches))
    Right_Padding = Compute_Legend_Pad_From_Inches(Ax_Right, max(0.0, Pad__Inches))

    # Draw range and std-deviation curves on the absolute panel
    Ax_Left.plot(P_Input__GPa, P_Range__GPa, color=Plot_Styling.Theme["Primary_Text"], marker="o", ms=Marker_Size, lw=Curve_Style["line_lw"], label="Range (max-min)")
    Ax_Left.plot(P_Input__GPa, P_Std__GPa, color=Plot_Styling.Theme["Primary_Color"], marker="s", ms=Marker_Size, lw=Curve_Style["line_lw"], label="Standard Deviation")
    # Place the legend in the corner with the least data overlap
    Left_Info = Plot_Utilities.Place_Feature_Best_Corner(
        Ax_Left,
        Feature="legend",
        Padding=Left_Padding,
        X_Data=P_Input__GPa,
        Y_Series=[P_Range__GPa, P_Std__GPa],
        Legend_Kwargs={"fontsize": Legend_Font, "markerscale": 1.0},
        Return_Info=True,
    )
    Left_Legend = Left_Info["artist"]
    # Apply theme text color to all legend entries when a legend was successfully placed
    if Left_Legend is not None:
        for Legend_Text in Left_Legend.get_texts():
            Legend_Text.set_color(Plot_Styling.Theme["Primary_Text"])
    Plot_Styling.Style_Ax(Ax_Left, X_Pressure_Label, "Difference (GPa)", "Absolute Difference")

    # Compute relative spread for the right panel, restricted to the valid-pressure mask
    P_Rel = P_Range__GPa[Valid_Mask] / P_Input__GPa[Valid_Mask] * 100
    P_Std_Rel = P_Std__GPa[Valid_Mask] / P_Input__GPa[Valid_Mask] * 100

    # Draw range and std-deviation curves on the relative panel
    Ax_Right.plot(P_Input__GPa[Valid_Mask], P_Rel, color=Plot_Styling.Theme["Primary_Text"], marker="o", ms=Marker_Size, lw=Curve_Style["line_lw"], label="Range (max-min)")
    Ax_Right.plot(P_Input__GPa[Valid_Mask], P_Std_Rel, color=Plot_Styling.Theme["Primary_Color"], marker="s", ms=Marker_Size, lw=Curve_Style["line_lw"], label="Standard Deviation")
    # Place the right-panel legend in the corner with the least data overlap
    Right_Info = Plot_Utilities.Place_Feature_Best_Corner(
        Ax_Right,
        Feature="legend",
        Padding=Right_Padding,
        X_Data=P_Input__GPa[Valid_Mask],
        Y_Series=[P_Rel, P_Std_Rel],
        Legend_Kwargs={"fontsize": Legend_Font, "markerscale": 1.0},
        Return_Info=True,
    )
    Right_Legend = Right_Info["artist"]
    # Apply theme text color to all legend entries when a legend was successfully placed
    if Right_Legend is not None:
        for Legend_Text in Right_Legend.get_texts():
            Legend_Text.set_color(Plot_Styling.Theme["Primary_Text"])
    Plot_Styling.Style_Ax(Ax_Right, X_Pressure_Label, "% Difference", "Relative Difference")

    # Add a shared supertitle describing the figure content and EoS count
    Plot_Styling.Place_Spread_Suptitle(
        Figure,
        [Ax_Left, Ax_Right],
        f"{Dataset['material']} - Pressure scale disagreement (vs selected comparison study)\n({len(Eos_Plot_List)} EoS shown; comparison study excluded)",
    )

    # Return the completed figure for downstream PNG export
    return Figure




