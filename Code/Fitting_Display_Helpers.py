# Load libraries
    # Load standard libraries
import numpy as np
    # Load third party libraries
from PySide6.QtCore import Qt, QSize, QLocale, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem, QWidget
    # Load local functions from local files
from Themes.Theme import Get_Theme
from Fitting_Data_Table import Fitting_Data_Table
from View_Edit_And_Save_Calibration_Files_In_A_New_Window import Render_Latex_To_Pixmap





# Make a secondary button the same way EoSAlign makes its browse buttons
def Make_Secondary_Button(Text):

    Button = QPushButton(Text)
    Button.setObjectName("Secondary_Button")
    Button.setMinimumWidth(100)
    Button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    Button.setFixedHeight(32)

    return Button



# The font size of the equations (pt). The labels beside the equations are 12 pt, but the math font has smaller letters than the
# label font, so a larger size makes the equations look the same size as the text
Equation_Font_Size = 15.0



# Get the color of the equations; it is the color of the checkbox labels they sit beside, so they look like plain text
def Get_Equation_Text_Color():

    _, _, Colors = Get_Theme()

    return Colors.get("Tertiary_Text", "#B3B3B3")



# Render a LaTeX equation with the same high DPI path as Latex_Equation_Field, on a transparent background in the color and size of the text beside it
def Render_Equation_Pixmap(Latex_String):

    # Matplotlib mathtext does not support some commands, so replace or remove them
    Clean_Latex = (Latex_String
                   .replace(r'\!', '')
                   .replace(r'\tfrac', r'\frac')
                   .replace(r'\mathcal{F}', r'F'))
    Screen = QApplication.primaryScreen()
    Dpi = Screen.logicalDotsPerInchY() if Screen else 96.0
    Device_Pixel_Ratio = Screen.devicePixelRatio() if Screen else 1.0

    return Render_Latex_To_Pixmap(Clean_Latex, Get_Equation_Text_Color(), "none", Equation_Font_Size, Dpi, Device_Pixel_Ratio)



# A label for an equation image that shrinks the image to fit when there is not enough width for all of it
class Equation_Label(QLabel):
    def __init__(self, Parent=None):
        super().__init__(Parent)

        self.Equation_Pixmap = None
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)


    # Set the equation image
    def Set_Equation(self, Pixmap):

        self.Equation_Pixmap = Pixmap
        self.Show_The_Equation()
        self.updateGeometry()


    # The label can be made as narrow as needed, because the image is shrunk to fit
    def minimumSizeHint(self):

        return QSize(1, self.sizeHint().height())


    def resizeEvent(self, Event):

        super().resizeEvent(Event)
        self.Show_The_Equation()


    # Show the equation at its full size, or shrunk to the width of the label if it is wider
    def Show_The_Equation(self):

        if self.Equation_Pixmap is None:
            return
        Pixel_Ratio = self.Equation_Pixmap.devicePixelRatio()
        Full_Width = self.Equation_Pixmap.width() / Pixel_Ratio
        if self.width() > 1 and Full_Width > self.width():
            Shrunk = self.Equation_Pixmap.scaledToWidth(int(self.width() * Pixel_Ratio), Qt.SmoothTransformation)
            Shrunk.setDevicePixelRatio(Pixel_Ratio)
            self.setPixmap(Shrunk)
        else:
            self.setPixmap(self.Equation_Pixmap)



# The space between groups of inputs (px). The layouts already put 8 px on each side of every item, so a spacer is this minus 16
Group_Space = 30
Spacer_Height = Group_Space - 16



# Make an empty space that can be shown and hidden with the inputs it separates
def Make_A_Spacer():

    Spacer = QWidget()
    Spacer.setObjectName("CollapsibleSubContainer")
    Spacer.setFixedHeight(Spacer_Height)

    return Spacer



