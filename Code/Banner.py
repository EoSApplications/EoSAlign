# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QApplication, QLabel, QHBoxLayout, QSizePolicy, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImageReader, QPainter
    # Load local functions from local files
from Loading_Message import Get_Resource_Path





# Create the Banner that will appear at the top of all windows
class Banner(QLabel):
    def __init__(self, Parent=None, Logo_And_Sun_Image_Path=None):
        super().__init__(Parent)

        # Get device pixel ratio so images render sharply on HiDPI/scaled displays
        Device_Pixel_Ratio = QApplication.primaryScreen().devicePixelRatio()
        # Create the space for the banner
        self.setObjectName("Banner_Label")
        # Set the size of the banner
        Banner_Height = 70
        Maximum_Banner_Width = 8000
        # Set the height of the banner to never change
        self.setFixedHeight(Banner_Height)

        # Load and tile stars image over black background
        Stars_Image_Path = Get_Resource_Path("Graphics/Stars.png")
        Read_The_Starts_Image = QImageReader(Stars_Image_Path)
        Read_The_Starts_Image.setAutoTransform(True)
        Stars_Image = Read_The_Starts_Image.read()
        Stars_Image_Pixmap = QPixmap.fromImage(Stars_Image)
        Scaled_Stars_Image = Stars_Image_Pixmap.scaledToHeight(int(Banner_Height * Device_Pixel_Ratio), Qt.SmoothTransformation)

        # Create an image where the stars image is duplicated horizontally to fill the width of the banner
        Stars_Banner_Image_Width = Maximum_Banner_Width
        Stars_Banner_Image_Pixmap = QPixmap(Stars_Banner_Image_Width, int(Banner_Height * Device_Pixel_Ratio))
        Stars_Banner_Image_Pixmap.fill(Qt.black)
        Stars_Banner_Image_Painter = QPainter(Stars_Banner_Image_Pixmap)
        X_Position = 0
        while X_Position < Stars_Banner_Image_Width:
            Stars_Banner_Image_Painter.drawPixmap(X_Position, 0, Scaled_Stars_Image)
            X_Position += Scaled_Stars_Image.width()
        Stars_Banner_Image_Painter.end()
        Stars_Banner_Image_Pixmap.setDevicePixelRatio(Device_Pixel_Ratio)

        # Create the banner background
        Banner_Background = QLabel(self)
        Banner_Background.setObjectName("Banner_Background")
        # Add the stars image to the banner background
        Banner_Background.setPixmap(Stars_Banner_Image_Pixmap)
        # Set the size of the banner background
        Banner_Background.setGeometry(0, 0, Stars_Banner_Image_Width, Banner_Height)
        # Send the banner background to the back
        Banner_Background.lower()

        # Setup the main layout for the banner
        Banner_Layout = QHBoxLayout(self)
        Banner_Layout.setContentsMargins(10, 0, 10, 0)
        Banner_Layout.setSpacing(0)
        Banner_Layout.setAlignment(Qt.AlignLeft)

        # Create a widget to display the planets
        Planets_Widget = QWidget(self)
        Planets_Widget.setStyleSheet("background: transparent;")
        Planets_Widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        Planets_Layout = QHBoxLayout(Planets_Widget)
        Planets_Layout.setContentsMargins(0, 0, 0, 0)
        Planets_Layout.setSpacing(0)

        # Get the planet images and their sizes
        Planet_Images = [
            ("Logo_And_Sun", 63, 63),
            ("Graphics/Mercury.png", 8, 8),
            ("Graphics/Venus.png", 8, 8),
            ("Graphics/Earth.png", 10, 10),
            ("Graphics/Mars.png", 8, 8),
            ("Graphics/Jupiter.png", 30, 30),
            ("Graphics/Saturn.png", 69, 30),
            ("Graphics/Uranus.png", 15, 15),
            ("Graphics/Neptune.png", 15, 15),
        ]

        # Set the relative distances of the planets from the sun
        Planet_Distances = [
            0.39,       # Mercury
            0.72,       # Venus
            1.00,       # Earth
            1.52,       # Mars
            5.20,       # Jupiter
            9.58,       # Saturn
            19.18,      # Uranus
            30.07,      # Neptune
        ]

        # Add each planet to the banner with the correct distance from the sun
        for Index, (Image_Path, Image_Width, Image_Height) in enumerate(Planet_Images):

            # Add spacing before each planet based on its orbital distance from the sun
            if Index > 0:
                Planet_Spacing = Planet_Distances[Index - 1] if Index - 1 < len(Planet_Distances) else 1
                Planets_Layout.addStretch(int(Planet_Spacing))

            # Load the logo and sun image
            if Image_Path == "Logo_And_Sun":
                # Find the logo and sun image path
                Logo_And_Sun_Image_Reader = QImageReader(Get_Resource_Path(Logo_And_Sun_Image_Path))
                # Resize the logo and sun image
                Logo_And_Sun_Image_Reader.setAutoTransform(True)
                Logo_And_Sun_Image_Pixmap = QPixmap.fromImage(Logo_And_Sun_Image_Reader.read())
                Logo_And_Sun_Image_Pixmap = Logo_And_Sun_Image_Pixmap.scaled(int(Image_Width * Device_Pixel_Ratio), int(Image_Height * Device_Pixel_Ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                Logo_And_Sun_Image_Pixmap.setDevicePixelRatio(Device_Pixel_Ratio)
                # Create a label to display the logo and sun image
                Logo_And_Sun_Image_Label = QLabel(self)
                Logo_And_Sun_Image_Label.setPixmap(Logo_And_Sun_Image_Pixmap)
                Logo_And_Sun_Image_Label.setFixedSize(Image_Width, Image_Height)
                # Set the background of the logo and sun image to be transparent
                Logo_And_Sun_Image_Label.setStyleSheet("background: transparent;")
                Logo_And_Sun_Widget = Logo_And_Sun_Image_Label
                # Add the logo and sun image to the planets layout
                Planets_Layout.addWidget(Logo_And_Sun_Widget)

            # Load the planet image
            else:
                # Find the planet image path
                Planet_Image_Reader = QImageReader(Get_Resource_Path(Image_Path))
                # Resize the planet image
                Planet_Image_Reader.setAutoTransform(True)
                Planet_Image_Pixmap = QPixmap.fromImage(Planet_Image_Reader.read())
                Planet_Image_Pixmap = Planet_Image_Pixmap.scaled(int(Image_Width * Device_Pixel_Ratio), int(Image_Height * Device_Pixel_Ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                Planet_Image_Pixmap.setDevicePixelRatio(Device_Pixel_Ratio)
                # Create a label to display the planet image
                Planet_Image_Label = QLabel(self)
                Planet_Image_Label.setPixmap(Planet_Image_Pixmap)
                Planet_Image_Label.setFixedSize(Image_Width, Image_Height)
                # Set the background of the planet image to be transparent
                Planet_Image_Label.setStyleSheet("background: transparent;")
                Planet_Widget = Planet_Image_Label
                # Add the planet image to the planets layout
                Planets_Layout.addWidget(Planet_Widget)

        # Add the planets to the banner layout
        Banner_Layout.addWidget(Planets_Widget)




