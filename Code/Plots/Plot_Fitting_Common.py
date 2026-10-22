# Load libraries
    # Load standard libraries
from types import SimpleNamespace
    # Load local functions from local files
from Plots import Plot_Styling
from Themes.Plot_Style_Options import AUTO_COLORS





# Use EoSAlign's tab20 palette so the colors match the rest of the plots
Model_Colors = AUTO_COLORS

# Line style cycle used to tell the models apart in the summary figure
Model_Line_Styles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 1))]



# Where the plot style comes from. The desktop app leaves this as None and reads the user's settings (below).
# The website has no Qt or settings, so it sets this to a function that returns its own style config
Plot_Style_Config_Provider = None



# Build the plot style config from the theme and the plot font settings the user chose in EoSAlign's settings
def Build_The_Plot_Style_Config_From_The_User_Settings():

    # Qt is only loaded here so the rest of this file can be used without it (the website runs this file without Qt)
    from PySide6.QtCore import QSettings
    from Themes.Theme import Get_Theme

    Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
    _, _, Colors = Get_Theme()

    # Collect the same font overrides EoSAlign uses when it makes its figures
    Config = SimpleNamespace(
        Theme_Overrides={
            "Primary_Text": Colors.get("Primary_Text", "#111111"),
            "Secondary_Text": Colors.get("Secondary_Text", "#212121"),
            "Primary_Color": Colors.get("Primary_Color", "#FABE60"),
            "Secondary_Background": Colors.get("Secondary_Background", "#FFFFFF"),
            "Primary_Background": Colors.get("Primary_Background", "#FFFFFF"),
        },
        Ps_Overrides={
            "font_title": int(Settings_Store.value("Plot Title Font Size", 12)),
            "font_label": int(Settings_Store.value("Axis Label Font Size", 10)),
            "font_tick": int(Settings_Store.value("Tick Mark Font Size", 8)),
            "font_legend_max": float(Settings_Store.value("Legend Font Size", 8)),
            "title_bold": Settings_Store.value("Plot Title Bold", False, type=bool),
            "title_italic": Settings_Store.value("Plot Title Italic", False, type=bool),
            "label_bold": Settings_Store.value("Axis Label Bold", False, type=bool),
            "label_italic": Settings_Store.value("Axis Label Italic", False, type=bool),
            "tick_bold": Settings_Store.value("Tick Mark Bold", False, type=bool),
            "tick_italic": Settings_Store.value("Tick Mark Italic", False, type=bool),
            # The figures are drawn on screen, so they are saved at the screen resolution
            "dpi": 100,
        },
        Show_Bands=True,
        Show_Error_Bars=False,
        Show_Grid=Settings_Store.value("Show_Grid_Lines", False, type=bool),
    )

    return Config



# Apply EoSAlign's plot style (its colors, fonts, ticks and legend) with the theme and the plot font settings the user chose in EoSAlign's settings
def Apply_Fitting_Plot_Style():

    Config = Plot_Style_Config_Provider() if Plot_Style_Config_Provider is not None else Build_The_Plot_Style_Config_From_The_User_Settings()
    Plot_Styling.Apply_Plot_Style(Config)



# Get the plot colors, which are the colors of EoSAlign's plots. The figure is the color of the card it sits on, so only the plot itself shows
def Get_Fitting_Plot_Colors():

    Apply_Fitting_Plot_Style()

    return {
        "Background": Plot_Styling.Theme["Secondary_Background"],
        "Axes_Background": Plot_Styling.Theme["Secondary_Background"],
        "Text": Plot_Styling.Theme["Primary_Text"],
        "Grid": Plot_Styling.Theme["Primary_Text"],
    }



# Get the color for the model or study at an index
def Get_Model_Color(Index):

    return Model_Colors[Index % len(Model_Colors)]



# Get the line style for the model at an index
def Get_Model_Line_Style(Index):

    return Model_Line_Styles[Index % len(Model_Line_Styles)]



# Make one set of axes in the style of EoSAlign's plots
def Make_Fitting_Axes(Figure, X_Label="", Y_Label="", Title=""):

    Apply_Fitting_Plot_Style()
    Ax = Figure.add_subplot(111)
    Plot_Styling.Style_Ax(Ax, X_Label, Y_Label, Title)

    return Ax



# Add a legend in the style of EoSAlign's plots: no frame, the spacing and text color of its legends, in a column beside the plot
def Add_Fitting_Legend(Ax, Font_Size=None):

    Legend = Ax.legend(
        fontsize=Font_Size or Plot_Styling.Ps["font_legend_max"],
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
        fancybox=False,
        shadow=False,
        handlelength=Plot_Styling.Ps["handlelength"] * 2,
        handletextpad=Plot_Styling.Ps["handletextpad"],
        labelspacing=Plot_Styling.Ps["labelspacing"],
        borderpad=Plot_Styling.Ps["borderpad"],
        markerscale=1.0,
    )
    for Label_Text in Legend.get_texts():
        Label_Text.set_color(Plot_Styling.Theme["Primary_Text"])
    Keep_Space_For_The_Legend(Ax.figure, Legend)



# Fit a figure's layout to its canvas. A legend is left out of the automatic layout, and the room it needs
# (its width in pixels does not change when the figure is resized) is kept free on the right instead.
def Fit_The_Figure_Layout(Figure):

    Legends = [Legend for Axes in Figure.axes for Legend in [Axes.get_legend()] if Legend is not None]
    if not Legends:
        Figure.tight_layout()
        return
    Legend_Width = max(Legend.get_window_extent(Figure._get_renderer()).width for Legend in Legends)
    Reserved_Fraction = min(0.5, (Legend_Width + 25) / max(Figure.bbox.width, 1))
    Figure.tight_layout(rect=(0, 0, 1 - Reserved_Fraction, 1))



# Keep the legend out of the automatic layout, and fit the layout again each time the canvas is resized
def Keep_Space_For_The_Legend(Figure, Legend):

    Legend.set_in_layout(False)
    Figure.Update_The_Legend_Space = lambda: Fit_The_Figure_Layout(Figure)
