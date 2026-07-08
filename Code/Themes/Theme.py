# Load libraries
    # Load standard libraries
import darkdetect
    # Load third party libraries
from PySide6.QtCore import QSettings





# List the brand colors and variants of the colors

ORANGE = {
    "900": "#EA8851",
    "800": "#F2A057",
    "700": "#F6AD58",
    "600": "#FABE60",
    "500": "#FDCA66",
    "400": "#FFD16B",
    "300": "#FFDB7D",
    "200": "#FFE49E",
    "100": "#FFEEC3",
    "50": "#FFF9E7",
}
ORANGE_50_PERCENT_LIGHT = {
    "800": "#F8CFAB",
    "600": "#FCDEAF",
}
ORANGE_50_PERCENT_DARK = {
    "800": "#89603C",
    "600": "#8D6F40",
}

BLUE = {
    "900": "#41468B",
    "800": "#4E63AC",
    "700": "#5574BF",
    "600": "#5E86D2",
    "500": "#6494E0",
    "400": "#70A3E5",
    "300": "#83B3EA",
    "200": "#A1C8F2",
    "100": "#C4DDF7",
    "50": "#E6F1FC",
}
BLUE_50_PERCENT_LIGHT = {
    "800": "#A6B1D5",
    "600": "#AEC2E8",
}
BLUE_50_PERCENT_DARK = {
    "800": "#374266",
    "600": "#3F5379",
}

TEAL = {
    "900": "#2F5071",
    "800": "#3B6F94",
    "700": "#417FA8",
    "600": "#4991BB",
    "500": "#509FC9",
    "400": "#5BACD0",
    "300": "#6DBAD8",
    "200": "#8ECDE4",
    "100": "#B8E1EF",
    "50": "#E3F3F8",
}
TAN = {
    "900": "#381800",
    "800": "#452600",
    "700": "#513304",
    "600": "#5F3F0D",
    "500": "#684812",
    "400": "#826131",
    "300": "#9B7C4F",
    "200": "#BF9F78",
    "100": "#E1C4A0",
    "50": "#FBE7C4",
}
NEUTRAL_CREAM = {
    "900": "#302A23",
    "800": "#534C44",
    "700": "#736C63",
    "600": "#888078",
    "500": "#B2AAA1",
    "400": "#D0C8BF",
    "300": "#F2E9E0",
    "200": "#FAF1E7",
    "100": "#FFF6EC",
    "50": "#FFFBF1",
}
RED = {
    "900": "#A6411C",
    "800": "#C04C21",
    "700": "#CE5224",
    "600": "#DC5928",
    "500": "#E65E2C",
    "400": "#E97449",
    "300": "#EC8B69",
    "200": "#F1AB93",
    "100": "#F6CCBD",
    "50": "#F7E9E7",
}
GREEN = {
    "900": "#2E7D32",
    "800": "#388E3C",
    "700": "#43A047",
    "600": "#4CAF50",
    "500": "#66BB6A",
    "400": "#81C784",
    "300": "#A5D6A7",
    "200": "#C8E6C9",
    "100": "#E8F5E9",
    "50": "#F1F8F1",
}
GREEN_50_PERCENT_LIGHT = {
    "800": "#9BC69D",
    "600": "#A5D7A7",
}
GREEN_50_PERCENT_DARK = {
    "800": "#2C572E",
    "600": "#366838",
}

BOARDER_ROUNDING = 20
DEFAULT_MINIMUM_CONTENT_WIDTH = 500

STYLE_SHEET_FILES = [
    "Themes/Qt_Style_Sheets/Base_Style.qss",
    "Themes/Qt_Style_Sheets/MenuBar.qss",
    "Themes/Qt_Style_Sheets/Banner.qss",
    "Themes/Qt_Style_Sheets/Buttons.qss",
    "Themes/Qt_Style_Sheets/Dropdowns.qss",
    "Themes/Qt_Style_Sheets/Checkboxes.qss",
    "Themes/Qt_Style_Sheets/Text_Entry.qss",
    "Themes/Qt_Style_Sheets/Scrollbar.qss",
    "Themes/Qt_Style_Sheets/Warning_Messages.qss",
    "Themes/Qt_Style_Sheets/Success_Messages.qss",
    "Themes/Qt_Style_Sheets/EoSApplications.qss",
    "Themes/Qt_Style_Sheets/Settings.qss",
    "Themes/Qt_Style_Sheets/Collapsible_Sections.qss",
    "Themes/Qt_Style_Sheets/Nested_Collapsible_Sections.qss",
    "Themes/Qt_Style_Sheets/Footnotes.qss",
    "Themes/Qt_Style_Sheets/Preview_CSV.qss",
    "Themes/Qt_Style_Sheets/View_Edits_And_Save_Calibration_Files_Window.qss",
    "Themes/Qt_Style_Sheets/Workflow_Tabs.qss",
    "Themes/Qt_Style_Sheets/EoSHolo.qss",
    "Themes/Qt_Style_Sheets/EoSHolo_Node_Popup.qss",
]

