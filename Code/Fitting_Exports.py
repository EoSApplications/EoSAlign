# Load libraries
    # Load standard libraries
import os





# The save dialogs and messages are the only parts of this file that need Qt, so Qt is loaded inside them
# and the tables of results (Build_Parameters_Dataframe and Build_Alignment_Dataframe) can be used without it (the website)



# Get the folder the save dialogs start in (the Desktop, or the home folder if there is no Desktop)
def Get_The_Default_Export_Directory():

    Home_Directory = os.path.expanduser("~")
    Desktop_Directory = os.path.join(Home_Directory, "Desktop")
    if os.path.isdir(Desktop_Directory):
        return Desktop_Directory
    return Home_Directory



# Ask where to save a figure and save it as a PNG
def Save_Figure(Parent, Figure, Dialog_Title, Default_Name="figure.png"):

    from PySide6.QtWidgets import QFileDialog
    from Message_Manager import Warning_Message, Success_Message

    Default_Filename = os.path.join(Get_The_Default_Export_Directory(), Default_Name)
    Filename, _ = QFileDialog.getSaveFileName(Parent, Dialog_Title, Default_Filename, "PNG Image (*.png);;All Files (*)")
    if not Filename:
        return
    if not Filename.lower().endswith(".png"):
        Filename += ".png"
    try:
        Figure.savefig(Filename, dpi=150, bbox_inches="tight", facecolor=Figure.get_facecolor())
        Success_Message(Parent, "Fitting Figure Save Success", filename=Filename)
    except Exception as Error:
        Warning_Message(Parent, "Save File Error", error=str(Error))



# Ask where to save a table and save it as a CSV
def Save_Csv(Parent, Dataframe, Dialog_Title, Default_Name="results.csv"):

    from PySide6.QtWidgets import QFileDialog
    from Message_Manager import Warning_Message, Success_Message

    Default_Filename = os.path.join(Get_The_Default_Export_Directory(), Default_Name)
    Filename, _ = QFileDialog.getSaveFileName(Parent, Dialog_Title, Default_Filename, "CSV Files (*.csv)")
    if not Filename:
        return
    if not Filename.lower().endswith(".csv"):
        Filename += ".csv"
    try:
        Dataframe.to_csv(Filename, index=False, encoding="utf-8-sig")
        Success_Message(Parent, "Fitting CSV Save Success", filename=Filename)
    except Exception as Error:
        Warning_Message(Parent, "Save File Error", error=str(Error))



# Build the table of fitted parameters, one row per model
def Build_Parameters_Dataframe(Fit_Results):

    import pandas as pd

    Rows = []
    for Model_Name, Model_Fit in Fit_Results.items():
        Result = Model_Fit["result"]
        Stderr_Map = Model_Fit.get("param_stderr") or {}
        Row = {"Model": Model_Name}
        for Parameter_Name, Parameter in Result.params.items():
            Stderr = Stderr_Map.get(Parameter_Name, Parameter.stderr)
            Row[Parameter_Name] = Parameter.value
            Row[f"{Parameter_Name}_stderr"] = Stderr if Stderr else 0.0
        Row["chi_sq"] = Result.chisqr
        Row["redchi"] = Result.redchi
        Rows.append(Row)

    return pd.DataFrame(Rows)



# Build the table of original and aligned fits with separate value and stderr columns plus the goodness of fit
def Build_Alignment_Dataframe(Fit_Results, Aligned_Results, Study_Label_Map):

    import pandas as pd

    # Build one row from one model's fit
    def Build_Row(Group, Study, Model_Name, Model_Fit):
        Result = Model_Fit["result"]
        Stderr_Map = Model_Fit.get("param_stderr") or {}
        Row = {"Group": Group, "Study": Study, "Model": Model_Name}
        for Parameter_Name, Parameter in Result.params.items():
            Stderr = Stderr_Map.get(Parameter_Name, Parameter.stderr)
            Row[f"{Parameter_Name}_value"] = Parameter.value
            Row[f"{Parameter_Name}_stderr"] = Stderr if Stderr is not None else ""
        Row["chi2_per_N"] = Result.redchi
        Row["R2"] = Result.rsquared
        return Row

    Rows = []
    # Original fits
    for Model_Name, Model_Fit in Fit_Results.items():
        Rows.append(Build_Row("Original", "", Model_Name, Model_Fit))
    # Aligned fits
    for Target_Label, Aligned_Entry in Aligned_Results.items():
        Study_Label = Study_Label_Map.get(Target_Label, Target_Label)
        for Model_Name in Fit_Results.keys():
            if Model_Name in Aligned_Entry["model_results"]:
                Rows.append(Build_Row("Aligned", Study_Label, Model_Name, Aligned_Entry["model_results"][Model_Name]))

    return pd.DataFrame(Rows)
