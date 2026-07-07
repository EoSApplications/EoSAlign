




List_Of_Warning_Messages = {



    ########################################
    # Check For Updates Warnings
    ########################################


    "Update Available": {
        "Title": "Update Available",
        "Message": "Version {version} is available (you have {current_version}).<br><br>Download it from GitHub:<br><a href=\"{release_url}\">{release_url}</a>",
    },

    "Update Available Pip Install": {
        "Title": "Update Available",
        "Message": "Version {version} is available (you have {current_version}).<br><br>Run the following command to update:<br><br>&nbsp;&nbsp;&nbsp;&nbsp;pip install --upgrade eosapplications<br><br>Release notes:<br><a href=\"{release_url}\">{release_url}</a>",
    },

    "Failed to Update Calibrations": {
        "Title": "Failed to Update Calibrations",
        "Message": "The calibration files could not be downloaded:\n{message}",
    },

    "Install Mac Terminal Commands": {
        "Title": "Install Terminal Commands",
        "Message": "Install terminal commands for this application?\n\nThis will place launcher commands in /usr/local/bin so they work in Terminal.\nmacOS will ask for administrator permission.\n\n{command_list}",
    },

    "Terminal Command Install Failed": {
        "Title": "Terminal Command Install Failed",
        "Message": "The terminal commands could not be installed.",
    },



    ########################################
    # Menu Bar Warnings
    ########################################


    "Application Not Found": {
        "Title": "Application Not Found",
        "Message": "{executable_name} was not found\nMake sure the application is installed or bundled with this launcher",
    },

    "Managed Applications Need Attention": {
        "Title": "Managed Applications Need Attention",
        "Message": "{message}",
    },

    "Menu Action Not Available": {
        "Title": "Menu Action Not Available",
        "Message": "{action} is not available in this window",
    },



    ########################################
    # Enter Data Warnings
    ########################################


    "Could Not Read The Entered Data File": {
        "Title": "Could Not Read The Entered Data File",
        "Message": "Could not read the uploaded file:\n{error}",
    },

    "Could Not Read The Entered Uncertainty File": {
        "Title": "Could Not Read The Entered Uncertainty File",
        "Message": "Could not read the uploaded uncertainty file:\n{error}",
    },

    "Missing Data Entry Method": {
        "Title": "Missing Data Entry Method",
        "Message": "Please select a data entry method:\n\t- Manual Entry: type your values into the provided text box\n\t- Upload File: load values from an existing file"
    },

    "Missing Data Values": {
        "Title": "Missing Data Values",
        "Message": "No numeric values were found.\n\tPlease enter at least one value",
    },

    "Missing Units Selection": {
        "Title": "Missing Units Selection",
        "Message": "Please select the units for the data values",
    },

    "Missing Volume Units Selection": {
        "Title": "Missing Volume Units Selection",
        "Message": "The data units are volume but no volume units were selected\n\tPlease select a specific volume unit"
    },

    "Missing Uncertainty Values": {
        "Title": "Missing Uncertantly Values",
        "Message": "Error propagation is enabled but no numeric uncertainty values were found\n\tPlease enter at least one uncertainty value"
    },

    "Entered Data Length And Entered Uncertanty Length Do Not Match": {
        "Title": "Entered Data Length And Entered Uncertanty Length Do Not Match",
        "Message": "The number of entered data values ({data_count}) does not match the number of entered uncertainty values ({uncertainty_count})\n\tPlease make sure the data and uncertanties have the same number of values"
    },



    ########################################
    # Select Composition Warnings
    ########################################


    "Missing Composition Selection": {
        "Title": "Missing Composition Selection",
        "Message": "Please select a composition",
    },



    ########################################
    # Select Method Warnings
    ########################################


    "Missing Method Selection": {
        "Title": "Missing Method Selection",
        "Message": "Please select a method",
    },



    ########################################
    # Select Pressure Calibration Warnings
    ########################################


    "Missing Pressure Calibration Study Selection": {
        "Title": "Missing Pressure Calibration Study Selection",
        "Message": "Please select a pressure calibration study",
    },

    "Missing Initial Pressure Calibration Study Selection": {
        "Title": "Missing Initial Pressure Calibration Study Selection",
        "Message": "Please select an initial pressure calibration study",
    },

    "Missing Pressure Calibration Study With A Different Composition And Method Selection": {
        "Title": "Missing Pressure Calibration Study With A Different Composition And Method Selection",
        "Message": "Please select a pressure calibration study with a different composition and method",
    },

    "Missing Final Pressure Calibration Study Selection": {
        "Title": "Missing Final Pressure Calibration Study Selection",
        "Message": "Please select a final pressure calibration study",
    },

    "Incomplete Pressure Calibration Selection": {
        "Title": "Incomplete Pressure Calibration Selection",
        "Message": "Please complete the pressure calibration selection before continuing",
    },



    ########################################
    # Select Studies for Comparison Warnings
    ########################################


    "Preview CSV Error": {
        "Title": "Preview CSV Error",
        "Message": "{message}",
    },

    "No Studies Selected For Preview": {
        "Title": "No Studies Selected For Preview",
        "Message": "Please select at least one study to preview",
    },

    # For All_Steps_Layout
    "Missing Composition Or Method Selection": {
        "Title": "Missing Composition Or Method Selection",
        "Message": "Please select a composition and method",
    },

    "Continue Without Studies": {
        "Title": "No Studies Selected",
        "Message": "No studies are selected for comparison. Do you want to continue anyway?",
    },



    ########################################
    # Select Final Actions Warnings
    ########################################


    # "Preview CSV Error": {
    #     "Title": "Preview CSV Error",
    #     "Message": "{message}",
    # },

    "Plot Error": {
        "Title": "Plot Error",
        "Message": "{message}",
    },

    "Plot Creation Failed": {
        "Title": "Plot Error",
        "Message": "An error occurred while creating the plot:\n{error}",
    },

    "Export Error": {
        "Title": "Export Error",
        "Message": "{message}",
    },

    "Save File Error": {
        "Title": "Save File Error",
        "Message": "Could not save file:\n{error}",
    },



    ########################################
    # View, Edit, and Save Calibration File Warnings
    ########################################


    "Could Not Load The Calibration File": {
        "Title": "Could Not Load The Calibration File",
        "Message": "Could not load the calibration file:\n\t{error}",
    },

    "Missing File Path": {
        "Title": "Missing File Path",
        "Message": "No file path specified",
    },

    "Could Not Read The Calibration File": {
        "Title": "Could Not Read The Calibration File",
        "Message": "Could not read the calibration file:\n\t{error}",
    },

    "Save Calibration Error": {
        "Title": "Save Calibration Error",
        "Message": "Could not save the calibration file:\n\t{error}",
    },

    "Missing Calibration Study Name": {
        "Title": "Missing Calibration Study Name",
        "Message": "The calibration must have a name before it can be saved",
    },

    "Missing Calibration Selection": {
        "Title": "Missing Calibration Selection",
        "Message": "Please select a calibration before previewing",
    },

    "Could Not Find The Calibration File": {
        "Title": "Could Not Find The Calibration File",
        "Message": "The calibration file could not be found",
    },



    ########################################
    # Batch Export Warnings
    ########################################


    "Export In Progress": {
        "Title": "Export In Progress",
        "Message": "Batch export is still running\nPlease wait for it to finish before closing the application",
    },

    "Error Exporting Figures": {
        "Title": "Error Exporting Figures",
        "Message": "Some figures could not be saved:\n\t{errors}",
    },

    "Nothing Ready To Export": {
        "Title": "Nothing To Export",
        "Message": "No figures are ready to export yet.",
    },

    "Export Figure Skip Or Stop": {
        "Title": "Skip or Stop?",
        "Message": "'{title}' was skipped.\n\nContinue with the remaining figures?",
    },

    # "Missing Data Values": {
    #     "Title": "Missing Data Values",
    #     "Message": "No numeric values were found.\n\tPlease enter at least one value",
    # },

    "Missing Output Folder": {
        "Title": "Missing Output Folder",
        "Message": "Please select a folder to save the exported files",
    },

    "Missing Export Data": {
        "Title": "Missing Export Data",
        "Message": "Please enter data before exporting",
    },

    # "Missing Pressure Calibration Study Selection": {
    #     "Title": "Missing Pressure Calibration Study Selection",
    #     "Message": "Please select a pressure calibration study",
    # },

    "No Studies For Comparison": {
        "Title": "No Studies For Comparison",
        "Message": "No studies are available for comparison for this combination of composition and method",
    },

    "Could Not Prepare Export": {
        "Title": "Could Not Prepare Export",
        "Message": "Could not prepare the current combination for export",
    },

    # "Export Error": {
    #     "Title": "Export Error",
    #     "Message": "There was an error during the export process:\n\t{message}",
    # },

    "Nothing To Export": {
        "Title": "Nothing To Export",
        "Message": "There are no combinations of composition and method that have any calibrations for comparison",
    },

    "Missing Math Style Selection": {
        "Title": "Missing Math Style Selection",
        "Message": "Please select at least one math style\n\t- Shorthand: use the shorthand notation for equations and explicit forward and inverse equations for each calibration\n\t- Longhand: use the longhand notation for equations and implicit forward and inverse equations for each calibration",
    },

    "Export Finished With Errors": {
        "Title": "Export Finished With Errors",
        "Message": "Exported {successful_count} of {task_count} combinations.\n\n\t{details}",
    },

    "Reset Application": {
        "Title": "Reset Application",
        "Message": "Are you sure you want to reset all entries and start over?",
    },

    "Comparison Failed": {
        "Title": "Comparison Failed",
        "Message": "The comparison could not be completed:\n\t{details}",
    },

    "Missing Comparison File Selection": {
        "Title": "Missing File Selection",
        "Message": "Please select both files before running the comparison",
    },

    "Invalid Comparison File Path": {
        "Title": "Invalid File Path",
        "Message": "One or both selected paths are not valid files",
    },

    "Units Mismatch On Recalculation": {
        "Title": "Units Mismatch",
        "Message": "The previous run used units <b>{previous_units}</b>, but the new data uses units <b>{new_units}</b>.<br><br>Recalculate requires the same unit type as the previous run (switching between different volume units is allowed). Please go back and select matching units, or start a new run.",
    },



}



# Get a list of all warning keys
def Get_All_Warning_Keys():
    return tuple(List_Of_Warning_Messages.keys())



# Get a warning message by the warning key
def Get_Warning(Warning_Key, **Format_Values):

    try:
        Warning_Definition = List_Of_Warning_Messages[Warning_Key]
    except KeyError as Error:
        raise KeyError(f"Unknown warning message key: {Warning_Key}") from Error
    try:
        Message_Text = Warning_Definition["Message"].format(**Format_Values)
    except KeyError as Error:
        Missing_Field = Error.args[0]
        raise KeyError(f"Missing format value '{Missing_Field}' for warning message key: {Warning_Key}") from Error

    # Return the warning message contents
    return {"Key": Warning_Key, "Title": Warning_Definition["Title"], "Message": Message_Text}



# 
__all__ = ["List_Of_Warning_Messages", "Get_All_Warning_Keys", "Get_Warning"]


