import sys
import io
import pyembroidery # Import pyembroidery
import math # For rotation calculations

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsItemGroup # Added QGraphicsItemGroup
)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QTransform # Added QTransform
from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF

# Constants for styling
POINT_COLOR = QColor(37, 99, 235)   # Tailwind blue-600
SEGMENT_COLOR = QColor(79, 70, 229) # Tailwind indigo-600
HIGHLIGHT_COLOR = QColor(239, 68, 68) # Tailwind red-500 (for selected points/segments)
GROUP_SELECTION_COLOR = QColor(79, 70, 229) # Tailwind indigo-600 (for selected group border)
HANDLE_COLOR = QColor(37, 99, 235)   # Tailwind blue-600 (for group transform handles)
POINT_SIZE = 8
SEGMENT_WIDTH = 2
HIGHLIGHT_WIDTH = 4
HANDLE_SIZE = 10
ROTATION_HANDLE_OFFSET = 25 # Distance of rotation handle from top center

# Predefined SVG content for demonstration (a simple triangle path)
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
        self.setFlags(QGraphicsEllipseItem.ItemIsSelectable) # Still selectable for individual highlight
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
        self.setFlags(QGraphicsLineItem.ItemIsSelectable) # Still selectable for individual highlight
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


class TransformableSvgGroup(QGraphicsItemGroup):
    """
    A QGraphicsItemGroup that allows scaling, rotation, and moving of its children.
    It draws a selection box, resize handles, and a rotation handle.
    """
    def __init__(self, items, parent=None):
        super().__init__(parent)
        for item in items:
            self.addToGroup(item)

        self.setFlags(QGraphicsItemGroup.ItemIsSelectable |
                      QGraphicsItemGroup.ItemIsMovable |
                      QGraphicsItemGroup.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self.is_resizing = False
        self.is_rotating = False
        self.resize_handle = None # 'nw', 'ne', 'sw', 'se'
        self.last_mouse_pos_scene = QPointF()

        # Store initial state for transformations
        self._initial_transform = QTransform()
        self._initial_group_rect_scene = QRectF()
        self._initial_mouse_pos_scene_for_transform = QPointF()
        self._initial_angle = 0.0

    def paint(self, painter, option, widget=None):
        """
        Paints the group's children and its selection/transform controls if selected.
        """
        # Paint children first
        super().paint(painter, option, widget)

        if self.isSelected():
            # Get the bounding rect of the group in its own local coordinates
            # This accounts for current scale/rotation of the group itself
            group_rect = self.childrenBoundingRect()

            # Draw selection border
            painter.setPen(QPen(GROUP_SELECTION_COLOR, SELECTION_BORDER_WIDTH, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(group_rect)

            # Draw resize handles
            painter.setBrush(QBrush(HANDLE_COLOR))
            painter.setPen(Qt.NoPen)
            handles = self._get_handles(group_rect)
            for handle_pos in handles.values():
                painter.drawRect(handle_pos.x() - HANDLE_SIZE / 2,
                                 handle_pos.y() - HANDLE_SIZE / 2,
                                 HANDLE_SIZE, HANDLE_SIZE)

            # Draw rotation handle
            rotation_handle_pos = self._get_rotation_handle_pos(group_rect)
            painter.drawEllipse(rotation_handle_pos.x() - HANDLE_SIZE / 2,
                                rotation_handle_pos.y() - HANDLE_SIZE / 2,
                                HANDLE_SIZE, HANDLE_SIZE)

            # Draw line from center to rotation handle
            painter.setPen(QPen(HANDLE_COLOR, 1, Qt.DotLine))
            painter.drawLine(group_rect.center(), rotation_handle_pos)

    def boundingRect(self):
        """
        Returns the bounding rectangle of the item, including selection handles
        and rotation handle.
        """
        # Get the bounding rect of children in local coordinates
        rect = self.childrenBoundingRect()
        if self.isSelected():
            # Expand bounding rect to include handles and rotation handle
            # Need to consider the rotation handle's offset
            expanded_rect = rect.adjusted(-HANDLE_SIZE, -HANDLE_SIZE - ROTATION_HANDLE_OFFSET,
                                          HANDLE_SIZE, HANDLE_SIZE)
            return expanded_rect
        return rect

    def _get_handles(self, group_rect: QRectF):
        """
        Calculates the positions of the resize handles in local coordinates.
        """
        x1, y1 = group_rect.x(), group_rect.y()
        x2, y2 = group_rect.x() + group_rect.width(), group_rect.y() + group_rect.height()

        return {
            'nw': QPointF(x1, y1),
            'ne': QPointF(x2, y1),
            'sw': QPointF(x1, y2),
            'se': QPointF(x2, y2)
        }

    def _get_rotation_handle_pos(self, group_rect: QRectF):
        """
        Calculates the position of the rotation handle in local coordinates.
        """
        top_center = QPointF(group_rect.center().x(), group_rect.y())
        return QPointF(top_center.x(), top_center.y() - ROTATION_HANDLE_OFFSET)

    def _get_handle_at_pos(self, pos: QPointF):
        """
        Checks if a given position (in local coordinates) is over a resize handle.
        Returns the handle name ('nw', etc.) or 'rotate' or None.
        """
        group_rect = self.childrenBoundingRect()
        handles = self._get_handles(group_rect)
        for key, handle_pos in handles.items():
            handle_rect = QRectF(handle_pos.x() - HANDLE_SIZE / 2,
                                 handle_pos.y() - HANDLE_SIZE / 2,
                                 HANDLE_SIZE, HANDLE_SIZE)
            if handle_rect.contains(pos):
                return key

        # Check rotation handle
        rotation_handle_pos = self._get_rotation_handle_pos(group_rect)
        rotation_handle_rect = QRectF(rotation_handle_pos.x() - HANDLE_SIZE / 2,
                                      rotation_handle_pos.y() - HANDLE_SIZE / 2,
                                      HANDLE_SIZE, HANDLE_SIZE)
        if rotation_handle_rect.contains(pos):
            return 'rotate'

        return None

    def mousePressEvent(self, event):
        """
        Handles mouse press events for dragging, resizing, and rotating.
        """
        if event.button() == Qt.LeftButton:
            if self.isSelected():
                self.resize_handle = self._get_handle_at_pos(event.pos())
                if self.resize_handle:
                    if self.resize_handle == 'rotate':
                        self.is_rotating = True
                        self._initial_angle = self.rotation()
                        self._initial_mouse_pos_scene_for_transform = event.scenePos()
                        # Set transform origin to center for rotation
                        self.setTransformOriginPoint(self.childrenBoundingRect().center())
                    else:
                        self.is_resizing = True
                        self._initial_transform = self.transform() # Store current transform
                        self._initial_group_rect_scene = self.sceneBoundingRect() # Rect in scene coordinates
                        self._initial_mouse_pos_scene_for_transform = event.scenePos()

                        # Set transform origin point to the opposite corner for scaling
                        fixed_point_scene = QPointF()
                        if self.resize_handle == 'nw':
                            fixed_point_scene = self._initial_group_rect_scene.bottomRight()
                        elif self.resize_handle == 'ne':
                            fixed_point_scene = self._initial_group_rect_scene.bottomLeft()
                        elif self.resize_handle == 'sw':
                            fixed_point_scene = self._initial_group_rect_scene.topRight()
                        elif self.resize_handle == 'se':
                            fixed_point_scene = self._initial_group_rect_scene.topLeft()

                        # Map the fixed point from scene coordinates to the item's local coordinates
                        fixed_point_local = self.mapFromScene(fixed_point_scene)
                        self.setTransformOriginPoint(fixed_point_local)
                    event.accept()
                    return # Handled by custom logic

            # If not resizing or rotating, let the default movable behavior handle dragging
            super().mousePressEvent(event)
            self.last_mouse_pos_scene = event.scenePos() # Store scene position for moving

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events for dragging, resizing, and rotating.
        """
        if self.is_resizing and self.resize_handle:
            current_mouse_pos_scene = event.scenePos()
            delta_scene = current_mouse_pos_scene - self._initial_mouse_pos_scene_for_transform

            # Get the current dimensions of the group in scene coordinates
            current_group_width_scene = self._initial_group_rect_scene.width()
            current_group_height_scene = self._initial_group_rect_scene.height()

            new_width_candidate = current_group_width_scene
            new_height_candidate = current_group_height_scene

            # Adjust dimensions based on the active handle
            if 'w' in self.resize_handle:
                new_width_candidate -= delta_scene.x()
            elif 'e' in self.resize_handle:
                new_width_candidate += delta_scene.x()

            if 'n' in self.resize_handle:
                new_height_candidate -= delta_scene.y()
            elif 's' in self.resize_handle:
                new_height_candidate += delta_scene.y()

            # Ensure minimum size
            min_size = HANDLE_SIZE * 2
            new_width_candidate = max(min_size, new_width_candidate)
            new_height_candidate = max(min_size, new_height_candidate)

            # Calculate new scale factor based on original content dimensions
            # Use the childrenBoundingRect() to get the actual content dimensions before any scaling
            original_content_width = self.childrenBoundingRect().width() / self.scale()
            original_content_height = self.childrenBoundingRect().height() / self.scale()

            if original_content_width == 0 or original_content_height == 0:
                return # Avoid division by zero if content is empty

            scale_x = new_width_candidate / original_content_width
            scale_y = new_height_candidate / original_content_height

            # Maintain aspect ratio by taking the average scale factor
            new_scale = (scale_x + scale_y) / 2
            new_scale = max(0.1, new_scale) # Prevent scale from becoming too small

            self.setScale(new_scale)
            self.update() # Request a repaint
            event.accept()

        elif self.is_rotating:
            group_center_scene = self.mapToScene(self.childrenBoundingRect().center())
            current_mouse_pos_scene = event.scenePos()

            # Calculate vectors from center to mouse positions
            vec_initial = self._initial_mouse_pos_scene_for_transform - group_center_scene
            vec_current = current_mouse_pos_scene - group_center_scene

            # Calculate angles
            angle_initial = math.degrees(math.atan2(vec_initial.y(), vec_initial.x()))
            angle_current = math.degrees(math.atan2(vec_current.y(), vec_current.x()))

            # Calculate rotation delta
            rotation_delta = angle_current - angle_initial

            self.setRotation(self._initial_angle + rotation_delta)
            self.update()
            event.accept()

        else:
            # If not resizing or rotating, let the default movable behavior handle dragging
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events to stop dragging, resizing, or rotating.
        """
        if event.button() == Qt.LeftButton:
            self.is_resizing = False
            self.is_rotating = False
            self.resize_handle = None
            # Reset transform origin point to the center of the item for future operations
            self.setTransformOriginPoint(self.childrenBoundingRect().center())
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """
        Changes the cursor based on whether the mouse is over a handle or the item body.
        """
        if self.isSelected():
            handle = self._get_handle_at_pos(event.pos())
            if handle:
                if handle == 'rotate':
                    self.setCursor(Qt.CrossCursor) # Or a custom rotation cursor
                elif handle in ['nw', 'se']:
                    self.setCursor(Qt.SizeFDiagCursor)
                elif handle in ['ne', 'sw']:
                    self.setCursor(Qt.SizeBDiagCursor)
                return
            # Check if mouse is over the item itself for moving
            elif self.childrenBoundingRect().contains(event.pos()):
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
    A QGraphicsView subclass that loads SVG content via pyembroidery
    and renders it as a transformable group of individual stitch points and segments.
    """
    def __init__(self, parent=None):
        super().__init__(QGraphicsScene(), parent)
        self.scene = self.scene()
        self.scene.setSceneRect(0, 0, 800, 600) # Initial scene dimensions, will adapt
        self.setRenderHint(QPainter.Antialiasing) # For smoother rendering
        self.setDragMode(QGraphicsView.RubberBandDrag) # Enable rubber band selection for groups

        # Allow the widget to resize with the window
        self.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Expanding, # Changed from QtWidgets.QSizePolicy.Expanding
            PySide6.QtWidgets.QSizePolicy.Expanding  # Changed from QtWidgets.QSizePolicy.Expanding
        )
        # Removed setFixedSize(800, 600)

        self.setStyleSheet("""
            QGraphicsView {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)

    def resizeEvent(self, event):
        """
        Adjusts the scene rectangle to match the view's new size on resize.
        """
        self.scene.setSceneRect(self.rect())
        super().resizeEvent(event)

    def load_svg_as_segments(self, svg_content_bytes: str):
        """
        Parses SVG content using pyembroidery and adds a single
        TransformableSvgGroup containing all stitch points and segments to the scene.
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

        # Collect all items to be added to the group
        group_items = []
        prev_point = None
        for i, stitch in enumerate(pattern.stitches):
            # pyembroidery stitches are (x, y, command_code)
            x, y, command = stitch[0], stitch[1], stitch[2]

            current_point = QPointF(x, y)

            # Add a segment (line) if there's a previous point and it's a valid draw command
            if prev_point and command == pyembroidery.STITCH:
                segment_item = PathSegmentItem(prev_point, current_point, i - 1)
                group_items.append(segment_item)
            
            # Add the stitch point itself
            point_item = StitchPointItem(x, y, i)
            group_items.append(point_item)

            prev_point = current_point

        if group_items:
            # Create a single transformable group for all parsed SVG elements
            svg_group = TransformableSvgGroup(group_items)
            self.scene.addItem(svg_group)

            # Center the group in the scene initially
            group_bounds = svg_group.childrenBoundingRect()
            scene_center = self.scene.sceneRect().center()
            group_center = svg_bounds.center() # Changed from group_bounds.center() to svg_bounds.center()
            svg_group.setPos(scene_center - group_center) # Changed from group_bounds.center() to svg_bounds.center()
            
            # Select the group by default
            svg_group.setSelected(True)

        self.scene.update() # Ensure scene updates to show new items


class MainWindow(QMainWindow):
    """
    The main application window, containing the canvas and a button to load SVG.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 SVG Renderer with Transformable Group")
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
