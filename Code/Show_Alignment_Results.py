# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton)
from matplotlib.figure import Figure
    # Load local functions from local files
from Fitting_Display_Helpers import Make_Secondary_Button, Make_Results_Table, Clear_The_Table_Selection, Fill_Result_Column, Get_All_Parameter_Names
from Fitting_Exports import Save_Figure, Save_Csv, Build_Alignment_Dataframe
from Message_Manager import Warning_Message
from Plots.Plot_Canvas import Scroll_Friendly_Canvas
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors
from Plots.Plot_Alignment_Results import Plot_Aligned_Study, Plot_Alignment_Summary





# Create the show alignment results content
class Show_Alignment_Results(QWidget):
    def __init__(self, *, Parent=None):
        super().__init__(Parent)

        # Store the results being shown
        self.Fit_Results = {}
        self.Aligned_Results = {}
        self.Study_Label_Map = {}
        self.Summary_Figure = None
        # Keep the figures and canvases alive while they are displayed
        self.Figure_References = []

        # Create the show alignment results display
        self.Create_The_Show_Alignment_Results_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the show alignment results section to its initial state
    def Reset(self):

        self.Fit_Results = {}
        self.Aligned_Results = {}
        self.Study_Label_Map = {}
        self.Result_Table.setRowCount(0)
        self.Result_Table.setColumnCount(0)
        self.Result_Table.Fit_The_Height()
        self.Clear_The_Figures()


    # Show the original and aligned fits
    def Refresh(self, *, Fit_Results, Aligned_Results, Study_Label_Map, Data, Y_Label, **context):

        self.Fit_Results = Fit_Results
        self.Aligned_Results = Aligned_Results
        self.Study_Label_Map = Study_Label_Map
        self.Update_The_Results_Table()
        self.Update_The_Figures(Data["Measurement"], Data["Sigma_Measurement"], Y_Label)



    # Create the show alignment results display
    def Create_The_Show_Alignment_Results_Display(self):

        # Create the show alignment results display
        self.setObjectName("CollapsibleContent")
        Show_Alignment_Results_Display = QVBoxLayout(self)
        Show_Alignment_Results_Display.setContentsMargins(5, 5, 5, 5)
        Show_Alignment_Results_Display.setSpacing(8)

        # Create the show alignment results layout
        self.Show_Alignment_Results_Layout = QWidget()
        self.Show_Alignment_Results_Layout.setObjectName("CollapsibleSubContainer")
        Show_Alignment_Results_Layout = QVBoxLayout(self.Show_Alignment_Results_Layout)
        Show_Alignment_Results_Layout.setContentsMargins(0, 0, 0, 0)
        Show_Alignment_Results_Layout.setSpacing(8)
        Show_Alignment_Results_Display.addWidget(self.Show_Alignment_Results_Layout)

        # Create the parameter table, which grows to show every row without scrolling
        self.Result_Table = Make_Results_Table()
        Show_Alignment_Results_Layout.addWidget(self.Result_Table)

        # Create the place for one figure per study and a summary figure
        self.Figures_Widget = QWidget()
        self.Figures_Widget.setObjectName("CollapsibleSubContainer")
        self.Figures_Layout = QVBoxLayout(self.Figures_Widget)
        self.Figures_Layout.setSpacing(16)
        self.Figures_Layout.setContentsMargins(0, 0, 0, 0)
        Show_Alignment_Results_Layout.addWidget(self.Figures_Widget)

        # Create the save buttons
        Save_Button_Layout = QHBoxLayout()
        Save_Button_Layout.addStretch()
        self.Save_Csv_Button = Make_Secondary_Button("Save CSV")
        Save_Button_Layout.addWidget(self.Save_Csv_Button)
        self.Save_Figure_Button = Make_Secondary_Button("Save Figure")
        Save_Button_Layout.addWidget(self.Save_Figure_Button)
        Save_Button_Layout.addStretch()
        Show_Alignment_Results_Layout.addLayout(Save_Button_Layout)



    # Connect the buttons to their functions
    def Connect_Signals(self):

        self.Save_Csv_Button.clicked.connect(self.When_Save_Csv_Is_Clicked)
        self.Save_Figure_Button.clicked.connect(self.When_Save_Figure_Is_Clicked)



    # Fill the table with the original fits followed by the fits aligned to each study
    def Update_The_Results_Table(self):

        if not self.Aligned_Results:
            return
        Model_Names = list(self.Fit_Results.keys())
        All_Parameters = Get_All_Parameter_Names(self.Fit_Results)

        # Build the column headers
        Column_Headers = [f"Original\n{Model_Name}" for Model_Name in Model_Names]
        for Target_Label in self.Aligned_Results.keys():
            # Use the first two pipe separated segments for the header (Author | Material)
            Parts = [Part.strip() for Part in self.Study_Label_Map.get(Target_Label, Target_Label).split("|")]
            Short_Label = " | ".join(Parts[:2]) if len(Parts) >= 2 else Parts[0]
            for Model_Name in Model_Names:
                Column_Headers.append(f"{Short_Label}\n{Model_Name}")

        # Set up the table
        Row_Labels = All_Parameters + ["Reduced χ²", "R²"]
        self.Result_Table.setRowCount(len(Row_Labels))
        self.Result_Table.setColumnCount(len(Column_Headers))
        self.Result_Table.setHorizontalHeaderLabels(Column_Headers)
        self.Result_Table.setVerticalHeaderLabels(Row_Labels)

        # Fill the original fits
        for Column, Model_Name in enumerate(Model_Names):
            Model_Fit = self.Fit_Results[Model_Name]
            Fill_Result_Column(self.Result_Table, Column, All_Parameters, Model_Fit["result"], Model_Fit.get("param_stderr") or {})
        # Fill the aligned fits
        for Study_Index, Target_Label in enumerate(self.Aligned_Results.keys()):
            Aligned_Model_Results = self.Aligned_Results[Target_Label]["model_results"]
            for Model_Index, Model_Name in enumerate(Model_Names):
                if Model_Name not in Aligned_Model_Results:
                    continue
                Column = len(Model_Names) + Study_Index * len(Model_Names) + Model_Index
                Aligned_Fit = Aligned_Model_Results[Model_Name]
                Fill_Result_Column(self.Result_Table, Column, All_Parameters, Aligned_Fit["result"], Aligned_Fit.get("param_stderr") or {})

        Clear_The_Table_Selection(self.Result_Table)
        self.Result_Table.Fit_To_The_Contents()



    # Remove the old figures
    def Clear_The_Figures(self):

        for Index in reversed(range(self.Figures_Layout.count())):
            Item = self.Figures_Layout.takeAt(Index)
            if Item and Item.widget():
                Item.widget().deleteLater()
        self.Figure_References = []
        self.Summary_Figure = None


    # Add a figure to the display
    def Add_A_Figure(self, Figure_To_Add):

        Canvas = Scroll_Friendly_Canvas(Figure_To_Add)
        Canvas.setMinimumHeight(380)
        self.Figures_Layout.addWidget(Canvas)
        self.Figure_References.append((Figure_To_Add, Canvas))
        Canvas.draw_idle()


    # Draw one figure per study and a summary figure of all the fits
    def Update_The_Figures(self, Measurement, Sigma_Measurement, Y_Label):

        self.Clear_The_Figures()
        Model_Names = list(self.Fit_Results.keys())
        Background = Get_Fitting_Plot_Colors()["Background"]

        # Draw the aligned data and fits for each study
        for Study_Index, (Target_Label, Aligned_Entry) in enumerate(self.Aligned_Results.items()):
            Study_Figure = Figure(figsize=(7, 4.5), facecolor=Background)
            Plot_Aligned_Study(Study_Figure, self.Study_Label_Map.get(Target_Label, Target_Label), Study_Index, Aligned_Entry, Model_Names, Measurement, Sigma_Measurement, Y_Label)
            self.Add_A_Figure(Study_Figure)

        # Draw the summary of every fit
        self.Summary_Figure = Figure(figsize=(7, 4.5), facecolor=Background)
        Plot_Alignment_Summary(self.Summary_Figure, self.Fit_Results, self.Aligned_Results, self.Study_Label_Map, Model_Names, Y_Label)
        self.Add_A_Figure(self.Summary_Figure)



    # Save the table of original and aligned fits
    def When_Save_Csv_Is_Clicked(self):

        if not self.Aligned_Results:
            Warning_Message(self, "Fitting Nothing To Export", message="Run alignment first.")
            return
        try:
            Save_Csv(self, Build_Alignment_Dataframe(self.Fit_Results, self.Aligned_Results, self.Study_Label_Map), "Save Alignment CSV", "alignment_results.csv")
        except Exception as Error:
            Warning_Message(self, "Save File Error", error=str(Error))


    # Save the summary figure
    def When_Save_Figure_Is_Clicked(self):

        if self.Summary_Figure is None:
            Warning_Message(self, "Fitting Nothing To Export", message="Run alignment first.")
            return
        Save_Figure(self, self.Summary_Figure, "Save Alignment Figure", "alignment_figure.png")
