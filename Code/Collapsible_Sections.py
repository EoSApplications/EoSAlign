# Load libraries
    # Load standard libraries
import html as html_lib
    # Load third party libraries
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QStyleOptionComboBox, QApplication, QStyle, QCheckBox, QGraphicsDropShadowEffect, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QTextDocument
    # Load local functions from local files
from Themes.Theme import DEFAULT_MINIMUM_CONTENT_WIDTH, Get_Theme


ANIMATION_DURATION = 200  # ms

# Custom item-data role used to flag dropdown options that are user-edited or user-entered.
# When set, the popup renders a non-selectable caution line under that option's text.
IS_USER_CALIBRANT_ROLE = Qt.UserRole + 100


# Build the HTML used to render a dropdown option, optionally appending a caution
# line below it. Both the leading "* " on the option's own line and the caution
# sub-line use Caution_Color (Caution_Text normally, Caution_Text_Accent while hovered/selected).
def Build_Dropdown_Item_Html(Display_Text, Is_User_Calibrant, Normal_Color, Caution_Color):
    Html_Lines = []
    # First line: the option text itself. Only its leading "* " gets the caution color.
    if Display_Text.startswith("* "):
        Html_Lines.append(f'<span style="color:{Caution_Color};">*</span>{html_lib.escape(Display_Text[1:])}')
    else:
        Html_Lines.append(html_lib.escape(Display_Text))
    # Caution sub-line: the entire line is caution-colored and rendered smaller,
    # matching the footnote style used under the comparison checkboxes.
    if Is_User_Calibrant:
        Html_Lines.append(
            f'<span style="color:{Caution_Color}; font-size:8pt;">'
            f'{html_lib.escape("* indicates user edited or entered calibrant")}</span>'
        )
    Body = "<br>".join(Html_Lines)
    return f'<span style="color:{Normal_Color};">{Body}</span>'




# Item delegate that renders combobox popup items with pre-formatted multi-line text
    # Text is pre-broken with \n before being added to the model; this delegate
    # provides the correct row height and paints the wrapped lines properly
