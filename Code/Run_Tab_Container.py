# Load third party libraries
from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QImageReader
# Load local functions from local files
from EoSAlign__Step_By_Step_Layout import Step_By_Step_Layout_Content
from Window_Show_Guard import Guard_Unwanted_Window_Shows


# ── tab bar shadow constants (tune here) ────────────────────────────────────
Button_Corner_Radius = 15   # must match border-top-left-radius / border-top-right-radius in QSS
Shadow_Blur_Radius = 14   # Gaussian blur radius in px — controls shadow spread
Shadow_Fill_Alpha = 180  # fill alpha of shape before blur (0-255) — controls darkness


class Run_Tab_Background(QWidget):
    Maximum_Tile_Width = 8000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RunTabBackground")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        from Loading_Message import Get_Resource_Path
        reader = QImageReader(Get_Resource_Path("Graphics/Stars.png"))
        reader.setAutoTransform(True)
        self.Stars_Source = QPixmap.fromImage(reader.read())

        self.Stars_Label = QLabel(self)
        self.Stars_Label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.Stars_Label.lower()
        self.Stars_Label.hide()

        self.Show_Stars = False
        self.Tiled_Height = 0
        self.Background_Color = QColor(0, 0, 0)

    def Set_Dark_Mode(self, is_dark, bg_color="#000000"):
        self.Background_Color = QColor(bg_color)
        self.Show_Stars = is_dark and not self.Stars_Source.isNull()
        if self.Show_Stars:
            self.Tile_Stars()
            self.Stars_Label.show()
        else:
            self.Stars_Label.hide()

    def Tile_Stars(self):
        h = self.height()
        if h <= 0 or self.Stars_Source.isNull():
            return
        dpr = QApplication.primaryScreen().devicePixelRatio()
        scaled = self.Stars_Source.scaledToHeight(int(h * dpr), Qt.SmoothTransformation)
        tiled = QPixmap(self.Maximum_Tile_Width, int(h * dpr))
        tiled.fill(self.Background_Color)
        p = QPainter(tiled)
        x = 0
        while x < self.Maximum_Tile_Width:
            p.drawPixmap(x, 0, scaled)
            x += scaled.width()
        p.end()
        tiled.setDevicePixelRatio(dpr)
        self.Stars_Label.setPixmap(tiled)
        self.Stars_Label.setGeometry(0, 0, self.Maximum_Tile_Width, h)
        self.Tiled_Height = h

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.Show_Stars and self.height() != self.Tiled_Height:
            self.Tile_Stars()


class Tab_Bar_Shadow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.Buttons = []
        self.Active_Index = 0
        self.Separator_Y_Position = 0
        self.Cached_Pixmap = None   # (w, h, QPixmap)

    def Update_State(self, btns, active_idx, sep_y):
        self.Buttons = btns
        self.Active_Index = active_idx
        self.Separator_Y_Position = sep_y
        self.Cached_Pixmap = None
        self.update()

    def Build_Shadow(self, w, h):
        r = float(Button_Corner_Radius)
        sep_y = self.Separator_Y_Position
        shape = QPainterPath()
        sep_path = QPainterPath()
        sep_path.addRect(QRectF(0, sep_y, w, h - sep_y))
        shape = shape.united(sep_path)
        for btn in self.Buttons:
            pos = self.mapFromGlobal(btn.mapToGlobal(QPoint(0, 0)))
            bx  = float(pos.x())
            by  = float(pos.y())
            bw  = float(btn.width())
            bp  = QPainterPath()
            bp.moveTo(bx, by + r)
            bp.arcTo(QRectF(bx, by, 2*r, 2*r), 180, -90)
            bp.lineTo(bx + bw - r, by)
            bp.arcTo(QRectF(bx + bw - 2*r, by, 2*r, 2*r), 90, -90)
            bp.lineTo(bx + bw, sep_y)
            bp.lineTo(bx, sep_y)
            bp.closeSubpath()
            shape = shape.united(bp)
        shape_px = QPixmap(w, h)
        shape_px.fill(QColor(0, 0, 0, 0))
        sp = QPainter(shape_px)
        sp.setRenderHint(QPainter.Antialiasing)
        sp.fillPath(shape, QColor(0, 0, 0, Shadow_Fill_Alpha))
        sp.end()
        scene = QGraphicsScene()
        item  = QGraphicsPixmapItem(shape_px)
        blur  = QGraphicsBlurEffect()
        blur.setBlurRadius(Shadow_Blur_Radius)
        item.setGraphicsEffect(blur)
        scene.addItem(item)
        result = QPixmap(w, h)
        result.fill(QColor(0, 0, 0, 0))
        rp = QPainter(result)
        scene.render(rp, QRectF(0, 0, w, h), QRectF(0, 0, w, h))
        rp.end()
        return result

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        if self.Cached_Pixmap is None or self.Cached_Pixmap[0] != w or self.Cached_Pixmap[1] != h:
            self.Cached_Pixmap = (w, h, self.Build_Shadow(w, h))
        p = QPainter(self)
        p.drawPixmap(0, 0, self.Cached_Pixmap[2])
        p.end()