EOSHOLO_STYLE_SHEET_FILES = [
    "Themes/Qt_Style_Sheets/EoSHolo.qss",
    "Themes/Qt_Style_Sheets/EoSHolo_Node_Popup.qss",
]

EOSHOLO_NODE_POPUP_STYLE_SHEET_FILES = [
    "Themes/Qt_Style_Sheets/EoSHolo_Node_Popup.qss",
]





# Define color palette for light mode
LIGHT_COLORS = {
    "Primary_Background": "#FFFFFF",    # page background — medium gray so cards pop
    "Secondary_Background": "#FFFFFF",  # top-level cards — pure white
    "Tertiary_Background": "#FFFFFF",   # surfaces inside cards
    "Quaternary_Background": "#FFFFFF", # nested cards / inputs
    "Quinary_Background": "#EEEEEE",    # deeper nested
    "Senary_Background": "#E8E8E8",     # deepest nested

    "Run_Tab_Row_Background": "#FFFFFF",

    "Primary_Text": "#111111",          # near-black for high contrast
    "Secondary_Text": "#212121",        # 87% black
    "Tertiary_Text": "#4D4D4D",         # 70% black
    "Quaternary_Text": "#757575",       # 50% black
    "Quinary_Text": "#9E9E9E",          # 38% black
    # "Senary_Text": "#"

    "Warning_Color": RED["500"],
    "Warning_Accent": RED["700"],

    "Caution_Text": TAN["800"],
    "Caution_Text_Accent": TAN["300"],
    "Secondary_Caution_Text": TAN["600"],

    "Primary_Color": ORANGE["600"],
    "Primary_Accent": ORANGE["800"],
    "Primary_Disabled": ORANGE_50_PERCENT_LIGHT["600"],
    "Secondary_Color": BLUE["600"],
    "Secondary_Accent": BLUE["800"],
    "Secondary_Disabled": BLUE_50_PERCENT_LIGHT["600"],
    "Tertiary_Color": GREEN["600"],
    "Tertiary_Accent": GREEN["800"],
    "Tertiary_Disabled": GREEN_50_PERCENT_LIGHT["600"],

    "Neautral_Color": NEUTRAL_CREAM["800"],

    "Card_Border": "transparent",

}





# Define color palette for dark mode
DARK_COLORS = {
    "Primary_Background": "#121212",    # Dark Grey
    "Secondary_Background": "#202020",  # 5% white overlay
    "Tertiary_Background": "#222222",   # 7% white overlay
    "Quaternary_Background": "#242424", # 8% white overlay
    "Quinary_Background": "#262626",    # 9% white overlay
    "Senary_Background": "#292929",     # 11% white overlay

    "Run_Tab_Row_Background": "#000000",
    
    "Primary_Text": "#FFFFFF",          # White
    "Secondary_Text": "#DEDEDE",        # 87% white
    "Tertiary_Text": "#B3B3B3",         # 70% white
    "Quaternary_Text": "#808080",       # 50% white
    "Quinary_Text": "#616161",          # 38% white
    # "Senary_Text": "#"

    "Warning_Color": RED["800"],
    "Warning_Accent": RED["500"],

    "Caution_Text": TAN["300"],
    "Caution_Text_Accent": TAN["700"],
    "Secondary_Caution_Text": TAN["300"],

    "Primary_Color": ORANGE["800"],
    "Primary_Accent": ORANGE["600"],
    "Primary_Disabled": ORANGE_50_PERCENT_DARK["800"],
    "Secondary_Color": BLUE["800"],
    "Secondary_Accent": BLUE["600"],
    "Secondary_Disabled": BLUE_50_PERCENT_DARK["800"],
    "Tertiary_Color": GREEN["800"],
    "Tertiary_Accent": GREEN["600"],
    "Tertiary_Disabled": GREEN_50_PERCENT_DARK["800"],

    "Neautral_Color": NEUTRAL_CREAM["500"],

    "Card_Border": "transparent",       # no border needed in dark mode

}





