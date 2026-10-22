# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy)
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
    # Load local functions from local files
from Fitting_Display_Helpers import Make_Secondary_Button, Make_Results_Table, Clear_The_Table_Selection, Fill_Result_Column, Get_All_Parameter_Names
from Fitting_Exports import Save_Figure, Save_Csv, Build_Parameters_Dataframe
from Message_Manager import Warning_Message
from Plots.Plot_Canvas import Scroll_Friendly_Canvas
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors
from Plots.Plot_Fit_Results import Plot_Fit_Results





# Create the show fit results content
class Show_Fit_Results(QWidget):
    def __init__(self, *, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Store the results being shown
        self.Fit_Results = {}

        # Create the show fit results display
        self.Create_The_Show_Fit_Results_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the show fit results section to its initial state
    def Reset(self):

        self.Fit_Results = {}
        self.Result_Table.setRowCount(0)
        self.Result_Table.setColumnCount(0)
        self.Result_Table.Fit_The_Height()
        self.Report_Text.clear()
        self.Fit_Figure.clear()
        self.Fit_Canvas.draw_idle()


    # Show the results of a fit
    def Refresh(self, *, Fit_Results, Reports, Data, Y_Label, **context):

        self.Fit_Results = Fit_Results
        self.Report_Text.setPlainText("\n".join(Reports))
        # If nothing could be fitted the reports explain why, so show them
        if not Fit_Results:
            self.Set_The_Fit_Reports_Visible(True)
        self.Update_The_Results_Table()
        # Plot the data and fitted models
        Plot_Fit_Results(self.Fit_Figure, Fit_Results, Data["Measurement"], Data["Sigma_Measurement"], Data["Pressure"], Data["Sigma_Pressure"], Y_Label)
        self.Fit_Canvas.draw_idle()



    # Create the show fit results display
    def Create_The_Show_Fit_Results_Display(self):

        # Create the show fit results display
        self.setObjectName("CollapsibleContent")
        Show_Fit_Results_Display = QVBoxLayout(self)
        Show_Fit_Results_Display.setContentsMargins(5, 5, 5, 5)
        Show_Fit_Results_Display.setSpacing(8)

        # Create the show fit results layout
        self.Show_Fit_Results_Layout = QWidget()
        self.Show_Fit_Results_Layout.setObjectName("CollapsibleSubContainer")
        Show_Fit_Results_Layout = QVBoxLayout(self.Show_Fit_Results_Layout)
        Show_Fit_Results_Layout.setContentsMargins(0, 0, 0, 0)
        Show_Fit_Results_Layout.setSpacing(8)
        Show_Fit_Results_Display.addWidget(self.Show_Fit_Results_Layout)

        # Create the parameter table, which grows to show every row without scrolling
        self.Result_Table = Make_Results_Table()
        Show_Fit_Results_Layout.addWidget(self.Result_Table)

        # Create the figure of pressure vs the measurement
        self.Fit_Figure = Figure(figsize=(6, 4), facecolor=Get_Fitting_Plot_Colors()["Background"])
        self.Fit_Canvas = Scroll_Friendly_Canvas(self.Fit_Figure)
        self.Fit_Canvas.setMinimumHeight(300)
        Show_Fit_Results_Layout.addWidget(self.Fit_Canvas)

        # Create the save buttons
        Save_Button_Layout = QHBoxLayout()
        Save_Button_Layout.addStretch()
        self.Save_Csv_Button = Make_Secondary_Button("Save CSV")
        Save_Button_Layout.addWidget(self.Save_Csv_Button)
        self.Save_Figure_Button = Make_Secondary_Button("Save Figure")
        Save_Button_Layout.addWidget(self.Save_Figure_Button)
        Save_Button_Layout.addStretch()
        Show_Fit_Results_Layout.addLayout(Save_Button_Layout)

        # Create the detailed fit reports, which are hidden until the user asks for them
        self.Report_Button = Make_Secondary_Button("Show Detailed Fit Reports ▼")
        Show_Fit_Results_Layout.addWidget(self.Report_Button, alignment=Qt.AlignHCenter)
        self.Report_Text = QTextEdit()
        self.Report_Text.setObjectName("TextEdit")
        self.Report_Text.setReadOnly(True)
        self.Report_Text.setMinimumHeight(100)
        self.Report_Text.setVisible(False)
        Show_Fit_Results_Layout.addWidget(self.Report_Text)

        # Create the continue button
        self.Continue_Button = QPushButton("Continue")
        self.Continue_Button.setObjectName("Primary_Button")
        self.Continue_Button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Continue_Button.setFixedHeight(32)
        # Show or hide the continue button based on the Show_Continue_Button flag
        if self.Show_Continue_Button:
            self.Continue_Button.show()
        else:
            self.Continue_Button.hide()
        Show_Fit_Results_Layout.addWidget(self.Continue_Button)



    # Connect the buttons to their functions
    def Connect_Signals(self):

        self.Save_Csv_Button.clicked.connect(self.When_Save_Csv_Is_Clicked)
        self.Save_Figure_Button.clicked.connect(self.When_Save_Figure_Is_Clicked)
        self.Report_Button.clicked.connect(self.Show_Or_Hide_The_Fit_Reports)
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)



    # Fill the parameter comparison table with one column per model
    def Update_The_Results_Table(self):

        if not self.Fit_Results:
            return
        All_Parameters = Get_All_Parameter_Names(self.Fit_Results)
        Model_Names = list(self.Fit_Results.keys())
        Extra_Rows = ["Reduced χ²", "R²"]
        self.Result_Table.setRowCount(len(All_Parameters) + len(Extra_Rows))
        self.Result_Table.setColumnCount(len(Model_Names))
        self.Result_Table.setHorizontalHeaderLabels(Model_Names)
        self.Result_Table.setVerticalHeaderLabels(All_Parameters + Extra_Rows)
        for Column, Model_Name in enumerate(Model_Names):
            Model_Fit = self.Fit_Results[Model_Name]
            Fill_Result_Column(self.Result_Table, Column, All_Parameters, Model_Fit["result"], Model_Fit.get("param_stderr") or {})
        Clear_The_Table_Selection(self.Result_Table)
        self.Result_Table.Fit_To_The_Contents()


    # Show or hide the detailed fit reports
    def Show_Or_Hide_The_Fit_Reports(self):

        Show_Reports = not self.Report_Text.isVisible()
        self.Report_Text.setVisible(Show_Reports)
        self.Report_Button.setText("Hide Detailed Fit Reports ▲" if Show_Reports else "Show Detailed Fit Reports ▼")


    # Save the table of fitted parameters
    def When_Save_Csv_Is_Clicked(self):

        if not self.Fit_Results:
            Warning_Message(self, "Fitting Nothing To Export", message="Run a fit first.")
            return
        try:
            Save_Csv(self, Build_Parameters_Dataframe(self.Fit_Results), "Save Parameters CSV", "fit_parameters.csv")
        except Exception as Error:
            Warning_Message(self, "Save File Error", error=str(Error))


    # Save the fit figure
    def When_Save_Figure_Is_Clicked(self):

        if not self.Fit_Results:
            Warning_Message(self, "Fitting Nothing To Export", message="Run a fit first.")
            return
        Save_Figure(self, self.Fit_Figure, "Save Fit Figure", "fit_figure.png")


    # When the continue button is clicked, send out the results through the callback
    def When_The_Continue_Button_Is_Clicked(self):

        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Fit_Results)
