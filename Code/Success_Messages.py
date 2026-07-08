List_Of_Success_Messages = {

    ########################################
    # View, Edit, and Save Calibration File Success Messages
    ########################################

    "Saved Edited Calibration": {
        "Title": "Saved",
        "Message": "Changes saved to:\n{save_path}\n\nOriginal preserved at:\n{original_path}",
    },

    "Saved New Calibration": {
        "Title": "Saved",
        "Message": "New calibration saved to:\n{save_path}",
    },

    "Calibration Update Complete": {
        "Title": "Calibration Update Complete",
        "Message": "{count} calibration file(s) downloaded successfully.",
    },

    "No Calibration Updates Available": {
        "Title": "No Calibration Updates Available",
        "Message": "Your calibration files are already up to date.",
    },


    ########################################
    # Check For Updates Success Messages
    ########################################

    "No Update Available": {
        "Title": "No Update Available",
        "Message": "You already have the latest version ({current_version}).",
    },


    ########################################
    # Batch Export Success Messages
    ########################################

    "Batch Export Complete": {
        "Title": "Batch Export Complete",
        "Message": "Successfully exported {task_count} combination(s).",
    },


    ########################################
    # CSV Export Success Messages
    ########################################

    "CSV Save Success": {
        "Title": "Save Successful",
        "Message": "Data saved to {filename}\n\nSolved pressures saved to {pressures_filename}",
    },

    "CSV Save Success Without Solved Pressures": {
        "Title": "Save Successful",
        "Message": "Data saved to {filename}",
    },

    "Pressure-Units Save Success": {
        "Title": "Save Successful",
        "Message": "Data saved to {filename}",
    },

    "Mac Terminal Commands Installed": {
        "Title": "Terminal Commands Installed",
        "Message": "The terminal commands were installed successfully. Open a new Terminal window to use them.",
    },
}


# Get a list of all success message keys
def Get_All_Success_Message_Keys():
    return tuple(List_Of_Success_Messages.keys())


# Get a success message by the success key
def Get_Success_Message(Success_Key, **Format_Values):

    try:
        Success_Definition = List_Of_Success_Messages[Success_Key]
    except KeyError as Error:
        raise KeyError(f"Unknown success message key: {Success_Key}") from Error
    try:
        Message_Text = Success_Definition["Message"].format(**Format_Values)
    except KeyError as Error:
        Missing_Field = Error.args[0]
        raise KeyError(f"Missing format value '{Missing_Field}' for success message key: {Success_Key}") from Error

    # Return the success message contents
    return {"Key": Success_Key, "Title": Success_Definition["Title"], "Message": Message_Text}


__all__ = ["List_Of_Success_Messages", "Get_All_Success_Message_Keys", "Get_Success_Message"]
