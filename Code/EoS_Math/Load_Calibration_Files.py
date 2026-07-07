# Load libraries
    # Load standard libraries
import os
import sys
    # Load third-party libraries
import yaml
import pickle
    # Load local libraries
from Version import Get_Current_Running_Application_Id, Get_Application_Information





# Find the user's application data folder
def Find_User_Applications_Folder():

    # If the platform is Windows, use the LOCALAPPDATA environment variable
        # This will point to a folder like C:\Users\Username\AppData\Local
    if sys.platform == 'win32':
        return os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    
    # If the platform is macOS, use the ~/Library/Application Support folder
        # This will point to a folder like /Users/Username/Library/Application Support
    elif sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support')
    
    # If the platform is Linux, use the XDG_DATA_HOME environment variable or default to ~/.local/share
        # This will point to a folder like /home/username/.local/share
    elif sys.platform == 'linux':
        return os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    
    # For other platforms, default to the user's home directory
    else:
        return os.path.expanduser('~')
    


# Find the calibration files folder baised on if the application is packaged as an executable or individual code files
def Find_Application_Calibration_Files_Folder():

    # If the application is a packaged executable
    if getattr(sys, 'frozen', False):
        # Windows installers copy one shared Calibration_Files folder into the install root,
        # beside the EoSApplications\, EoSAlign\, and EoSHolo\ subfolders (not inside any one of
        # them) - the Windows PyInstaller build does not embed Calibration_Files into the exe itself
        if sys.platform == 'win32':
            base = os.path.dirname(os.path.dirname(sys.executable))
        # macOS and Linux builds embed Calibration_Files via PyInstaller datas, which the onefile
        # bootloader extracts to sys._MEIPASS at runtime rather than beside the executable
        else:
            base = sys._MEIPASS
    # If the application is running as individual python scripts
    else:
        # Then the calibration files are located in a folder with all the application python files
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base, 'Calibration_Files')



# Define all the paths to the calibration files
    # Start with the folder where the user's application data is stored
User_Applications_Folder = Find_User_Applications_Folder()
User_Application_Data_Folder = os.path.join(User_Applications_Folder, 'EoS')
        # If the folder does not exist make it
os.makedirs(User_Application_Data_Folder, exist_ok=True)
        # Inside the user's application data there will be a user edited folder
User_Edited_Calibration_Files_Folder = os.path.join(User_Application_Data_Folder, 'User_Edited_Calibration_Files')
            # If the folder does not exist make it
os.makedirs(User_Edited_Calibration_Files_Folder, exist_ok=True)
        # Inside the user's application data there will be a user entered folder
User_Entered_Calibration_Files_Folder = os.path.join(User_Application_Data_Folder, 'User_Entered_Calibration_Files')
            # If the folder does not exist make it
os.makedirs(User_Entered_Calibration_Files_Folder, exist_ok=True)
        # Inside the user's application data there will be a folder for calibration files synced from EoSCalibrations
Downloaded_Calibration_Files_Folder = os.path.join(User_Application_Data_Folder, 'Downloaded_Calibration_Files')
            # If the folder does not exist make it
os.makedirs(Downloaded_Calibration_Files_Folder, exist_ok=True)
            # Overwritten downloaded files are archived here rather than deleted
Downloaded_Calibration_Files_Previous_Edits_Folder = os.path.join(Downloaded_Calibration_Files_Folder, 'Previous_Edits')
os.makedirs(Downloaded_Calibration_Files_Previous_Edits_Folder, exist_ok=True)
    # The main calibration files are stored with the application itself
Application_Calibration_Files_Folder = Find_Application_Calibration_Files_Folder()
    # The calibration file cache is stored in the user's application data folder
Calibration_Files_Cache_File_Name = '.Calibration_Files_Cache.pkl'
Calibration_Files_Cache_File_Path = os.path.join(User_Application_Data_Folder, Calibration_Files_Cache_File_Name)



# Move an existing file to Old_Dir with a versioned filename instead of overwriting it in place
    # Shared by the user-edited-calibration save path and the downloaded-calibration sync path
