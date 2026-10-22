# Load libraries
    # Load third party libraries
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QAbstractItemView, QApplication, QStyledItemDelegate, QTableWidget, QTableWidgetItem
    # Load local functions from local files
from Themes.Theme import Get_Theme





# Get the style sheet that makes the table match the text boxes of EoSAlign's collapsible sections
def Get_Fitting_Data_Table_Style_Sheet():

    _, _, Colors = Get_Theme()

    return f"""
        QTableWidget#FittingDataTable {{
            background: {Colors['Quaternary_Background']};
            color: {Colors['Primary_Text']};
            border: 1px solid transparent;
            border-radius: 15px;
            font-family: 'Noto Sans Mono', monospace;
            font-size: 12pt;
            selection-background-color: {Colors['Primary_Accent']};
            selection-color: {Colors['Primary_Background']};
        }}
        QTableWidget#FittingDataTable::item {{
            padding: 3px;
            border: none;
        }}
        QTableWidget#FittingDataTable::item:selected, QTableWidget#FittingDataTable::item:focus {{
            background: {Colors['Primary_Accent']};
            color: {Colors['Primary_Background']};
        }}
        QTableWidget#FittingDataTable QHeaderView {{
            background: {Colors['Quaternary_Background']};
        }}
        QTableWidget#FittingDataTable QHeaderView::section {{
            background: {Colors['Quaternary_Background']};
            color: {Colors['Quaternary_Text']};
            border: none;
            padding: 4px;
            font-weight: bold;
        }}
        QTableWidget#FittingDataTable QTableCornerButton::section {{
            background: {Colors['Quaternary_Background']};
            border: none;
        }}
    """


# Draw the lines between the cells of a table but not around the outside edge of the table
class Inner_Grid_Delegate(QStyledItemDelegate):
    def __init__(self, Table, Line_Color):
        super().__init__(Table)

        self.Table = Table
        self.Line_Pen = QPen(QColor(Line_Color), 1)


    def paint(self, Painter, Option, Index):

        super().paint(Painter, Option, Index)
        Visible_Columns = self.Table.Get_Visible_Columns()
        Painter.save()
        Painter.setPen(self.Line_Pen)
        # The line on the right of a cell, except for the last column
        if Visible_Columns and Index.column() != Visible_Columns[-1]:
            Painter.drawLine(Option.rect.topRight(), Option.rect.bottomRight())
        # The line below a cell, except for the last row
        if Index.row() != self.Table.rowCount() - 1:
            Painter.drawLine(Option.rect.bottomLeft(), Option.rect.bottomRight())
        Painter.restore()





# A table that supports Excel style copy and paste, and Delete or Backspace to clear the selected cells
class Fitting_Data_Table(QTableWidget):

    def __init__(self, Rows, Columns, Read_Only=False, Parent=None):
        super().__init__(Rows, Columns, Parent)

        # A read only table can be selected and copied but not changed
        self.Read_Only = Read_Only
        if Read_Only:
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Match the text boxes of the collapsible sections
        self.setObjectName("FittingDataTable")
        self.setStyleSheet(Get_Fitting_Data_Table_Style_Sheet())
        # The lines between the cells are the color of the text, and there are no lines around the outside edge
        self.setShowGrid(False)
        _, _, Colors = Get_Theme()
        self.setItemDelegate(Inner_Grid_Delegate(self, Colors["Primary_Text"]))


    def keyPressEvent(self, event):

        Key = event.key()
        Modifiers = event.modifiers()

        # Copy
        if Modifiers == Qt.ControlModifier and Key == Qt.Key_C:
            self.Copy_Selection()
            return
        # Paste
        if Modifiers == Qt.ControlModifier and Key == Qt.Key_V and not self.Read_Only:
            self.Paste_Clipboard()
            return
        # Clear the selected cells
        if Key in (Qt.Key_Delete, Qt.Key_Backspace) and not self.Read_Only:
            for Index in self.selectedIndexes():
                self.setItem(Index.row(), Index.column(), QTableWidgetItem(""))
            return

        super().keyPressEvent(event)



    # Get the columns that are shown, in order
    def Get_Visible_Columns(self):

        return [Column for Column in range(self.columnCount()) if not self.isColumnHidden(Column)]



    # Copy the selected cells as tab separated text with one line per row
    def Copy_Selection(self):

        Selected_Cells = {(Index.row(), Index.column()) for Index in self.selectedIndexes()}
        if not Selected_Cells:
            return
        # Find the bounding box of the selected cells, using only the columns that are shown
        Top = min(Row for Row, _ in Selected_Cells)
        Bottom = max(Row for Row, _ in Selected_Cells)
        Left = min(Column for _, Column in Selected_Cells)
        Right = max(Column for _, Column in Selected_Cells)
        Columns = [Column for Column in self.Get_Visible_Columns() if Left <= Column <= Right]
        # Build the text, leaving unselected cells in the box empty
        Rows = []
        for Row in range(Top, Bottom + 1):
            Row_Cells = []
            for Column in Columns:
                if (Row, Column) in Selected_Cells:
                    Item = self.item(Row, Column)
                    Row_Cells.append(Item.text() if Item else "")
                else:
                    Row_Cells.append("")
            Rows.append("\t".join(Row_Cells))
        QApplication.clipboard().setText("\n".join(Rows))



    # Paste tab separated clipboard text starting at the current cell, filling only the columns that are shown
    def Paste_Clipboard(self):

        Text = QApplication.clipboard().text()
        if not Text:
            return
        Visible_Columns = self.Get_Visible_Columns()
        Current_Index = self.currentIndex()
        Start_Row = Current_Index.row() if Current_Index.isValid() else 0
        Start_Position = Visible_Columns.index(Current_Index.column()) if Current_Index.isValid() and Current_Index.column() in Visible_Columns else 0
        for Row_Offset, Line in enumerate(Text.splitlines()):
            Row = Start_Row + Row_Offset
            # Add rows as needed
            if Row >= self.rowCount():
                self.setRowCount(Row + 1)
            for Column_Offset, Cell in enumerate(Line.split("\t")):
                Position = Start_Position + Column_Offset
                if Position < len(Visible_Columns):
                    self.setItem(Row, Visible_Columns[Position], QTableWidgetItem(Cell.strip()))
