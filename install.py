"""
One-command installer for EoSApplications, EoSAlign, and EoSHolo.

Run this with:
    python install.py        (Windows)
    python3 install.py       (Mac/Linux)

What it does, in order:
  1. Checks that Python 3.10+ is running this script.
  2. Creates a private virtual environment (in ".venv" here on macOS/Linux,
     or in "%LOCALAPPDATA%\EoSApplications\venv" on Windows -- see
     Get_Venv_Dir() for why) so none of this app's dependencies ever touch
     your system-wide Python.
  3. Installs every package listed in requirements.txt into that environment.
  4. Generates small launcher commands (eosapplications, eosalign, eosholo,
     eosapplications-cleanup) into a "Command_Line_Interface" folder here,
     each one pointing at the private environment's Python and the matching
     script in Code/.
  5. Adds that folder to your PATH, so the commands work from any terminal.

Safe to re-run any time (for example after downloading an updated copy of
this repository) -- it rebuilds the environment and launcher commands from
scratch and simply overwrites its own PATH entry rather than duplicating it.
"""

import ctypes
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


Minimum_Python_Version = (3, 10)

# Command name -> script inside Code/ that its launcher should run
Applications = {
    "eosapplications": "EoSApplications.py",
    "eosalign": "EoSAlign.py",
    "eosholo": "EoSHolo.py",
    "eosapplications-cleanup": "Cleanup_User_Data.py",
}


def Print_Heading(Text):
    print()
    print("=" * 60)
    print(Text)
    print("=" * 60)


def Check_Python_Version():
    if sys.version_info < Minimum_Python_Version:
        Current = ".".join(str(Part) for Part in sys.version_info[:3])
        Required = ".".join(str(Part) for Part in Minimum_Python_Version)
        print(f"ERROR: Python {Required}+ is required, but this is Python {Current}.")
        print("Install a newer Python from https://www.python.org/downloads/ and re-run this script.")
        sys.exit(1)


def Get_Venv_Python(Venv_Dir):
    if sys.platform == "win32":
        return Venv_Dir / "Scripts" / "python.exe"
    return Venv_Dir / "bin" / "python"


def Get_Venv_Dir(Repo_Dir):
    # On Windows, PySide6's wheel contains very deeply nested internal paths
    # (qml/Qt/labs/assetdownloader/...) that can exceed Windows' 260-character
    # path limit once combined with a long, deeply-nested project folder name
    # (e.g. a repo downloaded into "Desktop\GitHub\...\EoSAlign"). Placing the
    # environment under the short, per-user LOCALAPPDATA path instead avoids
    # that without requiring admin rights or enabling long-path support.
    # macOS/Linux have no such limit, so the environment stays inside the
    # repository folder for simplicity.
    if sys.platform == "win32":
        Local_App_Data = os.environ.get("LOCALAPPDATA")
        if Local_App_Data:
            return Path(Local_App_Data) / "EoSApplications" / "venv"
    return Repo_Dir / ".venv"


def Create_Virtual_Environment(Venv_Dir):
    Print_Heading("Creating the Python environment (.venv)")
    Builder = venv.EnvBuilder(with_pip=True, clear=True)
    Builder.create(Venv_Dir)
    print(f"  Created: {Venv_Dir}")


