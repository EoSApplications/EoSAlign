# Load Libraries
    # Load standard libraries
import sys
import os
import time
from pathlib import Path
from Installed_Applications_Registry import Register_Installed_Application_And_Exit_If_Requested
from Session_Paths import (
    start_new_session,
    cleanup_current_session_directories,
    sweep_stale_session_directories,
)


def Cleanup_Session_Files():
    # Delete figure cache and manual-entry data files for this app session only.
    cleanup_current_session_directories()





# Make the EoSAlign Window
def Make_The_EoSAlign_Window():

    # Load libraries
        # Load standard libraries
    import darkdetect
        # Load third party libraries
    from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QApplication)
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QIcon
        # Load local functions from local files
    from Settings import Settings
    from MenuBar import MainMenuBar
    from Banner import Banner
    from Loading_Message import Get_Resource_Path
    from Run_Tab_Container import Step_By_Step_Layout
    from EoSAlign__All_Steps_Layout import All_Steps_Layout
    from Message_Manager import Warning_Message
    from Themes.Theme import Get_Theme
    from Window_Show_Guard import Guard_Unwanted_Window_Shows



    class EoSAlign(QMainWindow):
        def __init__(self):
            super().__init__()

            # Build Settings lazily to avoid creating an extra top-level dialog at startup.
            self.Settings = None
            # Set the window title
            self.setWindowTitle("EoSAlign")
            # Set the window logo
            Dark_Mode = darkdetect.isDark()
            EoSAlign_Logo_File = "Graphics/EoSAlign_With_Sun.png"
            self.setWindowIcon(QIcon(Get_Resource_Path(EoSAlign_Logo_File)))
            # Set palette background so Windows uses the theme color during maximize/restore.
            _, _, Startup_Colors = Get_Theme()
            from PySide6.QtGui import QPalette, QColor
            Palette = self.palette()
            Palette.setColor(QPalette.Window, QColor(Startup_Colors.get('Primary_Background', '#ffffff')))
            self.setPalette(Palette)
            # Set the menu bar
            self.setMenuBar(MainMenuBar(self))

            # Setup the the main layout
            EoSAlign_Main_Widget = QWidget()
            EoSAlign_Main_Layout = QVBoxLayout(EoSAlign_Main_Widget)
            EoSAlign_Main_Layout.setContentsMargins(0, 0, 0, 0)
            EoSAlign_Main_Layout.setSpacing(0)
            # Add the banner to the main layout
            self.banner = Banner("", Get_Resource_Path("Graphics/EoSAlign_With_Sun.png"))
            EoSAlign_Main_Layout.addWidget(self.banner)
            # Add a place for the main widgets
            self.Main_Widget_Layout = QStackedWidget()
            EoSAlign_Main_Layout.addWidget(self.Main_Widget_Layout)
            self.setCentralWidget(EoSAlign_Main_Widget)
            # Load the current layout
            self.Load_The_Current_EoSAlign_Layout()

            # Find the size of the screen
            Screen = QApplication.primaryScreen()
            Screen_Geometry = Screen.availableGeometry()
            EoSAlign_Screen_Width = int(Screen_Geometry.width() * 0.7)
            EoSAlign_Screen_Height = int(Screen_Geometry.height() * 0.8)
            # Center the application launcher on the user's screen
            X = Screen_Geometry.x() + (Screen_Geometry.width() - EoSAlign_Screen_Width) // 2
            Y = Screen_Geometry.y() + (Screen_Geometry.height() - EoSAlign_Screen_Height) // 2
            # Set the size and position of the application launcher window
            self.setGeometry(X, Y, EoSAlign_Screen_Width, EoSAlign_Screen_Height)
            self.setMinimumSize(500, 400)


        # Get the current settings
        def Get_Settings_Dialog(self):

            # Check if there are any settings
            if self.Settings is None:
                # parent=None makes Settings a true top-level window so it
                # minimises to the taskbar instead of an owned-window strip.
                self.Settings = Settings(None)
                # Check which layout to use
                if hasattr(self.Settings, "EoSAlign_Layout_Changed"):
                    self.Settings.EoSAlign_Layout_Changed.connect(self.Switch_The_EoSAlign_Layout)
            
            # Return the current
            return self.Settings


        # Load the current EoSAlign layout
        def Load_The_Current_EoSAlign_Layout(self):

            # Load the current layout selection from the settings
            EoSAlign_Settings = QSettings("EoSAlign", "EoSAlignApp")
            Layout_Selection = EoSAlign_Settings.value("Layout Selection", "Step by Step")
            # Check if the layout selection is valid
            with Guard_Unwanted_Window_Shows():
                Layout = Step_By_Step_Layout() if Layout_Selection == "Step by Step" else All_Steps_Layout()
            # Add the layout to the main widget layout
            self.Main_Widget_Layout.addWidget(Layout)
            self.Current_Layout = Layout


        # Switch the EoSAlign layout
        def Switch_The_EoSAlign_Layout(self, Layout_Selection):

            # Build the new layout while the old one is still visible, then
            # switch atomically - the QStackedWidget never has an empty page.
            with Guard_Unwanted_Window_Shows():
                New_Layout = Step_By_Step_Layout() if Layout_Selection == "Step by Step" else All_Steps_Layout()
            Old_Layout = self.Current_Layout
            self.Main_Widget_Layout.addWidget(New_Layout)
            self.Main_Widget_Layout.setCurrentWidget(New_Layout)
            self.Current_Layout = New_Layout
            # Remove and discard the old layout now that it is hidden.
            if Old_Layout is not None:
                self.Main_Widget_Layout.removeWidget(Old_Layout)
                Old_Layout.deleteLater()


        # Route the File > Open action to the active layout
        def handle_open_file(self):

            Layout = getattr(self, "Current_Layout", None)
            if Layout is not None and hasattr(Layout, "Handle_Menu_Open_Action"):
                Layout.Handle_Menu_Open_Action()
            else:
                Warning_Message(self, "Menu Action Not Available", action="Open")


        # Route the File > Save Data action to the active layout
        def handle_save_data(self):

            Layout = getattr(self, "Current_Layout", None)
            if Layout is not None and hasattr(Layout, "Handle_Menu_Save_Action"):
                Layout.Handle_Menu_Save_Action()
            else:
                Warning_Message(self, "Menu Action Not Available", action="Save Data")


    # Return the EoSAlign Window
    return EoSAlign



