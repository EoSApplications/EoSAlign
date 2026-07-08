from contextlib import contextmanager

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QSplashScreen, QWidget


class Temporary_Window_Show_Guard(QObject):

    def __init__(self):
        super().__init__()
        self.Allowed_Window_Ids = set()

    def allow(self, widget):
        if widget is not None:
            self.Allowed_Window_Ids.add(id(widget))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
            if id(obj) in self.Allowed_Window_Ids or isinstance(obj, QSplashScreen):
                return False
            obj.move(-32000, -32000)
        return False


@contextmanager
def Guard_Unwanted_Window_Shows(*allowed_widgets):
    app = QApplication.instance()
    if app is None:
        yield None
        return

    guard = Temporary_Window_Show_Guard()
    for widget in allowed_widgets:
        guard.allow(widget)
    app.installEventFilter(guard)
    try:
        yield guard
    finally:
        app.removeEventFilter(guard)


@contextmanager
def Suspend_Widget_Updates(*widgets):
    active_widgets = []
    seen = set()
    for widget in widgets:
        if widget is None:
            continue
        wid = id(widget)
        if wid in seen:
            continue
        seen.add(wid)
        active_widgets.append(widget)

    previous_states = []
    for widget in active_widgets:
        previous_states.append(widget.updatesEnabled())
        widget.setUpdatesEnabled(False)

    try:
        yield
    finally:
        for widget, was_enabled in zip(active_widgets, previous_states):
            widget.setUpdatesEnabled(was_enabled)
            widget.update()