class WordWrapDelegate(QStyledItemDelegate):

    def __init__(self, view, combo_box=None):
        super().__init__(view)
        # Storing the combo box lets sizeHint use its current pixel width,
        # which equals the popup width and is available before the popup opens.
        self.Combo_Box = combo_box
        # QListView defaults to uniform item sizes for performance, which queries
        # sizeHint() for only a sample row and reuses that height for every row.
        # Rows that need an extra caution line would then get clipped to whatever
        # height the sampled (possibly shorter, unflagged) row reported. Disable
        # it so every row's wrapped/multi-line height is measured individually.
        if view is not None:
            view.setUniformItemSizes(False)
            # Defensive: never let the view elide our manually-wrapped text with "…".
            view.setTextElideMode(Qt.TextElideMode.ElideNone)

    def sizeHint(self, option, index):
        text = index.data() or ""
        Is_User_Calibrant = bool(index.data(IS_USER_CALIBRANT_ROLE))
        # Priority: combo_box.width() → viewport.width() → option.rect → fallback.
        # combo_box.width() is reliable even before the popup has ever been shown;
        # view.viewport().width() is NOT — it can report a small placeholder size
        # at that point, which previously caused massive over-wrapping (and rows so
        # tall only one was visible at a time). It's kept only as a later fallback.
        if self.Combo_Box is not None and self.Combo_Box.width() > 0:
            available_width = self.Combo_Box.width()
        else:
            view = self.parent()
            vp = view.viewport() if view is not None else None
            if vp is not None and vp.width() > 0:
                available_width = vp.width()
            elif option.rect.width() > 0:
                available_width = option.rect.width()
            else:
                available_width = 400
        # The QSS rules use margin: 4px 8px and padding: 8px 16px.
        # Horizontal inset for text = margin(8+8) + padding(16+16) = 48px.
        # Vertical extra needed  = margin(4+4) + padding(8+8)     = 24px.
        # Computing bounding with the correct text width ensures the wrapped
        # height matches what the style engine actually renders.
        # An extra safety margin absorbs the popup's vertical scrollbar (which
        # narrows the real row width paint() gets below the closed box's width)
        # without the wild over-wrapping that came from trusting viewport().width().
        Scrollbar_Safety_Margin = 20
        text_width = max(1, available_width - 48 - Scrollbar_Safety_Margin)
        Html = Build_Dropdown_Item_Html(text, Is_User_Calibrant, "#000000", "#000000")
        Document = QTextDocument()
        Document.setDefaultFont(option.font)
        Document.setHtml(Html)
        Document.setTextWidth(text_width)
        return QSize(available_width, int(Document.size().height()) + 24)

    def paint(self, painter, option, index):
        painter.save()

        # Initialise the full style option (palette, font, state, etc.)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # Let the style engine draw the background / selection highlight
        # without text (we redraw text ourselves so it renders all lines)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        # Draw all lines top-aligned using the correct foreground colour.
        # Non-caution text uses palette text/highlightedText depending on hover state.
        # A leading "* " (and the caution sub-line) use Caution_Text normally, switching
        # to Caution_Text_Accent while hovered so they stay legible against the highlight
        # background. Only State_MouseOver counts as "active" here — State_Selected stays
        # true for the current item even after the mouse moves away, but the QSS only
        # paints a highlighted background on :hover, so text must not switch on that alone.
        text = index.data() or ""
        Is_User_Calibrant = bool(index.data(IS_USER_CALIBRANT_ROLE))
        _active = QStyle.StateFlag.State_MouseOver
        _, _, Theme_Colors = Get_Theme()
        if opt.state & _active:
            Normal_Color = opt.palette.highlightedText().color().name()
            Caution_Color = Theme_Colors.get("Caution_Text_Accent")
        else:
            Normal_Color = opt.palette.text().color().name()
            Caution_Color = Theme_Colors.get("Caution_Text")

        Html = Build_Dropdown_Item_Html(text, Is_User_Calibrant, Normal_Color, Caution_Color)
        Document = QTextDocument()
        Document.setDefaultFont(opt.font)
        Document.setHtml(Html)
        # Offset matches the QSS layout: margin(8,4) + padding(16,8) = (24,12) each side.
        text_rect = option.rect.adjusted(24, 12, -24, -12)
        Document.setTextWidth(text_rect.width())

        painter.translate(text_rect.topLeft())
        Document.drawContents(painter, QRect(0, 0, text_rect.width(), text_rect.height()))

        painter.restore()




# QPushButton whose label wraps across multiple lines
    # A QLabel (with word-wrap enabled) is laid out inside the button so that
    # the button height grows to fit the text.  The label is transparent to
    # mouse events so clicks still reach the button correctly.
class WordWrapPushButton(QPushButton):

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.Full_Text = text
        self.Label = QLabel(text, self)
        self.Label.setWordWrap(True)
        self.Label.setAlignment(Qt.AlignCenter)
        self.Label.setAttribute(Qt.WA_TransparentForMouseEvents)
        # Do NOT set an inline stylesheet on the label — doing so creates a
        # per-widget QSS context that prevents external rules such as
        # QPushButton#ModeButton QLabel { color: ... } from being applied.
        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(6, 6, 6, 6)
        Layout.addWidget(self.Label)
        # Clear the button's own text so it is not drawn twice
        super().setText("")

    def setText(self, text):
        self.Full_Text = text
        self.Label.setText(text)

    def text(self):
        return self.Full_Text




# Rotating ▶ arrow overlay used inside Dropdown widgets
class Dropdown_Arrow(QLabel):

    def __init__(self, parent=None):
        super().__init__("▶", parent)
        self.setObjectName("DropdownArrow")
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.Angle = 0.0

    def Get_Angle(self):
        return self.Angle

    def Set_Angle(self, angle):
        self.Angle = angle
        self.update()

    angle = Property(float, Get_Angle, Set_Angle)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.rotate(self.Angle)
        painter.translate(-self.width() / 2.0, -self.height() / 2.0)
        # Read color from the parent combo box so the arrow always matches its text
        p = self.parentWidget()
        color = p.palette().color(p.foregroundRole()) if p else self.palette().color(self.foregroundRole())
        painter.setPen(color)
        painter.setFont(self.font())
        painter.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, "▶")




