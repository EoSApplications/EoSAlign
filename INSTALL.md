# Installing EoSApplications, EoSAlign, and EoSHolo

This page covers everything needed to get `eosapplications`, `eosalign`, and `eosholo` running as terminal commands on Windows, macOS, or Linux, using the included one-command installer script (`install.py`).

No conda, no manual dependency wrangling, and no admin/root privileges are required — `install.py` builds a private Python environment inside this folder and installs everything into it.


## 1. Install Python (one-time, skip if you already have it)

You need Python 3.10 or newer.

- Windows / macOS: download the installer from [python.org/downloads](https://www.python.org/downloads/) and run it. **On Windows, check the "Add python.exe to PATH" box** on the first install screen — this is required for the next steps to work.
- Linux: Python 3.10+ is preinstalled on most modern distributions. If not, install it with your package manager, e.g. `sudo apt install python3 python3-venv`.

To confirm it worked, open a terminal and run:

    python --version        # Windows
    python3 --version       # macOS/Linux

Either should print `Python 3.10.x` or higher.


## 2. Download this repository

Either:

- Click **Code -> Download ZIP** on the GitHub page and extract it somewhere you'll remember (e.g. your Desktop), or
- Clone it with git:

      git clone https://github.com/EoSApplications/EoSAlign.git

Either way, you should end up with a folder (e.g. `EoSAlign`) that directly contains this `INSTALL.md` file, `install.py`, a `Code` folder, and so on.


## 3. Run the installer

Open a terminal **inside that folder** and run:

    python install.py        # Windows
    python3 install.py       # macOS/Linux

This single script:

1. Creates a private virtual environment — on macOS/Linux, in a new `.venv` folder here; on Windows, in `%LOCALAPPDATA%\EoSApplications\venv` instead (PySide6's installed files include very deeply nested paths that can exceed Windows' path-length limit if the environment lives inside a long, deeply-nested download location, so it's kept in a short, fixed spot instead). Either way, it does not touch your system Python or any other project.
2. Installs every package listed in [requirements.txt](requirements.txt) into that environment (PySide6, numpy, pandas, matplotlib, pillow, scipy, networkx, plotly, pyyaml, darkdetect).
3. Generates `eosapplications`, `eosalign`, and `eosholo` launcher commands into a new `Command_Line_Interface` folder here.
4. Adds that folder to your PATH (a per-user PATH change on Windows; a symlink into `/usr/local/bin` or `~/.local/bin` on macOS/Linux) so those commands work from any terminal.

This takes a few minutes the first time, mostly spent downloading packages.


## 4. Open a new terminal and run the apps

PATH changes only apply to terminals opened *after* the installer ran, so close and reopen your terminal, then run any of:

    eosapplications      # the launcher hub for all three apps
    eosalign              # EoSAlign directly
    eosholo                # EoSHolo directly


## Updating

If you download a newer copy of this repository (or `git pull`), just run `python install.py` (or `python3 install.py`) again from inside it. It rebuilds the environment and commands from scratch and safely overwrites its own PATH entry rather than duplicating it — you don't need to remove anything first.


## Uninstalling

1. Remove the command shortcuts and environment the installer created:
   - Windows: delete the `Command_Line_Interface` subfolder from the repository (step 3 below removes the rest of it anyway), and delete `%LOCALAPPDATA%\EoSApplications` (the private environment). The PATH entry pointing at `Command_Line_Interface` is harmless once that folder is gone, but if you'd like to remove it too: Settings -> "Edit environment variables for your account" -> select `Path` -> Edit -> remove the entry ending in `Command_Line_Interface`.
   - macOS/Linux: delete the symlinks the installer created:

         rm /usr/local/bin/eosapplications /usr/local/bin/eosalign /usr/local/bin/eosholo /usr/local/bin/eosapplications-cleanup

     (If the installer had to fall back to `~/.local/bin` instead, delete them from there.)
2. If you have data you entered or calibration updates you downloaded and want them wiped too, run `eosapplications-cleanup` **before** deleting anything (it asks for confirmation, then deletes the app's user data folder).
3. Delete the downloaded/cloned repository folder.


## Troubleshooting

**`'python' is not recognized` / `command not found: python3`**
Python isn't installed, or (on Windows) wasn't added to PATH during installation. Reinstall Python from [python.org/downloads](https://www.python.org/downloads/) and make sure "Add python.exe to PATH" is checked.

**`eosalign`/`eosholo`/`eosapplications` still not found after installing**
Make sure you opened a *new* terminal window after running `install.py` — PATH changes never apply to terminals that were already open.

**Installer says a newer Python is required**
Your default `python`/`python3` points at an older version. Install Python 3.10+ from [python.org/downloads](https://www.python.org/downloads/), then re-run `install.py` (on Windows, the installer offers to make the new version the default; on macOS/Linux you may need to invoke it explicitly, e.g. `python3.12 install.py`).

**macOS/Linux: installer asks for your password**
This only happens if `/usr/local/bin` isn't writable without elevated privileges — the installer uses `sudo` once to place the command shortcuts there. If you'd rather not enter a password, cancel and it will fall back to `~/.local/bin` on the next run (make sure that folder is on your PATH, per the note the installer prints).




