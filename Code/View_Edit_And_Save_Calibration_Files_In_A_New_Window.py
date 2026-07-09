# Load libraries
    # Load standard libraries
import io
import os
import re
import html as Html_Module
import webbrowser
from datetime import datetime
import yaml
    # Load third party libraries
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QSizePolicy, QScrollArea, QWidget, QGridLayout,
    QComboBox, QTextBrowser, QMenu,
)
from PySide6.QtCore import QEvent, Qt, Signal, QTimer
import Themes.Theme as Theme_Module
    # Load local functions from local files
from Loading_Message import Get_Resource_Path
from MenuBar import MainMenuBar
from Banner import Banner
from Collapsible_Sections import Collapsible_Content_Container, WordWrapDelegate, Dropdown, IS_USER_CALIBRANT_ROLE
from Message_Manager import Warning_Message, Success_Message
from Window_Show_Guard import Guard_Unwanted_Window_Shows
from EoS_Math.Build_Dataframe import (
    Load_The_Calibrations_Into_Memory,
    Calibration_List, Calibration_Metadata,
)
from EoS_Math.Load_Calibration_Files import User_Application_Data_Folder, Archive_Existing_File_With_Version
from Reference_Values_And_Units import (
    Calibration_File_Variable_Information, Function_Information,
    Calibration_Field_Sections, Calibration_Multiline_Fields,
    Material_Information, Method_Units, Volume_Units,
    Equation_Entry_From_Calibration_Entry,
)




# Label helpers

    # Greek letter substitutions used when converting LaTeX to Qt HTML
Greek_Letter_Map = {
    '\\alpha': 'α',  '\\beta': 'β',   '\\gamma': 'γ',  '\\delta': 'δ',
    '\\eta':   'η',  '\\theta': 'θ',  '\\kappa': 'κ',  '\\lambda': 'λ',
    '\\mu':    'μ',  '\\nu':    'ν',  '\\xi':    'ξ',  '\\pi':     'π',
    '\\rho':   'ρ',  '\\sigma': 'σ',  '\\tau':   'τ',  '\\phi':    'φ',
    '\\chi':   'χ',  '\\psi':   'ψ',  '\\omega': 'ω',  '\\infty':  '∞',
    '\\Gamma': 'Γ',  '\\Delta': 'Δ',  '\\Sigma': 'Σ',  '\\Omega':  'Ω',
}

# Convert simple LaTeX math notation to Qt-compatible HTML using subscript and superscript tags
def Convert_Latex_To_Html(Latex_String):
    if not Latex_String:
        # Return the original empty value
        return Latex_String
    Converted_Text = Latex_String
    for Command, Unicode_Character in Greek_Letter_Map.items():
        Converted_Text = Converted_Text.replace(Command, Unicode_Character)
    Converted_Text = re.sub(r'_\{([^}]*)\}', r'<sub>\1</sub>', Converted_Text)
    Converted_Text = re.sub(r'\^\{([^}]*)\}', r'<sup>\1</sup>', Converted_Text)
    Converted_Text = re.sub(r'_([A-Za-z0-9])', r'<sub>\1</sub>', Converted_Text)
    Converted_Text = re.sub(r'\^([A-Za-z0-9])', r'<sup>\1</sup>', Converted_Text)
    # Return the converted HTML text
    return Converted_Text


# Return the method-specific item when a field stores one value per method
def Get_Value_For_Method(Value, Method_Index):
    if isinstance(Value, list):
        Selected_Value = Value[Method_Index] if Method_Index < len(Value) else (Value[-1] if Value else '')
        # Return the selected method-specific value
        return Selected_Value
    # Return the original value or an empty string when it is missing
    return Value or ''


# Build the best available field label using LaTeX, then Unicode, then display text
def Build_Best_Label_Html(Entry, Method_Index=0):
    Latex = Get_Value_For_Method(Entry.get('Latex_Symbol', ''), Method_Index)
    if Latex:
        # Return the LaTeX-derived HTML label
        return Convert_Latex_To_Html(Latex)
    Unicode = Get_Value_For_Method(Entry.get('Unicode_Symbol', ''), Method_Index)
    if Unicode:
        # Return the escaped Unicode label
        return Html_Module.escape(Unicode)
    Display = Get_Value_For_Method(Entry.get('Display_Name', ''), Method_Index)
    # Return the escaped display-name fallback
    return Html_Module.escape(Display or '?')




# Value helpers

# Convert a parsed Python value into the text shown in the form widgets
def Convert_Value_To_Display_Text(Value):
    if Value is None:
        # Return an empty string for missing values
        return ''
    if isinstance(Value, list):
        Display_Text = '\n'.join(str(Item) for Item in Value)
        # Return the multi-line text for list values
        return Display_Text
    if isinstance(Value, bool):
        Display_Text = 'yes' if Value else 'no'
        # Return the normalized yes/no text for booleans
        return Display_Text
    Display_Text = str(Value).strip()
    # Return the stripped text representation
    return Display_Text


# Convert a form text string back into the most appropriate YAML scalar value
def Parse_Calibration_Value(Text):
    Stripped = Text.strip()
    if not Stripped:
        # Return None for blank form fields so they are omitted on save
        return None
    try:
        Parsed = yaml.safe_load(Stripped)
        if isinstance(Parsed, (dict, list)):
            # Return the raw text when parsing produced a complex type
            return Stripped
        # Return the parsed scalar value
        return Parsed
    except Exception:
        # Return the raw text when YAML parsing fails
        return Stripped




# Method filtering helpers

# Check whether a field definition applies to the current method filter
def Check_If_Method_Matches(Entry, Method):
    if Method is None:
        # Return True when all methods should be shown
        return True
    Entry_Methods = Entry['Method']
    if isinstance(Entry_Methods, str):
        Entry_Methods = [Entry_Methods]
    Matches_Method = Method in Entry_Methods
    # Return whether the field matches the active method
    return Matches_Method


# Find the index of the active method inside a method-specific field definition
def Find_Method_Index(Entry, Method):
    if Method is None:
        # Return the first method position when no filter is active
        return 0
    Entry_Methods = Entry['Method']
    if isinstance(Entry_Methods, str):
        Entry_Methods = [Entry_Methods]
    Method_Index = Entry_Methods.index(Method) if Method in Entry_Methods else 0
    # Return the resolved method index
    return Method_Index




# Typo fallbacks for calibration keys found with incorrect spellings in some files
    # These supplement the alternative-key lists already in Calibration_File_Variable_Information
    # Canonical key -> known alternate spellings to try when loading YAML data
Typo_Fallbacks = {
    'is_K0_fixed': ['is_k0_fixed'],
    'notes':       ['note'],
}

    # Fields whose values are always auto-generated on save and never edited by the user
Always_Readonly_Entry_Keys = {'Last Edited'}

    # Entry keys that use a dropdown (QComboBox) instead of a plain text input
    # Note: 'Composition' is excluded here - it uses Composition_Container instead
Combo_Entry_Keys = {
    "Equation of State",
    "Method",
    "Catagory",
    "Is The Initial Bulk Modulus Fixed?",
}

    # Entry keys that are derived from other fields - no form row is created for them
Hidden_Entry_Keys = {"Order"}

    # Alternate V0 entries are handled by the single V0 widget in the UI
Hidden_Entry_Keys.update({
    "V0 per Formula Unit",
    "V0 per Atom",
    "V0 per Centimeter Cubed per Mole",
    "Reference Wavelength (nm)",
    "Reference Frequency",
})

    # Fields that belong to the Pressure Calibration Reference section;
    # each value is a semicolon-separated string with one segment per reference study
Reference_Fields_List = [
    ('cal_to_name',         'Reference Study'),
    ('cal_to_composition',  'Reference Composition'),
    ('cal_to_method',       'Reference Method'),
    ('cal_to_eos',          'Reference Equation of State'),
    ('cal_to_order',        'Reference Equation of State Order'),
    ('cal_to_max_pressure', 'Reference Maximum Pressure'),
    ('cal_to_is_K0_fixed',  'K0 Fixed in Reference Calibration?'),
    ('cal_to_cal',          "Reference's Reference Study"),
]
Reference_Calibration_Keys = [Field_Information[0] for Field_Information in Reference_Fields_List]

    # Placeholder texts shown in empty editable fields
Placeholder_Texts = {
    'Study':              'Enter the study name',
    'Technique':          'Enter experimental technique',
    'DOI':                "Enter the study's corresponding DOI",
    'Data Quality Notes': 'Enter any data quality notes',
    'Notes':              'Enter any notes about this calibration',
    'Atomic Number':      'Enter the atomic number for this composition',
    'Last Edited':        'Enter date this calibration was last edited',
    'Reference Pressure': 'Enter the reference pressure in GPa',
    'Maximum Pressure':   'Enter the maximum pressure in GPa',
    'Full Equation':      'Enter the equation in latex format',
}

    # Entry keys whose input widget gets a unit label to the right of the text box
Unit_Label_Fields = {
    'Reference Pressure': 'GPa',
    'Maximum Pressure':   'GPa',
}

    # Ordered XRD V0 unit variants, from the most-specialized calibration key to the generic one
V0_XRD_Entry_Key_Order = [
    'V0 per Centimeter Cubed per Mole',
    'V0 per Formula Unit',
    'V0 per Atom',
    'V0',
]

    # Entry-key to display unit mapping for the V0 widget
V0_Entry_Key_To_Unit_Text = {
    'V0': 'Å³/unit cell',
    'V0 per Formula Unit': 'Å³/formula unit',
    'V0 per Atom': 'Å³/atom',
    'V0 per Centimeter Cubed per Mole': 'cm³/mol',
}

    # Method-specific unit text for the generic V0 entry
V0_Generic_Unit_Text_By_Method = {
    'XRD': 'Å³/unit cell',
    'Luminescence': 'nm',
    'Raman': 'cm^-1',
}

    # XRD volume-unit dropdown text to entry-key mapping
V0_Unit_Text_To_Entry_Key = {
    'Å³/unit cell': 'V0',
    'Å³/formula unit': 'V0 per Formula Unit',
    'Å³/atom': 'V0 per Atom',
    'cm³/mol': 'V0 per Centimeter Cubed per Mole',
}

    # Required entry keys per equation display name (from function signatures)
