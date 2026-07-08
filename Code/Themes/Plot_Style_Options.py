# Plot style options for EoSAlign plots
    # Marker shapes and color palette used across all plot windows
    # Edit this file to add, remove, or rename style options




# All marker shapes available for plot lines
    # Display_Name: shown to the user in the marker dropdown
    # Matplotlib_Code: passed directly to the matplotlib marker= parameter
    # Shape list matches what is used in Allison_Code/EoS_Comparison_Plotter.ipynb
PLOT_MARKER_OPTIONS = [
    {"Display_Name": "Circle",            "Matplotlib_Code": "o"},
    {"Display_Name": "Square",            "Matplotlib_Code": "s"},
    {"Display_Name": "Triangle Up",       "Matplotlib_Code": "^"},
    {"Display_Name": "Diamond",           "Matplotlib_Code": "D"},
    {"Display_Name": "Triangle Down",     "Matplotlib_Code": "v"},
    {"Display_Name": "Triangle Left",     "Matplotlib_Code": "<"},
    {"Display_Name": "Triangle Right",    "Matplotlib_Code": ">"},
    {"Display_Name": "Pentagon",          "Matplotlib_Code": "p"},
    {"Display_Name": "Hexagon",           "Matplotlib_Code": "h"},
    {"Display_Name": "Star",              "Matplotlib_Code": "*"},
    {"Display_Name": "Plus (filled)",     "Matplotlib_Code": "P"},
    {"Display_Name": "X (filled)",        "Matplotlib_Code": "X"},
    {"Display_Name": "Thin Diamond",      "Matplotlib_Code": "d"},
    {"Display_Name": "Octagon",           "Matplotlib_Code": "8"},
    {"Display_Name": "Hexagon 2",         "Matplotlib_Code": "H"},
]

# Default marker code used when no user selection has been saved in QSettings
DEFAULT_MARKER = "o"


# N = 40
# colors = plt.cm.hsv(np.linspace(0, 1, N))


# Color palette available in the color picker panel
    # Tab20 group: matplotlib tab20 colormap colors, used as Allison's default
    #   gradient palette in Allison_Code/EoS_Comparison_Plotter.ipynb
    # Named group: explicit colors from Allison_Code/error_propagation_figure.ipynb
PLOT_COLOR_PALETTE = [
    # ── Tab20 palette (matplotlib tab20 colormap, 20 evenly-spaced entries) ──
    {"Display_Name": "Blue",               "Hex": "#1f77b4"},
    {"Display_Name": "Light Blue",         "Hex": "#aec7e8"},
    {"Display_Name": "Orange",             "Hex": "#ff7f0e"},
    {"Display_Name": "Light Orange",       "Hex": "#ffbb78"},
    {"Display_Name": "Green",              "Hex": "#2ca02c"},
    {"Display_Name": "Light Green",        "Hex": "#98df8a"},
    {"Display_Name": "Red",                "Hex": "#d62728"},
    {"Display_Name": "Light Red",          "Hex": "#ff9896"},
    {"Display_Name": "Purple",             "Hex": "#9467bd"},
    {"Display_Name": "Light Purple",       "Hex": "#c5b0d5"},
    {"Display_Name": "Brown",              "Hex": "#8c564b"},
    {"Display_Name": "Light Brown",        "Hex": "#c49c94"},
    {"Display_Name": "Pink",               "Hex": "#e377c2"},
    {"Display_Name": "Light Pink",         "Hex": "#f7b6d2"},
    {"Display_Name": "Gray",               "Hex": "#7f7f7f"},
    {"Display_Name": "Light Gray",         "Hex": "#c7c7c7"},
    {"Display_Name": "Yellow-Green",       "Hex": "#bcbd22"},
    {"Display_Name": "Light Yellow-Green", "Hex": "#dbdb8d"},
    {"Display_Name": "Teal",               "Hex": "#17becf"},
    {"Display_Name": "Light Teal",         "Hex": "#9edae5"},
    # ── Named colors from error_propagation_figure.ipynb ──────────────────────
    {"Display_Name": "Gold",               "Hex": "#D4A017"},   # Au data
    {"Display_Name": "Sky Blue",           "Hex": "#2E86C1"},   # Sakai conversion
    {"Display_Name": "Crimson",            "Hex": "#E74C3C"},   # Dewaele
    {"Display_Name": "Emerald",            "Hex": "#27AE60"},   # Ding
    {"Display_Name": "Violet",             "Hex": "#8E44AD"},   # Hixson & Fritz
]


# ── Auto-assignment palette ────────────────────────────────────────────────────
# 20 tab20 colors and 15 marker shapes. Both advance together with each study:
#   color_idx  = i % 20
#   marker_idx = i % 15
# Because gcd(20,15)=5 → lcm(20,15)=60 unique color+marker combos before any repeat.
AUTO_COLORS = [entry["Hex"] for entry in PLOT_COLOR_PALETTE[:20]]
AUTO_MARKERS = ['o', 's', '^', 'D', 'v', '<', '>', 'p', 'h', '*',
                'P', 'X', 'd', '8', 'H']
