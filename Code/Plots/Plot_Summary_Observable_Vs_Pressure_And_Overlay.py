# Load libraries
    # Load third-party libraries
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure as MplFigure
import matplotlib.pyplot as plt

    # Load local libraries
import Plot_Styling
import Plot_Utilities




Figure_Basename = "summary_observable_vs_pressure_and_overlay"




# Snapshot helpers


# Render the absolute-spread inset as a standalone RGBA image for overlay compositing
def Local__Build_Abs_Spread_Snapshot(P_Input__GPa, P_Range__GPa, P_Std__GPa, Right_Panel_Width, Panel_Height, X_Label):
    # Scale markers to the inset panel dimensions rather than the main figure
    Snapshot_Marker_Size = Plot_Styling.Calculate_Marker_Size(Right_Panel_Width, Panel_Height, Base_Marker_Size=1, Reference_Area=25.0)
    Snapshot_Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Snapshot_Marker_Size)

    # Create an off-screen figure at the inset panel size for pixel-accurate cropping
    Snapshot_Figure = MplFigure(figsize=(Right_Panel_Width, Panel_Height), dpi=Plot_Styling.Ps["dpi"])
    Canvas = FigureCanvasAgg(Snapshot_Figure)
    # Transparent background so the inset blends into the main figure's axes area
    Snapshot_Figure.patch.set_facecolor("none")
    Snapshot_Figure.patch.set_alpha(0.0)

    Snapshot_Axis = Snapshot_Figure.add_subplot(111)
    # Tight margins so as much axis area as possible is used within the inset bounds
    Snapshot_Figure.subplots_adjust(left=0.22, right=0.97, bottom=0.24, top=0.82)
    Snapshot_Axis.set_facecolor("none")
    Snapshot_Axis.patch.set_alpha(0.0)

    # Draw range and std deviation curves with the inset-specific marker and line sizes
    Snapshot_Axis.plot(P_Input__GPa, P_Range__GPa, color=Plot_Styling.Theme["Primary_Text"], marker="o", markersize=Snapshot_Marker_Size, linewidth=Snapshot_Curve_Style["line_lw"], label="Range (max-min)")
    Snapshot_Axis.plot(P_Input__GPa, P_Std__GPa, color=Plot_Styling.Theme["Primary_Color"], marker="s", markersize=Snapshot_Marker_Size, linewidth=Snapshot_Curve_Style["line_lw"], label="Standard Deviation")

    # Apply axis labels using the main figure's theme and font settings
    Snapshot_Axis.set_xlabel(
        X_Label,
        color=Plot_Styling.Theme["Primary_Text"],
        **Plot_Styling.Label_Font_Kwargs(Size=float(Plot_Styling.Ps["font_label"])),
    )
    Snapshot_Axis.set_ylabel(
        "Difference (GPa)",
        color=Plot_Styling.Theme["Primary_Text"],
        **Plot_Styling.Label_Font_Kwargs(Size=float(Plot_Styling.Ps["font_label"])),
    )
    Snapshot_Axis.set_title(
        "Absolute spread",
        color=Plot_Styling.Theme["Primary_Text"],
        **Plot_Styling.Title_Font_Kwargs(Size=float(Plot_Styling.Ps["font_title"])),
    )
    Snapshot_Axis.minorticks_on()
    Snapshot_Axis.tick_params(labelsize=float(Plot_Styling.Ps["font_tick"]))
    Plot_Styling.Apply_Tick_Label_Style(Snapshot_Axis)

    # Place the legend in the corner with the least data overlap
    Plot_Utilities.Place_Feature_Best_Corner(
        Snapshot_Axis,
        Feature="legend",
        Padding=Plot_Styling.Ps["spread_legend_edge_pad"],
        X_Data=P_Input__GPa,
        Y_Series=[P_Range__GPa, P_Std__GPa],
        Legend_Kwargs={"fontsize": Plot_Styling.Ps["spread_legend_font"], "markerscale": 1.0},
    )

    # Rasterize the canvas so the image array is available for cropping
    Canvas.draw()
    Renderer = Canvas.get_renderer()
    Image_Rgba = np.asarray(Canvas.buffer_rgba()).copy()
    # Get the tight bounding box of the axis content in pixel coordinates
    Tight_Bbox = Snapshot_Axis.get_tightbbox(Renderer)
    Image_Height, Image_Width = Image_Rgba.shape[0], Image_Rgba.shape[1]

    # Convert the tight bounding box to integer pixel indices, clamped to image bounds
    Px_X0 = int(np.floor(max(0.0, Tight_Bbox.x0)))
    Px_X1 = int(np.ceil(min(float(Image_Width), Tight_Bbox.x1)))
    Px_Y0 = int(np.floor(max(0.0, Tight_Bbox.y0)))
    Px_Y1 = int(np.ceil(min(float(Image_Height), Tight_Bbox.y1)))
    # numpy row indexing is top-to-bottom, so invert the y coordinates
    Row0 = max(0, Image_Height - Px_Y1)
    Row1 = min(Image_Height, Image_Height - Px_Y0)
    Col0 = max(0, Px_X0)
    Col1 = min(Image_Width, Px_X1)
    Cropped_Rgba = Image_Rgba[Row0:Row1, Col0:Col1].copy()

    # Record the data and full-image aspect ratios for downstream overlay sizing
    Crop_Height, Crop_Width = Cropped_Rgba.shape[0], Cropped_Rgba.shape[1]
    Snapshot_Meta = {
        "data_aspect": float(max(Snapshot_Axis.bbox.width, 1.0) / max(Snapshot_Axis.bbox.height, 1.0)),
        "full_aspect": float(max(Crop_Width, 1.0) / max(Crop_Height, 1.0)),
    }

    # Return the cropped RGBA array and its metadata for use by the placement logic
    return Cropped_Rgba, Snapshot_Meta


