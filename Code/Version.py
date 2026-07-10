# Load libraries
    # Load standard libraries
import copy
import os
import sys





# Store the single canonical version for the whole suite -- EoSApplications and
# every app it bundles (EoSAlign, EoSHolo, EoSFitting) release in lockstep, so this
# is the one line a release bumps. Every other file that needs the version
# (pyproject.toml, the Windows installer, README badges, ...) is generated/synced
# from this value by Installer_Files/Generate_Pyproject_Toml.py and
# Installer_Files/Sync_App_Version.py -- never hand-edit a version number elsewhere.
Current_Suite_Version = "1.0.1"

# Store the version and repository information for each application
Applications = {
    "EoSApplications": {
        "App_Id": "EoSApplications",
        "Display_Name": "EoS Applications",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": {
            "win32": "EoSApplications__Windows__x86_64.exe",
            "darwin": "EoSApplications_Mac.dmg",
            "linux": "EoSApplications_Linux.AppImage",
        },
    },

    "EoSAlign": {
        "App_Id": "EoSAlign",
        "Display_Name": "EoS Align",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": {
            "win32": "EoSApplications__Windows__x86_64.exe",
            "darwin": "EoSApplications_Mac.dmg",
            "linux": "EoSApplications_Linux.AppImage",
        },
    },
    "EoSHolo": {
        "App_Id": "EoSHolo",
        "Display_Name": "EoS Holo",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": {
            "win32": "EoSApplications__Windows__x86_64.exe",
            "darwin": "EoSApplications_Mac.dmg",
            "linux": "EoSApplications_Linux.AppImage",
        },
    },
    "EoSFitting": {
        "App_Id": "EoSFitting",
        "Display_Name": "EoS Fitting",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": {
            "win32": "EoSApplications__Windows__x86_64.exe",
            "darwin": "EoSApplications_Mac.dmg",
            "linux": "EoSApplications_Linux.AppImage",
        },
    },
}

# Store the child-application versions bundled with the wrapper application
EoSApplications__Bundled_Applications = {
    "EoSAlign": Current_Suite_Version,
    "EoSHolo": Current_Suite_Version,
    "EoSFitting": Current_Suite_Version,
}

# EoSFitting is not ready for users to launch yet; keep it out of the Applications
# menu and the EoSApplications launcher cards until this is switched back on
EoSFitting_Menu_Enabled = False


# Find the platform key used by the current operating system
def Get_Current_Platform_Key():

    # If this is a Linux system normalize the key to plain "linux"
    if sys.platform.startswith("linux"):
        Current_Platform_Key = "linux"
    # Otherwise use the Python platform string directly
    else:
        Current_Platform_Key = sys.platform

    # Return the normalized platform key
    return Current_Platform_Key



# Find the version and repository information for a specific application
def Get_Application_Information(Application_Id):

    # Check that the requested application exists in the shared version table
    if Application_Id not in Applications:
        raise ValueError(f"Unknown application id: {Application_Id}")

    Application_Information = copy.deepcopy(Applications[Application_Id])

    # Return a copy so callers do not accidentally modify the shared metadata
    return Application_Information



# Find the installer or packaged asset name for one application on one platform
def Get_Platform_Asset_Name(Application_Id, Platform_Key=None):

    # Use the current operating system if no platform key was provided
    if Platform_Key is None:
        Platform_Key = Get_Current_Platform_Key()

    Application_Information = Get_Application_Information(Application_Id)
    Platform_Assets = Application_Information.get("Platform_Assets", {})
    Asset_Name = Platform_Assets.get(Platform_Key)

    # Return the installer or packaged asset name for the requested platform
    return Asset_Name



# Find the child-application versions that are bundled with the wrapper release
def Get_EoSApplications__Bundled_Applications():

    Bundled_Applications = copy.deepcopy(EoSApplications__Bundled_Applications)

    # Return a copy of the wrapper bundle metadata
    return Bundled_Applications



# Find the application ids that are managed by the wrapper application
def Get_EoSApplications__Child_Application_Ids():

    Child_Application_Ids = tuple(Get_EoSApplications__Bundled_Applications().keys())

    # Return the child-application ids managed by the wrapper
    return Child_Application_Ids



# Find which application is currently running
    # Shared widgets (Settings, Plot_Window, ...) are compiled into every EoS
    # executable but are not told which one they were opened from, so this
    # infers it from the running entry-point's file name instead
        # A frozen build's sys.argv[0] is the executable path (e.g. ".../EoSHolo.exe")
        # A plain Python run's sys.argv[0] is the launched script path (e.g. ".../EoSHolo.py")
        # A pip console-script's sys.argv[0] is the generated wrapper's path, using the
        # all-lowercase command name (e.g. ".../Scripts/eosholo.exe" or ".../bin/eosholo"),
        # so the comparison below must be case-insensitive to still match "EoSHolo"
def Get_Current_Running_Application_Id():

    Entry_Point_Base_Name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    # Check every known application id for a matching entry-point file name
    for Known_Application_Id in Applications:
        if Entry_Point_Base_Name.lower() == Known_Application_Id.lower():
            # Return the application id that matches the running entry point
            return Known_Application_Id

    # Fall back to the wrapper application id when the entry point could not be matched
        # This keeps shared widgets working even when launched from an unrecognized entry point
    return "EoSApplications"