# Get the current theme and its colors
def Get_Theme():

    # Load the theme selection from the settings
    Settings = QSettings("EoSAlign", "EoSAlignApp")

    # Find the current theme
    Current_Theme = Settings.value("Theme", "System Default")

    # Check if the current theme is light or dark
    if Current_Theme == "Light":
        return "Light", STYLE_SHEET_FILES, LIGHT_COLORS
    elif Current_Theme == "Dark":
        return "Dark", STYLE_SHEET_FILES, DARK_COLORS
    
    # If the current theme is set to system default, check if the system is in light or dark mode
    else:
        # System default — darkdetect can return None on some Windows builds, so check explicitly
        is_dark = darkdetect.isDark()
        if is_dark is True:
            return "Dark", STYLE_SHEET_FILES, DARK_COLORS
        if is_dark is None:
            # darkdetect couldn't detect; read the Windows registry directly as a fallback
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                ) as _key:
                    _value, _ = winreg.QueryValueEx(_key, "AppsUseLightTheme")
                    if _value == 0:
                        return "Dark", STYLE_SHEET_FILES, DARK_COLORS
            except Exception:
                pass
        return "Light", STYLE_SHEET_FILES, LIGHT_COLORS


# Load and combine one or more QSS files
def Load_Style_Sheet_From_Files(Style_Sheet_File_Paths, Colors, Get_Resource_Path_Function):

    # Normalize the input so callers can pass either one file path or a list of file paths
    if isinstance(Style_Sheet_File_Paths, str):
        List_Of_Style_Sheet_File_Paths = [Style_Sheet_File_Paths]
    else:
        List_Of_Style_Sheet_File_Paths = list(Style_Sheet_File_Paths)

    # Load the contents of each stylesheet file in order
    List_Of_Style_Sheet_Text_Blocks = []
    for Style_Sheet_File_Path in List_Of_Style_Sheet_File_Paths:
        Resolved_Style_Sheet_Path = Get_Resource_Path_Function(Style_Sheet_File_Path)
        with open(Resolved_Style_Sheet_Path, "r") as Style_Sheet_File:
            Current_Style_Sheet_Text = Style_Sheet_File.read()
        List_Of_Style_Sheet_Text_Blocks.append(Current_Style_Sheet_Text)

    # Combine the stylesheet blocks into one stylesheet string
    Combined_Style_Sheet = "\n\n".join(List_Of_Style_Sheet_Text_Blocks)

    # Replace all color tokens with the current theme values
    for Color, Hex_Code in Colors.items():
        Combined_Style_Sheet = Combined_Style_Sheet.replace(f"{{{Color}}}", Hex_Code)

    # Return the final stylesheet string
    return Combined_Style_Sheet


# Load the full application stylesheet for the current theme
def Load_Application_Style_Sheet(Get_Resource_Path_Function):

    # Get the current theme information
    Theme_Name, Style_Sheet_File_Paths, Colors = Get_Theme()

    # Load and combine the stylesheet files for the application
    Application_Style_Sheet = Load_Style_Sheet_From_Files(
        Style_Sheet_File_Paths,
        Colors,
        Get_Resource_Path_Function,
    )

    # Return the theme name, stylesheet text, and colors
    return Theme_Name, Application_Style_Sheet, Colors


# Load the EoSHolo-specific stylesheet block for widget-local application
def Load_EoSHolo_Style_Sheet(Get_Resource_Path_Function):

    # Get the current theme colors
    Theme_Name, Style_Sheet_File_Paths, Colors = Get_Theme()

    # Load only the EoSHolo-specific stylesheet files
    EoSHolo_Style_Sheet = Load_Style_Sheet_From_Files(
        EOSHOLO_STYLE_SHEET_FILES,
        Colors,
        Get_Resource_Path_Function,
    )

    # Return the EoSHolo-specific stylesheet text
    return EoSHolo_Style_Sheet


# Load the EoSHolo node popup stylesheet block for popup-local application
def Load_EoSHolo_Node_Popup_Style_Sheet(Get_Resource_Path_Function):

    # Get the current theme colors
    Theme_Name, Style_Sheet_File_Paths, Colors = Get_Theme()

    # Load only the EoSHolo node popup stylesheet files
    EoSHolo_Node_Popup_Style_Sheet = Load_Style_Sheet_From_Files(
        EOSHOLO_NODE_POPUP_STYLE_SHEET_FILES,
        Colors,
        Get_Resource_Path_Function,
    )

    # Return the EoSHolo node popup stylesheet text
    return EoSHolo_Node_Popup_Style_Sheet




