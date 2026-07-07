# Load libraries
    # Load standard libraries
import sys
import os
import time
import math
from Installed_Applications_Registry import Register_Installed_Application_And_Exit_If_Requested



# Get the absolute path to a resource file (works in both dev and frozen/PyInstaller environments)
def Get_Resource_Path(Relative_Path):
    if getattr(sys, 'frozen', False):
        # Onefile bootloader extracts embedded data to sys._MEIPASS on every
        # platform, including inside a macOS .app bundle (see Loading_Message.py).
        Base_Path = sys._MEIPASS
    else:
        Base_Path = os.path.abspath(".")
    return os.path.join(Base_Path, Relative_Path)


def Stable_Unit_Float(text):
    """
    Fast deterministic hash mapped to [0, 1], stable across runs/platforms.
    """
    h = 2166136261  # FNV-1a 32-bit offset basis
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h / 4294967295.0




# Placeholder class — the real EoSHolo is built inside Build_EoSHolo_Window() after the splash appears
class EoSHolo:
    pass




# Build the EoSHolo window class (called after the splash screen is shown so heavy imports are deferred)
def Build_EoSHolo_Window():

    # Load libraries
        # Load third party libraries
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
        QLabel, QSizePolicy, QCheckBox, QGraphicsView, QGraphicsScene,
        QGraphicsObject, QGraphicsItem, QFrame, QGraphicsDropShadowEffect
    )
    from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, QEvent
    from PySide6.QtGui import (
        QIcon, QColor, QPen, QBrush, QPainter, QPainterPath, QPainterPathStroker,
        QFont, QFontMetrics, QPolygonF, QCursor, QPalette
    )
        # Load local functions from local files
    from Settings import Settings
    from Themes.Theme import Get_Theme
    from MenuBar import MainMenuBar
    from Banner import Banner
    from Collapsible_Sections import WordWrapDelegate, CheckboxRow, Dropdown, IS_USER_CALIBRANT_ROLE
    from Reference_Values_And_Units import Material_Information
    import EoS_Math.Build_Dataframe  # must precede EoS_Math import of Calibration_Metadata
    from EoS_Math.Build_Dataframe import Calibration_List, Calibration_Metadata
    from Node_Info_Popup import Build_Node_Info_Popup
    from View_Edit_And_Save_Calibration_Files_In_A_New_Window import Preview_Calibration_File_For_File_Path


    # Fallback scene dimensions used only if viewport size is temporarily unavailable.
    Scene_Width_Default = 2000
    Scene_Height_Default = 1200


    # ─── Shape helper ────────────────────────────────────────────────────────────

    def Shape_Path(shape, cx, cy, r):
        """Return a QPainterPath for the requested shape, centered at (cx, cy) with radius r."""
        p = QPainterPath()
        if shape == 'ellipse':
            p.addEllipse(QPointF(cx, cy), r, r)
        elif shape == 'square':
            p.addRect(cx - r, cy - r, r * 2, r * 2)
        elif shape == 'diamond':
            poly = QPolygonF([
                QPointF(cx,     cy - r),
                QPointF(cx + r, cy),
                QPointF(cx,     cy + r),
                QPointF(cx - r, cy),
            ])
            p.addPolygon(poly)
            p.closeSubpath()
        elif shape == 'triangle':
            poly = QPolygonF([
                QPointF(cx,                       cy - r),
                QPointF(cx + r * math.sqrt(3)/2, cy + r / 2),
                QPointF(cx - r * math.sqrt(3)/2, cy + r / 2),
            ])
            p.addPolygon(poly)
            p.closeSubpath()
        elif shape == 'star':
            r_in = r * 0.42
            pts = []
            for i in range(10):
                angle = math.radians(-90 + i * 36)
                rad = r if i % 2 == 0 else r_in
                pts.append(QPointF(cx + rad * math.cos(angle),
                                   cy + rad * math.sin(angle)))
            p.addPolygon(QPolygonF(pts))
            p.closeSubpath()
        else:
            p.addEllipse(QPointF(cx, cy), r, r)
        return p


    # ─── Node item ───────────────────────────────────────────────────────────────

    class NodeItem(QGraphicsObject):
        """
        A draggable calibration node.  Shape and fill color express the node class
        (selected, chain, normal, missing, absolute, not_specified).  Right-click
        emits Right_Clicked for the info popup.
        """

        Clicked       = Signal(str)          # node_id
        Right_Clicked = Signal(str, object)  # node_id, QPointF screen position
        User_Moved    = Signal(str, object)  # node_id, QPointF scene position

        def __init__(self, node_id, node_class, style, label_text, colors, route_role=None, is_user_moved=False, label_font_size=10.0):
            super().__init__()
            self._id     = node_id
            self._cls    = node_class
            self._shape  = style['shape']
            self._r      = style['radius']
            self._label  = label_text
            self._fill   = QColor(style['fill'])
            self._bg     = QColor(colors.get('Tertiary_Background'))
            self._text   = QColor(colors.get('Secondary_Text'))
            self._edges  = []
            self._route_role = route_role  # semantic role: absolute | not_specified | None
            self._is_user_moved = bool(is_user_moved)
            self._drag_start_pos = None

            # Pre-compute label metrics in scene units so boundingRect is accurate
            self._lbl_font = QFont('Noto Sans', 10)
            self._lbl_font.setPointSizeF(max(1.0, float(label_font_size)))
            if label_text:
                fm             = QFontMetrics(self._lbl_font)
                self._lbl_w    = fm.horizontalAdvance(label_text)
                self._lbl_h    = fm.height()
                self._lbl_asc  = fm.ascent()
            else:
                self._lbl_w = self._lbl_h = self._lbl_asc = 0

            self.setFlag(QGraphicsItem.ItemIsMovable,             True)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges,  True)
            self.setAcceptHoverEvents(True)
            self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
            self.setZValue(style.get('z', 2))

            shadow = style.get('shadow')
            if shadow:
                eff = QGraphicsDropShadowEffect()
                eff.setBlurRadius(shadow.get('blur', 7.0))
                eff.setOffset(shadow.get('offset_x', 1.0), shadow.get('offset_y', 1.5))
                shadow_color = QColor(shadow.get('color'))
                shadow_color.setAlpha(shadow.get('alpha', 70))
                eff.setColor(shadow_color)
                self.setGraphicsEffect(eff)

        # ── edge bookkeeping ──────────────────────────────────────────────────

        def add_edge(self, edge):
            self._edges.append(edge)

        def itemChange(self, change, value):
            if change == QGraphicsItem.ItemPositionHasChanged:
                for e in self._edges:
                    e.update_path()
            return super().itemChange(change, value)

        def preferred_anchor_side(self):
            """
            Return preferred edge anchor side for this node:
            - 'below' for absolute nodes (unless user-moved)
            - 'above' for not_specified nodes (unless user-moved)
            - None otherwise.
            """
            if self._is_user_moved:
                return None
            if self._route_role == 'absolute':
                return 'below'
            if self._route_role == 'not_specified':
                return 'above'
            return None

        # ── geometry ─────────────────────────────────────────────────────────

        def boundingRect(self):
            r = self._r
            pad = 4
            aa_pad = 10  # repaint padding for antialias fringe + drop shadow

            # Symbol bounds
            left = -(r + 4)
            top = -(r + 4)
            right = (r + 4)
            bottom = (r + 4)

            # Label bounds (if present) as painted in paint()
            if self._label:
                tw = self._lbl_w
                th = self._lbl_h
                lx = -(tw + 2 * pad) / 2
                ly = r + 8
                lright = lx + tw + 2 * pad
                lbot = ly + th + 2 * pad
                left = min(left, lx)
                right = max(right, lright)
                bottom = max(bottom, lbot)

            return QRectF(
                left - aa_pad,
                top - aa_pad,
                (right - left) + aa_pad * 2,
                (bottom - top) + aa_pad * 2,
            )

        # ── painting ─────────────────────────────────────────────────────────

        def paint(self, painter, *_):
            painter.setRenderHint(QPainter.Antialiasing)
            r      = self._r
            path   = Shape_Path(self._shape, 0, 0, r)

            painter.setBrush(QBrush(self._fill))
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)

            if self._label:
                pad = 4
                tw  = self._lbl_w
                th  = self._lbl_h
                lx  = -(tw + 2 * pad) / 2
                ly  = r + 8
                bg  = QColor(self._bg)
                bg.setAlpha(220)
                painter.setFont(self._lbl_font)
                painter.setBrush(QBrush(bg))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(lx, ly, tw + 2 * pad, th + 2 * pad, 4, 4)
                painter.setPen(self._text)
                painter.drawText(
                    QRectF(lx, ly, tw + 2 * pad, th + 2 * pad),
                    Qt.AlignCenter,
                    self._label
                )

        # ── interaction ──────────────────────────────────────────────────────

        def mousePressEvent(self, event):
            if event.button() == Qt.RightButton:
                print(f"[NodeItem] Right click detected on node: {self._id}")
                self.Right_Clicked.emit(self._id, event.screenPos())
                event.accept()
                return
            if event.button() == Qt.LeftButton:
                self._drag_start_pos = QPointF(self.pos())
            # Left-click is drag-only for now; do not trigger selection redraw.
            super().mousePressEvent(event)

        def mouseReleaseEvent(self, event):
            super().mouseReleaseEvent(event)
            if event.button() == Qt.LeftButton and self._drag_start_pos is not None:
                end_pos = self.pos()
                moved_dist = math.hypot(end_pos.x() - self._drag_start_pos.x(),
                                        end_pos.y() - self._drag_start_pos.y())
                if moved_dist > 0.75:
                    self._is_user_moved = True
                    self.User_Moved.emit(self._id, QPointF(end_pos))
                self._drag_start_pos = None

        def contextMenuEvent(self, event):
            print(f"[NodeItem] contextMenuEvent on node: {self._id}")
            # Right-click popup is triggered from mousePressEvent to support
            # trackpads consistently; avoid duplicate popup opens here.
            event.accept()

        def hoverEnterEvent(self, event):
            self.setCursor(QCursor(Qt.PointingHandCursor))
            super().hoverEnterEvent(event)

        def hoverLeaveEvent(self, event):
            self.unsetCursor()
            super().hoverLeaveEvent(event)


    # ─── Edge item ───────────────────────────────────────────────────────────────

    class EdgeItem(QGraphicsItem):
        """
        A directed bezier edge with a filled arrowhead at the target.
        Can optionally render a second arrowhead at the source for reciprocal links.
        Recomputes its path automatically whenever a connected node moves.
        """

        def __init__(self, source_node, target_node, line_hex, line_width, z_val, source_gap=6.0, target_gap=6.0, bidirectional=False):
            super().__init__()
            self._src   = source_node
            self._tgt   = target_node
            self._color = QColor(line_hex)
            self._width = line_width
            self._source_gap = source_gap
            self._target_gap = target_gap
            self._bidirectional = bool(bidirectional)
            self._path  = QPainterPath()
            self._arrows = QPainterPath()
            self._collision_path = QPainterPath()
            self.setZValue(z_val)
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
            source_node.add_edge(self)
            target_node.add_edge(self)
            self.update_path()

        def _shares_node_with(self, other):
            return (
                self._src is other._src or self._src is other._tgt or
                self._tgt is other._src or self._tgt is other._tgt
            )

        def _endpoint_for_node(self, node_pos, node_r, node_gap, other_pos, preferred_side):
            """
            Endpoint just outside the node boundary.
            preferred_side:
            - 'below': anchor at node bottom
            - 'above': anchor at node top
            - None: radial anchor toward other node
            """
            if preferred_side in ('below', 'above'):
                side = 1.0 if preferred_side == 'below' else -1.0
                dx = other_pos.x() - node_pos.x()
                x_bias = max(-node_r * 0.6, min(node_r * 0.6, dx * 0.15))
                return QPointF(
                    node_pos.x() + x_bias,
                    node_pos.y() + side * (node_r + node_gap)
                )

            dx = other_pos.x() - node_pos.x()
            dy = other_pos.y() - node_pos.y()
            lng = math.sqrt(dx * dx + dy * dy) or 1.0
            nx, ny = dx / lng, dy / lng
            return QPointF(
                node_pos.x() + nx * (node_r + node_gap),
                node_pos.y() + ny * (node_r + node_gap)
            )

        def _build_arrowhead(self, base_mid, dir_x, dir_y, node_radius):
            a_len = max(9.0, node_radius * 0.55)
            a_half_w = max(4.5, node_radius * 0.32)
            alen = math.sqrt(dir_x * dir_x + dir_y * dir_y) or 1.0
            anx, any_ = dir_x / alen, dir_y / alen
            tip = QPointF(base_mid.x() + anx * a_len, base_mid.y() + any_ * a_len)
            left = QPointF(base_mid.x() + any_ * a_half_w, base_mid.y() - anx * a_half_w)
            right = QPointF(base_mid.x() - any_ * a_half_w, base_mid.y() + anx * a_half_w)
            arrow = QPainterPath(tip)
            arrow.lineTo(left)
            arrow.lineTo(right)
            arrow.closeSubpath()
            return arrow

        def _build_route(self, curved=True):
            sp = self._src.pos()
            tp = self._tgt.pos()
            sr = self._src._r
            tr = self._tgt._r

            src_pref = self._src.preferred_anchor_side() if hasattr(self._src, "preferred_anchor_side") else None
            tgt_pref = self._tgt.preferred_anchor_side() if hasattr(self._tgt, "preferred_anchor_side") else None

            src_pt = self._endpoint_for_node(sp, sr, self._source_gap, tp, src_pref)
            tgt_pt = self._endpoint_for_node(tp, tr, self._target_gap, sp, tgt_pref)

            ddx = tgt_pt.x() - src_pt.x()
            ddy = tgt_pt.y() - src_pt.y()
            lng = math.sqrt(ddx * ddx + ddy * ddy) or 1.0
            nx, ny = ddx / lng, ddy / lng
            px, py = -ny, nx  # perpendicular unit vector

            path = QPainterPath(src_pt)

            if curved:
                bow = min(lng * 0.18, 55.0)
                src_v_bias = 0.0
                tgt_v_bias = 0.0
                if src_pref == 'below':
                    src_v_bias = min(44.0, lng * 0.20)
                elif src_pref == 'above':
                    src_v_bias = -min(44.0, lng * 0.20)
                if tgt_pref == 'below':
                    tgt_v_bias = min(44.0, lng * 0.20)
                elif tgt_pref == 'above':
                    tgt_v_bias = -min(44.0, lng * 0.20)

                c1 = QPointF(
                    src_pt.x() + nx * lng * 0.25 + px * bow,
                    src_pt.y() + ny * lng * 0.25 + py * bow + src_v_bias
                )
                c2 = QPointF(
                    tgt_pt.x() - nx * lng * 0.25 + px * bow,
                    tgt_pt.y() - ny * lng * 0.25 + py * bow + tgt_v_bias
                )
                path.cubicTo(c1, c2, tgt_pt)
                adx = tgt_pt.x() - c2.x()
                ady = tgt_pt.y() - c2.y()
                sdx = c1.x() - src_pt.x()
                sdy = c1.y() - src_pt.y()
            else:
                path.lineTo(tgt_pt)
                adx = tgt_pt.x() - src_pt.x()
                ady = tgt_pt.y() - src_pt.y()
                sdx = ddx
                sdy = ddy

            # Arrowhead — direction taken from the terminal tangent.
            arrows = self._build_arrowhead(tgt_pt, adx, ady, tr)
            if self._bidirectional:
                arrows.addPath(self._build_arrowhead(src_pt, -sdx, -sdy, sr))

            stroker = QPainterPathStroker()
            stroker.setWidth(max(self._width + 3.0, 4.0))
            stroker.setCapStyle(Qt.RoundCap)
            collision_path = stroker.createStroke(path)

            return path, arrows, collision_path

        def _curve_would_collide(self, candidate_collision_path):
            scene = self.scene()
            if scene is None:
                return False
            for item in scene.items():
                if not isinstance(item, EdgeItem) or item is self:
                    continue
                if self._shares_node_with(item):
                    continue
                other_collision = getattr(item, "_collision_path", None)
                if other_collision is None or other_collision.isEmpty():
                    continue
                if candidate_collision_path.intersects(other_collision):
                    return True
            return False

        def update_path(self):
            curved_path, curved_arrows, curved_collision = self._build_route(curved=True)
            if self._curve_would_collide(curved_collision):
                path, arrows, collision = self._build_route(curved=False)
            else:
                path, arrows, collision = curved_path, curved_arrows, curved_collision

            self.prepareGeometryChange()
            self._path = path
            self._arrows = arrows
            self._collision_path = collision

        def boundingRect(self):
            return (self._path.boundingRect()
                    .united(self._arrows.boundingRect())
                    .adjusted(-4, -4, 4, 4))

        def paint(self, painter, *_):
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(self._color, self._width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self._path)
            painter.setBrush(QBrush(self._color))
            painter.setPen(Qt.NoPen)
            painter.drawPath(self._arrows)


    # ─── Background column item ───────────────────────────────────────────────────

    class BackgroundItem(QGraphicsItem):
        """
        Semi-transparent rounded rect marking one composition column.
        The composition name is drawn inside the top edge.
        """

        def __init__(self, cx, cy, w, h, label, colors, label_font=None, label_height=26):
            super().__init__()
            self._rect  = QRectF(cx - w / 2, cy - h / 2, w, h)
            self._label = label
            fill        = QColor(colors.get('Quinary_Text'))
            fill.setAlphaF(0.18)
            self._fill  = fill
            self._text  = QColor(colors.get('Quinary_Text'))
            self._label_font = label_font if label_font is not None else QFont('Noto Sans', 9, QFont.Bold)
            self._label_h    = label_height
            self.setZValue(0)
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)

        def boundingRect(self):
            return self._rect.adjusted(-1, -1, 1, 1)

        def paint(self, painter, *_):
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw background below the top label band.
            bg_rect = QRectF(
                self._rect.x(),
                self._rect.y() + self._label_h,
                self._rect.width(),
                max(0.0, self._rect.height() - self._label_h)
            )
            painter.setBrush(QBrush(self._fill))
            painter.setPen(Qt.NoPen)
            if bg_rect.height() > 0:
                painter.drawRoundedRect(bg_rect, 10, 10)

            painter.setFont(self._label_font)
            painter.setPen(self._text)
            label_rect = QRectF(self._rect.x(), self._rect.y(),
                                self._rect.width(), self._label_h)
            painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap,
                             self._label)


    # ─── Graph view ───────────────────────────────────────────────────────────────

    class CalibrationGraphView(QGraphicsView):
        """
        Zoomable (mouse-wheel), pannable (left-drag) view of the calibration graph.
        Emits Node_Clicked and Node_Right_Clicked so the parent window can act on them.
        """

        Node_Clicked       = Signal(str)
        Node_Right_Clicked = Signal(str, object)
        Node_Moved         = Signal(str, object)

        def __init__(self, parent=None):
            super().__init__(parent)
            self._scene = QGraphicsScene(self)
            self.setScene(self._scene)
            self.setRenderHint(QPainter.Antialiasing)
            self.setRenderHint(QPainter.SmoothPixmapTransform)
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setFrameShape(QFrame.NoFrame)
            self.setObjectName("GraphView")
            self._min_zoom = 0.04
            self._max_zoom = 8.0

        def wheelEvent(self, event):
            factor = 1.18 if event.angleDelta().y() > 0 else 1.0 / 1.18
            cur    = self.transform().m11()
            if (factor > 1 and cur < self._max_zoom) or \
               (factor < 1 and cur > self._min_zoom):
                self.scale(factor, factor)

        def reset_zoom(self):
            rect = self._scene.sceneRect()
            if rect.isEmpty():
                rect = self._scene.itemsBoundingRect()
            if not rect.isEmpty():
                self.resetTransform()
                self.centerOn(rect.center())
                self.fitInView(rect, Qt.KeepAspectRatio)

        def fill_to_viewport(self):
            rect = self._scene.sceneRect()
            if rect.isEmpty():
                rect = self._scene.itemsBoundingRect()
            if not rect.isEmpty():
                self.fitInView(rect, Qt.IgnoreAspectRatio)

        def build(self, bg_items, node_items, edge_items, scene_rect=None, auto_fit=True):
            """Replace scene contents with the provided items."""
            self._scene.clear()
            for item in bg_items:
                self._scene.addItem(item)
            for item in edge_items:
                self._scene.addItem(item)
            for item in node_items:
                self._scene.addItem(item)
                if hasattr(item, 'Clicked'):
                    item.Clicked.connect(self.Node_Clicked)
                if hasattr(item, 'Right_Clicked'):
                    item.Right_Clicked.connect(self.Node_Right_Clicked)
                if hasattr(item, 'User_Moved'):
                    item.User_Moved.connect(self.Node_Moved)
            # Recompute edge paths now that all edges are in-scene so collision-aware
            # curve-vs-straight routing can compare against neighbors.
            for _ in range(2):
                for item in edge_items:
                    if hasattr(item, 'update_path'):
                        item.update_path()
            if scene_rect is not None:
                self._scene.setSceneRect(scene_rect)
            else:
                self._scene.setSceneRect(self._scene.itemsBoundingRect())
            if auto_fit:
                self.reset_zoom()


    # ─── Main window ──────────────────────────────────────────────────────────────

    class EoSHolo(QMainWindow):

        def __init__(self):
            super().__init__()

            # Build Settings lazily to avoid creating an extra top-level dialog at startup.
            self.Settings = None
            self._Node_Info_Popup = None
            self._Node_Info_Filter_Installed = False
            self._Focus_Mode = "default"        # default | to_node | through_node
            self._Focus_Node_ID = None
            self._Manual_Node_Positions = {}    # node_id -> (x, y), set by user drag
            self._Seen_Reciprocal_Print_Signatures = set()
            self._Initial_Graph_Drawn = False
            self._Initial_Graph_Revealed = False
            self._Graph_Update_Pending = False
            self._Graph_Update_Pending_Params = None
            self._Graph_Update_Timer = QTimer()
            self._Graph_Update_Timer.setSingleShot(True)
            self._Graph_Update_Timer.timeout.connect(self._Run_Scheduled_Graph_Update)

            # Set the window title and icon
            self.setWindowTitle("EoSHolo")
            Icon_File = "Graphics/EoSHolo_With_Sun.png"
            self.setWindowIcon(QIcon(Get_Resource_Path(Icon_File)))
            # Pre-paint the top-level window with theme background to avoid any
            # transient default (white) frame before child widgets finish drawing.
            _, _, startup_colors = Get_Theme()
            bg_color = startup_colors.get('Primary_Background', '#1a1a2e')
            self.setStyleSheet(
                f"QMainWindow {{ background: {bg_color}; }}"
            )
            # Also set the Qt palette so Windows uses the correct color during
            # maximize/restore animation (stylesheet alone does not cover this).
            from PySide6.QtGui import QPalette, QColor
            _pal = self.palette()
            _pal.setColor(QPalette.Window, QColor(bg_color))
            self.setPalette(_pal)

            # Debounce timer for resize events
            self.Resize_Timer = QTimer()
            self.Resize_Timer.setSingleShot(True)
            self.Resize_Timer.timeout.connect(self.On_Resize_Complete)

            # Menu bar
            self.setMenuBar(MainMenuBar(self))

            # Load calibration data and build graph structure
            self.Initialize_Data()

            # ── Layout ────────────────────────────────────────────────────────

            Central_Widget = QWidget()
            Central_Widget.setObjectName("CentralWidget")
            Main_Layout = QVBoxLayout()
            Main_Layout.setContentsMargins(0, 0, 0, 0)
            Main_Layout.setSpacing(0)

            # Banner
            self.Banner = Banner("", Get_Resource_Path("Graphics/EoSHolo_With_Sun.png"))
            Main_Layout.addWidget(self.Banner)

            # Size and centre the window
            Screen          = self.screen()
            Screen_Geometry = Screen.availableGeometry()
            Window_Width    = int(Screen_Geometry.width()  * 0.7)
            Window_Height   = int(Screen_Geometry.height() * 0.8)
            X = (Screen_Geometry.width()  - Window_Width)  // 2 + Screen_Geometry.x()
            Y = (Screen_Geometry.height() - Window_Height) // 2 + Screen_Geometry.y()
            self.setGeometry(X, Y, Window_Width, Window_Height)
            self.setMinimumSize(500, 400)

            # Controls bar
            self.Controls_Widget = QWidget()
            self.Controls_Widget.setObjectName("ControlsBar")
            Controls_Layout = QVBoxLayout(self.Controls_Widget)
            Controls_Layout.setContentsMargins(10, 10, 10, 10)
            Controls_Layout.setSpacing(10)

            Top_Controls_Layout = QHBoxLayout()
            Top_Controls_Layout.setContentsMargins(0, 0, 0, 0)
            Top_Controls_Layout.setSpacing(10)
            Controls_Layout.addLayout(Top_Controls_Layout)

            Comp_Label = QLabel("Composition:")
            Comp_Label.setObjectName("ControlsLabel")
            Top_Controls_Layout.addWidget(Comp_Label)

            self.Composition_Dropdown = Dropdown()
            self.Composition_Dropdown.setObjectName("Dropdown")
            self.Composition_Dropdown.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.Composition_Dropdown.setPlaceholderText("Select a composition...")
            for Composition_Key in sorted(self.Compositions, key=lambda c: Material_Information.get(c, {}).get('Display_Name', c)):
                Display_Label = Material_Information.get(Composition_Key, {}).get('Display_Name', Composition_Key)
                self.Composition_Dropdown.addItem(Display_Label, Composition_Key)
            self.Composition_Dropdown.setCurrentIndex(-1)
            Top_Controls_Layout.addWidget(self.Composition_Dropdown)
            self.Fit_Composition_Dropdown_Width()

            Study_Label = QLabel("Study:")
            Study_Label.setObjectName("ControlsLabel")

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

            self.Study_Dropdown = Dropdown()
            self.Study_Dropdown.setObjectName("Dropdown")
            self.Study_Dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.Study_Dropdown.setPlaceholderText("Select a pressure calibration study...")
            self.Study_Dropdown.setSizeAdjustPolicy(Dropdown.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self.Study_Dropdown.view().setItemDelegate(
                WordWrapDelegate(self.Study_Dropdown.view(), self.Study_Dropdown)
            )
            self.Study_Dropdown.setMinimumWidth(240)
            self.Study_Dropdown.setCurrentIndex(-1)
            Study_Row_Layout.addWidget(self.Study_Dropdown)
            Study_Row_Layout.setStretchFactor(self.Study_Dropdown, 1)
            Study_Column_Layout.addLayout(Study_Row_Layout)

            # Footnote row — shown only when the currently selected study is user-edited or entered.
            # Indented past the "Study:" label and spacing, plus the dropdown's own internal
            # text inset, so it lines up with where the "*" appears in the dropdown text.
            Footnote_Left_Margin = Study_Label.sizeHint().width() + Study_Row_Layout.spacing() + 9
            self.EoSHolo_Study_Footnote = QLabel("* indicates user edited or entered calibrant")
            self.EoSHolo_Study_Footnote.setObjectName("ControlsFootnote")
            self.EoSHolo_Study_Footnote.setStyleSheet(f"font-size: 8pt; color: {self._Get_Colors().get('Caution_Text')};")
            self.EoSHolo_Study_Footnote.setWordWrap(True)
            self.EoSHolo_Study_Footnote.setContentsMargins(Footnote_Left_Margin, 0, 0, 0)
            self.EoSHolo_Study_Footnote.setVisible(False)
            Study_Column_Layout.addWidget(self.EoSHolo_Study_Footnote)

            Top_Controls_Layout.addLayout(Study_Column_Layout, 1)

            self.Preview_Calibration_Button = QPushButton("Preview Calibrant")
            self.Preview_Calibration_Button.setObjectName("Preview_Calibration_Button")
            self.Preview_Calibration_Button.setToolTip("Select a study to preview its YAML file.")
            self.Preview_Calibration_Button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.Preview_Calibration_Button.setFixedHeight(32)
            Top_Controls_Layout.addWidget(self.Preview_Calibration_Button)

            self.Reset_Zoom_Button = QPushButton("Reset Zoom")
            self.Reset_Zoom_Button.setObjectName("PrimaryButton")
            self.Reset_Zoom_Button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.Reset_Zoom_Button.setFixedHeight(32)
            Top_Controls_Layout.addWidget(self.Reset_Zoom_Button)

            self.Show_All_Row = CheckboxRow()
            Show_All_Row_Layout = QHBoxLayout(self.Show_All_Row)
            Show_All_Row_Layout.setContentsMargins(6, 4, 6, 4)
            Show_All_Row_Layout.setSpacing(6)

            self.Show_All_Checkbox = QCheckBox()
            self.Show_All_Checkbox.setObjectName("Checkbox")
            self.Show_All_Checkbox.setChecked(True)
            self.Show_All_Checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            Show_All_Row_Layout.addWidget(self.Show_All_Checkbox)

            self.Show_All_Label = QLabel("Show All Nodes")
            self.Show_All_Label.setObjectName("CollapsibleContentLabel")
            self.Show_All_Label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
            self.Show_All_Label.mousePressEvent = lambda _, cb=self.Show_All_Checkbox: cb.setChecked(not cb.isChecked())
            Show_All_Row_Layout.addWidget(self.Show_All_Label)
            Show_All_Row_Layout.addStretch(1)
            self.Show_All_Row.mousePressEvent = (
                lambda event, cb=self.Show_All_Checkbox: cb.setChecked(not cb.isChecked())
                if event.button() == Qt.LeftButton else None
            )

            Top_Controls_Layout.addWidget(self.Show_All_Row)
            Main_Layout.addWidget(self.Controls_Widget)

            # Graph view
            self.Graph_View = CalibrationGraphView()
            self.Graph_View.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.Graph_View.setVisible(True)
            _bg_color = QColor(startup_colors.get('Primary_Background'))
            _graph_bg = QBrush(_bg_color)
            self.Graph_View.setBackgroundBrush(_graph_bg)
            self.Graph_View._scene.setBackgroundBrush(_graph_bg)
            Main_Layout.addWidget(self.Graph_View, stretch=1)

            Central_Widget.setLayout(Main_Layout)
            self.setCentralWidget(Central_Widget)

            # Apply EoSHolo-specific stylesheet to the central widget
            self.Apply_EoSHolo_Stylesheet(Central_Widget)

            # The stylesheet above breaks Qt's palette inheritance chain from
            # QMainWindow, leaving the viewport with QPalette.Base = white.
            # That causes a white flash when new pixels are auto-filled before
            # QGraphicsView's own paint event runs (e.g. on first maximize).
            _vp = self.Graph_View.viewport()
            _vp_pal = _vp.palette()
            _vp_pal.setColor(QPalette.All, QPalette.Base, _bg_color)
            _vp_pal.setColor(QPalette.All, QPalette.Window, _bg_color)
            _vp.setPalette(_vp_pal)
            # Disable the automatic pre-paint erase so Qt never fills the
            # viewport with the white Base colour before drawBackground() runs.
            # The scene backgroundBrush covers the full exposed rect instead.
            _vp.setAutoFillBackground(False)

            # Wire up controls
            self.Composition_Dropdown.currentIndexChanged.connect(self.On_Composition_Changed)
            self.Study_Dropdown.currentTextChanged.connect(self.On_Study_Changed)
            self.Preview_Calibration_Button.clicked.connect(self.On_Preview_Calibration_Clicked)
            self.Reset_Zoom_Button.clicked.connect(self.Graph_View.reset_zoom)
            self.Show_All_Checkbox.stateChanged.connect(self.On_Show_All_Changed)
            self.Graph_View.Node_Clicked.connect(self.On_Node_Clicked)
            self.Graph_View.Node_Right_Clicked.connect(self.Show_Node_Info)
            self.Graph_View.Node_Moved.connect(self.On_Node_Moved)
            self._Update_Preview_Calibration_Button_State()

            # Initial graph draw is deferred until a real viewport size exists.


        # ── Stylesheet helpers ────────────────────────────────────────────────

        def Get_Settings_Dialog(self):
            if self.Settings is None:
                # parent=None → true top-level window, minimises to taskbar normally.
                self.Settings = Settings(None)
                if hasattr(self.Settings, "theme_changed"):
                    self.Settings.theme_changed.connect(self.On_Theme_Changed)
            return self.Settings

        def _Study_Display_Sort_Key(self, display_label):
            text = str(display_label or "")
            study_name, separator, remainder = text.partition(" | ")
            normalized_study_name = study_name.replace("*", "").strip().casefold()
            normalized_remainder = remainder.casefold() if separator else ""
            return (normalized_study_name, normalized_remainder, text.casefold())

        def _Load_EoSHolo_QSS(self):
            """Load the EoSHolo-specific QSS blocks for the current theme."""
            from Themes.Theme import Load_EoSHolo_Style_Sheet
            return Load_EoSHolo_Style_Sheet(Get_Resource_Path)

        def Apply_EoSHolo_Stylesheet(self, widget):
            widget.setStyleSheet(self._Load_EoSHolo_QSS())

        def _Get_Colors(self):
            """Return current theme colours."""
            _, _, COLORS = Get_Theme()
            return COLORS

        def Fit_Composition_Dropdown_Width(self):
            """Size composition dropdown tightly to its longest item text."""
            fm = QFontMetrics(self.Composition_Dropdown.font())
            longest_text = max((self.Composition_Dropdown.itemText(i) for i in range(self.Composition_Dropdown.count())), key=len, default="")
            text_width = fm.horizontalAdvance(longest_text)
            # Account for QSS padding and dropdown button area.
            self.Composition_Dropdown.setFixedWidth(text_width + 50)

        def _Get_Selected_Composition_Key(self):
            if self.Composition_Dropdown.currentIndex() < 0:
                return None
            return self.Composition_Dropdown.currentData() or None

        def _Schedule_Graph_Update(self, forced_viewport_size=None, auto_fit=True, delay_ms=0):
            """
            Queue a graph rebuild onto the next event-loop tick so UI controls can
            repaint before heavy layout/render work starts.
            """
            self._Graph_Update_Pending_Params = (forced_viewport_size, auto_fit)
            if not self._Graph_Update_Pending:
                self._Graph_Update_Pending = True
            self._Graph_Update_Timer.start(max(0, int(delay_ms)))

        def _Run_Scheduled_Graph_Update(self):
            self._Graph_Update_Pending = False
            Params = self._Graph_Update_Pending_Params or (None, True)
            self._Graph_Update_Pending_Params = None
            forced_viewport_size, auto_fit = Params
            self.Update_Graph(forced_viewport_size=forced_viewport_size, auto_fit=auto_fit)

        def _Get_Node_Styles(self, colors, fixed_node_size=25):
            """
            Central node style definition:
            - size/radius per class
            - shape per class
            - fill color per class
            """
            base_radius = fixed_node_size / 2
            size_scale = {
                'normal':        1.0,
                'selected':      2.5,
                'absolute':       1.0,
                'chain':         1.0,
                'through_child': 1.0,
                'not_specified': 1.0,
                'missing':       1.0,
            }
            shape_for_class = {
                'normal':        'ellipse',
                'selected':      'star',
                'chain':         'ellipse',
                'through_child': 'ellipse',
                'missing':       'triangle',
                'absolute':       'diamond',
                'not_specified': 'square',
            }
            fill_for_class = {
                'selected':      colors.get('Primary_Color'),
                'chain':         colors.get('Secondary_Color'),
                'through_child': colors.get('Tertiary_Color', colors.get('Tertiary_Text')),
                'normal':        colors.get('Tertiary_Text'),
                'missing':       colors.get('Warning_Color'),
                'absolute':       colors.get('Quaternary_Text'),
                'not_specified': colors.get('Quaternary_Text'),
            }
            z_for_class = {
                'not_specified': 2,
                'normal':        4,
                'missing':       3,
                'absolute':       5,
                'chain':         6,
                'through_child': 6,
                'selected':      7,
            }
            shadow = {
                'blur': 7.0,
                'offset_x': 1.2,
                'offset_y': 1.8,
                'color': '#000000',
                'alpha': 70,
            }

            styles = {}
            for node_class in shape_for_class:
                styles[node_class] = {
                    'radius': base_radius * size_scale.get(node_class, 1.0),
                    'shape': shape_for_class[node_class],
                    'fill': fill_for_class[node_class],
                    'z': z_for_class.get(node_class, 2),
                    'shadow': dict(shadow),
                }
            return styles

        def _Get_Edge_Styles(self, colors):
            """Central edge style definition for line/arrow color, width, and endpoint spacing."""
            return {
                'source_gap': 8.0,
                'target_gap': 14.0,
                'normal': {
                    'color': colors.get('Tertiary_Text'),
                    'width': 2,
                    'z': 1,
                },
                'chain': {
                    'color': colors.get('Secondary_Text'),
                    'width': 4,
                    'z': 1,
                },
            }


        # ── Data loading (unchanged logic from original) ───────────────────────

        def Initialize_Data(self):

            self.Parsed_Calibrations = []
            Seen_Combinations        = {}
            All_Nodes                = {}
            Special_Node_Prefix      = "__EoSHolo::special::"
            Missing_Node_Prefix      = "__EoSHolo::missing_parent::"

            for Label, _ in Calibration_List:
                Metadata     = Calibration_Metadata[Label]
                Study_Name   = Metadata['Study']
                Composition  = Metadata['Composition']
                EoS          = Metadata['Equation of State']
                Order        = Metadata['Order']
                Cal_To_Name  = Metadata.get('Reference Study', '')
                PTM          = Metadata.get('Pressure Transmitting Medium', '')
                Max_Pressure = Metadata['Maximum Pressure']
                Is_K0_Fixed  = Metadata.get('Is The Initial Bulk Modulus Fixed?', '')
                Method       = Metadata.get('Method', '')

                _Is_User = Metadata.get('is_user_edited', False) or Metadata.get('is_user_entered', False)
                _User_Prefix = "* " if _Is_User else ""
                Display_Label = (
                    f"{_User_Prefix}{Study_Name} | {Composition} | {Method} | {EoS} | "
                    f"K0 Fixed: {Is_K0_Fixed} | cal_to: {Cal_To_Name} | "
                    f"Max Pressure: {Max_Pressure} GPa | PTM: {PTM}"
                ).replace("\n", "").strip()

                # Use the canonical calibration key from the cache/calibration list.
                # This guarantees one node per calibration entry and stable uniqueness.
                Node_Key = Label
                if Node_Key in Seen_Combinations:
                    print(f"ERROR: Duplicate calibration found!")
                    continue
                Seen_Combinations[Node_Key] = Label

                Entry = {
                    'study':          Study_Name,
                    'composition':    Composition,
                    'eos':            EoS,
                    'order':          Order,
                    'max_pressure':   Max_Pressure,
                    'is_K0_fixed':    Is_K0_Fixed,
                    'parent_info': {
                        'cal_to_name':         Metadata.get('Reference Study', ''),
                        'cal_to_composition':  Metadata.get('Reference Composition', ''),
                        'cal_to_eos':          Metadata.get('Reference Equation of State', ''),
                        'cal_to_order':        Metadata.get('Reference Equation of State Order', None),
                        'cal_to_max_pressure': Metadata.get('Reference Maximum Pressure', None),
                        'cal_to_is_K0_fixed':  Metadata.get('Reference Initial Bulk Modulus Fixed?', None),
                        'cal_to_method':       Metadata.get('Reference Method', None),
                        'cal_to_cal':          Metadata.get("Reference's Reference", ''),
                    },
                    'parent_node_ids': [],
                    'label':           Label,
                    'display_label':   Display_Label,
                    'metadata':        Metadata,
                    'node_id':         Node_Key,
                    'has_calibration':        True,
                    'is_special':      False,
                }

                self.Parsed_Calibrations.append(Entry)
                All_Nodes[Node_Key] = Entry

            Missing_Parents = {}
            Special_Nodes   = {}
            Unresolved_Parent_Refs = []

            def _norm_text(value):
                if value is None:
                    return ''
                text = str(value).strip()
                if text.lower() in ('not specified', 'not specfied', 'none', 'null'):
                    return ''
                return text

            def _norm_ci(value):
                return _norm_text(value).lower()

            def _parse_int_or_none(value):
                text = _norm_text(value)
                if not text:
                    return None
                try:
                    return int(text)
                except Exception:
                    return None

            def _parse_float_or_none(value):
                text = _norm_text(value)
                if not text:
                    return None
                try:
                    return float(text)
                except Exception:
                    return None

            def _norm_k0_flag(value):
                text = _norm_ci(value)
                if not text:
                    return None
                if text in ('true', 'yes', 'y', '1'):
                    return True
                if text in ('false', 'no', 'n', '0'):
                    return False
                return text

            def _find_parent_node_ids(parent_study, parent_comp, parent_method, parent_eos, parent_order, parent_max_p, parent_k0):
                """
                Return all parent node IDs using ranked matching:
                1) Study (required)
                2) Composition
                3) Method
                4) Equation of State + Order
                5) Max pressure / K0 fixed as ideal tie-breakers
                """
                study_ci = _norm_ci(parent_study)
                if not study_ci:
                    return []

                comp_ci = _norm_ci(parent_comp)
                method_ci = _norm_ci(parent_method)
                eos_ci = _norm_ci(parent_eos)
                order_v = _parse_int_or_none(parent_order)
                max_p_v = _parse_float_or_none(parent_max_p)
                k0_v = _norm_k0_flag(parent_k0)

                candidates = []
                for nid, node in All_Nodes.items():
                    # Synthetic terminal markers (Absolute / Not Specified) are never
                    # real parents for other studies — they're only reachable via the
                    # single entry that created them.
                    if node.get('is_special'):
                        continue

                    # 1) Must match Study
                    if _norm_ci(node.get('study', '')) != study_ci:
                        continue

                    # 2) Must match Composition when specified
                    if comp_ci and _norm_ci(node.get('composition', '')) != comp_ci:
                        continue

                    # 3) Must match Method when specified
                    if method_ci and _norm_ci(node.get('metadata', {}).get('Method', '')) != method_ci:
                        continue

                    # 4) Must match EoS and Order when specified
                    if eos_ci and _norm_ci(node.get('eos', '')) != eos_ci:
                        continue
                    if order_v is not None:
                        node_order_v = _parse_int_or_none(node.get('order'))
                        if node_order_v != order_v:
                            continue

                    # 5) Nice-to-have tie-break scoring only
                    score = 0
                    if max_p_v is not None:
                        node_max_p_v = _parse_float_or_none(node.get('max_pressure'))
                        if node_max_p_v is not None and abs(node_max_p_v - max_p_v) < 1e-9:
                            score += 2
                    if k0_v is not None:
                        node_k0_v = _norm_k0_flag(node.get('is_K0_fixed'))
                        if node_k0_v == k0_v:
                            score += 1

                    candidates.append((score, nid))

                # Keep every valid parent, ordered by ideal matches first.
                candidates.sort(key=lambda pair: (-pair[0], pair[1]))
                return [nid for _, nid in candidates]

            for Entry in self.Parsed_Calibrations:
                Parent_Info  = Entry.get('parent_info', {})
                Cal_To_Name  = Parent_Info.get('cal_to_name', '')
                if not Cal_To_Name:
                    continue

                Parent_Studies      = [P.strip() for P in Cal_To_Name.split(';')]
                Parent_Compositions = [P.strip() for P in (Parent_Info.get('cal_to_composition', '') or '').split(';')] if Parent_Info.get('cal_to_composition') else []
                Parent_EoSs         = [P.strip() for P in (Parent_Info.get('cal_to_eos', '')          or '').split(';')] if Parent_Info.get('cal_to_eos')         else []
                Parent_Orders       = [P.strip() for P in str(Parent_Info.get('cal_to_order', '')      or '').split(';')] if Parent_Info.get('cal_to_order')       else []
                Parent_Max_Ps       = [P.strip() for P in str(Parent_Info.get('cal_to_max_pressure', '') or '').split(';')] if Parent_Info.get('cal_to_max_pressure') else []
                Parent_K0s          = [P.strip() for P in str(Parent_Info.get('cal_to_is_K0_fixed', '') or '').split(';')] if Parent_Info.get('cal_to_is_K0_fixed') else []
                Parent_Methods      = [P.strip() for P in (Parent_Info.get('cal_to_method', '')        or '').split(';')] if Parent_Info.get('cal_to_method')      else []
                Parent_Cal_Refs     = [P.strip() for P in str(Parent_Info.get('cal_to_cal', '')        or '').split(';')] if Parent_Info.get('cal_to_cal')         else []

                for lst in [Parent_Compositions, Parent_EoSs, Parent_Orders,
                             Parent_Max_Ps, Parent_K0s, Parent_Methods, Parent_Cal_Refs]:
                    if not lst:
                        lst.append('')

                for P_Idx, P_Study in enumerate(Parent_Studies):
                    P_Study_Norm = P_Study.strip().lower()
                    # cal_to_cal is informational in this matcher (tracks lineage
                    # notes) and is not used as the parent-node lookup key.

                    if 'not specif' in P_Study_Norm:
                        if P_Study.strip() != "Not Specified":
                            print(f"WARNING: Typo in cal_to_name: '{P_Study.strip()}'")
                        Comp = Parent_Compositions[min(P_Idx, len(Parent_Compositions) - 1)] if Parent_Compositions else ''
                        if not Comp or 'not specif' in Comp.lower():
                            Comp = 'Not Specified'
                        Sp_Key = f"{Special_Node_Prefix}not_specified::{Comp}"
                        if Sp_Key not in Special_Nodes:
                            Sp_Node = {
                                'study': 'Not Specified', 'composition': Comp,
                                'eos': '', 'order': None, 'max_pressure': None,
                                'is_K0_fixed': None,
                                'parent_info': {'cal_to_name': '', 'cal_to_composition': '',
                                                'cal_to_eos': '', 'cal_to_order': None,
                                                'cal_to_max_pressure': None, 'cal_to_is_K0_fixed': None,
                                                'cal_to_cal': ''},
                                'parent_node_ids': [], 'label': "Not Specified",
                                'metadata': {}, 'node_id': Sp_Key,
                                'has_calibration': False, 'is_special': True, 'special_type': 'not_specified',
                            }
                            Special_Nodes[Sp_Key] = Sp_Node
                            All_Nodes[Sp_Key]     = Sp_Node
                            self.Parsed_Calibrations.append(Sp_Node)
                        Entry['parent_node_ids'].append(Sp_Key)
                        continue

                    if P_Study_Norm == 'absolute':
                        Study    = Entry['study']
                        Comp     = Entry['composition']
                        Sp_Key   = f"{Special_Node_Prefix}absolute::{Study}::{Comp}"
                        if Sp_Key not in Special_Nodes:
                            Sp_Node = {
                                'study': Study, 'composition': Comp,
                                'eos': '', 'order': None, 'max_pressure': None,
                                'is_K0_fixed': None,
                                'parent_info': {'cal_to_name': '', 'cal_to_composition': '',
                                                'cal_to_eos': '', 'cal_to_order': None,
                                                'cal_to_max_pressure': None, 'cal_to_is_K0_fixed': None,
                                                'cal_to_cal': ''},
                                'parent_node_ids': [], 'label': f"{Study} (Absolute)",
                                'metadata': {}, 'node_id': Sp_Key,
                                'has_calibration': False, 'is_special': True, 'special_type': 'absolute',
                            }
                            Special_Nodes[Sp_Key] = Sp_Node
                            All_Nodes[Sp_Key]     = Sp_Node
                            self.Parsed_Calibrations.append(Sp_Node)
                        Entry['parent_node_ids'].append(Sp_Key)
                        continue

                    Sub = P_Study.strip()
                    if not Sub or len(Sub) < 3:
                        continue
                    if '(' in Sub or ')' in Sub or ':' in Sub:
                        continue

                    P_Comp   = Parent_Compositions[min(P_Idx, len(Parent_Compositions) - 1)]
                    P_EoS    = Parent_EoSs[min(P_Idx, len(Parent_EoSs) - 1)]
                    P_Order  = Parent_Orders[min(P_Idx, len(Parent_Orders) - 1)]
                    P_Max_P  = Parent_Max_Ps[min(P_Idx, len(Parent_Max_Ps) - 1)]
                    P_K0     = Parent_K0s[min(P_Idx, len(Parent_K0s) - 1)]
                    P_Method = Parent_Methods[min(P_Idx, len(Parent_Methods) - 1)]

                    Sub_Comps = [sc.strip() for sc in P_Comp.split(' - ')] if P_Comp and ' - ' in P_Comp else [P_Comp]

                    for Sub_Comp in Sub_Comps:
                        if not Sub_Comp:
                            Sub_Comp = Entry['composition']
                        if Sub_Comp and 'not specif' in Sub_Comp.lower():
                            Sub_Comp = 'Not Specified'

                        P_Order_V = _parse_int_or_none(P_Order)
                        P_Max_P_V = _parse_float_or_none(P_Max_P)
                        Parent_Node_IDs = _find_parent_node_ids(Sub, Sub_Comp, P_Method, P_EoS, P_Order, P_Max_P, P_K0)

                        if not Parent_Node_IDs:
                            # Record unresolved parent references for diagnostics.
                            Child_File_Path = Entry.get('metadata', {}).get('file_path', '')
                            Child_Calibration_Name = os.path.basename(Child_File_Path) if Child_File_Path else f"{Entry.get('node_id', '')}.yaml"
                            Unresolved_Parent_Refs.append({
                                'child_id': Entry.get('node_id', ''),
                                'child_calibration_name': Child_Calibration_Name,
                                'child_study': Entry.get('study', ''),
                                'child_composition': Entry.get('composition', ''),
                                'cal_to_name': Sub,
                                'cal_to_composition': Sub_Comp,
                                'cal_to_method': P_Method,
                                'cal_to_eos': P_EoS,
                                'cal_to_order': P_Order_V,
                                'cal_to_max_pressure': P_Max_P_V,
                                'cal_to_is_K0_fixed': P_K0,
                            })
                            Miss_Key = f"{Missing_Node_Prefix}{Sub}|{Sub_Comp}|{P_EoS or ''}|{P_Order_V}|{P_Max_P_V}|{P_K0}"
                            if Miss_Key not in Missing_Parents:
                                Miss_Node = {
                                    'study': Sub, 'composition': Sub_Comp,
                                    'eos': P_EoS or '', 'order': P_Order_V,
                                    'max_pressure': P_Max_P_V, 'is_K0_fixed': P_K0,
                                    'parent_info': {'cal_to_name': '', 'cal_to_composition': '',
                                                    'cal_to_eos': '', 'cal_to_order': None,
                                                    'cal_to_max_pressure': None, 'cal_to_is_K0_fixed': None,
                                                    'cal_to_cal': ''},
                                    'parent_node_ids': [], 'label': f"{Sub} (missing YAML)",
                                    'metadata': {}, 'node_id': Miss_Key,
                                    'has_calibration': False, 'is_special': False,
                                }
                                Missing_Parents[Miss_Key] = Miss_Node
                                All_Nodes[Miss_Key]       = Miss_Node
                                self.Parsed_Calibrations.append(Miss_Node)
                            Parent_Node_IDs = [Miss_Key]

                        for Parent_Node_ID in Parent_Node_IDs:
                            if Parent_Node_ID and Parent_Node_ID not in Entry['parent_node_ids']:
                                Entry['parent_node_ids'].append(Parent_Node_ID)

            self.Calibration_List = self.Parsed_Calibrations
            self.Compositions     = sorted({E['composition'] for E in self.Calibration_List})

            print(f"\nLoaded {len([E for E in self.Calibration_List if E['has_calibration']])} calibrations from YAML files")
            # print(f"Created {len(Missing_Parents)} missing parent nodes")
            print(f"Created {len(Special_Nodes)} special nodes (Absolute/Not Specified)")
            if Unresolved_Parent_Refs:
                Unresolved_Child_Count = len({rec.get('child_id', '') for rec in Unresolved_Parent_Refs if rec.get('child_id', '')})
                print(f"[EoSHolo] Calibrations with unresolved parent node: {Unresolved_Child_Count}")
            #     print("")
            #     for rec in sorted(Unresolved_Parent_Refs, key=lambda r: (r.get('child_calibration_name', ''), r.get('cal_to_name', ''), r.get('cal_to_composition', ''))):
            #         print(f"{rec.get('child_calibration_name', '')} | {rec.get('cal_to_name', '')} | {rec.get('cal_to_composition', '')}")
            # print("")


        # ── Controls callbacks ─────────────────────────────────────────────────

        def On_Composition_Changed(self, *_):
            self._Focus_Mode = "default"
            self._Focus_Node_ID = None
            Had_Selected_Study = bool((self.Study_Dropdown.currentText() or "").strip())
            Composition = self._Get_Selected_Composition_Key()
            Studies = sorted(set(
                E['display_label'] for E in self.Calibration_List
                if E['composition'] == Composition and E['has_calibration']
            ), key=self._Study_Display_Sort_Key)
            self.Study_Dropdown.blockSignals(True)
            self.Study_Dropdown.clear()
            self.Study_Dropdown.addItems(Studies)
            self.Study_Dropdown.setCurrentIndex(-1)
            self.Study_Dropdown.blockSignals(False)
            self.Update_Study_Dropdown_Footnote()
            self._Update_Preview_Calibration_Button_State()
            if Had_Selected_Study:
                self._Schedule_Graph_Update()

        def On_Study_Changed(self):
            self._Focus_Mode = "default"
            self._Focus_Node_ID = None
            self._Update_Preview_Calibration_Button_State()
            self.Update_Study_Dropdown_Footnote()
            # Give the dropdown one paint frame before rebuilding the graph.
            self._Schedule_Graph_Update(delay_ms=16)

        # Show the caution footnote only when the currently selected study is flagged,
        # and flag each popup option so WordWrapDelegate draws its caution sub-line
        def Update_Study_Dropdown_Footnote(self):
            for Index in range(self.Study_Dropdown.count()):
                Item_Text = self.Study_Dropdown.itemText(Index)
                self.Study_Dropdown.setItemData(Index, Item_Text.startswith("* "), IS_USER_CALIBRANT_ROLE)
            if hasattr(self, 'EoSHolo_Study_Footnote'):
                self.EoSHolo_Study_Footnote.setVisible(self.Study_Dropdown.currentText().startswith("* "))

        def On_Show_All_Changed(self):
            self._Focus_Mode = "default"
            self._Focus_Node_ID = None
            self._Schedule_Graph_Update()

        def On_Node_Moved(self, Node_ID, Scene_Pos):
            if Node_ID:
                self._Manual_Node_Positions[Node_ID] = (Scene_Pos.x(), Scene_Pos.y())

        def On_Node_Clicked(self, Node_ID):
            """Select the clicked node in the dropdowns and redraw."""
            Entry = next((E for E in self.Calibration_List
                          if E['node_id'] == Node_ID and E.get('has_calibration')), None)
            if not Entry:
                return

            Composition   = Entry['composition']
            Display_Label = Entry.get('display_label', Entry['label'])

            self.Composition_Dropdown.blockSignals(True)
            self.Study_Dropdown.blockSignals(True)

            C_Idx = self.Composition_Dropdown.findData(Composition)
            if C_Idx >= 0:
                self.Composition_Dropdown.setCurrentIndex(C_Idx)
                Studies = sorted(set(
                    E['display_label'] for E in self.Calibration_List
                    if E['composition'] == Composition and E['has_calibration']
                ), key=self._Study_Display_Sort_Key)
                self.Study_Dropdown.clear()
                self.Study_Dropdown.addItems(Studies)
                S_Idx = self.Study_Dropdown.findText(Display_Label)
                if S_Idx >= 0:
                    self.Study_Dropdown.setCurrentIndex(S_Idx)

            self.Composition_Dropdown.blockSignals(False)
            self.Study_Dropdown.blockSignals(False)
            self.Update_Study_Dropdown_Footnote()
            self._Update_Preview_Calibration_Button_State()

            self._Focus_Mode = "default"
            self._Focus_Node_ID = None
            self._Schedule_Graph_Update()


        # ── Node info popup (right-click) ───────────────────────────────────────

        def _Is_Widget_Inside_Node_Info_Popup(self, Widget):
            Popup = self._Node_Info_Popup
            if Popup is None or Widget is None:
                return False
            return (Widget is Popup) or Popup.isAncestorOf(Widget)

        def Close_Node_Info_Popup(self, Close_All=False):
            App = QApplication.instance()
            if Close_All and App is not None:
                for Widget in list(App.topLevelWidgets()):
                    if Widget is None:
                        continue
                    if Widget.objectName() == "NodeInfoPopupHost":
                        try:
                            Widget.close()
                        except Exception:
                            pass

            if self._Node_Info_Popup is not None:
                try:
                    self._Node_Info_Popup.close()
                except Exception:
                    pass
            self._Node_Info_Popup = None

            if self._Node_Info_Filter_Installed and App is not None:
                App.removeEventFilter(self)
                self._Node_Info_Filter_Installed = False

        def Show_Node_Info(self, Node_ID, Screen_Pos):
            print(f"[EoSHolo] Show_Node_Info called for node: {Node_ID}")
            Entry = next((E for E in self.Calibration_List if E['node_id'] == Node_ID), None)
            if not Entry:
                print(f"[EoSHolo] Show_Node_Info: node not found in Calibration_List: {Node_ID}")
                return

            self.Close_Node_Info_Popup(Close_All=True)

            def _Preview_Calibration_For_This_Node(File_Path):
                self.Close_Node_Info_Popup()
                Preview_Calibration_File_For_File_Path(self, File_Path)

            _, _, COLORS = Get_Theme()
            popup = Build_Node_Info_Popup(
                self,
                Entry,
                Get_Resource_Path,
                COLORS,
                on_preview_calibration=(lambda _checked=False, fp=_fp: _Preview_Calibration_For_This_Node(fp))
                    if (_fp := Entry.get("metadata", {}).get("file_path")) else None,
                on_chain_to_node=lambda _checked=False, nid=Node_ID: self.Focus_Chain_To_Node(nid),
                on_chains_through_node=lambda _checked=False, nid=Node_ID: self.Focus_Chains_Through_Node(nid),
            )
            self._Node_Info_Popup = popup
            popup.destroyed.connect(self._On_Node_Info_Popup_Destroyed)

            pos = Screen_Pos.toPoint() if hasattr(Screen_Pos, 'toPoint') else Screen_Pos
            host_geo = self.frameGeometry()
            max_x = host_geo.left() + max(0, host_geo.width() - popup.width())
            max_y = host_geo.top() + max(0, host_geo.height() - popup.height())
            x = min(max(pos.x(), host_geo.left()), max_x)
            y = min(max(pos.y(), host_geo.top()), max_y)
            print(f"[EoSHolo] Node info popup move-> ({x}, {y})")
            popup.move(x, y)
            popup.show()
            popup.raise_()
            print("[EoSHolo] Node info popup shown")

            if not self._Node_Info_Filter_Installed:
                QApplication.instance().installEventFilter(self)
                self._Node_Info_Filter_Installed = True

        def _On_Node_Info_Popup_Destroyed(self, *_):
            self._Node_Info_Popup = None
            if self._Node_Info_Filter_Installed and QApplication.instance() is not None:
                QApplication.instance().removeEventFilter(self)
                self._Node_Info_Filter_Installed = False

        def eventFilter(self, obj, event):
            if self._Node_Info_Popup is not None:
                Event_Type = event.type()

                # Close popup if any other top-level window appears.
                if Event_Type == QEvent.Show and hasattr(obj, "isWindow") and obj is not None:
                    if obj.isWindow() and not self._Is_Widget_Inside_Node_Info_Popup(obj):
                        self.Close_Node_Info_Popup()
                        return False

                # Close popup on outside pointer interactions.
                if Event_Type in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.Wheel):
                    gp = None
                    if hasattr(event, "globalPosition"):
                        gp = event.globalPosition().toPoint()
                    elif hasattr(event, "globalPos"):
                        gp = event.globalPos()

                    target = QApplication.widgetAt(gp) if gp is not None else None
                    if target is None and hasattr(obj, "isWindow") and obj is not None and obj.isWindow():
                        target = obj
                    if not self._Is_Widget_Inside_Node_Info_Popup(target):
                        self.Close_Node_Info_Popup()
                        return False
            return super().eventFilter(obj, event)

        def _Sync_Dropdowns_For_Node(self, Node_ID):
            Entry = next((E for E in self.Calibration_List if E['node_id'] == Node_ID), None)
            if not Entry:
                return

            self.Composition_Dropdown.blockSignals(True)
            self.Study_Dropdown.blockSignals(True)

            comp = Entry.get('composition', '')
            c_idx = self.Composition_Dropdown.findData(comp)
            if c_idx >= 0:
                self.Composition_Dropdown.setCurrentIndex(c_idx)

            studies = sorted(set(
                E['display_label'] for E in self.Calibration_List
                if E['composition'] == comp and E['has_calibration']
            ), key=self._Study_Display_Sort_Key)
            self.Study_Dropdown.clear()
            self.Study_Dropdown.addItems(studies)

            if Entry.get('has_calibration'):
                display_label = Entry.get('display_label', Entry.get('label', ''))
                s_idx = self.Study_Dropdown.findText(display_label)
                if s_idx >= 0:
                    self.Study_Dropdown.setCurrentIndex(s_idx)
                else:
                    self.Study_Dropdown.setCurrentIndex(-1)
            else:
                self.Study_Dropdown.setCurrentIndex(-1)

            self.Study_Dropdown.blockSignals(False)
            self.Composition_Dropdown.blockSignals(False)
            self.Update_Study_Dropdown_Footnote()
            self._Update_Preview_Calibration_Button_State()

        def _Get_Selected_Study_Entry(self):
            selected_comp = self._Get_Selected_Composition_Key()
            selected_label = self.Study_Dropdown.currentText()
            if not selected_comp or not selected_label:
                return None
            return next(
                (
                    E for E in self.Calibration_List
                    if (
                        E.get('display_label', E['label']) == selected_label
                        and E['composition'] == selected_comp
                        and E.get('has_calibration')
                    )
                ),
                None
            )

        def _Update_Preview_Calibration_Button_State(self):
            selected_entry = self._Get_Selected_Study_Entry()
            file_path = selected_entry.get('metadata', {}).get("file_path") if selected_entry else None
            has_file = bool(file_path and os.path.exists(file_path))
            self.Preview_Calibration_Button.setEnabled(has_file)
            if has_file:
                self.Preview_Calibration_Button.setToolTip(
                    f"Preview the calibration YAML file for {selected_entry.get('study', 'the selected study')}"
                )
            elif selected_entry:
                self.Preview_Calibration_Button.setToolTip("No YAML file path available for the selected study.")
            else:
                self.Preview_Calibration_Button.setToolTip("Select a study to preview its YAML file.")

        def On_Preview_Calibration_Clicked(self):
            selected_entry = self._Get_Selected_Study_Entry()
            file_path = selected_entry.get('metadata', {}).get("file_path") if selected_entry else None
            Preview_Calibration_File_For_File_Path(self, file_path)
            self._Update_Preview_Calibration_Button_State()

        def Focus_Chain_To_Node(self, Node_ID):
            print(f"[EoSHolo] Focus_Chain_To_Node -> {Node_ID}")
            self._Focus_Mode = "to_node"
            self._Focus_Node_ID = Node_ID
            self._Sync_Dropdowns_For_Node(Node_ID)

            self.Show_All_Checkbox.blockSignals(True)
            self.Show_All_Checkbox.setChecked(False)
            self.Show_All_Checkbox.blockSignals(False)
            self.Update_Graph()

        def Focus_Chains_Through_Node(self, Node_ID):
            print(f"[EoSHolo] Focus_Chains_Through_Node -> {Node_ID}")
            self._Focus_Mode = "through_node"
            self._Focus_Node_ID = Node_ID
            self._Sync_Dropdowns_For_Node(Node_ID)

            self.Show_All_Checkbox.blockSignals(True)
            self.Show_All_Checkbox.setChecked(False)
            self.Show_All_Checkbox.blockSignals(False)
            self.Update_Graph()

        def Get_Node_Connected_Subgraph(self, Node_ID):
            if not Node_ID:
                return set()

            Lookup = {E['node_id']: E for E in self.Calibration_List}
            Children = {}
            for E in self.Calibration_List:
                cid = E['node_id']
                for pid in E.get('parent_node_ids', []):
                    if pid:
                        Children.setdefault(pid, []).append(cid)

            connected = set()
            stack = [Node_ID]
            while stack:
                nid = stack.pop()
                if nid in connected:
                    continue
                connected.add(nid)

                entry = Lookup.get(nid)
                if entry:
                    for pid in entry.get('parent_node_ids', []):
                        if pid and pid not in connected:
                            stack.append(pid)

                for child_id in Children.get(nid, []):
                    if child_id not in connected:
                        stack.append(child_id)

            return connected

        def Get_Node_Chains_Through_Set(self, Node_ID):
            """
            Return nodes that belong to chains containing Node_ID:
            - all ancestors of Node_ID (including Node_ID)
            - all descendants of Node_ID
            """
            if not Node_ID:
                return set()

            lookup = {E['node_id']: E for E in self.Calibration_List}
            if Node_ID not in lookup:
                return set()

            # Ancestors (and Node_ID) from existing helper.
            ancestors = set(self.Get_Study_Chain(Node_ID))

            # Descendants via parent -> child map.
            children = {}
            for E in self.Calibration_List:
                cid = E['node_id']
                for pid in E.get('parent_node_ids', []):
                    if pid:
                        children.setdefault(pid, []).append(cid)

            descendants = set()
            stack = list(children.get(Node_ID, []))
            while stack:
                nid = stack.pop()
                if nid in descendants:
                    continue
                descendants.add(nid)
                stack.extend(children.get(nid, []))

            return ancestors.union(descendants)

        def Get_Node_Descendants(self, Node_ID):
            """Return all descendant node IDs of Node_ID (children, grandchildren, ...)."""
            if not Node_ID:
                return set()
            children = {}
            for E in self.Calibration_List:
                cid = E['node_id']
                for pid in E.get('parent_node_ids', []):
                    if pid:
                        children.setdefault(pid, []).append(cid)
            descendants = set()
            stack = list(children.get(Node_ID, []))
            while stack:
                nid = stack.pop()
                if nid in descendants:
                    continue
                descendants.add(nid)
                stack.extend(children.get(nid, []))
            return descendants


        # ── Graph structure helpers (unchanged logic) ───────────────────────────

        def Get_Study_Chain(self, Node_ID):
            """Return all ancestor node IDs of Node_ID (root first, selected node last)."""
            if not Node_ID:
                return []
            Lookup  = {E['node_id']: E for E in self.Calibration_List}
            Chain   = []
            Visited = set()

            def Traverse(NID):
                if NID in Visited:
                    return
                Visited.add(NID)
                E = Lookup.get(NID)
                if E and E['parent_node_ids']:
                    for PID in E['parent_node_ids']:
                        if PID:
                            Traverse(PID)
                Chain.append(NID)

            Traverse(Node_ID)
            return Chain

        def Get_Tree_Depths(self):
            Lookup = {E['node_id']: E for E in self.Calibration_List}
            Depths = {}

            def Compute(NID, Visited=None):
                if Visited is None:
                    Visited = set()
                if NID in Depths:
                    return Depths[NID]
                if NID in Visited:
                    return 0
                Visited.add(NID)
                E = Lookup.get(NID)
                if E and E.get('is_special'):
                    Depths[NID] = -1
                    return -1
                if not E or not E['parent_node_ids']:
                    D = 0
                else:
                    Valid = [PID for PID in E['parent_node_ids']
                             if not Lookup.get(PID, {}).get('is_special', False)]
                    if not Valid:
                        D = 0
                    else:
                        PDs = [D2 for D2 in [Compute(PID, Visited.copy()) for PID in Valid] if D2 >= 0]
                        D   = max(PDs) + 1 if PDs else 0
                Depths[NID] = D
                return D

            for E in self.Calibration_List:
                if not E.get('is_special'):
                    Compute(E['node_id'])
            return Depths


        # ── Graph rendering ────────────────────────────────────────────────────

        def Update_Graph(self, forced_viewport_size=None, auto_fit=True):
            Selected_Comp  = self._Get_Selected_Composition_Key()
            Selected_Label = self.Study_Dropdown.currentText()
            Show_All       = self.Show_All_Checkbox.isChecked()

            # Find the selected node entry
            Selected_Node = self._Get_Selected_Study_Entry() if (Selected_Label and Selected_Comp) else None

            Selected_Node_ID = Selected_Node['node_id'] if Selected_Node else None
            if self._Focus_Node_ID:
                Selected_Node_ID = self._Focus_Node_ID

            # Ancestor chain of the selected node (all connected ancestors + selected)
            if self._Focus_Mode == "through_node" and Selected_Node_ID:
                Chain = list(self.Get_Node_Chains_Through_Set(Selected_Node_ID))
            else:
                Chain = self.Get_Study_Chain(Selected_Node_ID) if Selected_Node_ID else []
            Chain_IDs = set(Chain)
            Through_Descendant_IDs = (
                self.Get_Node_Descendants(Selected_Node_ID)
                if (self._Focus_Mode == "through_node" and Selected_Node_ID)
                else set()
            )

            # Build ordered composition list — "Not Specified" always last
            All_Comps = sorted({E['composition'] for E in self.Calibration_List})
            Reg_Comps = [C for C in All_Comps if C != 'Not Specified']
            NS_Comp   = ['Not Specified'] if 'Not Specified' in All_Comps else []
            Elem_Order = Reg_Comps + NS_Comp

            Lookup       = {E['node_id']: E for E in self.Calibration_List}
            Elem_Groups  = {El: [] for El in Elem_Order}
            for E in self.Calibration_List:
                C = E['composition']
                if C in Elem_Groups:
                    Elem_Groups[C].append(E['node_id'])

            def _unique_node_ids(ids):
                seen = set()
                out = []
                for nid in ids:
                    if nid in seen:
                        continue
                    seen.add(nid)
                    out.append(nid)
                return out

            # Sort within each group: Primary → Regular (by depth) → Not Specified
            Depths = self.Get_Tree_Depths()

            def _sort_group(nodes):
                primary_ns, regular, not_spec = [], [], []
                for NID in nodes:
                    E = Lookup[NID]
                    if E.get('is_special'):
                        (primary_ns if E.get('special_type') == 'absolute' else not_spec).append(NID)
                    else:
                        regular.append(NID)
                regular.sort(key=lambda NID: Depths.get(NID, 0))
                return primary_ns + regular + not_spec

            for C in Elem_Groups:
                Elem_Groups[C] = _sort_group(_unique_node_ids(Elem_Groups[C]))

            # --- Live drawing dimensions from the current graph viewport ---
            if forced_viewport_size is not None:
                SW, SH = forced_viewport_size
            else:
                Viewport = self.Graph_View.viewport()
                SW = Viewport.width() if Viewport else 0
                SH = Viewport.height() if Viewport else 0
            if SW <= 0 or SH <= 0:
                return

            # Requested layout spacing:
            # - 3% horizontal edge padding
            # - 2% horizontal gap between composition columns
            # - 3% vertical edge padding
            Pad_H          = SH * 0.03
            Pad_W          = SW * 0.01
            Available_H    = SH - 2 * Pad_H
            Available_W    = SW - 2 * Pad_W
            H_Gap_Frac     = 0.01
            V_Gap_Frac     = 0.005
            Rect_Top       = Pad_H

            # --- Determine visible nodes ---
            Visible_IDs = set()
            if self._Focus_Mode == "through_node" and Selected_Node_ID:
                Visible_IDs = self.Get_Node_Chains_Through_Set(Selected_Node_ID)
            elif self._Focus_Mode == "to_node" and Selected_Node_ID:
                Visible_IDs = set(self.Get_Study_Chain(Selected_Node_ID))
            elif Show_All or not Selected_Node_ID:
                Visible_IDs = set(E['node_id'] for E in self.Calibration_List)
            else:
                def _collect_ancestors(NID):
                    Visible_IDs.add(NID)
                    E = Lookup.get(NID)
                    if E and E['parent_node_ids']:
                        for PID in E['parent_node_ids']:
                            if PID not in Visible_IDs:
                                _collect_ancestors(PID)
                _collect_ancestors(Selected_Node_ID)

            if self._Focus_Mode in ("to_node", "through_node"):
                print(
                    f"[EoSHolo] Focus mode={self._Focus_Mode}, selected={Selected_Node_ID}, "
                    f"visible_nodes={len(Visible_IDs)}"
                )

            # Track visible directed edges so reciprocal links can be treated as
            # parent-like chain nodes for styling decisions.
            Visible_Directed_Edge_Set = set()
            for E in self.Calibration_List:
                Child_ID = E['node_id']
                if Child_ID not in Visible_IDs:
                    continue
                for Parent_ID in E.get('parent_node_ids', []):
                    if Parent_ID and Parent_ID in Visible_IDs:
                        Visible_Directed_Edge_Set.add((Parent_ID, Child_ID))

            Reciprocal_Node_Pairs = set()
            for Parent_ID, Child_ID in Visible_Directed_Edge_Set:
                if Parent_ID != Child_ID and (Child_ID, Parent_ID) in Visible_Directed_Edge_Set:
                    pair = tuple(sorted((Parent_ID, Child_ID)))
                    Reciprocal_Node_Pairs.add(pair)
            Reciprocal_Display_Pairs = sorted(set(
                (
                    f"{Lookup[a]['study']} ({Lookup[a]['composition']})",
                    f"{Lookup[b]['study']} ({Lookup[b]['composition']})"
                ) if f"{Lookup[a]['study']} ({Lookup[a]['composition']})" <= f"{Lookup[b]['study']} ({Lookup[b]['composition']})"
                else
                (
                    f"{Lookup[b]['study']} ({Lookup[b]['composition']})",
                    f"{Lookup[a]['study']} ({Lookup[a]['composition']})"
                )
                for a, b in Reciprocal_Node_Pairs
            ))
            Reciprocal_Print_Signature = tuple(Reciprocal_Display_Pairs)
            if (
                Reciprocal_Display_Pairs
                and Reciprocal_Print_Signature not in self._Seen_Reciprocal_Print_Signatures
            ):
                # print("[EoSHolo] Reciprocal parent/child node pairs:")
                # for left, right in Reciprocal_Display_Pairs:
                #     print(f"  {left} <-> {right}")
                self._Seen_Reciprocal_Print_Signatures.add(Reciprocal_Print_Signature)

            Reciprocal_Chain_Node_IDs = set()
            if Chain_IDs:
                for Parent_ID, Child_ID in Visible_Directed_Edge_Set:
                    if (
                        Parent_ID != Child_ID
                        and
                        (Child_ID, Parent_ID) in Visible_Directed_Edge_Set
                        and Parent_ID in Chain_IDs
                        and Child_ID in Chain_IDs
                    ):
                        Reciprocal_Chain_Node_IDs.add(Parent_ID)
                        Reciprocal_Chain_Node_IDs.add(Child_ID)

            def _resolve_node_class(NID):
                E = Lookup[NID]
                if NID == Selected_Node_ID:
                    return 'selected'
                if E.get('is_special'):
                    return 'absolute' if E.get('special_type') == 'absolute' else 'not_specified'
                if NID in Chain_IDs and NID in Reciprocal_Chain_Node_IDs:
                    # Reciprocal parent<->child links should behave like parent
                    # chain nodes whenever they participate in the selected chain.
                    return 'chain'
                if self._Focus_Mode == "through_node" and NID in Through_Descendant_IDs:
                    return 'through_child'
                if not E.get('has_calibration'):
                    return 'missing'
                if NID in Chain_IDs:
                    return 'chain'
                return 'normal'

            # "View all nodes" mode uses explicit anchoring for special rows.
            Is_View_All_Mode = Show_All and self._Focus_Mode == "default"

            # Recompute depths for the visible subset when filtered
            if not Show_All and Selected_Node_ID:
                Vis_Lookup = {NID: E for NID, E in Lookup.items() if NID in Visible_IDs}
                Depths     = {}

                def _vis_depth(NID, Vis=None):
                    if Vis is None:
                        Vis = set()
                    if NID in Depths:
                        return Depths[NID]
                    if NID in Vis:
                        return 0
                    Vis.add(NID)
                    E = Vis_Lookup.get(NID)
                    if E and E.get('is_special'):
                        Depths[NID] = -1
                        return -1
                    if not E or not E['parent_node_ids']:
                        D = 0
                    else:
                        Valid = [PID for PID in E['parent_node_ids']
                                 if PID in Visible_IDs
                                 and not Vis_Lookup.get(PID, {}).get('is_special', False)]
                        PDs  = [D2 for D2 in [_vis_depth(PID, Vis.copy()) for PID in Valid] if D2 >= 0]
                        D    = max(PDs) + 1 if PDs else 0
                    Depths[NID] = D
                    return D

                for NID in Visible_IDs:
                    E = Vis_Lookup.get(NID)
                    if E and not E.get('is_special'):
                        _vis_depth(NID)

            # Re-sort groups with updated depths
            for C in Elem_Groups:
                Elem_Groups[C] = _sort_group(_unique_node_ids([
                    NID for NID in Elem_Groups[C] if NID in Visible_IDs
                ]))

            # Filter composition columns to only those with visible nodes
            Vis_Comps    = {Lookup[NID]['composition'] for NID in Visible_IDs}
            Filt_Order   = [El for El in Elem_Order if El in Vis_Comps]
            Num_Vis_Cols = len(Filt_Order)
            if Num_Vis_Cols > 0:
                Col_Gap_W           = SW * H_Gap_Frac
                Total_Inter_Col_Gap = Col_Gap_W * (Num_Vis_Cols - 1)
                Width_For_Cols      = max(Available_W - Total_Inter_Col_Gap, 0)
                Vis_Rect_W          = Width_For_Cols / Num_Vis_Cols if Num_Vis_Cols else 0
                Vis_Col_W           = Vis_Rect_W + Col_Gap_W
            else:
                Vis_Rect_W = Available_W
                Col_Gap_W  = 0
                Vis_Col_W  = Available_W

            # Wrap two-word labels onto two lines and size text from the longest
            # single word across all composition names (including non-visible),
            # capped at 20 pt.
            def _format_composition_label(label):
                words = (label or "").split()
                if len(words) == 2:
                    return f"{words[0]}\n{words[1]}"
                return label

            Label_Font = QFont('Noto Sans', 9, QFont.Bold)
            Max_Column_Label_Font_Size = 20.0
            Label_Names_For_Sizing = [Label for Label in Elem_Order if Label]
            if Label_Names_For_Sizing and Vis_Rect_W > 0:
                all_words = []
                for label in Label_Names_For_Sizing:
                    words = label.split()
                    if words:
                        all_words.extend(words)
                    else:
                        all_words.append(label)

                def _widest_word_width(point_size):
                    f = QFont('Noto Sans', 9, QFont.Bold)
                    f.setPointSizeF(point_size)
                    fm = QFontMetrics(f)
                    return max(fm.horizontalAdvance(word) for word in all_words)

                low, high = 1.0, Max_Column_Label_Font_Size
                target_w = Vis_Rect_W

                if _widest_word_width(high) <= target_w:
                    chosen_size = high
                elif _widest_word_width(low) >= target_w:
                    chosen_size = low
                else:
                    for _ in range(24):
                        mid = (low + high) / 2.0
                        if _widest_word_width(mid) <= target_w:
                            low = mid
                        else:
                            high = mid
                    chosen_size = low

                Label_Font.setPointSizeF(chosen_size)

            Visible_Labels = [_format_composition_label(Element) for Element in Filt_Order]
            Max_Label_Lines = max((Label.count('\n') + 1 for Label in Visible_Labels), default=1)
            Label_Height = max(26, (QFontMetrics(Label_Font).height() * Max_Label_Lines) + 6)

            # Always fill the full available height within top/bottom padding.
            Rect_H = Available_H

            # Node placement must stay inside the colored box area (below label band).
            Node_Area_Top = Rect_Top + Label_Height
            Node_Area_H   = max(0.0, Rect_H - Label_Height)

            # Keep nodes slightly inset from box edges so symbols/borders never
            # bleed into the label band or outside the colored box.
            Node_Inset = max(4.0, Node_Area_H * 0.005)
            Place_Area_Top = Node_Area_Top + Node_Inset
            Place_Area_H   = max(0.0, Node_Area_H - 2 * Node_Inset)

            Prim_Zone_H = Place_Area_H * 0.05
            Reg_Zone_H  = Place_Area_H * 0.90
            NS_Zone_H   = Place_Area_H * 0.05
            V_Gap_Size  = Place_Area_H * V_Gap_Frac

            # Adaptive shared sizing rules:
            # - column label max 20
            # - node label max 10 (scales with column label size)
            # - node max size 25 (scales with column label size)
            Max_Node_Label_Font_Size = 10.0
            Max_Node_Size = 25.0
            Column_Label_Scale = min(1.0, max(0.0, Label_Font.pointSizeF() / Max_Column_Label_Font_Size))
            Node_Label_Font_Size = max(1.0, min(Label_Font.pointSizeF(), Max_Node_Label_Font_Size))

            # Node size tracks column width (half width), but is clamped by
            # the shared scaled max and by vertical room so symbol+label fit.
            Node_Label_Font_For_Metrics = QFont('Noto Sans', 10)
            Node_Label_Font_For_Metrics.setPointSizeF(Node_Label_Font_Size)
            Node_Label_Pixel_Height = QFontMetrics(Node_Label_Font_For_Metrics).height()
            Max_Node_Size_By_Height = max(4.0, Node_Area_H - (40.0 + Node_Label_Pixel_Height))
            Node_Size = max(
                4.0,
                min(
                    Vis_Rect_W * 0.5,
                    Max_Node_Size * Column_Label_Scale,
                    Max_Node_Size_By_Height
                )
            )

            # --- Gather theme colours + central style maps ---
            COLORS = self._Get_Colors()
            Node_Styles = self._Get_Node_Styles(COLORS, fixed_node_size=Node_Size)
            Edge_Styles = self._Get_Edge_Styles(COLORS)

            # Per-composition placement bounds for keeping whole node+label inside
            # the colored box area (below composition label band).
            Col_Bounds = {}
            for E_Idx, Element in enumerate(Filt_Order):
                left  = Pad_W + E_Idx * Vis_Col_W
                right = left + Vis_Rect_W
                top   = Node_Area_Top
                bot   = Node_Area_Top + Node_Area_H
                Col_Bounds[Element] = (left, right, top, bot)

            # --- Compute node positions ---
            Pos = {}
            Visible_Node_Count = len(Visible_IDs)

            def _place_nodes(nodes, zone_top, zone_h, rect_x):
                n = len(nodes)
                if n == 0:
                    return
                if n == 1:
                    Pos[nodes[0]] = (rect_x, zone_top + zone_h / 2)
                    return
                total_gap  = V_Gap_Size * (n - 1)
                section_h  = (zone_h - total_gap) / n
                for i, NID in enumerate(nodes):
                    Pos[NID] = (rect_x, zone_top + i * (section_h + V_Gap_Size) + section_h / 2)

            # For smaller filtered sets, enforce one node per row across the
            # entire view (all composition columns combined), while preserving
            # Primary/Regular/Not Specified vertical zones.
            if 0 < Visible_Node_Count < 50:
                Col_Index = {Element: idx for idx, Element in enumerate(Filt_Order)}

                def _node_sort_key(nid):
                    E = Lookup[nid]
                    return (
                        Depths.get(nid, 0),
                        Col_Index.get(E['composition'], 10**6),
                        E.get('study', ''),
                        nid,
                    )

                def _order_regular_nodes(node_ids):
                    node_set = set(node_ids)
                    if not node_set:
                        return []

                    indegree = {nid: 0 for nid in node_set}
                    children = {nid: [] for nid in node_set}
                    for nid in node_set:
                        for pid in Lookup[nid].get('parent_node_ids', []):
                            if pid in node_set:
                                indegree[nid] += 1
                                children[pid].append(nid)

                    ready = sorted([nid for nid, d in indegree.items() if d == 0], key=_node_sort_key)
                    ordered = []
                    while ready:
                        nid = ready.pop(0)
                        ordered.append(nid)
                        for cid in children.get(nid, []):
                            indegree[cid] -= 1
                            if indegree[cid] == 0:
                                ready.append(cid)
                        ready.sort(key=_node_sort_key)

                    # Cycle safety fallback.
                    remaining = [nid for nid in node_set if nid not in ordered]
                    if remaining:
                        ordered.extend(sorted(remaining, key=_node_sort_key))
                    return ordered

                def _place_global_rows(ordered_nodes, zone_top, zone_h, edge_aligned=False):
                    n = len(ordered_nodes)
                    if n == 0:
                        return
                    if n == 1:
                        nid = ordered_nodes[0]
                        e_idx = Col_Index.get(Lookup[nid]['composition'], 0)
                        rect_x = Pad_W + e_idx * Vis_Col_W + Vis_Rect_W / 2
                        Pos[nid] = (rect_x, zone_top + zone_h / 2)
                        return

                    if edge_aligned:
                        step = (zone_h / (n - 1)) if n > 1 else 0.0
                        for i, nid in enumerate(ordered_nodes):
                            e_idx = Col_Index.get(Lookup[nid]['composition'], 0)
                            rect_x = Pad_W + e_idx * Vis_Col_W + Vis_Rect_W / 2
                            y = zone_top + i * step
                            Pos[nid] = (rect_x, y)
                        return

                    gap = V_Gap_Size
                    total_gap = gap * (n - 1)
                    if total_gap >= zone_h:
                        gap = 0.0
                        section_h = zone_h / n if n else 0.0
                    else:
                        section_h = (zone_h - total_gap) / n

                    for i, nid in enumerate(ordered_nodes):
                        e_idx = Col_Index.get(Lookup[nid]['composition'], 0)
                        rect_x = Pad_W + e_idx * Vis_Col_W + Vis_Rect_W / 2
                        y = zone_top + i * (section_h + gap) + section_h / 2
                        Pos[nid] = (rect_x, y)

                def _node_len_for_spacing(nid):
                    if nid == Selected_Node_ID:
                        return max(1.0, Node_Styles['selected']['radius'] * 2.0)
                    return max(1.0, Node_Styles['normal']['radius'] * 2.0)

                def _pair_gap(prev_nid, cur_nid, base_min_step):
                    # Enforce at least requested 1.5 node heights, and expand
                    # spacing for larger rendered nodes (e.g., selected).
                    return max(base_min_step, 1.5 * max(_node_len_for_spacing(prev_nid), _node_len_for_spacing(cur_nid)))

                def _node_class_and_label_for_layout(nid):
                    e = Lookup[nid]
                    _meta = e.get('metadata', {})
                    _is_user = _meta.get('is_user_edited', False) or _meta.get('is_user_entered', False)
                    study = ("* " if _is_user else "") + e['study']
                    node_class = _resolve_node_class(nid)
                    if e.get('is_special') and e.get('special_type') == 'absolute':
                        return node_class, f"{study} (Absolute)"
                    return node_class, study

                def _node_y_limits(nid):
                    comp = Lookup[nid]['composition']
                    bounds = Col_Bounds.get(comp)
                    if not bounds:
                        return (Place_Area_Top, Place_Area_Top + Place_Area_H)
                    _, _, top, bot = bounds
                    node_class, label = _node_class_and_label_for_layout(nid)
                    route_role = Lookup[nid].get('special_type') if Lookup[nid].get('is_special') else None
                    temp_item = NodeItem(
                        nid, node_class, Node_Styles[node_class], label, COLORS,
                        route_role=route_role, is_user_moved=False,
                        label_font_size=Node_Label_Font_Size
                    )
                    br = temp_item.boundingRect()
                    min_y = top - br.top()
                    max_y = bot - br.bottom()
                    if min_y > max_y:
                        mid = (min_y + max_y) / 2.0
                        return (mid, mid)
                    return (min_y, max_y)

                def _respread_column_nodes(node_ids, min_step, y_min, y_max):
                    # Second pass: preserve row-first ordering, while pinning
                    # primaries to the top and not-specified nodes to the bottom.
                    ordered = [nid for nid in sorted(node_ids, key=lambda nid: Pos[nid][1]) if nid in Pos]
                    if len(ordered) < 2:
                        return

                    primary = []
                    ns = []
                    middle = []
                    for nid in ordered:
                        e = Lookup.get(nid, {})
                        if e.get('is_special') and e.get('special_type') == 'absolute':
                            primary.append(nid)
                        elif e.get('is_special') and e.get('special_type') == 'not_specified':
                            ns.append(nid)
                        else:
                            middle.append(nid)

                    fixed = {}
                    # Pin primary nodes at the top (stacked if more than one).
                    for idx, nid in enumerate(primary):
                        nmin, nmax = _node_y_limits(nid)
                        anchor = y_min + idx * min_step
                        fixed[nid] = min(max(anchor, nmin), nmax)
                    # Pin not-specified nodes at the bottom (stacked upward).
                    n_ns = len(ns)
                    for idx, nid in enumerate(ns):
                        nmin, nmax = _node_y_limits(nid)
                        anchor = y_max - (n_ns - 1 - idx) * min_step
                        fixed[nid] = min(max(anchor, nmin), nmax)

                    # Keep the original global-row order as desired order.
                    sequence = ordered
                    desired = {}
                    for nid in sequence:
                        nmin, nmax = _node_y_limits(nid)
                        base_y = fixed.get(nid, Pos[nid][1])
                        desired[nid] = min(max(base_y, nmin), nmax)
                    y = {nid: desired[nid] for nid in sequence}

                    # Forward pass
                    for i, nid in enumerate(sequence):
                        if nid in fixed:
                            y[nid] = fixed[nid]
                            continue
                        if i > 0:
                            prev = sequence[i - 1]
                            gap = _pair_gap(prev, nid, min_step)
                            nmin, nmax = _node_y_limits(nid)
                            cand = max(y[nid], y[prev] + gap)
                            y[nid] = min(max(cand, nmin), nmax)

                    # Backward pass
                    for i in range(len(sequence) - 1, -1, -1):
                        nid = sequence[i]
                        if nid in fixed:
                            y[nid] = fixed[nid]
                            continue
                        if i < len(sequence) - 1:
                            nxt = sequence[i + 1]
                            gap = _pair_gap(nid, nxt, min_step)
                            nmin, nmax = _node_y_limits(nid)
                            cand = min(y[nid], y[nxt] - gap)
                            y[nid] = min(max(cand, nmin), nmax)

                    for nid in sequence:
                        x, _ = Pos[nid]
                        Pos[nid] = (x, y[nid])

                primary_nodes = []
                regular_nodes = []
                ns_nodes = []
                for Element in Filt_Order:
                    for NID in Elem_Groups.get(Element, []):
                        if NID not in Visible_IDs:
                            continue
                        E = Lookup[NID]
                        if E.get('is_special') and E.get('special_type') == 'absolute':
                            primary_nodes.append(NID)
                        elif E.get('is_special') and E.get('special_type') == 'not_specified':
                            ns_nodes.append(NID)
                        else:
                            regular_nodes.append(NID)

                primary_order = sorted(primary_nodes, key=_node_sort_key)
                regular_order = _order_regular_nodes(regular_nodes)
                ns_order = sorted(ns_nodes, key=_node_sort_key)

                # Apply global rows across ALL visible nodes (<50 path), not by
                # zone, so every node class participates in the same row system.
                all_order = primary_order + regular_order + ns_order
                # Edge-aligned rows keep primaries at the very top and
                # not-specified nodes at the very bottom.
                _place_global_rows(all_order, Place_Area_Top, Place_Area_H, edge_aligned=True)

                # Post-pass: after row assignment, spread same-column nodes
                # by at least 1.5 node lengths vertically.
                min_same_col_step = 1.5 * max(1.0, Node_Styles['normal']['radius'] * 2.0)
                y_min = Place_Area_Top
                y_max = Place_Area_Top + Place_Area_H
                for Element in Filt_Order:
                    Col_Nodes = [nid for nid in Elem_Groups.get(Element, []) if nid in Visible_IDs and nid in Pos]
                    if len(Col_Nodes) > 1:
                        _respread_column_nodes(Col_Nodes, min_same_col_step, y_min, y_max)
            else:
                for E_Idx, Element in enumerate(Filt_Order):
                    Nodes_In = Elem_Groups.get(Element, [])
                    Rect_X   = Pad_W + E_Idx * Vis_Col_W + Vis_Rect_W / 2

                    Primary_Ns = [NID for NID in Nodes_In if Lookup[NID].get('is_special') and Lookup[NID].get('special_type') == 'absolute']
                    Regular_Ns = [NID for NID in Nodes_In if not Lookup[NID].get('is_special')]
                    NS_Nodes   = [NID for NID in Nodes_In if Lookup[NID].get('is_special') and Lookup[NID].get('special_type') == 'not_specified']

                    _place_nodes(Primary_Ns, Place_Area_Top,                            Prim_Zone_H, Rect_X)
                    _place_nodes(Regular_Ns, Place_Area_Top + Prim_Zone_H,              Reg_Zone_H,  Rect_X)
                    _place_nodes(NS_Nodes,   Place_Area_Top + Prim_Zone_H + Reg_Zone_H, NS_Zone_H,   Rect_X)

            # --- Build scene items ---
            BG_Items   = []
            Node_Items = []
            Edge_Items = []

            # Background rectangles
            BG_Y = Rect_Top + Rect_H / 2
            for E_Idx, Element in enumerate(Filt_Order):
                BG_X = Pad_W + E_Idx * Vis_Col_W + Vis_Rect_W / 2
                BG_Items.append(BackgroundItem(
                    BG_X, BG_Y, Vis_Rect_W, Rect_H, _format_composition_label(Element), COLORS,
                    label_font=Label_Font, label_height=Label_Height
                ))

            # Node items
            Node_Map   = {}
            Added_NIDs = set()

            for Element in Filt_Order:
                for NID in Elem_Groups.get(Element, []):
                    if NID in Visible_IDs and NID not in Added_NIDs and NID in Pos:
                        E     = Lookup[NID]
                        Study = E['study']
                        Node_Class = _resolve_node_class(NID)
                        if E.get('is_special') and E.get('special_type') == 'absolute':
                            Label = f"{Study} (Absolute)"
                        else:
                            Label = Study

                        route_role = E.get('special_type') if E.get('is_special') else None
                        manual_pos = self._Manual_Node_Positions.get(NID)
                        item = NodeItem(
                            NID, Node_Class, Node_Styles[Node_Class], Label, COLORS,
                            route_role=route_role, is_user_moved=(manual_pos is not None),
                            label_font_size=Node_Label_Font_Size
                        )
                        if manual_pos is not None:
                            # Preserve the user's dragged y-position, but always
                            # recompute x from the current column layout so the node
                            # stays inside its correct composition column even when
                            # the number of visible columns changes.
                            _, y = manual_pos
                            comp   = Lookup[NID]['composition']
                            bounds = Col_Bounds.get(comp)
                            if bounds:
                                left, right, top, bot = bounds
                                br = item.boundingRect()
                                node_w = max(1.0, item._r * 2.0)
                                col_w = max(0.0, right - left)
                                x = (left + right) / 2
                                if col_w > (3.0 * node_w):
                                    mid_left = left + 0.15 * col_w
                                    mid_right = right - 0.15 * col_w
                                    if mid_right > mid_left:
                                        u = Stable_Unit_Float(f"{NID}|{comp}")
                                        x = mid_left + u * (mid_right - mid_left)
                                min_x = left - br.left()
                                max_x = right - br.right()
                                min_y = top - br.top()
                                max_y = bot - br.bottom()
                                if min_x <= max_x:
                                    x = min(max(x, min_x), max_x)
                                if min_y <= max_y:
                                    y = min(max(y, min_y), max_y)
                            else:
                                x, _ = Pos[NID]
                        else:
                            x, y = Pos[NID]
                            comp   = Lookup[NID]['composition']
                            bounds = Col_Bounds.get(comp)
                            if bounds:
                                left, right, top, bot = bounds
                                br = item.boundingRect()

                                # If the composition column is wide relative to the node,
                                # place x in the middle 70% (stable-random per node).
                                node_w = max(1.0, item._r * 2.0)
                                col_w = max(0.0, right - left)
                                if col_w > (3.0 * node_w):
                                    mid_left = left + 0.15 * col_w
                                    mid_right = right - 0.15 * col_w
                                    if mid_right > mid_left:
                                        u = Stable_Unit_Float(f"{NID}|{comp}")
                                        x = mid_left + u * (mid_right - mid_left)

                                min_x = left - br.left()
                                max_x = right - br.right()
                                min_y = top - br.top()
                                max_y = bot - br.bottom()
                                if min_x <= max_x:
                                    x = min(max(x, min_x), max_x)
                                if min_y <= max_y:
                                    y = min(max(y, min_y), max_y)

                            if Is_View_All_Mode and Visible_Node_Count >= 50:
                                symbol_edge_pad = 2.0
                                if Node_Class == 'absolute':
                                    y = Node_Area_Top + item._r + symbol_edge_pad
                                elif Node_Class == 'not_specified':
                                    # Keep the symbol near the composition-box bottom, but
                                    # ensure the label stays just above the window bottom.
                                    node_area_bottom = Node_Area_Top + Node_Area_H
                                    desired_y = node_area_bottom - item._r - symbol_edge_pad
                                    label_bottom_pad = 8.0
                                    # label_bottom_local = r + 8 + (label_h + 2*4)
                                    label_bottom_local = item._r + 16 + item._lbl_h
                                    max_y_for_label = SH - label_bottom_pad - label_bottom_local
                                    y = min(desired_y, max_y_for_label)

                        item.setPos(x, y)
                        Node_Items.append(item)
                        Node_Map[NID] = item
                        Added_NIDs.add(NID)

            # Edge items
            Directed_Edges = []
            Directed_Edge_Set = set()
            for E in self.Calibration_List:
                NID = E['node_id']
                if NID not in Visible_IDs:
                    continue
                for PID in E['parent_node_ids']:
                    if PID not in Visible_IDs:
                        continue
                    if PID not in Node_Map or NID not in Node_Map:
                        continue
                    Edge_Key = (PID, NID)
                    if Edge_Key in Directed_Edge_Set:
                        continue
                    Directed_Edges.append(Edge_Key)
                    Directed_Edge_Set.add(Edge_Key)

            Added_Edges = set()
            for PID, NID in Directed_Edges:
                if (PID, NID) in Added_Edges:
                    continue
                Reverse_Edge = (NID, PID)
                Is_Bidirectional = (PID != NID) and (Reverse_Edge in Directed_Edge_Set)

                Is_Chain_Edge = (
                    Selected_Node_ID and
                    (NID == Selected_Node_ID or NID in Chain_IDs) and
                    (PID == Selected_Node_ID or PID in Chain_IDs)
                )
                E_Class = 'chain' if Is_Chain_Edge else 'normal'
                E_Style = Edge_Styles[E_Class]

                Edge_Items.append(EdgeItem(
                    Node_Map[PID], Node_Map[NID],
                    E_Style['color'], E_Style['width'], E_Style['z'],
                    source_gap=Edge_Styles['source_gap'],
                    target_gap=Edge_Styles['target_gap'],
                    bidirectional=Is_Bidirectional
                ))
                Added_Edges.add((PID, NID))
                if Is_Bidirectional:
                    Added_Edges.add(Reverse_Edge)

            self.Graph_View.build(BG_Items, Node_Items, Edge_Items, QRectF(0, 0, SW, SH), auto_fit=auto_fit)


        def _Estimate_Initial_Graph_Viewport_Size(self):
            Window_Geometry = self.geometry()
            Window_W = max(1, Window_Geometry.width())
            Window_H = max(1, Window_Geometry.height())

            Menu_H = self.menuBar().sizeHint().height() if self.menuBar() is not None else 0
            Banner_H = self.Banner.height() if hasattr(self, "Banner") else 0
            Controls_H = (
                self.Controls_Widget.sizeHint().height()
                if hasattr(self, "Controls_Widget") and self.Controls_Widget is not None
                else 0
            )

            Graph_W = max(1, Window_W)
            Graph_H = max(1, Window_H - Menu_H - Banner_H - Controls_H)
            return Graph_W, Graph_H

        def Bootstrap_Initial_Graph_No_Show(self):
            if self._Initial_Graph_Drawn:
                return
            SW, SH = self._Estimate_Initial_Graph_Viewport_Size()
            self.Update_Graph(forced_viewport_size=(SW, SH), auto_fit=False)
            self._Initial_Graph_Drawn = True


        # ── Resize handling ────────────────────────────────────────────────────

        def Draw_Initial_Graph_If_Ready(self):
            if self._Initial_Graph_Drawn:
                return True
            viewport = self.Graph_View.viewport() if hasattr(self, "Graph_View") else None
            if viewport and viewport.width() > 0 and viewport.height() > 0:
                self.Update_Graph()
            else:
                SW, SH = self._Estimate_Initial_Graph_Viewport_Size()
                if SW <= 0 or SH <= 0:
                    return False
                self.Update_Graph(forced_viewport_size=(SW, SH), auto_fit=False)
            self._Initial_Graph_Drawn = True
            return True

        def Reveal_Initial_Graph(self, refit=True):
            if self._Initial_Graph_Revealed:
                return
            # Prevent a queued startup resize debounce from triggering a visible reflow
            # right after first paint.
            self.Resize_Timer.stop()
            if refit:
                # Let layout settle with the graph view visible, then rebuild/freeze fit once.
                QApplication.instance().processEvents()
                self.Update_Graph()
                self.Graph_View.reset_zoom()
            self._Initial_Graph_Revealed = True

        def showEvent(self, Event):
            super().showEvent(Event)
            self.Draw_Initial_Graph_If_Ready()
            if not self._Initial_Graph_Revealed:
                self.Reveal_Initial_Graph(refit=True)
            # Re-assert autoFillBackground=False after Qt's Polish event may have
            # re-enabled it via the stylesheet background rule on the GraphView.
            if hasattr(self, "Graph_View") and self.Graph_View is not None:
                self.Graph_View.viewport().setAutoFillBackground(False)

        def resizeEvent(self, Event):
            super().resizeEvent(Event)
            self.Close_Node_Info_Popup()
            if not self._Initial_Graph_Drawn:
                self.Draw_Initial_Graph_If_Ready()
            if not self._Initial_Graph_Revealed:
                return
            if hasattr(self, "Graph_View") and self.Graph_View is not None:
                self.Graph_View.fill_to_viewport()
            self.Resize_Timer.stop()
            self.Resize_Timer.start(150)

        def On_Resize_Complete(self):
            if not self._Initial_Graph_Drawn and not self.Draw_Initial_Graph_If_Ready():
                return
            # Recompute layout from the new viewport size.
            Viewport = self.Graph_View.viewport() if hasattr(self, "Graph_View") else None
            if Viewport and Viewport.width() > 0 and Viewport.height() > 0:
                self.Update_Graph(forced_viewport_size=(Viewport.width(), Viewport.height()))
            else:
                self.Update_Graph()


        def changeEvent(self, event):
            from PySide6.QtCore import QEvent
            super().changeEvent(event)
            if (event.type() == QEvent.WindowStateChange
                    and self._Initial_Graph_Revealed
                    and (self.isMaximized() or self.isFullScreen())):
                # Rebuild synchronously so the scene is complete before the event
                # loop processes any paint events queued by the resizeEvent above.
                # No intermediate scaled/blank state is ever composited.
                self.Resize_Timer.stop()
                self.On_Resize_Complete()


        # ── Theme change ───────────────────────────────────────────────────────

        def On_Theme_Changed(self):
            from Themes.Theme import Load_Application_Style_Sheet
            _, QSS, COLORS = Load_Application_Style_Sheet(Get_Resource_Path)
            QApplication.instance().setStyleSheet(QSS)

            # Re-apply EoSHolo stylesheet and redraw with new colours
            self.Apply_EoSHolo_Stylesheet(self.centralWidget())
            if hasattr(self, 'Graph_View') and self.Graph_View is not None:
                _bg = QBrush(QColor(COLORS.get('Primary_Background')))
                self.Graph_View.setBackgroundBrush(_bg)
                self.Graph_View._scene.setBackgroundBrush(_bg)
                _vp = self.Graph_View.viewport()
                _vp_pal = _vp.palette()
                _bg_color = QColor(COLORS.get('Primary_Background'))
                _vp_pal.setColor(QPalette.All, QPalette.Base, _bg_color)
                _vp_pal.setColor(QPalette.All, QPalette.Window, _bg_color)
                _vp.setPalette(_vp_pal)
                _vp.setAutoFillBackground(False)
            self.Update_Graph()


    return EoSHolo