Equation_Required_Entry_Keys = {
    # XRD
    'First-Order Murnaghan':               {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Second-Order Murnaghan':              {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus', 'Second Pressure Derivative of the Bulk Modulus'},
    'Second-Order Birch-Murnaghan':        {'V0', 'Initial Bulk Modulus'},
    'Third-Order Birch-Murnaghan':         {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Fourth-Order Birch-Murnaghan':        {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus', 'Second Pressure Derivative of the Bulk Modulus'},
    'Third-Order Rydberg-Vinet':           {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Extended Rydberg-Vinet':              {'V0', 'Initial Bulk Modulus', 'eta', 'beta', 'psi', 'gamma'},
    'Adapted Polynomial (AP2)':            {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Holzapfel (H02)':                     {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Holzapfel (H12)':                     {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus'},
    'Keane':                               {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus', 'Pressure Derivative of the Bulk Modulus at Infinite Pressure'},
    'Rydberg-Stacey':                      {'V0', 'Initial Bulk Modulus', 'First Pressure Derivative of the Bulk Modulus', 'Pressure Derivative of the Bulk Modulus at Infinite Pressure'},
    # Luminescence
    'Linear Scale':                        {'V0', 'A'},
    'Power':                               {'V0', 'A', 'B'},
    'Second-Order Polynomial':             {'V0', 'A', 'B'},
    'Third-Order Modified Freud-Ingalls Form': {'V0', 'A', 'B', 'C'},
    'SrB₄O₇ (Datchi 1997)':               {'V0', 'A', 'B', 'C'},
    # Raman
    'Akahama & Kawamura 2004 (Diamond, Polynomial)':                  {'V0', 'A', 'B', 'C', 'D', 'E', 'F'},
    'Akahama & Kawamura 2006 (Diamond, Finite Strain Approximation)': {'V0', 'A', 'B'},
    'Akahama & Kawamura 2010 (Diamond)':   {'V0', 'A', 'B', 'C', 'D', 'E'},
    'Eremets et al. 2023 (Diamond)':       {'V0', 'A', 'B'},
    'Evans et al. 2005 (Beryllium, Polynomial)':                {'A', 'B', 'C'},
    'Olijnyk et al. 2001 (Beryllium & Rhenium, Polynomial)':    {'V0', 'A', 'B'},
    'Pease et al. 2025 (Rhenium, Polynomial)':                  {'V0', 'A', 'B'},
    'Goncharov et al. 2005 (Cubic Boron Nitride)':              {'V0', 'A', 'B'},
    'Datchi & Canny 2004 (Cubic Boron Nitride)':                {'V0', 'A', 'B', 'C', 'D', 'E', 'F'},
    'Ren et al. 2023 (Cubic Boron Nitride)':                    {'V0', 'A', 'B'},
    'Datchi et al. 2007 (Cubic Boron Nitride)':                 {'V0', 'A'},
}




# No-scroll combo box

# Display a combo box that ignores scroll-wheel events to avoid accidental selection changes
class No_Scroll_Combo_Box(QComboBox):
    def wheelEvent(self, event):
        event.ignore()




# Unit-labelled line edit

# Display a line edit with a fixed unit label on the right side
class Unit_Line_Edit(QWidget):

    def __init__(self, unit_text, parent=None):
        super().__init__(parent)
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(6)
        self.line = QLineEdit()
        self.line.setObjectName('LineEdit')
        Layout.addWidget(self.line)
        Unit_Label = QLabel(unit_text)
        Unit_Label.setObjectName('CollapsibleContentLabel')
        Unit_Label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        Layout.addWidget(Unit_Label)

    def text(self):
        return self.line.text()

    def setText(self, text):
        self.line.setText(text)

    def setReadOnly(self, readonly):
        self.line.setReadOnly(readonly)

    def setPlaceholderText(self, text):
        self.line.setPlaceholderText(text)


# V0 field

# Display the V0 value with either a fixed unit label or an editable XRD volume-unit dropdown
class V0_Field(QWidget):

    unit_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Current_Method = None
        self.Current_Entry_Key = 'V0'

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(6)

        self.line = QLineEdit()
        self.line.setObjectName('LineEdit')
        Layout.addWidget(self.line)

        self.Unit_Label = QLabel()
        self.Unit_Label.setObjectName('CollapsibleContentLabel')
        self.Unit_Label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        Layout.addWidget(self.Unit_Label)

        self.Unit_Combo = No_Scroll_Combo_Box()
        self.Unit_Combo.setObjectName('Dropdown')
        self.Unit_Combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.Unit_Combo.setVisible(False)
        for Entry_Key in ('V0', 'V0 per Formula Unit', 'V0 per Atom', 'V0 per Centimeter Cubed per Mole'):
            self.Unit_Combo.addItem(V0_Entry_Key_To_Unit_Text[Entry_Key], Entry_Key)
        self.Unit_Combo.currentIndexChanged.connect(self.On_Unit_Changed)
        Layout.addWidget(self.Unit_Combo)


    def On_Unit_Changed(self, Index):
        Entry_Key = self.current_entry_key()
        if Entry_Key:
            self.unit_changed.emit(Entry_Key)


    def Configure(self, Method, Entry_Key, Editing):
        self.Current_Method = Method
        self.Current_Entry_Key = Entry_Key
        Display_Information = Get_V0_Display_Information(Entry_Key, Method)
        Unit_Text = Display_Information['Unit_Text']

        if Method == 'XRD' and Editing:
            Combo_Index = self.Unit_Combo.findData(Entry_Key)
            self.Unit_Combo.blockSignals(True)
            self.Unit_Combo.setCurrentIndex(Combo_Index if Combo_Index >= 0 else -1)
            self.Unit_Combo.blockSignals(False)
            self.Unit_Label.setVisible(False)
            self.Unit_Combo.setVisible(True)
        else:
            self.Unit_Label.setText(Unit_Text)
            self.Unit_Label.setVisible(bool(Unit_Text))
            self.Unit_Combo.setVisible(False)


    def current_unit_text(self):
        if not self.Unit_Combo.isHidden():
            # Return the selected XRD volume unit
            return self.Unit_Combo.currentText().strip()
        # Return the fixed label unit text
        return self.Unit_Label.text().strip()


    def current_entry_key(self):
        if not self.Unit_Combo.isHidden():
            Entry_Key = self.Unit_Combo.currentData()
            if Entry_Key:
                # Return the selected XRD V0 entry key
                return Entry_Key
        # Return the current non-XRD or read-only V0 entry key
        return self.Current_Entry_Key


    def text(self):
        return self.line.text()


    def setText(self, text):
        self.line.setText(text)


    def setPlaceholderText(self, text):
        self.line.setPlaceholderText(text)


    def setReadOnly(self, readonly):
        self.line.setReadOnly(readonly)
        if self.Current_Method == 'XRD':
            self.Unit_Combo.setEnabled(not readonly)


# Extract the content of a braced LaTeX group and return the next unread index
def Extract_Braced_Content(Text, Start_Index):
    if Start_Index >= len(Text) or Text[Start_Index] != '{':
        # Return an empty result when the requested position is not a braced group
        return '', Start_Index
    Depth = 0
    for Index in range(Start_Index, len(Text)):
        Char = Text[Index]
        if Char == '{':
            Depth += 1
        elif Char == '}':
            Depth -= 1
            if Depth == 0:
                # Return the braced content and the index after the closing brace
                return Text[Start_Index + 1:Index], Index + 1
    # Return the remaining text when no closing brace was found
    return Text[Start_Index + 1:], len(Text)


# Convert a fraction into a compact inline HTML representation
def Convert_Fraction_To_Html(Numerator_Html, Denominator_Html):
    Fraction_Html = f'({Numerator_Html}/{Denominator_Html})'
    # Return the compact fraction HTML
    return Fraction_Html


# Convert a LaTeX string into approximate rich text for read-only display widgets
def Convert_Latex_To_Display_Html(Latex_String):
    if not Latex_String:
        # Return an empty string when there is nothing to render
        return ''

    Command_Map = {
        '\\cdot': '&middot;',
        '\\times': '&times;',
        '\\pm': '&plusmn;',
        '\\geq': '&ge;',
        '\\leq': '&le;',
        '\\neq': '&ne;',
        '\\approx': '&asymp;',
        '\\infty': '&infin;',
        '\\left(': '(',
        '\\right)': ')',
        '\\left[': '[',
        '\\right]': ']',
        '\\left\\{': '{',
        '\\right\\}': '}',
    }
    Greek_Map = dict(Greek_Letter_Map)
    Greek_Map.update({
        '\\epsilon': 'ε',
        '\\varepsilon': 'ε',
        '\\vartheta': 'ϑ',
        '\\varphi': 'φ',
        '\\varrho': 'ρ',
        '\\upsilon': 'υ',
    })

    # Render a segment of LaTeX-like text into HTML
    def Render_Segment(Text):
        Parts = []
        Index = 0

        while Index < len(Text):
            if Text.startswith('\\begin{aligned}', Index):
                Index += len('\\begin{aligned}')
                continue
            if Text.startswith('\\end{aligned}', Index):
                Index += len('\\end{aligned}')
                continue
            if Text.startswith('\\\\', Index):
                Parts.append('<br/>')
                Index += 2
                continue
            if Text.startswith('\\left', Index):
                Index += len('\\left')
                continue
            if Text.startswith('\\right', Index):
                Index += len('\\right')
                continue
            if Text.startswith('\\frac', Index):
                Next_Index = Index + len('\\frac')
                while Next_Index < len(Text) and Text[Next_Index].isspace():
                    Next_Index += 1
                if Next_Index < len(Text) and Text[Next_Index] == '{':
                    Numerator, Next_Index = Extract_Braced_Content(Text, Next_Index)
                    while Next_Index < len(Text) and Text[Next_Index].isspace():
                        Next_Index += 1
                    if Next_Index < len(Text) and Text[Next_Index] == '{':
                        Denominator, Next_Index = Extract_Braced_Content(Text, Next_Index)
                        Parts.append(
                            Convert_Fraction_To_Html(
                                Render_Segment(Numerator),
                                Render_Segment(Denominator),
                            )
                        )
                        Index = Next_Index
                        continue
            if Text[Index] in '^_':
                Tag = 'sup' if Text[Index] == '^' else 'sub'
                Next_Index = Index + 1
                while Next_Index < len(Text) and Text[Next_Index].isspace():
                    Next_Index += 1
                if Next_Index < len(Text) and Text[Next_Index] == '{':
                    Group_Text, Next_Index = Extract_Braced_Content(Text, Next_Index)
                    Rendered_Group = Render_Segment(Group_Text)
                elif Next_Index < len(Text):
                    Rendered_Group = Html_Module.escape(Text[Next_Index])
                    Next_Index += 1
                else:
                    Rendered_Group = ''
                Parts.append(f'<{Tag}>{Rendered_Group}</{Tag}>')
                Index = Next_Index
                continue
            if Text.startswith('\\text', Index):
                Next_Index = Index + len('\\text')
                while Next_Index < len(Text) and Text[Next_Index].isspace():
                    Next_Index += 1
                if Next_Index < len(Text) and Text[Next_Index] == '{':
                    Group_Text, Next_Index = Extract_Braced_Content(Text, Next_Index)
                    Parts.append(Html_Module.escape(Group_Text))
                    Index = Next_Index
                    continue
            if Text[Index] == '\\':
                Command_End = Index + 1
                while Command_End < len(Text) and Text[Command_End].isalpha():
                    Command_End += 1
                Command = Text[Index:Command_End]
                if Command in Greek_Map:
                    Parts.append(Greek_Map[Command])
                    Index = Command_End
                    continue
                if Command in Command_Map:
                    Parts.append(Command_Map[Command])
                    Index = Command_End
                    continue
                if Command in ('\\ln', '\\exp', '\\sin', '\\cos', '\\tan', '\\log'):
                    Parts.append(Html_Module.escape(Command[1:]))
                    Index = Command_End
                    continue
                if Command_End == Index + 1 and Command_End < len(Text):
                    Parts.append(Html_Module.escape(Text[Command_End]))
                    Index = Command_End + 1
                    continue
                Parts.append(Html_Module.escape(Command[1:]))
                Index = Command_End
                continue
            if Text[Index] in '{}':
                Index += 1
                continue
            if Text[Index] == '&':
                Index += 1
                continue
            if Text[Index] == '\n':
                Parts.append('<br/>')
                Index += 1
                continue
            Parts.append(Html_Module.escape(Text[Index]))
            Index += 1

        return ''.join(Parts)

    Body = Render_Segment(Latex_String.strip().strip('$'))
    Display_Html = (
        '<div style="font-size:14pt; line-height:1.35; white-space: nowrap;">'
        f'{Body}'
        '</div>'
    )
    # Return the generated display HTML
    return Display_Html


# Check whether a text entry is a valid DOI or DOI URL
def Check_If_Text_Is_A_Valid_Doi(Doi_Text):
    Cleaned_Doi_Text = str(Doi_Text or '').strip()
    if not Cleaned_Doi_Text:
        # Return False when there is no DOI text
        return False

    Doi_Pattern = re.compile(
        r'^(?:(?:https?://)?(?:dx\.)?doi\.org/)?10\.\d{4,9}/\S+$',
        re.IGNORECASE
    )
    Is_Valid_Doi = bool(Doi_Pattern.match(Cleaned_Doi_Text))
    # Return whether the text is a valid DOI
    return Is_Valid_Doi


# Convert one DOI entry into a browser-openable URL
def Convert_Doi_Text_To_Url(Doi_Text):
    Cleaned_Doi_Text = str(Doi_Text or '').strip()
    if not Check_If_Text_Is_A_Valid_Doi(Cleaned_Doi_Text):
        # Return an empty URL when the DOI text is not valid
        return ''
    if Cleaned_Doi_Text.lower().startswith(('http://', 'https://')):
        # Return the DOI text unchanged when it is already a full URL
        return Cleaned_Doi_Text
    Doi_Url = f'https://doi.org/{Cleaned_Doi_Text.lstrip("/")}'
    # Return the DOI resolver URL
    return Doi_Url


# Return the theme-matched DOI link color
def Get_Doi_Link_Color(Editor_Widget):
    Palette_Background = Editor_Widget.palette().base().color()
    Is_Dark = Palette_Background.lightness() < 128
    if Is_Dark:
        Colors = Theme_Module.DARK_COLORS
    else:
        Colors = Theme_Module.LIGHT_COLORS
    Doi_Link_Color = Colors['Tertiary_Color']
    # Return the theme-matched DOI link color
    return Doi_Link_Color


# Return the normal textbox text color for non-link DOI text
def Get_Doi_Plain_Text_Color(Editor_Widget):
    Plain_Text_Color = Editor_Widget.palette().text().color().name()
    # Return the normal textbox text color
    return Plain_Text_Color


# Build clickable HTML for one or more DOI lines
def Build_Doi_Display_Html(Doi_Text, Link_Color, Plain_Text_Color, Font_Size__Pt):
    Doi_Lines = [Line.strip() for Line in str(Doi_Text or '').splitlines() if Line.strip()]
    if not Doi_Lines:
        # Return an empty string when there are no DOI lines to display
        return ''

    Html_Lines = []
    for Current_Doi_Line in Doi_Lines:
        Doi_Url = Convert_Doi_Text_To_Url(Current_Doi_Line)
        Escaped_Doi_Text = Html_Module.escape(Current_Doi_Line)
        if Doi_Url:
            Escaped_Doi_Url = Html_Module.escape(Doi_Url, quote=True)
            Html_Lines.append(
                f'<a href="{Escaped_Doi_Url}" '
                f'style="text-decoration: underline;">{Escaped_Doi_Text}</a>'
            )
        else:
            Html_Lines.append(f'<span>{Escaped_Doi_Text}</span>')

    Doi_Display_Html = (
        '<div style="white-space: pre-wrap; margin: 0; padding: 0;">'
        + '<br/>'.join(Html_Lines)
        + '</div>'
    )
    Doi_Display_Html = (
        '<html><head><style>'
        f'* {{ font-family: \'Noto Mono\', monospace; font-size: {Font_Size__Pt}pt; }} '
        f'a {{ color: {Link_Color}; text-decoration: underline; }} '
        f'a:hover {{ color: {Link_Color}; text-decoration: underline; }} '
        f'span {{ color: {Plain_Text_Color}; }} '
        f'body {{ margin: 0; padding: 0; color: {Plain_Text_Color}; background: transparent; line-height: 1.45; }}'
        '</style></head><body>'
        f'{Doi_Display_Html}'
        '</body></html>'
    )
    # Return the rendered DOI HTML
    return Doi_Display_Html


# Split a display name into a plain label and optional unit text
def Split_Display_Name_And_Unit(Display_Name):
    Display_Text = str(Display_Name or '').strip()
    Match = re.match(r'^(.*?)(?:\s*\(([^()]*)\))$', Display_Text)
    if Match:
        Base_Label_Text = Match.group(1).strip()
        Unit_Text = Match.group(2).strip()
    else:
        Base_Label_Text = Display_Text
        Unit_Text = ''
    # Return the split base label and unit text
    return Base_Label_Text, Unit_Text


# Return the display information for the current V0 variant
def Get_V0_Display_Information(Entry_Key, Method):
    Entry = Calibration_File_Variable_Information.get(Entry_Key, {})
    Method_Index = Find_Method_Index(Entry, Method) if Entry_Key == 'V0' else 0

    if Entry_Key == 'V0':
        Display_Name = Get_Value_For_Method(Entry.get('Display_Name', ''), Method_Index)
    else:
        Display_Name = str(Entry.get('Display_Name', '') or '')

    Base_Label_Text, Unit_Text_From_Display_Name = Split_Display_Name_And_Unit(Display_Name)
    if Entry_Key == 'V0':
        Unit_Text = V0_Generic_Unit_Text_By_Method.get(Method, Unit_Text_From_Display_Name)
    else:
        Unit_Text = V0_Entry_Key_To_Unit_Text.get(Entry_Key, Unit_Text_From_Display_Name)
    V0_Display_Information = {
        'Display_Name': Display_Name,
        'Base_Label_Text': Base_Label_Text,
        'Unit_Text': Unit_Text,
        # LaTeX/Unicode-preferred label for the on-screen row (Base_Label_Text is plain-text only, for placeholders)
        'Symbol_Html': Build_Best_Label_Html(Entry, Method_Index),
    }
    # Return the current V0 display information
    return V0_Display_Information


# Find which V0 calibration key is active for the current method and data
def Find_Active_V0_Entry_Key(Data, Method):
    if Method == 'XRD':
        for Entry_Key in V0_XRD_Entry_Key_Order:
            Entry = Calibration_File_Variable_Information.get(Entry_Key, {})
            Calibration_Key = Entry.get('Calibration_File_Variable_Name', '')
            if isinstance(Calibration_Key, list):
                Calibration_Keys = Calibration_Key
            else:
                Calibration_Keys = [Calibration_Key]
            for Current_Calibration_Key in Calibration_Keys:
                if Current_Calibration_Key in Data and str(Data.get(Current_Calibration_Key, '') or '').strip():
                    # Return the first XRD V0 variant with a value
                    return Entry_Key
        # Return the generic XRD V0 entry when no value is present yet
        return 'V0'

    # Return the generic V0 entry for Raman and Luminescence methods
    return 'V0'


# Return the calibration key that should be written for the current V0 entry and method
def Get_Primary_V0_Calibration_Key(Entry_Key, Method):
    if Entry_Key != 'V0':
        Entry = Calibration_File_Variable_Information.get(Entry_Key, {})
        Calibration_Key = Entry.get('Calibration_File_Variable_Name', '')
        if isinstance(Calibration_Key, list):
            # Return the first calibration key for the V0 variant
            return Calibration_Key[0]
        # Return the scalar calibration key for the V0 variant
        return Calibration_Key

    if Method == 'Luminescence':
        # Return the Luminescence V0 calibration key
        return 'lambda_0'
    if Method == 'Raman':
        # Return the Raman V0 calibration key
        return 'V0'
    # Return the XRD V0 calibration key
    return 'V0'


# Return all calibration keys that may store the V0-family value
def Get_All_V0_Calibration_Keys():
    All_V0_Calibration_Keys = []
    for Entry_Key in ('V0', 'V0 per Formula Unit', 'V0 per Atom', 'V0 per Centimeter Cubed per Mole'):
        Entry = Calibration_File_Variable_Information.get(Entry_Key, {})
        Calibration_Key = Entry.get('Calibration_File_Variable_Name', '')
        if isinstance(Calibration_Key, list):
            All_V0_Calibration_Keys.extend(Calibration_Key)
        elif Calibration_Key:
            All_V0_Calibration_Keys.append(Calibration_Key)
    # Return the full list of possible V0 calibration keys
    return All_V0_Calibration_Keys


def Get_Equation_Colors(Editor_Widget):
    """Return (fg_hex, bg_hex) for equation rendering matched to the current theme.

    Detects light vs dark from the editor widget's styled background so the result
    updates correctly whenever the stylesheet is toggled at runtime.
    Light mode → Primary_Text on Quaternary_Background.
    Dark mode  → Quaternary_Text on Quaternary_Background.
    """
    Palette_Bg = Editor_Widget.palette().base().color()
    Is_Dark = Palette_Bg.lightness() < 128
    if Is_Dark:
        Colors = Theme_Module.DARK_COLORS
    else:
        Colors = Theme_Module.LIGHT_COLORS
    Foreground_Color = Colors['Primary_Text'] if not Is_Dark else Colors['Quaternary_Text']
    Background_Color = Colors['Quaternary_Background']
    return Foreground_Color, Background_Color


def Extract_Math_Lines(Text):
    """Split a LaTeX string into individual math-mode lines.

    Handles \\begin{aligned}...\\end{aligned} by stripping the environment,
    splitting on \\\\ line breaks, and removing & alignment markers.
    Returns a list of strings, each suitable for wrapping in $...$
    """
    Aligned_Match = re.search(r'\\begin\{aligned\}(.*?)\\end\{aligned\}', Text, re.DOTALL)
    if not Aligned_Match:
        return [Text]
    Content = Aligned_Match.group(1)
    Parts = re.split(r'\\\\', Content)
    Lines = []
    for Part in Parts:
        Line = Part.replace('&', '').strip()
        if Line:
            Lines.append(Line)
    return Lines if Lines else [Text]


def Render_Latex_To_Pixmap(Latex_String, Fg_Color='#000000', Bg_Color='#ffffff', Font_Size=12.0, Logical_Dpi=96.0, Device_Pixel_Ratio=1.0):
    """Render a bare LaTeX math string to a QPixmap using matplotlib mathtext.

    Uses a solid Bg_Color background so anti-aliasing is computed correctly and
    text edges are crisp. Renders at 2× (Logical_Dpi × Device_Pixel_Ratio) for
    sharpness, then sets the pixmap device-pixel-ratio accordingly.
    """
    if not Latex_String or not Latex_String.strip():
        return None

    Text = Latex_String.strip().strip('$')
    Lines = Extract_Math_Lines(Text)
    N = len(Lines)

    Render_Dpi = Logical_Dpi * Device_Pixel_Ratio * 4

    Fig = Figure(dpi=Render_Dpi, facecolor=Bg_Color)
    Fig.set_size_inches(40, N * 0.6)
    Canvas = FigureCanvasAgg(Fig)
    for i, Line in enumerate(Lines):
        y = 1.0 - (i + 0.5) / N
        Fig.text(0.005, y, f'${Line}$', fontsize=Font_Size, color=Fg_Color,
                 va='center', ha='left', math_fontfamily='cm')
    Canvas.draw()

    Buf = io.BytesIO()
    Fig.savefig(Buf, format='png', bbox_inches='tight',
                facecolor=Bg_Color, dpi=Render_Dpi, pad_inches=0.06)
    Buf.seek(0)

    Pixmap = QPixmap()
    Pixmap.loadFromData(Buf.read())
    if not Pixmap.isNull():
        Pixmap.setDevicePixelRatio(Device_Pixel_Ratio * 4)
    return Pixmap if not Pixmap.isNull() else None


class Latex_Equation_Field(QWidget):
    """Composite field: edit mode shows a QTextEdit; view mode overlays the rendered equation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Stored_Text = ''

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)

        self.editor = QTextEdit()
        self.editor.setObjectName('TextEdit')
        self.editor.setMinimumHeight(70)
        self.editor.setMaximumHeight(110)
        Layout.addWidget(self.editor)

        # Overlay label covering the editor viewport in view mode.
        # Background is set to the theme color so text anti-aliasing is correct.
        self.Overlay = QLabel(self.editor.viewport())
        self.Overlay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.Overlay.hide()

        self.editor.viewport().installEventFilter(self)
        self.editor.textChanged.connect(self.On_Editor_Text_Changed)
        self.Is_Readonly = True
        self.Theme_Refresh_Timer = QTimer(self)
        self.Theme_Refresh_Timer.setSingleShot(True)
        self.Theme_Refresh_Timer.timeout.connect(self.Refresh_Rendered_View)
        self.setReadOnly(True)

    def changeEvent(self, event):
        super().changeEvent(event)
        if self.Is_Readonly and event.type() == QEvent.Type.PaletteChange:
            self.Theme_Refresh_Timer.start(0)

    def eventFilter(self, watched, event):
        if watched is self.editor.viewport() and event.type() == QEvent.Type.Resize:
            self.Overlay.setGeometry(0, 0, watched.width(), watched.height())
            if self.Is_Readonly and self.Stored_Text:
                self.Theme_Refresh_Timer.start(0)
        return super().eventFilter(watched, event)

    def On_Editor_Text_Changed(self):
        if not self.Is_Readonly:
            self.Stored_Text = self.editor.toPlainText()

    def Refresh_Rendered_View(self):
        Text = self.Stored_Text.strip()
        if not Text:
            self.Overlay.clear()
            return

        Fg_Color, Bg_Color = Get_Equation_Colors(self.editor)
        self.Overlay.setStyleSheet(f'background-color: {Bg_Color};')

        Font = self.editor.font()
        Font_Pt = Font.pointSizeF()
        Screen = QApplication.primaryScreen()
        Logical_Dpi = Screen.logicalDotsPerInchY() if Screen else 96.0
        if Font_Pt <= 0:
            Font_Px = Font.pixelSize()
            Font_Pt = (Font_Px * 72.0 / Logical_Dpi) if Font_Px > 0 else 12.0
        Device_Pixel_Ratio = Screen.devicePixelRatio() if Screen else 1.0
        Effective_Dpr = Device_Pixel_Ratio * 4

        try:
            Pixmap = Render_Latex_To_Pixmap(Text, Fg_Color, Bg_Color, Font_Pt, Logical_Dpi, Device_Pixel_Ratio)
            if Pixmap is not None and not Pixmap.isNull():
                # Scale down to fit the viewport width if the equation is too wide.
                Vp = self.editor.viewport()
                Available_W = max(Vp.width() - 16, 1)
                Logical_W = int(Pixmap.width() / Effective_Dpr)
                if Logical_W > Available_W:
                    Pixmap = Pixmap.scaledToWidth(
                        int(Available_W * Effective_Dpr),
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    Pixmap.setDevicePixelRatio(Effective_Dpr)
                self.Overlay.setPixmap(Pixmap)
                return
        except Exception:
            pass
        self.Overlay.setText(Text)

    def setPlaceholderText(self, text):
        self.editor.setPlaceholderText(text)

    def setPlainText(self, text):
        self.Stored_Text = text
        if self.Is_Readonly:
            self.Refresh_Rendered_View()
        else:
            self.editor.blockSignals(True)
            self.editor.setPlainText(text)
            self.editor.blockSignals(False)

    def toPlainText(self):
        return self.Stored_Text if self.Is_Readonly else self.editor.toPlainText()

    def text(self):
        return self.toPlainText()

    def setReadOnly(self, readonly):
        Was_Editing = not self.Is_Readonly
        self.Is_Readonly = readonly
        self.editor.setReadOnly(readonly)
        if readonly:
            # Only snapshot the editor when transitioning from edit mode.
            # Redundant readonly→readonly calls must not overwrite _stored_text,
            # which may have been set directly via setPlainText while already readonly.
            if Was_Editing:
                self.Stored_Text = self.editor.toPlainText()
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)
            vp = self.editor.viewport()
            self.Overlay.setGeometry(0, 0, vp.width(), vp.height())
            self.Overlay.raise_()
            self.Overlay.show()
            self.Refresh_Rendered_View()
        else:
            self.Overlay.hide()
            self.editor.blockSignals(True)
            self.editor.setPlainText(self.Stored_Text)
            self.editor.blockSignals(False)


# DOI field

# Display DOI HTML with a link-aware right-click context menu
class Doi_Text_Browser(QTextBrowser):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)


    def contextMenuEvent(self, Event):
        Link_Url = self.anchorAt(Event.pos())
        if not Link_Url:
            super().contextMenuEvent(Event)
            return

        Context_Menu = QMenu(self)

        Open_Link_Action = Context_Menu.addAction('Open Link in Browser')
        Copy_Link_Action = Context_Menu.addAction('Copy Link Address')
        Context_Menu.addSeparator()
        Copy_Action = Context_Menu.addAction('Copy')
        Select_All_Action = Context_Menu.addAction('Select All')

        Chosen_Action = Context_Menu.exec(Event.globalPos())
        if Chosen_Action is Open_Link_Action:
            webbrowser.open_new_tab(Link_Url)
        elif Chosen_Action is Copy_Link_Action:
            QApplication.clipboard().setText(Link_Url)
        elif Chosen_Action is Copy_Action:
            self.copy()
        elif Chosen_Action is Select_All_Action:
            self.selectAll()


# Display DOI text as editable multi-line text in edit mode and clickable links in read-only mode
class Doi_Field(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Stored_Text = ''
        self.Is_Readonly = True

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)

        self.editor = QTextEdit()
        self.editor.setObjectName('TextEdit')
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        Layout.addWidget(self.editor)

        self.Overlay = Doi_Text_Browser(self.editor.viewport())
        self.Overlay.setFrameStyle(0)
        self.Overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.Overlay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.Overlay.setStyleSheet('background: transparent; border: none;')
        self.Overlay.anchorClicked.connect(self.Open_Doi_Link)
        self.Overlay.document().setDocumentMargin(0)
        self.Overlay.hide()

        self.editor.viewport().installEventFilter(self)
        self.editor.textChanged.connect(self.On_Editor_Text_Changed)
        self.setReadOnly(True)
        self.Update_Field_Height()


    def eventFilter(self, watched, event):
        if watched is self.editor.viewport() and event.type() == QEvent.Type.Resize:
            self.Overlay.setGeometry(0, 0, watched.width(), watched.height())
            self.Update_Field_Height()
        # Return the base event-filter result
        return super().eventFilter(watched, event)


    def On_Editor_Text_Changed(self):
        if not self.Is_Readonly:
            self.Stored_Text = self.editor.toPlainText()
        self.Update_Field_Height()


    def Open_Doi_Link(self, Url):
        Doi_Url = Url.toString().strip()
        if Doi_Url:
            webbrowser.open_new_tab(Doi_Url)


    def Refresh_Readonly_View(self):
        Link_Color = Get_Doi_Link_Color(self.editor)
        Plain_Text_Color = Get_Doi_Plain_Text_Color(self.editor)
        Font = self.editor.font()
        Font_Size__Pt = Font.pointSizeF()
        if Font_Size__Pt <= 0:
            Font_Size__Pt = 10.0
        Doi_Display_Html = Build_Doi_Display_Html(
            self.Stored_Text,
            Link_Color,
            Plain_Text_Color,
            Font_Size__Pt,
        )
        self.Overlay.setHtml(Doi_Display_Html)
        self.Update_Field_Height()


    def Update_Field_Height(self):
        Font_Metrics = self.editor.fontMetrics()
        Document_Margin = self.editor.document().documentMargin()
        Vertical_Padding = 14
        Single_Line_Height = int(Font_Metrics.lineSpacing() + (2 * Document_Margin) + Vertical_Padding)

        Available_Width = max(self.editor.viewport().width() - 2, 1)
        Active_Document = self.Overlay.document() if self.Is_Readonly else self.editor.document()
        Active_Document.setTextWidth(Available_Width)
        Document_Height = Active_Document.documentLayout().documentSize().height()
        Target_Height = max(Single_Line_Height, int(Document_Height + Vertical_Padding))

        self.editor.setFixedHeight(Target_Height)
        self.setFixedHeight(Target_Height)


    def setPlaceholderText(self, text):
        self.editor.setPlaceholderText(text)


    def setPlainText(self, text):
        self.Stored_Text = str(text or '')
        if self.Is_Readonly:
            self.Refresh_Readonly_View()
        else:
            self.editor.blockSignals(True)
            self.editor.setPlainText(self.Stored_Text)
            self.editor.blockSignals(False)


    def toPlainText(self):
        if self.Is_Readonly:
            # Return the stored DOI text in read-only mode
            return self.Stored_Text
        # Return the live editor DOI text in edit mode
        return self.editor.toPlainText()


    def text(self):
        # Return the current DOI text
        return self.toPlainText()


    def setReadOnly(self, readonly):
        Was_Editing = not self.Is_Readonly
        self.Is_Readonly = readonly
        self.editor.setReadOnly(readonly)

        if readonly:
            if Was_Editing:
                self.Stored_Text = self.editor.toPlainText()
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)
            Viewport = self.editor.viewport()
            self.Overlay.setGeometry(0, 0, Viewport.width(), Viewport.height())
            self.Overlay.raise_()
            self.Overlay.show()
            self.Refresh_Readonly_View()
        else:
            self.Overlay.hide()
            self.editor.blockSignals(True)
            self.editor.setPlainText(self.Stored_Text)
            self.editor.blockSignals(False)




# Composition container

# Display a composition selector that can switch between a known-material dropdown and free text
class Composition_Container(QWidget):
    """Composition input: dropdown of known materials that can switch to a free-text QLineEdit.

    Emits composition_changed(str) whenever the selected/typed value changes.
    """

    composition_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(2)

        # dropdown of known materials
        self.combo = No_Scroll_Combo_Box()
        self.combo.setObjectName('Dropdown')
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo.setPlaceholderText('Select a composition')

        Seen_Labels = set()
        for Key, Entry in Material_Information.items():
            Display_Val = Entry.get('Display_Label', Key)
            if Display_Val not in Seen_Labels:
                self.combo.addItem(Display_Val, Key)
                Seen_Labels.add(Display_Val)

        self.combo.addItem('-- Enter different composition --', '__custom__')
        self.combo.setCurrentIndex(-1)

        # free-text fallback
        self.line = QLineEdit()
        self.line.setObjectName('LineEdit')
        self.line.setPlaceholderText('Enter a composition')
        self.line.setVisible(False)

        Layout.addWidget(self.combo)
        Layout.addWidget(self.line)

        self.Is_Custom_Mode = False
        self.combo.currentIndexChanged.connect(self.On_Combo_Index_Changed)
        self.line.textChanged.connect(lambda t: self.composition_changed.emit(t))

    # internal helpers

    def On_Combo_Index_Changed(self, Index):
        if Index < 0:
            return
        if self.combo.itemData(Index) == '__custom__':
            self.Switch_To_Text()
        else:
            self.composition_changed.emit(self.combo.currentText())

    def Switch_To_Text(self, Text=''):
        self.Is_Custom_Mode = True
        self.combo.setVisible(False)
        self.line.setVisible(True)
        Old = self.line.blockSignals(True)
        self.line.setText(Text)
        self.line.blockSignals(Old)
        self.line.setFocus()

    def Switch_To_Combo(self):
        self.Is_Custom_Mode = False
        self.line.setVisible(False)
        self.combo.setVisible(True)

    # public interface

    def Is_Custom_Mode_Active(self):
        return self.Is_Custom_Mode

    def current_text(self):
        """Display text from whichever widget is active."""
        return self.line.text() if self.Is_Custom_Mode else self.combo.currentText()

    def current_value(self):
        """Material key for known compositions, raw text for custom entries."""
        if self.Is_Custom_Mode:
            return self.line.text().strip()
        Data = self.combo.currentData()
        if Data is not None and Data != '__custom__':
            return Data
        return self.combo.currentText().strip()

    def populate(self, Comp_Key, Display_Val):
        """Load a composition value: use the dropdown for known materials, text box for custom."""
        if Comp_Key and Comp_Key in Material_Information:
            Idx = self.combo.findData(Comp_Key)
            if Idx < 0:
                Idx = self.combo.findText(Display_Val)
            if Idx >= 0:
                Old = self.combo.blockSignals(True)
                self.combo.setCurrentIndex(Idx)
                self.combo.blockSignals(Old)
                self.Switch_To_Combo()
                return
        if Display_Val or Comp_Key:
            self.Switch_To_Text(Display_Val or Comp_Key)
        else:
            Old = self.combo.blockSignals(True)
            self.combo.setCurrentIndex(-1)
            self.combo.blockSignals(Old)
            self.Switch_To_Combo()

    def set_readonly(self, Readonly):
        """Apply or remove read-only state to both internal widgets."""
        self.combo.setEnabled(not Readonly)
        self.line.setReadOnly(Readonly)




# Single calibration reference entry

# Display one pressure-calibration reference inside its own collapsible section
class Reference_Entry(QWidget):
    """One pressure-calibration reference, displayed inside a nested collapsible section.

    The section title updates live as the user types in the Reference Study field.
    """

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.Reference_Index = index
        self.Field_Lines = {}   # calibration_key -> QLineEdit
        self.Field_Labels = {}   # calibration_key -> QLabel
        self.Section = None
        self.Setup_Ui()

    def Setup_Ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 4, 0, 4)
        outer_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName('CollapsibleContent')
        grid = QGridLayout(content)
        grid.setContentsMargins(8, 4, 8, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 220)

        for row, (calibration_key, label_text) in enumerate(Reference_Fields_List):
            lbl = QLabel(label_text + ':')
            lbl.setObjectName('CollapsibleContentLabel')
            lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            grid.addWidget(lbl, row, 0)
            self.Field_Labels[calibration_key] = lbl

            if calibration_key == 'cal_to_is_K0_fixed':
                widget = No_Scroll_Combo_Box()
                widget.setObjectName('Dropdown')
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.addItem('Select yes or no', '')
                widget.addItem('Yes', 'yes')
                widget.addItem('No',  'no')
                widget.setCurrentIndex(-1)
                widget.setEnabled(False)
            else:
                widget = QLineEdit()
                widget.setObjectName('LineEdit')
                widget.setPlaceholderText(f'Enter {label_text}')
                widget.setReadOnly(True)
                if calibration_key == 'cal_to_name':
                    widget.textChanged.connect(self.On_Name_Changed)

            grid.addWidget(widget, row, 1)
            self.Field_Lines[calibration_key] = widget

        self.Section = Collapsible_Content_Container(
            f'Reference {self.Reference_Index + 1}',
            content,
            Show_Container_Title=True,
            Initially_Show_Container=True,
            Expanding_Content=True,
            Drop_Shadow=4,
        )
        outer_layout.addWidget(self.Section)

    def On_Name_Changed(self, text):
        title = text.strip() or f'Reference {self.Reference_Index + 1}'
        self.Section.Set_The_Section_Title_Text(title)

    def Get_Widget_Text(self, widget):
        if isinstance(widget, QComboBox):
            # Empty-string data marks the placeholder item - treat as no value
            data = widget.currentData()
            return '' if not data else data
        return widget.text().strip()

    def set_values(self, values_dict):
        for calibration_key, widget in self.Field_Lines.items():
            val = values_dict.get(calibration_key, '') or ''
            old = widget.blockSignals(True)
            if isinstance(widget, QComboBox):
                key = val.strip().lower()
                idx = widget.findData(key) if key else 0
                widget.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                widget.setText(val)
            widget.blockSignals(old)
        name_widget = self.Field_Lines.get('Reference Study')
        if name_widget is not None:
            self.On_Name_Changed(name_widget.text())

    def get_values(self):
        return {k: self.Get_Widget_Text(w) for k, w in self.Field_Lines.items()}

    def set_readonly(self, readonly, apply_visibility=True):
        for widget in self.Field_Lines.values():
            if isinstance(widget, QComboBox):
                widget.setEnabled(not readonly)
            else:
                widget.setReadOnly(readonly)
        if apply_visibility:
            self.Apply_Visibility(editing=not readonly)

    def Apply_Visibility(self, editing):
        for calibration_key, widget in self.Field_Lines.items():
            lbl     = self.Field_Labels.get(calibration_key)
            visible = editing or bool(self.Get_Widget_Text(widget))
            widget.setVisible(visible)
            if lbl:
                lbl.setVisible(visible)

    def has_data(self):
        return any(self.Get_Widget_Text(w) for w in self.Field_Lines.values())




# Panel containing all reference entries

# Manage the full list of nested reference-entry widgets and the add button
class References_Panel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Entries = []
        self.Is_Readonly = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self.Entries_Layout = QVBoxLayout()
        self.Entries_Layout.setContentsMargins(0, 0, 0, 0)
        self.Entries_Layout.setSpacing(4)
        outer.addLayout(self.Entries_Layout)

        self.Add_Button = QPushButton('Add Calibration Reference')
        self.Add_Button.setObjectName('Primary_Button')
        self.Add_Button.clicked.connect(self.Add_Empty_Entry)
        self.Add_Button.setVisible(False)
        outer.addWidget(self.Add_Button, alignment=Qt.AlignHCenter)
        outer.setContentsMargins(0, 0, 0, 10)

    def Add_Entry(self, values=None, apply_visibility=True):
        idx   = len(self.Entries)
        entry = Reference_Entry(idx)
        if values:
            entry.set_values(values)
        entry.set_readonly(self.Is_Readonly, apply_visibility=apply_visibility)
        self.Entries.append(entry)
        self.Entries_Layout.addWidget(entry)
        return entry

    def Add_Empty_Entry(self):
        self.Add_Entry(apply_visibility=True)

    def populate(self, data_dict):
        for entry in self.Entries:
            entry.setParent(None)
        self.Entries.clear()

        split_data = {}
        max_count  = 0
        for key in Reference_Calibration_Keys:
            val = data_dict.get(key)
            if val is not None and str(val).strip():
                parts = [p.strip() for p in str(val).split(';')]
                split_data[key] = parts
                max_count = max(max_count, len(parts))

        for i in range(max_count):
            values = {key: (parts[i] if i < len(parts) else '')
                      for key, parts in split_data.items()}
            self.Add_Entry(values, apply_visibility=False)

    def get_data(self):
        result = {}
        for key in Reference_Calibration_Keys:
            parts = [entry.get_values().get(key, '') for entry in self.Entries]
            non_empty = [p for p in parts if p]
            result[key] = '; '.join(non_empty) if non_empty else None
        return result

    def set_readonly(self, readonly):
        self.Is_Readonly = readonly
        for entry in self.Entries:
            entry.set_readonly(readonly)
        self.Add_Button.setVisible(not readonly)

    def has_data(self):
        return bool(self.Entries)




# Main dialog
class View_Edit_And_Save_Calibration_Files_In_A_New_Window(QDialog):
    """
    Unified YAML calibration viewer, editor, and new-entry dialog.

    mode='view_edit'  Opens an existing calibration read-only; user can enable editing
                      and save changes to User_Edited_Calibration_Files (original preserved).
    mode='new'        Opens a blank form in edit mode; saves to User_Entered_Calibration_Files.

    The form is built automatically from Calibration_Field_Sections and
    Calibration_File_Variable_Information in Reference_Values_And_Units.py.
    Only fields that match the loaded calibration's method are shown.
    Labels use LaTeX -> Unicode -> Display_Name priority.
    Equation, Method, Category, and K0 Fixed use smart dropdowns.
    Composition uses a dropdown with a "Enter different composition" escape hatch.
    """

    # Emitted with the calibration key after a successful save
    calibration_saved = Signal(str)

    def __init__(self, Parent=None, Calibration_File_Path=None, mode='view_edit', start_with_no_selection=False):
        super().__init__(Parent)
        self.Mode = mode
        self.Is_Editing = (mode == 'new')
        self.Start_With_No_Selection = start_with_no_selection
        self.Calibration_Was_Saved = False
        self.Field_Widgets = {}     # entry_key -> QLineEdit | QTextEdit | QComboBox | Composition_Container | Unit_Line_Edit
        self.Label_Widgets = {}     # entry_key -> QLabel (paired with Field_Widgets)
        self.Section_Widgets = []     # [(Collapsible_Content_Container, Section_Name, [entry_keys])]
        self.Equation_Variables_Entry_Keys = set()  # entry keys in the "Equation Variables" section
        self.Equation_Combo = None   # QComboBox for "Equation of State"
        self.Method_Combo = None   # QComboBox for "Method"
        self.Composition_Container_Widget = None  # Composition_Container for "Composition"
        self.Composition_Combo = None   # inner QComboBox inside Composition_Container_Widget
        self.Atomic_Number_Widget = None   # QLineEdit for "Atomic Number" (auto-filled)
        self.References_Panel_Widget = None   # References_Panel for "Pressure Calibration Reference"
        self.V0_Widget = None
        self.Current_V0_Entry_Key = 'V0'
        self.Is_Updating_Combos = False  # prevents circular signals between equation/method
        self.Current_Method = ...    # Ellipsis = sentinel, means form not yet built
        self.Composition_Selector = None
        self.Study_Selector = None

        # Default to the first calibration when no path is supplied in view_edit mode
        if (
            Calibration_File_Path is None
            and mode == 'view_edit'
            and not self.Start_With_No_Selection
            and Calibration_List
        ):
            First_Key      = Calibration_List[0][0]
            Calibration_File_Path = Calibration_Metadata.get(First_Key, {}).get('file_path')
        self.Calibration_File_Path = Calibration_File_Path

        # Full window title bar with minimize, maximize, and close buttons.
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle(
            'Enter New Calibration' if mode == 'new' else 'Calibration Viewer'
        )
        self.setWindowIcon(QIcon(Get_Resource_Path('Graphics/EoS_With_Sun.png')))
        self.setMinimumSize(840, 700)

        # Root layout (zero margins so banner touches edges)
        self.Dialog_Layout = QVBoxLayout(self)
        self.Dialog_Layout.setContentsMargins(0, 0, 0, 0)
        self.Dialog_Layout.setSpacing(0)

        # Menu bar and banner
        self.Menu_Bar = MainMenuBar(self)
        self.Menu_Bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Dialog_Layout.addWidget(self.Menu_Bar)

        self.Banner_Widget = Banner('', Get_Resource_Path('Graphics/EoS_With_Sun.png'))
        self.Dialog_Layout.addWidget(self.Banner_Widget)

        # Mode-specific top content
        if mode == 'view_edit':
            self.Build_Calibration_Selector()
        else:
            Info_Label = QLabel(
                'Fill in the calibration details below. '
                'The Study field is required. '
                'Leave unused fields blank - they will not be written to the file.'
            )
            Info_Label.setObjectName('CollapsibleContentLabel')
            Info_Label.setWordWrap(True)
            Info_Label.setContentsMargins(16, 8, 16, 4)
            self.Dialog_Layout.addWidget(Info_Label)

        self.User_Edited_Banner = QLabel()
        self.User_Edited_Banner.setObjectName('UserEditedBanner')
        self.User_Edited_Banner.setVisible(False)

        # Scrollable form area
        self.Scroll_Area = QScrollArea()
        self.Scroll_Area.setWidgetResizable(True)
        self.Dialog_Layout.addWidget(self.Scroll_Area)

        self.Form_Container = QWidget()
        self.Form_Container.setObjectName('CalibrationFormContainer')
        self.Form_Layout = QVBoxLayout(self.Form_Container)
        self.Form_Layout.setContentsMargins(16, 12, 16, 16)
        self.Form_Layout.setSpacing(4)
        self.Scroll_Area.setWidget(self.Form_Container)

        # In new-entry mode build the full form immediately (all methods shown)
        if mode == 'new':
            self.Current_Method = None
            self.Build_Form(Method=None)
            # Make all fields immediately editable since Is_Editing is True from the start
            self.Apply_Widget_Styles()
            self.Auto_Fill_Last_Edited()

        self.Build_Buttons()

        # In view_edit mode the form is built when the first file is loaded
        if mode == 'view_edit' and self.Calibration_File_Path:
            self.Sync_Selector_To_File(self.Calibration_File_Path)
            self.Load_Form_From_File(self.Calibration_File_Path)

        self.Has_Shown_Once = False


    def show(self):
        """Show without a white flash by appearing off-screen first."""
        if not self.Has_Shown_Once:
            self.Has_Shown_Once = True
            screen = QApplication.primaryScreen()
            sg = screen.availableGeometry()
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


    # Calibration selector (view_edit mode only)

    def Build_Calibration_Selector(self):
        Container = QWidget()
        Container.setObjectName('FormSelectorContainer')
        Row = QHBoxLayout(Container)
        Row.setContentsMargins(16, 8, 16, 4)
        Row.setSpacing(10)

        Composition_Label = QLabel('Composition:')
        Composition_Label.setObjectName('CollapsibleTitle')
        Row.addWidget(Composition_Label)

        self.Composition_Selector = No_Scroll_Combo_Box()
        self.Composition_Selector.setObjectName('Dropdown')
        self.Composition_Selector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.Composition_Selector.setMaxVisibleItems(20)
        self.Composition_Selector.setPlaceholderText('Select a composition')
        for Composition_Key in self.Get_Available_Composition_Keys():
            Display_Label = Material_Information.get(Composition_Key, {}).get('Display_Label', Composition_Key)
            self.Composition_Selector.addItem(Display_Label, Composition_Key)
        self.Composition_Selector.setCurrentIndex(-1)
        self.Composition_Selector.currentIndexChanged.connect(self.On_Selector_Composition_Changed)
        Row.addWidget(self.Composition_Selector)

        Study_Label = QLabel('Study:')
        Study_Label.setObjectName('CollapsibleTitle')

        # Wrap the study label, dropdown, and footnote in their own column so the
        # footnote row sits directly under the dropdown and can be indented to
        # line up with where the "*" appears in the dropdown's selected text.
        Study_Column_Layout = QVBoxLayout()
        Study_Column_Layout.setContentsMargins(0, 0, 0, 0)
        Study_Column_Layout.setSpacing(2)
        Study_Row_Layout = QHBoxLayout()
        Study_Row_Layout.setContentsMargins(0, 0, 0, 0)
        Study_Row_Layout.setSpacing(10)
        Study_Row_Layout.addWidget(Study_Label)

        self.Study_Selector = Dropdown()
        self.Study_Selector.setObjectName('Dropdown')
        self.Study_Selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Study_Selector.setMaxVisibleItems(20)
        self.Study_Selector.setPlaceholderText('Select a study')
        self.Study_Selector.view().setItemDelegate(
            WordWrapDelegate(self.Study_Selector.view(), self.Study_Selector)
        )
        self.Study_Selector.currentIndexChanged.connect(self.On_Selector_Study_Changed)
        Study_Row_Layout.addWidget(self.Study_Selector)
        Study_Row_Layout.setStretchFactor(self.Study_Selector, 1)
        Study_Column_Layout.addLayout(Study_Row_Layout)

        # Footnote row — shown only when the currently selected study is user-edited or entered.
        # Indented past the "Study:" label and spacing, plus the dropdown's own internal
        # text inset, so it lines up with where the "*" appears in the dropdown text.
        Footnote_Left_Margin = Study_Label.sizeHint().width() + Study_Row_Layout.spacing() + 9
        Caution_Color = Theme_Module.Get_Theme()[2].get('Caution_Text')
        self.Calibration_Selector_Footnote = QLabel("* indicates user edited or entered calibrant")
        self.Calibration_Selector_Footnote.setStyleSheet(f"font-size: 8pt; color: {Caution_Color};")
        self.Calibration_Selector_Footnote.setWordWrap(True)
        self.Calibration_Selector_Footnote.setContentsMargins(Footnote_Left_Margin, 0, 16, 4)
        self.Calibration_Selector_Footnote.setVisible(False)
        Study_Column_Layout.addWidget(self.Calibration_Selector_Footnote)

        Row.addLayout(Study_Column_Layout, 1)
        self.Dialog_Layout.addWidget(Container)


    def Sync_Selector_To_File(self, File_Path):
        """Select the dropdown item matching the given file."""
        if not File_Path:
            return

        Exact_Key = os.path.splitext(os.path.basename(File_Path))[0]
        Calibration_Key = Exact_Key
        if Calibration_Key not in Calibration_Metadata:
            Calibration_Key = Exact_Key.replace(' - User Edited', '')

        Metadata = Calibration_Metadata.get(Calibration_Key, {})
        Composition_Key = str(Metadata.get('Composition', '') or '').strip()
        if not Composition_Key or self.Composition_Selector is None or self.Study_Selector is None:
            return

        Composition_Index = self.Composition_Selector.findData(Composition_Key)
        if Composition_Index >= 0:
            self.Composition_Selector.blockSignals(True)
            self.Composition_Selector.setCurrentIndex(Composition_Index)
            self.Composition_Selector.blockSignals(False)

        self.Populate_Study_Selector(Composition_Key, Selected_Calibration_Key=Calibration_Key)


    def Get_Available_Composition_Keys(self):
        Seen_Composition_Keys = set()
        Ordered_Composition_Keys = []
        for Calibration_Key, Calibration_Label in Calibration_List:
            Metadata = Calibration_Metadata.get(Calibration_Key, {})
            Composition_Key = str(Metadata.get('Composition', '') or '').strip()
            if Composition_Key and Composition_Key not in Seen_Composition_Keys:
                Seen_Composition_Keys.add(Composition_Key)
                Ordered_Composition_Keys.append(Composition_Key)

        Sorted_Composition_Keys = sorted(
            Ordered_Composition_Keys,
            key=lambda Composition_Key: Material_Information.get(Composition_Key, {}).get('Display_Label', Composition_Key)
        )
        # Return the sorted list of available composition keys
        return Sorted_Composition_Keys


    def Build_Study_Selector_Label(self, Calibration_Key):
        Metadata = Calibration_Metadata.get(Calibration_Key, {})
        Prefix = ''
        if Metadata.get('is_user_edited') or Metadata.get('is_user_entered'):
            Prefix = '* '
        Study_Label = str(Metadata.get('Study', Calibration_Key) or Calibration_Key)
        Composition_Label = str(Metadata.get('Composition', '') or '')
        Method_Label = str(Metadata.get('Method', '') or '')
        Equation_Of_State_Label = str(Metadata.get('Equation of State', '') or '')
        Is_K0_Fixed_Label = str(Metadata.get('Is The Initial Bulk Modulus Fixed?', '') or '')
        Cal_To_Label = str(Metadata.get('Reference Study', '') or '')
        Max_Pressure_Label = str(Metadata.get('Maximum Pressure', '') or '')
        Pressure_Transmitting_Medium_Label = str(Metadata.get('Pressure Transmitting Medium', '') or '')
        Study_Display_Label = (
            f'{Prefix}{Study_Label} | {Composition_Label} | {Method_Label} | '
            f'{Equation_Of_State_Label} | K0 Fixed: {Is_K0_Fixed_Label} | '
            f'cal_to: {Cal_To_Label} | Max Pressure: {Max_Pressure_Label} GPa | '
            f'PTM: {Pressure_Transmitting_Medium_Label}'
        ).replace('\n', '').strip()
        # Return the study selector label
        return Study_Display_Label


    def Get_Study_Sort_Key(self, Display_Label):
        Study_Name, Separator, Remainder = str(Display_Label or '').partition(' | ')
        Normalized_Study_Name = Study_Name.replace('*', '').strip().casefold()
        Normalized_Remainder = Remainder.casefold() if Separator else ''
        Study_Sort_Key = (Normalized_Study_Name, Normalized_Remainder, str(Display_Label or '').casefold())
        # Return the case-insensitive study sort key
        return Study_Sort_Key


    def Populate_Study_Selector(self, Composition_Key, Selected_Calibration_Key=None):
        if self.Study_Selector is None:
            return

        Study_Items = []
        for Calibration_Key, Calibration_Label in Calibration_List:
            Metadata = Calibration_Metadata.get(Calibration_Key, {})
            Entry_Composition_Key = str(Metadata.get('Composition', '') or '').strip()
            if Entry_Composition_Key != str(Composition_Key or '').strip():
                continue
            Study_Items.append((self.Build_Study_Selector_Label(Calibration_Key), Calibration_Key))

        Study_Items.sort(key=lambda Item: self.Get_Study_Sort_Key(Item[0]))

        self.Study_Selector.blockSignals(True)
        self.Study_Selector.clear()
        for Display_Label, Calibration_Key in Study_Items:
            self.Study_Selector.addItem(Display_Label, Calibration_Key)
            self.Study_Selector.setItemData(
                self.Study_Selector.count() - 1, Display_Label.startswith('* '), IS_USER_CALIBRANT_ROLE
            )
        self.Study_Selector.setCurrentIndex(-1)
        self.Study_Selector.blockSignals(False)

        if Selected_Calibration_Key is not None:
            for Current_Index in range(self.Study_Selector.count()):
                if self.Study_Selector.itemData(Current_Index) == Selected_Calibration_Key:
                    self.Study_Selector.blockSignals(True)
                    self.Study_Selector.setCurrentIndex(Current_Index)
                    self.Study_Selector.blockSignals(False)
                    break

        self.Update_Calibration_Selector_Footnote()


    # Show the caution footnote only when the currently selected study is flagged
    def Update_Calibration_Selector_Footnote(self):
        if not hasattr(self, 'Calibration_Selector_Footnote') or self.Study_Selector is None:
            return
        Calibration_Key = self.Study_Selector.currentData()
        Metadata = Calibration_Metadata.get(Calibration_Key) if Calibration_Key else None
        Is_User_Calibrant = bool(Metadata and (Metadata.get('is_user_edited') or Metadata.get('is_user_entered')))
        self.Calibration_Selector_Footnote.setVisible(Is_User_Calibrant)


    def On_Selector_Composition_Changed(self, Index):
        if self.Composition_Selector is None:
            return
        Composition_Key = self.Composition_Selector.itemData(Index)
        if not Composition_Key:
            if self.Study_Selector is not None:
                self.Study_Selector.blockSignals(True)
                self.Study_Selector.clear()
                self.Study_Selector.blockSignals(False)
            self.Update_Calibration_Selector_Footnote()
            return

        self.Populate_Study_Selector(Composition_Key)


    def On_Selector_Study_Changed(self, Index):
        if self.Study_Selector is None:
            return
        self.Update_Calibration_Selector_Footnote()
        Key = self.Study_Selector.itemData(Index)
        if not Key:
            return
        File_Path = Calibration_Metadata.get(Key, {}).get('file_path')
        if File_Path and os.path.exists(File_Path):
            self.Calibration_File_Path = File_Path
            # Reset edit state before loading so the rebuilt form starts read-only
            self.Is_Editing = False
            self.Load_Form_From_File(File_Path)
            if hasattr(self, 'Enable_Edit_Button'):
                self.Enable_Edit_Button.setText('Enable Editing')
            if hasattr(self, 'Save_Changes_Button'):
                self.Save_Changes_Button.setVisible(False)


    # Form construction

    def Build_Form(self, Method=None):
        """Build collapsible sections from Calibration_Field_Sections, filtered by Method."""
        self.Field_Widgets = {}
        self.Label_Widgets = {}
        self.Section_Widgets = []
        self.Equation_Variables_Entry_Keys = set()
        self.Equation_Combo = None
        self.Method_Combo = None
        self.Composition_Container_Widget = None
        self.Composition_Combo = None
        self.Atomic_Number_Widget = None
        self.References_Panel_Widget = None
        self.V0_Widget = None

        for Section_Name, Entry_Keys in Calibration_Field_Sections.items():

            # Special case: replace the entire Pressure Calibration Reference section
            # with a References_Panel that renders one nested collapsible per study
            if Section_Name == 'Pressure Calibration Reference':
                Has_Method_Match = any(
                    Check_If_Method_Matches(Calibration_File_Variable_Information.get(ek, {}), Method)
                    for ek in Entry_Keys
                    if ek not in Hidden_Entry_Keys
                    and Calibration_File_Variable_Information.get(ek) is not None
                )
                if not Has_Method_Match:
                    continue
                self.References_Panel_Widget = References_Panel()
                Section = Collapsible_Content_Container(
                    'Pressure Calibration Reference',
                    self.References_Panel_Widget,
                    Show_Container_Title=True,
                    Initially_Show_Container=(self.Mode != 'new'),
                    Expanding_Content=True,
                    Drop_Shadow=8,
                )
                self.Form_Layout.addWidget(Section)
                self.Section_Widgets.append((Section, Section_Name, []))
                continue

            # Collect entries that are relevant to the current method
            Visible_Entries = []
            for Entry_Key in Entry_Keys:
                if Entry_Key in Hidden_Entry_Keys:
                    continue
                Entry = Calibration_File_Variable_Information.get(Entry_Key)
                if Entry is None:
                    continue
                if not Check_If_Method_Matches(Entry, Method):
                    continue
                Midx = Find_Method_Index(Entry, Method)
                Visible_Entries.append((Entry_Key, Entry, Midx))

            if not Visible_Entries:
                continue

            # Build grid of label + input widget pairs for this section
            Content_Widget = QWidget()
            Content_Widget.setObjectName('CollapsibleContent')
            Grid = QGridLayout(Content_Widget)
            Grid.setContentsMargins(8, 4, 8, 12)
            Grid.setHorizontalSpacing(12)
            Grid.setVerticalSpacing(6)
            Grid.setColumnStretch(1, 1)
            Grid.setColumnMinimumWidth(0, 220)

            Row_Idx = 0
            for Entry_Key, Entry, Midx in Visible_Entries:

                # Label - HTML rich text with LaTeX/Unicode/Display_Name priority
                Label_Html = Build_Best_Label_Html(Entry, Midx) + ':'
                Lbl = QLabel()
                Lbl.setText(Label_Html)
                Lbl.setObjectName('CollapsibleContentLabel')
                Lbl.setTextFormat(Qt.RichText)
                Lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                Lbl.setWordWrap(True)
                Grid.addWidget(Lbl, Row_Idx, 0)

                # Input widget
                if Entry_Key == 'Composition':
                    Widget = self.Build_Composition_Container()
                elif Entry_Key == 'V0':
                    Widget = V0_Field()
                    Widget.unit_changed.connect(self.On_V0_Unit_Changed)
                elif Entry_Key in Combo_Entry_Keys:
                    Widget = self.Create_Combo_Widget(Entry_Key, Method)
                elif Entry_Key == 'DOI':
                    Widget = Doi_Field()
                    if self.Mode == 'new' and Entry_Key in Placeholder_Texts:
                        Widget.setPlaceholderText(Placeholder_Texts[Entry_Key])
                elif Entry_Key == 'Full Equation':
                    Widget = Latex_Equation_Field()
                    if Entry_Key in Placeholder_Texts:
                        Widget.setPlaceholderText(Placeholder_Texts[Entry_Key])
                elif Entry_Key in Calibration_Multiline_Fields:
                    Widget = QTextEdit()
                    Widget.setObjectName('TextEdit')
                    Widget.setMinimumHeight(70)
                    Widget.setMaximumHeight(110)
                    if Entry_Key in Placeholder_Texts:
                        Widget.setPlaceholderText(Placeholder_Texts[Entry_Key])
                elif Entry_Key in Unit_Label_Fields:
                    Widget = Unit_Line_Edit(Unit_Label_Fields[Entry_Key])
                    if Entry_Key in Placeholder_Texts:
                        Widget.setPlaceholderText(Placeholder_Texts[Entry_Key])
                else:
                    Widget = QLineEdit()
                    Widget.setObjectName('LineEdit')
                    if Entry_Key in Placeholder_Texts:
                        Widget.setPlaceholderText(Placeholder_Texts[Entry_Key])
                    elif Section_Name == 'Equation Variables':
                        Display_Name = Get_Value_For_Method(Entry.get('Display_Name', ''), Midx)
                        Widget.setPlaceholderText(f'Enter the {Display_Name} value')
                    elif Section_Name == 'Experimental Setup':
                        Display_Name = Get_Value_For_Method(Entry.get('Display_Name', ''), Midx)
                        Widget.setPlaceholderText(f'Enter {Display_Name}')

                # Track special-purpose widgets by entry key
                if Entry_Key == 'Equation of State':
                    self.Equation_Combo = Widget
                elif Entry_Key == 'Method':
                    self.Method_Combo = Widget
                elif Entry_Key == 'Composition':
                    self.Composition_Container_Widget = Widget
                    self.Composition_Combo = Widget.combo
                elif Entry_Key == 'Atomic Number':
                    self.Atomic_Number_Widget = Widget
                elif Entry_Key == 'V0':
                    self.V0_Widget = Widget

                # All fields start read-only; _Apply_Widget_Styles switches them
                self.Set_Widget_Readonly(Widget)
                Grid.addWidget(Widget, Row_Idx, 1)
                self.Field_Widgets[Entry_Key] = Widget
                self.Label_Widgets[Entry_Key] = Lbl

                if Entry_Key == 'V0':
                    self.Update_V0_Field_Presentation()
                Row_Idx += 1

            # Wrap the grid in a collapsible section card
            Initially_Open = (Section_Name == 'Study Information') if self.Mode == 'new' else True
            Section = Collapsible_Content_Container(
                Section_Name,
                Content_Widget,
                Show_Container_Title=True,
                Initially_Show_Container=Initially_Open,
                Expanding_Content=True,
                Drop_Shadow=8,
            )
            self.Form_Layout.addWidget(Section)
            Section_Entry_Keys = [ek for ek, _, _ in Visible_Entries]
            self.Section_Widgets.append((Section, Section_Name, Section_Entry_Keys))
            if Section_Name == 'Equation Variables':
                self.Equation_Variables_Entry_Keys = set(Section_Entry_Keys)

        self.Form_Layout.addStretch()


    def Build_Composition_Container(self):
        """Create the Composition_Container and connect its signal."""
        Container = Composition_Container()
        Container.composition_changed.connect(self.On_Composition_Changed)
        return Container


    def Create_Combo_Widget(self, Entry_Key, Method):
        """Create and configure a QComboBox for the given entry key."""
        Combo = No_Scroll_Combo_Box()
        Combo.setObjectName('Dropdown')
        Combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if Entry_Key == 'Equation of State':
            self.Build_Equation_Combo_Items(Combo, Method_Filter=Method)
            Combo.currentIndexChanged.connect(self.On_Equation_Changed)

        elif Entry_Key == 'Method':
            Combo.setPlaceholderText('Select a method')
            for Method_Name in Method_Units.keys():
                Combo.addItem(Method_Name, Method_Name)
            Combo.setCurrentIndex(-1)
            Combo.currentIndexChanged.connect(self.On_Method_Changed)

        elif Entry_Key == 'Catagory':
            Combo.setPlaceholderText('Select a category')
            for Cat in ('1', '2', '3'):
                Combo.addItem(Cat, Cat)
            Combo.setCurrentIndex(-1)

        elif Entry_Key == 'Is The Initial Bulk Modulus Fixed?':
            Combo.setPlaceholderText('Select yes or no')
            Combo.addItem('yes', 'yes')
            Combo.addItem('no',  'no')
            Combo.setCurrentIndex(-1)

        return Combo


    def Build_Equation_Combo_Items(self, Combo, Method_Filter=None):
        """Populate Combo with equation display names, optionally filtered by method.
        Preserves the current selection if it is still available after filtering.
        """
        Current_Data  = Combo.currentData() or {}
        Current_Eos   = Current_Data.get('eos')
        Current_Order = Current_Data.get('order')

        Combo.blockSignals(True)
        Combo.clear()
        Combo.setPlaceholderText('Select an equation')

        Restore_Index = -1
        for Display_Name, Info in Function_Information.items():
            if Method_Filter is not None and Info['Method'] != Method_Filter:
                continue
            Item_Data = {
                'eos':    Info['Calibration_File_EoS_Name'],
                'order':  Info['Calibration_File_EoS_Order'],
                'method': Info['Method'],
            }
            Combo.addItem(Display_Name, Item_Data)
            if Item_Data['eos'] == Current_Eos and Item_Data['order'] == Current_Order:
                Restore_Index = Combo.count() - 1

        Combo.setCurrentIndex(Restore_Index)
        Combo.blockSignals(False)


    def Rebuild_Form(self, Method):
        """Clear and rebuild the form for a different method filter."""
        while self.Form_Layout.count():
            Item = self.Form_Layout.takeAt(0)
            if Item.widget():
                Item.widget().setParent(None)
        self.Build_Form(Method)


    def Build_Buttons(self):
        Container = QWidget()
        Container.setObjectName('ButtonContainer')
        Row = QHBoxLayout(Container)
        Row.setContentsMargins(16, 8, 16, 12)

        self.Enable_Edit_Button = QPushButton('Enable Editing')
        self.Enable_Edit_Button.setObjectName('Secondary_Button')
        self.Enable_Edit_Button.clicked.connect(self.Edit_Calibration_File)
        Row.addWidget(self.Enable_Edit_Button)

        self.Save_Changes_Button = QPushButton('Save Changes')
        self.Save_Changes_Button.setObjectName('Primary_Button')
        self.Save_Changes_Button.clicked.connect(self.Save_Changes_To_Calibration_File)
        Row.addWidget(self.Save_Changes_Button)

        self.Save_Button = QPushButton('Save Calibration')
        self.Save_Button.setObjectName('Primary_Button')
        self.Save_Button.clicked.connect(self.Save_New_Calibration)
        Row.addWidget(self.Save_Button)

        self.Close_Button = QPushButton('Close')
        self.Close_Button.setObjectName('TertiaryButton')
        self.Close_Button.clicked.connect(self.close)
        Row.addWidget(self.Close_Button)

        self.Dialog_Layout.addWidget(Container)
        self.Update_Action_Button_Visibility()


    def Update_Action_Button_Visibility(self):
        Is_New_Mode = (self.Mode == 'new')

        if hasattr(self, 'Enable_Edit_Button'):
            self.Enable_Edit_Button.setVisible(not Is_New_Mode)
            self.Enable_Edit_Button.setText('Disable Editing' if self.Is_Editing else 'Enable Editing')

        if hasattr(self, 'Save_Changes_Button'):
            self.Save_Changes_Button.setVisible((not Is_New_Mode) and self.Is_Editing)

        if hasattr(self, 'Save_Button'):
            self.Save_Button.setVisible(Is_New_Mode and self.Is_Editing)


    # Equation / Method / Composition combo signal handlers

    def On_Equation_Changed(self, Index):
        """When an equation is selected, auto-set the method combo, sync the Full Equation
        field, and refresh which Equation Variables are visible.
        """
        if self.Is_Updating_Combos:
            return
        self.Is_Updating_Combos = True
        try:
            Data = self.Equation_Combo.itemData(Index) if self.Equation_Combo else None
            if Data and self.Method_Combo is not None:
                Eq_Method = Data.get('method', '')
                Midx = self.Method_Combo.findData(Eq_Method)
                if Midx >= 0:
                    self.Method_Combo.setCurrentIndex(Midx)
        finally:
            self.Is_Updating_Combos = False

        self.Sync_Full_Equation_From_Eos()
        self.Apply_View_Visibility()


    def On_Method_Changed(self, Index):
        """When a method is selected, filter the equation combo to that method's equations."""
        if self.Is_Updating_Combos:
            return
        self.Is_Updating_Combos = True
        try:
            Method_Text   = self.Method_Combo.currentText() if self.Method_Combo else ''
            Method_Filter = Method_Text if Method_Text else None
            if self.Equation_Combo is not None:
                self.Build_Equation_Combo_Items(self.Equation_Combo, Method_Filter=Method_Filter)
        finally:
            self.Is_Updating_Combos = False

        self.Update_V0_Field_Presentation()
        self.Sync_Full_Equation_From_Eos()
        self.Apply_View_Visibility()


    def On_Composition_Changed(self, Text):
        """When composition changes, auto-fill and lock/unlock the atomic number field."""
        self.Update_Atomic_Number_Lock(Text, Autofill=True)


    def On_V0_Unit_Changed(self, Entry_Key):
        if self.Current_Method != 'XRD':
            return
        self.Current_V0_Entry_Key = Entry_Key or 'V0'
        self.Update_V0_Field_Presentation()


    def Update_V0_Field_Presentation(self):
        if self.V0_Widget is None:
            return

        if self.Method_Combo is not None and self.Method_Combo.currentText().strip():
            Method = self.Method_Combo.currentText().strip()
        elif isinstance(self.Current_Method, str):
            Method = self.Current_Method
        else:
            Method = None

        if Method == 'XRD':
            Entry_Key = self.Current_V0_Entry_Key or 'V0'
        else:
            Entry_Key = 'V0'
            self.Current_V0_Entry_Key = 'V0'

        Display_Information = Get_V0_Display_Information(Entry_Key, Method)
        Base_Label_Text = Display_Information['Base_Label_Text']
        Display_Name = Display_Information['Display_Name']

        V0_Label = self.Label_Widgets.get('V0')
        if V0_Label is not None:
            V0_Label.setText(Display_Information['Symbol_Html'] + ':')
            V0_Label.setTextFormat(Qt.RichText)

        V0_Unc_Label = self.Label_Widgets.get('V0 Uncertainty')
        if V0_Unc_Label is not None:
            V0_Unc_Entry = Calibration_File_Variable_Information.get('V0 Uncertainty', {})
            V0_Unc_Method_Index = Find_Method_Index(V0_Unc_Entry, Method)
            V0_Unc_Label.setText(Build_Best_Label_Html(V0_Unc_Entry, V0_Unc_Method_Index) + ':')
            V0_Unc_Label.setTextFormat(Qt.RichText)

        V0_Unc_Widget = self.Field_Widgets.get('V0 Uncertainty')
        if V0_Unc_Widget is not None:
            if self.Is_Editing:
                V0_Unc_Widget.setPlaceholderText(f'Enter the {Base_Label_Text} Uncertainty value')
            else:
                V0_Unc_Widget.setPlaceholderText('')

        if self.Is_Editing:
            Unit_Text = Display_Information['Unit_Text']
            if Unit_Text:
                Placeholder_Text = f'Enter the {Base_Label_Text} ({Unit_Text}) value'
            else:
                Placeholder_Text = f'Enter the {Base_Label_Text} value'
            self.V0_Widget.setPlaceholderText(Placeholder_Text)
        else:
            self.V0_Widget.setPlaceholderText('')

        self.V0_Widget.Configure(Method, Entry_Key, self.Is_Editing)


    def Sync_Full_Equation_From_Eos(self):
        Full_Eq_Widget = self.Field_Widgets.get('Full Equation')
        if Full_Eq_Widget is None or self.Equation_Combo is None:
            return
        Data = self.Equation_Combo.currentData()
        if not Data:
            if isinstance(Full_Eq_Widget, (Latex_Equation_Field, Doi_Field, QTextEdit)):
                Full_Eq_Widget.setPlainText('')
            else:
                Full_Eq_Widget.setText('')
            return
        Display_Name = Equation_Entry_From_Calibration_Entry.get(
            (Data.get('eos'), Data.get('order'), Data.get('method'))
        )
        if Display_Name is None:
            if isinstance(Full_Eq_Widget, (Latex_Equation_Field, Doi_Field, QTextEdit)):
                Full_Eq_Widget.setPlainText('')
            else:
                Full_Eq_Widget.setText('')
            return
        Latex_Eq = Function_Information.get(Display_Name, {}).get('Latex_Equation', '')
        if isinstance(Full_Eq_Widget, (Latex_Equation_Field, Doi_Field, QTextEdit)):
            Full_Eq_Widget.setPlainText(Latex_Eq)
        else:
            Full_Eq_Widget.setText(Latex_Eq)


    def Update_Atomic_Number_Lock(self, Composition_Text, Autofill=False):
        """Lock atomic number (and auto-fill it) when a known material is selected;
        unlock it when the user enters a custom composition.
        """
        if self.Atomic_Number_Widget is None:
            return
        Display_To_Key = {v['Display_Label']: k for k, v in Material_Information.items()}
        Key = Display_To_Key.get(Composition_Text.strip())
        if Key is not None:
            Z = (Material_Information.get(Key) or {}).get('Atomic_Number')
            if Z is not None:
                # Fill when the user actively changed composition (Autofill + editing),
                # OR when the field is empty - for example, the YAML had no atomic_number entry.
                Field_Is_Empty = not self.Atomic_Number_Widget.text().strip()
                if (Autofill and self.Is_Editing) or Field_Is_Empty:
                    self.Atomic_Number_Widget.setText(str(Z))
            self.Atomic_Number_Widget.setReadOnly(True)
        else:
            if self.Is_Editing:
                self.Atomic_Number_Widget.setReadOnly(False)


    # Form data loading

    def Load_Form_From_File(self, File_Path):
        """Parse the YAML at File_Path, rebuild the form if the method changed,
        populate all fields, and collapse sections that have no data.
        """
        self.Calibration_File_Path = File_Path
        try:
            with open(File_Path, 'r', encoding='utf-8') as f:
                Data = yaml.safe_load(f) or {}
        except Exception as e:
            Warning_Message(self, "Could Not Load The Calibration File", error=e)
            return

        # Rebuild the form when the method changes (XRD/Raman/Luminescence show different fields)
        Method = Data.get('method')
        if Method != self.Current_Method:
            self.Current_Method = Method
            self.Rebuild_Form(Method)

        Key  = os.path.splitext(os.path.basename(File_Path))[0]
        Meta = Calibration_Metadata.get(Key.replace(' - User Edited', ''), {})
        Is_User_Edited = (
            Meta.get('is_user_edited', False) or
            os.path.basename(os.path.dirname(File_Path)) in
            ('User_Edited_Yaml_Files', 'User_Edited_Calibration_Files')
        )
        self.User_Edited_Banner.setVisible(False)

        Prefix = '* ' if Is_User_Edited else ''
        self.setWindowTitle(f'YAML Calibration: {Prefix}{os.path.basename(File_Path)}')

        self.Populate_Fields(Data)

        # Collapse sections where every displayed field is empty
        for Section, Section_Name, Entry_Keys in self.Section_Widgets:
            if Section_Name == 'Pressure Calibration Reference':
                Has_Data = self.References_Panel_Widget is not None and self.References_Panel_Widget.has_data()
            else:
                Has_Data = any(
                    self.Get_Widget_Text(self.Field_Widgets[ek]).strip()
                    for ek in Entry_Keys if ek in self.Field_Widgets
                )
            Section.Expand_Or_Collapse_Section(Has_Data)

        self.Apply_Widget_Styles()
        self.Apply_View_Visibility()


    def Populate_Fields(self, Data):
        """Fill all form fields from a YAML data dict."""
        Method = str(Data.get('method', '') or self.Current_Method or '')
        self.Current_V0_Entry_Key = Find_Active_V0_Entry_Key(Data, Method)

        # Block equation and method combo signals during population
        for Widget in (self.Equation_Combo, self.Method_Combo):
            if Widget is not None:
                Widget.blockSignals(True)
        # Composition container handles its own signal blocking inside populate()

        for Entry_Key, Widget in self.Field_Widgets.items():
            if isinstance(Widget, Composition_Container):
                self.Populate_Composition_Field(Widget, Data)
            elif isinstance(Widget, QComboBox):
                self.Populate_Combo_Field(Entry_Key, Widget, Data)
            else:
                self.Populate_Text_Field(Entry_Key, Widget, Data)

        for Widget in (self.Equation_Combo, self.Method_Combo):
            if Widget is not None:
                Widget.blockSignals(False)

        # Populate the pressure calibration reference panel
        if self.References_Panel_Widget is not None:
            self.References_Panel_Widget.populate(Data)

        # Sync Full Equation from the loaded EoS (only fills if yaml had no equation_full value)
        self.Update_V0_Field_Presentation()
        self.Sync_Full_Equation_From_Eos()

        # After population, update atomic number lock without auto-filling
        Comp_Text = (
            self.Composition_Container_Widget.current_text()
            if self.Composition_Container_Widget is not None
            else (self.Composition_Combo.currentText() if self.Composition_Combo else '')
        )
        self.Update_Atomic_Number_Lock(Comp_Text, Autofill=False)


    def Populate_Text_Field(self, Entry_Key, Widget, Data):
        """Populate a QLineEdit or QTextEdit from YAML data."""
        if Entry_Key == 'V0' and isinstance(Widget, V0_Field):
            Method = str(Data.get('method', '') or self.Current_Method or '')
            self.Current_V0_Entry_Key = Find_Active_V0_Entry_Key(Data, Method)
            if self.Current_V0_Entry_Key == 'V0':
                Value = None
                for Generic_V0_Calibration_Key in ('V0', 'lambda_0', 'nu_0', 'nu0'):
                    if Generic_V0_Calibration_Key in Data:
                        Value = Data.get(Generic_V0_Calibration_Key)
                        if Value is not None and str(Value).strip():
                            break
            else:
                Active_Calibration_Key = Get_Primary_V0_Calibration_Key(self.Current_V0_Entry_Key, Method)
                Value = Data.get(Active_Calibration_Key)
            Display = Convert_Value_To_Display_Text(Value)
            Widget.setText(Display)
            self.Update_V0_Field_Presentation()
            return

        Entry     = Calibration_File_Variable_Information.get(Entry_Key, {})
        Calibration_Keys = Entry.get('Calibration_File_Variable_Name', '')
        if isinstance(Calibration_Keys, str):
            Calibration_Keys = [Calibration_Keys]

        Value = None
        for Yk in Calibration_Keys:
            if Yk in Data:
                Value = Data[Yk]
                break
            for Alt in Typo_Fallbacks.get(Yk, []):
                if Alt in Data:
                    Value = Data[Alt]
                    break
            if Value is not None:
                break

        Display = Convert_Value_To_Display_Text(Value)
        if isinstance(Widget, (Latex_Equation_Field, Doi_Field, QTextEdit)):
            Widget.setPlainText(Display)
        elif isinstance(Widget, Unit_Line_Edit):
            Widget.setText(Display)
        else:
            Widget.setText(Display)


    def Populate_Combo_Field(self, Entry_Key, Widget, Data):
        """Populate a QComboBox from YAML data using entry-key-specific logic."""
        if Entry_Key == 'Equation of State':
            Eos       = str(Data.get('eos', '') or '')
            Order_Raw = Data.get('order')
            # Keep None as None (unordered equations); convert integers/strings to str
            Order     = str(Order_Raw) if Order_Raw is not None and Order_Raw != '' else None
            Method    = str(Data.get('method', '') or '') or None
            Display_Name = Equation_Entry_From_Calibration_Entry.get((Eos, Order, Method))
            # Fallback: some equations (e.g. AP2) store Calibration_File_EoS_Order=None even
            # though YAML files may have an 'order' value.  Try matching by EoS name alone.
            if Display_Name is None and Order is not None:
                Display_Name = Equation_Entry_From_Calibration_Entry.get((Eos, None, Method))
            Idx = Widget.findText(Display_Name) if Display_Name else -1
            Widget.setCurrentIndex(Idx if Idx >= 0 else -1)

        elif Entry_Key == 'Method':
            Method_Text = str(Data.get('method', '') or '')
            Idx = Widget.findText(Method_Text)
            Widget.setCurrentIndex(Idx if Idx >= 0 else -1)

        elif Entry_Key == 'Catagory':
            Cat_Val = str(Data.get('catagory', '') or '')
            Idx = Widget.findText(Cat_Val)
            Widget.setCurrentIndex(Idx if Idx >= 0 else -1)

        elif Entry_Key == 'Is The Initial Bulk Modulus Fixed?':
            Raw = Data.get('Is The Initial Bulk Modulus Fixed?')
            if Raw is None:
                Raw = Data.get('is_k0_fixed')
            if isinstance(Raw, bool):
                Val = 'yes' if Raw else 'no'
            else:
                Val = str(Raw).strip().lower() if Raw is not None else ''
            Idx = Widget.findText(Val)
            Widget.setCurrentIndex(Idx if Idx >= 0 else 0)


    def Populate_Composition_Field(self, Container, Data):
        """Populate the Composition_Container from YAML data."""
        Comp_Key    = str(Data.get('composition', '') or '')
        Display_Val = Material_Information.get(Comp_Key, {}).get('Display_Label', Comp_Key)
        Container.populate(Comp_Key, Display_Val)


    def Get_Widget_Text(self, Widget):
        if isinstance(Widget, Composition_Container):
            return Widget.current_text()
        if isinstance(Widget, QComboBox):
            return Widget.currentText()
        if isinstance(Widget, V0_Field):
            return Widget.text()
        if isinstance(Widget, Unit_Line_Edit):
            return Widget.text()
        if isinstance(Widget, (Latex_Equation_Field, Doi_Field)):
            return Widget.toPlainText()
        return Widget.toPlainText() if isinstance(Widget, QTextEdit) else Widget.text()


    # Edit / read mode

    def Set_Widget_Readonly(self, Widget):
        """Make a widget read-only while keeping its normal input-box styling."""
        if isinstance(Widget, Composition_Container):
            Widget.set_readonly(True)
        elif isinstance(Widget, V0_Field):
            Widget.setReadOnly(True)
        elif isinstance(Widget, QComboBox):
            Widget.setEnabled(False)
        elif isinstance(Widget, Unit_Line_Edit):
            Widget.setReadOnly(True)
        else:
            Widget.setReadOnly(True)


    def Set_Widget_Editable(self, Widget):
        """Make a widget editable."""
        if isinstance(Widget, Composition_Container):
            Widget.set_readonly(False)
        elif isinstance(Widget, V0_Field):
            Widget.setReadOnly(False)
        elif isinstance(Widget, QComboBox):
            Widget.setEnabled(True)
        elif isinstance(Widget, Unit_Line_Edit):
            Widget.setReadOnly(False)
        else:
            Widget.setReadOnly(False)


    def Apply_Widget_Styles(self):
        """Apply read or edit styling to all widgets based on the current edit state."""
        for Entry_Key, Widget in self.Field_Widgets.items():
            Always_Readonly = Entry_Key in Always_Readonly_Entry_Keys
            if Entry_Key == 'Full Equation':
                self.Set_Widget_Readonly(Widget)
            elif self.Is_Editing and not Always_Readonly:
                self.Set_Widget_Editable(Widget)
            else:
                self.Set_Widget_Readonly(Widget)

        if self.References_Panel_Widget is not None:
            self.References_Panel_Widget.set_readonly(not self.Is_Editing)

        self.Update_V0_Field_Presentation()

        # Atomic number lock depends on composition selection, not just edit mode
        Comp_Text = (
            self.Composition_Container_Widget.current_text()
            if self.Composition_Container_Widget is not None
            else (self.Composition_Combo.currentText() if self.Composition_Combo else '')
        )
        self.Update_Atomic_Number_Lock(Comp_Text, Autofill=False)


    def Get_Required_Entry_Keys_For_Selected_Eos(self):
        """Return the set of required entry keys for the currently selected equation,
        or None if no equation is selected.
        """
        if self.Equation_Combo is None:
            return None
        Data = self.Equation_Combo.currentData()
        if not Data:
            return None
        Display_Name = Equation_Entry_From_Calibration_Entry.get(
            (Data.get('eos'), Data.get('order'), Data.get('method'))
        )
        if Display_Name is None:
            return None
        return Equation_Required_Entry_Keys.get(Display_Name)


    def Apply_View_Visibility(self):
        """In view mode, hide field rows that have no value. In edit mode show all rows.
        For Equation Variables, also filter to only show fields required by the selected equation.
        """
        Required_Keys = self.Get_Required_Entry_Keys_For_Selected_Eos()

        for Entry_Key in self.Field_Widgets:
            Widget = self.Field_Widgets[Entry_Key]
            Label  = self.Label_Widgets.get(Entry_Key)

            if Entry_Key in self.Equation_Variables_Entry_Keys:
                Is_Required = (Required_Keys is None) or (Entry_Key in Required_Keys)
                Has_Value   = bool(self.Get_Widget_Text(Widget).strip())
                Is_Uncertainty = 'Uncertainty' in Entry_Key
                if Is_Uncertainty:
                    Base_Key = Entry_Key[:-len(' Uncertainty')] if Entry_Key.endswith(' Uncertainty') else None
                    Unc_Entry   = Calibration_File_Variable_Information.get(Entry_Key, {})
                    Unc_Methods = Unc_Entry.get('Method', [])
                    if isinstance(Unc_Methods, str):
                        Unc_Methods = [Unc_Methods]
                    Eq_Method = (self.Equation_Combo.currentData() or {}).get('method', '') if self.Equation_Combo else ''
                    Method_Compatible = (not Eq_Method) or (not Unc_Methods) or (Eq_Method in Unc_Methods)
                    Base_Is_Required = Method_Compatible and (
                        (Required_Keys is None) or (Base_Key is not None and Base_Key in Required_Keys)
                    )
                if self.Is_Editing:
                    if Is_Uncertainty:
                        Visible = Base_Is_Required
                    else:
                        Visible = Is_Required
                else:
                    if Is_Uncertainty:
                        Visible = Has_Value and Base_Is_Required
                    else:
                        Visible = Is_Required and Has_Value
            else:
                Visible = self.Is_Editing or bool(self.Get_Widget_Text(Widget).strip())

            Widget.setVisible(Visible)
            if Label:
                Label.setVisible(Visible)


    def Auto_Fill_Last_Edited(self):
        """Fill the Last Edited field with today's date (m/d/yyyy)."""
        Widget = self.Field_Widgets.get('Last Edited')
        if Widget is None:
            return
        today = datetime.now()
        Date_Str = f'{today.month}/{today.day}/{today.year}'
        if isinstance(Widget, QTextEdit):
            Widget.setPlainText(Date_Str)
        else:
            Widget.setText(Date_Str)


    def Set_Edit_Mode(self, Editing):
        self.Is_Editing = Editing
        self.Apply_Widget_Styles()
        self.Apply_View_Visibility()
        if Editing:
            self.Auto_Fill_Last_Edited()
        self.Update_Action_Button_Visibility()


    def Edit_Calibration_File(self):
        """Toggle between view and edit modes."""
        self.Set_Edit_Mode(not self.Is_Editing)


    # Collect form data for saving

    def Collect_Form_Data(self, Base_Data=None):
        """Read all form widgets and merge with Base_Data; auto-set last_edited."""
        Data = dict(Base_Data or {})

        for Entry_Key, Widget in self.Field_Widgets.items():
            Entry     = Calibration_File_Variable_Information.get(Entry_Key, {})
            Calibration_Keys = Entry.get('Calibration_File_Variable_Name', '')
            if not Calibration_Keys:
                continue
            Primary_Key = Calibration_Keys[0] if isinstance(Calibration_Keys, list) else Calibration_Keys
            if not Primary_Key or Primary_Key == 'last_edited':
                continue

            if Entry_Key == 'Equation of State' and isinstance(Widget, QComboBox):
                Item_Data = Widget.currentData()
                if Item_Data:
                    Data['eos']   = Item_Data['eos']
                    Data['order'] = Item_Data['order']
                else:
                    Data.pop('eos',   None)
                    Data.pop('order', None)
                continue

            if Entry_Key == 'Composition' and isinstance(Widget, Composition_Container):
                Val = Widget.current_value()
                if Val:
                    Data[Primary_Key] = Val
                else:
                    Data.pop(Primary_Key, None)
                continue

            if Entry_Key == 'V0' and isinstance(Widget, V0_Field):
                Method = self.Method_Combo.currentText().strip() if self.Method_Combo is not None else str(self.Current_Method or '')
                if Method == 'XRD':
                    Active_Entry_Key = Widget.current_entry_key()
                else:
                    Active_Entry_Key = 'V0'
                self.Current_V0_Entry_Key = Active_Entry_Key
                Active_Calibration_Key = Get_Primary_V0_Calibration_Key(Active_Entry_Key, Method)

                for V0_Calibration_Key in Get_All_V0_Calibration_Keys():
                    Data.pop(V0_Calibration_Key, None)

                Text = Widget.text().strip()
                Value = Parse_Calibration_Value(Text)
                if Value is not None:
                    Data[Active_Calibration_Key] = Value
                continue

            if isinstance(Widget, QComboBox):
                # Method, Catagory, Is The Initial Bulk Modulus Fixed?
                Text  = Widget.currentText().strip()
                Value = Parse_Calibration_Value(Text)
                if Value is None:
                    Data.pop(Primary_Key, None)
                else:
                    Data[Primary_Key] = Value
                continue

            Text = self.Get_Widget_Text(Widget).strip()

            if Primary_Key == 'doi':
                Lines = [l.strip() for l in Text.splitlines() if l.strip()]
                Value = Lines if len(Lines) > 1 else (Lines[0] if Lines else None)
            else:
                Value = Parse_Calibration_Value(Text)

            if Value is None:
                Data.pop(Primary_Key, None)
            else:
                Data[Primary_Key] = Value

        # Merge reference panel data (cal_to_* fields)
        if self.References_Panel_Widget is not None:
            for Ref_Key, Ref_Val in self.References_Panel_Widget.get_data().items():
                if Ref_Val is None:
                    Data.pop(Ref_Key, None)
                else:
                    Data[Ref_Key] = Ref_Val

        Data['last_edited'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return Data


    # Save: user-edited existing calibration

    def Archive_If_Exists(self, Path, Old_Dir):
        """Move an existing file to Old_Dir with a versioned filename before overwriting."""
        Archive_Existing_File_With_Version(Path, Old_Dir)


    def Get_User_Edits_Path(self, File_Path):
        """Return (save_path, original_path) for a user-edited copy of File_Path."""
        User_Data_Dir   = User_Application_Data_Folder
        User_Edited_Dir = os.path.join(User_Data_Dir, 'User_Edited_Calibration_Files')
        Old_Dir         = os.path.join(User_Edited_Dir, 'Previous_Edits')
        os.makedirs(User_Edited_Dir, exist_ok=True)
        os.makedirs(Old_Dir,         exist_ok=True)

        Base       = os.path.splitext(os.path.basename(File_Path))[0]
        Base       = Base.replace(' - User Edited', '')
        Save_Fname = Base + ' - User Edited.yaml'
        Save_Path  = os.path.join(User_Edited_Dir, Save_Fname)

        self.Archive_If_Exists(Save_Path, Old_Dir)
        return Save_Path, File_Path


    def Save_Changes_To_Calibration_File(self):
        """Collect form values and write them to User_Edited_Calibration_Files.
        The original YAML file is never modified.
        """
        if not self.Calibration_File_Path:
            Warning_Message(self, "Missing File Path")
            return

        # Load the current file so fields not shown in the form are preserved
        try:
            with open(self.Calibration_File_Path, 'r', encoding='utf-8') as f:
                Base_Data = yaml.safe_load(f) or {}
        except Exception as e:
            Warning_Message(self, "Could Not Read The Calibration File", error=e)
            return

        Data = self.Collect_Form_Data(Base_Data)
        Save_Path, Original_Path = self.Get_User_Edits_Path(self.Calibration_File_Path)

        try:
            with open(Save_Path, 'w', encoding='utf-8') as f:
                yaml.dump(Data, f, default_flow_style=False, allow_unicode=True,
                          sort_keys=False, width=120)
        except Exception as e:
            Warning_Message(self, "Save Calibration Error", error=e)
            return

        Load_The_Calibrations_Into_Memory()
        self.Refresh_Selector()
        self.Calibration_Was_Saved = True

        self.User_Edited_Banner.setVisible(False)
        self.setWindowTitle(f'YAML Calibration: * {os.path.basename(Save_Path)}')

        self.Set_Edit_Mode(False)
        self.Calibration_File_Path = Save_Path

        Success_Message(self, "Saved Edited Calibration", save_path=Save_Path, original_path=Original_Path)

        Key = os.path.splitext(os.path.basename(Save_Path))[0]
        self.calibration_saved.emit(Key)


    def Refresh_Selector(self):
        """Rebuild the calibration selector dropdown from the current in-memory data."""
        if self.Composition_Selector is None or self.Study_Selector is None:
            return
        Current_File_Path = self.Calibration_File_Path
        Current_Composition_Key = self.Composition_Selector.currentData()

        self.Composition_Selector.blockSignals(True)
        self.Composition_Selector.clear()
        for Composition_Key in self.Get_Available_Composition_Keys():
            Display_Label = Material_Information.get(Composition_Key, {}).get('Display_Label', Composition_Key)
            self.Composition_Selector.addItem(Display_Label, Composition_Key)
        self.Composition_Selector.setCurrentIndex(-1)
        self.Composition_Selector.blockSignals(False)

        if Current_File_Path:
            self.Sync_Selector_To_File(Current_File_Path)
        elif Current_Composition_Key:
            Composition_Index = self.Composition_Selector.findData(Current_Composition_Key)
            if Composition_Index >= 0:
                self.Composition_Selector.blockSignals(True)
                self.Composition_Selector.setCurrentIndex(Composition_Index)
                self.Composition_Selector.blockSignals(False)
                self.Populate_Study_Selector(Current_Composition_Key)
        else:
            self.Study_Selector.blockSignals(True)
            self.Study_Selector.clear()
            self.Study_Selector.blockSignals(False)
            if hasattr(self, 'Calibration_Selector_Footnote'):
                self.Calibration_Selector_Footnote.setVisible(False)


    # Save: new user-entered calibration

    def Save_New_Calibration(self):
        """Collect form values and write a new calibration to User_Entered_Calibration_Files."""
        Study_Widget = self.Field_Widgets.get('Study')
        Study_Text   = self.Get_Widget_Text(Study_Widget).strip() if Study_Widget else ''
        if not Study_Text:
            Warning_Message(self, "Missing Calibration Study Name")
            return

        Data = self.Collect_Form_Data()

        User_Data_Dir    = User_Application_Data_Folder
        User_Entered_Dir = os.path.join(User_Data_Dir, 'User_Entered_Calibration_Files')
        os.makedirs(User_Entered_Dir, exist_ok=True)

        Safe_Name = Study_Text.replace('/', '-').replace('\\', '-')
        Save_Path = os.path.join(User_Entered_Dir, f'{Safe_Name} - User Entered.yaml')

        try:
            with open(Save_Path, 'w', encoding='utf-8') as f:
                yaml.dump(Data, f, default_flow_style=False, allow_unicode=True,
                          sort_keys=False, width=120)
        except Exception as e:
            Warning_Message(self, "Save Calibration Error", error=e)
            return

        Load_The_Calibrations_Into_Memory()
        Key = os.path.splitext(os.path.basename(Save_Path))[0]
        self.Calibration_Was_Saved = True
        self.calibration_saved.emit(Key)
        self.Calibration_File_Path = Save_Path
        self.Mode = 'view_edit'
        self.Set_Edit_Mode(False)
        self.Load_Form_From_File(Save_Path)
        Success_Message(self, "Saved New Calibration", save_path=Save_Path)




# Module-level helper functions

# Repopulate the parent widget's study list after a calibration save
def Repopulate_Parent(Parent):
    """Repopulate the parent widget's study list after a calibration save."""
    if hasattr(Parent, 'Populate_Checkboxes') and getattr(Parent, 'Composition', None):
        Parent.Refresh(
            Composition=Parent.Composition,
            Method=getattr(Parent, 'Method', None),
            Data=getattr(Parent, 'Data', None),
            Units=getattr(Parent, 'Units', None),
            Pressure_Calibration_Study=getattr(Parent, 'Pressure_Calibration_Study', None),
        )
    elif hasattr(Parent, 'Add_Relavent_Studies_To_The_Pressure_Calibration_Studies_Dropdown_Display'):
        Parent.Add_Relavent_Studies_To_The_Pressure_Calibration_Studies_Dropdown_Display()


def Reload_Preview_Dialog_With_File(Dialog, File_Path):
    """Refresh an already-open preview dialog to show a different calibration file."""
    if Dialog.Calibration_File_Path == File_Path:
        return
    # Reset edit state before loading so the rebuilt form starts read-only
    Dialog.Is_Editing = False
    Dialog.Sync_Selector_To_File(File_Path)
    Dialog.Load_Form_From_File(File_Path)
    if hasattr(Dialog, 'Enable_Edit_Button'):
        Dialog.Enable_Edit_Button.setText('Enable Editing')
    if hasattr(Dialog, 'Save_Changes_Button'):
        Dialog.Save_Changes_Button.setVisible(False)


def Bring_Preview_Dialog_To_Front(Dialog):
    """Restore, raise, and focus a preview dialog so it is immediately visible to the user.

    raise_()/activateWindow() alone do not un-minimize a window on Windows, so a
    dialog left minimized from an earlier preview would silently update its content
    without ever appearing in front of the user.
    """
    if Dialog.isMinimized():
        Dialog.showNormal()
    Dialog.raise_()
    Dialog.activateWindow()


def Resolve_Calibration_File_Path(Calibration_Key):
    """Look up a calibration's on-disk file path, self-healing once if it is stale.

    The in-memory Calibration_Metadata is only refreshed at startup or after an
    explicit save - if a calibration file was renamed, moved, or deleted elsewhere
    (e.g. by a downloaded-calibration sync) while this session was already running,
    the recorded path can go stale mid-session. Rather than surface that as a dead
    end, force one full reload and retry before giving up.
    """
    Meta = Calibration_Metadata.get(Calibration_Key)
    File_Path = Meta.get('file_path') if Meta else None
    if File_Path and os.path.exists(File_Path):
        return File_Path

    Load_The_Calibrations_Into_Memory()
    Meta = Calibration_Metadata.get(Calibration_Key)
    File_Path = Meta.get('file_path') if Meta else None
    if File_Path and os.path.exists(File_Path):
        return File_Path
    return None


def Preview_Calibration_File_For_Dropdown(self, Dropdown_Selection):
    """Open a preview/edit dialog for the YAML file linked to a dropdown's selection."""
    if Dropdown_Selection is None or Dropdown_Selection.currentData() is None:
        Warning_Message(self, "Missing Calibration Selection")
        return
    Selected_Label = Dropdown_Selection.currentData()
    File_Path = Resolve_Calibration_File_Path(Selected_Label)

    if not File_Path:
        Warning_Message(self, "Could Not Find The Calibration File")
        return

    # Reuse an existing open dialog rather than stacking multiple windows.
    existing = getattr(self, 'Calibration_Preview_Dialog', None)
    if existing is not None and existing.isVisible():
        Reload_Preview_Dialog_With_File(existing, File_Path)
        Bring_Preview_Dialog_To_Front(existing)
        return

    with Guard_Unwanted_Window_Shows() as Guard:
        Dlg = View_Edit_And_Save_Calibration_Files_In_A_New_Window(Parent=None, Calibration_File_Path=File_Path)
        if Guard is not None:
            Guard.allow(Dlg)
        Dlg.calibration_saved.connect(lambda _key: Repopulate_Parent(self))
        self.Calibration_Preview_Dialog = Dlg  # strong reference — keeps dialog alive
        Dlg.show()
        Dlg.raise_()
        Dlg.activateWindow()


def Preview_Calibration_File_For_File_Path(self, File_Path):
    """Open a preview/edit dialog for a specific YAML file path."""
    if not File_Path:
        Warning_Message(self, "Could Not Find The Calibration File")
        return

    if not os.path.exists(File_Path):
        # Recorded path is stale (renamed/moved/deleted mid-session) - re-derive the
        # calibration key from the filename and try to re-resolve it after a reload
        Calibration_Key = os.path.splitext(os.path.basename(File_Path))[0].replace(' - User Edited', '')
        File_Path = Resolve_Calibration_File_Path(Calibration_Key)

    if not File_Path or not os.path.exists(File_Path):
        Warning_Message(self, "Could Not Find The Calibration File")
        return

    # Reuse an existing open dialog rather than stacking multiple windows.
    existing = getattr(self, 'Calibration_Preview_Dialog', None)
    if existing is not None and existing.isVisible():
        Reload_Preview_Dialog_With_File(existing, File_Path)
        Bring_Preview_Dialog_To_Front(existing)
        return

    with Guard_Unwanted_Window_Shows() as Guard:
        Dlg = View_Edit_And_Save_Calibration_Files_In_A_New_Window(Parent=None, Calibration_File_Path=File_Path)
        if Guard is not None:
            Guard.allow(Dlg)
        Dlg.calibration_saved.connect(lambda _key: Repopulate_Parent(self))
        self.Calibration_Preview_Dialog = Dlg  # strong reference — keeps dialog alive
        Dlg.show()
        Dlg.raise_()
        Dlg.activateWindow()




# New-entry convenience subclass

class Enter_Calibration_Window(View_Edit_And_Save_Calibration_Files_In_A_New_Window):
    """Opens the calibration dialog in new-entry mode (blank form, edit mode on by default)."""

    def __init__(self, Parent=None):
        super().__init__(Parent=Parent, mode='new')


class View_Calibration_Window(View_Edit_And_Save_Calibration_Files_In_A_New_Window):
    """Opens the calibration dialog in view mode with no initial selection."""

    def __init__(self, Parent=None):
        super().__init__(Parent=Parent, mode='view_edit', start_with_no_selection=True)
