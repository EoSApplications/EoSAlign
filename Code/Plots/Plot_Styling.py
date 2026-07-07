# Load libraries
    # Load standard libraries
import re
import textwrap
    # Load third-party libraries
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np




# Default style parameters


# Default plot style parameter dictionary
#   All values may be overridden per-run by the config module passed to Apply_Plot_Style
Default_Ps = dict(
    max_fig_width=7.09,
    summary_fig_width_scale=2.0,
    summary_gap_frac=0.06,
    summary_overlay_edge_pad=0.03,
    plot_aspect=11 / 7,
    margin_left=0.50,
    margin_right=0.20,
    margin_bottom=0.50,
    margin_top=0.50,
    gap=0.20,
    legend_col_width=1.50,
    max_legend_cols=1,
    entries_per_col=20,
    labelspacing=0.30,
    borderpad=0.40,
    handlelength=0.80,
    handletextpad=0.30,
    columnspacing=0.30,
    line_spacing=1.20,
    font_label=7,
    font_title=8,
    font_tick=6,
    font_legend_max=8.0,
    font_legend_min=1.0,
    title_bold=False,
    title_italic=False,
    label_bold=False,
    label_italic=False,
    tick_bold=False,
    tick_italic=False,
    spread_panel_frac=0.45,
    spread_gap_frac=0.10,
    spread_legend_font=5.0,
    spread_legend_edge_pad=0.06,
    marker_size=3.0,
    line_width_ratio=0.20,
    spread_suptitle_lines=2,
    spread_suptitle_gap=1.0,
    dpi=500,
)

# Default theme color dictionary
#   Colors are hex strings used for text, backgrounds, and accent elements
Default_Theme = {
    "Primary_Text": "#111111",
    "Secondary_Text": "#212121",
    "Primary_Color": "#FABE60",
    "Secondary_Background": "#FFFFFF",
    "Primary_Background": "#FFFFFF",
}

# Ordered list of matplotlib marker shapes for cycling through calibration studies
Markers = ["o", "s", "^", "D", "v", "<", ">", "p", "h", "*", "P", "X", "d", "8", "H"]

# Ordered array of tab20 colors for cycling through calibration studies
Colors = plt.cm.tab20(np.linspace(0, 1, 20))

# Annotation appended to figure titles to explain open vs filled marker semantics
Sym_Note = "(filled = within $P_{max}$, open = beyond $P_{max}$)"


# Module-level mutable style state


# Active plot style params dict — copy of Default_Ps, updated each run by Apply_Plot_Style
Ps = dict(Default_Ps)

# Active theme color dict — copy of Default_Theme, updated each run by Apply_Plot_Style
Theme = dict(Default_Theme)

# Whether to draw confidence bands behind calibration curves
Show_Bands = True

# Whether to draw error bars on data points
Show_Error_Bars = False

# Whether to draw grid lines on axes
Show_Grid = False


# Apply style


# Reset all module globals to defaults then apply any overrides from the config module
def Apply_Plot_Style(Config_Module=None):
    # Declare intent to modify the module-level globals
    global Ps, Theme, Show_Bands, Show_Error_Bars, Show_Grid

    # Start from a clean copy of the defaults so previous runs do not bleed into this one
    Ps = dict(Default_Ps)
    Theme = dict(Default_Theme)

    # Apply any overrides provided by the figure config module
    if Config_Module is not None:
        # Merge style parameter overrides from the config; skip if the attribute is absent or None
        Ps.update(getattr(Config_Module, "Ps_Overrides", {}) or {})
        # Merge theme color overrides from the config
        Theme.update(getattr(Config_Module, "Theme_Overrides", {}) or {})
        # Read band, error bar, and grid toggles from the config
        Show_Bands = bool(getattr(Config_Module, "Show_Bands", True))
        Show_Error_Bars = bool(getattr(Config_Module, "Show_Error_Bars", False))
        Show_Grid = bool(getattr(Config_Module, "Show_Grid", False))
    # No config module given — reset toggles to their hardcoded defaults
    else:
        Show_Bands = True
        Show_Error_Bars = False
        Show_Grid = False

    # Pull theme colors into local variables for the rcParams block below
    Text_Color = Theme.get("Primary_Text", "#111111")
    Edge_Color = Theme.get("Secondary_Text", "#212121")
    Background_Color = Theme.get("Secondary_Background", "white")
    Figure_Color = Theme.get("Primary_Background", "white")

    # Reset matplotlib to its built-in defaults before applying our overrides
    plt.style.use("default")

    # Apply all visual style settings to matplotlib's global rcParams
    plt.rcParams.update(
        {
            # Background colors for the figure canvas and individual axes
            "figure.facecolor": Figure_Color,
            "axes.facecolor": Background_Color,

            # Base font size and text color for all text elements
            "font.size": 11,
            "text.color": Text_Color,
            "axes.labelcolor": Text_Color,
            "axes.titlecolor": Text_Color,

            # Axis spine line weight and color
            "axes.linewidth": 1.2,
            "axes.edgecolor": Text_Color,

            # Tick mark and tick label colors and directions
            "xtick.color": Text_Color,
            "ytick.color": Text_Color,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.minor.size": 3,
            "ytick.minor.size": 3,
            # Mirror ticks on all four sides for a publication-style look
            "xtick.top": True,
            "ytick.right": True,

            # Grid line appearance
            "grid.color": Text_Color,
            "grid.alpha": 0.2,
            "grid.linewidth": 0.6,

            # Legend appearance
            "legend.fontsize": 8,
            "legend.frameon": True,
            "legend.facecolor": Background_Color,
            "legend.edgecolor": Edge_Color,

            # DPI for on-screen and saved figures
            "figure.dpi": Ps["dpi"],
            "savefig.dpi": "figure",
        }
    )


