# Load Libraries
    # Load standard libraries
import sys
import os
import time
    # Load third party libraries
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtGui import QColor, QFont





# Create the loading image where the loading messages will be displayed
class Create_Loading_Message_Screen(QSplashScreen):

    # Adjust this value (in pixels) to fine-tune text position relative to the lower middle:
    #   positive = shift text down, negative = shift text up
    Text_Vertical_Offset = 0

    # Override Qt's drawContents to control where the message text is painted
        # The method name must match Qt's camelCase API exactly for the override to work
    def drawContents(self, Painter):

        # Get the current loading message
        Loading_Message = self.message()
        # If there is no message there is nothing to draw
        if not Loading_Message:
            # Return without painting anything
            return

        # Get the bounding rectangle of the splash screen
        Rectangle_Shape = self.rect()
        # Calculate the vertical position for the text
            # Place the text at 70% of the screen height, adjusted by the vertical offset
        Text_Y = int(Rectangle_Shape.height() * 0.7) + self.Text_Vertical_Offset

        # Set the font for the loading message text
        Painter.setFont(QFont("Noto Sans", 12))
        # Set the text color to black
        Painter.setPen(QColor(0, 0, 0))
        # Draw the loading message text centered horizontally and word-wrapped
        Painter.drawText(QRect(Rectangle_Shape.x() + 10, Text_Y, Rectangle_Shape.width() - 20, Rectangle_Shape.height() - Text_Y), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, Loading_Message)



# Get the absolute path for all files depending on the operating system
def Get_Resource_Path(Relative_Path):

    # Check if the application is running as a bundled executable
    if getattr(sys, 'frozen', False):
        # The Mac/Linux/Windows .spec files all build onefile bundles (EXE
        # receives a.binaries/a.datas directly, no COLLECT step), so the
        # bootloader extracts embedded data to sys._MEIPASS at runtime on
        # every platform -- including inside a macOS .app bundle.
        Base_Path = sys._MEIPASS
        return os.path.join(Base_Path, Relative_Path)

    # Check if the application is running as a pip-installed package
        # Only take this branch when this very file was loaded from inside the installed
        # "eosapplications" package - otherwise, merely having that package pip-installed
        # somewhere in the environment (e.g. to test a build) would still match here.
        # importlib.resources.files("eosapplications") has the side effect of importing
        # the package, whose __init__.py inserts its own directory at the front of
        # sys.path - which would then shadow every sibling module (EoS_Math, etc.) with
        # the installed copy instead of the local one for the rest of the process
    if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == "eosapplications":
        try:
            import importlib.resources
            Package_Dir = importlib.resources.files("eosapplications")
            return str(Package_Dir / Relative_Path)
        except Exception:
            pass

    # If the application is running as a script use the current directory
    Base_Path = os.path.abspath(".")
    return os.path.join(Base_Path, Relative_Path)



# Load all bundled fonts from the Fonts directory and set the application font
def Load_Fonts(App):

    # Load libraries
        # Load third party libraries
    from PySide6.QtGui import QFontDatabase, QFont

    # Find the Fonts directory
    Fonts_Directory = Get_Resource_Path("Fonts")

    # If the Fonts directory does not exist, skip font loading
    if not os.path.isdir(Fonts_Directory):
        # Return without loading any fonts
        return

    # Walk the Fonts directory and load every font file found
    for Root, Subdirectory_Names, Files in os.walk(Fonts_Directory):
        # Check each file in the directory
        for File in Files:
            # Only load TrueType and OpenType font files
            if File.lower().endswith((".ttf", ".otf")):
                # Add the font file to the application's font database
                QFontDatabase.addApplicationFont(os.path.join(Root, File))

    # Set Noto Sans as the application font
    App.setFont(QFont("Noto Sans", 11))



# Create the loading message
def Create_Loading_Message(App, Logo_Path=None):

    # Load libraries
        # Load third party libraries
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QColor
    from PySide6.QtCore import Qt

    # If no logo stated use the Sun image as a default
    if Logo_Path is None:
        Logo_Path = "Graphics/Sun.png"
    # Find the size of the screen
    Screen = QApplication.primaryScreen()
    Screen_Geometry = Screen.availableGeometry()
    Loading_Screen_Width = min(500, int(Screen_Geometry.width() * 0.5))
    Loading_Screen_Height = min(500, int(Screen_Geometry.height() * 0.5))
    # Load the logo and set the size of the loading screen
    Logo = QPixmap(Get_Resource_Path(Logo_Path))
    # If the logo can not be loaded a grey box will be shown instead
    if Logo.isNull() or Logo.width() == 0:
        # Create a grey placeholder pixmap of the loading screen size
        Logo = QPixmap(Loading_Screen_Width, Loading_Screen_Height)
        # Fill the placeholder with a dark grey color
        Logo.fill(QColor("#515151"))
    # If the logo is too big it will be scaled down
    else:
        Logo = Logo.scaled(Loading_Screen_Width, Loading_Screen_Height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # Create and display the loading screen
    Loading_Screen = Create_Loading_Message_Screen(Logo)
    # Center the loading screen on the user's screen
    Loading_Screen_X_Position = Screen_Geometry.x() + (Screen_Geometry.width() - Loading_Screen.width()) // 2
    Loading_Screen_Y_Position = Screen_Geometry.y() + (Screen_Geometry.height() - Loading_Screen.height()) // 2
    # Move the loading screen to the calculated position
    Loading_Screen.move(Loading_Screen_X_Position, Loading_Screen_Y_Position)
    # Show the loading screen
    Loading_Screen.show()
    # Force the UI to update and display the loading screen immediately
        # Called twice to ensure the splash screen is fully rendered before loading begins
    App.processEvents()
    App.processEvents()

    # Return the loading screen
    return Loading_Screen



# Update the loading message
def Update_Loading_Message(Loading_Screen, App, Message, Timer=None):

    # Load libraries
        # Load third party libraries
    from PySide6.QtCore import Qt

    # If a timer was provided, log timing information for each loading step
    if Timer is not None:
        # Record the current time
        Time_Right_Now = time.perf_counter()
        # Calculate the total elapsed time since the application started loading
        Time_Total = Time_Right_Now - Timer["Started Loading the Application"]
        # Calculate the time elapsed since the last loading message
        Time_Since_Last = Time_Right_Now - Timer.get("Last Loading Message", Timer["Started Loading the Application"])
        # Print completion time for the step that just finished before showing the next message
        if "Current Step" in Timer:
            print(f"\tCompleted in {Time_Since_Last:.4f}s - (total so far: {Time_Total:.4f}s)")
        # Update the timer with the current time and the new loading step
        Timer["Last Loading Message"] = Time_Right_Now
        Timer["Current Step"] = Message
        # Print the new loading step to the console
        print(f"Loading: {Message}")
        # Update the loading screen with the new message
        Loading_Screen.showMessage(Message, Qt.AlignBottom | Qt.AlignHCenter)
    # If no timer was provided, just update the loading screen with the new message
    else:
        Loading_Screen.showMessage(Message, Qt.AlignBottom | Qt.AlignHCenter)

    # Update the loading screen immediately
    App.processEvents()




