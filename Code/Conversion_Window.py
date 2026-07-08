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
from EoS_Math.Build_Dataframe import Calibration_Metadata




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

        # Create descriptive header labels based on column naming conventions
        Header_Labels = []
        for Column_Name in Dataframe.columns.tolist():

            if Column_Name.startswith("Measured_"):
                # Input measured values (non-pressure units)
                Label = Column_Name.replace("Measured_", "Input: ").replace("_Input", "")
                Header_Labels.append(Label)

            elif Column_Name.startswith("Input_Pressure_"):
                # Input pressure values
                Header_Labels.append("Input:\nPressure (GPa)")

            elif "_From_" in Column_Name and not Column_Name.startswith("Pressure_From_"):
                # Intermediate observable: "{Unit}_From_{Study}" or "{Unit}_From_{Study}_({Comp}_{Method})"
                unit_label, study_and_rest = Column_Name.split("_From_", 1)
                if "_(" in study_and_rest:
                    study, comp_method_raw = study_and_rest.rsplit("_(", 1)
                    comp_method = comp_method_raw.rstrip(")").replace("_", " / ")
                    Header_Labels.append(f"{unit_label}\nFrom {study}\n({comp_method})")
                else:
                    Header_Labels.append(f"{unit_label}\nFrom {study_and_rest}")

            elif Column_Name.startswith("Pressure_From_") and "(" in Column_Name:
                # Pressure conversion steps with composition/method info
                Parts = Column_Name.replace("Pressure_From_", "").split("(")
                Study = Parts[0].strip("_")
                Comp_Method = Parts[1].rstrip(")").replace("_", " / ")
                Header_Labels.append(f"Pressure\nFrom {Study}\n({Comp_Method})")

            elif Column_Name.startswith("Assumed_Equal_Pressure_"):
                # Assumption step showing pressure equality between two studies
                Parts = Column_Name.replace("Assumed_Equal_Pressure_", "").split("_=_")
                if len(Parts) == 2:
                    Study_1 = Parts[0]
                    Study_2 = Parts[1]
                    Header_Labels.append(f"Assumption:\n{Study_1}\n= {Study_2}\n(Pressure)")
                else:
                    Header_Labels.append(Column_Name.replace("_", " "))

            elif Column_Name.startswith("Pressure_") and not Column_Name.startswith("Pressure_From_"):
                # Output pressure columns — look up study display name from metadata
                cal_name = Column_Name[len("Pressure_"):]
                metadata = Calibration_Metadata.get(cal_name, {})
                study = metadata.get("Study", cal_name)
                Header_Labels.append(f"Output:\nPressure (GPa)\n{study}")

            elif Column_Name.startswith("Output: "):
                Label = Column_Name[len("Output: "):]
                if Label.endswith("_Unc"):
                    Header_Labels.append(f"Output Unc:\n{Label[:-4]}")
                else:
                    Header_Labels.append(f"Output:\n{Label}")

            elif Column_Name == 'Volume_A3_UnitCell':
                Header_Labels.append("Volume (Å³/unit cell)\n(converted; used for calculations)")

            elif Column_Name == 'Volume_A3_UnitCell_Unc':
                Header_Labels.append("Volume Unc (Å³/unit cell)")

            elif Column_Name.startswith("Input_") and not Column_Name.startswith("Input_Pressure_"):
                # Original input values before unit conversion (e.g. cm³/mol → Å³/unit cell)
                if Column_Name.endswith("_Unc"):
                    original_label = Column_Name[len("Input_"):-len("_Unc")].replace("_per_", "/").replace("_", " ")
                    Header_Labels.append(f"Input Unc (original):\n{original_label}")
                else:
                    original_label = Column_Name[len("Input_"):].replace("_per_", "/").replace("_", " ")
                    Header_Labels.append(f"Input (original):\n{original_label}")

            else:
                # Default formatting: replace underscores with spaces
                if " | " in Column_Name:
                    Parts = Column_Name.split(" | ")
                    Header_Labels.append("\n".join(Parts))
                else:
                    Header_Labels.append(Column_Name.replace("_", " "))

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
