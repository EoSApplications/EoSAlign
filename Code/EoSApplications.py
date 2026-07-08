# Load Libraries
    # Load standard libraries
import os
import sys
import time
    # Load local libraries
from Installed_Applications_Registry import (
    Get_Installed_Application_Entry,
    Get_Installed_Application_Launch_Path,
    Register_Installed_Application_And_Exit_If_Requested,
    Register_Installed_Application_For_Launch_Path,
)





# Convert a version string into a numeric tuple for comparisons
def Parse_Version(Version_Text):

    import re

    Version_Core = str(Version_Text or "").strip().lstrip("vV").split("-", 1)[0]
    Version_Parts = re.findall(r"\d+", Version_Core)
    Parsed_Version = tuple(int(Part) for Part in Version_Parts)

    # Return the numeric version tuple used for comparisons
    return Parsed_Version or (0,)



# Find the wrapper bundle status for one managed child application
def Get_Managed_Application_Status(Application_Id):

    from Version import Get_EoSApplications__Bundled_Applications

    Bundled_Applications = Get_EoSApplications__Bundled_Applications()
    Bundled_Version = str(Bundled_Applications.get(Application_Id, "") or "").strip()
    Installed_Application_Entry = Get_Installed_Application_Entry(Application_Id)
    Installed_Launch_Path = Get_Installed_Application_Launch_Path(Application_Id)
    Installed_Version = ""

    # Load the installed version from the registry entry when one exists
    if isinstance(Installed_Application_Entry, dict):
        Installed_Version = str(Installed_Application_Entry.get("Installed_Version", "") or "").strip()

    # If there is no usable launch path then the child application is effectively missing
    if not Installed_Launch_Path:
        Status_Information = {
            "Application_Id": Application_Id,
            "Bundled_Version": Bundled_Version,
            "Installed_Version": Installed_Version,
            "Installed_Launch_Path": None,
            "Status_Key": "missing",
            "Status_Text": f"Not installed in the local registry. Wrapper bundle version: {Bundled_Version}.",
        }
    # If the installed version is older than the wrapper bundle version then the child application is outdated relative to the wrapper
    elif Parse_Version(Installed_Version) < Parse_Version(Bundled_Version):
        Status_Information = {
            "Application_Id": Application_Id,
            "Bundled_Version": Bundled_Version,
            "Installed_Version": Installed_Version,
            "Installed_Launch_Path": Installed_Launch_Path,
            "Status_Key": "outdated",
            "Status_Text": f"Installed version {Installed_Version} is older than the wrapper bundle version {Bundled_Version}.",
        }
    # If the installed version is newer than the wrapper bundle version then keep the installed child and do not downgrade it
    elif Parse_Version(Installed_Version) > Parse_Version(Bundled_Version):
        Status_Information = {
            "Application_Id": Application_Id,
            "Bundled_Version": Bundled_Version,
            "Installed_Version": Installed_Version,
            "Installed_Launch_Path": Installed_Launch_Path,
            "Status_Key": "newer_than_wrapper",
            "Status_Text": f"Installed version {Installed_Version} is newer than the wrapper bundle version {Bundled_Version}.",
        }
    # Otherwise the installed child matches the wrapper bundle version
    else:
        Status_Information = {
            "Application_Id": Application_Id,
            "Bundled_Version": Bundled_Version,
            "Installed_Version": Installed_Version,
            "Installed_Launch_Path": Installed_Launch_Path,
            "Status_Key": "up_to_date",
            "Status_Text": f"Installed version {Installed_Version} matches the wrapper bundle version.",
        }

    # Return the wrapper bundle status for this child application
    return Status_Information


# Return True when EoSFitting.py currently sits next to this wrapper in Code/
# (still under development -- it lives at the repo root by default, so it is
# only treated as a managed child application once it is moved back)
def Is_EoSFitting_Available():

    from Version import EoSFitting_Menu_Enabled

    # EoSFitting is not ready to be offered as a selectable application yet
    if not EoSFitting_Menu_Enabled:
        return False

    from MenuBar import Check_If_Application_Can_Be_Launched

    # Return whether EoSFitting can currently be launched from this install context
    return Check_If_Application_Can_Be_Launched("EoSFitting.py", "EoSFitting", Application_Id="EoSFitting")



