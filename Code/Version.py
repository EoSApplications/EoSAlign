# Load libraries
    # Load standard libraries
import copy
import os
import platform
import sys





# Store the single canonical version for the whole suite -- EoSApplications and
# every app it bundles (EoSAlign, EoSHolo, EoSFitting) release in lockstep, so this
# is the one line a release bumps. Every other file that needs the version
# (pyproject.toml, the Windows installer, README badges, ...) is generated/synced
# from this value by Installer_Files/Generate_Pyproject_Toml.py and
# Installer_Files/Sync_App_Version.py -- never hand-edit a version number elsewhere.
Current_Suite_Version = "1.1.0"

# Status values for one platform+architecture's installer asset (used inside
# Default_Platform_Assets below) -- distinguishes "never built" from "used to be built, no
# longer is," since the latter is what should push an installed user toward pip instead of
# a normal update notification (see Is_Current_Platform_Architecture_Retired())
Asset_Status_Supported = "Supported"       # currently built and distributed for this release
Asset_Status_Unsupported = "Unsupported"   # never built for this platform+architecture (not yet, or not planned)
Asset_Status_Retired = "Retired"           # used to be built; no longer produced as of this version
# Example of what a freshly retired entry looks like (Last_Supported_Version is hand-set at the
# moment an architecture flips to Retired -- it's never computed automatically, since only a
# person doing the retiring knows which version was the last one actually built for it):
#   "x86_64": Platform_Asset(Asset_Status_Retired, Last_Supported_Version="1.2.0"),


# Build one platform+architecture entry for Default_Platform_Assets below
def Platform_Asset(Status, Filename=None, Last_Supported_Version=None):
    return {"Status": Status, "Filename": Filename, "Last_Supported_Version": Last_Supported_Version}


# Every distributable app currently ships from the same suite-wide installer/DMG/AppImage
# builds, so every entry in Applications below points at this one shared table instead of
# four separate copies of it (Get_Application_Information() deep-copies before handing this
# out, so nothing here is ever mutated in place -- safe to share the reference).
# Update this table -- not the individual app entries -- whenever a platform+architecture
# combination starts, stops, or resumes being built. Filenames must match exactly what each
# platform's build scripts actually produce:
#   Windows_Step_2_Build_Installer.bat -> EoSApplications__Windows__<arch>.exe
#   Mac_Step_2_Build_Dmg.sh            -> EoSApplications__Mac__<arch>.dmg
#   Linux_Step_2_Build_Appimage.sh     -> EoSApplications__Linux__<arch>.AppImage
# This lists every platform+architecture combination PySide6 itself ships a wheel for today
# (win_amd64, win_arm64, manylinux_2_28_x86_64, manylinux_2_39_aarch64, macosx_12_0_universal2
# covering both Mac architectures) -- that is the real ceiling of what could ever be built here
# at all, so it doubles as the complete, ongoing tracking list. Unsupported entries below are
# platforms PySide6 can build for but this pipeline doesn't build/ship yet, not platforms that
# are impossible. See Developer_Documentation/Platform_Architecture_Support.md for the full
# explanation of this table and how the update checker uses it.
Default_Platform_Assets = {
    # Windows has no separate "arm64" entry here, unlike Mac/Linux -- the .iss already sets
    # ArchitecturesAllowed=x64compatible / ArchitecturesInstallIn64BitMode=x64compatible, which
    # Inno Setup documents as matching BOTH real x64 Windows AND Windows 11 on ARM64 (via its
    # built-in x64 emulation layer). So the one x86_64 installer already fully covers ARM64
    # Windows machines today; there is no distinct "Windows ARM64" build to track as
    # Supported/Unsupported/Retired. Get_Current_Architecture_Key() normalizes a native ARM64
    # host reported by platform.machine() down to "x86_64" for exactly this reason -- see its
    # docstring-style comment below for why that detection needs to happen at all.
    "win32": {
        "x86_64": Platform_Asset(Asset_Status_Supported, "EoSApplications__Windows__x86_64.exe"),
    },
    "darwin": {
        "arm64": Platform_Asset(Asset_Status_Supported, "EoSApplications__Mac__arm64.dmg"),
        "x86_64": Platform_Asset(Asset_Status_Supported, "EoSApplications__Mac__x86_64.dmg"),
    },
    "linux": {
        "x86_64": Platform_Asset(Asset_Status_Supported, "EoSApplications__Linux__x86_64.AppImage"),
        # No arm64/aarch64 Linux build exists yet -- the GitHub Actions "linux" job only
        # covers ubuntu-latest (x86_64). Flip to Asset_Status_Supported once one is added.
        "aarch64": Platform_Asset(Asset_Status_Unsupported),
    },
}

