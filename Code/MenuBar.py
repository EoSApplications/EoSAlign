# Load libraries
    # Load standard libraries
import os
import subprocess
import sys
    # Load third party libraries
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMenuBar, QMessageBox
from Installed_Applications_Registry import Check_If_Installed_Application_Entry_Is_Usable, Get_Installed_Application_Launch_Path
from Message_Manager import Warning_Message
from Version import EoSFitting_Menu_Enabled
from Window_Show_Guard import Guard_Unwanted_Window_Shows





# Find the bundled application paths that are valid for the current runtime layout
def Get_Bundled_Application_Path_Candidates(Script_Name, Executable_Name):

    # Check if the application is a script or an executable
    if getattr(sys, 'frozen', False):
        # Check if this is a Mac
        if sys.platform == 'darwin':
            # sys.executable is inside AppName.app/Contents/MacOS/
            Application_Directory = os.path.normpath(os.path.join(os.path.dirname(sys.executable), '..', '..', '..'))
            Candidate_Paths = [
                os.path.join(Application_Directory, f'{Executable_Name}.app'),
                os.path.join(Application_Directory, Executable_Name, f'{Executable_Name}.app'),
            ]
        # Otherwise this is Windows or Linux (Linux executables have no file extension)
        else:
            # onedir builds place each app's executable inside its own subfolder
            # (e.g. Distribution_Files/EoSAlign/EoSAlign.exe), so sys.executable
            # sits one level deeper than the shared install directory. Check both
            # the current process's own folder and its parent for sibling apps.
            Executable_Directory = os.path.dirname(sys.executable)
            Parent_Directory = os.path.dirname(Executable_Directory)
            Executable_File_Name = Executable_Name + '.exe' if sys.platform == 'win32' else Executable_Name
            Candidate_Paths = [
                os.path.join(Executable_Directory, Executable_File_Name),
                os.path.join(Executable_Directory, Executable_Name, Executable_File_Name),
                os.path.join(Parent_Directory, Executable_File_Name),
                os.path.join(Parent_Directory, Executable_Name, Executable_File_Name),
            ]
    # Otherwise this is a script
    else:
        Script_Directory = os.path.dirname(os.path.abspath(__file__))
        Candidate_Paths = [os.path.join(Script_Directory, Script_Name)]

    # Return the bundled application paths for the current runtime mode
    return Candidate_Paths



# Find the bundled application path beside the current script or executable
def Get_Bundled_Application_Path(Script_Name, Executable_Name):

    Candidate_Paths = Get_Bundled_Application_Path_Candidates(Script_Name, Executable_Name)

    for Candidate_Path in Candidate_Paths:
        if os.path.exists(Candidate_Path):
            return Candidate_Path

    # Return the primary bundled path even when it is currently missing
    return Candidate_Paths[0]



# Launch one application path in a way that works for both scripts and packaged applications
def Launch_Application_Path(Application_Path):

    Application_Path_Text = str(Application_Path)

    # Launch macOS .app bundles through the open command
    if sys.platform == 'darwin' and Application_Path_Text.lower().endswith('.app'):
        subprocess.Popen(['open', Application_Path_Text])
    # Launch Windows executables directly even when the current process was started from source
    elif sys.platform == 'win32' and Application_Path_Text.lower().endswith('.exe'):
        os.startfile(Application_Path_Text)
    # Launch Python scripts through the current interpreter
    elif Application_Path_Text.lower().endswith('.py'):
        subprocess.Popen([sys.executable, Application_Path_Text])
    # Otherwise launch the Python entry-point script directly
    else:
        subprocess.Popen([Application_Path_Text])



# Open another application
def Launch_An_Application(Script_Name, Executable_Name, Application_Id=None):

    Bundled_Application_Path = Get_Bundled_Application_Path(Script_Name, Executable_Name)

    # Prefer the application that matches the current runtime context.
    # If the current process is a source script, launch the sibling source script.
    # If the current process is a packaged executable or .app, launch the bundled sibling child.
    if os.path.exists(Bundled_Application_Path):
        Launch_Application_Path(Bundled_Application_Path)
        return

    Installed_Application_Launch_Path = None

    # Fall back to the installed-application registry entry when an application id was provided
    if Application_Id is not None:
        Installed_Application_Launch_Path = Get_Installed_Application_Launch_Path(Application_Id)

    # Launch the installed application when a usable registry entry exists
    if Installed_Application_Launch_Path:
        Launch_Application_Path(Installed_Application_Launch_Path)
        return

    Warning_Message(None, "Application Not Found", executable_name=Executable_Name)