# QComboBox with a rotating ▶ arrow that animates open/close,
# and ignores mouse wheel events when closed
class Dropdown(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Dropdown")
        self.Arrow = Dropdown_Arrow(self)
        self.Arrow_Animation = QPropertyAnimation(self.Arrow, b"angle")
        self.Arrow_Animation.setDuration(ANIMATION_DURATION)
        self.Arrow_Animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.Position_Arrow()
        # Apply the widget shadow directly so it works even inside collapsible
        # sections whose own QGraphicsDropShadowEffect would otherwise prevent
        # child effects from rendering outside their bounding rect
        self.Update_Shadow()

    def Position_Arrow(self):
        w, h = self.width() or 100, self.height() or 32
        # Fill the entire 28px drop-down button area so the font is never clipped
        self.Arrow.setGeometry(w - 28, 0, 28, h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.Position_Arrow()

    def Update_Shadow(self):
        # Detect light/dark from the actual applied palette rather than QSettings
        # so this works correctly in Style_Preview as well as the main app
        bg = self.palette().color(self.backgroundRole())
        is_light = bg.lightness() > 128
        if is_light:
            if self.graphicsEffect() is None:
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(8)
                shadow.setXOffset(0)
                shadow.setYOffset(2)
                shadow.setColor(QColor(0, 0, 0, 25))
                self.setGraphicsEffect(shadow)
        else:
            self.setGraphicsEffect(None)

    def changeEvent(self, event):
        super().changeEvent(event)
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.StyleChange:
            self.Update_Shadow()

    def showPopup(self):
        # Discard Qt's cached item sizes before the popup opens so that
        # sizeHint() is re-evaluated at the current combo box width.
        # Without this, row heights from the original window size are reused
        # even after the window has been resized, causing inconsistent spacing.
        self.view().scheduleDelayedItemsLayout()
        if not hasattr(self, "Popup_Flags_Configured"):
            self.Popup_Flags_Configured = False
        if not self.Popup_Flags_Configured:
            popup_window = self.view().window()
            popup_window.setWindowFlags(popup_window.windowFlags() | Qt.NoDropShadowWindowHint)
            self.Popup_Flags_Configured = True
        super().showPopup()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.Strip_Popup_Shadow)
        self.Arrow_Animation.stop()
        self.Arrow_Animation.setStartValue(self.Arrow.Angle)
        self.Arrow_Animation.setEndValue(90.0)
        self.Arrow_Animation.start()

    def Strip_Popup_Shadow(self):
        import sys, ctypes
        if sys.platform != "win32":
            return
        hwnd = int(self.view().window().winId())
        DWMWA_NCRENDERING_POLICY = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_NCRENDERING_POLICY, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))

    def hidePopup(self):
        super().hidePopup()
        self.Arrow_Animation.stop()
        self.Arrow_Animation.setStartValue(self.Arrow.Angle)
        self.Arrow_Animation.setEndValue(0.0)
        self.Arrow_Animation.start()

    def wheelEvent(self, event):
        # Only allow the wheel to change the value when the dropdown is open
        if self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()

    def paintEvent(self, event):
        # Calibration dropdowns prefix user-edited/entered option text with "* ".
        # Color just that leading "*" in the closed box; everything else paints
        # exactly as the default QComboBox would.
        Current_Text = self.currentText()
        if not Current_Text.startswith("* "):
            super().paintEvent(event)
            return

        painter = QPainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        Style = self.style()

        # Let the style paint the frame, background, and arrow area; draw the text ourselves.
        # The widget argument is required so the QSS engine resolves this widget's rules —
        # without it the style falls back to native chrome (square corners, double arrow).
        opt.currentText = ""
        Style.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt, painter, self)

        Text_Rect = Style.subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField, self)
        Text_Rect = Text_Rect.adjusted(2, 0, -2, 0)

        _, _, Theme_Colors = Get_Theme()
        Star_Color = QColor(Theme_Colors.get("Secondary_Caution_Text"))
        Normal_Color = self.palette().color(self.foregroundRole())

        painter.setFont(self.font())
        fm = painter.fontMetrics()
        Star_Width = fm.horizontalAdvance("*")

        Star_Rect = QRect(Text_Rect.left(), Text_Rect.top(), Star_Width, Text_Rect.height())
        Rest_Rect = QRect(Text_Rect.left() + Star_Width, Text_Rect.top(), Text_Rect.width() - Star_Width, Text_Rect.height())

        painter.setPen(Star_Color)
        painter.drawText(Star_Rect, Qt.AlignVCenter | Qt.AlignLeft, "*")

        Rest_Text = fm.elidedText(Current_Text[1:], Qt.ElideRight, Rest_Rect.width())
        painter.setPen(Normal_Color)
        painter.drawText(Rest_Rect, Qt.AlignVCenter | Qt.AlignLeft, Rest_Text)