# Create the EoSAlign Window
def EoSAlign(Parent=None):

    # Make the EoSAlign Window
    EoSAlign_Window = Make_The_EoSAlign_Window()

    # Return the EoSAlign Window
    return EoSAlign_Window()



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
        print("EoSAlign could not load its Qt (PySide6) libraries:")
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
        print("  2. Install/run EoSAlign from a dedicated conda environment or a")
        print("     plain venv instead of the base environment.")
        print("")
        sys.exit(1)



# Start the EoSAlign application
def main():

    Exit_If_PySide6_Cannot_Be_Imported()

    Register_Installed_Application_And_Exit_If_Requested("EoSAlign")

    # Set the path to the project directory
    # Use sys.executable when frozen so os.chdir() targets the .exe folder, not
    # the PyInstaller temp extraction folder (sys._MEIPASS).  Pointing CWD at
    # sys._MEIPASS prevents Windows from deleting the temp folder on exit.
    if getattr(sys, 'frozen', False):
        project_dir = os.path.dirname(sys.executable)
    else:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    # Sweep stale temp folders left by crashed sessions before starting a new one.
    sweep_stale_session_directories()

    # Assign a fresh app-session id so each EoSAlign window gets its own temp space.
    start_new_session()

    # Delete figure cache and manual-entry data files for this session.
    Cleanup_Session_Files()

    # Load libraries
        # Load third party libraries
    from PySide6.QtWidgets import QApplication, QWidget, QSplashScreen
    from PySide6.QtCore import QObject, QEvent, QTimer
    from PySide6.QtGui import QIcon
        # Load local functions from local files
    from Loading_Message import Get_Resource_Path, Create_Loading_Message, Update_Loading_Message, Load_Fonts
    from Mac_Terminal_Commands import Prompt_To_Install_Mac_Terminal_Commands_If_Needed
    from Shadow_Filter import Install_Shadow_Filter

    # Create the application
    App = QApplication(sys.argv)
    App.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
    # Force the Fusion style so the stylesheet (border-radius, fonts, dropdown
    # sizing) is fully obeyed on every OS instead of native widget painting
    # taking over (macOS's native style ignores much of the QSS below).
    App.setStyle("Fusion")
    App.aboutToQuit.connect(Cleanup_Session_Files)


    # Display the loading message while the window is being build
    class Startup_Window_Guard(QObject):
        def __init__(self):
            super().__init__()
            self.Allowed_Window_IDs = set()
            self.Enabled = True


        # Allow widgets to be displayed during startup
        def allow(self, widget):

            if widget is not None:
                self.Allowed_Window_IDs.add(id(widget))


        # Remove the window display guard after startup is complete
        def disable(self):

            self.Enabled = False


        # Prevent windows from being displayed during startup
        def eventFilter(self, obj, event):

            # Allow everything to be displayed
            if not self.Enabled:
                return False
            # Check if the window has been built
            if event.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
                # Allow everything to be displayed
                if id(obj) in self.Allowed_Window_IDs:
                    return False
                # Display the window off screen
                if isinstance(obj, QSplashScreen):
                    return False
                # Set the off screen position for the window
                obj.move(-32000, -32000)

            # Allow everything to be displayed
            return False

    # Set up the window to be built off screen
    Startup_Window_Guard_Filter = Startup_Window_Guard()
    App.installEventFilter(Startup_Window_Guard_Filter)
    # Load bundled fonts before the stylesheet so font-family resolves correctly
    Load_Fonts(App)
    Install_Shadow_Filter(App)
    # Create the loading screen
    Loading_Screen = Create_Loading_Message(App, Logo_Path=Get_Resource_Path("Graphics/EoSAlign_With_Sun.png"))
    Startup_Window_Guard_Filter.allow(Loading_Screen)
    # Start the timer
    Timer = {"Started Loading the Application": time.perf_counter(), "Last Loading Message": time.perf_counter()}

    # Start loading the calibration files
    Update_Loading_Message(Loading_Screen, App, "Loading calibration files...", Timer)
    # Load libraries
        # Load local functions from local files
    # Load the cached calibration information
    import EoS_Math.Build_Dataframe
    # Start loading the style sheet
    Update_Loading_Message(Loading_Screen, App, "Loading style sheet...", Timer)
    # Load libraries
        # Load third party libraries
    from Themes.Theme import Load_Application_Style_Sheet
    # Get the current theme
    Theme_Name, Style_Sheet, COLORS = Load_Application_Style_Sheet(Get_Resource_Path)

    # Start applying the style sheet
    Update_Loading_Message(Loading_Screen, App, "Applying style sheet...", Timer)
    # Apply the style sheet to the application
    App.setStyleSheet(Style_Sheet)
    # Set the app-level palette so the DWM uses the theme color during
    # maximize/restore animation (stylesheet alone doesn't reach this).
    from PySide6.QtGui import QPalette, QColor
    App_Palette = App.palette()
    App_Background_Color = COLORS.get('Primary_Background', '#ffffff')
    App_Palette.setColor(QPalette.Window,        QColor(App_Background_Color))
    App_Palette.setColor(QPalette.Base,          QColor(App_Background_Color))
    App_Palette.setColor(QPalette.AlternateBase, QColor(App_Background_Color))
    App.setPalette(App_Palette)

    # Start building the application launcher
    Update_Loading_Message(Loading_Screen, App, "Building EoSAlign...", Timer)
    # Build and instantiate the main window class
    EoSAlign_Window_Class = Make_The_EoSAlign_Window()

    # Start the application launcher
    Update_Loading_Message(Loading_Screen, App, "Starting EoSAlign...", Timer)
    Window = EoSAlign_Window_Class()
    Startup_Window_Guard_Filter.allow(Window)
    # Show off-screen and transparent first to avoid any transient native frame flash.
    final_pos = Window.pos()
    Window.move(-32000, -32000)
    Window.setWindowOpacity(0.0)
    Window.show()
    App.processEvents()
    Window.move(final_pos)
    App.processEvents()
    Window.setWindowOpacity(1.0)
    App.processEvents()
    # Close the loading message
    Loading_Screen.finish(Window)
    Startup_Window_Guard_Filter.disable()
    App.removeEventFilter(Startup_Window_Guard_Filter)
    QTimer.singleShot(0, lambda: Prompt_To_Install_Mac_Terminal_Commands_If_Needed(Window, "EoSAlign"))

    # Check for updates in the background (skips silently if offline)
    from Check_For_Updates import Check_For_Updates_On_Startup
    Check_For_Updates_On_Startup(Window, "EoSAlign")
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




