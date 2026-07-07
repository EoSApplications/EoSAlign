# Load libraries
    # Load third-party libraries
import matplotlib.pyplot as plt
import numpy as np

    # Load local libraries
import Plot_Styling
import Plot_Utilities




Figure_Basename = "individual_absolute_pressure_difference"




# Figure builder


# Build the individual-panel absolute pressure-difference figure and return it
def Create_Figure(Dataset, Config_Module):
    # Unpack pressure axis, EoS list, and axis label from the pre-built dataset
    P_Input__GPa = Dataset["p_input"]
    Eos_List = Dataset["eos_list"]
    First_Key = Dataset["first_key"]
    X_Pressure_Label = Dataset.get("x_pressure_label", "Input Pressure (GPa)")

    # Each comparison study gets its own panel; the reference study is excluded
    Eos_List_Filtered = [Eos for Eos in Eos_List if Eos["key"] != First_Key]

    # At least one comparison study is required to draw any panels
    if not Eos_List_Filtered:
        raise ValueError("No individual EoS panels are available for absolute pressure-difference plotting.")

    # Use overlay dimensions as a proxy for the base plot size used in marker scaling
    Plot_Width, Plot_Height, Unused_Figure_Width, Unused_Figure_Height = Plot_Styling.Get_Overlay_Dimensions()
    # Each square panel is half the maximum figure width
    Panel_Side = 0.5 * Plot_Styling.Ps["max_fig_width"]
    # Double the base marker size for individual panels so they read clearly at smaller scale
    Marker_Size = 2.0 * Plot_Styling.Calculate_Marker_Size(Plot_Width, Plot_Height, Base_Marker_Size=1, Reference_Area=25.0)
    Curve_Style = Plot_Utilities.Curve_Style_From_Marker_Size(Marker_Size)

    # Read layout parameters from the config module, falling back to sensible defaults
    Panel_Gap = float(getattr(Config_Module, "Individual_Panel_Gap__Inches", 0.90))
    Individuals_Across = getattr(Config_Module, "Individuals_Across", 4)
    Render_Dpi = getattr(Config_Module, "Individual_Render_Dpi", Plot_Styling.Ps["dpi"]) or Plot_Styling.Ps["dpi"]

    # If no column count is specified, fit as many panels as the max figure width allows
    if Individuals_Across is None:
        Usable_Width = max(Plot_Styling.Ps["max_fig_width"] - Plot_Styling.Ps["margin_left"] - Plot_Styling.Ps["margin_right"], Panel_Side)
        Num_Cols = max(1, int(np.floor((Usable_Width + Panel_Gap) / (Panel_Side + Panel_Gap))))
    # Otherwise use the explicit column count from the config
    else:
        Num_Cols = max(1, int(Individuals_Across))

    # Clamp columns to the actual number of panels so no empty columns are reserved
    Num_Cols = min(Num_Cols, len(Eos_List_Filtered))
    Num_Rows = int(np.ceil(len(Eos_List_Filtered) / Num_Cols))

    # Compute the full figure dimensions from the panel grid plus margins
    Grid_Width = Num_Cols * Panel_Side + (Num_Cols - 1) * Panel_Gap
    Grid_Height = Num_Rows * Panel_Side + (Num_Rows - 1) * Panel_Gap
    Figure_Width = Grid_Width + Plot_Styling.Ps["margin_left"] + Plot_Styling.Ps["margin_right"]

    # Reserve extra headroom above the panel grid for the (two-line) per-panel titles in the
    # top row plus a clearly separated figure-level suptitle, so the suptitle never crowds or
    # clips against the panel titles below it.
    Panel_Title_Height = (2 * Plot_Styling.Ps["font_title"] * Plot_Styling.Ps["line_spacing"]) / 72
    Suptitle_Height = ((Plot_Styling.Ps["font_title"] + 2) * Plot_Styling.Ps["line_spacing"] * Plot_Styling.Ps["spread_suptitle_lines"]) / 72
    Suptitle_Gap = ((Plot_Styling.Ps["font_title"] + 2) * Plot_Styling.Ps["line_spacing"] * Plot_Styling.Ps["spread_suptitle_gap"] * 2) / 72
    Figure_Height = (
        Grid_Height + Plot_Styling.Ps["margin_bottom"] + Plot_Styling.Ps["margin_top"]
        + Panel_Title_Height + Suptitle_Gap + Suptitle_Height
    )

    Figure = plt.figure(figsize=(Figure_Width, Figure_Height), dpi=Render_Dpi)

    # Pre-allocate axes in row-major order; data is drawn in the second loop below
    Axes_List = []
    for Eos_Index, Unused_Eos in enumerate(Eos_List_Filtered):
        # Compute the row and column position for this panel
        Panel_Row = Eos_Index // Num_Cols
        Panel_Col = Eos_Index % Num_Cols
        # Convert grid coordinates to figure fractions for add_axes
        Left__Inches = Plot_Styling.Ps["margin_left"] + Panel_Col * (Panel_Side + Panel_Gap)
        Bottom__Inches = Plot_Styling.Ps["margin_bottom"] + (Num_Rows - 1 - Panel_Row) * (Panel_Side + Panel_Gap)
        Axes_List.append(
            Figure.add_axes(
                [
                    Left__Inches / Figure_Width,
                    Bottom__Inches / Figure_Height,
                    Panel_Side / Figure_Width,
                    Panel_Side / Figure_Height,
                ]
            )
        )

    # Draw each EoS curve into its corresponding panel axis
    for Eos_Index, Eos in enumerate(Eos_List_Filtered):
        Axis = Axes_List[Eos_Index]
        # Use per-study color/marker overrides if present, otherwise cycle the palette
        Curve_Color = Eos.get("color", Plot_Styling.Get_Color_At_Index(Eos_Index))
        Curve_Marker = Eos.get("marker", Plot_Styling.Get_Marker_At_Index(Eos_Index))
        Plot_Utilities.Plot_Eos_Curve(
            Axis,
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
        # Draw the zero-difference reference line as a dashed guide
        Plot_Utilities.Draw_Horizontal_Reference_Line(
            Axis,
            0.0,
            X_Values=P_Input__GPa,
            Color=Plot_Styling.Theme["Secondary_Text"],
            Line_Style="--",
            Line_Width=Curve_Style["open_lw"],
            Z_Order=0,
        )
        # Build a two-line panel title from the study name and its max-pressure label
        Pmax_Label = f"Pmax = {Eos['p_max']:.0f} GPa" if np.isfinite(Eos["p_max"]) else "Pmax: N/A"
        Study_Label = Plot_Styling.Wrap_Label(Eos["author"], Plot_Styling.Ps["font_title"], Max_Extent__Pt=Panel_Side * 72.0)
        Tail_Label = Plot_Styling.Wrap_Label(f"{Eos['form']} | {Pmax_Label}", Plot_Styling.Ps["font_title"], Max_Extent__Pt=Panel_Side * 72.0)
        Plot_Styling.Style_Ax(Axis, X_Pressure_Label, "Pdiff (GPa)", f"{Study_Label}\n{Tail_Label}")

    # Add a shared supertitle identifying the composition and figure type, dynamically placed
    # a full line above the tallest panel title so it never crowds or clips against them
    Plot_Styling.Place_Spread_Suptitle(
        Figure,
        Axes_List,
        f"{Dataset['inputs']['composition']} - Individual EoS (Pdiff)\n{Plot_Styling.Sym_Note}",
        Gap_Lines=2,
    )

    # Return the completed figure for downstream PNG export
    return Figure