# A row widget that tracks hover state via a dynamic property so that
# child label/checkbox text colours can be changed via QSS selectors like
# QWidget#CheckboxRow[hovered="true"] QLabel { color: ...; }
class CheckboxRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CheckboxRow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("hovered", False)
        # Extra callbacks invoked on hover change (e.g. to swap caution-colored
        # rich text that QSS selectors can't reach, since inline HTML spans
        # override any QSS-driven color on the QLabel that contains them).
        self.Hover_Callbacks = []

    def Add_Hover_Callback(self, callback):
        self.Hover_Callbacks.append(callback)

    def Set_Hovered(self, value):
        self.setProperty("hovered", value)
        self.style().unpolish(self)
        self.style().polish(self)
        for child in self.findChildren(QLabel):
            child.style().unpolish(child)
            child.style().polish(child)
        for child in self.findChildren(QCheckBox):
            child.setProperty("row_hovered", value)
            child.style().unpolish(child)
            child.style().polish(child)
        for callback in self.Hover_Callbacks:
            callback(value)

    def enterEvent(self, event):
        self.Set_Hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.Set_Hovered(False)
        super().leaveEvent(event)




# Arrow label that rotates smoothly via QPropertyAnimation
    # 0 degrees = pointing right (collapsed), 90 degrees = pointing down (expanded)
class Arrow_Label(QLabel):

    def __init__(self, parent=None):
        # Set the text so sizeHint is calculated correctly
        super().__init__("▶", parent)
        self.setObjectName("CollapsibleArrow")
        self.setAlignment(Qt.AlignCenter)
        self.Angle = 0.0

    def Get_Angle(self):
        return self.Angle

    def Set_Angle(self, angle):
        self.Angle = angle
        self.update()

    angle = Property(float, Get_Angle, Set_Angle)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.rotate(self.Angle)
        painter.translate(-self.width() / 2.0, -self.height() / 2.0)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(self.font())
        painter.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, "▶")




# Clickable header bar containing the title label and rotating arrow
class Collapsible_Header(QWidget):
    clicked = Signal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("CollapsibleHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)

        Header_Layout = QHBoxLayout(self)
        Header_Layout.setContentsMargins(12, 8, 12, 8)
        Header_Layout.setSpacing(8)

        self.Arrow = Arrow_Label()

        self.Title = QLabel(title)
        self.Title.setObjectName("CollapsibleTitle")

        Header_Layout.addWidget(self.Arrow)
        Header_Layout.addWidget(self.Title)
        Header_Layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)




# A reusable collapsible section that can contain a widget
    # When the header is clicked it will smoothly expand or collapse