# Place a pre-rendered RGBA image as a transparent inset axis inside an existing axis
def Local__Place_Frozen_Image(Ax, Corner, Box, Image_Rgba):
    # Unpack the bounding box in axes-fraction coordinates
    Ax_X0, Ax_Y0, Ax_X1, Ax_Y1 = Box
    # Create an inset axis at the specified position within the parent axis
    Image_Axis = Ax.inset_axes([Ax_X0, Ax_Y0, Ax_X1 - Ax_X0, Ax_Y1 - Ax_Y0], transform=Ax.transAxes)
    # Map the corner name to the matplotlib anchor code for pixel-exact placement
    Anchor_Map = {
        "upper right": "NE",
        "upper left": "NW",
        "lower left": "SW",
        "lower right": "SE",
    }
    Image_Axis.set_anchor(Anchor_Map.get(Corner, "C"))
    Image_Axis.set_facecolor("none")
    Image_Axis.patch.set_alpha(0.0)
    Image_Axis.imshow(Image_Rgba, interpolation="antialiased", aspect="equal")
    Image_Axis.set_axis_off()
    # High z-order so the inset renders on top of the parent axis data
    Image_Axis.set_zorder(6)

    # Return the inset axis in case the caller needs to modify it further
    return Image_Axis




# Figure builder


