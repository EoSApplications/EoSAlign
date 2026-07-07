# Load libraries
    # Load standard libraries
import os
import sys
    # Load third-party libraries
try:
    import dill
except ImportError:
    # In the browser (Pyodide) dill is not worth installing over the network just for
    # this: the cache it pickles lives on disk, which is meaningless in the browser's
    # ephemeral virtual filesystem anyway. Every dill call below already runs inside a
    # broad try/except that falls back to a full rebuild, so leaving dill as None here
    # is enough to make caching a no-op instead of a hard failure.
    dill = None
    # Load local libraries
from .Load_Calibration_Files import *
from .Parse_Calibration_Information import *





# Find the path to the calibration cache file
Calibration_Cache_File_Name = '.Calibration_Cache.pkl'
Calibration_Build_Cache_File_Path = os.path.join(User_Application_Data_Folder, Calibration_Cache_File_Name)



# Check whether the calibration cache is still valid
def Check_If_Calibration_Cache_Is_Valid():

    # Check if the calibration cache file exists
    if not os.path.exists(Calibration_Build_Cache_File_Path):
        # If the calibration cache file does not exist then it is not valid
        return False
    # Find the last time the calibration cache file was modified
    Cache_File_Modified_Time = os.path.getmtime(Calibration_Build_Cache_File_Path)
    # Find the most recent modification times for calibration files and yaml folders
    Latest_Calibration_File_Modified_Time = Check_For_Calibration_File_Changes()
    Latest_Calibration_Folder_Modified_Time = Check_For_Calibration_Folder_Changes()
    # Check if any calibration file or calibration folder was modified after the cache file
    if Latest_Calibration_File_Modified_Time > Cache_File_Modified_Time or Latest_Calibration_Folder_Modified_Time > Cache_File_Modified_Time:
        # Then the cache is out of date
        return False

    # The cache file exists and is newer than all calibration sources
    return True



# Delete the current calibration cache file so it will be rebuilt
def Delete_Current_Calibration_Cache():

    # Try to delete the cache file
    try:
        os.remove(Calibration_Build_Cache_File_Path)
    except FileNotFoundError:
        # If the cache file does not exist then there is nothing to delete
        pass



# Load calibration data from the cache file
def Load_Calibration_Cache():

    # Open the cache file and load the stored data
    with open(Calibration_Build_Cache_File_Path, 'rb') as Calibration_Cache_File:
        # Return the loaded cache data
        return dill.load(Calibration_Cache_File)



# Check that every calibration file path recorded in cached metadata still exists on disk
def Check_If_Calibration_Metadata_File_Paths_Still_Exist(Calibration_Metadata):
    return all(
        os.path.exists(Entry['file_path'])
        for Entry in Calibration_Metadata.values()
        if Entry.get('file_path')
    )



# Save calibration data to the cache file
def Save_Calibration_Cache(Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods):

    # Try to write the cache file
    try:
        # Make sure the application data folder exists
        os.makedirs(User_Application_Data_Folder, exist_ok=True)
        # Create a temporary cache file path for atomic replace
        Temporary_Cache_File_Path = Calibration_Build_Cache_File_Path + '.tmp'
        # Write all calibration cache information to the temporary cache file
        with open(Temporary_Cache_File_Path, 'wb') as Cache_File:
            dill.dump({'Folder_Fingerprint': Get_Calibration_Folders_Fingerprint(), 'Application_Version': Get_Current_Application_Version_For_Cache(), 'Calibration_List': Calibration_List, 'Label_To_Entry': Label_To_Entry, 'Calibration_Metadata': Calibration_Metadata, 'Calibration_Functions': Calibration_Functions, 'All_Compositions': All_Compositions, 'All_Methods': All_Methods,}, Cache_File)
        # Replace the old cache file with the new cache file
        os.replace(Temporary_Cache_File_Path, Calibration_Build_Cache_File_Path)
        # Hide the file on Windows
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                existing = kernel32.GetFileAttributesW(Calibration_Build_Cache_File_Path)
                if existing != 0xFFFFFFFF:
                    kernel32.SetFileAttributesW(Calibration_Build_Cache_File_Path, existing | 0x02)
            except Exception:
                pass
        print('[Calibration Cache] Cache saved.')
    except Exception as exc:
        # If writing fails send a warning and continue without cache persistence
        print(f"[Calibration Cache] Warning: could not write cache - {exc}")



# Load all calibration data, using cache when valid
def Load_All_Calibrations(Force_Rebuild=False):

    # Check if a rebuild was not requested and the cache is valid
    if not Force_Rebuild and Check_If_Calibration_Cache_Is_Valid():
        # Try loading from the cache file
        try:
            Cache_Data = Load_Calibration_Cache()

            # Reject a cache built from a different folder location (e.g. a relocated
            # source checkout) even though its mtimes look fresh
            if Cache_Data.get('Folder_Fingerprint') != Get_Calibration_Folders_Fingerprint():
                raise ValueError('Calibration folder location changed since this cache was built')

            # Reject a cache built under a different application version - Calibration_Functions
            # holds dill-pickled closures built by the equation-parsing code, which can change
            # between versions even when no calibration file or folder has changed, so an update
            # must always rebuild once rather than silently keep serving the old cached closures
            if Cache_Data.get('Application_Version') != Get_Current_Application_Version_For_Cache():
                raise ValueError('Application version changed since this cache was built')

            # Get all calibration information from the loaded cache data
            Calibration_List = Cache_Data.get('Calibration_List', [])
            Label_To_Entry = Cache_Data.get('Label_To_Entry')
            Calibration_Metadata = Cache_Data.get('Calibration_Metadata', {})
            Calibration_Functions = Cache_Data.get('Calibration_Functions', {})
            All_Compositions = Cache_Data.get('All_Compositions', [])
            All_Methods = Cache_Data.get('All_Methods', [])

            # Reject a cache whose recorded file paths have since moved or been deleted
            if not Check_If_Calibration_Metadata_File_Paths_Still_Exist(Calibration_Metadata):
                raise ValueError('Cached calibration file paths no longer exist')

            # Rebuild Label_To_Entry if this cache file does not have it
            if Label_To_Entry is None:
                Label_To_Entry = {Calibration_Key: Calibration_Entry for Calibration_Key, Calibration_Entry in Calibration_List}

            print('[Calibration Cache] Calibrations loaded from cache.')
            # Return the loaded cache data
            return (Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods)
        except Exception as exc:
            # If cache loading fails then fall back to full rebuild
            print(f"[Calibration Cache] Cache invalid ({exc}), rebuilding...")

    # Load calibration files and build all calibrations from scratch
    Calibration_Files_Data = Load_All_Calibration_Files(Force_Reload=Force_Rebuild)
    Calibration_List, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods = Build_All_Calibrations(Calibration_Files_Data)
    # Build a label to entry lookup from the calibration list
    Label_To_Entry = {Calibration_Key: Calibration_Entry for Calibration_Key, Calibration_Entry in Calibration_List}
    # Save the rebuilt data to the cache file
    Save_Calibration_Cache(Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods)

    # Return the built calibration data
    return (Calibration_List, Label_To_Entry, Calibration_Metadata, Calibration_Functions, All_Compositions, All_Methods)



# Force a full calibration reload from calibration files
    # This should be called after user-entered or user-edited calibration changes
def Reload_Calibrations():

    # Force a full rebuild of the calibration cache and return the new data
    return Load_All_Calibrations(Force_Rebuild=True)