class Collapsible_Content_Container(QWidget):
    Section_Animation_Finished = Signal(bool)

    def __init__(self, Container_Title, Content, *,
                 Show_Container_Title=True, Initially_Show_Container=True,
                 Expanding_Content=False, Drop_Shadow=True, Parent=None):
        super().__init__(Parent)
        self.setObjectName("CollapsibleSection")
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Prevent the outer layout from giving this section more height than its content needs
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        if Drop_Shadow:
            Shadow = QGraphicsDropShadowEffect(self)
            Shadow.setBlurRadius(Drop_Shadow if isinstance(Drop_Shadow, int) else 16)
            Shadow.setXOffset(0)
            Shadow.setYOffset(2)
            Shadow.setColor(QColor(0, 0, 0, 40))
            self.setGraphicsEffect(Shadow)

        self.Content = Content
        self.Show_Container_Title = Show_Container_Title
        self.Is_Expanded = Initially_Show_Container or not Show_Container_Title

        # Content is placed inside an HBox row.
        # Expanding_Content=True: content fills all available width (use for sections
        #   whose sizeHint is unreliable — e.g. word-wrapped labels or minimal-hint
        #   dropdowns that should still grow to fill the window).
        # Expanding_Content=False (default): content stays at its natural sizeHint
        #   width; a trailing stretch absorbs leftover space. A minimum of
        #   DEFAULT_MINIMUM_CONTENT_WIDTH ensures usability on narrow windows.
        self.Content.setMinimumWidth(DEFAULT_MINIMUM_CONTENT_WIDTH)
        self.Content_Row = QWidget()
        self.Content_Row.setObjectName("CollapsibleContentRow")
        Content_Row_Layout = QHBoxLayout(self.Content_Row)
        # 36px left indent: outer layout has 8px, so 8+36=44px total,
        # aligning content under the title text (header: 12px + 24px arrow + 8px spacing).
        Content_Row_Layout.setContentsMargins(36, 0, 0, 0)
        Content_Row_Layout.setSpacing(0)
        if Expanding_Content:
            Content_Row_Layout.addWidget(self.Content, stretch=1)
        else:
            Content_Row_Layout.addWidget(self.Content)
            Content_Row_Layout.addStretch()

        Collapsible_Section_Layout = QVBoxLayout(self)
        # Left/right/bottom margins keep content away from the rounded corners
        # so the card's border-radius is always visible
        Collapsible_Section_Layout.setContentsMargins(8, 0, 8, 8)
        Collapsible_Section_Layout.setSpacing(0)

        self.Header = Collapsible_Header(Container_Title)
        self.Header.clicked.connect(self.Toggle_Section)

        if Show_Container_Title:
            Collapsible_Section_Layout.addWidget(self.Header)
        else:
            self.Header.setVisible(False)

        Collapsible_Section_Layout.addWidget(self.Content_Row)

        # Height animation targets the row wrapper so the content animates
        # as a unit (including the trailing stretch space).
        self.Height_Animation = QPropertyAnimation(self.Content_Row, b"maximumHeight")
        self.Height_Animation.setDuration(ANIMATION_DURATION)
        self.Height_Animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.Height_Animation.finished.connect(self.When_Animation_Finishes)

        # Arrow rotation animation
        self.Arrow_Animation = QPropertyAnimation(self.Header.Arrow, b"angle")
        self.Arrow_Animation.setDuration(ANIMATION_DURATION)
        self.Arrow_Animation.setEasingCurve(QEasingCurve.InOutCubic)

        # Set initial visual state without animating
        if self.Is_Expanded:
            self.Content_Row.setVisible(True)
            self.Content_Row.setMaximumHeight(16777215)
            self.Header.Arrow.Set_Angle(90.0)
        else:
            self.Content_Row.setVisible(False)
            self.Content_Row.setMaximumHeight(0)
            self.Header.Arrow.Set_Angle(0.0)



    # Return the correct height for the given width, propagating word-wrap from children
    def hasHeightForWidth(self):
        return bool(self.layout() and self.layout().hasHeightForWidth())

    def heightForWidth(self, w):
        if self.layout() and self.layout().hasHeightForWidth():
            return self.layout().heightForWidth(w)
        return super().sizeHint().height()

    # Override sizeHint so the Maximum size policy uses the correct word-wrap-aware height.
    # When self.width() is not yet set (first layout pass), fall back to parent width minus
    # parent layout margins as a reasonable proxy for what this widget's width will be.
    def sizeHint(self):
        w = self.width()
        if w == 0 and self.parentWidget():
            parent = self.parentWidget()
            if parent.width() > 0:
                parent_layout = parent.layout()
                if parent_layout:
                    m = parent_layout.contentsMargins()
                    w = max(0, parent.width() - m.left() - m.right())
                else:
                    w = parent.width()
        if w > 0 and self.layout() and self.layout().hasHeightForWidth():
            h = self.layout().heightForWidth(w)
            return QSize(super().sizeHint().width(), h)
        return super().sizeHint()


    # Toggle the section open or closed with animation
    def Toggle_Section(self):
        expanding = not self.Is_Expanded
        self.Is_Expanded = expanding

        # Animate the arrow rotation
        self.Arrow_Animation.stop()
        self.Arrow_Animation.setStartValue(self.Header.Arrow.Angle)
        self.Arrow_Animation.setEndValue(90.0 if expanding else 0.0)
        self.Arrow_Animation.start()

        # Animate the content height
        self.Height_Animation.stop()
        if expanding:
            # Make visible and measure natural height before animating
            self.Content_Row.setVisible(True)
            self.Content_Row.setMaximumHeight(16777215)
            # Use heightForWidth for accurate target when content has word-wrapped labels.
            # self.width() may be 0 on first expand (widget not yet laid out), so fall back
            # to parent width minus parent layout margins as a proxy.
            w = self.width()
            if w == 0 and self.parentWidget():
                parent = self.parentWidget()
                if parent.width() > 0:
                    parent_layout = parent.layout()
                    if parent_layout:
                        m = parent_layout.contentsMargins()
                        w = max(0, parent.width() - m.left() - m.right())
                    else:
                        w = parent.width()
            # Content_Row sits inside this container's VBox which has left=8, right=8 margins
            content_row_w = max(1, w - 16) if w > 0 else 0
            if content_row_w > 0 and self.Content_Row.hasHeightForWidth():
                Natural_Height = self.Content_Row.heightForWidth(content_row_w)
            else:
                Natural_Height = self.Content_Row.sizeHint().height()
            self.Content_Row.setMaximumHeight(0)
            self.Height_Animation.setStartValue(0)
            self.Height_Animation.setEndValue(Natural_Height if Natural_Height > 0 else 300)
        else:
            self.Height_Animation.setStartValue(self.Content_Row.height())
            self.Height_Animation.setEndValue(0)

        self.Height_Animation.start()



    # When animation completes, clean up height constraints or hide content
    def When_Animation_Finishes(self):
        if self.Is_Expanded:
            # Remove the height cap so content can resize freely (e.g. if window resizes)
            self.Content_Row.setMaximumHeight(16777215)
        else:
            self.Content_Row.setVisible(False)
        self.Section_Animation_Finished.emit(self.Is_Expanded)



    # Set the section title
    def Set_The_Section_Title_Text(self, Section_Title):
        self.Header.Title.setText(Section_Title)


    # Get the section title
    def Get_The_Section_Title_Text(self):
        return self.Header.Title.text()


    # Expand or collapse the section programmatically
    def Expand_Or_Collapse_Section(self, Section_Checked):
        if Section_Checked != self.Is_Expanded:
            self.Toggle_Section()


    # Check if the section is expanded or collapsed
    def Section_Is_Expanded(self):
        return self.Is_Expanded


    # Prevent or allow the user from toggling this section
    def Disable_Collapsible_Section(self, locked: bool):
        try:
            self.Header.clicked.disconnect(self.Toggle_Section)
        except RuntimeError:
            pass
        if not locked:
            self.Header.clicked.connect(self.Toggle_Section)
            self.Header.setCursor(Qt.PointingHandCursor)
        else:
            self.Header.setCursor(Qt.ArrowCursor)
        self.Header.setProperty("locked", locked)
        self.Header.style().unpolish(self.Header)
        self.Header.style().polish(self.Header)
        for label in self.Header.findChildren(QLabel):
            label.style().unpolish(label)
            label.style().polish(label)


    # Return the content widget contained in the collapsible section
    def Content_Within_A_Collapsible_Section(self):
        return self.Content
