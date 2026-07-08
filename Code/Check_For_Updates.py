# Load libraries
    # Load standard libraries
import json
import os
import re
import sys
import urllib.request
    # Load third party libraries
from PySide6.QtCore import QThread, Signal, QSettings, QTimer
    # Load local libraries
from Version import Get_Application_Information
from Installed_Applications_Registry import Register_Installed_Application
from Message_Manager import Warning_Message, Success_Message





# Store the user agent used for GitHub API requests
User_Agent = "EoSAlign-update-check"

# Store the fallback version used when no version is configured
Default_Current_Version = "0.0.0"

# Store the QSettings key that remembers whether update notifications are enabled
    # Stored per application id under the "EoSApplications" organization, matching the pattern
    # already used by Mac_Terminal_Commands.py for other once-per-app preferences
Show_Update_Notifications_Setting_Key = "Show_Update_Notifications"


# Detect if the application was installed via pip rather than a bundled installer
def Is_Pip_Install() -> bool:
    if getattr(sys, 'frozen', False):
        return False
    try:
        import importlib.metadata
        importlib.metadata.version("eosapplications")
        return True
    except Exception:
        return False


# Convert an application id into the matching environment-variable prefix
def Get_Application_Environment_Prefix(Application_Id: str) -> str:

    Environment_Prefix = re.sub(r"[^A-Za-z0-9]+", "_", str(Application_Id or "").strip()).upper()

    # Return the environment-variable prefix for this application
    return Environment_Prefix



# Find the configured application information, applying environment overrides when present
def Get_Application_Update_Information(Application_Id: str) -> dict:

    Application_Information = Get_Application_Information(Application_Id)
    Environment_Prefix = Get_Application_Environment_Prefix(Application_Id)

    Configured_Current_Version = os.environ.get(f"{Environment_Prefix}_CURRENT_VERSION", "").strip()
    if Configured_Current_Version:
        Application_Information["Version"] = Configured_Current_Version

    Configured_Github_Owner = os.environ.get(f"{Environment_Prefix}_GITHUB_OWNER", "").strip()
    if Configured_Github_Owner:
        Application_Information["Github_Owner"] = Configured_Github_Owner

    Configured_Github_Repository = os.environ.get(f"{Environment_Prefix}_GITHUB_REPOSITORY", "").strip()
    if Configured_Github_Repository:
        Application_Information["Github_Repository"] = Configured_Github_Repository

    # Return the application metadata with any environment overrides applied
    return Application_Information



# Find the current version for one application
def Get_Current_Version(Application_Id: str) -> str:

    Application_Information = Get_Application_Update_Information(Application_Id)
    Current_Version = str(Application_Information.get("Version", Default_Current_Version) or Default_Current_Version).strip()

    # Return the configured current version for this application
    return Current_Version



# Find the GitHub latest-release API endpoint for one application
def Get_Github_Release_Api_Url(Application_Id: str) -> str | None:

    Application_Information = Get_Application_Update_Information(Application_Id)
    Github_Owner = str(Application_Information.get("Github_Owner", "") or "").strip()
    Github_Repository = str(Application_Information.get("Github_Repository", "") or "").strip()

    # Return no URL when the repository location is not configured
    if not Github_Owner or not Github_Repository:
        return None

    Github_Api_Url = f"https://api.github.com/repos/{Github_Owner}/{Github_Repository}/releases/latest"

    # Return the latest-release API endpoint for the configured repository
    return Github_Api_Url



# Convert a version string into a numeric tuple for comparisons
def Parse_Version(Version_Text: str) -> tuple:

    Version_Core = str(Version_Text or "").strip().lstrip("vV").split("-", 1)[0]
    Version_Parts = re.findall(r"\d+", Version_Core)
    Parsed_Version = tuple(int(Part) for Part in Version_Parts)

    # Return the numeric version tuple used for comparisons
    return Parsed_Version or (0,)



# Check whether update notifications are currently turned on for one application
def Are_Update_Notifications_Enabled(Application_Id: str) -> bool:

    Notification_Settings = QSettings("EoSApplications", Application_Id)
    Are_Enabled = Notification_Settings.value(Show_Update_Notifications_Setting_Key, True, type=bool)

    # Return whether the user still wants to see update notifications for this application
    return Are_Enabled



# Turn update notifications on or off for one application
    # Used both by the "do not show this message again" checkbox on the update dialog
    # and by the matching toggle on the General settings page
