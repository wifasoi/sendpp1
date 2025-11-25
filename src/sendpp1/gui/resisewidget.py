import sys
from PySide6.QtWidgets import ( # Changed from PyQt5.QtWidgets
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsRectItem
)
from PySide6.QtGui import QBrush, QPen, QColor, QCursor, QPainter # Changed from PyQt5.QtGui, added QPainter
from PySide6.QtCore import Qt, QRectF, QPointF # Changed from PyQt5.QtCore

# Constants for styling
RECT_COLOR = QColor(59, 130, 246)  # Tailwind blue-500
SELECTION_COLOR = QColor(79, 70, 229) # Tailwind indigo-600
HANDLE_COLOR = QColor(37, 99, 235)   # Tailwind blue-600
HANDLE_SIZE = 10
SELECTION_BORDER_WIDTH = 2

class ResizableRectItem(QGraphicsRectItem):
    """
    A custom QGraphicsRectItem that supports selection, dragging, and resizing.
    """
    def __init__(self, x, y, width, height, parent=None):
        super().__init__(x, y, width, height, parent)
        self.setFlags(QGraphicsRectItem.ItemIsSelectable |
                      QGraphicsRectItem.ItemIsMovable |
                      QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) # Enable hover events for cursor changes

        self.setBrush(QBrush(RECT_COLOR))
        self.setPen(QPen(Qt.NoPen)) # Default no border

        self.is_resizing = False
        self.resize_handle = None # Stores which handle is being dragged (e.g., 'nw', 'ne', 'sw', 'se')
        self.last_mouse_pos = QPointF() # Stores the last mouse position for dragging/resizing

    def paint(self, painter, option, widget=None):
        """
        Paints the rectangle and its selection handles if selected.
        """
        # Paint the main rectangle
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(self.rect())

        # If selected, draw selection border and resize handles
        if self.isSelected():
            painter.setPen(QPen(SELECTION_COLOR, SELECTION_BORDER_WIDTH, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())

            painter.setBrush(QBrush(HANDLE_COLOR))
            painter.setPen(Qt.NoPen)
            handles = self._get_handles()
            for handle_pos in handles.values():
                painter.drawRect(handle_pos.x() - HANDLE_SIZE / 2,
                                 handle_pos.y() - HANDLE_SIZE / 2,
                                 HANDLE_SIZE, HANDLE_SIZE)

    def boundingRect(self):
        """
        Returns the bounding rectangle of the item, including selection handles.
        This is crucial for proper redraws and hit testing.
        """
        rect = super().boundingRect()
        if self.isSelected():
            # Expand bounding rect to include handles
            return rect.adjusted(-HANDLE_SIZE, -HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)
        return rect

    def _get_handles(self):
        """
        Calculates the positions of the resize handles.
        """
        rect = self.rect()
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
        Checks if a given position is over a resize handle.
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
                    self.last_mouse_pos = event.pos() # Store local position for resizing
                    event.accept()
                    return

            # If not resizing, let the default movable behavior handle dragging
            super().mousePressEvent(event)
            self.last_mouse_pos = event.pos() # Store local position for dragging

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events for dragging and resizing.
        """
        if self.is_resizing and self.resize_handle:
            delta = event.pos() - self.last_mouse_pos
            current_rect = self.rect()

            new_x = current_rect.x()
            new_y = current_rect.y()
            new_width = current_rect.width()
            new_height = current_rect.height()

            # Adjust dimensions based on the active handle
            if 'n' in self.resize_handle: # North handles
                new_y += delta.y()
                new_height -= delta.y()
            if 's' in self.resize_handle: # South handles
                new_height += delta.y()
            if 'w' in self.resize_handle: # West handles
                new_x += delta.x()
                new_width -= delta.x()
            if 'e' in self.resize_handle: # East handles
                new_width += delta.x()

            # Ensure minimum size
            min_size = HANDLE_SIZE * 2 # Prevent rectangles from collapsing too much
            new_width = max(min_size, new_width)
            new_height = max(min_size, new_height)

            # Adjust position if width/height changed due to west/north resize
            if 'w' in self.resize_handle and new_width == min_size:
                new_x = current_rect.x() + current_rect.width() - min_size
            if 'n' in self.resize_handle and new_height == min_size:
                new_y = current_rect.y() + current_rect.height() - min_size

            self.setRect(new_x, new_y, new_width, new_height)
            self.last_mouse_pos = event.pos()
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
            elif self.contains(event.pos()):
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
    A QGraphicsView subclass that manages drawing new rectangles
    and switching between draw and select modes.
    """
    def __init__(self, parent=None):
        super().__init__(QGraphicsScene(), parent)
        self.scene = self.scene()
        self.scene.setSceneRect(0, 0, 800, 600) # Set scene dimensions
        self.setRenderHint(QPainter.Antialiasing) # For smoother rendering
        self.setDragMode(QGraphicsView.NoDrag) # Default no drag, handled by items

        self.current_mode = 'draw' # 'draw' or 'select'
        self.drawing_rect = None # The rectangle being drawn
        self.start_pos = QPointF()

        self.setFixedSize(800, 600) # Fixed size for the canvas view
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)

    def set_mode(self, mode):
        """
        Sets the current interaction mode for the canvas.
        """
        self.current_mode = mode
        if mode == 'draw':
            self.setDragMode(QGraphicsView.NoDrag)
            # Deselect all items when switching to draw mode
            for item in self.scene.selectedItems():
                item.setSelected(False)
        elif mode == 'select':
            # Allow selection by rubberband in select mode
            self.setDragMode(QGraphicsView.RubberBandDrag)

    def mousePressEvent(self, event):
        """
        Handles mouse press events for drawing new rectangles.
        """
        if self.current_mode == 'draw' and event.button() == Qt.LeftButton:
            self.start_pos = self.mapToScene(event.pos())
            self.drawing_rect = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.drawing_rect.setPen(QPen(QColor(96, 165, 250), 1, Qt.DashLine)) # Blue-400 dashed
            self.drawing_rect.setBrush(Qt.NoBrush)
            self.scene.addItem(self.drawing_rect)
            event.accept()
        else:
            super().mousePressEvent(event) # Let QGraphicsView handle selection/item clicks

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events for drawing new rectangles.
        """
        if self.current_mode == 'draw' and self.drawing_rect:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.drawing_rect.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events to finalize drawing a new rectangle.
        """
        if self.current_mode == 'draw' and self.drawing_rect:
            end_pos = self.mapToScene(event.pos())
            final_rect = QRectF(self.start_pos, end_pos).normalized()

            # Remove the temporary drawing rect
            self.scene.removeItem(self.drawing_rect)
            self.drawing_rect = None

            if final_rect.width() > 0 and final_rect.height() > 0:
                # Add the actual resizable rectangle item
                new_item = ResizableRectItem(final_rect.x(), final_rect.y(),
                                             final_rect.width(), final_rect.height())
                self.scene.addItem(new_item)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class MainWindow(QMainWindow):
    """
    The main application window, containing the canvas and mode control buttons.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Canvas Transform Widget")
        self.setGeometry(100, 100, 850, 750) # Adjusted window size

        self.canvas_widget = CanvasWidget()

        # Control buttons
        self.draw_mode_btn = QPushButton("Draw Mode")
        self.select_mode_btn = QPushButton("Select Mode")

        self.draw_mode_btn.clicked.connect(lambda: self.set_app_mode('draw'))
        self.select_mode_btn.clicked.connect(lambda: self.set_app_mode('select'))

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.draw_mode_btn)
        control_layout.addWidget(self.select_mode_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas_widget)
        main_layout.setAlignment(Qt.AlignCenter) # Center the content

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.set_app_mode('draw') # Set initial mode
        self._apply_styles()

    def set_app_mode(self, mode):
        """
        Sets the application-wide interaction mode and updates button styles.
        """
        self.canvas_widget.set_mode(mode)
        if mode == 'draw':
            self.draw_mode_btn.setStyleSheet(self._get_button_style(active=True))
            self.select_mode_btn.setStyleSheet(self._get_button_style(active=False))
        else:
            self.draw_mode_btn.setStyleSheet(self._get_button_style(active=False))
            self.select_mode_btn.setStyleSheet(self._get_button_style(active=True))

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
        self.draw_mode_btn.setStyleSheet(self._get_button_style(active=True))
        self.select_mode_btn.setStyleSheet(self._get_button_style(active=False))

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
    # Load Inter font (assuming it's available on the system or can be loaded)
    # For a robust solution, you might need to bundle fonts or use QFontDatabase.addApplicationFont
    # from PySide6.QtGui import QFontDatabase
    # QFontDatabase.addApplicationFont("path/to/Inter-Regular.ttf")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) # Changed from app.exec_()


