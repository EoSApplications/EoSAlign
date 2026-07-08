# Load libraries
    # Load standard libraries
import os
    # Load PySide6 (Qt) libraries
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QPushButton
from PySide6.QtCore import QTimer, Qt, QSize, QEvent, Signal
from PySide6.QtGui import QPixmap, QImageReader

# Remove Qt's default 256 MB allocation cap so large multi-panel figures can load without error
QImageReader.setAllocationLimit(0)


# Module-level constants


# How often the display widget polls for the PNG file, in milliseconds
Poll_Interval__Ms = 500

# How long the display widget waits before declaring a load failure, in milliseconds
Load_Timeout__Ms = 30_000

# Fraction of the window width the frame widget occupies
Frame_Width_Fraction = 0.92

# Fraction of the window height the frame widget occupies at maximum
Frame_Height_Fraction = 0.80


# PNG display widget


# Widget that displays a PNG file once it appears on disk
#   Polls the file system at Poll_Interval__Ms until the file exists and is non-null
#   Shows "Loading..." for up to Load_Timeout__Ms, then shows a reload button (if a callback
#   is provided) or "Failed to load plot." text
#   Emits Finished (deferred one event-loop tick) on load success or timeout so that callers
#   can chain multiple widgets sequentially — each 30-second timer only starts after the
#   previous widget completes
#   Pass Deferred=True to suppress auto-start; call Start_Loading() manually
class PNG_Display_Widget(QWidget):

    # Emitted (deferred one tick via QTimer.singleShot) when loading completes or times out
    Finished = Signal()

    # Initialize the widget, optionally starting the polling timers immediately
    def __init__(self, Png_Path=None, parent=None, Deferred=False, Reload_Callback=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Scope to this class name so the rule does not create a cascade boundary for child widgets
        self.setStyleSheet("PNG_Display_Widget { background: transparent; }")

        # Store the path to the PNG file that this widget should display
        self.Local__Path = str(Png_Path) if Png_Path else ""

        # Track the last seen file modification time to detect updates
        self.Local__Last_Mtime = None

        # Flag set to True when the load timeout expires
        self.Local__Timed_Out = False

        # The loaded source pixmap at full resolution; null until loading succeeds
        self.Local__Source_Pixmap = QPixmap()

        # Optional callable invoked when the user clicks the reload button
        self.Local__Reload_Callback = Reload_Callback

        # Label used to show either the pixmap or a text placeholder message
        self.Local__Label = QLabel(self)
        self.Local__Label.setAlignment(Qt.AlignCenter)
        self.Local__Label.setStyleSheet("background: transparent;")
        self.Local__Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Reload button shown after a timeout when a reload callback is available
        self.Local__Reload_Button = QPushButton("Reload Figure", self)
        self.Local__Reload_Button.setObjectName("Secondary_Button")
        self.Local__Reload_Button.setFixedHeight(32)
        self.Local__Reload_Button.setVisible(False)
        self.Local__Reload_Button.clicked.connect(self.Local__Handle_Reload_Clicked)

        # Timer that fires repeatedly to check whether the PNG file has appeared or changed
        self.Local__Poll_Timer = QTimer(self)
        self.Local__Poll_Timer.setInterval(Poll_Interval__Ms)
        self.Local__Poll_Timer.timeout.connect(self.Local__Poll)

        # One-shot timer that fires after the load timeout has elapsed
        self.Local__Timeout_Timer = QTimer(self)
        self.Local__Timeout_Timer.setSingleShot(True)
        self.Local__Timeout_Timer.setInterval(Load_Timeout__Ms)
        self.Local__Timeout_Timer.timeout.connect(self.Local__On_Timeout)

        # No path: show a static placeholder immediately
        if not self.Local__Path:
            self.Local__Show_Text_Placeholder("No figure available.")
        # Deferred mode: show loading text but wait for Start_Loading() to begin polling
        elif Deferred:
            self.Local__Set_Loading_Text()
        # Normal mode: attempt one synchronous poll before starting the timers
        else:
            self.Local__Set_Loading_Text()
            self.Local__Poll()
            # Only start the timers if the first synchronous poll did not succeed
            if self.Local__Source_Pixmap.isNull() and not self.Local__Timed_Out:
                self.Local__Poll_Timer.start()
                self.Local__Timeout_Timer.start()

    # Public API

    # Point the widget at a new PNG file and reset to the deferred loading state
    def Set_Path(self, Png_Path):
        self.Local__Path = str(Png_Path) if Png_Path else ""
        self.Reset()

    # Reset the loading state without starting timers; used to prepare for chained loading
    def Reset(self):
        self.Local__Last_Mtime = None
        self.Local__Timed_Out = False
        self.Local__Source_Pixmap = QPixmap()
        self.Local__Poll_Timer.stop()
        self.Local__Timeout_Timer.stop()
        # Show loading text when a path exists; otherwise show a "no figure" placeholder
        if self.Local__Path:
            self.Local__Set_Loading_Text()
        else:
            self.Local__Show_Text_Placeholder("No figure available.")

    # Reset and begin polling for the PNG file
    #   If there is no path, emits Finished immediately (deferred one tick) so a sequential
    #   chain advances past this widget without hanging
    def Start_Loading(self):
        self.Reset()
        # No path: advance the chain immediately so we do not block sequential loading
        if not self.Local__Path:
            QTimer.singleShot(0, self.Finished.emit)
            return
        # Attempt one synchronous poll before relying on the timer
        self.Local__Poll()
        if self.Local__Source_Pixmap.isNull() and not self.Local__Timed_Out:
            self.Local__Poll_Timer.start()
            self.Local__Timeout_Timer.start()

    # Return the width/height aspect ratio of the loaded image, or None if not yet loaded
    def Natural_Aspect_Ratio(self):
        if self.Local__Source_Pixmap.isNull():
            return None
        Width = self.Local__Source_Pixmap.width()
        Height = self.Local__Source_Pixmap.height()
        # Return the ratio only when height is positive to avoid division by zero
        return (Width / Height) if Height > 0 else None

    # Internal helpers

    # Show the "Loading..." placeholder text
    def Local__Set_Loading_Text(self):
        self.Local__Show_Text_Placeholder("Loading...")

    # Show a centered text placeholder and hide the reload button
    def Local__Show_Text_Placeholder(self, Text):
        self.Local__Reload_Button.hide()
        self.Local__Label.show()
        self.Local__Label.setPixmap(QPixmap())
        self.Local__Label.setText(Text)
        self.Local__Update_Placeholder_Geometry()

    # Show the reload button when a callback is available, or a failure text when it is not
    def Local__Show_Reload_Button(self):
        self.Local__Label.hide()
        self.Local__Label.setPixmap(QPixmap())
        self.Local__Label.setText("")
        # If there is no reload callback, fall back to static failure text
        if self.Local__Reload_Callback is None:
            self.Local__Show_Text_Placeholder("Failed to load plot.")
            return
        self.Local__Reload_Button.show()
        self.Local__Update_Placeholder_Geometry()

    # Position the active placeholder element (label or reload button) centered in the widget
    def Local__Update_Placeholder_Geometry(self):
        if self.Local__Reload_Button.isVisible():
            # Center the reload button within the widget
            Button_Size = self.Local__Reload_Button.sizeHint()
            Button_X = (self.width() - Button_Size.width()) // 2
            Button_Y = (self.height() - Button_Size.height()) // 2
            self.Local__Reload_Button.setGeometry(
                max(0, Button_X),
                max(0, Button_Y),
                Button_Size.width(),
                Button_Size.height(),
            )
        else:
            # Stretch the text label to fill the entire widget
            self.Local__Label.setGeometry(0, 0, max(0, self.width()), max(0, self.height()))

    # Invoke the reload callback when the user clicks the reload button
    def Local__Handle_Reload_Clicked(self):
        if callable(self.Local__Reload_Callback):
            self.Local__Reload_Callback()

    # Check whether the PNG file has appeared or been updated and load it if so
    def Local__Poll(self):
        # Nothing to poll when no path is set or the file does not yet exist
        if not self.Local__Path or not os.path.exists(self.Local__Path):
            return
        try:
            # Read the file modification time to detect newly written PNGs
            Mtime = os.path.getmtime(self.Local__Path)
        except OSError:
            # File may have been deleted between the exists() check and getmtime()
            return

        # Skip if the file has not been updated since our last successful load
        if self.Local__Last_Mtime is not None and Mtime <= self.Local__Last_Mtime:
            return
        try:
            # Load the PNG into a pixmap; QPixmap can return null for unsupported formats
            New_Pixmap = QPixmap(self.Local__Path)
        except Exception:
            # Loading failed — file may be partially written or corrupted
            return
        if New_Pixmap.isNull():
            return

        # Update state and display the newly loaded image
        self.Local__Last_Mtime = Mtime
        self.Local__Source_Pixmap = New_Pixmap
        self.Local__Poll_Timer.stop()
        self.Local__Timeout_Timer.stop()
        self.Local__Timed_Out = False
        self.Local__Reload_Button.hide()
        self.Local__Label.show()
        self.Local__Label.setText("")
        self.Local__Update_Display()

        # Emit Finished deferred so callers in the event loop receive it after this call returns
        QTimer.singleShot(0, self.Finished.emit)

    # Handle the load timeout by stopping polling and showing the reload button
    def Local__On_Timeout(self):
        self.Local__Poll_Timer.stop()
        self.Local__Timed_Out = True
        self.Local__Show_Reload_Button()
        # Emit Finished so a sequential chain advances even though loading failed
        QTimer.singleShot(0, self.Finished.emit)

    # Scale and center the loaded pixmap to fill the current widget size
    def Local__Update_Display(self):
        if self.Local__Source_Pixmap.isNull() or self.width() <= 0 or self.height() <= 0:
            return

        # Use at least 2x physical pixels so Qt's compositing pipeline has enough data
        # to produce sharp output even on 1x displays
        Device_Scale = max(self.devicePixelRatio(), 2.0)
        Target_Size = QSize(
            max(1, int(self.width() * Device_Scale)),
            max(1, int(self.height() * Device_Scale)),
        )
        Scaled_Pixmap = self.Local__Source_Pixmap.scaled(
            Target_Size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        Scaled_Pixmap.setDevicePixelRatio(Device_Scale)
        self.Local__Label.setPixmap(Scaled_Pixmap)

        # Compute logical dimensions for centering; logical = physical / device_scale
        Logical_Width = int(Scaled_Pixmap.width() / Device_Scale)
        Logical_Height = int(Scaled_Pixmap.height() / Device_Scale)
        Display_X = (self.width() - Logical_Width) // 2
        Display_Y = (self.height() - Logical_Height) // 2
        self.Local__Label.setGeometry(Display_X, Display_Y, Logical_Width, Logical_Height)

    # Override of Qt's resizeEvent — method name must match Qt's camelCase API exactly
    def resizeEvent(self, Event):
        super().resizeEvent(Event)
        # Re-scale the displayed image to the new widget size
        if not self.Local__Source_Pixmap.isNull():
            self.Local__Update_Display()
        # Re-center the placeholder element if no image is loaded yet
        else:
            self.Local__Update_Placeholder_Geometry()


# PNG frame widget


# Responsive frame that sizes an inner PNG_Display_Widget to a fraction of the main window
#   Width  = window_width  × Frame_Width_Fraction
#   Height = Width / aspect_ratio, capped at window_height × Frame_Height_Fraction
#   Aspect ratio is taken from the loaded image; falls back to 4:3 until the image loads
#   Pass Width_Only=True to let height grow freely with no height cap
class PNG_Frame_Widget(QWidget):

    # Initialize the frame with an inner display widget and optional sizing overrides
    def __init__(
        self,
        Inner_Widget,
        Aspect_Ratio=None,
        parent=None,
        Frame_Width_Fraction_Override=None,
        Frame_Height_Fraction_Override=None,
        Width_Only=False,
    ):
        super().__init__(parent)
        self.setObjectName("PlotFrame")
        self.setStyleSheet("background: transparent;")

        # The inner widget whose PNG this frame is sizing
        self.Local__Inner_Widget = Inner_Widget

        # Cached aspect ratio; updated once the inner widget loads its image
        self.Local__Aspect_Ratio = float(Aspect_Ratio) if Aspect_Ratio else None

        # Use caller-provided fractions or fall back to the module-level defaults
        self.Local__Frame_Width_Fraction = float(Frame_Width_Fraction_Override) if Frame_Width_Fraction_Override else Frame_Width_Fraction
        self.Local__Frame_Height_Fraction = float(Frame_Height_Fraction_Override) if Frame_Height_Fraction_Override else Frame_Height_Fraction

        # When True, the height grows freely rather than being capped at a fraction of the window
        self.Local__Width_Only = Width_Only

        # Reference to the top-level window we are listening to for resize events
        self.Local__Watched_Window = None

        Inner_Widget.setParent(self)

        # Start at a reasonable placeholder size until the window size is known
        self.setFixedSize(400, 300)

        # Poll until the image loads so the aspect ratio can be updated
        self.Local__Aspect_Timer = QTimer(self)
        self.Local__Aspect_Timer.setInterval(600)
        self.Local__Aspect_Timer.timeout.connect(self.Local__Refresh_Aspect)
        self.Local__Aspect_Timer.start()

        # Trigger an initial size calculation after the event loop starts
        QTimer.singleShot(0, self.Local__Update_From_Window)

    # Window tracking

    # Override of Qt's showEvent — method name must match Qt's camelCase API exactly
    def showEvent(self, Event):
        super().showEvent(Event)
        # Attach a resize listener to the top-level window when this widget becomes visible
        self.Local__Attach_Window_Filter()
        self.Local__Update_From_Window()

    # Install an event filter on the top-level window so we hear its resize events
    def Local__Attach_Window_Filter(self):
        Window = self.window()
        # Do not reinstall if already watching this window
        if Window is self or Window is self.Local__Watched_Window:
            return
        # Remove the filter from the previous window before installing on the new one
        if self.Local__Watched_Window is not None:
            self.Local__Watched_Window.removeEventFilter(self)
        Window.installEventFilter(self)
        self.Local__Watched_Window = Window

    # Override of Qt's eventFilter — method name must match Qt's camelCase API exactly
    def eventFilter(self, Watched_Object, Event):
        # Update our size whenever the watched window is resized
        if Event.type() == QEvent.Resize and Watched_Object is self.Local__Watched_Window:
            self.Local__Update_From_Window()
        # Return False to let the event propagate normally
        return False

    # Size calculation

    # Check if the inner widget has loaded its image and update the stored aspect ratio
    def Local__Refresh_Aspect(self):
        Natural_Ratio = self.Local__Inner_Widget.Natural_Aspect_Ratio()
        if Natural_Ratio is not None:
            # Image is now available — store the real ratio and stop polling
            self.Local__Aspect_Ratio = Natural_Ratio
            self.Local__Aspect_Timer.stop()
            self.Local__Update_From_Window()

    # Return the best available aspect ratio, falling back to 4:3 if no image is loaded yet
    def Local__Current_Aspect(self):
        if self.Local__Aspect_Ratio:
            return self.Local__Aspect_Ratio
        Natural_Ratio = self.Local__Inner_Widget.Natural_Aspect_Ratio()
        # Return the natural ratio when available, otherwise use a 4:3 placeholder
        return Natural_Ratio if Natural_Ratio else (4.0 / 3.0)

    # Recompute and apply the widget's fixed size based on the current window dimensions
    def Local__Update_From_Window(self):
        Window = self.window()
        # Cannot compute size relative to self — wait until a real parent window exists
        if Window is self:
            return
        Window_Width = Window.width()
        Window_Height = Window.height()
        if Window_Width <= 0 or Window_Height <= 0:
            return

        Aspect_Ratio = self.Local__Current_Aspect()
        Target_Width = max(50, int(Window_Width * self.Local__Frame_Width_Fraction))
        Target_Height = max(40, int(Window_Height * self.Local__Frame_Height_Fraction))

        # Width-only mode: height grows freely with no cap
        if self.Local__Width_Only:
            Width = Target_Width
            Height = max(40, int(Target_Width / Aspect_Ratio))
        # Normal mode: fit within both width and height constraints, preserving aspect ratio
        else:
            Width_From_Height = int(Target_Height * Aspect_Ratio)
            Height_From_Width = int(Target_Width / Aspect_Ratio)
            # Use the height constraint if it produces a width that fits; otherwise use width
            if Width_From_Height <= Target_Width:
                Width, Height = Width_From_Height, Target_Height
            else:
                Width, Height = Target_Width, Height_From_Width

        New_Size = QSize(max(50, Width), max(40, Height))

        # Only apply the new size when it actually changed to avoid unnecessary redraws
        if self.size() != New_Size:
            self.setFixedSize(New_Size)
            self.updateGeometry()

        # Stretch the inner widget to fill the frame
        self.Local__Inner_Widget.setGeometry(0, 0, self.width(), self.height())