def Archive_Existing_File_With_Version(Path, Old_Dir):

    # Nothing to archive if the file does not exist yet
    if not os.path.exists(Path):
        return

    os.makedirs(Old_Dir, exist_ok=True)
    Base = os.path.splitext(os.path.basename(Path))[0]
    Ext = os.path.splitext(Path)[1]

    # Find the next unused versioned filename and move the existing file there
    n = 1
    while True:
        Archived = os.path.join(Old_Dir, f'{Base}_v{n:03d}{Ext}')
        if not os.path.exists(Archived):
            os.replace(Path, Archived)
            break
        n += 1



# Check if there have been any changes to the calibration files since the last time they were loaded
def Check_For_Calibration_File_Changes():

    # Get the last modified time of each calibration file in each folder
    Application_Calibration_Files_Mtime = max((os.path.getmtime(os.path.join(Application_Calibration_Files_Folder, f)) for f in os.listdir(Application_Calibration_Files_Folder) if f.endswith('.yaml')), default=0.0)
    User_Edited_Calibration_Files_Mtime = max((os.path.getmtime(os.path.join(User_Edited_Calibration_Files_Folder, f)) for f in os.listdir(User_Edited_Calibration_Files_Folder) if f.endswith('.yaml')), default=0.0)
    User_Entered_Calibration_Files_Mtime = max((os.path.getmtime(os.path.join(User_Entered_Calibration_Files_Folder, f)) for f in os.listdir(User_Entered_Calibration_Files_Folder) if f.endswith('.yaml')), default=0.0)
    Downloaded_Calibration_Files_Mtime = max((os.path.getmtime(os.path.join(Downloaded_Calibration_Files_Folder, f)) for f in os.listdir(Downloaded_Calibration_Files_Folder) if f.endswith('.yaml')), default=0.0)

    # Get the most recent modified time across all calibration files
    Latest_Calibration_File_Mtime = max(Application_Calibration_Files_Mtime, User_Edited_Calibration_Files_Mtime, User_Entered_Calibration_Files_Mtime, Downloaded_Calibration_Files_Mtime)

    return Latest_Calibration_File_Mtime



# Check if there have been any changes to the calibration file folders since the last time they were loaded
def Check_For_Calibration_Folder_Changes():

    # Get the last modified time of the application calibration files folder
    Application_Calibration_Files_Folder_Mtime = os.path.getmtime(Application_Calibration_Files_Folder)
    # Get the last modified time of the user edited calibration files folder
    User_Edited_Calibration_Files_Folder_Mtime = os.path.getmtime(User_Edited_Calibration_Files_Folder)
    # Get the last modified time of the user entered calibration files folder
    User_Entered_Calibration_Files_Folder_Mtime = os.path.getmtime(User_Entered_Calibration_Files_Folder)
    # Get the last modified time of the downloaded calibration files folder
    Downloaded_Calibration_Files_Folder_Mtime = os.path.getmtime(Downloaded_Calibration_Files_Folder)

    # Get the most recent modified time across all calibration file folders
    Latest_Calibration_File_Folder_Mtime = max(Application_Calibration_Files_Folder_Mtime, User_Edited_Calibration_Files_Folder_Mtime, User_Entered_Calibration_Files_Folder_Mtime, Downloaded_Calibration_Files_Folder_Mtime)

    return Latest_Calibration_File_Folder_Mtime



# Build a fingerprint of the resolved calibration folder locations. Renaming or moving
    # these folders (e.g. relocating the source checkout) does not reliably change their
    # mtimes, so the mtime-based staleness check below cannot detect it on its own - the
    # fingerprint lets a relocated cache be rejected outright instead of silently serving
    # calibration file paths that no longer exist.
def Get_Calibration_Folders_Fingerprint():
    return (
        os.path.normcase(os.path.abspath(Application_Calibration_Files_Folder)),
        os.path.normcase(os.path.abspath(User_Edited_Calibration_Files_Folder)),
        os.path.normcase(os.path.abspath(User_Entered_Calibration_Files_Folder)),
        os.path.normcase(os.path.abspath(Downloaded_Calibration_Files_Folder)),
    )



# Check that every calibration file path recorded in loaded cache data still exists on disk
def Check_If_Calibration_File_Paths_Still_Exist(Calibration_Files_Data):
    return all(
        os.path.exists(Entry['Calibration File Path'])
        for Entry in Calibration_Files_Data.values()
    )



