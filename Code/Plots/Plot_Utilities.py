# Load libraries
    # Load third-party libraries
import matplotlib.pyplot as plt
import numpy as np
    # Load local libraries
import Plot_Styling




# Pressure masking


# Return (within_mask, beyond_mask) boolean arrays based on whether x values are within P_max
def Compute_Pmax_Masks(X_Values, P_Max__GPa, P_Max_Specified=True):
    X_Values = np.asarray(X_Values, dtype=float)

    # When a finite maximum pressure is specified, split into within-range and beyond-range
    if bool(P_Max_Specified) and np.isfinite(P_Max__GPa):
        Within_Mask = X_Values <= P_Max__GPa
        Beyond_Mask = X_Values > P_Max__GPa
    # When no maximum is specified, treat all finite values as beyond-range (no within-range)
    else:
        Within_Mask = np.zeros_like(X_Values, dtype=bool)
        Beyond_Mask = np.isfinite(X_Values)

    # Return the two masks for downstream segment rendering decisions
    return Within_Mask, Beyond_Mask


# Curve cache builder


# Pre-compute all curve variants (diff, pct, ratio) for a calibration study and cache them
#   The cache avoids recomputing these arrays each time a figure script draws a curve
def Build_Eos_Curve_Cache(P_Input__GPa, P_Eos__GPa, P_Max__GPa, P_Max_Specified=True, P_Unc=None, X_Unc=None):
    P_Input__GPa = np.asarray(P_Input__GPa, dtype=float)
    P_Eos__GPa = np.asarray(P_Eos__GPa, dtype=float)

    # Convert optional uncertainty arrays to numpy, keeping None when not provided
    P_Unc_Array = np.asarray(P_Unc, dtype=float) if P_Unc is not None else None
    X_Unc_Array = np.asarray(X_Unc, dtype=float) if X_Unc is not None else None

    # Absolute pressure difference: y = P_eos - P_input, x = P_input
    X_Diff = P_Input__GPa
    Y_Diff = P_Eos__GPa - X_Diff
    Within_Diff, Beyond_Diff = Compute_Pmax_Masks(X_Diff, P_Max__GPa, P_Max_Specified)

    # Relative arrays exclude points below 0.1 GPa to avoid division-by-near-zero
    Valid_Relative_Mask = P_Input__GPa > 0.1
    X_Relative = P_Input__GPa[Valid_Relative_Mask]
    P_Eos_Relative = P_Eos__GPa[Valid_Relative_Mask]

    # Percent difference: (P_eos - P_ref) / P_ref * 100
    Y_Percent = (P_Eos_Relative - X_Relative) / X_Relative * 100

    # Pressure ratio: P_eos / P_ref
    Y_Ratio = P_Eos_Relative / X_Relative

    Within_Relative, Beyond_Relative = Compute_Pmax_Masks(X_Relative, P_Max__GPa, P_Max_Specified)

    # Return a dict keyed by display mode; each value is (x, y, within_mask, beyond_mask)
    return {
        "diff": (X_Diff, Y_Diff, Within_Diff, Beyond_Diff),
        "pct": (X_Relative, Y_Percent, Within_Relative, Beyond_Relative),
        "ratio": (X_Relative, Y_Ratio, Within_Relative, Beyond_Relative),
        # Percent plots currently suppress uncertainty display entirely
        "xerr": {"diff": X_Unc_Array, "pct": None},
        "yerr": {"diff": P_Unc_Array, "pct": None},
    }


# Curve style helpers


