# Load libraries
    # Load standard libraries
import hashlib
import json
import os
import urllib.parse
import urllib.request
    # Load third party libraries
from PySide6.QtCore import QThread, Signal, QSettings, QTimer
    # Load local libraries
from EoS_Math.Load_Calibration_Files import (
    Downloaded_Calibration_Files_Folder,
    Downloaded_Calibration_Files_Previous_Edits_Folder,
    User_Application_Data_Folder,
    Archive_Existing_File_With_Version,
)
from Check_For_Updates import Show_Update_Notifications_Setting_Key
from Calibration_Update_Review_Dialog import Calibration_Update_Review_Dialog
from Message_Manager import Warning_Message, Success_Message





# Store the user agent used for calibration manifest/file requests
User_Agent = "EoSAlign-calibration-check"

# Store the GitHub location of the shared Calibration_Files repo
    # This repo has no per-app version and no Releases (calibration data is shared by every
    # app in the suite), so it is not stored in Version.py's per-application Applications table
Calibration_Files_Github_Owner = "EoSApplications"
Calibration_Files_Github_Repository = "Calibration_Files"
Calibration_Files_Github_Branch = "main"

# Store where the locally recorded manifest of already-downloaded calibration file hashes is kept
Calibration_Manifest_Record_File_Name = '.Calibration_Manifest_Record.json'
Calibration_Manifest_Record_Path = os.path.join(User_Application_Data_Folder, Calibration_Manifest_Record_File_Name)

# Calibration updates are shared across every app in the suite (the same downloaded/user
# calibration folders are used no matter which app is running), so the notification
# preference is one shared setting rather than per application id like the main app updater's
Calibration_Update_Notifications_Settings_Scope = "Calibration_Files"


# Find the GitHub location of the calibration repo, applying environment overrides when present
    # Mirrors the override pattern in Check_For_Updates.py so a fork/test repo can be used instead
def Get_Calibration_Files_Repository_Information():

    Github_Owner = os.environ.get("CALIBRATION_FILES_GITHUB_OWNER", "").strip() or Calibration_Files_Github_Owner
    Github_Repository = os.environ.get("CALIBRATION_FILES_GITHUB_REPOSITORY", "").strip() or Calibration_Files_Github_Repository
    Github_Branch = os.environ.get("CALIBRATION_FILES_GITHUB_BRANCH", "").strip() or Calibration_Files_Github_Branch

    # Return the owner, repository, and branch to use for calibration manifest/file requests
    return Github_Owner, Github_Repository, Github_Branch



# Find the raw-content base URL for the calibration repo
def Get_Calibrations_Raw_Base_Url():

    Github_Owner, Github_Repository, Github_Branch = Get_Calibration_Files_Repository_Information()

    # Return no URL when the repository location is not configured
    if not Github_Owner or not Github_Repository:
        return None

    # Return the raw-content base URL for the calibration data repo
    return f"https://raw.githubusercontent.com/{Github_Owner}/{Github_Repository}/{Github_Branch}"



# Load the locally recorded manifest of previously-downloaded calibration file hashes
def Load_Calibration_Manifest_Record():

    if not os.path.exists(Calibration_Manifest_Record_Path):
        return {}

    try:
        with open(Calibration_Manifest_Record_Path, 'r', encoding='utf-8') as Record_File:
            return json.load(Record_File)
    except Exception:
        # A corrupted or unreadable record is treated as "nothing downloaded yet"
        return {}



# Save the locally recorded manifest of synced calibration file hashes
def Save_Calibration_Manifest_Record(Record):

    Temporary_Path = Calibration_Manifest_Record_Path + '.tmp'
    with open(Temporary_Path, 'w', encoding='utf-8') as Record_File:
        json.dump(Record, Record_File, indent=2, sort_keys=True)
    os.replace(Temporary_Path, Calibration_Manifest_Record_Path)

    # Hide the file on Windows (dot-prefix is sufficient on macOS/Linux)
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            existing = kernel32.GetFileAttributesW(Calibration_Manifest_Record_Path)
            if existing != 0xFFFFFFFF:
                kernel32.SetFileAttributesW(Calibration_Manifest_Record_Path, existing | 0x02)
        except Exception:
            pass



# Check whether calibration update notifications are currently turned on
def Are_Calibration_Update_Notifications_Enabled() -> bool:

    Notification_Settings = QSettings("EoS", Calibration_Update_Notifications_Settings_Scope)
    Are_Enabled = Notification_Settings.value(Show_Update_Notifications_Setting_Key, True, type=bool)

    # Return whether the user still wants to see calibration update notifications
    return Are_Enabled



# Turn calibration update notifications on or off
    # Used both by the "do not show this message again" checkbox on the review dialog
    # and by the matching toggle on the General settings page
def Set_Calibration_Update_Notifications_Enabled(Are_Enabled: bool):

    Notification_Settings = QSettings("EoS", Calibration_Update_Notifications_Settings_Scope)
    Notification_Settings.setValue(Show_Update_Notifications_Setting_Key, bool(Are_Enabled))