# Find the version of the currently running application
    # Used to invalidate calibration caches after an update - the calibration-parsing and
    # equation-building code can change between versions even when no calibration file or
    # folder has changed, which none of the checks above are able to detect on their own
def Get_Current_Application_Version_For_Cache():
    return str(Get_Application_Information(Get_Current_Running_Application_Id()).get('Version', '') or '')



# Check if the calibration file cache exists and is up to date
def Check_If_Calibration_Cache_Is_Valid():

    # If the cache file does not exist
    if not os.path.exists(Calibration_Files_Cache_File_Path):
        # The cache is not valid
        return False

    # Get the last modified time of the cache file
    Cache_File_Mtime = os.path.getmtime(Calibration_Files_Cache_File_Path)
    # Get the most recent modified time across all calibration files
    Latest_Calibration_File_Mtime = Check_For_Calibration_File_Changes()
    # Get the most recent modified time across all calibration file folders
    Latest_Calibration_File_Folder_Mtime = Check_For_Calibration_Folder_Changes()

    # If any calibration file or folder has been modified more recently than the cache file
    if Latest_Calibration_File_Mtime > Cache_File_Mtime or Latest_Calibration_File_Folder_Mtime > Cache_File_Mtime:
        # The cache is not valid
        return False

    # The calibration file cache is valid
    return True



# Load the calibration file cache, returning None if it is missing, stale, was built from a
    # different folder location, or its recorded file paths have since moved/been deleted
def Load_Valid_Calibration_Cache():

    if not Check_If_Calibration_Cache_Is_Valid():
        return None

    try:
        with open(Calibration_Files_Cache_File_Path, 'rb') as Calibration_File_Cache:
            Cache_Envelope = pickle.load(Calibration_File_Cache)

        if Cache_Envelope.get('Folder_Fingerprint') != Get_Calibration_Folders_Fingerprint():
            print('[Calibration Files Cache] Calibration folder location changed, rebuilding...')
            return None

        if Cache_Envelope.get('Application_Version') != Get_Current_Application_Version_For_Cache():
            print('[Calibration Files Cache] Application version changed, rebuilding...')
            return None

        Calibration_Files_Data = Cache_Envelope['Calibration_Files_Data']
        if not Check_If_Calibration_File_Paths_Still_Exist(Calibration_Files_Data):
            print('[Calibration Files Cache] Cached file paths no longer exist, rebuilding...')
            return None

        return Calibration_Files_Data
    except Exception as exc:
        print(f"[Calibration Files Cache] Cache corrupted ({exc}), rebuilding...")
        return None



# If the cache is remade save it to a temperary file and then rename it to the actual cache file
def Save_Calibration_Cache(Calibration_Files_Data):

    Cache_Envelope = {
        'Folder_Fingerprint': Get_Calibration_Folders_Fingerprint(),
        'Application_Version': Get_Current_Application_Version_For_Cache(),
        'Calibration_Files_Data': Calibration_Files_Data,
    }

    # Create a temperary cache file
    Temperary_Cache_File = Calibration_Files_Cache_File_Path + '.tmp'

    # Open the temperary cache file
    with open(Temperary_Cache_File, 'wb') as Calibration_File_Cache:
        # Save the data to the temperary cache file
        pickle.dump(Cache_Envelope, Calibration_File_Cache)

    # Rename the temperary cache file to the actual cache file
    os.replace(Temperary_Cache_File, Calibration_Files_Cache_File_Path)
    # Hide the file on Windows (dot-prefix is sufficient on macOS/Linux)
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            existing = kernel32.GetFileAttributesW(Calibration_Files_Cache_File_Path)
            if existing != 0xFFFFFFFF:
                kernel32.SetFileAttributesW(Calibration_Files_Cache_File_Path, existing | 0x02)
        except Exception:
            pass



