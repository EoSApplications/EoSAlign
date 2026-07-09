# Installing EoSApplications, EoSAlign, and EoSHolo

EoSApplications requires Python 3.12.x. Python 3.11 and older and Python 3.13
and newer are not supported by this release.

After installation, these commands are available:

```text
eosapplications
eosalign
eosholo
```

Choose one installation method below. Most users should use pipx because it
creates and manages an isolated environment automatically.

## Option 1: Install with pipx (recommended)

pipx creates a private environment for EoSApplications and makes its commands
available from every terminal. You do not activate the environment yourself.

### Windows

Install Python 3.12 from [python.org](https://www.python.org/downloads/) and
select **Add python.exe to PATH** during installation. Then open PowerShell:

```powershell
py -3.12 -m pip install --user pipx
py -3.12 -m pipx ensurepath
```

Close and reopen PowerShell, then install EoSApplications:

```powershell
pipx install --python 3.12 eosapplications
```

### macOS

Install Python 3.12 from [python.org](https://www.python.org/downloads/) or
Homebrew. Install pipx and EoSApplications:

```bash
brew install pipx
pipx ensurepath
pipx install --python 3.12 eosapplications
```

Close and reopen the terminal after `pipx ensurepath` if the commands are not
found immediately.

### Linux

Install Python 3.12, its `venv` support, and pipx with your distribution's
package manager. For Ubuntu:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv pipx
pipx ensurepath
pipx install --python 3.12 eosapplications
```

Package names vary by Linux distribution.

### Update or uninstall a pipx installation

```text
pipx upgrade eosapplications
pipx uninstall eosapplications
```

To delete downloaded calibration updates and other user data, run
`eosapplications-cleanup` before uninstalling.

## Option 2: Install with pip in a virtual environment

This method gives you direct control over the environment. You must activate
the environment again whenever you open a new terminal before running the
applications.

### Windows PowerShell

```powershell
py -3.12 -m venv eosapplications-env
.\eosapplications-env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install eosapplications
```

The claimed-name aliases install the same suite:

```text
python -m pip install eosalign
python -m pip install eosholo
```

For later sessions, return to the folder containing the environment and run:

```powershell
.\eosapplications-env\Scripts\Activate.ps1
eosalign
```

### Windows Command Prompt

```bat
py -3.12 -m venv eosapplications-env
eosapplications-env\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install eosapplications
```

For later sessions:

```bat
eosapplications-env\Scripts\activate.bat
eosalign
```

### macOS or Linux

```bash
python3.12 -m venv eosapplications-env
source eosapplications-env/bin/activate
python -m pip install --upgrade pip
python -m pip install eosapplications
```

For later sessions, return to the folder containing the environment and run:

```bash
source eosapplications-env/bin/activate
eosalign
```

To leave an activated environment:

```text
deactivate
```

To update the application while the environment is active:

```text
python -m pip install --upgrade eosapplications
```

To uninstall it, run `eosapplications-cleanup` first if you also want to delete
user data, then run:

```text
python -m pip uninstall eosapplications
```

The environment folder can be deleted after deactivation.

## Option 3: Download or clone the source repository

Use this method to run the checked-out source files. The included `install.py`
script creates a private environment, installs the exact dependencies from
`requirements.txt`, and creates launcher commands.

### Install Python

Install Python 3.12 from [python.org](https://www.python.org/downloads/).
On Windows, select **Add python.exe to PATH**.

Confirm the version:

```powershell
py -3.12 --version
```

```bash
python3.12 --version
```

The result must begin with `Python 3.12`.

### Download or clone

Either select **Code -> Download ZIP** on GitHub and extract the archive, or:

```text
git clone https://github.com/EoSApplications/EoSAlign.git
```

Open a terminal in the resulting `EoSAlign` folder.

### Run install.py

Windows:

```powershell
py -3.12 install.py
```

macOS or Linux:

```bash
python3.12 install.py
```

The script:

1. Verifies that Python 3.12 is being used.
2. Creates a private virtual environment.
3. Installs PySide6, NumPy, pandas, Matplotlib, Pillow, SciPy, PyYAML,
   darkdetect, dill, and lmfit at the tested versions.
4. Creates the `eosapplications`, `eosalign`, `eosholo`, and
   `eosapplications-cleanup` commands.
5. Adds those commands to the user PATH.

Close and reopen the terminal after installation, then run any application
command.

### Update or uninstall a source installation

After downloading a newer copy or running `git pull`, rerun `install.py`.

Before removing the repository, run `eosapplications-cleanup` if you also want
to delete downloaded calibration updates and other user data.

On Windows, remove the repository and
`%LOCALAPPDATA%\EoSApplications\venv`. You can also remove the repository's
`Command_Line_Interface` entry from your user PATH.

On macOS or Linux, remove the generated command links from `/usr/local/bin` or
`~/.local/bin`, then delete the repository and its `.venv` folder.

## Troubleshooting

### Python 3.12 is not found

Install Python 3.12 and make sure it is available as `py -3.12` on Windows or
`python3.12` on macOS/Linux.

### PowerShell blocks Activate.ps1

Use the Windows Command Prompt instructions, or run the environment's Python
without activation:

```powershell
.\eosapplications-env\Scripts\eosalign.exe
```

### A command is not found after pipx or install.py

Close and reopen the terminal so the updated PATH is loaded. For pipx, rerun:

```text
pipx ensurepath
```

### Linux reports that venv or pip is missing

Install your distribution's Python 3.12 `venv` and pip packages. On Ubuntu,
these are commonly named `python3.12-venv` and `python3-pip`.
