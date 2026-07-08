# Load libraries
    # Load standard libraries
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path




# Find the terminal commands that should be installed for one application
def Get_Mac_Terminal_Command_Map(Application_Id):

    if Application_Id == "EoSApplications":
        Terminal_Command_Map = {
            "EoSApplications": "EoSApplications",
            "eosapplications": "EoSApplications",
            "EoSAlign": "EoSAlign",
            "eosalign": "EoSAlign",
            "EoSHolo": "EoSHolo",
            "eosholo": "EoSHolo",
        }
    elif Application_Id == "EoSAlign":
        Terminal_Command_Map = {
            "EoSAlign": "EoSAlign",
            "eosalign": "EoSAlign",
        }
    elif Application_Id == "EoSHolo":
        Terminal_Command_Map = {
            "EoSHolo": "EoSHolo",
            "eosholo": "EoSHolo",
        }
    else:
        Terminal_Command_Map = {}

    # Return the command names that belong to this application
    return Terminal_Command_Map



# Build one macOS terminal launcher script
def Build_Mac_Terminal_Launcher_Text(Target_Application_Name):

    Launcher_Text = f"""#!/bin/bash
set -euo pipefail

APP_NAME="{Target_Application_Name}"

if [[ -d "/Applications/${{APP_NAME}}.app" ]]; then
  APP_PATH="/Applications/${{APP_NAME}}.app"
elif [[ -d "$HOME/Applications/${{APP_NAME}}.app" ]]; then
  APP_PATH="$HOME/Applications/${{APP_NAME}}.app"
else
  APP_PATH="${{APP_NAME}}"
fi

if [[ "$#" -gt 0 ]]; then
  exec open -a "${{APP_PATH}}" --args "$@"
else
  exec open -a "${{APP_PATH}}"
fi
"""

    # Return the shell script text for this launcher
    return Launcher_Text



# Check whether every requested macOS terminal command is already installed
def Check_If_Mac_Terminal_Commands_Are_Installed(Application_Id):

    Terminal_Command_Map = Get_Mac_Terminal_Command_Map(Application_Id)
    Install_Directory = Path("/usr/local/bin")

    for Command_Name in Terminal_Command_Map:
        Command_Path = Install_Directory / Command_Name

        # Return False when any required command is missing or not executable
        if not Command_Path.exists() or not os.access(Command_Path, os.X_OK):
            return False

    # Return True when every required command already exists
    return True



# Install the requested macOS terminal commands into /usr/local/bin with administrator privileges
def Install_Mac_Terminal_Commands(Application_Id):

    Terminal_Command_Map = Get_Mac_Terminal_Command_Map(Application_Id)

    # Return immediately when there is nothing to install
    if not Terminal_Command_Map:
        return True

    Temporary_Directory = Path(tempfile.mkdtemp(prefix="eos_terminal_commands_"))

    try:
        # Create all launchers in a temporary user-writable directory first
        for Command_Name, Target_Application_Name in Terminal_Command_Map.items():
            Launcher_Path = Temporary_Directory / Command_Name
            Launcher_Text = Build_Mac_Terminal_Launcher_Text(Target_Application_Name)
            Launcher_Path.write_text(Launcher_Text, encoding="utf-8")
            Launcher_Path.chmod(0o755)

        Shell_Commands = [
            "/bin/mkdir -p /usr/local/bin",
        ]

        for Command_Name in Terminal_Command_Map:
            Source_Path = Temporary_Directory / Command_Name
            Target_Path = Path("/usr/local/bin") / Command_Name
            Shell_Commands.append(f"/bin/cp {shlex.quote(str(Source_Path))} {shlex.quote(str(Target_Path))}")
            Shell_Commands.append(f"/bin/chmod 755 {shlex.quote(str(Target_Path))}")

        Combined_Shell_Command = " && ".join(Shell_Commands)
        Escaped_Shell_Command = Combined_Shell_Command.replace("\\", "\\\\").replace('"', '\\"')

        AppleScript_Command = [
            "osascript",
            "-e",
            f'do shell script "{Escaped_Shell_Command}" with administrator privileges',
        ]

        subprocess.run(AppleScript_Command, check=True)
    except Exception:
        # Return False when the install did not complete successfully
        return False
    finally:
        shutil.rmtree(Temporary_Directory, ignore_errors=True)

    # Return whether the commands now appear to be installed
    return Check_If_Mac_Terminal_Commands_Are_Installed(Application_Id)



# Offer to install macOS terminal commands once per application version
def Prompt_To_Install_Mac_Terminal_Commands_If_Needed(Parent_Window, Application_Id):

    # Only do this for packaged macOS application launches
    if sys.platform != "darwin" or not getattr(sys, "frozen", False):
        return

    # Skip the prompt when the commands are already installed
    if Check_If_Mac_Terminal_Commands_Are_Installed(Application_Id):
        return

    from Version import Get_Application_Information
    from Message_Manager import Success_Message, Warning_Message
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QMessageBox

    Application_Information = Get_Application_Information(Application_Id)
    Application_Version = str(Application_Information.get("Version", "") or "").strip()
    Prompt_Settings = QSettings("EoSApplications", Application_Id)
    Prompt_Key = "Mac_Terminal_Commands__Prompted_Version"
    Last_Prompted_Version = str(Prompt_Settings.value(Prompt_Key, "") or "").strip()

    # Only prompt once for each app version when the user declines
    if Last_Prompted_Version == Application_Version:
        return

    Terminal_Command_Map = Get_Mac_Terminal_Command_Map(Application_Id)
    Command_List_Text = "\n".join(Terminal_Command_Map.keys())

    Install_Response = Warning_Message(
        Parent_Window,
        "Install Mac Terminal Commands",
        Buttons=QMessageBox.Yes | QMessageBox.No,
        Default_Button=QMessageBox.Yes,
        command_list=Command_List_Text,
    )

    if Install_Response != QMessageBox.Yes:
        Prompt_Settings.setValue(Prompt_Key, Application_Version)
        return

    Install_Was_Successful = Install_Mac_Terminal_Commands(Application_Id)

    if Install_Was_Successful:
        Prompt_Settings.setValue(Prompt_Key, Application_Version)
        Success_Message(
            Parent_Window,
            "Mac Terminal Commands Installed",
        )
    else:
        Warning_Message(
            Parent_Window,
            "Terminal Command Install Failed",
        )