# Return a dict of line and marker style parameters derived from a base marker size
def Curve_Style_From_Marker_Size(Marker_Size, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Plot_Styling.Ps if Ps_Override is None else Ps_Override
    Marker_Size = float(Marker_Size)
    # Line width is a fixed ratio of the marker size to keep proportions consistent
    Line_Width = float(Marker_Size * Active_Ps.get("line_width_ratio", 0.20))
    # Return a dict so callers can unpack only the keys they need
    return {
        "ms": Marker_Size,
        "line_lw": Line_Width,
        "open_lw": Line_Width,
        "open_mew": Line_Width,
        "legend_lw": Line_Width,
        "legend_ms": Marker_Size,
    }


# EoS curve plotting


# Plot a single EoS curve onto an axes, handling within-range, beyond-range, and below-P0 segments
def Plot_Eos_Curve(
    Ax,
    P_Input__GPa,
    P_Eos__GPa,
    P_Max__GPa,
    Color,
    Marker,
    Label,
    Marker_Size=4,
    Line_Width=None,
    Z_Order=2,
    Mode="diff",
    Curve_Cache=None,
    P_Max_Specified=True,
    P0__GPa=None,
    Show_Bands=None,
    Show_Error_Bars=None,
):
    # Fall back to the module-level global toggle when no override is given
    Show_Bands = Plot_Styling.Show_Bands if Show_Bands is None else Show_Bands
    Show_Error_Bars = Plot_Styling.Show_Error_Bars if Show_Error_Bars is None else Show_Error_Bars

    # Build the curve cache on demand if the caller did not provide a pre-built one
    if Curve_Cache is None:
        Curve_Cache = Build_Eos_Curve_Cache(P_Input__GPa, P_Eos__GPa, P_Max__GPa, P_Max_Specified)

    # Unpack the requested mode's arrays; fall back to the diff mode if the mode key is missing
    X_Values, Y_Values, Within_Mask, Beyond_Mask = Curve_Cache.get(Mode, Curve_Cache["diff"])
    X_Errors = (Curve_Cache.get("xerr") or {}).get(Mode)
    Y_Errors = (Curve_Cache.get("yerr") or {}).get(Mode)

    # Sort by x so line segments render in order and do not cross back on themselves
    Sort_Index = np.argsort(X_Values)
    X_Values = X_Values[Sort_Index]
    Y_Values = Y_Values[Sort_Index]
    Within_Mask = Within_Mask[Sort_Index]
    Beyond_Mask = Beyond_Mask[Sort_Index]

    # Apply the same sort to the error arrays when they exist
    if X_Errors is not None:
        X_Errors = X_Errors[Sort_Index]
    if Y_Errors is not None:
        Y_Errors = Y_Errors[Sort_Index]

    # Calibrations that have a P0 parameter are invalid below that pressure
    P0_Value = float(P0__GPa) if P0__GPa is not None else 0.0
    Below_P0_Mask = Within_Mask & (X_Values < P0_Value)
    Valid_Mask = Within_Mask & (X_Values >= P0_Value)

    # Compute line widths from the marker size
    Curve_Style = Curve_Style_From_Marker_Size(Marker_Size)
    Solid_Line_Width = float(Curve_Style["line_lw"] if Line_Width is None else Line_Width)
    Open_Line_Width = float(Solid_Line_Width)
    Marker_Edge_Width = float(Solid_Line_Width)

    # Draw a shaded uncertainty band behind the curve when bands are enabled
    if Show_Bands and Y_Errors is not None:
        Y_Error_Array = np.asarray(Y_Errors, dtype=float)
        Finite_Mask = np.isfinite(X_Values) & np.isfinite(Y_Values) & np.isfinite(Y_Error_Array)
        if np.any(Finite_Mask):
            # Sort the finite subset again to avoid crossed fill segments
            Sorted_Finite_Index = np.argsort(X_Values[Finite_Mask])
            Ax.fill_between(
                X_Values[Finite_Mask][Sorted_Finite_Index],
                Y_Values[Finite_Mask][Sorted_Finite_Index] - Y_Error_Array[Finite_Mask][Sorted_Finite_Index],
                Y_Values[Finite_Mask][Sorted_Finite_Index] + Y_Error_Array[Finite_Mask][Sorted_Finite_Index],
                color=Color,
                alpha=0.15,
                zorder=max(0, Z_Order - 2),
            )

    # Nested helper: draw error bars for the points identified by a boolean mask
    def Draw_Error_Bars(Mask):
        # Skip entirely when error bars are turned off or no uncertainty data exists
        if not Show_Error_Bars:
            return
        if X_Errors is None and Y_Errors is None:
            return
        Ax.errorbar(
            X_Values[Mask],
            Y_Values[Mask],
            xerr=X_Errors[Mask] if X_Errors is not None else None,
            yerr=Y_Errors[Mask] if Y_Errors is not None else None,
            fmt="none",
            ecolor=Color,
            alpha=0.5,
            capsize=2,
            zorder=max(0, Z_Order - 1),
        )

    # Draw points below P0 as open dashed markers to indicate extrapolation territory
    if np.any(Below_P0_Mask):
        Ax.plot(
            X_Values[Below_P0_Mask],
            Y_Values[Below_P0_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor="none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="--",
            linewidth=Open_Line_Width,
            markeredgewidth=Marker_Edge_Width,
            zorder=Z_Order,
            alpha=0.7,
        )
        Draw_Error_Bars(Below_P0_Mask)

    # Draw the within-range segment; filled markers when P_max is specified, open when it is not
    if np.any(Valid_Mask):
        Pmax_Is_Valid = bool(P_Max_Specified) and P_Max__GPa is not None and np.isfinite(float(P_Max__GPa))
        Ax.plot(
            X_Values[Valid_Mask],
            Y_Values[Valid_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor=Color if Pmax_Is_Valid else "none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="-" if Pmax_Is_Valid else "--",
            linewidth=Solid_Line_Width,
            markeredgewidth=Solid_Line_Width,
            label=Label,
            zorder=Z_Order,
        )
        Draw_Error_Bars(Valid_Mask)

    # Draw the beyond-P_max segment as open dashed markers
    if np.any(Beyond_Mask):
        # Only set the label on the beyond segment if nothing within range was drawn
        Beyond_Label = None if (np.any(Valid_Mask) or np.any(Below_P0_Mask)) else Label
        Ax.plot(
            X_Values[Beyond_Mask],
            Y_Values[Beyond_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor="none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="--",
            linewidth=Open_Line_Width,
            markeredgewidth=Marker_Edge_Width,
            label=Beyond_Label,
            zorder=Z_Order,
            alpha=0.7,
        )
        Draw_Error_Bars(Beyond_Mask)

    # Draw short connector segments across any transitions between solid and dashed regions
    for Segment_Index in range(len(X_Values) - 1):
        Is_A_Below = X_Values[Segment_Index] < P0_Value
        Is_B_Below = X_Values[Segment_Index + 1] < P0_Value
        Is_A_Valid = (X_Values[Segment_Index] >= P0_Value) and bool(Within_Mask[Segment_Index])
        Is_B_Valid = (X_Values[Segment_Index + 1] >= P0_Value) and bool(Within_Mask[Segment_Index + 1])
        Is_A_Beyond = bool(Beyond_Mask[Segment_Index])
        Is_B_Beyond = bool(Beyond_Mask[Segment_Index + 1])

        # A connector is needed whenever two consecutive points straddle a style boundary
        Needs_Connector = (
            (Is_A_Below and Is_B_Valid)
            or (Is_A_Valid and Is_B_Below)
            or (Is_A_Valid and Is_B_Beyond)
            or (Is_A_Beyond and Is_B_Valid)
        )
        if Needs_Connector:
            Ax.plot(
                [X_Values[Segment_Index], X_Values[Segment_Index + 1]],
                [Y_Values[Segment_Index], Y_Values[Segment_Index + 1]],
                color=Color,
                linestyle="--",
                linewidth=Open_Line_Width,
                marker="",
            )


# Create a legend proxy Line2D handle for a calibration curve
def Make_Line_Handle(Color, Marker, Marker_Size, P_Max_Specified=True):
    # Filled face for curves within their rated range; open face for unrated curves
    Marker_Face_Color = Color if bool(P_Max_Specified) else "none"
    Curve_Style = Curve_Style_From_Marker_Size(Marker_Size)
    # Return a Line2D patch used as a legend handle — not drawn on any axes
    return plt.Line2D(
        [0],
        [0],
        marker=Marker,
        color=Color,
        markerfacecolor=Marker_Face_Color,
        markeredgecolor=Color,
        markeredgewidth=Curve_Style["open_mew"],
        markersize=Curve_Style["legend_ms"],
        linestyle="-",
        linewidth=Curve_Style["legend_lw"],
    )


# Draw a horizontal dashed reference line spanning the data range or the current axis limits
def Draw_Horizontal_Reference_Line(Ax, Y_Value, X_Values=None, Color="k", Line_Style="--", Line_Width=1.0, Z_Order=0, Alpha=1.0):
    # Determine x extent from the data when provided
    if X_Values is not None:
        X_Values = np.asarray(X_Values, dtype=float)
        Finite_Mask = np.isfinite(X_Values)
        if np.any(Finite_Mask):
            X_Min = float(np.nanmin(X_Values[Finite_Mask]))
            X_Max = float(np.nanmax(X_Values[Finite_Mask]))
        # No finite data — fall back to the current axis limits
        else:
            X_Min, X_Max = Ax.get_xlim()
    # No x data given — use the current axis limits directly
    else:
        X_Min, X_Max = Ax.get_xlim()

    # Guard against degenerate or non-finite axis limits
    if not np.isfinite(X_Min) or not np.isfinite(X_Max) or X_Min == X_Max:
        X_Min, X_Max = Ax.get_xlim()

    # Draw and return the line so the caller can store it if needed
    Reference_Line = Ax.plot(
        [X_Min, X_Max],
        [Y_Value, Y_Value],
        color=Color,
        linestyle=Line_Style,
        linewidth=Line_Width,
        zorder=Z_Order,
        alpha=Alpha,
    )[0]

    # Return the line artist for optional caller use
    return Reference_Line


# Observable curve plotting


# Plot a single observable-vs-pressure curve onto an axes
def Plot_Observable_Curve(
    Ax,
    X_Eos__GPa,
    Y_Observable,
    P_Max__GPa,
    P_Max_Specified,
    Color,
    Marker,
    Label=None,
    Marker_Size=4,
    Line_Width=None,
    Z_Order=2,
    P0__GPa=None,
    Show_Bands=None,
    Show_Error_Bars=None,
    X_Errors=None,
    Y_Errors=None,
):
    # Fall back to the module-level global toggle when no override is given
    Show_Bands = Plot_Styling.Show_Bands if Show_Bands is None else Show_Bands
    Show_Error_Bars = Plot_Styling.Show_Error_Bars if Show_Error_Bars is None else Show_Error_Bars

    # Sort by x so line segments render in order
    X_Values = np.asarray(X_Eos__GPa, dtype=float)
    Y_Values = np.asarray(Y_Observable, dtype=float)
    Sort_Index = np.argsort(X_Values)
    X_Values = X_Values[Sort_Index]
    Y_Values = Y_Values[Sort_Index]

    # Sort the x-error array with the same index when provided
    if X_Errors is not None:
        X_Errors = np.asarray(X_Errors, dtype=float)[Sort_Index]

    # Sort the error array with the same index when provided
    if Y_Errors is not None:
        Y_Errors = np.asarray(Y_Errors, dtype=float)[Sort_Index]

    # Compute line widths from the marker size
    Curve_Style = Curve_Style_From_Marker_Size(Marker_Size)
    Solid_Line_Width = float(Curve_Style["line_lw"] if Line_Width is None else Line_Width)
    Open_Line_Width = float(Solid_Line_Width)
    Marker_Edge_Width = float(Solid_Line_Width)
    P0_Value = float(P0__GPa) if P0__GPa is not None else 0.0

    # Compute within/beyond masks and the below-P0 sub-mask
    Within_Mask, Beyond_Mask = Compute_Pmax_Masks(X_Values, P_Max__GPa, P_Max_Specified)
    Below_P0_Mask = Within_Mask & (X_Values < P0_Value)
    Valid_Mask = Within_Mask & (X_Values >= P0_Value)

    # Draw a shaded uncertainty band behind the curve when bands are enabled
    if Show_Bands and Y_Errors is not None:
        Finite_Mask = np.isfinite(X_Values) & np.isfinite(Y_Values) & np.isfinite(Y_Errors)
        if np.any(Finite_Mask):
            Ax.fill_between(
                X_Values[Finite_Mask],
                Y_Values[Finite_Mask] - Y_Errors[Finite_Mask],
                Y_Values[Finite_Mask] + Y_Errors[Finite_Mask],
                color=Color,
                alpha=0.15,
            )

    # Draw points below P0 as open dashed markers
    if np.any(Below_P0_Mask):
        Ax.plot(
            X_Values[Below_P0_Mask],
            Y_Values[Below_P0_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor="none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="--",
            linewidth=Open_Line_Width,
            markeredgewidth=Marker_Edge_Width,
            zorder=Z_Order,
            alpha=0.7,
        )
        if Show_Error_Bars and (X_Errors is not None or Y_Errors is not None):
            Ax.errorbar(
                X_Values[Below_P0_Mask],
                Y_Values[Below_P0_Mask],
                xerr=X_Errors[Below_P0_Mask] if X_Errors is not None else None,
                yerr=Y_Errors[Below_P0_Mask] if Y_Errors is not None else None,
                fmt="none",
                ecolor=Color,
                alpha=0.5,
                capsize=2,
                zorder=max(0, Z_Order - 1),
            )

    # Draw the within-range segment; filled markers when P_max is specified
    if np.any(Valid_Mask):
        Pmax_Is_Valid = bool(P_Max_Specified) and P_Max__GPa is not None and np.isfinite(float(P_Max__GPa))
        Ax.plot(
            X_Values[Valid_Mask],
            Y_Values[Valid_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor=Color if Pmax_Is_Valid else "none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="-" if Pmax_Is_Valid else "--",
            linewidth=Solid_Line_Width,
            markeredgewidth=Solid_Line_Width,
            label=Label,
            zorder=Z_Order,
        )
        if Show_Error_Bars and (X_Errors is not None or Y_Errors is not None):
            Ax.errorbar(
                X_Values[Valid_Mask],
                Y_Values[Valid_Mask],
                xerr=X_Errors[Valid_Mask] if X_Errors is not None else None,
                yerr=Y_Errors[Valid_Mask] if Y_Errors is not None else None,
                fmt="none",
                ecolor=Color,
                alpha=0.5,
                capsize=2,
                zorder=max(0, Z_Order - 1),
            )

    # Draw the beyond-P_max segment as open dashed markers
    if np.any(Beyond_Mask):
        # Only use the label here if no within-range segment was drawn
        Beyond_Label = None if (np.any(Valid_Mask) or np.any(Below_P0_Mask)) else Label
        Ax.plot(
            X_Values[Beyond_Mask],
            Y_Values[Beyond_Mask],
            marker=Marker,
            color=Color,
            markerfacecolor="none",
            markeredgecolor=Color,
            markersize=Marker_Size,
            linestyle="--",
            linewidth=Open_Line_Width,
            markeredgewidth=Marker_Edge_Width,
            label=Beyond_Label,
            zorder=Z_Order,
            alpha=0.7,
        )
        if Show_Error_Bars and (X_Errors is not None or Y_Errors is not None):
            Ax.errorbar(
                X_Values[Beyond_Mask],
                Y_Values[Beyond_Mask],
                xerr=X_Errors[Beyond_Mask] if X_Errors is not None else None,
                yerr=Y_Errors[Beyond_Mask] if Y_Errors is not None else None,
                fmt="none",
                ecolor=Color,
                alpha=0.5,
                capsize=2,
                zorder=max(0, Z_Order - 1),
            )

    # Draw connector segments across style-boundary transitions
    for Segment_Index in range(len(X_Values) - 1):
        Is_A_Below = X_Values[Segment_Index] < P0_Value
        Is_B_Below = X_Values[Segment_Index + 1] < P0_Value
        Is_A_Valid = (X_Values[Segment_Index] >= P0_Value) and bool(Within_Mask[Segment_Index])
        Is_B_Valid = (X_Values[Segment_Index + 1] >= P0_Value) and bool(Within_Mask[Segment_Index + 1])
        Is_A_Beyond = bool(Beyond_Mask[Segment_Index])
        Is_B_Beyond = bool(Beyond_Mask[Segment_Index + 1])

        # Connect any two consecutive points that straddle a fill/dash style boundary
        Needs_Connector = (
            (Is_A_Below and Is_B_Valid)
            or (Is_A_Valid and Is_B_Below)
            or (Is_A_Valid and Is_B_Beyond)
            or (Is_A_Beyond and Is_B_Valid)
        )
        if Needs_Connector:
            Ax.plot(
                [X_Values[Segment_Index], X_Values[Segment_Index + 1]],
                [Y_Values[Segment_Index], Y_Values[Segment_Index + 1]],
                color=Color,
                linestyle="--",
                linewidth=Open_Line_Width,
                marker="",
            )


# Legend placement utilities


# Return a dict of four candidate bounding boxes (one per corner) in axes-fraction coordinates
def Get_Legend_Bbox_Candidates(Width, Height, Pad=0.03):
    # Parse padding into separate x and y components
    if np.isscalar(Pad):
        Pad_X = float(np.clip(Pad, 0.0, 0.95))
        Pad_Y = float(np.clip(Pad, 0.0, 0.95))
    else:
        # Two-value pad sequence: (x_pad, y_pad)
        if len(Pad) != 2:
            raise ValueError("pad must be a scalar or a two-value sequence")
        Pad_X = float(np.clip(Pad[0], 0.0, 0.95))
        Pad_Y = float(np.clip(Pad[1], 0.0, 0.95))

    # Clamp the box dimensions to ensure they fit within the padded region
    Width = float(np.clip(Width, 0.05, max(0.05, 1.0 - Pad_X)))
    Height = float(np.clip(Height, 0.05, max(0.05, 1.0 - Pad_Y)))

    # Compute the four corner anchor points in axes-fraction space
    Right_X = 1.0 - Pad_X
    Left_X = Pad_X
    Top_Y = 1.0 - Pad_Y
    Bottom_Y = Pad_Y

    # Return each box as (x0, y0, x1, y1) in axes fractions
    return {
        "upper right": (Right_X - Width, Top_Y - Height, Right_X, Top_Y),
        "upper left": (Left_X, Top_Y - Height, Left_X + Width, Top_Y),
        "lower left": (Left_X, Bottom_Y, Left_X + Width, Bottom_Y + Height),
        "lower right": (Right_X - Width, Bottom_Y, Right_X, Bottom_Y + Height),
    }


# Score a candidate box by counting empty rings around it before any data point falls inside
#   A higher score means more empty space, so higher = better placement
def Score_Box_Progressive(Points, Box, Ring_Step=0.01, Max_Rings=40):
    # An axes with no data is always a perfect placement
    if Points.size == 0:
        return int(Max_Rings + 1)

    X_Values = Points[:, 0]
    Y_Values = Points[:, 1]
    Box_X0, Box_Y0, Box_X1, Box_Y1 = Box
    Score = 0
    Previous_Ring = None

    # Expand the box outward one ring at a time until a data point falls inside
    for Ring_Index in range(Max_Rings + 1):
        Ring_Distance = float(Ring_Index) * float(Ring_Step)
        Current_Ring = (
            max(0.0, Box_X0 - Ring_Distance),
            max(0.0, Box_Y0 - Ring_Distance),
            min(1.0, Box_X1 + Ring_Distance),
            min(1.0, Box_Y1 + Ring_Distance),
        )

        # Stop early if the ring did not expand (clamped at boundaries)
        if Previous_Ring is not None and Current_Ring == Previous_Ring:
            break

        # Check whether any data point falls inside the new ring shell
        Inside_Current_Mask = (
            (X_Values >= Current_Ring[0])
            & (X_Values <= Current_Ring[2])
            & (Y_Values >= Current_Ring[1])
            & (Y_Values <= Current_Ring[3])
        )

        # On the first ring, test the entire interior; on subsequent rings, test only the new shell
        if Previous_Ring is None:
            New_Ring_Region = Inside_Current_Mask
        else:
            Inside_Previous_Mask = (
                (X_Values >= Previous_Ring[0])
                & (X_Values <= Previous_Ring[2])
                & (Y_Values >= Previous_Ring[1])
                & (Y_Values <= Previous_Ring[3])
            )
            New_Ring_Region = Inside_Current_Mask & (~Inside_Previous_Mask)

        # If any data point appears in this ring shell, stop counting empty rings
        if np.any(New_Ring_Region):
            break

        Score += 1
        Previous_Ring = Current_Ring

    # Return the number of empty rings — more empty rings means better placement
    return int(Score)


# Axes data collection (internal)


# Downsample an (N, 2) array to at most max_points rows, evenly spaced by index
def Local__Downsample_Xy(Xy_Points, Max_Points=1500):
    Point_Count = int(Xy_Points.shape[0])
    # No downsampling needed when already within the limit
    if Point_Count <= Max_Points:
        return Xy_Points
    # Pick evenly spaced indices across the point array
    Sample_Indices = np.linspace(0, Point_Count - 1, Max_Points).astype(int)
    # Return the sampled subset
    return Xy_Points[Sample_Indices]


# Create a dense (N, 2) polyline from (x, y) arrays by inserting points along each segment
#   The density per segment is weighted by segment length relative to the total polyline length
def Local__Densify_Polyline(X_Values, Y_Values, Max_Points=2500):
    X_Values = np.asarray(X_Values, dtype=float)
    Y_Values = np.asarray(Y_Values, dtype=float)

    # A single-point line has nothing to densify; return it as a column-stacked array
    if X_Values.size < 2 or Y_Values.size < 2:
        if X_Values.size and Y_Values.size:
            return np.column_stack([X_Values, Y_Values])
        return np.empty((0, 2), dtype=float)

    # Compute the Euclidean length of each segment
    Delta_X = np.diff(X_Values)
    Delta_Y = np.diff(Y_Values)
    Segment_Length = np.hypot(Delta_X, Delta_Y)
    Total_Length = float(np.sum(Segment_Length))

    # A degenerate or zero-length polyline cannot be densified meaningfully
    if (not np.isfinite(Total_Length)) or Total_Length <= 0.0:
        return np.column_stack([X_Values, Y_Values])

    Segment_Count = len(Segment_Length)
    # Minimum point count per segment to avoid very sparse short segments
    Base_Count = max(2, int(Max_Points / max(Segment_Count, 1)))

    X_Segments = []
    Y_Segments = []

    # Allocate points to each segment proportional to its fraction of the total length
    for Segment_Index in range(Segment_Count):
        Segment_Weight = Segment_Length[Segment_Index] / Total_Length
        Segment_Point_Count = max(2, int(round(Segment_Weight * Max_Points)))
        Segment_Point_Count = max(Segment_Point_Count, Base_Count)
        # endpoint=False avoids duplicating the junction point between segments
        X_Segments.append(np.linspace(X_Values[Segment_Index], X_Values[Segment_Index + 1], Segment_Point_Count, endpoint=False))
        Y_Segments.append(np.linspace(Y_Values[Segment_Index], Y_Values[Segment_Index + 1], Segment_Point_Count, endpoint=False))

    # Append the final endpoint which was excluded by endpoint=False throughout
    X_Segments.append(np.array([X_Values[-1]], dtype=float))
    Y_Segments.append(np.array([Y_Values[-1]], dtype=float))

    Dense_Points = np.column_stack([np.concatenate(X_Segments), np.concatenate(Y_Segments)])

    # Return the dense array downsampled to the point limit
    return Local__Downsample_Xy(Dense_Points, Max_Points=Max_Points)


# Collect all visible data points from an axes into a single (N, 2) array in data coordinates
def Local__Collect_Axes_Data_Points(Ax, X_Data=None, Y_Series=None):
    Data_Points_List = []

    # Walk every plotted line in the axes
    for Line in Ax.get_lines():
        if not Line.get_visible():
            continue
        X_Values = np.asarray(Line.get_xdata(), dtype=float)
        Y_Values = np.asarray(Line.get_ydata(), dtype=float)
        if X_Values.size == 0 or Y_Values.size == 0:
            continue
        Finite_Mask = np.isfinite(X_Values) & np.isfinite(Y_Values)
        if not np.any(Finite_Mask):
            continue
        X_Finite = X_Values[Finite_Mask]
        Y_Finite = Y_Values[Finite_Mask]
        # Densify short lines; short lines with fewer than 2 points need no densification
        if X_Finite.size < 2:
            Line_Points = np.column_stack([X_Finite, Y_Finite])
        else:
            Line_Points = Local__Densify_Polyline(X_Finite, Y_Finite, Max_Points=2500)
        if Line_Points.size:
            Data_Points_List.append(Line_Points)

    # Walk every scatter collection in the axes
    for Collection in Ax.collections:
        if not Collection.get_visible():
            continue
        try:
            # get_offsets can raise for some collection subtypes
            Offsets = np.asarray(Collection.get_offsets(), dtype=float)
        except Exception:
            continue
        if Offsets.size == 0:
            continue
        Offsets = np.reshape(Offsets, (-1, 2))
        Finite_Mask = np.isfinite(Offsets[:, 0]) & np.isfinite(Offsets[:, 1])
        if not np.any(Finite_Mask):
            continue
        Data_Points_List.append(Local__Downsample_Xy(Offsets[Finite_Mask], Max_Points=1500))

    # Also include any explicitly provided data series that are not yet drawn on the axes
    if X_Data is not None and Y_Series is not None:
        X_Values = np.asarray(X_Data, dtype=float)
        for Y_Series_Item in Y_Series:
            Y_Values = np.asarray(Y_Series_Item, dtype=float)
            if X_Values.size == 0 or Y_Values.size == 0:
                continue
            Finite_Mask = np.isfinite(X_Values) & np.isfinite(Y_Values)
            if not np.any(Finite_Mask):
                continue
            Data_Points_List.append(Local__Downsample_Xy(
                np.column_stack([X_Values[Finite_Mask], Y_Values[Finite_Mask]]),
                Max_Points=1500,
            ))

    # Return an empty array when no data was found
    if not Data_Points_List:
        return np.empty((0, 2), dtype=float)

    # Stack all data into one array and downsample to a final budget
    return Local__Downsample_Xy(np.vstack(Data_Points_List), Max_Points=8000)


# Convert data-coordinate points to axes-fraction coordinates for overlap detection
def Points_To_Axes_Coords(Ax, X_Data=None, Y_Series=None):
    # Collect all visible data in data coordinates
    Xy_Data = Local__Collect_Axes_Data_Points(Ax, X_Data=X_Data, Y_Series=Y_Series)

    # Return empty when no data is available
    if Xy_Data.size == 0:
        return np.empty((0, 2), dtype=float)

    # Transform from data space to display pixels, then to axes fractions
    Xy_Display = Ax.transData.transform(Xy_Data)
    Xy_Axes = Ax.transAxes.inverted().transform(Xy_Display)

    # Return the array in axes-fraction coordinates
    return Xy_Axes


# Estimate the legend size as a fraction of the axes dimensions by creating a temporary legend
def Local__Estimate_Legend_Size(Ax, Font_Size=5.0, Marker_Scale=1.0, Ps_Override=None):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Plot_Styling.Ps if Ps_Override is None else Ps_Override
    Handles, Labels = Ax.get_legend_handles_labels()

    # Default fallback when the axes has no legend handles
    if not Handles:
        return 0.20, 0.14

    # Create a temporary legend to measure its rendered size
    Temporary_Legend = Ax.legend(
        Handles,
        Labels,
        loc="upper right",
        fontsize=Font_Size,
        borderaxespad=0.0,
        borderpad=Active_Ps["borderpad"],
        handlelength=Active_Ps["handlelength"],
        handletextpad=Active_Ps["handletextpad"],
        labelspacing=Active_Ps["labelspacing"],
        markerscale=Marker_Scale,
        frameon=True,
    )
    Figure = Ax.figure
    Figure.canvas.draw()
    Renderer = Figure.canvas.get_renderer()

    # Measure the legend and axes bounding boxes in display pixels
    Legend_Bbox = Temporary_Legend.get_window_extent(renderer=Renderer)
    Axes_Bbox = Ax.get_window_extent(renderer=Renderer)

    # Remove the temporary legend so it does not persist in the figure
    Temporary_Legend.remove()

    # Return legend size as fractions of the axes dimensions
    return float(Legend_Bbox.width / max(Axes_Bbox.width, 1.0)), float(Legend_Bbox.height / max(Axes_Bbox.height, 1.0))


# Auto placement


# Place a legend or custom feature in the corner of an axes that has the most empty space
def Place_Feature_Best_Corner(
    Ax,
    Feature="legend",
    Padding=0.0,
    X_Data=None,
    Y_Series=None,
    Ring_Step=0.01,
    Max_Rings=40,
    Legend_Kwargs=None,
    Feature_Size_Axes=None,
    Place_Feature_Fn=None,
    Feature_Kwargs=None,
    Return_Info=False,
    Ps_Override=None,
):
    # Use the provided override if given; otherwise fall back to the module global
    Active_Ps = Plot_Styling.Ps if Ps_Override is None else Ps_Override

    # Ensure kwargs dicts are mutable copies so we can update them safely
    Legend_Kwargs = {} if Legend_Kwargs is None else dict(Legend_Kwargs)
    Feature_Kwargs = {} if Feature_Kwargs is None else dict(Feature_Kwargs)

    # Estimate the feature's size in axes fractions
    if Feature == "legend":
        # Measure the legend size by creating a temporary legend
        Legend_Width, Legend_Height = Local__Estimate_Legend_Size(
            Ax,
            Font_Size=float(Legend_Kwargs.get("fontsize", 5.0)),
            Marker_Scale=float(Legend_Kwargs.get("markerscale", 1.0)),
            Ps_Override=Active_Ps,
        )
    # Non-legend features must provide their own size estimate
    else:
        if Feature_Size_Axes is None:
            raise ValueError("Feature_Size_Axes is required for non-legend placement")
        Legend_Width, Legend_Height = map(float, Feature_Size_Axes)

    # Build the four candidate corner boxes and score each against the current data
    Corner_Boxes = Get_Legend_Bbox_Candidates(Legend_Width, Legend_Height, Pad=Padding)
    Data_Points = Points_To_Axes_Coords(Ax, X_Data=X_Data, Y_Series=Y_Series)

    # Clip points to a slightly expanded axes region to ignore far outliers
    if Data_Points.size:
        Data_Points = Data_Points[
            (Data_Points[:, 0] >= -0.25)
            & (Data_Points[:, 0] <= 1.25)
            & (Data_Points[:, 1] >= -0.25)
            & (Data_Points[:, 1] <= 1.25)
        ]

    # Score every corner by the number of empty rings before any data point intrudes
    Corner_Scores = {
        Corner_Name: Score_Box_Progressive(Data_Points, Corner_Box, Ring_Step=Ring_Step, Max_Rings=Max_Rings)
        for Corner_Name, Corner_Box in Corner_Boxes.items()
    }

    # Tie-break by preferred corner order: upper right first
    Corner_Tie_Order = ["upper right", "upper left", "lower left", "lower right"]
    Best_Corner = max(Corner_Tie_Order, key=lambda Corner_Name: (Corner_Scores[Corner_Name], -Corner_Tie_Order.index(Corner_Name)))

    # Determine the anchor point for the chosen corner box
    Box_X0, Box_Y0, Box_X1, Box_Y1 = Corner_Boxes[Best_Corner]
    Corner_Anchors = {
        "upper right": (Box_X1, Box_Y1),
        "upper left": (Box_X0, Box_Y1),
        "lower left": (Box_X0, Box_Y0),
        "lower right": (Box_X1, Box_Y0),
    }
    Best_Anchor = Corner_Anchors[Best_Corner]

    # Place the feature in the winning corner
    if Feature == "legend":
        # Build legend kwargs with sensible defaults, then apply caller overrides
        Legend_Defaults = {
            "loc": Best_Corner,
            "bbox_to_anchor": Best_Anchor,
            "borderaxespad": 0.0,
            "borderpad": Active_Ps["borderpad"],
            "handlelength": Active_Ps["handlelength"],
            "handletextpad": Active_Ps["handletextpad"],
            "labelspacing": Active_Ps["labelspacing"],
            "frameon": False,
            "fancybox": False,
        }
        Legend_Defaults.update(Legend_Kwargs)
        # Re-apply loc and anchor in case the caller's kwargs tried to override them
        Legend_Defaults["loc"] = Best_Corner
        Legend_Defaults["bbox_to_anchor"] = Best_Anchor
        Feature_Artist = Ax.legend(**Legend_Defaults)
    # Custom feature placement via caller-supplied function
    else:
        if Place_Feature_Fn is None:
            raise ValueError("Place_Feature_Fn is required for non-legend placement")
        Feature_Artist = Place_Feature_Fn(Ax=Ax, Corner=Best_Corner, Box=Corner_Boxes[Best_Corner], Anchor=Best_Anchor, **Feature_Kwargs)

    # Optionally return diagnostic info for debugging and testing placement decisions
    if Return_Info:
        return {
            "artist": Feature_Artist,
            "corner": Best_Corner,
            "scores": Corner_Scores,
            "boxes": Corner_Boxes,
            "size_axes": (Legend_Width, Legend_Height),
            "anchor": Best_Anchor,
        }

    # Return just the artist when diagnostic info is not requested
    return Feature_Artist




