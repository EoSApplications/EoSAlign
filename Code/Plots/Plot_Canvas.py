# Load libraries
    # Load third party libraries
from PySide6.QtWidgets import QScrollArea
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg





# A figure canvas that passes wheel events to the parent scroll area so the
# outer scroll view keeps working while the mouse is over a figure
class Scroll_Friendly_Canvas(FigureCanvasQTAgg):

    def resizeEvent(self, event):

        # Tell the figure its new size first, then let it fit its legend to the new size
        super().resizeEvent(event)
        Update_The_Legend_Space = getattr(self.figure, "Update_The_Legend_Space", None)
        if Update_The_Legend_Space is not None:
            Update_The_Legend_Space()


    def wheelEvent(self, event):

        # Find the nearest scroll area above this canvas
        Parent = self.parent()
        while Parent is not None:
            if isinstance(Parent, QScrollArea):
                Parent.wheelEvent(event)
                return
            Parent = Parent.parent()

        super().wheelEvent(event)