class Active_Tab_Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.Active_Button = None
        self.Inactive_Path = QPainterPath()
        self.Cached_Pixmap = None   # (w, h, QPixmap)

    def Update_State(self, active_btn, inactive_path):
        self.Active_Button = active_btn
        self.Inactive_Path = inactive_path
        self.Cached_Pixmap = None
        self.update()

    def Build_Overlay(self, w, h):
        if self.Active_Button is None or self.Inactive_Path.isEmpty():
            return None
        r = float(Button_Corner_Radius)
        pos = self.mapFromGlobal(self.Active_Button.mapToGlobal(QPoint(0, 0)))
        bx  = float(pos.x())
        by  = float(pos.y())
        bw  = float(self.Active_Button.width())
        bh  = float(self.Active_Button.height())
        active_path = QPainterPath()
        active_path.moveTo(bx, by + r)
        active_path.arcTo(QRectF(bx, by, 2*r, 2*r), 180, -90)
        active_path.lineTo(bx + bw - r, by)
        active_path.arcTo(QRectF(bx + bw - 2*r, by, 2*r, 2*r), 90, -90)
        active_path.lineTo(bx + bw, by + bh)
        active_path.lineTo(bx, by + bh)
        active_path.closeSubpath()
        shape_px = QPixmap(w, h)
        shape_px.fill(QColor(0, 0, 0, 0))
        sp = QPainter(shape_px)
        sp.setRenderHint(QPainter.Antialiasing)
        sp.fillPath(active_path, QColor(0, 0, 0, Shadow_Fill_Alpha))
        sp.end()
        scene = QGraphicsScene()
        item  = QGraphicsPixmapItem(shape_px)
        blur  = QGraphicsBlurEffect()
        blur.setBlurRadius(Shadow_Blur_Radius)
        item.setGraphicsEffect(blur)
        scene.addItem(item)
        blurred = QPixmap(w, h)
        blurred.fill(QColor(0, 0, 0, 0))
        rp = QPainter(blurred)
        scene.render(rp, QRectF(0, 0, w, h), QRectF(0, 0, w, h))
        rp.end()
        result = QPixmap(w, h)
        result.fill(QColor(0, 0, 0, 0))
        cp = QPainter(result)
        cp.setRenderHint(QPainter.Antialiasing)
        cp.setClipPath(self.Inactive_Path)
        cp.drawPixmap(0, 0, blurred)
        cp.end()
        return result

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        if self.Cached_Pixmap is None or self.Cached_Pixmap[0] != w or self.Cached_Pixmap[1] != h:
            self.Cached_Pixmap = (w, h, self.Build_Overlay(w, h))
        if self.Cached_Pixmap[2] is None:
            return
        p = QPainter(self)
        p.drawPixmap(0, 0, self.Cached_Pixmap[2])
        p.end()


