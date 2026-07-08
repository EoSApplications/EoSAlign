# Load libraries
    # Load standard libraries
import json
import os
import sys
from datetime import datetime, timezone
    # Load local libraries
from Version import Get_Application_Information
from Session_Paths import ensure_hidden_directory, get_user_data_root, hide_path_from_file_explorer





# Store the registry file name used to track installed applications
Installed_Applications_Registry_File_Name = "Installed_Applications.json"
Register_Installed_Application_Command = "--register-installed-application"


# Find the folder where installed-application registry information should be stored
def Get_Installed_Applications_Registry_Directory(Create: bool = True):

    Registry_Directory = get_user_data_root() / ".registry"

    # Create the registry directory when requested
    if Create:
        Registry_Directory = ensure_hidden_directory(Registry_Directory)

    # Return the installed-application registry directory
    return Registry_Directory



# Find the installed-application registry file path
def Get_Installed_Applications_Registry_File_Path(Create: bool = True):

    Registry_Directory = Get_Installed_Applications_Registry_Directory(Create=Create)
    Registry_File_Path = Registry_Directory / Installed_Applications_Registry_File_Name

    # Return the installed-application registry file path
    return Registry_File_Path



# Load the installed-application registry from disk
def Load_Installed_Applications_Registry():

    Registry_File_Path = Get_Installed_Applications_Registry_File_Path(Create=False)

    # Return an empty registry when the file does not exist yet
    if not Registry_File_Path.exists():
        return {}

    try:
        with open(Registry_File_Path, "r", encoding="utf-8") as Registry_File:
            Registry_Information = json.load(Registry_File)

        # Return the registry when it is a dictionary
        if isinstance(Registry_Information, dict):
            return Registry_Information
    except Exception:
        pass

    # Return an empty registry when the file cannot be read safely
    return {}



# Save the installed-application registry to disk
def Save_Installed_Applications_Registry(Registry_Information):

    Registry_File_Path = Get_Installed_Applications_Registry_File_Path(Create=True)
    Temporary_File_Path = Registry_File_Path.with_suffix(".tmp")

    with open(Temporary_File_Path, "w", encoding="utf-8") as Temporary_File:
        json.dump(Registry_Information, Temporary_File, indent=2)

    os.replace(Temporary_File_Path, Registry_File_Path)
    hide_path_from_file_explorer(Registry_File_Path)



# Find the launch path for the currently running application
def Get_Current_Application_Launch_Path():

    # Use the executable path when the application is running from a packaged build
    if getattr(sys, "frozen", False):
        Launch_Path = os.path.abspath(sys.executable)
    # Otherwise use the Python entry-point path for the current script run
    else:
        Launch_Path = os.path.abspath(sys.argv[0])

    # Return the current application launch path
    return Launch_Path



# Build one registry entry for the currently running application
def Build_Installed_Application_Entry(Application_Id: str, Installed_By: str = "Direct"):

    Application_Information = Get_Application_Information(Application_Id)
    Launch_Path = Get_Current_Application_Launch_Path()
    Install_Directory = os.path.dirname(Launch_Path)
    Updated_At = datetime.now(timezone.utc).isoformat()

    Registry_Entry = {
        "App_Id": Application_Information.get("App_Id", Application_Id),
        "Display_Name": Application_Information.get("Display_Name", Application_Id),
        "Installed_Version": Application_Information.get("Version", ""),
        "Is_Prerelease": bool(Application_Information.get("Is_Prerelease", False)),
        "Github_Owner": Application_Information.get("Github_Owner", ""),
        "Github_Repository": Application_Information.get("Github_Repository", ""),
        "Install_Directory": Install_Directory,
        "Launch_Path": Launch_Path,
        "Installed_By": Installed_By,
        "Last_Validated_At__UTC": Updated_At,
    }

    # Return the registry entry for the current application
    return Registry_Entry



