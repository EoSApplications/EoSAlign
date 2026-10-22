# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QMessageBox
from PySide6.QtCore import Qt
    # Load local functions from local files
from Run_Tab_Container import Step_By_Step_Layout, Run_Tab_Background, Tab_Bar_Shadow, Active_Tab_Overlay, Shadow_Blur_Radius
from EoSFitting__Step_By_Step_Layout import Fitting_Step_By_Step_Layout_Content
from Fitting_Display_Helpers import Make_Secondary_Button
from Message_Manager import Warning_Message
from Window_Show_Guard import Guard_Unwanted_Window_Shows





# The tabs for the step by step layout for EoSFitting: one tab per fit, with buttons to start a new fit and to reset everything.
# This reuses the look and the tab drawing of EoSAlign's Step_By_Step_Layout. That class builds its own first tab from EoSAlign's
# content, so it is rebuilt here with the EoSFitting content and the two buttons.
class Fitting_Step_By_Step_Layout(Step_By_Step_Layout):
    def __init__(self):
        # Skip Step_By_Step_Layout.__init__ so no EoSAlign content is built
        QWidget.__init__(self)

        self.Runs = []
        self.Tab_Buttons = []
        self.Inactive_Connectors = []

        # Tab button row: the tabs on the left, then the new fit and reset buttons on the right
        self.Tab_Row = QWidget()
        self.Tab_Row.setObjectName("RunTabRow")
        self.Tab_Row.setAttribute(Qt.WA_StyledBackground, True)
        self.Tab_Row.setAutoFillBackground(False)
        Tab_Row_Display = QHBoxLayout(self.Tab_Row)
        Tab_Row_Display.setContentsMargins(self.Initial_Tab_Indent, self.Top_Button_Gap, 10, 0)
        Tab_Row_Display.setSpacing(6)
        # The tabs are inserted into this layout before its stretch
        self.Tab_Row_Layout = QHBoxLayout()
        self.Tab_Row_Layout.setContentsMargins(0, 0, 0, 0)
        self.Tab_Row_Layout.setSpacing(3)
        self.Tab_Row_Layout.addStretch()
        Tab_Row_Display.addLayout(self.Tab_Row_Layout, stretch=1)
        self.New_Fit_Button = Make_Secondary_Button("New Fit")
        self.New_Fit_Button.clicked.connect(self.Add_New_Fit_Tab)
        Tab_Row_Display.addWidget(self.New_Fit_Button, alignment=Qt.AlignBottom)
        self.Reset_Button = Make_Secondary_Button("Reset")
        self.Reset_Button.clicked.connect(self.Confirm_Reset_All_Fits)
        Tab_Row_Display.addWidget(self.Reset_Button, alignment=Qt.AlignBottom)

        # Separator line
        self.Separator = QWidget()
        self.Separator.setObjectName("RunSeparator")
        self.Separator.setAttribute(Qt.WA_StyledBackground, True)
        self.Separator.setFixedHeight(self.Separator_Height)

        # Content stack
        self.Run_Stack = QStackedWidget()

        # Floating connector that covers the separator under the selected tab
        self.Connector = QWidget(self)
        self.Connector.setObjectName("RunTabConnector")
        self.Connector.setAttribute(Qt.WA_StyledBackground, True)
        self.Connector.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.Connector.setFixedHeight(self.Separator_Height)
        self.Connector.hide()

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, Shadow_Blur_Radius, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.Tab_Row)
        Layout.addWidget(self.Separator)
        Layout.addWidget(self.Run_Stack)

        # Tab bar background, shadow and active tab overlay
        self.Tab_Bar_Background = Run_Tab_Background(self)
        self.Tab_Bar_Background.lower()
        from Themes.Theme import Get_Theme
        Theme_Name, _, Theme_Colors = Get_Theme()
        self.Tab_Bar_Background.Set_Dark_Mode(Theme_Name == "Dark", Theme_Colors.get("Run_Tab_Row_Background", "#000000"))
        self.Shadow = Tab_Bar_Shadow(self)
        self.Overlay = Active_Tab_Overlay(self)

        # Add the first fit
        self.Attach_Run(Fitting_Step_By_Step_Layout_Content(), "Fit 1")


    # Add a new fit tab that starts from the data and models of the current fit
    def Add_New_Fit_Tab(self):

        Current_Run = self.Get_Current_Run()
        Prefill = Current_Run.Get_Prefill() if Current_Run is not None else None
        Fit_Number = len(self.Runs) + 1
        with Guard_Unwanted_Window_Shows():
            New_Run = Fitting_Step_By_Step_Layout_Content(Prefill=Prefill)
        self.Attach_Run(New_Run, f"Fit {Fit_Number}")


    # Ask before removing every fit
    def Confirm_Reset_All_Fits(self):

        Answer = Warning_Message(self.window(), "Reset Application", Buttons=QMessageBox.Ok | QMessageBox.Cancel, Default_Button=QMessageBox.Cancel)
        if Answer == QMessageBox.Ok:
            self.Reset_All_Runs()


    # Remove all tabs and start over with a single fresh fit
    def Reset_All_Runs(self):

        # Build the new first fit first so the stack is never left empty
        with Guard_Unwanted_Window_Shows():
            First_Run = Fitting_Step_By_Step_Layout_Content()

        # Stash old references before clearing the lists
        Old_Buttons = list(self.Tab_Buttons)
        Old_Connectors = list(self.Inactive_Connectors)
        Old_Runs = list(self.Runs)

        # Reset internal state and attach the fresh fit (switches display)
        self.Tab_Buttons = []
        self.Inactive_Connectors = []
        self.Runs = []
        self.Attach_Run(First_Run, "Fit 1")

        # Now safely discard the old tabs, which are already hidden
        self.Connector.hide()
        for Button in Old_Buttons:
            self.Tab_Row_Layout.removeWidget(Button)
            Button.deleteLater()
        for Connector in Old_Connectors:
            Connector.deleteLater()
        for Run in Old_Runs:
            self.Run_Stack.removeWidget(Run)
            Run.deleteLater()