# Build the two-panel summary figure with observable overlay, pressure-diff overlay, and an inset spread snapshot
def Create_Figure(Dataset, Config_Module):
    # Unpack dataset fields used across both panels. The left (observable) panel's x-axis is
    # the reference/last-calibration-study pressure (p_ref); the right (difference) panel and
    # the spread inset compare against the original input pressure (p_input).
    P_Ref__GPa = Dataset["p_ref"]
    P_Input__GPa = Dataset["p_input"]
    Observable = Dataset["observable"]
    Y_Label = Dataset["obs_label"]
    First_Label = Dataset["first_label"]
    X_Pressure_Label = Dataset.get("x_pressure_label", "Input Pressure (GPa)")
    # The left observable panel uses p_ref as x; label it with the reference study name
    Ref_P_Label = Dataset.get("ref_pressure_label", "Pressure (GPa)")

    # Identify the reference/last pressure-calibration study. Extracted here so that both
    # the Eos_Plot_List filter and the per-panel drawing blocks use the same object.
    First_Key = Dataset.get("first_key") or None
    Reference_Eos = next((Eos for Eos in Dataset["eos_list"] if First_Key and Eos["key"] == First_Key), None)

    # Comparison studies are everything except the reference; use identity so the same
    # entry is excluded regardless of key string equality edge cases.
    Eos_Plot_List = [Eos for Eos in Dataset["eos_list"] if Eos is not Reference_Eos]

    # At least one comparison study is required for the pressure-diff and spread panels
    if not Eos_Plot_List:
        raise ValueError("Summary plot requires at least one comparison EoS.")

    # Compute spread statistics across all comparison studies for the inset panel
    All_Dp__GPa = np.column_stack([Eos["data"] - P_Input__GPa for Eos in Eos_Plot_List])
    P_Range__GPa = np.nanmax(All_Dp__GPa, axis=1) - np.nanmin(All_Dp__GPa, axis=1)
    P_Std__GPa = np.nanstd(All_Dp__GPa, axis=1)

    # Compute figure and panel dimensions from the preset values
    Figure_Width = Plot_Styling.Ps["max_fig_width"] * Plot_Styling.Ps.get("summary_fig_width_scale", 1.0)
    Main_Width = Figure_Width - Plot_Styling.Ps["margin_left"] - Plot_Styling.Ps["margin_right"] - Plot_Styling.Ps["legend_col_width"] - Plot_Styling.Ps["gap"]
    Gap_Frac = Plot_Styling.Ps.get("summary_gap_frac", 0.08)
    Panel_Width = Main_Width * ((1.0 - Gap_Frac) / 2.0)
    Panel_Gap__Inches = Main_Width * Gap_Frac
    Panel_Height = Panel_Width / Plot_Styling.Ps["plot_aspect"]
    Figure_Height = Plot_Styling.Ps["margin_bottom"] + Panel_Height + Plot_Styling.Ps["margin_top"]

    # Split the main area into a narrower observable panel and a wider pressure-diff panel
    Left_Panel_Width = (Main_Width - Panel_Gap__Inches) / 2.5
    Right_Panel_Width = Left_Panel_Width * 1.5

    # Derive marker and curve dimensions from the panel size
    Marker_Size = Plot_Styling.Calculate_Marker_Size(Panel_Width, Panel_Height, Base_Marker_Size=1, Reference_Area=25.0)
    Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Marker_Size)
    # Reference line is drawn heavier than comparison curves for visual hierarchy
    Reference_Line_Width = float(max(Curve_Style["line_lw"] * 2.0, 1.2))

    # Create the figure and place the three axes in absolute inch-to-fraction coordinates
    Figure = plt.figure(figsize=(Figure_Width, Figure_Height), dpi=Plot_Styling.Ps["dpi"])
    Left__Inches = Plot_Styling.Ps["margin_left"]
    Bottom__Inches = Plot_Styling.Ps["margin_bottom"]
    Ax_Left = Figure.add_axes([Left__Inches / Figure_Width, Bottom__Inches / Figure_Height, Left_Panel_Width / Figure_Width, Panel_Height / Figure_Height])

    # Right panel sits immediately after the left panel with a gap
    Right_Left__Inches = Left__Inches + Left_Panel_Width + Panel_Gap__Inches
    Ax_Right = Figure.add_axes([Right_Left__Inches / Figure_Width, Bottom__Inches / Figure_Height, Right_Panel_Width / Figure_Width, Panel_Height / Figure_Height])

    # Legend column fills the full figure height on the far right
    Legend_Left__Inches = Right_Left__Inches + Right_Panel_Width + Plot_Styling.Ps["gap"]
    Ax_Legend = Figure.add_axes([Legend_Left__Inches / Figure_Width, 0.0, Plot_Styling.Ps["legend_col_width"] / Figure_Width, 1.0])
    Ax_Legend.axis("off")

    # Optional observable uncertainty; None when not supplied
    Obs_Unc = Dataset.get("obs_unc")
    # The original input-pressure uncertainty is only present for pressure-input workflows
    P_Input_Unc__GPa = Dataset.get("p_input_unc")

    # Build the combined legend label and handle lists. Reference is first (if present), then
    # comparisons in order — matching the structure of the standalone observable and diff plots.
    Handles = []
    Legend_Labels = []
    if Reference_Eos is not None:
        Handles.append(plt.Line2D([0], [0], color=Plot_Styling.Theme["Primary_Text"], linewidth=Reference_Line_Width))
        Legend_Labels.append(First_Label)

    # ── Left panel: Measured Value vs Pressure ────────────────────────────────
    # Mirrors Plot_Observable_Vs_Pressure.py exactly: reference as thick solid line
    # (with error bars when enabled), then comparison studies with colors and markers.
    if Reference_Eos is not None:
        Ax_Left.plot(
            P_Ref__GPa, Observable,
            color=Plot_Styling.Theme["Primary_Text"],
            linestyle="-",
            linewidth=Reference_Line_Width,
            zorder=1,
        )
        if Plot_Styling.Show_Error_Bars and (P_Input_Unc__GPa is not None or Obs_Unc is not None):
            Ax_Left.errorbar(
                P_Ref__GPa, Observable,
                xerr=P_Input_Unc__GPa,
                yerr=Obs_Unc,
                fmt="none",
                ecolor=Plot_Styling.Theme["Primary_Text"],
                alpha=0.5,
                capsize=2,
                zorder=0,
            )

    for Eos_Index, Eos in enumerate(Eos_Plot_List):
        Curve_Color = Eos.get("color", Plot_Styling.Get_Color_At_Index(Eos_Index))
        Curve_Marker = Eos.get("marker", Plot_Styling.Get_Marker_At_Index(Eos_Index))
        Plot_Utilities.Plot_Observable_Curve(
            Ax_Left,
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
        Legend_Labels.append(Eos["label"])
    Plot_Styling.Style_Ax(Ax_Left, Ref_P_Label, Y_Label, "")

    # ── Right panel: Pressure Difference ─────────────────────────────────────
    # Mirrors Plot_All_EoS_Overlay_Absolute_Pressure_Difference.py exactly:
    # reference first (thick, no markers, solid→dashed at Pmax), then comparisons.
    if Reference_Eos is not None:
        Plot_Utilities.Plot_Eos_Curve(
            Ax_Right,
            P_Input__GPa,
            Reference_Eos["data"],
            Reference_Eos["p_max"],
            Plot_Styling.Theme["Primary_Text"],
            "",
            None,
            Marker_Size=Marker_Size,
            Line_Width=Reference_Line_Width,
            Z_Order=3,
            Mode="diff",
            Curve_Cache=Reference_Eos["curve_cache"],
            P0__GPa=Reference_Eos.get("p0"),
        )

    Dp_Series__GPa = []
    for Eos_Index, Eos in enumerate(Eos_Plot_List):
        Curve_Color = Eos.get("color", Plot_Styling.Get_Color_At_Index(Eos_Index))
        Curve_Marker = Eos.get("marker", Plot_Styling.Get_Marker_At_Index(Eos_Index))
        Plot_Utilities.Plot_Eos_Curve(
            Ax_Right,
            P_Input__GPa,
            Eos["data"],
            Eos["p_max"],
            Curve_Color,
            Curve_Marker,
            None,
            Marker_Size=Marker_Size,
            Line_Width=Curve_Style["line_lw"],
            Mode="diff",
            Curve_Cache=Eos["curve_cache"],
            P0__GPa=Eos.get("p0"),
        )
        Dp_Series__GPa.append(Eos["data"] - P_Input__GPa)

    Plot_Utilities.Draw_Horizontal_Reference_Line(
        Ax_Right,
        0.0,
        X_Values=P_Input__GPa,
        Color=Plot_Styling.Theme["Secondary_Text"],
        Line_Style="--",
        Line_Width=Curve_Style["open_lw"],
        Z_Order=0,
    )
    Plot_Styling.Style_Ax(Ax_Right, X_Pressure_Label, "Pdiff (GPa)", "")

    # ── Legend column ─────────────────────────────────────────────────────────
    # Build the legend from the combined Handles/Legend_Labels assembled above.
    # Font size and column count are optimized to fit within the figure height.
    Font_Pt, Wrapped = Plot_Styling.Optimize_Legend_Font(Legend_Labels, Figure_Height)
    Num_Cols, Unused_Legend_Width = Plot_Styling.Calculate_Legend_Dimensions(
        len(Legend_Labels), Plot_Styling.Ps["entries_per_col"], 1.0, Max_Columns=Plot_Styling.Ps["max_legend_cols"]
    )
    Plot_Styling.Draw_Overlay_Legend(Ax_Legend, Handles, Wrapped, Font_Pt, Num_Cols)

    # Render the absolute-spread inset as a standalone RGBA image
    Overlay_Area_Frac = 0.30
    Abs_Spread_Image, Abs_Spread_Meta = Local__Build_Abs_Spread_Snapshot(
        P_Input__GPa, P_Range__GPa, P_Std__GPa, Right_Panel_Width, Panel_Height, X_Pressure_Label
    )
    # Derive an overlay box size that covers the target area fraction while preserving aspect
    Image_Aspect = float(Abs_Spread_Meta.get("full_aspect", 1.0))
    Overlay_Width = float(np.sqrt(Overlay_Area_Frac * Image_Aspect))
    Overlay_Height = float(np.sqrt(Overlay_Area_Frac / Image_Aspect))

    # Clamp width so the inset never overflows the right panel horizontally
    if Overlay_Width > 0.95:
        Overlay_Width = 0.95
        Overlay_Height = Overlay_Width / Image_Aspect
    # Clamp height so the inset never overflows the right panel vertically
    if Overlay_Height > 0.95:
        Overlay_Height = 0.95
        Overlay_Width = Overlay_Height * Image_Aspect

    # Force a canvas render so pixel extents of the right axis are available
    Figure.canvas.draw()
    Renderer = Figure.canvas.get_renderer()
    Axis_Bbox__Inches = Ax_Right.get_window_extent(renderer=Renderer).transformed(Figure.dpi_scale_trans.inverted())
    Axis_Width__Inches = max(float(Axis_Bbox__Inches.width), 1e-9)
    Axis_Height__Inches = max(float(Axis_Bbox__Inches.height), 1e-9)
    # Convert the preset edge-padding inches to axis-fraction units for the placement scorer
    Pad__Inches = float(max(0.0, Plot_Styling.Ps.get("summary_overlay_edge_pad_in", 0.2)))
    Pad_X = Pad__Inches / Axis_Width__Inches
    Pad_Y = Pad__Inches / Axis_Height__Inches

    # Score all four corners using a small proxy box so the full-size inset doesn't bias scoring
    Score_Width = float(np.sqrt(0.05 * Image_Aspect))
    Score_Height = float(np.sqrt(0.05 / Image_Aspect))
    Score_Boxes = Plot_Utilities.Get_Legend_Bbox_Candidates(Score_Width, Score_Height, Pad=(Pad_X, Pad_Y))
    # Project all plotted data points to axes coordinates for occlusion scoring
    Plot_Points = Plot_Utilities.Points_To_Axes_Coords(Ax_Right, X_Data=P_Input__GPa, Y_Series=Dp_Series__GPa)
    # Filter to a slightly expanded viewport to exclude pathological out-of-range points
    if Plot_Points.size:
        Plot_Points = Plot_Points[
            (Plot_Points[:, 0] >= -0.25)
            & (Plot_Points[:, 0] <= 1.25)
            & (Plot_Points[:, 1] >= -0.25)
            & (Plot_Points[:, 1] <= 1.25)
        ]
    # Score each corner by how few data points fall inside its proxy box
    Corner_Scores = {Corner: Plot_Utilities.Score_Box_Progressive(Plot_Points, Box) for Corner, Box in Score_Boxes.items()}
    # Break ties by preferring upper-right, then proceeding clockwise
    Tie_Order = ["upper right", "upper left", "lower left", "lower right"]
    Best_Corner = max(Tie_Order, key=lambda Corner: (Corner_Scores[Corner], -Tie_Order.index(Corner)))
    # Recompute bounding boxes for the full inset size at the winning corner
    Actual_Boxes = Plot_Utilities.Get_Legend_Bbox_Candidates(Overlay_Width, Overlay_Height, Pad=(Pad_X, Pad_Y))
    Local__Place_Frozen_Image(Ax_Right, Best_Corner, Actual_Boxes[Best_Corner], Abs_Spread_Image)

    # Return the completed figure for downstream PNG export
    return Figure