# Find and load all calibration files from the application and user folders
def Find_And_Load_All_Calibration_Files():

    # Make a place to store the data from the calibration files
    Calibration_Files_Data = {}

    # Load application calibration files
    for File in sorted(os.listdir(Application_Calibration_Files_Folder)):
        # Make sure the file is a .calibration file
        if not File.endswith('.yaml'):
            continue

        # Get the file name by itself without the extension
        Filename = os.path.splitext(File)[0]

        # Set the path to the calibration file in the application folder
        Calibration_File_Path = os.path.join(Application_Calibration_Files_Folder, File)

        # Load the calibration file and store its data
        with open(Calibration_File_Path, 'r', encoding='utf-8') as f:
            Calibration_Files_Data[Filename] = {
                'Calibration File Contents': yaml.safe_load(f),
                'Calibration File Has Been Edited By User': False,
                'Calibration File Has Been Entered By User': False,
                'Calibration File Has Been Downloaded': False,
                'Calibration File Path': Calibration_File_Path,
            }

    # Load downloaded calibration files (synced from the EoSCalibrations branch)
        # These override the application calibration files of the same name
    for File in sorted(os.listdir(Downloaded_Calibration_Files_Folder)):
        # Make sure the file is a .calibration file
        if not File.endswith('.yaml'):
            continue

        # Get the file name by itself without the extension
        Filename = os.path.splitext(File)[0]

        # Set the path to the calibration file in the downloaded folder
        Calibration_File_Path = os.path.join(Downloaded_Calibration_Files_Folder, File)

        # Load the calibration file and store its data
        with open(Calibration_File_Path, 'r', encoding='utf-8') as f:
            Calibration_Files_Data[Filename] = {
                'Calibration File Contents': yaml.safe_load(f),
                'Calibration File Has Been Edited By User': False,
                'Calibration File Has Been Entered By User': False,
                'Calibration File Has Been Downloaded': True,
                'Calibration File Path': Calibration_File_Path,
            }

    # Load user entered calibration files
        # These override the application calibration files and downloaded calibration files of the same name
    for File in sorted(os.listdir(User_Entered_Calibration_Files_Folder)):
        # Make sure the file is a .calibration file
        if not File.endswith('.yaml'):
            continue

        # Get the file name by itself without the extension
        Filename = os.path.splitext(File)[0]

        # Set the path to the calibration file in the user entered folder
        Calibration_File_Path = os.path.join(User_Entered_Calibration_Files_Folder, File)

        # Load the calibration file and store its data
        with open(Calibration_File_Path, 'r', encoding='utf-8') as f:
            Calibration_Files_Data[Filename] = {
                'Calibration File Contents': yaml.safe_load(f),
                'Calibration File Has Been Edited By User': False,
                'Calibration File Has Been Entered By User': True,
                'Calibration File Has Been Downloaded': False,
                'Calibration File Path': Calibration_File_Path,
            }

    # Load user edited calibration files
        # These override the application calibration files and user entered calibration files of the same name
    for File in sorted(os.listdir(User_Edited_Calibration_Files_Folder)):
        # Make sure the file is a .calibration file
        if not File.endswith('.yaml'):
            continue

        # Get the file name by itself without the extension
        Filename = os.path.splitext(File)[0]

        # Set the path to the calibration file in the user edited folder
        Calibration_File_Path = os.path.join(User_Edited_Calibration_Files_Folder, File)
        
        # Load the calibration file and store its data
        with open(Calibration_File_Path, 'r', encoding='utf-8') as f:
            Calibration_Files_Data[Filename] = {
                'Calibration File Contents': yaml.safe_load(f),
                'Calibration File Has Been Edited By User': True,
                'Calibration File Has Been Entered By User': False,
                'Calibration File Has Been Downloaded': False,
                'Calibration File Path': Calibration_File_Path,
            }

    # Return the data from all the calibration files
    return Calibration_Files_Data



# Load all calibration files using the cache or by reloading all the files
def Load_All_Calibration_Files(Force_Reload=False):

    # Use the cache if it is valid, still points at real files, and a reload has not been forced
    if not Force_Reload:
        Calibration_Files_Data = Load_Valid_Calibration_Cache()
        if Calibration_Files_Data is not None:
            return Calibration_Files_Data

    # Reload all the files
    Calibration_Files_Data = Find_And_Load_All_Calibration_Files()
    # Create the cache
    Save_Calibration_Cache(Calibration_Files_Data)

    # Return the data from all the calibration files
    return Calibration_Files_Data




