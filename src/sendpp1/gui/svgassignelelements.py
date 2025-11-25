import sys
import io
import pyembroidery # Import pyembroidery

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QGraphicsLineItem, QGraphicsEllipseItem # Using Line and Ellipse items
)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QPointF, QRectF

# Constants for styling
POINT_COLOR = QColor(37, 99, 235)   # Tailwind blue-600
SEGMENT_COLOR = QColor(79, 70, 229) # Tailwind indigo-600
HIGHLIGHT_COLOR = QColor(239, 68, 68) # Tailwind red-500
POINT_SIZE = 8
SEGMENT_WIDTH = 2
HIGHLIGHT_WIDTH = 4

# Predefined SVG content for demonstration (a simple triangle path)
# pyembroidery will convert this path into a series of stitches.
DEFAULT_SVG_CONTENT = """
<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M 10 10 L 90 10 L 50 90 Z" fill="none" stroke="#3b82f6" stroke-width="2"/>
</svg>
"""

class StitchPointItem(QGraphicsEllipseItem):
    """
    Represents a single stitch point from the pyembroidery pattern.
    """
    def __init__(self, x, y, stitch_index, parent=None):
        super().__init__(x - POINT_SIZE / 2, y - POINT_SIZE / 2, POINT_SIZE, POINT_SIZE, parent)
        self.setBrush(QBrush(POINT_COLOR))
        self.setPen(QPen(Qt.NoPen))
        self.setFlags(QGraphicsEllipseItem.ItemIsSelectable)
        self.stitch_index = stitch_index
        self.setZValue(1) # Ensure points are drawn on top of lines

    def paint(self, painter, option, widget=None):
        """
        Paints the point, highlighting it if selected.
        """
        if self.isSelected():
            painter.setBrush(QBrush(HIGHLIGHT_COLOR))
        else:
            painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(self.rect())

    def mousePressEvent(self, event):
        """
        Handles mouse press for selection and prints stitch index.
        """
        if event.button() == Qt.LeftButton:
            self.setSelected(not self.isSelected()) # Toggle selection
            print(f"Clicked Stitch Point: Index {self.stitch_index}, Position ({self.pos().x()}, {self.pos().y()})")
            self.scene().update() # Request scene update to redraw selection
        super().mousePressEvent(event)

class PathSegmentItem(QGraphicsLineItem):
    """
    Represents a line segment connecting two stitch points.
    """
    def __init__(self, p1: QPointF, p2: QPointF, segment_index: int, parent=None):
        super().__init__(p1.x(), p1.y(), p2.x(), p2.y(), parent)
        self.setPen(QPen(SEGMENT_COLOR, SEGMENT_WIDTH))
        self.setFlags(QGraphicsLineItem.ItemIsSelectable)
        self.segment_index = segment_index
        self.setZValue(0) # Ensure lines are drawn below points

    def paint(self, painter, option, widget=None):
        """
        Paints the line segment, highlighting it if selected.
        """
        if self.isSelected():
            painter.setPen(QPen(HIGHLIGHT_COLOR, HIGHLIGHT_WIDTH))
        else:
            painter.setPen(self.pen())
        painter.drawLine(self.line())

    def mousePressEvent(self, event):
        """
        Handles mouse press for selection and prints segment index.
        """
        if event.button() == Qt.LeftButton:
            self.setSelected(not self.isSelected()) # Toggle selection
            print(f"Clicked Path Segment: Index {self.segment_index}, From ({self.line().p1().x()}, {self.line().p1().y()}) to ({self.line().p2().x()}, {self.line().p2().y()})")
            self.scene().update() # Request scene update to redraw selection
        super().mousePressEvent(event)


class CanvasWidget(QGraphicsView):
    """
    A QGraphicsView subclass that loads SVG content via pyembroidery
    and renders it as individual stitch points and segments.
    """
    def __init__(self, parent=None):
        super().__init__(QGraphicsScene(), parent)
        self.scene = self.scene()
        self.scene.setSceneRect(0, 0, 800, 600) # Set scene dimensions
        self.setRenderHint(QPainter.Antialiasing) # For smoother rendering
        self.setDragMode(QGraphicsView.NoDrag) # Disable default drag mode

        self.setFixedSize(800, 600) # Fixed size for the canvas view
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)

    def load_svg_as_segments(self, svg_content_bytes: str):
        """
        Parses SVG content using pyembroidery and adds individual
        stitch points and segments to the scene.
        """
        # Clear existing items from the scene
        self.scene.clear()

        # Create an EmbPattern from the SVG content
        pattern = pyembroidery.EmbPattern()
        try:
            # pyembroidery expects a file-like object for read_svg
            svg_file = io.StringIO(svg_content_bytes)
            pattern.read_svg(svg_file)
        except Exception as e:
            print(f"Error parsing SVG with pyembroidery: {e}")
            return

        if not pattern.stitches:
            print("No stitches found in SVG after parsing with pyembroidery.")
            return

        prev_point = None
        for i, stitch in enumerate(pattern.stitches):
            # pyembroidery stitches are (x, y, command_code)
            x, y, command = stitch[0], stitch[1], stitch[2]

            current_point = QPointF(x, y)

            # Add a segment (line) if there's a previous point and it's a valid draw command
            # pyembroidery.STITCH is a common command for drawing segments
            if prev_point and command == pyembroidery.STITCH:
                segment_item = PathSegmentItem(prev_point, current_point, i - 1)
                self.scene.addItem(segment_item)
            
            # Add the stitch point itself
            point_item = StitchPointItem(x, y, i)
            self.scene.addItem(point_item)

            prev_point = current_point

        self.scene.update() # Ensure scene updates to show new items


class MainWindow(QMainWindow):
    """
    The main application window, containing the canvas and a button to load SVG.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 SVG Segment Renderer")
        self.setGeometry(100, 100, 850, 750) # Adjusted window size

        self.canvas_widget = CanvasWidget()

        # Control button
        self.load_svg_btn = QPushButton("Load SVG Segments")

        # Connect button to load SVG function
        self.load_svg_btn.clicked.connect(lambda: self.canvas_widget.load_svg_as_segments(DEFAULT_SVG_CONTENT))

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.load_svg_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas_widget)
        main_layout.setAlignment(Qt.AlignCenter) # Center the content

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self._apply_styles()

    def _apply_styles(self):
        """
        Applies consistent styling to the main window and buttons.
        """
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5; /* Tailwind gray-100 */
                font-family: 'Inter', sans-serif;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease-in-out;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
                background-color: #4f46e5; /* Tailwind indigo-600 */
                color: white;
            }
            QPushButton:hover {
                background-color: #4338ca; /* Darker indigo on hover */
                transform: translateY(-1px);
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