# Allow other files to import EoSHolo as a class
def EoSHolo():
    Cls = Build_EoSHolo_Window()
    return Cls()




# Start EoSHolo
def main():

    Register_Installed_Application_And_Exit_If_Requested("EoSHolo")

    # Use sys.executable when frozen so os.chdir() targets the .exe folder, not
    # the PyInstaller temp extraction folder (sys._MEIPASS).  Pointing CWD at
    # sys._MEIPASS prevents Windows from deleting the temp folder on exit.
    if getattr(sys, 'frozen', False):
        project_dir = os.path.dirname(sys.executable)
    else:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    # Load libraries
        # Load third party libraries
    from PySide6.QtWidgets import QApplication, QWidget, QSplashScreen
    from PySide6.QtCore import QTimer, QObject, QEvent
    from PySide6.QtGui import QIcon
        # Load local functions from local files
    from Loading_Message import Create_Loading_Message, Update_Loading_Message, Load_Fonts
    from Mac_Terminal_Commands import Prompt_To_Install_Mac_Terminal_Commands_If_Needed
    from Shadow_Filter import Install_Shadow_Filter

    App = QApplication(sys.argv)
    App.setWindowIcon(QIcon(Get_Resource_Path("Graphics/EoS_With_Sun.png")))
    # Force the Fusion style so the stylesheet (border-radius, fonts, dropdown
    # sizing) is fully obeyed on every OS instead of native widget painting
    # taking over (macOS's native style ignores much of the QSS below).
    App.setStyle("Fusion")

    class Startup_Window_Guard(QObject):
        """
        Suppress unexpected top-level windows during startup.
        Allows only the loading splash and the main app window.
        """
        def __init__(self):
            super().__init__()
            self.Allowed_Window_IDs = set()
            self.Enabled = True

        def allow(self, widget):
            if widget is not None:
                self.Allowed_Window_IDs.add(id(widget))

        def disable(self):
            self.Enabled = False

        def eventFilter(self, obj, event):
            if not self.Enabled:
                return False
            if event.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
                if id(obj) in self.Allowed_Window_IDs:
                    return False
                if isinstance(obj, QSplashScreen):
                    return False
                # Keep transient startup windows off-screen, but do not suppress
                # the show event (some Qt internals rely on normal show lifecycle).
                obj.move(-32000, -32000)
                return False
            return False

    Startup_Window_Guard_Filter = Startup_Window_Guard()
    App.installEventFilter(Startup_Window_Guard_Filter)

    Load_Fonts(App)
    Install_Shadow_Filter(App)

    Loading_Screen = Create_Loading_Message(App, Logo_Path="Graphics/EoSHolo_With_Sun.png")
    Startup_Window_Guard_Filter.allow(Loading_Screen)
    Timer = {"Started Loading the Application": time.perf_counter(), "Last Loading Message": time.perf_counter()}

    Update_Loading_Message(Loading_Screen, App, "Loading libraries...", Timer)
    import darkdetect

    Update_Loading_Message(Loading_Screen, App, "Loading calibrations...", Timer)
    import EoS_Math.Build_Dataframe

    Update_Loading_Message(Loading_Screen, App, "Loading style sheet...", Timer)
    from Themes.Theme import Load_Application_Style_Sheet
    Theme_Name, QSS, COLORS = Load_Application_Style_Sheet(Get_Resource_Path)

    Update_Loading_Message(Loading_Screen, App, "Applying style sheet...", Timer)
    App.setStyleSheet(QSS)
    # Set the app-level palette background so the DWM uses the theme color when
    # animating the window during maximize/restore (stylesheet alone does not
    # reach the Win32 background-brush that DWM reads for that animation).
    from PySide6.QtGui import QPalette, QColor
    App_Palette = App.palette()
    App_Background_Color = COLORS.get('Primary_Background', '#1a1a2e')
    App_Palette.setColor(QPalette.Window,     QColor(App_Background_Color))
    App_Palette.setColor(QPalette.Base,       QColor(App_Background_Color))
    App_Palette.setColor(QPalette.AlternateBase, QColor(App_Background_Color))
    App.setPalette(App_Palette)

    Update_Loading_Message(Loading_Screen, App, "Building window...", Timer)
    EoSHolo_Window_Class = Build_EoSHolo_Window()
    Window = EoSHolo_Window_Class()
    Startup_Window_Guard_Filter.allow(Window)

    # Build the initial graph before first show so startup has no warm-up window flash.
    def On_Ready():
        from Check_For_Updates import Check_For_Updates_On_Startup
        Window.Bootstrap_Initial_Graph_No_Show()
        # Show off-screen first so any transient native frame is never visible.
        final_pos = Window.pos()
        Window.move(-32000, -32000)
        # Keep the window fully transparent while Qt composes the first frame.
        # This prevents any transient native white frame from being visible.
        Window.setWindowOpacity(0.0)
        Window.show()
        Window.raise_()
        Window.activateWindow()
        App.processEvents()
        # Tell Windows to render the non-client area (title bar, borders) in dark
        # mode so the window chrome never flashes white during the maximize animation.
        try:
            import ctypes
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                int(Window.winId()),
                20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
                ctypes.byref(ctypes.c_int(1)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass
        # Move into place only after the native window has been realized.
        Window.move(final_pos)
        App.processEvents()
        Window.Reveal_Initial_Graph(refit=False)
        Window.repaint()
        App.processEvents()
        Window.setWindowOpacity(1.0)
        App.processEvents()
        Loading_Screen.finish(Window)
        Startup_Window_Guard_Filter.disable()
        App.removeEventFilter(Startup_Window_Guard_Filter)
        QTimer.singleShot(0, lambda: Prompt_To_Install_Mac_Terminal_Commands_If_Needed(Window, "EoSHolo"))
        Check_For_Updates_On_Startup(Window, "EoSHolo")
        from Check_For_Calibration_Updates import Check_For_Calibration_Updates_On_Startup
        Check_For_Calibration_Updates_On_Startup(Window)

    # QGraphicsView renders synchronously — schedule the reveal on the next event loop tick
    QTimer.singleShot(0, On_Ready)

    print(f"")
    print(f"Total loading time: {(time.perf_counter() - Timer['Started Loading the Application']):.4f} seconds")
    print(f"")

    sys.exit(App.exec())


if __name__ == "__main__":
    main()
