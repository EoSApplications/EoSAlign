# Load Libraries
    # Load standard libraries
import os
    # Load third party libraries
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget, QWidget, QSizePolicy, QAbstractScrollArea, QApplication, QSpinBox, QGridLayout, QTextBrowser, QCheckBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QColor, QIcon
    # Load local functions from local files
from Themes.Theme import Get_Theme
from EoS_Math.Build_Dataframe import Set_Calibration_File_Settings as set_calibration_file_settings
from Loading_Message import Get_Resource_Path
from Collapsible_Sections import Dropdown
from Version import Get_Current_Running_Application_Id
from Check_For_Updates import Are_Update_Notifications_Enabled, Set_Update_Notifications_Enabled
from Check_For_Calibration_Updates import Are_Calibration_Update_Notifications_Enabled, Set_Calibration_Update_Notifications_Enabled





# Create the settings
class Settings(QDialog):

    # Add signals for when the settings are changed
    Plot_Settings_Changed = Signal()
    EoSAlign_Layout_Changed = Signal(str)

    def __init__(self, Parent=None):
        super().__init__(Parent)

        # Give this dialog a full window title bar with minimize, maximize, and close buttons.
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        # Set the window title
        self.setWindowTitle("Settings")
        # Set the default window icon
        self.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
        # Set the window size — taller than before to accommodate study panel
        self.resize(700, 550)

        # Setup the main settings layout
        Main_Settings_Layout = QHBoxLayout()

        # Create the sidebar display
        self.Sidebar_Display = QListWidget()
        self.Sidebar_Display.setObjectName("SettingsTabTitle")
        self.Sidebar_Display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.Sidebar_Display.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        # Add a tab for each settings page
        self.Sidebar_Display.addItem(QListWidgetItem("General"))
        self.Sidebar_Display.addItem(QListWidgetItem("Plots"))
        self.Sidebar_Display.addItem(QListWidgetItem("Documentation"))
        self.Sidebar_Display.addItem(QListWidgetItem("About Application"))
        # Fix the sidebar width to fit the widest item label
        Maximum_Sidebar_Width = max(self.Sidebar_Display.fontMetrics().horizontalAdvance(self.Sidebar_Display.item(i).text()) for i in range(self.Sidebar_Display.count()))
        self.Sidebar_Display.setFixedWidth(Maximum_Sidebar_Width + 60)
        Main_Settings_Layout.addWidget(self.Sidebar_Display)

        # Setup the a widget to display each settings page, wrapped in a styled card
        self.Settings_Page_Content = QStackedWidget()
        Content_Panel = QWidget()
        Content_Panel.setObjectName("SettingsContentPanel")
        Content_Panel.setAttribute(Qt.WA_StyledBackground, True)
        Content_Panel_Layout = QVBoxLayout(Content_Panel)
        Content_Panel_Layout.setContentsMargins(12, 12, 12, 12)
        Content_Panel_Layout.addWidget(self.Settings_Page_Content)
        Content_Panel_Shadow = QGraphicsDropShadowEffect(Content_Panel)
        Content_Panel_Shadow.setBlurRadius(16)
        Content_Panel_Shadow.setXOffset(0)
        Content_Panel_Shadow.setYOffset(2)
        Content_Panel_Shadow.setColor(QColor(0, 0, 0, 40))
        Content_Panel.setGraphicsEffect(Content_Panel_Shadow)
        Main_Settings_Layout.addWidget(Content_Panel)

        # Build each settings page
        self.Build_The_General_Settings_Page()
        self.Build_The_Plots_Settings_Page()
        self.Build_The_Documentation_Page()
        self.Build_The_About_Application_Page()

        # Setup the OK button that will close the settings
        Close_Settings_Button_Layout = QHBoxLayout()
        Close_Settings_Button = QPushButton("OK")
        Close_Settings_Button.setObjectName("Primary_Button")
        Close_Settings_Button.setFixedHeight(32)
        Close_Settings_Button.clicked.connect(self.accept)
        Close_Settings_Button_Layout.addWidget(Close_Settings_Button)

        # Setup the main settings layout
        Settings_Layout = QVBoxLayout(self)
        Settings_Layout.addLayout(Main_Settings_Layout)
        Settings_Layout.addLayout(Close_Settings_Button_Layout)
        self.setLayout(Settings_Layout)
        # Put the sidebar and content in the main layout
        self.Sidebar_Display.currentRowChanged.connect(self.Settings_Page_Content.setCurrentIndex)
        self.Sidebar_Display.setCurrentRow(0)

        # Load the saved settings
        self.Load_Settings()

        # Apply the theme immediately when changed
        self.Select_Theme_Layout.currentTextChanged.connect(self.Apply_Theme_Immediately)

        # Redraw plots whenever a font-size spinbox changes
        self.Plot_Title_Font_Size_Selection.valueChanged.connect(self.Apply_Plot_Settings)
        self.Axis_Label_Font_Size_Selection.valueChanged.connect(self.Apply_Plot_Settings)
        self.Tick_Mark_Font_Size_Selection.valueChanged.connect(self.Apply_Plot_Settings)
        self.Legend_Font_Size_Selection.valueChanged.connect(self.Apply_Plot_Settings)
        self.Has_Shown_Once = False


    def show(self):
        """Show without a native frame flash by revealing from off-screen."""
        if not self.Has_Shown_Once:
            self.Has_Shown_Once = True
            screen = QApplication.primaryScreen()
            sg = screen.availableGeometry()
            self.adjustSize()
            w = max(self.width(), self.minimumWidth())
            h = max(self.height(), self.minimumHeight())
            cx = (sg.width() - w) // 2 + sg.x()
            cy = (sg.height() - h) // 2 + sg.y()
            self.setAttribute(Qt.WA_DontShowOnScreen, True)
            super().show()
            QApplication.processEvents()
            self.hide()
            self.setAttribute(Qt.WA_DontShowOnScreen, False)
            self.move(cx, cy)
            super().show()
        else:
            super().show()



    # Build the General settings page
    def Build_The_General_Settings_Page(self):

        # Create the general settings page display
        General_Settings_Page = QWidget()
        General_Settings_Layout = QVBoxLayout(General_Settings_Page)

        # Page header
        General_Settings_Header = QLabel("General Settings")
        General_Settings_Header.setObjectName("Settings_Header")
        General_Settings_Layout.addWidget(General_Settings_Header)

        # Select the theme
        General_Settings_Layout.addWidget(QLabel("Theme:"))
        self.Select_Theme_Layout = Dropdown()
        self.Select_Theme_Layout.addItems(["System Default", "Light", "Dark"])
        General_Settings_Layout.addWidget(self.Select_Theme_Layout)

        # Select the EoSAlign layout
        General_Settings_Layout.addWidget(QLabel("EoSAlign Layout:"))
        self.Select_EoSAlign_Layout = Dropdown()
        self.Select_EoSAlign_Layout.addItems(["Step by Step", "All Steps"])
        # Emit a signal when the layout is changed
        self.Select_EoSAlign_Layout.currentTextChanged.connect(self.When_EoSAlign_Layout_Changed)
        General_Settings_Layout.addWidget(self.Select_EoSAlign_Layout)

        # Update notification options
        General_Settings_Layout.addWidget(QLabel("Updates:"))
        self.Notify_About_Updates_Checkbox = QCheckBox("Notify me when a new version is available")
        self.Notify_About_Updates_Checkbox.setChecked(True)
        # Save immediately on change so the update checker sees the new choice right away
        self.Notify_About_Updates_Checkbox.toggled.connect(self.Save_Settings)
        General_Settings_Layout.addWidget(self.Notify_About_Updates_Checkbox)

        self.Notify_About_Calibration_Updates_Checkbox = QCheckBox("Notify me when calibration file updates are available")
        self.Notify_About_Calibration_Updates_Checkbox.setChecked(True)
        self.Notify_About_Calibration_Updates_Checkbox.toggled.connect(self.Save_Settings)
        General_Settings_Layout.addWidget(self.Notify_About_Calibration_Updates_Checkbox)

        # Calibration file source options
        General_Settings_Layout.addWidget(QLabel("Calibration Sources:"))
        self.Include_User_Edited_Checkbox = QCheckBox("Include user-edited files")
        self.Include_User_Edited_Checkbox.setChecked(True)
        self.Include_User_Edited_Checkbox.toggled.connect(self.When_Calibration_Source_Changed)
        General_Settings_Layout.addWidget(self.Include_User_Edited_Checkbox)

        self.Include_User_Entered_Checkbox = QCheckBox("Include user-entered files")
        self.Include_User_Entered_Checkbox.setChecked(True)
        self.Include_User_Entered_Checkbox.toggled.connect(self.When_Calibration_Source_Changed)
        General_Settings_Layout.addWidget(self.Include_User_Entered_Checkbox)

        # Display the general setting page
        General_Settings_Layout.addStretch()
        self.Settings_Page_Content.addWidget(General_Settings_Page)



    # Build the Plots settings page
    def Build_The_Plots_Settings_Page(self):

        # Create the plot settings page display
        Plot_Settings_Page = QWidget()
        Plot_Settings_Layout = QVBoxLayout(Plot_Settings_Page)

        # Page header
        Plot_Settings_Header = QLabel("Plot Settings")
        Plot_Settings_Header.setObjectName("Settings_Header")
        Plot_Settings_Layout.addWidget(Plot_Settings_Header)

        # Create a grid layout for the plot font settings
        Plot_Font_Settings_Grid_Layout = QGridLayout()
        # Set the size of the columns in the grid layout
            # The first column is for the setting label
        Plot_Font_Settings_Grid_Layout.setColumnMinimumWidth(0, 120)
            # The second column is for the font size
        Plot_Font_Settings_Grid_Layout.setColumnMinimumWidth(1, 60)
            # The third and fourth column are for bold
        Plot_Font_Settings_Grid_Layout.setColumnMinimumWidth(2, 40)
            # The fifth column is for italic
        Plot_Font_Settings_Grid_Layout.setColumnMinimumWidth(3, 40)

        # The first row of the grid is for the title font settings
        self.Plot_Title_Font_Size_Selection = QSpinBox()
        # Allow the plot title font size to be set between 5 points and 40 points
        self.Plot_Title_Font_Size_Selection.setRange(5, 40)
        # By default set the plot title font size to 10 points
        self.Plot_Title_Font_Size_Selection.setValue(8)
        # Create a button for bolding the plot title font
        self.Plot_Title_Bold_Button = QPushButton("B")
        self.Plot_Title_Bold_Button.setCheckable(True)
        self.Plot_Title_Bold_Button.setObjectName("TertiaryButton")
        self.Plot_Title_Bold_Button.setStyleSheet("font-weight: bold;")
        self.Plot_Title_Bold_Button.setFixedHeight(32)
        self.Plot_Title_Italic_Button = QPushButton("I")
        self.Plot_Title_Italic_Button.setCheckable(True)
        self.Plot_Title_Italic_Button.setObjectName("TertiaryButton")
        self.Plot_Title_Italic_Button.setStyleSheet("font-style: italic;")
        self.Plot_Title_Italic_Button.setFixedHeight(32)
        # Add the plot title font settings to the first row of the grid layout
            # Label
        Plot_Font_Settings_Grid_Layout.addWidget(QLabel("Plot Title:"), 0, 0)
            # Font size selection
        Plot_Font_Settings_Grid_Layout.addWidget(self.Plot_Title_Font_Size_Selection, 0, 1)
            # Bold button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Plot_Title_Bold_Button, 0, 2)
            # Italic button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Plot_Title_Italic_Button, 0, 3)
        # Connect the plot title font settings to the apply plot settings function
        self.Plot_Title_Bold_Button.toggled.connect(self.Apply_Plot_Settings)
        self.Plot_Title_Italic_Button.toggled.connect(self.Apply_Plot_Settings)

        # The second row of the grid is for the axis labels font settings
        self.Axis_Label_Font_Size_Selection = QSpinBox()
        # Allow the axis labels font size to be set between 5 points and 40 points
        self.Axis_Label_Font_Size_Selection.setRange(5, 40)
        # By default set the axis labels font size to 12 points
        self.Axis_Label_Font_Size_Selection.setValue(7)
        # Create a button for bolding the axis labels font
        self.Axis_Label_Bold_Button = QPushButton("B")
        self.Axis_Label_Bold_Button.setCheckable(True)
        self.Axis_Label_Bold_Button.setObjectName("TertiaryButton")
        self.Axis_Label_Bold_Button.setStyleSheet("font-weight: bold;")
        self.Axis_Label_Bold_Button.setFixedHeight(32)
        self.Axis_Label_Italic_Button = QPushButton("I")
        self.Axis_Label_Italic_Button.setCheckable(True)
        self.Axis_Label_Italic_Button.setObjectName("TertiaryButton")
        self.Axis_Label_Italic_Button.setStyleSheet("font-style: italic;")
        self.Axis_Label_Italic_Button.setFixedHeight(32)
        # Add the axis labels font settings to the second row of the grid layout
            # Label
        Plot_Font_Settings_Grid_Layout.addWidget(QLabel("Axis Labels:"), 1, 0)
            # Font size selection
        Plot_Font_Settings_Grid_Layout.addWidget(self.Axis_Label_Font_Size_Selection, 1, 1)
            # Bold button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Axis_Label_Bold_Button, 1, 2)
            # Italic button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Axis_Label_Italic_Button, 1, 3)
        # Connect the axis labels font settings to the apply plot settings function
        self.Axis_Label_Bold_Button.toggled.connect(self.Apply_Plot_Settings)
        self.Axis_Label_Italic_Button.toggled.connect(self.Apply_Plot_Settings)

        # The third row of the grid is for the tick mark labels font settings
        self.Tick_Mark_Font_Size_Selection = QSpinBox()
        # Allow the tick mark labels font size to be set between 5 points and 40 points
        self.Tick_Mark_Font_Size_Selection.setRange(5, 40)
        # By default set the tick mark labels font size to 8 points
        self.Tick_Mark_Font_Size_Selection.setValue(6)
        # Create a button for bolding the tick mark labels font
        self.Tick_Mark_Bold_Button = QPushButton("B")
        self.Tick_Mark_Bold_Button.setCheckable(True)
        self.Tick_Mark_Bold_Button.setObjectName("TertiaryButton")
        self.Tick_Mark_Bold_Button.setStyleSheet("font-weight: bold;")
        self.Tick_Mark_Bold_Button.setFixedHeight(32)
        self.Tick_Mark_Italic_Button = QPushButton("I")
        self.Tick_Mark_Italic_Button.setCheckable(True)
        self.Tick_Mark_Italic_Button.setObjectName("TertiaryButton")
        self.Tick_Mark_Italic_Button.setStyleSheet("font-style: italic;")
        self.Tick_Mark_Italic_Button.setFixedHeight(32)
        # Add the tick mark labels font settings to the third row of the grid layout
            # Label
        Plot_Font_Settings_Grid_Layout.addWidget(QLabel("Tick Labels:"), 2, 0)
            # Font size selection
        Plot_Font_Settings_Grid_Layout.addWidget(self.Tick_Mark_Font_Size_Selection, 2, 1)
            # Bold button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Tick_Mark_Bold_Button, 2, 2)
            # Italic button
        Plot_Font_Settings_Grid_Layout.addWidget(self.Tick_Mark_Italic_Button, 2, 3)
        # Connect the tick mark labels font settings to the apply plot settings function
        self.Tick_Mark_Bold_Button.toggled.connect(self.Apply_Plot_Settings)
        self.Tick_Mark_Italic_Button.toggled.connect(self.Apply_Plot_Settings)

        # The fourth row of the grid is for the legend font size
        self.Legend_Font_Size_Selection = QSpinBox()
        self.Legend_Font_Size_Selection.setRange(5, 40)
        self.Legend_Font_Size_Selection.setValue(4)
        Plot_Font_Settings_Grid_Layout.addWidget(QLabel("Legend:"), 3, 0)
        Plot_Font_Settings_Grid_Layout.addWidget(self.Legend_Font_Size_Selection, 3, 1)
        self.Legend_Font_Size_Selection.valueChanged.connect(self.Apply_Plot_Settings)

        # Add the plot font settings grid layout to the plot settings page layout
        Plot_Settings_Layout.addLayout(Plot_Font_Settings_Grid_Layout)

        # Create a button for resetting the plot settings
        Reset_Button = QPushButton("Reset Plot Settings")
        Reset_Button.setObjectName("Secondary_Button")
        Reset_Button.setFixedHeight(32)
        Reset_Button.clicked.connect(self.Reset_Plot_Settings)
        # Add the reset button to the plot settings page layout
        Plot_Settings_Layout.addWidget(Reset_Button)

        # Uncertainty options
        Plot_Settings_Layout.addWidget(QLabel("Uncertainty Display:"))

        # Toggle for showing or hiding uncertainty on all plots
        self.Show_Uncertainty_Checkbox = QCheckBox("Show Uncertainty")
        self.Show_Uncertainty_Checkbox.setChecked(True)
        self.Show_Uncertainty_Checkbox.toggled.connect(self.When_Uncertanty_Toggle_Is_Changed)
        self.Show_Uncertainty_Checkbox.toggled.connect(self.Apply_Plot_Settings)
        Plot_Settings_Layout.addWidget(self.Show_Uncertainty_Checkbox)

        # Toggle for showing or hiding grid lines on all plots
        self.Show_Grid_Lines_Checkbox = QCheckBox("Show Grid Lines")
        self.Show_Grid_Lines_Checkbox.setChecked(False)
        self.Show_Grid_Lines_Checkbox.toggled.connect(self.Apply_Plot_Settings)
        Plot_Settings_Layout.addWidget(self.Show_Grid_Lines_Checkbox)

        # Uncertainty style selector — indented, hidden when uncertainty is off
        self.Uncertainty_Style_Widget = QWidget()
        self.Uncertainty_Style_Widget.setObjectName("UncertaintyStyleRow")
        Uncertainty_Style_Row = QHBoxLayout(self.Uncertainty_Style_Widget)
        Uncertainty_Style_Row.setContentsMargins(20, 0, 0, 0)
        Uncertainty_Style_Row.setSpacing(8)
        Uncertainty_Style_Row.addWidget(QLabel("Style:"))
        self.Uncertainty_Style_Dropdown = Dropdown()
        self.Uncertainty_Style_Dropdown.addItems(["Bands", "Error Bars", "Both"])
        self.Uncertainty_Style_Dropdown.currentTextChanged.connect(self.Apply_Plot_Settings)
        Uncertainty_Style_Row.addWidget(self.Uncertainty_Style_Dropdown)
        Uncertainty_Style_Row.addStretch()
        Plot_Settings_Layout.addWidget(self.Uncertainty_Style_Widget)

        # Export figures
        Plot_Settings_Layout.addWidget(QLabel("Export Settings:"))

        # Toggle for remembering which figures the user chose to export last time
        self.Remember_Export_Checkbox = QCheckBox("Remember export figure selections")
        self.Remember_Export_Checkbox.setChecked(True)
        # Save immediately on change — does not trigger a plot redraw
        self.Remember_Export_Checkbox.toggled.connect(self.Save_Settings)
        Plot_Settings_Layout.addWidget(self.Remember_Export_Checkbox)

        # Display the plot settings page
        Plot_Settings_Layout.addStretch()
        self.Settings_Page_Content.addWidget(Plot_Settings_Page)



    # Build the documentation settings page
    def Build_The_Documentation_Page(self):

        # Create the documentation settings page display
        Documentation_Page = QWidget()
        Documentation_Layout = QVBoxLayout(Documentation_Page)

        # Page header
        Documentation_Header = QLabel("Documentation")
        Documentation_Header.setObjectName("Settings_Header")
        Documentation_Layout.addWidget(Documentation_Header)

        # Create a display for the documentation HTML content
        self.Documentation_HTML_Browser = QTextBrowser()
        self.Documentation_HTML_Browser.setOpenExternalLinks(True)
        self.Documentation_HTML_Browser.setObjectName("SettingsText")
        self.Documentation_HTML_Browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Find the documentation HTML file
        Documentation_HTML_Path = Get_Resource_Path("../Documentation/Documentation.html")
        # Load the documentation HTML file
        if os.path.exists(Documentation_HTML_Path):
            with open(Documentation_HTML_Path, "r", encoding="utf-8") as Documentation_HTML_File:
                self.Documentation_HTML_Browser.setHtml(Documentation_HTML_File.read())
        # If the documentation HTML file is not found, display an error message
        else:
            self.Documentation_HTML_Browser.setHtml("<h3>Documentation file not found.</h3>")

        # Display the documentation page
        Documentation_Layout.addWidget(self.Documentation_HTML_Browser)
        self.Settings_Page_Content.addWidget(Documentation_Page)



    # Build the about application page
    def Build_The_About_Application_Page(self):

        # Create the about application page
        About_Application_Page = QWidget()
        About_Application_Layout = QVBoxLayout(About_Application_Page)

        # Page header
        About_Application_Header = QLabel("About EoS Applications")
        About_Application_Header.setObjectName("Settings_Header")
        About_Application_Layout.addWidget(About_Application_Header)

        # Create a display for the about application HTML content
        self.About_Application_HTML_Browser = QTextBrowser()
        self.About_Application_HTML_Browser.setOpenExternalLinks(True)
        self.About_Application_HTML_Browser.setObjectName("SettingsText")
        self.About_Application_HTML_Browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Find the about application HTML file
        About_Application_HTML_File_Path = Get_Resource_Path("../Documentation/About_EoSAlign.html")
        # Load the about application HTML file
        if os.path.exists(About_Application_HTML_File_Path):
            with open(About_Application_HTML_File_Path, "r", encoding="utf-8") as About_Application_HTML_File:
                self.About_Application_HTML_Browser.setHtml(About_Application_HTML_File.read())
        # If the about application HTML file is not found, display an error message
        else:
            self.About_Application_HTML_Browser.setHtml("<h3>About application file not found.</h3>")

        # Display the about application page
        About_Application_Layout.addWidget(self.About_Application_HTML_Browser)
        self.Settings_Page_Content.addWidget(About_Application_Page)



    # Load the saved settings into the UI controls
    def Load_Settings(self):

        # Load the saved settings
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")

        # Load the theme selection
        Theme = Settings_Store.value("Theme", "System Default")
        Theme_Index = self.Select_Theme_Layout.findText(Theme)
        if Theme_Index != -1:
            self.Select_Theme_Layout.setCurrentIndex(Theme_Index)

        # Load the EoSAlign layout selection
        Layout = Settings_Store.value("Layout Selection", "Step by Step")
        Layout_Index = self.Select_EoSAlign_Layout.findText(Layout)
        if Layout_Index != -1:
            self.Select_EoSAlign_Layout.setCurrentIndex(Layout_Index)

        # Load the update notification preference for the currently running application
            # This is stored per application id (not in the shared Settings_Store above) since
            # Check_For_Updates.py reads and writes it the same way for the update dialog's
            # own "do not show this message again" checkbox
        self.Notify_About_Updates_Checkbox.setChecked(
            Are_Update_Notifications_Enabled(Get_Current_Running_Application_Id()))

        # Load the calibration update notification preference
            # Shared across every app in the suite rather than per application id, since the
            # same calibration data is used no matter which app is running
        self.Notify_About_Calibration_Updates_Checkbox.setChecked(
            Are_Calibration_Update_Notifications_Enabled())

        # Load calibration source settings
        self.Include_User_Edited_Checkbox.setChecked(
            Settings_Store.value("Include User Edited", True, type=bool))
        self.Include_User_Entered_Checkbox.setChecked(
            Settings_Store.value("Include User Entered", True, type=bool))

        # Load plot font settings
            # Title font settings
        self.Plot_Title_Font_Size_Selection.setValue(int(Settings_Store.value("Plot Title Font Size", 7)))
        self.Plot_Title_Bold_Button.setChecked(Settings_Store.value("Plot Title Bold", False, type=bool))
        self.Plot_Title_Italic_Button.setChecked(Settings_Store.value("Plot Title Italic", False, type=bool))
            # Axis labels font settings
        self.Axis_Label_Font_Size_Selection.setValue(int(Settings_Store.value("Axis Label Font Size", 6)))
        self.Axis_Label_Bold_Button.setChecked(Settings_Store.value("Axis Label Bold", False, type=bool))
        self.Axis_Label_Italic_Button.setChecked(Settings_Store.value("Axis Label Italic", False, type=bool))
            # Tick mark labels font settings
        self.Tick_Mark_Font_Size_Selection.setValue(int(Settings_Store.value("Tick Mark Font Size", 5)))
        self.Tick_Mark_Bold_Button.setChecked(Settings_Store.value("Tick Mark Bold", False, type=bool))
        self.Tick_Mark_Italic_Button.setChecked(Settings_Store.value("Tick Mark Italic", False, type=bool))
            # Legend font size
        self.Legend_Font_Size_Selection.setValue(int(Settings_Store.value("Legend Font Size", 5)))
        # Load uncertainty display settings
        Show_Uncertainty = Settings_Store.value("Show_Uncertainty", True, type=bool)
        self.Show_Uncertainty_Checkbox.setChecked(Show_Uncertainty)
        self.When_Uncertanty_Toggle_Is_Changed(Show_Uncertainty)
        Style_Index = self.Uncertainty_Style_Dropdown.findText(Settings_Store.value("Uncertainty_Style", "Bands"))
        if Style_Index != -1:
            self.Uncertainty_Style_Dropdown.setCurrentIndex(Style_Index)
        # Load grid line display setting
        self.Show_Grid_Lines_Checkbox.setChecked(Settings_Store.value("Show_Grid_Lines", False, type=bool))
        # Load export settings
        self.Remember_Export_Checkbox.setChecked(Settings_Store.value("Remember_Export_Selections", True, type=bool))



    # Save the current settings
    def Save_Settings(self):

        # Save the settings
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")

        # Save the theme selection
        Settings_Store.setValue("Theme", self.Select_Theme_Layout.currentText())

        # Save the EoSAlign layout selection
        Settings_Store.setValue("Layout Selection", self.Select_EoSAlign_Layout.currentText())

        # Save the update notification preference for the currently running application
        Set_Update_Notifications_Enabled(
            Get_Current_Running_Application_Id(), self.Notify_About_Updates_Checkbox.isChecked())

        # Save the calibration update notification preference
        Set_Calibration_Update_Notifications_Enabled(
            self.Notify_About_Calibration_Updates_Checkbox.isChecked())

        # Save calibration source settings
        Settings_Store.setValue("Include User Edited", self.Include_User_Edited_Checkbox.isChecked())
        Settings_Store.setValue("Include User Entered", self.Include_User_Entered_Checkbox.isChecked())

        # Save plot font settings
            # Title font settings
        Settings_Store.setValue("Plot Title Font Size", self.Plot_Title_Font_Size_Selection.value())
        Settings_Store.setValue("Plot Title Bold", self.Plot_Title_Bold_Button.isChecked())
        Settings_Store.setValue("Plot Title Italic", self.Plot_Title_Italic_Button.isChecked())
            # Axis labels font settings
        Settings_Store.setValue("Axis Label Font Size", self.Axis_Label_Font_Size_Selection.value())
        Settings_Store.setValue("Axis Label Bold", self.Axis_Label_Bold_Button.isChecked())
        Settings_Store.setValue("Axis Label Italic", self.Axis_Label_Italic_Button.isChecked())
            # Tick mark labels font settings
        Settings_Store.setValue("Tick Mark Font Size", self.Tick_Mark_Font_Size_Selection.value())
        Settings_Store.setValue("Tick Mark Bold", self.Tick_Mark_Bold_Button.isChecked())
        Settings_Store.setValue("Tick Mark Italic", self.Tick_Mark_Italic_Button.isChecked())
            # Legend font size
        Settings_Store.setValue("Legend Font Size", self.Legend_Font_Size_Selection.value())

        # Save uncertainty display settings
        Settings_Store.setValue("Show_Uncertainty", self.Show_Uncertainty_Checkbox.isChecked())
        Settings_Store.setValue("Uncertainty_Style", self.Uncertainty_Style_Dropdown.currentText())
        Settings_Store.setValue("Show_Grid_Lines", self.Show_Grid_Lines_Checkbox.isChecked())

        # Save export settings
        Settings_Store.setValue("Remember_Export_Selections", self.Remember_Export_Checkbox.isChecked())



    # Apply the selected theme immediately
    def Apply_Theme_Immediately(self, Theme_Name):

        # Load the settings
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")

        # Load the theme selection
        Settings_Store.setValue("Theme", Theme_Name)

        # Load the EoSAlign layout selection
        Settings_Store.setValue("Layout Selection", self.Select_EoSAlign_Layout.currentText())

        # Load the style sheet for the selected theme
        from Themes.Theme import Load_Application_Style_Sheet
        Theme_Name, Style_Sheet_Information, COLORS = Load_Application_Style_Sheet(Get_Resource_Path)
        QApplication.instance().setStyleSheet(Style_Sheet_Information)
        self.Plot_Settings_Changed.emit()



    # Show or hide the uncertainty style dropdown based on the toggle state
    def When_Uncertanty_Toggle_Is_Changed(self, Is_Checked):

        self.Uncertainty_Style_Widget.setVisible(Is_Checked)



    # Reload calibrations when the source checkboxes change
    def When_Calibration_Source_Changed(self):

        self.Save_Settings()
        set_calibration_file_settings(include_user_edited=self.Include_User_Edited_Checkbox.isChecked(), include_user_entered=self.Include_User_Entered_Checkbox.isChecked())



    # Emit a signal when the EoSAlign layout is changed
    def When_EoSAlign_Layout_Changed(self, Selected_EoSAlign_Layout):

        # Save the new layout selection
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        Settings_Store.setValue("Layout Selection", Selected_EoSAlign_Layout)

        # Send out the new layout selection
        self.EoSAlign_Layout_Changed.emit(Selected_EoSAlign_Layout)



    # Select a settings page
    def Select_A_Settings_Page(self, Page_Name):

        # Find the page in the sidebar and select it
        for Settings_Page in range(self.Sidebar_Display.count()):
            if self.Sidebar_Display.item(Settings_Page).text().lower() == Page_Name.lower():
                self.Sidebar_Display.setCurrentRow(Settings_Page)
                # Reset the scroll position for Documentation and About pages
                    # The check is all lowercase to avoid capitalization issues
                if Page_Name.lower() == "documentation":
                    self.Documentation_HTML_Browser.verticalScrollBar().setValue(0)
                elif Page_Name.lower() == "about application":
                    self.About_Application_HTML_Browser.verticalScrollBar().setValue(0)
                break



    # Emit a signal when the plot settings are changed
    def Apply_Plot_Settings(self):

        # Save the new plot settings
        self.Save_Settings()
        # Emit the signal to update the plots with the new settings
        self.Plot_Settings_Changed.emit()

    # Reset all plot settings to their defaults
    def Reset_Plot_Settings(self):

        # Reset all font sizes
        self.Plot_Title_Font_Size_Selection.setValue(7)
        self.Axis_Label_Font_Size_Selection.setValue(6)
        self.Tick_Mark_Font_Size_Selection.setValue(5)
        self.Legend_Font_Size_Selection.setValue(5)

        # Reset bold and italic toggles
        self.Plot_Title_Bold_Button.setChecked(False)
        self.Plot_Title_Italic_Button.setChecked(False)
        self.Axis_Label_Bold_Button.setChecked(False)
        self.Axis_Label_Italic_Button.setChecked(False)
        self.Tick_Mark_Bold_Button.setChecked(False)
        self.Tick_Mark_Italic_Button.setChecked(False)

        # Reset uncertainty display to defaults
        self.Show_Uncertainty_Checkbox.setChecked(True)
        Bands_Index = self.Uncertainty_Style_Dropdown.findText("Bands")
        if Bands_Index != -1:
            self.Uncertainty_Style_Dropdown.setCurrentIndex(Bands_Index)
        self.Show_Grid_Lines_Checkbox.setChecked(False)

        # Reset all per-study colors and markers stored in QSettings
        Settings_Store = QSettings("EoSAlign", "EoSAlignApp")
        for Key in Settings_Store.allKeys():
            if Key.endswith("_Color") or Key.endswith("_Marker"):
                Settings_Store.remove(Key)

        # Save the reset settings and apply them to the plots
        self.Apply_Plot_Settings()



    # Scroll the documentation page to a specific location
    def Scroll_Documentation_To(self, Specific_Location):

        # Select the documentation page
        self.Select_A_Settings_Page("Documentation")
        # Scroll to the specific location
        self.Documentation_HTML_Browser.scrollToAnchor(Specific_Location)



    # Scroll the about application page to a specific location
    def Scroll_About_To(self, Specific_Location):

        # Select the about application page
        self.Select_A_Settings_Page("About Application")
        # Scroll to the specific location
        self.About_Application_HTML_Browser.scrollToAnchor(Specific_Location)