# Store the version and repository information for each application
Applications = {
    "EoSApplications": {
        "App_Id": "EoSApplications",
        "Display_Name": "EoS Applications",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": Default_Platform_Assets,
    },

    "EoSAlign": {
        "App_Id": "EoSAlign",
        "Display_Name": "EoS Align",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": Default_Platform_Assets,
    },
    "EoSHolo": {
        "App_Id": "EoSHolo",
        "Display_Name": "EoS Holo",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": Default_Platform_Assets,
    },
    "EoSFitting": {
        "App_Id": "EoSFitting",
        "Display_Name": "EoS Fitting",
        "Version": Current_Suite_Version,
        "Is_Prerelease": False,
        "Github_Owner": "EoSApplications",
        "Github_Repository": "EoSAlign",
        "Platform_Assets": Default_Platform_Assets,
    },
}

# Store the child-application versions bundled with the wrapper application
EoSApplications__Bundled_Applications = {
    "EoSAlign": Current_Suite_Version,
    "EoSHolo": Current_Suite_Version,
    "EoSFitting": Current_Suite_Version,
}

# Set to False to hide EoSFitting from the Applications menu and the EoSApplications
# launcher cards (e.g. to pull it from a release without removing its files)
EoSFitting_Menu_Enabled = True


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



# Find the architecture key for the machine currently running this process, normalized to
# match the naming each platform's build scripts already use for their installer filenames.
    # Windows' platform.machine() reports "AMD64" for 64-bit Intel/AMD, but the installer
    # filename/PE-header detection in Windows_Step_2_Build_Installer.bat calls it "x86_64" --
    # normalize here so the two actually match.
    # It also reports "ARM64" (not "AMD64") when THIS x64 process is itself running under
    # emulation on a native ARM64 Windows machine -- platform.machine() checks the
    # PROCESSOR_ARCHITEW6432 environment variable first, which Windows sets to the true native
    # host architecture specifically for a WOW64/emulated process, only falling back to
    # PROCESSOR_ARCHITECTURE (the emulated process's own "AMD64") when that isn't set. Since
    # the one Windows installer is built with x64compatible (see Default_Platform_Assets'
    # comment above) and already runs on ARM64 Windows via that same emulation, an ARM64 host
    # here is exactly as supported as a native x64 one -- both normalize to "x86_64" so the
    # lookup in Default_Platform_Assets finds the one Supported Windows entry either way,
    # instead of an ARM64 user being incorrectly told their (perfectly working) architecture
    # is unsupported.
    # Mac (-> "arm64"/"x86_64", same as Apple's own naming and lipo -archs) and Linux (->
    # "x86_64"/"aarch64", same as `uname -m`) genuinely ship separate native builds per
    # architecture, so their values are used as-is with no such folding.
def Get_Current_Architecture_Key():

    Machine_Name = platform.machine()

    if sys.platform == "win32" and Machine_Name.upper() in ("AMD64", "X86_64", "ARM64"):
        return "x86_64"

    # Return the architecture key as reported for every other platform/architecture
    return Machine_Name



# Find the installer/DMG/AppImage asset status (Supported/Unsupported/Retired) and filename
# for one application on one platform+architecture
def Get_Platform_Asset_Info(Application_Id, Platform_Key=None, Architecture_Key=None):

    # Use the current operating system/architecture if none was provided
    if Platform_Key is None:
        Platform_Key = Get_Current_Platform_Key()
    if Architecture_Key is None:
        Architecture_Key = Get_Current_Architecture_Key()

    Application_Information = Get_Application_Information(Application_Id)
    Platform_Assets = Application_Information.get("Platform_Assets", {})
    Architecture_Assets = Platform_Assets.get(Platform_Key, {})
    Asset_Info = Architecture_Assets.get(Architecture_Key)

    # Any platform+architecture combination not listed at all (e.g. a machine type nobody
    # has added yet) is implicitly unsupported rather than an error
    if Asset_Info is None:
        return Platform_Asset(Asset_Status_Unsupported)

    # Return a copy of the found asset info for the requested platform+architecture
    return dict(Asset_Info)



# Find the installer or packaged asset name for one application on one platform+architecture
def Get_Platform_Asset_Name(Application_Id, Platform_Key=None, Architecture_Key=None):

    # Return the installer or packaged asset filename for the requested platform+architecture
    return Get_Platform_Asset_Info(Application_Id, Platform_Key, Architecture_Key).get("Filename")



# Check whether the currently running platform+architecture has been retired -- i.e. it used
# to have a real installer/DMG/AppImage built for it, but the current release lineup no
# longer produces one. Callers use this to steer a user stuck on a retired architecture
# toward `pip install` instead of a normal "download the new installer" update message.
def Is_Current_Platform_Architecture_Retired(Application_Id):

    Asset_Info = Get_Platform_Asset_Info(Application_Id)

    # Return whether the current platform/architecture's asset status is retired
    return Asset_Info.get("Status") == Asset_Status_Retired



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