# Return whether another application is available from the current bundle or local install registry
def Check_If_Application_Can_Be_Launched(Script_Name, Executable_Name, Application_Id=None):

    Bundled_Application_Path = Get_Bundled_Application_Path(Script_Name, Executable_Name)
    if os.path.exists(Bundled_Application_Path):
        return True

    if Application_Id is not None and Check_If_Installed_Application_Entry_Is_Usable(Application_Id):
        return True

    return False



# When the mouse leaves a menu bar automatically hide the menu bar
class AutoHideMenu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create an event filter to detect when the mouse leaves the menu bar
        self.installEventFilter(self)


    # When the mouse leaves the menu bar, hide the menu bar
    def eventFilter(self, Watched_Object, Event):

        # When the mouse leaves
        if Event.type() == QEvent.Leave:
            # Hide the menu bar
            self.hide()

        # Return the event result
        return super().eventFilter(Watched_Object, Event)



# Find the main window display
def Find_The_Main_Window(Current_Display):
    
    # Find the main window display
    while Current_Display is not None:
        # Check if the current display is inside the main window
        if isinstance(Current_Display, QMainWindow):
            return Current_Display
        # Keep looking for the main window
        Current_Display = Current_Display.parent()

    return None



# Create the main menu bar
class MainMenuBar(QMenuBar):
    def __init__(self, Parent=None):
        super().__init__(Parent)
        self.Parent = Parent
        Show_EoSAlign_Only_Actions = self.Is_EoSAlign_Window()

        # Create the menu bar options

        # File 
        File_Menu = AutoHideMenu("File", self)
        # Add options to the file menu
        if Show_EoSAlign_Only_Actions:
                # Open
            Open_Action = File_Menu.addAction("Open")
                    # When open is selected the user can open a data file
            Open_Action.triggered.connect(self.Open_Data_File)
                # Save Data
            Save_Action = File_Menu.addAction("Save Data")
                    # When save is selected the user can save the current data
            Save_Action.triggered.connect(self.Save_Data)
            # Add a seperator
            File_Menu.addSeparator()
            # Enter Calibration
        Enter_Calibration_Action = File_Menu.addAction("Enter Calibration")
                # When enter calibration is selected the enter calibration dialog will open
        Enter_Calibration_Action.triggered.connect(self.Open_Enter_Calibration)
            # View Calibration
        View_Calibration_Action = File_Menu.addAction("View Calibration")
                # When view calibration is selected the calibration viewer will open with no selection
        View_Calibration_Action.triggered.connect(self.Open_View_Calibration)
        # Add a seperator
        File_Menu.addSeparator()
            # Settings
        Settings_Action = File_Menu.addAction("Settings")
                # When settings is selected the settings dialog will open to the general settings page
        Settings_Action.triggered.connect(self.Open_Settings_General)
        # Add a seperator
        File_Menu.addSeparator()
            # Exit
        Exit_Action = File_Menu.addAction("Exit")
                # When exit is selected the application will close
        Exit_Action.triggered.connect(QApplication.quit)
        # Add the file menu to the menu bar
        self.addMenu(File_Menu)

        if Show_EoSAlign_Only_Actions:
            # Plots
            Plots_Menu = AutoHideMenu("Plots", self)
            # Add options to the plots menu
                # Plot settings
            Plots_Action = Plots_Menu.addAction("Plot Settings")
                    # When plot settings is selected the settings dialog will open to the plot settings page
            Plots_Action.triggered.connect(self.Open_Settings_Plots)
            # Add the plots menu to the menu bar
            self.addMenu(Plots_Menu)

        # Applications
        Applications_Menu = AutoHideMenu("Applications", self)

        # Only show applications that are actually launchable in the current install context
        Available_Applications = []
        if Check_If_Application_Can_Be_Launched('EoSAlign.py', 'EoSAlign', Application_Id="EoSAlign"):
            Available_Applications.append(("EoSAlign", self.Open_EoSAlign))
        if Check_If_Application_Can_Be_Launched('EoSHolo.py', 'EoSHolo', Application_Id="EoSHolo"):
            Available_Applications.append(("EoSHolo", self.Open_EoSHolo))
        if EoSFitting_Menu_Enabled and Check_If_Application_Can_Be_Launched('EoSFitting.py', 'EoSFitting', Application_Id="EoSFitting"):
            Available_Applications.append(("EoSFitting", self.Open_EoSFitting))

        for Application_Name, Open_Handler in Available_Applications:
            Application_Action = Applications_Menu.addAction(Application_Name)
            Application_Action.triggered.connect(Open_Handler)

        # Add the applications menu to the menu bar
        self.addMenu(Applications_Menu)

        # Help
        Help_Menu = AutoHideMenu("Help", self)
        # Add options to the help menu
            # Documentation
        Documentation_Action = Help_Menu.addAction("Documentation")
                # When documentation is selected the settings dialog will open to the documentation page
        Documentation_Action.triggered.connect(self.Open_Documentation)
            # Work Flow
        Workflow_Action = Help_Menu.addAction("Work Flow")
                # When work flow is selected the settings dialog will open to the work flow section of the documentation page
        Workflow_Action.triggered.connect(self.Open_Documentation_Work_Flow)
            # Example Data File
        Example_Data_Action = Help_Menu.addAction("Example Data File")
                # When example data file is selected the settings dialog will open to the example data file section of the documentation page
        Example_Data_Action.triggered.connect(self.Open_Documentation_Example_Data)
            # Included Calibrations
        Included_Calibrations_Action = Help_Menu.addAction("Included Calibrations")
                # When included calibrations is selected the settings dialog will open to the included calibrations section of the documentation page
        Included_Calibrations_Action.triggered.connect(self.Open_Documentation_Included_Calibrations)
        # Add a seperator
        Help_Menu.addSeparator()
            # Check for Version Updates
        Check_For_Version_Updates_Action = Help_Menu.addAction("Check for Version Updates")
                # When check for version updates is selected the app checks GitHub for a newer release
        Check_For_Version_Updates_Action.triggered.connect(self.Check_For_Version_Updates)
            # Check for Calibration Updates
        Check_For_Calibration_Updates_Action = Help_Menu.addAction("Check for Calibration Updates")
                # When check for calibration updates is selected the app checks for new or changed calibration files
        Check_For_Calibration_Updates_Action.triggered.connect(self.Check_For_Calibration_File_Updates)
        # Add a seperator
        Help_Menu.addSeparator()
            # About
        About_Action = Help_Menu.addAction("About")
                # When about is selected the settings dialog will open to the about section of the about page
        About_Action.triggered.connect(self.Open_About)
            # Authors
        Authors_Action = Help_Menu.addAction("Authors")
                # When authors is selected the settings dialog will open to the authors section of the about page
        Authors_Action.triggered.connect(self.Open_About_Authors)
            # Contact
        Contact_Action = Help_Menu.addAction("Contact")
                # When contact is selected the settings dialog will open to the contact section of the about page
        Contact_Action.triggered.connect(self.Open_About_Contact)
            # License
        License_Action = Help_Menu.addAction("License")
                # When license is selected the settings dialog will open to the license section of the about page
        License_Action.triggered.connect(self.Open_About_License)
        # Add the help menu to the menu bar
        self.addMenu(Help_Menu)


    # Open the settings window
    def Is_EoSAlign_Window(self):

        Main_Window = Find_The_Main_Window(self.parent())
        if Main_Window is None:
            return False

        Window_Title = (Main_Window.windowTitle() or "").strip()
        return Window_Title == "EoSAlign" or Window_Title.startswith("EoSAlign - ")


    # Open the settings window
    def Get_Settings_Dialog(self):

        Main_Window = Find_The_Main_Window(self.parent())
        if Main_Window is None:
            return None
        if hasattr(Main_Window, "Get_Settings_Dialog"):
            return Main_Window.Get_Settings_Dialog()
        return getattr(Main_Window, "Settings", None)


    # Open a data file
    def Open_Data_File(self):

        Parent = self.parent()
        if Parent is not None and hasattr(Parent, "handle_open_file"):
            Parent.handle_open_file()
        else:
            Warning_Message(self, "Menu Action Not Available", action="Open")


    # Save the current data
    def Save_Data(self):

        Parent = self.parent()
        if Parent is not None and hasattr(Parent, "handle_save_data"):
            Parent.handle_save_data()
        else:
            Warning_Message(self, "Menu Action Not Available", action="Save Data")


    # Open the enter calibration dialog
    def Open_Enter_Calibration(self):

        from View_Edit_And_Save_Calibration_Files_In_A_New_Window import Enter_Calibration_Window
        # Reuse the existing dialog if it is already open.
        existing = getattr(self, 'Enter_Calibration_Dialog', None)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return
        with Guard_Unwanted_Window_Shows() as Guard:
            dlg = Enter_Calibration_Window(Parent=None)
            if Guard is not None:
                Guard.allow(dlg)
            self.Enter_Calibration_Dialog = dlg  # strong reference keeps dialog alive
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()


    # Open the view calibration dialog
    def Open_View_Calibration(self):

        from View_Edit_And_Save_Calibration_Files_In_A_New_Window import View_Calibration_Window
        # Reuse the existing dialog if it is already open.
        existing = getattr(self, 'View_Calibration_Dialog', None)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return
        with Guard_Unwanted_Window_Shows() as Guard:
            dlg = View_Calibration_Window(Parent=None)
            if Guard is not None:
                Guard.allow(dlg)
            self.View_Calibration_Dialog = dlg  # strong reference keeps dialog alive
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()


    # Open the general settings page
    def Open_Settings_General(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.Select_A_Settings_Page("General")
            Dialog.show()
            Dialog.raise_()
            Dialog.activateWindow()


    # Open the plot settings page
    def Open_Settings_Plots(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.Select_A_Settings_Page("Plots")
            Dialog.show()
            Dialog.raise_()
            Dialog.activateWindow()


    # Open the EoSAlign Application
    def Open_EoSAlign(self):

        Launch_An_Application('EoSAlign.py', 'EoSAlign', Application_Id="EoSAlign")


    # Open the EoSHolo Application
    def Open_EoSHolo(self):

        Launch_An_Application('EoSHolo.py', 'EoSHolo', Application_Id="EoSHolo")


    # Open the EoSFitting Application
    def Open_EoSFitting(self):

        Launch_An_Application('EoSFitting.py', 'EoSFitting', Application_Id="EoSFitting")


    # Manually check for a newer version of the currently running application
    def Check_For_Version_Updates(self):

        from Check_For_Updates import Check_For_Updates_Manually
        from Version import Get_Current_Running_Application_Id
        Check_For_Updates_Manually(Find_The_Main_Window(self.parent()), Get_Current_Running_Application_Id())


    # Manually check for new or changed calibration files
    def Check_For_Calibration_File_Updates(self):

        from Check_For_Calibration_Updates import Check_For_Calibration_Updates_Manually
        Check_For_Calibration_Updates_Manually(Find_The_Main_Window(self.parent()))


    # Open the documentation page
    def Open_Documentation(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.Scroll_Documentation_To("EoSAlign")


    # Open the work flow section of the documentation page
    def Open_Documentation_Work_Flow(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.Scroll_Documentation_To("work_flow")


    # Open the example data file section of the documentation page
    def Open_Documentation_Example_Data(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.Scroll_Documentation_To("example_data_file")



    # Open the included calibrations section of the documentation page
    def Open_Documentation_Included_Calibrations(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.Scroll_Documentation_To("included_calibrations")



    # Open the about page
    def Open_About(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.Scroll_About_To("about")


    # Open the authors section of the about page
    def Open_About_Authors(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.activateWindow()
            Dialog.Scroll_About_To("authors")



    # Open the contact section of the about page
    def Open_About_Contact(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.activateWindow()
            Dialog.Scroll_About_To("contact")


    # Open the license section of the about page
    def Open_About_License(self):

        Dialog = self.Get_Settings_Dialog()
        if Dialog:
            Dialog.show()
            Dialog.raise_()
            Dialog.activateWindow()
            Dialog.Scroll_About_To("license")