# Step by step layout — custom folder-tab container
#
# Three physical layers achieve the classic "folder tab" look without
# relying on QSS border-color tricks:
#   Tab_Row  — row of QPushButton tabs above the separator
#   Separator  — a Separator_Height-px tall colored widget (the visible separator line)
#   Connector — a floating Separator_Height-px widget that covers Separator under the
#                selected tab, making the line appear to vanish there
#   Run_Stack — QStackedWidget holding one Step_By_Step_Layout_Content per tab
class Step_By_Step_Layout(QWidget):

    Separator_Height = 2   # separator height (px)
    Initial_Tab_Indent = 10  # left indent for the first tab button
    Top_Button_Gap = 8   # vertical gap between banner and tab buttons

    def __init__(self):
        super().__init__()

        self.Runs = []
        self.Tab_Buttons = []
        self.Inactive_Connectors = []

        # Tab button row
        self.Tab_Row = QWidget()
        self.Tab_Row.setObjectName("RunTabRow")
        self.Tab_Row.setAttribute(Qt.WA_StyledBackground, True)
        self.Tab_Row.setAutoFillBackground(False)
        self.Tab_Row_Layout = QHBoxLayout(self.Tab_Row)
        self.Tab_Row_Layout.setContentsMargins(self.Initial_Tab_Indent, self.Top_Button_Gap, 0, 0)
        self.Tab_Row_Layout.setSpacing(3)
        self.Tab_Row_Layout.addStretch()

        # Separator line
        self.Separator = QWidget()
        self.Separator.setObjectName("RunSeparator")
        self.Separator.setAttribute(Qt.WA_StyledBackground, True)
        self.Separator.setFixedHeight(self.Separator_Height)

        # Content stack
        self.Run_Stack = QStackedWidget()

        # Floating connector — absolutely positioned child, covers Separator under
        # the selected tab so the separator appears to disappear there
        self.Connector = QWidget(self)
        self.Connector.setObjectName("RunTabConnector")
        self.Connector.setAttribute(Qt.WA_StyledBackground, True)
        self.Connector.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.Connector.setFixedHeight(self.Separator_Height)
        self.Connector.hide()

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, Shadow_Blur_Radius, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.Tab_Row)
        Layout.addWidget(self.Separator)
        Layout.addWidget(self.Run_Stack)

        # Tab-bar background — behind the shadow so the blur renders over it.
        # Sized to the tab-row area only (y=0 … sep_y); separator and content
        # are not covered so their own backgrounds remain correct.
        self.Tab_Bar_Background = Run_Tab_Background(self)
        self.Tab_Bar_Background.lower()  # keep permanently below the shadow
        from Themes.Theme import Get_Theme
        Theme_Name, _, Theme_Colors = Get_Theme()
        self.Tab_Bar_Background.Set_Dark_Mode(
            Theme_Name == "Dark",
            Theme_Colors.get("Run_Tab_Row_Background", "#000000"),
        )

        self.Shadow = Tab_Bar_Shadow(self)
        self.Overlay = Active_Tab_Overlay(self)

        First_Run = Step_By_Step_Layout_Content(Run_Label="Run 1")
        First_Run.Add_New_Run.connect(self.Add_Recalculate_Tab)
        First_Run.Request_Reset_All.connect(self.Reset_All_Runs)
        self.Attach_Run(First_Run, "Run 1")


    def Attach_Run(self, run, label):

        idx = len(self.Runs)
        self.Runs.append(run)

        btn = QPushButton(label)
        btn.setObjectName("RunTabButton")
        btn.setCheckable(True)
        btn.setAutoFillBackground(False)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _, i=idx: self.Select_Tab(i))
        self.Tab_Buttons.append(btn)

        # Inactive connector — covers the separator under this button (styled to match inactive tab)
        inactive_conn = QWidget(self)
        inactive_conn.setObjectName("RunTabInactiveConnector")
        inactive_conn.setAttribute(Qt.WA_StyledBackground, True)
        inactive_conn.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        inactive_conn.setFixedHeight(self.Separator_Height)
        inactive_conn.hide()
        self.Inactive_Connectors.append(inactive_conn)

        # Insert before the trailing stretch
        self.Tab_Row_Layout.insertWidget(self.Tab_Row_Layout.count() - 1, btn)
        self.Run_Stack.addWidget(run)
        self.Select_Tab(idx)


    def Select_Tab(self, idx):

        for i, btn in enumerate(self.Tab_Buttons):
            btn.setChecked(i == idx)
        self.Run_Stack.setCurrentIndex(idx)
        QTimer.singleShot(0, self.Update_Connector)


    # Return the active run widget
    def Get_Current_Run(self):

        Current_Index = self.Run_Stack.currentIndex()
        if Current_Index < 0 or Current_Index >= len(self.Runs):
            return None
        return self.Runs[Current_Index]


    # Route File > Open to the active run
    def Handle_Menu_Open_Action(self):

        Current_Run = self.Get_Current_Run()
        if Current_Run is not None and hasattr(Current_Run, "Handle_Menu_Open_Action"):
            Current_Run.Handle_Menu_Open_Action()


    # Route File > Save Data to the active run
    def Handle_Menu_Save_Action(self):

        Current_Run = self.Get_Current_Run()
        if Current_Run is not None and hasattr(Current_Run, "Handle_Menu_Save_Action"):
            Current_Run.Handle_Menu_Save_Action()


    def Update_Connector(self):

        if not self.Tab_Buttons:
            self.Connector.hide()
            for conn in self.Inactive_Connectors:
                conn.hide()
            return
        sep_pos = self.Separator.mapTo(self, QPoint(0, 0))
        active_idx = self.Run_Stack.currentIndex()
        if active_idx < 0:
            active_idx = 0
        r = float(Button_Corner_Radius)

        Inactive_Path = QPainterPath()
        for i, btn in enumerate(self.Tab_Buttons):
            if i == active_idx:
                continue
            pos = self.Overlay.mapFromGlobal(btn.mapToGlobal(QPoint(0, 0)))
            bx, by = float(pos.x()), float(pos.y())
            bw, bh = float(btn.width()), float(btn.height())
            bottom = by + bh + self.Separator_Height  # extend to include inactive connector below button
            bp = QPainterPath()
            bp.moveTo(bx, by + r)
            bp.arcTo(QRectF(bx, by, 2*r, 2*r), 180, -90)
            bp.lineTo(bx + bw - r, by)
            bp.arcTo(QRectF(bx + bw - 2*r, by, 2*r, 2*r), 90, -90)
            bp.lineTo(bx + bw, bottom)
            bp.lineTo(bx, bottom)
            bp.closeSubpath()
            Inactive_Path = Inactive_Path.united(bp)

        Tab_Bar_Height = sep_pos.y() + self.Separator_Height
        self.Tab_Bar_Background.setGeometry(0, 0, self.width(), sep_pos.y())
        self.Shadow.setGeometry(0, 0, self.width(), Tab_Bar_Height)
        self.Shadow.Update_State(self.Tab_Buttons, active_idx, sep_pos.y())

        Active_Button = self.Tab_Buttons[active_idx]
        self.Overlay.setGeometry(0, 0, self.width(), Tab_Bar_Height)
        self.Overlay.Update_State(Active_Button, Inactive_Path)

        # Z-order: shadow → Tab_Row (buttons) → overlay → stack → inactive connectors → active connector
        self.Shadow.raise_()
        self.Tab_Row.raise_()
        self.Overlay.raise_()
        self.Run_Stack.raise_()

        for i, (btn, conn) in enumerate(zip(self.Tab_Buttons, self.Inactive_Connectors)):
            if i == active_idx:
                conn.hide()
            else:
                btn_x = btn.mapTo(self, QPoint(0, 0)).x()
                conn.setGeometry(btn_x, sep_pos.y(), btn.width(), self.Separator_Height)
                conn.raise_()
                conn.show()

        btn_x = Active_Button.mapTo(self, QPoint(0, 0)).x()
        self.Connector.setGeometry(btn_x, sep_pos.y(), Active_Button.width(), self.Separator_Height)
        self.Connector.raise_()
        self.Connector.show()


    def resizeEvent(self, event):

        super().resizeEvent(event)
        QTimer.singleShot(0, self.Update_Connector)


    # Add a new run tab pre-filled with the selections from the previous run
    def Add_Recalculate_Tab(self, Disabled_Collapsible_Section_Selections):

        Run_Number = len(self.Runs) + 1
        with Guard_Unwanted_Window_Shows():
            New_Run = Step_By_Step_Layout_Content(
                Disabled_Collapsible_Section_Selections=Disabled_Collapsible_Section_Selections,
                Run_Label=f"Run {Run_Number}",
            )
        New_Run.Add_New_Run.connect(self.Add_Recalculate_Tab)
        New_Run.Request_Reset_All.connect(self.Reset_All_Runs)
        New_Run.Disable_The_Middle_Collapsible_Sections(True)
        self.Attach_Run(New_Run, f"Run {Run_Number}")


    # Remove all tabs and start over with a single fresh run
    def Reset_All_Runs(self):

        # Build the new Run 1 first so the stack is never left empty.
        with Guard_Unwanted_Window_Shows():
            First_Run = Step_By_Step_Layout_Content(Run_Label="Run 1")
        First_Run.Add_New_Run.connect(self.Add_Recalculate_Tab)
        First_Run.Request_Reset_All.connect(self.Reset_All_Runs)

        # Stash old references before clearing the lists.
        Old_Buttons = list(self.Tab_Buttons)
        Old_Connectors = list(self.Inactive_Connectors)
        Old_Runs = list(self.Runs)

        # Reset internal state and attach the fresh run (switches display).
        self.Tab_Buttons = []
        self.Inactive_Connectors = []
        self.Runs = []
        self.Attach_Run(First_Run, "Run 1")

        # Now safely discard the old tabs — they are already hidden.
        self.Connector.hide()
        for btn in Old_Buttons:
            self.Tab_Row_Layout.removeWidget(btn)
            btn.deleteLater()
        for conn in Old_Connectors:
            conn.deleteLater()
        for run in Old_Runs:
            self.Run_Stack.removeWidget(run)
            run.deleteLater()
