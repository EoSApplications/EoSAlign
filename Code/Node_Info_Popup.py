from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


def Apply_Popup_Stylesheet(popup, get_resource_path, colors):
    from Themes.Theme import Load_EoSHolo_Node_Popup_Style_Sheet
    Qss = Load_EoSHolo_Node_Popup_Style_Sheet(get_resource_path)
    popup.setStyleSheet(Qss)


def Build_Node_Info_Popup(
    parent,
    entry,
    get_resource_path,
    colors,
    on_preview_calibration=None,
    on_chain_to_node=None,
    on_chains_through_node=None,
):
    Popup = QFrame(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    Popup.setObjectName("NodeInfoPopupHost")
    Popup.setAttribute(Qt.WA_DeleteOnClose)
    Popup.setAttribute(Qt.WA_ShowWithoutActivating)
    Popup.setAttribute(Qt.WA_TranslucentBackground, True)

    Panel = QFrame(Popup)
    Panel.setObjectName("NodeInfoPopup")
    Panel.setAttribute(Qt.WA_StyledBackground, True)
    Panel.setFrameShape(QFrame.NoFrame)

    Shadow = QGraphicsDropShadowEffect(Panel)
    Shadow.setBlurRadius(22)
    Shadow.setOffset(0, 3)
    Shadow.setColor(QColor(0, 0, 0, 110))
    Panel.setGraphicsEffect(Shadow)

    Host_Layout = QVBoxLayout(Popup)
    Host_Layout.setContentsMargins(12, 12, 12, 12)
    Host_Layout.setSpacing(0)
    Host_Layout.addWidget(Panel)

    Outer_Layout = QVBoxLayout(Panel)
    Outer_Layout.setContentsMargins(10, 10, 10, 10)
    Outer_Layout.setSpacing(6)

    # Title row
    Title_Row = QHBoxLayout()
    Title_Row.setContentsMargins(0, 0, 0, 0)
    Title_Row.setSpacing(8)

    Study_Name = entry.get("study", "")
    Metadata = entry.get("metadata", {})
    Is_User = Metadata.get("is_user_edited", False) or Metadata.get("is_user_entered", False)
    if Is_User:
        Study_Name = "* " + Study_Name
    if entry.get("is_special"):
        Special_Type = entry.get("special_type")
        if Special_Type == "primary":
            Popup_Title = f"{Study_Name} (Primary)"
        elif Special_Type == "not_specified":
            Popup_Title = f"{Study_Name} (Not Specified)"
        else:
            Popup_Title = Study_Name
    else:
        Popup_Title = Study_Name

    Title_Label = QLabel(Popup_Title)
    Title_Label.setObjectName("NodeInfoTitle")
    Title_Row.addWidget(Title_Label, 0, Qt.AlignLeft | Qt.AlignVCenter)

    Preview_Button = QPushButton("Preview Calibrant")
    Preview_Button.setObjectName("Preview_Calibration_Button")
    Preview_Button.setFixedHeight(32)
    if on_preview_calibration is not None:
        Preview_Button.clicked.connect(on_preview_calibration)
    else:
        Preview_Button.setEnabled(False)
        Preview_Button.setToolTip("No YAML file is available for this node.")
    Title_Row.addWidget(Preview_Button, 0, Qt.AlignLeft | Qt.AlignVCenter)

    Title_Row.addStretch(1)

    Close_Button = QPushButton("x")
    Close_Button.setObjectName("NodeInfoCloseButton")
    Close_Button.setFixedSize(28, 28)
    Close_Button.setAttribute(Qt.WA_StyledBackground, True)
    Close_Button.clicked.connect(Popup.close)
    Title_Row.addWidget(Close_Button, 0, Qt.AlignRight | Qt.AlignVCenter)
    Outer_Layout.addLayout(Title_Row)

    # Divider
    Divider = QLabel()
    Divider.setObjectName("NodeInfoDivider")
    Divider.setFixedHeight(1)
    Outer_Layout.addWidget(Divider)

    # Scrollable content area
    Scroll = QScrollArea()
    Scroll.setObjectName("NodeInfoScroll")
    Scroll.setWidgetResizable(True)
    Scroll.setFrameShape(QFrame.NoFrame)
    Scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    Scroll.viewport().setObjectName("NodeInfoViewport")

    Content = QWidget()
    Content.setObjectName("NodeInfoContent")
    Grid = QGridLayout(Content)
    Grid.setContentsMargins(8, 8, 8, 8)
    Grid.setHorizontalSpacing(12)
    Grid.setVerticalSpacing(4)

    def Add_Row(row, key, value):
        Key_Label = QLabel(key)
        Key_Label.setObjectName("NodeInfoKey")
        Value_Label = QLabel(str(value))
        Value_Label.setObjectName("NodeInfoValue")
        Value_Label.setWordWrap(True)
        Grid.addWidget(Key_Label, row, 0, Qt.AlignTop)
        Grid.addWidget(Value_Label, row, 1, Qt.AlignTop)

    Add_Row(0, "EoS:", entry.get("eos", ""))
    Add_Row(1, "Order:", entry.get("order", ""))
    Add_Row(2, "Composition:", entry.get("composition", ""))
    Add_Row(3, "Max Pressure:", entry.get("max_pressure", ""))

    Grid.setColumnStretch(1, 1)
    Scroll.setWidget(Content)
    Outer_Layout.addWidget(Scroll)

    # Action buttons
    Actions_Row = QHBoxLayout()
    Actions_Row.setContentsMargins(0, 4, 0, 0)
    Actions_Row.setSpacing(8)

    Left_Button = QPushButton("Calibrant Origin Chain")
    Left_Button.setObjectName("Secondary_Button")
    Left_Button.setFixedHeight(32)
    if on_chain_to_node is not None:
        Left_Button.clicked.connect(on_chain_to_node)
    Left_Button.clicked.connect(Popup.close)
    Actions_Row.addWidget(Left_Button)

    Right_Button = QPushButton("Complete Calibrant Chain")
    Right_Button.setObjectName("Secondary_Button")
    Right_Button.setFixedHeight(32)
    if on_chains_through_node is not None:
        Right_Button.clicked.connect(on_chains_through_node)
    Right_Button.clicked.connect(Popup.close)
    Actions_Row.addWidget(Right_Button)

    Outer_Layout.addLayout(Actions_Row)

    Apply_Popup_Stylesheet(Popup, get_resource_path, colors)

    Popup.adjustSize()
    Maximum_Height = 400
    if Popup.height() > Maximum_Height:
        Popup.resize(Popup.width(), Maximum_Height)

    return Popup