# Holds a widget that slides open and closed instead of popping in and out. While it moves, the scroll position of the page is held
# where it was, so the page does not jump
class Reveal_Container(QWidget):
    Animation_Duration = 220

    def __init__(self, Content, Parent=None):
        super().__init__(Parent)

        self.Content = Content
        self.Is_Revealed = False
        self.setObjectName("CollapsibleSubContainer")
        self.setVisible(False)
        Container_Layout = QVBoxLayout(self)
        Container_Layout.setContentsMargins(0, 0, 0, 0)
        Container_Layout.setSpacing(0)
        Container_Layout.addWidget(Content)

        self.Animation = QPropertyAnimation(self, b"maximumHeight")
        self.Animation.setDuration(self.Animation_Duration)
        self.Animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.Animation.finished.connect(self.When_The_Animation_Finishes)
        self.Animation.valueChanged.connect(self.Hold_The_Page)
        self.Held_Page = None


    # Find the scroll bar of the page this is on
    def Get_The_Page_Scroll_Bar(self):

        Parent = self.parentWidget()
        while Parent is not None:
            if isinstance(Parent, QScrollArea):
                return Parent.verticalScrollBar()
            Parent = Parent.parentWidget()

        return None


    # Get the height the content needs at the width it will have
    def Get_The_Open_Height(self):

        Parent = self.parentWidget()
        Width = Parent.width() if Parent is not None else self.width()
        if Parent is not None and Parent.layout() is not None:
            Margins = Parent.layout().contentsMargins()
            Width -= Margins.left() + Margins.right()
        if Width > 0 and self.Content.hasHeightForWidth():
            return self.Content.heightForWidth(Width)

        return self.Content.sizeHint().height()


    # Put the page back where it was while the content slides
    def Hold_The_Page(self, _=None):

        if self.Held_Page is not None:
            self.Held_Page[0].setValue(self.Held_Page[1])


    # Slide the content open or closed
    def Set_Revealed(self, Revealed):

        if Revealed == self.Is_Revealed:
            return
        self.Is_Revealed = Revealed
        self.Animation.stop()
        # Hold the page where it is while the content slides
        Scroll_Bar = self.Get_The_Page_Scroll_Bar()
        self.Held_Page = (Scroll_Bar, Scroll_Bar.value()) if Scroll_Bar is not None else None
        if Revealed:
            self.setMaximumHeight(0)
            self.setVisible(True)
            self.Animation.setStartValue(0)
            self.Animation.setEndValue(self.Get_The_Open_Height())
        else:
            self.Animation.setStartValue(self.height())
            self.Animation.setEndValue(0)
        self.Animation.start()


    # When it has finished opening let it size freely again, and when it has finished closing hide it
    def When_The_Animation_Finishes(self):

        if self.Is_Revealed:
            self.setMaximumHeight(16777215)
        else:
            self.setVisible(False)



# Write a number with the digits it needs and no more, e.g. 100.0, 4.0 or 0.00001, with no scientific notation
def Format_Number(Value):

    return np.format_float_positional(float(Value), trim="0")



# Get the style sheet for the number boxes, which match the text boxes of EoSAlign's collapsible sections
# On_Nested_Card is True for boxes inside a nested collapsible section, whose card is lighter than the main cards, so the box needs a different color to stand out
def Get_Number_Box_Style_Sheet(On_Nested_Card):

    _, _, Colors = Get_Theme()
    Background = Colors["Quaternary_Background"]
    if On_Nested_Card:
        # Use the main card color, or the page color when the two are the same (light theme)
        Background = Colors["Secondary_Background"] if Colors["Secondary_Background"] != Colors["Quaternary_Background"] else Colors["Primary_Background"]

    return f"""
        QLineEdit#FittingNumberBox {{
            background: {Background};
            color: {Colors['Primary_Text']};
            border: 1px solid transparent;
            border-radius: 15px;
            font-family: 'Noto Sans Mono', monospace;
            font-size: 12pt;
            padding: 5px;
            selection-background-color: {Colors['Primary_Accent']};
            selection-color: {Colors['Primary_Background']};
        }}
    """



# A box for typing a number. It looks like the text boxes of EoSAlign, has no up and down arrows, shows the number with the digits it was given
# (it keeps what the user types), and goes back to the last good number if what is typed is not a number or is out of range.
# Minimum is the smallest allowed number; Allow_Zero is False for a number that must be above zero
class Number_Box(QLineEdit):
    def __init__(self, Value=0.0, *, Integer=False, Minimum=None, Allow_Zero=True, On_Nested_Card=False, Width=190, Parent=None):
        super().__init__(Parent)

        self.Integer = Integer
        self.Minimum = Minimum
        self.Allow_Zero = Allow_Zero
        # Style the box
        self.setObjectName("FittingNumberBox")
        self.setStyleSheet(Get_Number_Box_Style_Sheet(On_Nested_Card))
        self.setFixedWidth(Width)
        # Only numbers can be typed
        if Integer:
            self.setValidator(QIntValidator(-999999, 999999, self))
        else:
            Validator = QDoubleValidator(-1e12, 1e12, 12, self)
            Validator.setNotation(QDoubleValidator.ScientificNotation)
            Validator.setLocale(QLocale(QLocale.C))
            self.setValidator(Validator)
        # The box is only selected when it is clicked, so nothing is selected when it first appears
        self.setFocusPolicy(Qt.ClickFocus)
        self.Last_Good_Text = ""
        self.setValue(Value)
        self.editingFinished.connect(self.Check_The_Entry)


    # Convert text to a number, or None if the text is not an allowed number
    def Read_The_Text(self, Text):

        try:
            Number = float(Text)
        except ValueError:
            return None
        if not np.isfinite(Number) or (self.Minimum is not None and Number < self.Minimum) or (not self.Allow_Zero and Number == 0):
            return None
        if self.Integer and Number != int(Number):
            return None

        return Number


    # Get the number in the box
    def value(self):

        Number = self.Read_The_Text(self.text())

        return Number if Number is not None else self.Read_The_Text(self.Last_Good_Text)


    # Put a number in the box
    def setValue(self, Value):

        Text = str(int(Value)) if self.Integer else Format_Number(Value)
        self.setText(Text)
        self.Last_Good_Text = Text
        self.deselect()


    # When the user finishes typing keep the number if it is allowed, otherwise go back to the last number that was
    def Check_The_Entry(self):

        if self.Read_The_Text(self.text()) is None:
            self.setText(self.Last_Good_Text)
        else:
            self.Last_Good_Text = self.text()