# Build a warning message for missing or outdated managed child applications
def Build_Managed_Application_Status_Warning_Message():

    Status_Lines = []

    Managed_Application_Ids = ["EoSAlign", "EoSHolo"]
    if Is_EoSFitting_Available():
        Managed_Application_Ids.append("EoSFitting")

    for Application_Id in Managed_Application_Ids:
        Status_Information = Get_Managed_Application_Status(Application_Id)

        # Only include child applications that are missing or older than the wrapper bundle version
        if Status_Information["Status_Key"] in ("missing", "outdated"):
            Status_Lines.append(f"{Application_Id}: {Status_Information['Status_Text']}")

    # Return no warning when every managed child application is already usable and current enough
    if not Status_Lines:
        return None

    Warning_Message_Text = "\n\n".join(Status_Lines)

    # Return the combined managed-child warning message
    return Warning_Message_Text



# Register bundled managed child applications when they are missing or older than the wrapper bundle version
def Sync_Bundled_Managed_Applications_With_The_Local_Registry():

    from MenuBar import Get_Bundled_Application_Path

    for Application_Id, Script_Name, Executable_Name in (
        ("EoSAlign", "EoSAlign.py", "EoSAlign"),
        ("EoSHolo", "EoSHolo.py", "EoSHolo"),
        ("EoSFitting", "EoSFitting.py", "EoSFitting"),
    ):
        Status_Information = Get_Managed_Application_Status(Application_Id)

        # Only adopt the bundled child application when the current registry entry is missing or older than the wrapper bundle version
        if Status_Information["Status_Key"] not in ("missing", "outdated"):
            continue

        Bundled_Application_Path = Get_Bundled_Application_Path(Script_Name, Executable_Name)

        # Skip this child application when the same-context bundled child does not exist
        if not os.path.exists(Bundled_Application_Path):
            continue

        Register_Installed_Application_For_Launch_Path(
            Application_Id,
            Bundled_Application_Path,
            Installed_By="Wrapper",
        )



