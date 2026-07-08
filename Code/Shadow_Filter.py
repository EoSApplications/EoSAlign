import darkdetect
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


# Shadow parameters per objectName: (blur_radius, y_offset, opacity 0-255)
Shadow_Map = {
    "Primary_Button": (10, 3, 50),
    "Secondary_Button": (10, 3, 50),
    "TertiaryButton": (10, 3, 50),
    "Preview_Calibration_Button": (10, 3, 50),
    "TextEdit": (10, 3, 35),
    "LineEdit": (10, 3, 35),
    "Dropdown": (10, 3, 35),
}


class Shadow_Filter(QObject):

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Polish and obj.objectName() in Shadow_Map:
            # Skip dropdown shadow in dark mode — it clashes with the OS popup shadow
            if obj.objectName() == "Dropdown" and darkdetect.isDark():
                return False
            if obj.graphicsEffect() is None:
                blur, offset, opacity = Shadow_Map[obj.objectName()]
                shadow = QGraphicsDropShadowEffect(obj)
                shadow.setBlurRadius(blur)
                shadow.setXOffset(0)
                shadow.setYOffset(offset)
                shadow.setColor(QColor(0, 0, 0, opacity))
                obj.setGraphicsEffect(shadow)
        return False


Installed_Shadow_Filter = None


def Install_Shadow_Filter(App):
    global Installed_Shadow_Filter
    Installed_Shadow_Filter = Shadow_Filter(App)
    App.installEventFilter(Installed_Shadow_Filter)