# A read-only table, styled like the data tables, that is as tall as its rows so it never scrolls vertically.
# If it is wider than the space it has, only the table scrolls sideways, and it is made taller to fit the scroll bar.
class Results_Table(Fitting_Data_Table):
    def __init__(self, Parent=None):
        super().__init__(0, 0, Read_Only=True, Parent=Parent)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        # The table can be made narrower than its columns; it scrolls instead of making the window wider
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        # Nothing is selected until the user clicks a cell
        self.setFocusPolicy(Qt.ClickFocus)


    # Size the columns and make the table tall enough for its header, every row and the scroll bar if there is one
    def Fit_To_The_Contents(self):

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.Fit_The_Height()


    # Make the table tall enough for everything but the part that scrolls sideways
    def Fit_The_Height(self):

        Frame = 2 * self.frameWidth()
        Header_Height = max(self.horizontalHeader().sizeHint().height(), 44 if self.columnCount() else 0)
        Content_Width = self.horizontalHeader().length() + self.verticalHeader().width() + Frame
        Scroll_Bar_Height = self.horizontalScrollBar().sizeHint().height() if Content_Width > self.width() else 0
        self.setFixedHeight(Header_Height + self.verticalHeader().length() + Frame + Scroll_Bar_Height + 2)


    def resizeEvent(self, Event):

        super().resizeEvent(Event)
        self.Fit_The_Height()


    def sizeHint(self):

        return QSize(200, self.height())



# Make a results table
def Make_Results_Table():

    return Results_Table()



# Make sure no cell of a table is selected or highlighted
def Clear_The_Table_Selection(Table):

    Table.clearSelection()
    Table.setCurrentItem(None)
    Table.setCurrentCell(-1, -1)
    Table.clearSelection()



# Get the text for one fitted parameter: value +/- uncertainty, marked (fixed) if it was held
def Get_Parameter_Text(Parameter, Stderr):

    if not Parameter.vary:
        # Fixed parameter: show the uncertainty only if the user supplied one
        return f"{Parameter.value:.5g} ± {Stderr:.3g} (fixed)" if Stderr else f"{Parameter.value:.5g} (fixed)"
    if Stderr is not None:
        return f"{Parameter.value:.5g} ± {Stderr:.3g}"

    return f"{Parameter.value:.5g}"



# Fill one model's column of a results table: every parameter, then reduced chi squared and R squared
def Fill_Result_Column(Table, Column, All_Parameters, Result, Stderr_Map):

    for Row, Parameter_Name in enumerate(All_Parameters):
        if Parameter_Name in Result.params:
            Parameter = Result.params[Parameter_Name]
            Text = Get_Parameter_Text(Parameter, Stderr_Map.get(Parameter_Name, Parameter.stderr))
        else:
            Text = "—"
        Item = QTableWidgetItem(Text)
        Item.setTextAlignment(Qt.AlignCenter)
        Table.setItem(Row, Column, Item)
    for Row, Text in ((len(All_Parameters), f"{Result.redchi:.4g}"), (len(All_Parameters) + 1, f"{Result.rsquared:.4f}" if np.isfinite(Result.rsquared) else "—")):
        Item = QTableWidgetItem(Text)
        Item.setTextAlignment(Qt.AlignCenter)
        Table.setItem(Row, Column, Item)



# Get the names of every parameter across the fitted models, in the order they first appear
def Get_All_Parameter_Names(Fit_Results):

    All_Parameters = []
    for Model_Fit in Fit_Results.values():
        for Parameter_Name in Model_Fit["result"].params:
            if Parameter_Name not in All_Parameters:
                All_Parameters.append(Parameter_Name)

    return All_Parameters
