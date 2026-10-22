# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy)
from matplotlib.figure import Figure
    # Load local functions from local files
from Collapsible_Sections import Dropdown
from Fitting_Display_Helpers import Make_Secondary_Button
from Fitting_Exports import Save_Figure
from Message_Manager import Warning_Message
from Plots.Plot_Canvas import Scroll_Friendly_Canvas
from Plots.Plot_Fitting_Common import Get_Fitting_Plot_Colors
from Plots.Plot_Covariance_Ellipses import Get_Parameter_Pairs, Plot_Covariance_Ellipses





# Create the show covariance ellipses content
class Show_Covariance_Ellipses(QWidget):
    def __init__(self, *, Once_A_Change_Is_Made=None, Show_Continue_Button=False, Parent=None):
        super().__init__(Parent)

        # Store the input parameters
        self.Once_A_Change_Is_Made = Once_A_Change_Is_Made
        self.Show_Continue_Button = Show_Continue_Button

        # Store the results being shown
        self.Fit_Results = {}

        # Create the show covariance ellipses display
        self.Create_The_Show_Covariance_Ellipses_Display()

        # Connect the signals
        self.Connect_Signals()



    # Reset the show covariance ellipses section to its initial state
    def Reset(self):

        self.Fit_Results = {}
        self.Pair_Dropdown_Display.blockSignals(True)
        self.Pair_Dropdown_Display.clear()
        self.Pair_Dropdown_Display.blockSignals(False)
        self.Update_The_Plot()


    # Show the covariance of the fitted models
    def Refresh(self, *, Fit_Results, **context):

        self.Fit_Results = Fit_Results
        # Rebuild the dropdown of parameter pairs without drawing for every item added
        self.Pair_Dropdown_Display.blockSignals(True)
        self.Pair_Dropdown_Display.clear()
        for Parameter_A, Parameter_B in Get_Parameter_Pairs(Fit_Results):
            self.Pair_Dropdown_Display.addItem(f"{Parameter_A}  vs  {Parameter_B}", (Parameter_A, Parameter_B))
        self.Pair_Dropdown_Display.blockSignals(False)
        self.Update_The_Plot()



    # Create the show covariance ellipses display
    def Create_The_Show_Covariance_Ellipses_Display(self):

        # Create the show covariance ellipses display
        self.setObjectName("CollapsibleContent")
        Show_Covariance_Ellipses_Display = QVBoxLayout(self)
        Show_Covariance_Ellipses_Display.setContentsMargins(5, 5, 5, 5)
        Show_Covariance_Ellipses_Display.setSpacing(8)

        # Create the show covariance ellipses layout
        self.Show_Covariance_Ellipses_Layout = QWidget()
        self.Show_Covariance_Ellipses_Layout.setObjectName("CollapsibleSubContainer")
        Show_Covariance_Ellipses_Layout = QVBoxLayout(self.Show_Covariance_Ellipses_Layout)
        Show_Covariance_Ellipses_Layout.setContentsMargins(0, 0, 0, 0)
        Show_Covariance_Ellipses_Layout.setSpacing(8)
        Show_Covariance_Ellipses_Display.addWidget(self.Show_Covariance_Ellipses_Layout)

        # Create the dropdown for selecting the parameter pair
        Pair_Dropdown_Layout = QHBoxLayout()
        Pair_Label = QLabel("Parameter pair:")
        Pair_Label.setObjectName("CollapsibleContentLabel")
        Pair_Dropdown_Layout.addWidget(Pair_Label)
        self.Pair_Dropdown_Display = Dropdown()
        self.Pair_Dropdown_Display.setObjectName("Dropdown")
        Pair_Dropdown_Layout.addWidget(self.Pair_Dropdown_Display, stretch=1)
        Show_Covariance_Ellipses_Layout.addLayout(Pair_Dropdown_Layout)

        # Create the figure of the ellipses
        self.Covariance_Figure = Figure(figsize=(6, 4), facecolor=Get_Fitting_Plot_Colors()["Background"])
        self.Covariance_Canvas = Scroll_Friendly_Canvas(self.Covariance_Figure)
        self.Covariance_Canvas.setMinimumHeight(320)
        Show_Covariance_Ellipses_Layout.addWidget(self.Covariance_Canvas)

        # Create the save button
        Save_Button_Layout = QHBoxLayout()
        Save_Button_Layout.addStretch()
        self.Save_Figure_Button = Make_Secondary_Button("Save Figure")
        Save_Button_Layout.addWidget(self.Save_Figure_Button)
        Save_Button_Layout.addStretch()
        Show_Covariance_Ellipses_Layout.addLayout(Save_Button_Layout)

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
        Show_Covariance_Ellipses_Layout.addWidget(self.Continue_Button)



    # Connect the dropdown and buttons to their functions
    def Connect_Signals(self):

        self.Pair_Dropdown_Display.currentIndexChanged.connect(self.Update_The_Plot)
        self.Save_Figure_Button.clicked.connect(self.When_Save_Figure_Is_Clicked)
        self.Continue_Button.clicked.connect(self.When_The_Continue_Button_Is_Clicked)



    # Draw the ellipses for the selected parameter pair
    def Update_The_Plot(self):

        Plot_Covariance_Ellipses(self.Covariance_Figure, self.Fit_Results, self.Pair_Dropdown_Display.currentData())
        self.Covariance_Canvas.draw_idle()


    # Save the covariance figure
    def When_Save_Figure_Is_Clicked(self):

        if self.Pair_Dropdown_Display.currentData() is None or not self.Fit_Results:
            Warning_Message(self, "Fitting Nothing To Export", message="Run a fit first.")
            return
        Save_Figure(self, self.Covariance_Figure, "Save Covariance Figure", "covariance_ellipses.png")


    # When the continue button is clicked, send out the results through the callback
    def When_The_Continue_Button_Is_Clicked(self):

        if self.Once_A_Change_Is_Made:
            self.Once_A_Change_Is_Made(self.Fit_Results)