# Build one registry entry for an explicit launch path
def Build_Installed_Application_Entry_For_Launch_Path(Application_Id: str, Launch_Path: str, Installed_By: str = "Direct"):

    Application_Information = Get_Application_Information(Application_Id)
    Resolved_Launch_Path = os.path.abspath(str(Launch_Path or "").strip())
    Install_Directory = os.path.dirname(Resolved_Launch_Path)
    Updated_At = datetime.now(timezone.utc).isoformat()

    Registry_Entry = {
        "App_Id": Application_Information.get("App_Id", Application_Id),
        "Display_Name": Application_Information.get("Display_Name", Application_Id),
        "Installed_Version": Application_Information.get("Version", ""),
        "Is_Prerelease": bool(Application_Information.get("Is_Prerelease", False)),
        "Github_Owner": Application_Information.get("Github_Owner", ""),
        "Github_Repository": Application_Information.get("Github_Repository", ""),
        "Install_Directory": Install_Directory,
        "Launch_Path": Resolved_Launch_Path,
        "Installed_By": Installed_By,
        "Last_Validated_At__UTC": Updated_At,
    }

    # Return the registry entry for the requested launch path
    return Registry_Entry



# Add or update one installed-application registry entry
def Register_Installed_Application(Application_Id: str, Installed_By: str = "Direct"):

    Registry_Information = Load_Installed_Applications_Registry()
    Registry_Entry = Build_Installed_Application_Entry(Application_Id, Installed_By=Installed_By)
    Registry_Information[Application_Id] = Registry_Entry
    Save_Installed_Applications_Registry(Registry_Information)

    # Return the updated registry entry
    return Registry_Entry



# Add or update one installed-application registry entry for an explicit launch path
def Register_Installed_Application_For_Launch_Path(Application_Id: str, Launch_Path: str, Installed_By: str = "Direct"):

    Registry_Information = Load_Installed_Applications_Registry()
    Registry_Entry = Build_Installed_Application_Entry_For_Launch_Path(Application_Id, Launch_Path, Installed_By=Installed_By)
    Registry_Information[Application_Id] = Registry_Entry
    Save_Installed_Applications_Registry(Registry_Information)

    # Return the updated registry entry for the explicit launch path
    return Registry_Entry



# Find one installed-application registry entry
def Get_Installed_Application_Entry(Application_Id: str):

    Registry_Information = Load_Installed_Applications_Registry()
    Registry_Entry = Registry_Information.get(Application_Id)

    # Return the installed-application registry entry if it exists
    return Registry_Entry



# Check if a registry entry points to a launch path that still exists on disk
def Check_If_Installed_Application_Entry_Is_Usable(Application_Id: str):

    Registry_Entry = Get_Installed_Application_Entry(Application_Id)

    # Return False when there is no installed-application registry entry
    if not isinstance(Registry_Entry, dict):
        return False

    Launch_Path = str(Registry_Entry.get("Launch_Path", "") or "").strip()

    # Return False when the stored launch path is empty
    if not Launch_Path:
        return False

    # Return whether the stored launch path still exists
    return os.path.exists(Launch_Path)



# Find the stored launch path for one installed application
def Get_Installed_Application_Launch_Path(Application_Id: str):

    Registry_Entry = Get_Installed_Application_Entry(Application_Id)

    # Return no path when there is no installed-application registry entry
    if not isinstance(Registry_Entry, dict):
        return None

    Launch_Path = str(Registry_Entry.get("Launch_Path", "") or "").strip()

    # Return no path when the stored launch path is empty or missing on disk
    if not Launch_Path or not os.path.exists(Launch_Path):
        return None

    # Return the stored launch path for this installed application
    return Launch_Path



# Check if the current command line is requesting registry-only application registration
def Check_If_Register_Installed_Application_Was_Requested():

    Register_Installed_Application_Was_Requested = Register_Installed_Application_Command in sys.argv[1:]

    # Return whether the current process was started in registry-only mode
    return Register_Installed_Application_Was_Requested



# Register the application and exit immediately when registry-only mode was requested
def Register_Installed_Application_And_Exit_If_Requested(Application_Id: str, Installed_By: str = "Installer"):

    # Continue normal startup when registry-only mode was not requested
    if not Check_If_Register_Installed_Application_Was_Requested():
        return False

    Register_Installed_Application(Application_Id, Installed_By=Installed_By)

    # Exit immediately after writing the registry entry
    raise SystemExit(0)