# Make a launch window for EoSAlign and EoSHolo (plus EoSFitting, if present in Code/)
def Make_The_Application_Launch_Window():

    # Load libraries
        # Load standard libraries
    import darkdetect
        # Load third party libraries
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QIcon, QPixmap
    from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget
        # Load local functions from local files
    from Banner import Banner
    from Loading_Message import Get_Resource_Path
    from MenuBar import Launch_An_Application as Launch_Application, MainMenuBar
    from Message_Manager import Warning_Message


    # Create a card that will display the logo and description of each application choice on the landing page
    class Application_Card(QWidget):

        # Add a signal for when the application card is clicked
        Application_Card_Clicked = Signal()

        # Setup the application card
        def __init__(self, Application_Logo_Path, Application_Title_Text, Application_Description_Text):
            super().__init__()

            # Setup the layout for the application card
            self.setObjectName("Application_Card")
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            Application_Card_Layout = QVBoxLayout(self)
            Application_Card_Layout.setContentsMargins(20, 20, 20, 20)
            Application_Card_Layout.setSpacing(12)
            Application_Card_Layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

            # Setup the application logo with a fixed height so both cards have equal image space
            Application_Logo = QLabel()
            Application_Logo.setObjectName("Application_Card_Logo")
            Application_Logo.setAlignment(Qt.AlignCenter)
            Application_Logo.setFixedHeight(160)
            Logo = QPixmap(Get_Resource_Path(Application_Logo_Path))
            if not Logo.isNull():
                # Scale by the device pixel ratio (and clear it back to 1.0 before rescaling) so the
                # logo renders sharply on HiDPI/scaled displays, matching Banner.py's approach.
                Device_Pixel_Ratio = QApplication.primaryScreen().devicePixelRatio()
                Scaled_Logo = Logo.scaled(int(220 * Device_Pixel_Ratio), int(160 * Device_Pixel_Ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                Scaled_Logo.setDevicePixelRatio(Device_Pixel_Ratio)
                Application_Logo.setPixmap(Scaled_Logo)
            Application_Card_Layout.addWidget(Application_Logo)

            # Setup the application description so users understand the purpose of each child application
            Application_Description = QLabel(Application_Description_Text)
            Application_Description.setObjectName("Application_Card_Description")
            Application_Description.setWordWrap(True)
            Application_Description.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            Application_Card_Layout.addWidget(Application_Description)

            Application_Card_Layout.addStretch()


        # When the application card is clicked emit the clicked signal
        def mousePressEvent(self, Event):

            self.Application_Card_Clicked.emit()
            super().mousePressEvent(Event)



    # Create the landing page for the application launcher
    class Application_Launcher(QWidget):

        # Add signals for when the user clicks on the application cards
        Launch_EoSAlign = Signal()
        Launch_EoSHolo = Signal()
        Launch_EoSFitting = Signal()

        def __init__(self):
            super().__init__()

            from Collapsible_Sections import Collapsible_Content_Container

            # Setup the layout for the landing page
            self.setObjectName("Application_Launcher")
            Application_Launcher_Layout = QVBoxLayout(self)
            Application_Launcher_Layout.setContentsMargins(40, 40, 40, 40)
            Application_Launcher_Layout.setSpacing(20)

            # Create the application card for EoSAlign
            self.EoSAlign_Application_Card = Application_Card(
                Application_Logo_Path="Graphics/EoSAlign_With_Sun.png",
                Application_Title_Text="EoSAlign",
                Application_Description_Text=("Convert and compare high-pressure experimental data across different equations of state calibrations."),
            )
            self.EoSAlign_Application_Card.Application_Card_Clicked.connect(self.Launch_EoSAlign)

            # Create the application card for EoSHolo
            self.EoSHolo_Application_Card = Application_Card(
                Application_Logo_Path="Graphics/EoSHolo_With_Sun.png",
                Application_Title_Text="EoSHolo",
                Application_Description_Text=("Explore the network of equation of state calibrations as an interactive graph."),
            )
            self.EoSHolo_Application_Card.Application_Card_Clicked.connect(self.Launch_EoSHolo)

            # Create the application card for EoSFitting only when it is actually
            # available in this install context (it lives at the repo root under
            # development by default, and only becomes a managed child once it is
            # moved back into Code/, next to this wrapper)
            self.EoSFitting_Application_Card = None
            if Is_EoSFitting_Available():
                self.EoSFitting_Application_Card = Application_Card(
                    Application_Logo_Path="Graphics/EoS_With_Sun.png",
                    Application_Title_Text="EoSFitting",
                    Application_Description_Text=("Fit equations of state to P–V, P–λ, or P–ν data with Monte Carlo error propagation and pressure-scale alignment."),
                )
                self.EoSFitting_Application_Card.Application_Card_Clicked.connect(self.Launch_EoSFitting)

            # Place cards side by side in a container widget
            Application_Card_Container = QWidget()
            Application_Card_Container.setObjectName("Application_Card_Container")
            Application_Card_Container_Layout = QHBoxLayout(Application_Card_Container)
            Application_Card_Container_Layout.setContentsMargins(0, 0, 0, 0)
            Application_Card_Container_Layout.setSpacing(30)
            Application_Card_Container_Layout.addWidget(self.EoSAlign_Application_Card)
            Application_Card_Container_Layout.addWidget(self.EoSHolo_Application_Card)
            if self.EoSFitting_Application_Card is not None:
                Application_Card_Container_Layout.addWidget(self.EoSFitting_Application_Card)

            # Wrap the cards in a permanently-expanded collapsible section
            Application_Section = Collapsible_Content_Container("Select an Application:", Application_Card_Container, Initially_Show_Container=True, Expanding_Content=True,)
            Application_Section.Disable_Collapsible_Section(True)
            Application_Launcher_Layout.addWidget(Application_Section)
            Application_Launcher_Layout.addStretch()

    # Create the application launcher window
    class Application_Launcher_Window(QMainWindow):

        def __init__(self):
            super().__init__()
            self.Settings = None

            # Set the window title
            self.setWindowTitle("EoS Applications")
            # Set the window logo
            Dark_Mode = darkdetect.isDark()
            Logo_File = "Graphics/EoSApplications_With_Sun.png" if Dark_Mode else "Graphics/EoSApplications_With_Sun.png"
            self.setWindowIcon(QIcon(Get_Resource_Path(Logo_File)))
            # Set palette background so Windows uses the theme color during maximize/restore.
            from PySide6.QtGui import QColor, QPalette
            from Themes.Theme import Get_Theme
            Theme_Name, Style_Sheet, Startup_Colors = Get_Theme()
            Palette = self.palette()
            Palette.setColor(QPalette.Window, QColor(Startup_Colors.get('Primary_Background', '#ffffff')))
            self.setPalette(Palette)
            # Set the menu bar
            self.setMenuBar(MainMenuBar(self))

            # Setup the the main layout
            Application_Launcher_Main_Widget = QWidget()
            Application_Launcher_Main_Layout = QVBoxLayout(Application_Launcher_Main_Widget)
            Application_Launcher_Main_Layout.setContentsMargins(0, 0, 0, 0)
            Application_Launcher_Main_Layout.setSpacing(0)
            # Add the banner to the main layout
            self.banner = Banner("", Get_Resource_Path("Graphics/EoSApplications_With_Sun.PNG"))
            Application_Launcher_Main_Layout.addWidget(self.banner)
            # Add a place for the main widgets
            self.Main_Widget_Layout = QStackedWidget()
            Application_Launcher_Main_Layout.addWidget(self.Main_Widget_Layout)
            self.setCentralWidget(Application_Launcher_Main_Widget)
            # Add the application launcher to the main widget
            self.Application_Launcher_Widget = Application_Launcher()
            self.Application_Launcher_Widget.Launch_EoSAlign.connect(self.Open_EoSAlign_Application)
            self.Application_Launcher_Widget.Launch_EoSHolo.connect(self.Open_EoSHolo_Application)
            self.Application_Launcher_Widget.Launch_EoSFitting.connect(self.Open_EoSFitting_Application)
            self.Main_Widget_Layout.addWidget(self.Application_Launcher_Widget)

            # Find the size of the screen
            Screen = QApplication.primaryScreen()
            Screen_Geometry = Screen.availableGeometry()
            Application_Launcher_Screen_Width = int(Screen_Geometry.width() * 0.7)
            Application_Launcher_Screen_Height = int(Screen_Geometry.height() * 0.8)
            # Center the application launcher on the user's screen
            X = Screen_Geometry.x() + (Screen_Geometry.width() - Application_Launcher_Screen_Width) // 2
            Y = Screen_Geometry.y() + (Screen_Geometry.height() - Application_Launcher_Screen_Height) // 2
            # Set the size and position of the application launcher window
            self.setGeometry(X, Y, Application_Launcher_Screen_Width, Application_Launcher_Screen_Height)
            self.setMinimumSize(500, 400)

            # After the launcher is visible, warn once if a managed child application is missing or older than the wrapper bundle
            QTimer.singleShot(1200, self.Show_Managed_Application_Status_Warnings)


        # Find the shared settings dialog for this wrapper window
        def Get_Settings_Dialog(self):

            if self.Settings is None:
                from Settings import Settings
                self.Settings = Settings(self)

            # Return the cached settings dialog for this wrapper window
            return self.Settings


        # Show the main widget layout
        def Show_Main_Widget_Layout(self):

            self.Main_Widget_Layout.setCurrentIndex(0)


        # Warn once if a managed child application is missing or outdated relative to the wrapper bundle metadata
        def Show_Managed_Application_Status_Warnings(self):

            Warning_Message_Text = Build_Managed_Application_Status_Warning_Message()

            # Do not show a warning when every managed child application is already usable and current enough
            if not Warning_Message_Text:
                return

            Warning_Message(
                self,
                "Managed Applications Need Attention",
                message=Warning_Message_Text,
            )


        # Open the EoSAlign application
        def Open_EoSAlign_Application(self):

            Launch_Application("EoSAlign.py", "EoSAlign", Application_Id="EoSAlign")


        # Open the EoSHolo application
        def Open_EoSHolo_Application(self):

            Launch_Application("EoSHolo.py", "EoSHolo", Application_Id="EoSHolo")


        # Open the EoSFitting application
        def Open_EoSFitting_Application(self):

            Launch_Application("EoSFitting.py", "EoSFitting", Application_Id="EoSFitting")


    # Return the application launcher window class
    return Application_Launcher_Window



# Confirm PySide6's compiled Qt bindings can actually load, and exit with actionable
# guidance instead of a bare traceback if not. This specifically catches the case of
# running from an Anaconda/Miniconda base environment whose bundled msvcp140.dll
# (living next to python.exe, which Windows always searches before PySide6's own
# newer bundled copy) is older than what PySide6's Qt6 binaries require.
def Exit_If_PySide6_Cannot_Be_Imported():

    try:
        import PySide6.QtCore  # noqa: F401
    except ImportError as Import_Error:
        # Only intercept the DLL-load failure this guard is meant for; let any other
        # ImportError (e.g. PySide6 genuinely not installed) surface normally
        if "DLL load failed" not in str(Import_Error):
            raise

        print("")
        print("EoSApplications could not load its Qt (PySide6) libraries:")
        print(f"    {Import_Error}")
        print("")
        print("This usually happens when running from an Anaconda/Miniconda base")
        print("environment whose bundled Microsoft Visual C++ runtime (msvcp140.dll,")
        print("in the same folder as python.exe) is older than what PySide6's Qt6")
        print("libraries require. Windows loads that older copy first, before")
        print("PySide6's own newer bundled copy, causing this failure.")
        print("")
        print("To fix it, try one of the following:")
        print("  1. Update conda:  conda update -n base --all")
        print("  2. Install/run EoSApplications from a dedicated conda environment")
        print("     or a plain venv instead of the base environment.")
        print("")
        sys.exit(1)



# Start the launch window
def main():

    Exit_If_PySide6_Cannot_Be_Imported()

    Register_Installed_Application_And_Exit_If_Requested("EoSApplications")

    # Set the path to the project directory
    # Use sys.executable when frozen so os.chdir() targets the .exe folder, not
    # the PyInstaller temp extraction folder (sys._MEIPASS).  Pointing CWD at
    # sys._MEIPASS prevents Windows from deleting the temp folder on exit.
    if getattr(sys, 'frozen', False):
        Project_Directory = os.path.dirname(sys.executable)
    else:
        Project_Directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(Project_Directory)
    if Project_Directory not in sys.path:
        sys.path.insert(0, Project_Directory)

    # Make sure the wrapper claims bundled child applications when they are missing or older than the wrapper bundle version
    Sync_Bundled_Managed_Applications_With_The_Local_Registry()

    # Load libraries
        # Load third party libraries
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
        # Load local functions from local files
    from Loading_Message import Create_Loading_Message, Get_Resource_Path, Load_Fonts, Update_Loading_Message
    from Mac_Terminal_Commands import Prompt_To_Install_Mac_Terminal_Commands_If_Needed
    from Shadow_Filter import Install_Shadow_Filter

    # Create the application
    App = QApplication(sys.argv)
    App.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
    # Force the Fusion style so the stylesheet (border-radius, fonts, dropdown
    # sizing) is fully obeyed on every OS instead of native widget painting
    # taking over (macOS's native style ignores much of the QSS below).
    App.setStyle("Fusion")

    # Load bundled fonts before the stylesheet so font-family resolves correctly
    Load_Fonts(App)
    Install_Shadow_Filter(App)

    # Create the loading screen
    Loading_Screen = Create_Loading_Message(App, Logo_Path=Get_Resource_Path("Graphics/EoSApplications_With_Sun.PNG"))
    # Start the timer
    Timer = {"Started Loading the Application": time.perf_counter(), "Last Loading Message": time.perf_counter()}

    # Start loading the calibration files
    Update_Loading_Message(Loading_Screen, App, "Loading calibration files...", Timer)
    # Get the cached calibration information
    import EoS_Math.Build_Dataframe
    # Start loading the style sheet
    Update_Loading_Message(Loading_Screen, App, "Loading style sheet...", Timer)
    from Themes.Theme import Load_Application_Style_Sheet
    Theme_Name, Style_Sheet, COLORS = Load_Application_Style_Sheet(Get_Resource_Path)

    # Start applying the style sheet
    Update_Loading_Message(Loading_Screen, App, "Applying style sheet...", Timer)
    App.setStyleSheet(Style_Sheet)
    # Set the app-level palette so the DWM uses the theme color during maximize/restore animation
    from PySide6.QtGui import QColor, QPalette
    App_Palette = App.palette()
    App_Background_Color = COLORS.get('Primary_Background', '#ffffff')
    App_Palette.setColor(QPalette.Window, QColor(App_Background_Color))
    App_Palette.setColor(QPalette.Base, QColor(App_Background_Color))
    App_Palette.setColor(QPalette.AlternateBase, QColor(App_Background_Color))
    App.setPalette(App_Palette)

    # Start building the application launcher
    Update_Loading_Message(Loading_Screen, App, "Building the application launcher...", Timer)
    Application_Launcher_Window = Make_The_Application_Launch_Window()

    # Start the application launcher
    Update_Loading_Message(Loading_Screen, App, "Starting the application launcher...", Timer)
    Window = Application_Launcher_Window()
    Window.show()
    Loading_Screen.finish(Window)
    QTimer.singleShot(0, lambda: Prompt_To_Install_Mac_Terminal_Commands_If_Needed(Window, "EoSApplications"))

    # Check for updates in the background (skips silently if offline)
    from Check_For_Updates import Check_For_Updates_On_Startup
    Check_For_Updates_On_Startup(Window, "EoSApplications")
    from Check_For_Calibration_Updates import Check_For_Calibration_Updates_On_Startup
    Check_For_Calibration_Updates_On_Startup(Window)

    # Print the loading message summary to the console
    print(f"")
    print(f"Total loading time: {(time.perf_counter() - Timer['Started Loading the Application']):.4f} seconds")
    print(f"")

    # Close the window when the user clicks the exit button
    sys.exit(App.exec())



# Start the application
if __name__ == "__main__":
    main()

