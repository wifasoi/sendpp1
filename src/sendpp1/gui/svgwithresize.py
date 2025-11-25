import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsRectItem
)
from PySide6.QtGui import QBrush, QPen, QColor, QCursor, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF, QByteArray # Added QSizeF, QByteArray
from PySide6.QtSvg import QSvgRenderer # Added QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem # Added QGraphicsSvgItem

# Constants for styling
RECT_COLOR = QColor(59, 130, 246)  # Tailwind blue-500 (used for default SVG fill if not specified in SVG)
SELECTION_COLOR = QColor(79, 70, 229) # Tailwind indigo-600
HANDLE_COLOR = QColor(37, 99, 235)   # Tailwind blue-600
HANDLE_SIZE = 10
SELECTION_BORDER_WIDTH = 2

# Predefined SVG content for demonstration (a simple blue circle)
# This SVG will be loaded when the "Load SVG" button is clicked.
DEFAULT_SVG_CONTENT = """
<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" fill="#3b82f6" stroke="#1d4ed8" stroke-width="5"/>
</svg>
"""

class ResizableSvgItem(QGraphicsSvgItem): # Changed base class to QGraphicsSvgItem
    """
    A custom QGraphicsSvgItem that supports selection, dragging, and resizing.
    """
    def __init__(self, svg_content_bytes, parent=None):
        # Initialize with a QSvgRenderer
        self._svg_renderer = QSvgRenderer(QByteArray(svg_content_bytes))
        super().__init__(parent)
        self.setSharedRenderer(self._svg_renderer) # Set the renderer for this item

        self.setFlags(QGraphicsSvgItem.ItemIsSelectable |
                      QGraphicsSvgItem.ItemIsMovable |
                      QGraphicsSvgItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) # Enable hover events for cursor changes

        # Store original SVG bounds for scaling calculations
        self._original_svg_bounds = self._svg_renderer.bounds()

        self.is_resizing = False
        self.resize_handle = None # Stores which handle is being dragged (e.g., 'nw', 'ne', 'sw', 'se')

        # Variables for resizing logic
        self._initial_scale = 1.0
        self._initial_mouse_pos_scene = QPointF()
        self._initial_item_rect_scene = QRectF()
        self._initial_item_pos = QPointF()


    def paint(self, painter, option, widget=None):
        """
        Paints the SVG item and its selection handles if selected.
        """
        # Paint the main SVG item using the base class method
        super().paint(painter, option, widget)

        # If selected, draw selection border and resize handles
        if self.isSelected():
            painter.setPen(QPen(SELECTION_COLOR, SELECTION_BORDER_WIDTH, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            # Use the item's current bounding rect (which is already scaled)
            painter.drawRect(self.boundingRect())

            painter.setBrush(QBrush(HANDLE_COLOR))
            painter.setPen(Qt.NoPen)
            handles = self._get_handles()
            for handle_pos in handles.values():
                # Handles are drawn in local coordinates relative to the item
                painter.drawRect(handle_pos.x() - HANDLE_SIZE / 2,
                                 handle_pos.y() - HANDLE_SIZE / 2,
                                 HANDLE_SIZE, HANDLE_SIZE)

    def boundingRect(self):
        """
        Returns the bounding rectangle of the item, including selection handles.
        This is crucial for proper redraws and hit testing.
        """
        # Get the base item's bounding rect (which is the scaled SVG bounds)
        rect = super().boundingRect()
        if self.isSelected():
            # Expand bounding rect to include handles
            return rect.adjusted(-HANDLE_SIZE, -HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)
        return rect

    def _get_handles(self):
        """
        Calculates the positions of the resize handles in local coordinates.
        """
        # Use the item's current bounding rectangle (which is scaled)
        rect = self.boundingRect()
        x1, y1 = rect.x(), rect.y()
        x2, y2 = rect.x() + rect.width(), rect.y() + rect.height()

        return {
            'nw': QPointF(x1, y1),
            'ne': QPointF(x2, y1),
            'sw': QPointF(x1, y2),
            'se': QPointF(x2, y2)
        }

    def _get_handle_at_pos(self, pos):
        """
        Checks if a given position (in local coordinates) is over a resize handle.
        Returns the handle name ('nw', etc.) or None.
        """
        handles = self._get_handles()
        for key, handle_pos in handles.items():
            handle_rect = QRectF(handle_pos.x() - HANDLE_SIZE / 2,
                                 handle_pos.y() - HANDLE_SIZE / 2,
                                 HANDLE_SIZE, HANDLE_SIZE)
            if handle_rect.contains(pos):
                return key
        return None

    def mousePressEvent(self, event):
        """
        Handles mouse press events for dragging and resizing.
        """
        if event.button() == Qt.LeftButton:
            if self.isSelected():
                self.resize_handle = self._get_handle_at_pos(event.pos())
                if self.resize_handle:
                    self.is_resizing = True
                    # Store initial state for resizing
                    self._initial_scale = self.scale()
                    self._initial_mouse_pos_scene = event.scenePos()
                    self._initial_item_rect_scene = self.sceneBoundingRect() # Rect in scene coordinates
                    self._initial_item_pos = self.pos() # Item's top-left position in parent coordinates

                    # Set the transform origin point to the opposite corner for scaling
                    fixed_point_scene = QPointF()
                    if self.resize_handle == 'nw':
                        fixed_point_scene = self._initial_item_rect_scene.bottomRight()
                    elif self.resize_handle == 'ne':
                        fixed_point_scene = self._initial_item_rect_scene.bottomLeft()
                    elif self.resize_handle == 'sw':
                        fixed_point_scene = self._initial_item_rect_scene.topRight()
                    elif self.resize_handle == 'se':
                        fixed_point_scene = self._initial_item_rect_scene.topLeft()

                    # Map the fixed point from scene coordinates to the item's local coordinates
                    fixed_point_local = self.mapFromScene(fixed_point_scene)
                    self.setTransformOriginPoint(fixed_point_local)

                    event.accept()
                    return

            # If not resizing, let the default movable behavior handle dragging
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events for dragging and resizing.
        """
        if self.is_resizing and self.resize_handle:
            current_mouse_pos_scene = event.scenePos()
            delta_scene = current_mouse_pos_scene - self._initial_mouse_pos_scene

            # Calculate new width/height based on mouse movement and initial dimensions
            current_item_width_scene = self._initial_item_rect_scene.width()
            current_item_height_scene = self._initial_item_rect_scene.height()

            new_width_candidate = current_item_width_scene
            new_height_candidate = current_item_height_scene

            if 'w' in self.resize_handle:
                new_width_candidate -= delta_scene.x()
            elif 'e' in self.resize_handle:
                new_width_candidate += delta_scene.x()

            if 'n' in self.resize_handle:
                new_height_candidate -= delta_scene.y()
            elif 's' in self.resize_handle:
                new_height_candidate += delta_scene.y()

            # Ensure minimum size
            new_width_candidate = max(HANDLE_SIZE * 2, new_width_candidate)
            new_height_candidate = max(HANDLE_SIZE * 2, new_height_candidate)

            # Calculate new scale factor
            # Use original SVG bounds for ratio calculation
            scale_x = new_width_candidate / self._original_svg_bounds.width()
            scale_y = new_height_candidate / self._original_svg_bounds.height()

            # Maintain aspect ratio by taking the average scale factor
            new_scale = (scale_x + scale_y) / 2
            new_scale = max(0.1, new_scale) # Prevent scale from becoming too small

            self.setScale(new_scale) # Apply the new scale
            self.update() # Request a repaint
            event.accept()
        else:
            # If not resizing, let the default movable behavior handle dragging
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events to stop dragging or resizing.
        """
        if event.button() == Qt.LeftButton:
            self.is_resizing = False
            self.resize_handle = None
            # Reset transform origin point to the center of the item for future operations
            self.setTransformOriginPoint(self.boundingRect().center())
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """
        Changes the cursor based on whether the mouse is over a handle or the item body.
        """
        if self.isSelected():
            handle = self._get_handle_at_pos(event.pos())
            if handle:
                # Set specific resize cursors
                if handle in ['nw', 'se']:
                    self.setCursor(Qt.SizeFDiagCursor)
                elif handle in ['ne', 'sw']:
                    self.setCursor(Qt.SizeBDiagCursor)
                return
            # Check if mouse is over the item itself for moving
            elif self.boundingRect().contains(event.pos()):
                self.setCursor(Qt.SizeAllCursor) # Move cursor
                return
        self.setCursor(Qt.ArrowCursor) # Default cursor
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Resets the cursor when the mouse leaves the item.
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)


class CanvasWidget(QGraphicsView):
    """
    A QGraphicsView subclass that manages adding new SVG items
    and switching between select mode.
    """
    def __init__(self, parent=None):
        super().__init__(QGraphicsScene(), parent)
        self.scene = self.scene()
        self.scene.setSceneRect(0, 0, 800, 600) # Set scene dimensions
        self.setRenderHint(QPainter.Antialiasing) # For smoother rendering
        self.setDragMode(QGraphicsView.RubberBandDrag) # Default to rubber band selection

        self.current_mode = 'select' # Default mode is select

        self.setFixedSize(800, 600) # Fixed size for the canvas view
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)

    def add_svg_item(self, svg_content_bytes, pos=QPointF(50, 50)):
        """
        Adds a new ResizableSvgItem to the scene.
        """
        new_item = ResizableSvgItem(svg_content_bytes)
        self.scene.addItem(new_item)
        new_item.setPos(pos)
        self.scene.update() # Ensure scene updates to show new item

    # mousePressEvent, mouseMoveEvent, mouseReleaseEvent for drawing are removed
    # as the canvas now focuses on loading and manipulating SVGs.
    # QGraphicsView's default behavior handles item selection and movement.


