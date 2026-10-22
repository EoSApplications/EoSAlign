# Load libraries
    # Load third party libraries
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                QTableWidget, QTableWidgetItem, QAbstractItemView, QApplication,
                                QSizePolicy)
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
    # Load local functions from local files
from Loading_Message import Get_Resource_Path
from MenuBar import MainMenuBar
from Banner import Banner
from Column_Labels import Get_Preview_Column_Labels




# Create a new window to preview converted data as it would appear in a CSV file
class Data_Preview_Dialog(QDialog):
    def __init__(self, Dataframe, Parent=None, Export_Callback=None):
        super().__init__(Parent)
        self.Export_Callback = Export_Callback

        # Set up the dialog
        # Full window title bar with minimize, maximize, and close buttons.
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("EoSAlign - Preview Conversion Results")
        self.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
        self.setMinimumSize(600, 400)

        # Create the layout
        self.Dialog_Layout = QVBoxLayout(self)
        self.Dialog_Layout.setContentsMargins(0, 0, 0, 0)
        self.Dialog_Layout.setSpacing(0)

        # Add menu bar and banner
        self.Menu_Bar = MainMenuBar(self)
        self.Menu_Bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Dialog_Layout.addWidget(self.Menu_Bar)
        self.Banner = Banner("", Get_Resource_Path("Graphics/EoSAlign_With_Sun.png"))
        self.Dialog_Layout.addWidget(self.Banner)

        # Create the table widget
        self.Data_Table = QTableWidget()
        self.Data_Table.setObjectName("PreviewDataTable")
        self.Data_Table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.Data_Table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.Populate_Table(Dataframe)
        self.Dialog_Layout.addWidget(self.Data_Table)

        # Add Ctrl+C shortcut to copy selected cells
        Copy_Shortcut = QShortcut(QKeySequence.Copy, self.Data_Table)
        Copy_Shortcut.activated.connect(self.Copy_Selection)

        # Create the button layout
        self.Button_Layout = QHBoxLayout()

        Export_Button_Layout = QHBoxLayout()
        Export_Button_Layout.addStretch()

        self.Export_Button = QPushButton("Export")
        self.Export_Button.setObjectName("Primary_Button")
        self.Export_Button.setFixedHeight(32)
        self.Export_Button.setEnabled(callable(self.Export_Callback))
        self.Export_Button.clicked.connect(self.Export_Data)
        Export_Button_Layout.addWidget(self.Export_Button)
        Export_Button_Layout.addStretch()

        # Close button
        Close_Button_Layout = QHBoxLayout()
        Close_Button_Layout.addStretch()
        self.Close_Button = QPushButton("Close")
        self.Close_Button.setObjectName("Secondary_Button")
        self.Close_Button.setFixedHeight(32)
        self.Close_Button.clicked.connect(self.close)
        Close_Button_Layout.addWidget(self.Close_Button)
        Close_Button_Layout.addStretch()

        self.Button_Layout.addLayout(Export_Button_Layout, 1)
        self.Button_Layout.addLayout(Close_Button_Layout, 1)

        self.Dialog_Layout.addLayout(self.Button_Layout)

        # Set a reasonable window size based on screen
        Screen = self.screen()
        Screen_Geometry = Screen.availableGeometry()
        Initial_Width = int(Screen_Geometry.width() * 0.8)
        Initial_Height = int(Screen_Geometry.height() * 0.7)
        Center_X = (Screen_Geometry.width() - Initial_Width) // 2 + Screen_Geometry.x()
        Center_Y = (Screen_Geometry.height() - Initial_Height) // 2 + Screen_Geometry.y()
        self.setGeometry(Center_X, Center_Y, Initial_Width, Initial_Height)
        self.Target_Position = (Center_X, Center_Y)
        self.Has_Shown_Once = False


    def Export_Data(self):
        if callable(self.Export_Callback):
            self.Export_Callback()


    def show(self):
        if not self.Has_Shown_Once:
            self.Has_Shown_Once = True
            self.setAttribute(Qt.WA_DontShowOnScreen, True)
            super().show()
            QApplication.processEvents()
            self.hide()
            self.setAttribute(Qt.WA_DontShowOnScreen, False)
            self.move(*self.Target_Position)
            super().show()
        else:
            super().show()


    def Populate_Table(self, Dataframe):
        """Populate the table widget with data from the dataframe."""
        if Dataframe is None or Dataframe.empty:
            return

        self.Data_Table.setRowCount(Dataframe.shape[0])
        self.Data_Table.setColumnCount(Dataframe.shape[1])

        # Create descriptive header labels from the shared preview label function
        Preview_Labels = Get_Preview_Column_Labels(Dataframe.columns.tolist())
        Header_Labels = [Preview_Labels[Column_Name] for Column_Name in Dataframe.columns.tolist()]

        self.Data_Table.setHorizontalHeaderLabels(Header_Labels)

        # Populate table data
        for Row_Index in range(Dataframe.shape[0]):
            for Column_Index in range(Dataframe.shape[1]):
                Value = Dataframe.iloc[Row_Index, Column_Index]
                if isinstance(Value, float):
                    Cell_Item = QTableWidgetItem(f"{Value:.6f}")
                else:
                    Cell_Item = QTableWidgetItem(str(Value))
                self.Data_Table.setItem(Row_Index, Column_Index, Cell_Item)

        # Resize columns to content and enforce a minimum column width
        self.Data_Table.resizeColumnsToContents()
        self.Data_Table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        for Column_Index in range(self.Data_Table.columnCount()):
            if self.Data_Table.columnWidth(Column_Index) < 100:
                self.Data_Table.setColumnWidth(Column_Index, 120)


    def Copy_Selection(self):
        """Copy selected cells to clipboard in tab-separated format."""
        Selected_Ranges = self.Data_Table.selectedRanges()
        if not Selected_Ranges:
            return

        # Collect all selected rows and columns
        Selected_Rows = set()
        Selected_Columns = set()
        for Range in Selected_Ranges:
            for Row in range(Range.topRow(), Range.bottomRow() + 1):
                Selected_Rows.add(Row)
            for Column in range(Range.leftColumn(), Range.rightColumn() + 1):
                Selected_Columns.add(Column)

        Selected_Rows = sorted(Selected_Rows)
        Selected_Columns = sorted(Selected_Columns)

        # Build tab-separated text from selected cells
        Text_Lines = []
        for Row in Selected_Rows:
            Row_Data = []
            for Column in Selected_Columns:
                Cell_Item = self.Data_Table.item(Row, Column)
                if Cell_Item:
                    Row_Data.append(Cell_Item.text())
                else:
                    Row_Data.append("")
            Text_Lines.append("\t".join(Row_Data))

        # Copy to clipboard
        Clipboard = QApplication.clipboard()
        Clipboard.setText("\n".join(Text_Lines))