def Set_Update_Notifications_Enabled(Application_Id: str, Are_Enabled: bool):

    Notification_Settings = QSettings("EoSApplications", Application_Id)
    Notification_Settings.setValue(Show_Update_Notifications_Setting_Key, bool(Are_Enabled))



# Check GitHub in the background for a newer version of one application
class Version_Check_Worker(QThread):
    update_available = Signal(str, str)  # (latest_version, release_page_url)
    no_update_available = Signal()
    check_failed = Signal(str)

    def __init__(self, Application_Id: str):
        super().__init__()
        self.Application_Id = Application_Id

    def run(self):
        Github_Api_Url = Get_Github_Release_Api_Url(self.Application_Id)
        Current_Version = Get_Current_Version(self.Application_Id)

        # Skip update checks when no repository has been configured
        if not Github_Api_Url:
            self.check_failed.emit("No update location is configured for this application.")
            return

        try:
            req = urllib.request.Request(Github_Api_Url, headers={"User-Agent": User_Agent})
            with urllib.request.urlopen(req, timeout=8) as resp:
                Data = json.loads(resp.read().decode())

            Latest_Tag = Data.get("tag_name", "")

            # Stop if the release payload does not include a tag
            if not Latest_Tag:
                self.check_failed.emit("GitHub did not report a release for this application.")
                return

            # Stop when the installed version is already current or newer
            if Parse_Version(Latest_Tag) <= Parse_Version(Current_Version):
                self.no_update_available.emit()
                return

            # Use the GitHub release page itself as the "download it here" link
                # It lists every platform's installer asset alongside the release notes, so the
                # same link works whether the app is running from an installer, a pip install,
                # or plain source files -- there is no auto-download to wire up per platform
            Release_Page_Url = str(Data.get("html_url", "") or "")

            # Stop if GitHub did not report a release page for this tag
            if not Release_Page_Url:
                self.check_failed.emit("GitHub did not report a release page for the latest version.")
                return

            self.update_available.emit(Latest_Tag.lstrip("v"), Release_Page_Url)
        except Exception as Error:
            self.check_failed.emit(str(Error))



# Check for updates for one application and notify the user if one exists
    # Manual=True also reports "already up to date" / failure outcomes, since a user who
    # explicitly asked to check expects some response either way, unlike the silent startup check
def Run_Version_Check(Parent_Window, Application_Id: str, Manual: bool = False):
    Worker = Version_Check_Worker(Application_Id)
    Parent_Window.Eos_Update_Worker = Worker

    def On_Update_Available(Version, Release_Page_Url):
        Current_Version = Get_Current_Version(Application_Id)

        # Pip installs are updated with a command rather than a downloaded installer asset
        Message_Key = "Update Available Pip Install" if Is_Pip_Install() else "Update Available"

        Acknowledgement_Result, Suppress_Future_Notifications = Warning_Message(
            Parent_Window,
            Message_Key,
            version=Version,
            current_version=Current_Version,
            release_url=Release_Page_Url,
            Checkbox_Text="Do not show this message again",
        )

        # Remember the user's choice to stop seeing update notifications for this application
        if Suppress_Future_Notifications:
            Set_Update_Notifications_Enabled(Application_Id, False)

    Worker.update_available.connect(On_Update_Available)

    if Manual:
        def On_No_Update_Available():
            Success_Message(Parent_Window, "No Update Available", current_version=Get_Current_Version(Application_Id))

        def On_Check_Failed(Message):
            Warning_Message(Parent_Window, "Update Check Failed", message=Message)

        Worker.no_update_available.connect(On_No_Update_Available)
        Worker.check_failed.connect(On_Check_Failed)

    Worker.start()



# Schedule a delayed startup version check for one application
def Check_For_Updates_On_Startup(Parent_Window, Application_Id: str = "EoSAlign"):

    # Update the local installed-application registry with the currently running application
    Register_Installed_Application(Application_Id)

    # Skip the check entirely once the user has asked to stop seeing update notifications
    if not Are_Update_Notifications_Enabled(Application_Id):
        return

    QTimer.singleShot(800, lambda: Run_Version_Check(Parent_Window, Application_Id))



# Immediately check for updates for one application, always reporting an outcome
    # Used by the "Check for Version Updates" menu action, so it ignores the notification
    # suppression setting -- that setting only controls the silent startup check
def Check_For_Updates_Manually(Parent_Window, Application_Id: str = "EoSAlign"):

    Register_Installed_Application(Application_Id)
    Run_Version_Check(Parent_Window, Application_Id, Manual=True)




