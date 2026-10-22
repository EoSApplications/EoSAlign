# Load libraries
    # Load standard libraries
import re
import numpy as np





# An error in an uploaded fitting data file; the key and values are for Warning_Message
class Fitting_Data_File_Error(Exception):

    def __init__(self, Warning_Key, **Format_Values):
        super().__init__(Warning_Key)
        self.Warning_Key = Warning_Key
        self.Format_Values = Format_Values





# Split a line into its cells. Commas, semicolons and tabs separate cells (so an empty cell is
# noticed); a line with none of them is split on spaces
def Split_A_Line_Into_Cells(Line):

    if re.search(r"[,;\t]", Line):
        Cells = [Cell.strip() for Cell in re.split(r"[,;\t]", Line)]
    else:
        Cells = Line.split()
    # A delimiter at the end of the line does not make another column
    while Cells and not Cells[-1]:
        Cells.pop()

    return Cells


# Convert cells to numbers, returning None if any cell is not a number
def Convert_Cells_To_Numbers(Cells):

    try:
        return [float(Cell) for Cell in Cells] if Cells else None
    except ValueError:
        return None



# Read the columns of numbers in the text of a data file.
# Every line of data must have the same number of values. Lines above the data that are not numbers are a
# header or title and are skipped, as are blank lines and lines starting with #. If the last header line has
# a name for every column those names are returned, otherwise the names are None.
# Returns (names, data) where data has one row per line and one column per column of the file.
def Read_Columns_From_Text(Text):

    Rows = []
    Header_Candidates = []
    Number_Of_Columns = None
    for Line_Number, Line in enumerate(Text.splitlines(), start=1):
        Stripped_Line = Line.strip()
        if not Stripped_Line or Stripped_Line.startswith("#"):
            continue
        Cells = Split_A_Line_Into_Cells(Stripped_Line)
        Values = Convert_Cells_To_Numbers(Cells)
        # A line that is not numbers is a header until the data starts, and an error after
        if Values is None:
            if Rows:
                raise Fitting_Data_File_Error("Fitting File Not Numeric", line_number=Line_Number, line_text=Stripped_Line)
            Header_Candidates.append(Cells)
            continue
        if Number_Of_Columns is None:
            Number_Of_Columns = len(Values)
        elif len(Values) != Number_Of_Columns:
            raise Fitting_Data_File_Error("Fitting File Uneven Columns", line_number=Line_Number, found_count=len(Values), expected_count=Number_Of_Columns)
        Rows.append(Values)

    if not Rows:
        raise Fitting_Data_File_Error("Fitting File Has No Data")

    # The names are the last header line that has a name for every column
    Names = None
    for Cells in reversed(Header_Candidates):
        if len(Cells) == Number_Of_Columns and all(Cells):
            Names = Cells
            break

    return Names, np.array(Rows)



# Get the label of each column for a dropdown: the name from the header if there is one, otherwise the column number
def Get_Column_Labels(Names, Number_Of_Columns):

    Labels = [Names[Index] if Names else f"Column {Index + 1}" for Index in range(Number_Of_Columns)]
    # Names that repeat get their column number so every choice is different
    return [f"{Label} (Column {Index + 1})" if Labels.count(Label) > 1 else Label for Index, Label in enumerate(Labels)]