class MainWindow(QMainWindow):
    """
    The main application window, containing the canvas and mode control buttons.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Canvas Transform Widget (SVG)")
        self.setGeometry(100, 100, 850, 750) # Adjusted window size

        self.canvas_widget = CanvasWidget()

        # Control buttons
        self.load_svg_btn = QPushButton("Load SVG")
        self.select_mode_btn = QPushButton("Select Mode") # Renamed from draw_mode_btn

        self.load_svg_btn.clicked.connect(lambda: self.canvas_widget.add_svg_item(DEFAULT_SVG_CONTENT))
        self.select_mode_btn.clicked.connect(lambda: self.set_app_mode('select'))

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.load_svg_btn)
        control_layout.addWidget(self.select_mode_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas_widget)
        main_layout.setAlignment(Qt.AlignCenter) # Center the content

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.set_app_mode('select') # Set initial mode to select
        self._apply_styles()

    def set_app_mode(self, mode):
        """
        Sets the application-wide interaction mode and updates button styles.
        """
        # In this version, the canvas only supports 'select' mode for item interaction
        # The 'load_svg_btn' directly adds an item, it doesn't change a mode.
        if mode == 'select':
            self.canvas_widget.setDragMode(QGraphicsView.RubberBandDrag)
            self.select_mode_btn.setStyleSheet(self._get_button_style(active=True))
            self.load_svg_btn.setStyleSheet(self._get_button_style(active=False)) # Load button is not a mode button
        else:
            # Fallback or future modes
            self.select_mode_btn.setStyleSheet(self._get_button_style(active=False))
            self.load_svg_btn.setStyleSheet(self._get_button_style(active=False))

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
            }
        """)
        # Initial button styles
        self.select_mode_btn.setStyleSheet(self._get_button_style(active=True))
        self.load_svg_btn.setStyleSheet(self._get_button_style(active=False))

    def _get_button_style(self, active):
        """
        Returns the CSS style string for a button based on its active state.
        """
        if active:
            return """
                QPushButton {
                    background-color: #2563eb; /* Tailwind blue-600 */
                    color: white;
                    box-shadow: inset 0px 2px 4px rgba(0, 0, 0, 0.2);
                }
                QPushButton:hover {
                    background-color: #1e40af; /* Darker blue on hover */
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #e2e8f0; /* Tailwind gray-200 */
                    color: #334155; /* Tailwind slate-700 */
                }
                QPushButton:hover {
                    background-color: #cbd5e1; /* Darker gray on hover */
                }
            """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