# Check the calibration repo in the background for new or changed calibration files
class Manifest_Check_Worker(QThread):
    manifest_checked = Signal(dict)  # {filename: new_hash} for files that are new or changed

    def run(self):
        Raw_Base_Url = Get_Calibrations_Raw_Base_Url()

        # Skip the check when no repository has been configured
        if not Raw_Base_Url:
            return

        try:
            # index.json lives in the Calibration_Files repo's Distribution/ subfolder,
            # kept separate from the hand-authored .yaml files it describes
            Manifest_Url = f"{Raw_Base_Url}/Distribution/index.json"
            Request = urllib.request.Request(Manifest_Url, headers={"User-Agent": User_Agent})
            with urllib.request.urlopen(Request, timeout=8) as Response:
                Remote_Manifest = json.loads(Response.read().decode())

            Remote_Files = Remote_Manifest.get("Files", {})
            Local_Record = Load_Calibration_Manifest_Record()

            # Find every file that is new or whose hash no longer matches what was last downloaded
            Changed_Files = {
                Filename: Remote_Hash
                for Filename, Remote_Hash in Remote_Files.items()
                if Local_Record.get(Filename) != Remote_Hash
            }

            self.manifest_checked.emit(Changed_Files)
        except Exception:
            return



# Download the user-approved calibration files in the background
class Calibration_Download_Worker(QThread):
    finished = Signal(int)  # number of files successfully downloaded
    error = Signal(str)

    def __init__(self, Approved_Files: dict):
        super().__init__()
        self.Approved_Files = Approved_Files

    def run(self):
        Raw_Base_Url = Get_Calibrations_Raw_Base_Url()
        if not Raw_Base_Url:
            self.error.emit("Calibration repository is not configured.")
            return

        Local_Record = Load_Calibration_Manifest_Record()
        Downloaded_Count = 0

        try:
            for Filename, Expected_Hash in self.Approved_Files.items():
                # Reject any manifest filename that could escape Downloaded_Calibration_Files_Folder
                # (e.g. "../../something") or that isn't a plain calibration file
                Safe_Filename = os.path.basename(Filename)
                if Safe_Filename != Filename or not Safe_Filename.endswith('.yaml'):
                    continue

                File_Url = f"{Raw_Base_Url}/{urllib.parse.quote(Filename)}"
                Request = urllib.request.Request(File_Url, headers={"User-Agent": User_Agent})
                with urllib.request.urlopen(Request, timeout=30) as Response:
                    File_Bytes = Response.read()

                # Skip this file if its downloaded contents do not match the manifest's declared hash
                Actual_Hash = f"sha256:{hashlib.sha256(File_Bytes).hexdigest()}"
                if Actual_Hash != Expected_Hash:
                    continue

                Destination_Path = os.path.join(Downloaded_Calibration_Files_Folder, Safe_Filename)
                # Archive any existing copy of this file before overwriting it
                Archive_Existing_File_With_Version(Destination_Path, Downloaded_Calibration_Files_Previous_Edits_Folder)

                with open(Destination_Path, 'wb') as Output_File:
                    Output_File.write(File_Bytes)

                Local_Record[Filename] = Expected_Hash
                Downloaded_Count += 1

            Save_Calibration_Manifest_Record(Local_Record)
            self.finished.emit(Downloaded_Count)
        except Exception as exc:
            # Save whatever succeeded before the failure so a retry does not repeat completed work
            Save_Calibration_Manifest_Record(Local_Record)
            self.error.emit(str(exc))



# Start downloading the given, already-approved calibration files in the background
def Start_Calibration_Download(Parent_Window, Approved_Files: dict):
    Downloader = Calibration_Download_Worker(Approved_Files)
    Parent_Window.Eos_Calibration_Downloader = Downloader

    def On_Finished(Downloaded_Count):
        # Rebuild the in-memory calibration set immediately so the update is usable without a restart
        from EoS_Math.Build_Dataframe import Load_The_Calibrations_Into_Memory
        Load_The_Calibrations_Into_Memory()
        Success_Message(Parent_Window, "Calibration Update Complete", count=Downloaded_Count)

    def On_Error(Message):
        Warning_Message(Parent_Window, "Failed to Update Calibrations", message=Message)

    Downloader.finished.connect(On_Finished)
    Downloader.error.connect(On_Error)
    Downloader.start()



# Check for calibration updates, let the user review/preview/select them, then download only what was approved
def Run_Calibration_Update_Check(Parent_Window):
    Worker = Manifest_Check_Worker()
    Parent_Window.Eos_Calibration_Check_Worker = Worker

    def On_Manifest_Checked(Changed_Files):
        # Nothing to do when every calibration file already matches what was last downloaded
        if not Changed_Files:
            return

        Raw_Base_Url = Get_Calibrations_Raw_Base_Url()
        Review_Dialog = Calibration_Update_Review_Dialog(Parent_Window, Changed_Files, Raw_Base_Url)
        Parent_Window.Eos_Calibration_Review_Dialog = Review_Dialog
        Dialog_Result = Review_Dialog.exec()

        # Remember the user's choice to stop seeing calibration update notifications,
        # regardless of whether they approved any downloads from this particular batch
        if Review_Dialog.Get_Suppress_Notifications_Checked():
            Set_Calibration_Update_Notifications_Enabled(False)

        # Stop here if the user cancelled instead of approving any files
        if Dialog_Result != Calibration_Update_Review_Dialog.Accepted:
            return

        Approved_Filenames = Review_Dialog.Get_Approved_Filenames()
        # Nothing to download if the user unchecked every file before approving
        if not Approved_Filenames:
            return

        Approved_Files = {Filename: Changed_Files[Filename] for Filename in Approved_Filenames}
        Start_Calibration_Download(Parent_Window, Approved_Files)

    Worker.manifest_checked.connect(On_Manifest_Checked)
    Worker.start()



# Schedule a delayed startup calibration check
def Check_For_Calibration_Updates_On_Startup(Parent_Window):

    # Skip the check entirely once the user has asked to stop seeing calibration update notifications
    if not Are_Calibration_Update_Notifications_Enabled():
        return

    QTimer.singleShot(1500, lambda: Run_Calibration_Update_Check(Parent_Window))