# Color and marker cycling


# Return the color at the given index, wrapping cyclically through the Colors array
def Get_Color_At_Index(Index):
    # Modulo ensures the index wraps rather than going out of bounds
    return Colors[Index % len(Colors)]


# Return the marker shape at the given index, wrapping cyclically through the Markers list
def Get_Marker_At_Index(Index):
    # Modulo ensures the index wraps rather than going out of bounds
    return Markers[Index % len(Markers)]


# Font helpers


# Return the matplotlib font weight string for a given text role based on active style params
def Local__Font_Weight(Role, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Return "bold" or "normal" based on the role's bold flag in the active style
    return "bold" if bool(Active_Ps.get(f"{Role}_bold", False)) else "normal"


# Return the matplotlib font style string for a given text role based on active style params
def Local__Font_Style(Role, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Return "italic" or "normal" based on the role's italic flag in the active style
    return "italic" if bool(Active_Ps.get(f"{Role}_italic", False)) else "normal"


# Return a kwargs dict for matplotlib title text using the active style params
def Title_Font_Kwargs(Size=None, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Return the font size, weight, and style as a single dict for **kwargs unpacking
    return {
        "fontsize": Active_Ps["font_title"] if Size is None else Size,
        "fontweight": Local__Font_Weight("title", Active_Ps),
        "fontstyle": Local__Font_Style("title", Active_Ps),
    }


# Return a kwargs dict for matplotlib axis label text using the active style params
def Label_Font_Kwargs(Size=None, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Return the font size, weight, and style as a single dict for **kwargs unpacking
    return {
        "fontsize": Active_Ps["font_label"] if Size is None else Size,
        "fontweight": Local__Font_Weight("label", Active_Ps),
        "fontstyle": Local__Font_Style("label", Active_Ps),
    }


# Return a kwargs dict for matplotlib tick label text using the active style params
def Tick_Font_Kwargs(Size=None, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Return the font size, weight, and style as a single dict for **kwargs unpacking
    return {
        "fontsize": Active_Ps["font_tick"] if Size is None else Size,
        "fontweight": Local__Font_Weight("tick", Active_Ps),
        "fontstyle": Local__Font_Style("tick", Active_Ps),
    }


# Apply the active tick font style to all tick labels on both axes of the given Axes object
def Apply_Tick_Label_Style(Ax, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Tick_Kwargs = Tick_Font_Kwargs(Ps_Override=Active_Ps)
    # Collect tick labels from both axes into one list to loop over together
    for Label in list(Ax.get_xticklabels()) + list(Ax.get_yticklabels()):
        Label.set_fontsize(Tick_Kwargs["fontsize"])
        Label.set_fontweight(Tick_Kwargs["fontweight"])
        Label.set_fontstyle(Tick_Kwargs["fontstyle"])
        Label.set_color(Theme["Primary_Text"])


# Figure dimension helpers


# Return the marker size scaled to the actual plot area relative to the reference area
#   Base size comes from the style params override when set, otherwise Base_Marker_Size
def Calculate_Marker_Size(Plot_Width__Inches, Plot_Height__Inches, Base_Marker_Size=3.0, Reference_Area=25.0):
    # Start from the style-param override when one is set; otherwise use the caller-supplied default
    Base = float(Ps.get("marker_size", Base_Marker_Size))
    # Scale by the square root of actual plot area vs reference area so markers grow with the plot
    Plot_Area = max(float(Plot_Width__Inches) * float(Plot_Height__Inches), 1e-6)
    Scale_Factor = (Plot_Area / max(float(Reference_Area), 1e-6)) ** 0.5
    # Clamp to a safe range so markers never become microscopic or absurdly large
    return float(np.clip(Base * Scale_Factor, 0.5, 20.0))


# Return (num_columns, total_legend_width) for a legend with the given number of entries
def Calculate_Legend_Dimensions(Num_Entries, Entries_Per_Column=20, Column_Width__Inches=1.0, Max_Columns=2):
    # Distribute entries across columns, clamped to the maximum allowed column count
    Num_Columns = min(Max_Columns, max(1, int(np.ceil(Num_Entries / Entries_Per_Column))))
    # Return the column count and total width so callers can size the legend axes
    return Num_Columns, Num_Columns * Column_Width__Inches


# Return (plot_width, plot_height, figure_width, figure_height) for an overlay figure layout
#   An overlay figure has a plot panel on the left and a legend panel on the right
def Get_Overlay_Dimensions(Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Subtract fixed margins and the legend panel width to get the usable plot area
    Plot_Width = Active_Ps["max_fig_width"] - Active_Ps["margin_left"] - Active_Ps["margin_right"] - Active_Ps["legend_col_width"] - Active_Ps["gap"]
    # Height is derived from width using the target aspect ratio
    Plot_Height = Plot_Width / Active_Ps["plot_aspect"]
    Figure_Width = Active_Ps["max_fig_width"]
    Figure_Height = Active_Ps["margin_bottom"] + Plot_Height + Active_Ps["margin_top"]
    # Return all four dimensions so callers can place axes by exact inches
    return Plot_Width, Plot_Height, Figure_Width, Figure_Height


# Return (plot_width, plot_height, figure_width, figure_height) for a single-panel figure layout
def Local__Single_Dimensions(Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    # Subtract only the margins — no legend panel on the right
    Plot_Width = Active_Ps["max_fig_width"] - Active_Ps["margin_left"] - Active_Ps["margin_right"]
    Plot_Height = Plot_Width / Active_Ps["plot_aspect"]
    Figure_Width = Active_Ps["max_fig_width"]
    Figure_Height = Active_Ps["margin_bottom"] + Plot_Height + Active_Ps["margin_top"]
    # Return all four dimensions so callers can place axes by exact inches
    return Plot_Width, Plot_Height, Figure_Width, Figure_Height


# Return dimension tuple for the two-panel disagreement spread figure layout
def Local__Spread_Panel_Dimensions(Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Figure_Width = Active_Ps["max_fig_width"]
    # The usable width is everything inside the left and right margins
    Usable_Width = Figure_Width - Active_Ps["margin_left"] - Active_Ps["margin_right"]

    # Two equal panels with a gap between them, sized as fractions of usable width
    Panel_Frac = Active_Ps["spread_panel_frac"]
    Gap_Frac = Active_Ps["spread_gap_frac"]
    Total_Frac = 2 * Panel_Frac + Gap_Frac
    Panel_Width = Usable_Width * (Panel_Frac / Total_Frac)
    Gap_Width = Usable_Width * (Gap_Frac / Total_Frac)
    Panel_Height = Panel_Width / Active_Ps["plot_aspect"]

    # Reserve vertical space for per-axis titles and the figure-level suptitle
    Title_Height = (Active_Ps["font_title"] * Active_Ps["line_spacing"]) / 72
    Suptitle_Height = ((Active_Ps["font_title"] + 2) * Active_Ps["line_spacing"] * Active_Ps["spread_suptitle_lines"]) / 72
    Suptitle_Gap = ((Active_Ps["font_title"] + 2) * Active_Ps["line_spacing"] * Active_Ps["spread_suptitle_gap"]) / 72
    Figure_Height = Active_Ps["margin_bottom"] + Panel_Height + Active_Ps["margin_top"] + Title_Height + Suptitle_Gap + Suptitle_Height

    # Return all five values so Make_Spread_Disagreement_Figure can place axes precisely
    return Panel_Width, Panel_Height, Gap_Width, Figure_Width, Figure_Height


# Find the largest font size that fits all legend labels into the available legend height
#   Uses a binary search over font sizes, wrapping each label at each candidate size
def Optimize_Legend_Font(Labels, Legend_Height__Inches, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Legend_Width = Active_Ps["legend_col_width"]
    Label_Spacing = Active_Ps["labelspacing"]
    Border_Pad = Active_Ps["borderpad"]
    Handle_Length = Active_Ps["handlelength"]
    Handle_Text_Pad = Active_Ps["handletextpad"]
    Line_Spacing = Active_Ps["line_spacing"]

    # Determine how many columns the legend will use
    Num_Columns, Unused_Legend_Width = Calculate_Legend_Dimensions(
        len(Labels),
        Active_Ps["entries_per_col"],
        1.0,
        Max_Columns=Active_Ps["max_legend_cols"],
    )
    Entries_Per_Column = int(np.ceil(len(Labels) / Num_Columns))

    # Start with the minimum allowed font size as the fallback
    Best_Font_Size = Active_Ps["font_legend_min"]
    Best_Wrapped = {Label_Index: Label_Text for Label_Index, Label_Text in enumerate(Labels)}

    # Binary search between the minimum and maximum font size
    Low = Active_Ps["font_legend_min"]
    High = Active_Ps["font_legend_max"]

    while High - Low > 0.01:
        Font_Size = (Low + High) / 2

        # Estimate how many characters fit on one line at this font size
        #   Available text width = legend width minus handle and padding overhead
        Available_Width__Inches = max(0.1, Legend_Width - (Handle_Length + Handle_Text_Pad + 2 * Border_Pad) * Font_Size / 72)
        Chars = max(5, int(Available_Width__Inches * 72 / (0.55 * Font_Size)))

        # Wrap every label to the computed character width
        Wrapped = {Label_Index: "\n".join(textwrap.wrap(Label_Text, Chars)) for Label_Index, Label_Text in enumerate(Labels)}

        # Count total line count across all wrapped labels
        Line_Count = sum(Label_Text.count("\n") + 1 for Label_Text in Wrapped.values())

        # Estimate the total height consumed by all labels at this font size
        Needed_Height = Font_Size * (Line_Count * Line_Spacing + Entries_Per_Column * Label_Spacing + 2 * Border_Pad) / 72

        # If everything fits at this font size, keep it as the best so far and try larger
        if Needed_Height <= Legend_Height__Inches:
            Best_Font_Size = Font_Size
            Best_Wrapped = Wrapped
            Low = Font_Size
        # Otherwise the font is too large and we need to try smaller
        else:
            High = Font_Size

    # Return the largest font that fit and its corresponding wrapped label dict
    return Best_Font_Size, Best_Wrapped


# Figure builders


# Create and return a complete overlay figure with a plot panel and a legend panel
def Make_Overlay_Figure(Eos_Labels, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Plot_Width, Plot_Height, Figure_Width, Figure_Height = Get_Overlay_Dimensions(Active_Ps)
    Marker_Size = Calculate_Marker_Size(Plot_Width, Plot_Height, Base_Marker_Size=1, Reference_Area=25.0)

    # Determine column count for the legend
    Num_Columns, Unused_Legend_Width = Calculate_Legend_Dimensions(
        len(Eos_Labels),
        Active_Ps["entries_per_col"],
        1.0,
        Max_Columns=Active_Ps["max_legend_cols"],
    )

    # Find the largest font size that fits all legend labels
    Font_Pt, Wrapped = Optimize_Legend_Font(Eos_Labels, Figure_Height, Active_Ps)

    # Create the figure at exact physical size in inches
    Figure = plt.figure(figsize=(Figure_Width, Figure_Height), dpi=Active_Ps["dpi"])

    # Place the plot axes using absolute inches converted to figure fractions
    Plot_Left = Active_Ps["margin_left"] / Figure_Width
    Plot_Bottom = Active_Ps["margin_bottom"] / Figure_Height
    Plot_Width_Norm = Plot_Width / Figure_Width
    Plot_Height_Norm = Plot_Height / Figure_Height
    Ax_Plot = Figure.add_axes([Plot_Left, Plot_Bottom, Plot_Width_Norm, Plot_Height_Norm])

    # Place the legend axes to the right of the plot, separated by the gap parameter
    Legend_Left = (Active_Ps["margin_left"] + Plot_Width + Active_Ps["gap"]) / Figure_Width
    Ax_Legend = Figure.add_axes([Legend_Left, Plot_Bottom, Active_Ps["legend_col_width"] / Figure_Width, Plot_Height_Norm])
    Ax_Legend.axis("off")

    # Return everything callers need to populate and style the figure
    return Figure, Ax_Plot, Ax_Legend, Marker_Size, Font_Pt, Wrapped, Num_Columns


# Create and return a single-panel figure with no legend axes
def Make_Single_Figure(Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Plot_Width, Plot_Height, Figure_Width, Figure_Height = Local__Single_Dimensions(Active_Ps)
    Marker_Size = Calculate_Marker_Size(Plot_Width, Plot_Height, Base_Marker_Size=1, Reference_Area=25.0)

    # Create the figure and add a single plot axes filling the available space
    Figure = plt.figure(figsize=(Figure_Width, Figure_Height), dpi=Active_Ps["dpi"])
    Axis = Figure.add_axes(
        [
            Active_Ps["margin_left"] / Figure_Width,
            Active_Ps["margin_bottom"] / Figure_Height,
            Plot_Width / Figure_Width,
            Plot_Height / Figure_Height,
        ]
    )
    # Return the figure, the single axes, and the computed marker size
    return Figure, Axis, Marker_Size


# Create and return a two-panel disagreement figure with absolute and relative difference panels
def Make_Spread_Disagreement_Figure(Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override
    Panel_Width, Panel_Height, Gap_Width, Figure_Width, Figure_Height = Local__Spread_Panel_Dimensions(Active_Ps)

    Figure = plt.figure(figsize=(Figure_Width, Figure_Height), dpi=Active_Ps["dpi"])
    Left = Active_Ps["margin_left"]
    Bottom = Active_Ps["margin_bottom"]

    # Place the left panel (absolute difference) starting at the left margin
    Ax_Left = Figure.add_axes([Left / Figure_Width, Bottom / Figure_Height, Panel_Width / Figure_Width, Panel_Height / Figure_Height])

    # Place the right panel (relative difference) immediately after the gap
    Ax_Right_Left = Left + Panel_Width + Gap_Width
    Ax_Right = Figure.add_axes([Ax_Right_Left / Figure_Width, Bottom / Figure_Height, Panel_Width / Figure_Width, Panel_Height / Figure_Height])

    Marker_Size = Calculate_Marker_Size(Panel_Width, Panel_Height, Base_Marker_Size=1.0, Reference_Area=25.0)

    # Return the figure, both axes panels, and the computed marker size
    return Figure, Ax_Left, Ax_Right, Marker_Size


# Axes styling


# Apply all active style settings to a single Axes object
def Style_Ax(Ax, X_Label="", Y_Label="", Title="", Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override

    # Set axis labels and title with the active font styles
    Ax.set_xlabel(X_Label, color=Theme["Primary_Text"], **Label_Font_Kwargs(Ps_Override=Active_Ps))
    Ax.set_ylabel(Y_Label, color=Theme["Primary_Text"], **Label_Font_Kwargs(Ps_Override=Active_Ps))
    Ax.set_title(Title, color=Theme["Primary_Text"], **Title_Font_Kwargs(Ps_Override=Active_Ps))
    Ax.set_facecolor(Theme["Secondary_Background"])

    # Style all four spines with the active text color and a consistent line weight
    for Spine in Ax.spines.values():
        Spine.set_color(Theme["Primary_Text"])
        Spine.set_linewidth(1.2)

    # Configure major tick marks
    Ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        colors=Theme["Primary_Text"],
        length=5,
        labelsize=Active_Ps["font_tick"],
    )
    # Configure minor tick marks
    Ax.tick_params(
        axis="both",
        which="minor",
        direction="in",
        top=True,
        right=True,
        colors=Theme["Primary_Text"],
        length=3,
    )

    # Turn on minor ticks with automatic 2-subdivision on each axis
    Ax.minorticks_on()
    Ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    Ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    # Ensure label colors match the text color (set_xlabel may not always propagate)
    Ax.xaxis.label.set_color(Theme["Primary_Text"])
    Ax.yaxis.label.set_color(Theme["Primary_Text"])
    Ax.title.set_color(Theme["Primary_Text"])

    # Apply tick label font style and color
    Apply_Tick_Label_Style(Ax, Active_Ps)

    # Show or hide the grid based on the active module-level toggle
    Ax.grid(bool(Show_Grid), which="both", axis="both")


# Draw the overlay legend in the dedicated legend axes panel
def Draw_Overlay_Legend(Ax_Legend, Handles, Wrapped, Font_Pt, Num_Cols, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override

    # Create the legend using the optimized font size and wrapped label strings
    Legend = Ax_Legend.legend(
        Handles,
        list(Wrapped.values()),
        fontsize=Font_Pt,
        loc="center",
        frameon=False,
        fancybox=False,
        shadow=False,
        handlelength=Active_Ps["handlelength"],
        handletextpad=Active_Ps["handletextpad"],
        columnspacing=Active_Ps["columnspacing"],
        labelspacing=Active_Ps["labelspacing"],
        borderpad=Active_Ps["borderpad"],
        ncol=Num_Cols,
        markerscale=1.0,
    )
    # Apply the active text color to each legend label
    for Label_Text in Legend.get_texts():
        Label_Text.set_color(Theme["Primary_Text"])

    # Return the legend artist so callers can further adjust it if needed
    return Legend


# Position the figure suptitle above the highest axis title, then return the suptitle artist
def Place_Spread_Suptitle(Fig, Axes, Text, Ps_Override=None, Gap_Lines=1):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Ps if Ps_Override is None else Ps_Override

    # The suptitle is slightly larger than per-panel titles for visual hierarchy
    Font_Size = Active_Ps["font_title"] + 2
    Suptitle = Fig.suptitle(
        Text,
        color=Theme["Primary_Text"],
        x=0.5,
        y=0.99,
        ha="center",
        **Title_Font_Kwargs(Size=Font_Size, Ps_Override=Active_Ps),
    )

    # Render the canvas to get accurate bounding boxes for the axis titles
    Fig.canvas.draw()
    Renderer = Fig.canvas.get_renderer()

    # Collect the top edge of each axis title that has text
    Title_Tops = []
    for Ax in Axes:
        if Ax.get_title():
            Title_Tops.append(Ax.title.get_window_extent(renderer=Renderer).y1)

    # If no axis has a title, leave the suptitle at its default y position
    if not Title_Tops:
        return Suptitle

    # Position the suptitle Gap_Lines line-heights above the tallest axis title
    Tallest_Top = max(Title_Tops)
    Line_Height__Px = Font_Size * Active_Ps["line_spacing"] * Fig.dpi / 72.0 * max(1, int(Gap_Lines))
    Suptitle_Bbox = Suptitle.get_window_extent(renderer=Renderer)
    Desired_Bottom = Tallest_Top + Line_Height__Px
    Desired_Top = Desired_Bottom + Suptitle_Bbox.height

    # Clamp to just inside the figure boundary
    Suptitle.set_y(min(0.995, Desired_Top / Fig.bbox.height))

    # Return the suptitle artist in case the caller needs to adjust it further
    return Suptitle


# Label formatting


# Wrap a text label to fit within a given character width or physical extent in points
def Wrap_Label(Text, Font_Size, Max_Extent__Pt=None, Width=None):
    # Estimate the wrap width from the physical extent if given
    if Max_Extent__Pt is not None:
        # Approximate average glyph width for the given font size (0.56 * pt ≈ average character width)
        Average_Glyph_Width = max(1.0, 0.56 * max(1, Font_Size))
        Width = max(6, int(Max_Extent__Pt / Average_Glyph_Width))
    # Fall back to a proportional default width when no extent is specified
    elif Width is None:
        Base_Width = 15
        Width = max(6, int(Base_Width * 12 / max(1, Font_Size)))

    # Tokenize the label, treating parenthesized groups as atomic tokens
    Tokens = re.findall(r"\([^)]*\)|[^\s]+", str(Text))

    # An empty token list produces an empty string
    if not Tokens:
        return ""

    # Greedy line-packing: accumulate tokens until the next token would exceed the width limit
    Lines = []
    Current_Line = Tokens[0]
    for Token in Tokens[1:]:
        Candidate = f"{Current_Line} {Token}"
        # Append the token to the current line if it still fits
        if len(Candidate) <= Width:
            Current_Line = Candidate
        # Otherwise flush the current line and start a new one
        else:
            Lines.append(Current_Line)
            Current_Line = Token

    # Flush the last line
    Lines.append(Current_Line)

    # Return the wrapped label as a newline-joined string
    return "\n".join(Lines)