def Install_Requirements(Venv_Python, Requirements_File):
    Print_Heading("Installing required packages (this can take a few minutes)")
    try:
        subprocess.run([str(Venv_Python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(Venv_Python), "-m", "pip", "install", "-r", str(Requirements_File)], check=True)
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install required packages. See the pip output above for details.")
        sys.exit(1)


def Generate_Launchers(Repo_Dir, Venv_Python):
    Print_Heading("Creating the eosapplications / eosalign / eosholo commands")
    Cli_Dir = Repo_Dir / "Command_Line_Interface"
    Cli_Dir.mkdir(exist_ok=True)
    Code_Dir = Repo_Dir / "Code"

    for Command_Name, Script_File in Applications.items():
        Script_Path = Code_Dir / Script_File
        if sys.platform == "win32":
            Launcher_Path = Cli_Dir / f"{Command_Name}.bat"
            Launcher_Path.write_text(
                f'@echo off\r\n"{Venv_Python}" "{Script_Path}" %*\r\n',
                encoding="utf-8",
            )
        else:
            Launcher_Path = Cli_Dir / Command_Name
            Launcher_Path.write_text(
                f'#!/bin/bash\nexec "{Venv_Python}" "{Script_Path}" "$@"\n',
                encoding="utf-8",
            )
            Launcher_Path.chmod(0o755)
        print(f"  {Command_Name}")

    return Cli_Dir


def Add_To_Windows_Path(Cli_Dir):
    import winreg

    Folder = str(Cli_Dir)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as Key:
        try:
            Current_Path, _ = winreg.QueryValueEx(Key, "Path")
        except FileNotFoundError:
            Current_Path = ""
        Existing_Entries = [Entry for Entry in Current_Path.split(";") if Entry]
        if Folder in Existing_Entries:
            print(f"  Already on PATH: {Folder}")
            return
        New_Path = ";".join(Existing_Entries + [Folder])
        winreg.SetValueEx(Key, "Path", 0, winreg.REG_EXPAND_SZ, New_Path)

    # Tell already-running processes (like File Explorer) that the environment
    # changed. New terminal windows will pick up the change either way.
    Result = ctypes.c_long()
    ctypes.windll.user32.SendMessageTimeoutW(
        0xFFFF, 0x1A, 0, "Environment", 0x0002, 5000, ctypes.byref(Result)
    )
    print(f"  Added to your PATH: {Folder}")


def Add_To_Unix_Path(Cli_Dir):
    Target_Dir = Path("/usr/local/bin")
    Use_Sudo = False

    if Target_Dir.is_dir() and os.access(Target_Dir, os.W_OK):
        pass
    elif shutil.which("sudo"):
        Use_Sudo = True
    else:
        Target_Dir = Path.home() / ".local" / "bin"
        Target_Dir.mkdir(parents=True, exist_ok=True)

    print(f"  Linking commands into: {Target_Dir}" + (" (requires your password)" if Use_Sudo else ""))
    for Command_Name in Applications:
        Source_Path = Cli_Dir / Command_Name
        Destination_Path = Target_Dir / Command_Name
        if Use_Sudo:
            subprocess.run(["sudo", "ln", "-sf", str(Source_Path), str(Destination_Path)], check=True)
        else:
            if Destination_Path.exists() or Destination_Path.is_symlink():
                Destination_Path.unlink()
            os.symlink(Source_Path, Destination_Path)
        print(f"    {Command_Name}")

    Path_Entries = os.environ.get("PATH", "").split(os.pathsep)
    if str(Target_Dir) not in Path_Entries:
        print()
        print(f"  NOTE: {Target_Dir} is not on your PATH yet.")
        print("  Add this line to ~/.zshrc or ~/.bashrc, then open a new terminal:")
        print(f'    export PATH="{Target_Dir}:$PATH"')


def main():
    Check_Python_Version()

    Repo_Dir = Path(__file__).resolve().parent
    Venv_Dir = Get_Venv_Dir(Repo_Dir)
    Requirements_File = Repo_Dir / "requirements.txt"

    Create_Virtual_Environment(Venv_Dir)
    Venv_Python = Get_Venv_Python(Venv_Dir)
    Install_Requirements(Venv_Python, Requirements_File)
    Cli_Dir = Generate_Launchers(Repo_Dir, Venv_Python)

    Print_Heading("Adding commands to your PATH")
    if sys.platform == "win32":
        Add_To_Windows_Path(Cli_Dir)
    else:
        Add_To_Unix_Path(Cli_Dir)

    Print_Heading("Done")
    print("Open a NEW terminal window (so the PATH change takes effect), then run:")
    print("  eosapplications   - launch the EoS Applications hub")
    print("  eosalign          - launch EoSAlign directly")
    print("  eosholo           - launch EoSHolo directly")
    print()


if __name__ == "__main__":
    main()
