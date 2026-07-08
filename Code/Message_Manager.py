# Load libraries
    # Load third-party libraries
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QMessageBox
from PySide6.QtGui import QIcon
    # Load local libraries
from Loading_Message import Get_Resource_Path
from Warning_Messages import Get_Warning
from Success_Messages import Get_Success_Message


# Build the message contents
def Get_Message(Message_Key, Message_Type="warning", **Format_Values):
    if Message_Type == "warning":
        return Get_Warning(Message_Key, **Format_Values)
    if Message_Type == "success":
        return Get_Success_Message(Message_Key, **Format_Values)
    raise ValueError(f"Unknown message type: {Message_Type}")


def Get_Message_Icon(Message_Type, Icon=None):
    if Icon is not None:
        return Icon
    if Message_Type == "success":
        return QMessageBox.Information
    return QMessageBox.Warning


# Build and show a general message box
    # When Checkbox_Text is given (e.g. "Do not show this message again") a checkbox is
    # added to the box and the return value becomes (Result, Checkbox_Is_Checked) instead
    # of a plain Result, so only callers that ask for a checkbox see the different shape
def Message(Parent, Message_Key, Message_Type="warning", Buttons=None, Default_Button=None, Icon=None, Checkbox_Text=None, **Format_Values):
    # Keep the actual message window implementation in one place so it can be
    # replaced later with a custom-designed dialog without changing call sites.
    Rendered_Message = Get_Message(Message_Key, Message_Type=Message_Type, **Format_Values)
    Message_Box = QMessageBox(Parent)
    if Message_Type == "warning":
        Message_Box.setObjectName("WarningMessageBox")
    elif Message_Type == "success":
        Message_Box.setObjectName("SuccessMessageBox")
    Message_Box.setWindowTitle(Rendered_Message["Title"])
    Message_Box.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
    Message_Box.setText(Rendered_Message["Message"])
    Message_Box.setIcon(Get_Message_Icon(Message_Type, Icon=Icon))
    Message_Box.setStandardButtons(Buttons if Buttons is not None else QMessageBox.Ok)
    if Default_Button is not None:
        Message_Box.setDefaultButton(Default_Button)

    # Make any hyperlink inside the message text (e.g. a GitHub release link) open in the
    # user's default browser instead of doing nothing when clicked
        # Qt auto-detects the "<a href=...>" markup as rich text, so no format change is needed here
    Message_Label = Message_Box.findChild(QLabel, "qt_msgbox_label")
    if Message_Label is not None:
        Message_Label.setOpenExternalLinks(True)

    # Add an optional "do not show again"-style checkbox to the message box
    Checkbox = None
    if Checkbox_Text:
        Checkbox = QCheckBox(Checkbox_Text)
        Message_Box.setCheckBox(Checkbox)

    Message_Box.adjustSize()
    screen = QApplication.primaryScreen()
    if screen is not None:
        sg = screen.availableGeometry()
        w = max(Message_Box.width(), Message_Box.minimumWidth())
        h = max(Message_Box.height(), Message_Box.minimumHeight())
        cx = (sg.width() - w) // 2 + sg.x()
        cy = (sg.height() - h) // 2 + sg.y()
        Message_Box.move(-32000, -32000)
        Message_Box.setWindowOpacity(0.0)
        QTimer.singleShot(0, lambda: Reveal_Message_Box(Message_Box, cx, cy))
    Result = Message_Box.exec()

    # Only change the return shape for callers that actually asked for a checkbox
    if Checkbox is not None:
        return Result, Checkbox.isChecked()
    return Result


def Reveal_Message_Box(Message_Box, Center_X, Center_Y):
    if Message_Box is None:
        return
    Message_Box.move(Center_X, Center_Y)
    Message_Box.setWindowOpacity(1.0)


# Show a warning message
def Warning_Message(Parent, Warning_Key, Buttons=None, Default_Button=None, Icon=None, Checkbox_Text=None, **Format_Values):
    return Message(
        Parent,
        Warning_Key,
        Message_Type="warning",
        Buttons=Buttons,
        Default_Button=Default_Button,
        Icon=Icon,
        Checkbox_Text=Checkbox_Text,
        **Format_Values,
    )


# Show a success message
def Success_Message(Parent, Success_Key, Buttons=None, Default_Button=None, Icon=None, **Format_Values):
    return Message(
        Parent,
        Success_Key,
        Message_Type="success",
        Buttons=Buttons,
        Default_Button=Default_Button,
        Icon=Icon,
        **Format_Values,
    )


def Show_Warning(Parent, Warning_Key, **Format_Values):
    return Warning_Message(Parent, Warning_Key, **Format_Values)


def Show_Success(Parent, Success_Key, **Format_Values):
    return Success_Message(Parent, Success_Key, **Format_Values)


__all__ = [
    "Get_Message",
    "Message",
    "Warning_Message",
    "Success_Message",
    "Show_Warning",
    "Show_Success",
]
