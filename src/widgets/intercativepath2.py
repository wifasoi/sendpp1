import sys
from PySide6.QtCore import (
    Qt, QPointF, QVariantAnimation, QEasingCurve, Signal
)
from PySide6.QtGui import (
    QPolygonF, QPainterPath, QBrush, QColor, QPen
)
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QMenu, QAction
)

# -----------------------------
# External animation + styling logic
# -----------------------------

active_animations = {}


def animate_vertex_external(polygon_item, vertex_index, start_radius, end_radius, duration=200):
    """Animate a vertex's radius externally using QVariantAnimation."""
    anim = QVariantAnimation()
    anim.setStartValue(start_radius)
    anim.setEndValue(end_radius)
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def on_value_changed(value):
        polygon_item.vertex_radii[vertex_index] = value
        polygon_item.update()

    anim.valueChanged.connect(on_value_changed)

    def on_finished():
        active_animations.pop(vertex_index, None)
        anim.deleteLater()

    anim.finished.connect(on_finished)
    anim.start()
    active_animations[vertex_index] = anim


def stylize_vertex(polygon_item, vertex_index, color=None, outline=None):
    """Apply external styling to a vertex (color or outline)."""
    if color:
        polygon_item.vertex_colors[vertex_index] = QColor(color)
    if outline is not None:
        polygon_item.vertex_outlines[vertex_index] = outline
    polygon_item.update()


# -----------------------------
# Interactive Polygon Item
# -----------------------------
class 

class InteractivePolygonItem(QGraphicsPathItem):
    vertexHovered = Signal(int)
    vertexUnhovered = Signal(int)
    vertexClicked = Signal(int)
    vertexSelected = Signal(int)

    def __init__(self, polygon, parent=None):
        super().__init__(parent)
        self.polygon = polygon
        self.hovered_vertex = None
        self.selected_vertex = None
        self.vertex_radii = [3.0 for _ in range(len(polygon))]
        self.vertex_colors = [QColor(255, 0, 0) for _ in range(len(polygon))]
        self.vertex_outlines = [None for _ in range(len(polygon))]

        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(100, 200, 255, 80)))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.updatePath()

    def updatePath(self):
        path = QPainterPath()
        path.addPolygon(self.polygon)
        self.setPath(path)
        self.update()

    def paint(self, painter, option, widget):
        """Draw polygon and vertices."""
        super().paint(painter, option, widget)
        for i, pt in enumerate(self.polygon):
            color = self.vertex_colors[i]
            radius = self.vertex_radii[i]

            painter.setBrush(QBrush(color))
            if self.vertex_outlines[i]:
                pen = QPen(QColor(self.vertex_outlines[i]), 2)
            else:
                pen = Qt.PenStyle.NoPen
            painter.setPen(pen)
            painter.drawEllipse(pt, radius, radius)

    def findClosestVertex(self, point, radius=8):
        for i, vertex in enumerate(self.polygon):
            if (vertex - point).manhattanLength() < radius:
                return i
        return None

    def hoverMoveEvent(self, event):
        pos = event.pos()
        new_hover = self.findClosestVertex(pos, radius=8)
        if new_hover != self.hovered_vertex:
            old_hover = self.hovered_vertex
            self.hovered_vertex = new_hover

            if old_hover is not None:
                self.vertexUnhovered.emit(old_hover)
            if new_hover is not None:
                self.vertexHovered.emit(new_hover)

    def hoverLeaveEvent(self, event):
        if self.hovered_vertex is not None:
            self.vertexUnhovered.emit(self.hovered_vertex)
            self.hovered_vertex = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.findClosestVertex(event.pos())
            if idx is not None:
                self.selected_vertex = idx
                self.vertexSelected.emit(idx)
                self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            idx = self.findClosestVertex(event.pos())
            if idx is not None:
                self.showContextMenu(event.screenPos(), idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def showContextMenu(self, global_pos, vertex_index):
        menu = QMenu()
        vertex = self.polygon[vertex_index]
        info_action = QAction(f"Vertex {vertex_index}: ({vertex.x():.1f}, {vertex.y():.1f})", menu)
        menu.addAction(info_action)
        delete_action = QAction("Delete vertex", menu)
        delete_action.triggered.connect(lambda: self.deleteVertex(vertex_index))
        menu.addAction(delete_action)
        menu.exec(global_pos)

    def deleteVertex(self, index):
        if 0 <= index < len(self.polygon):
            self.polygon.remove(index)
            self.vertex_radii.pop(index)
            self.vertex_colors.pop(index)
            self.vertex_outlines.pop(index)
            self.updatePath()


# -----------------------------
# Main View (connects signals)
# -----------------------------

class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()
        scene = QGraphicsScene()
        self.setScene(scene)

        polygon = QPolygonF([
            QPointF(50, 50),
            QPointF(150, 50),
            QPointF(150, 150),
            QPointF(100, 200),
            QPointF(50, 150)
        ])

        item = InteractivePolygonItem(polygon)
        scene.addItem(item)

        # --- External connections for animation + styling ---
        item.vertexHovered.connect(
            lambda i: (
                animate_vertex_external(item, i, item.vertex_radii[i], 6.0),
                stylize_vertex(item, i, color="#ff5050", outline="orange")
            )
        )

        item.vertexUnhovered.connect(
            lambda i: (
                animate_vertex_external(item, i, item.vertex_radii[i], 3.0),
                stylize_vertex(item, i, color="#ff0000", outline=None)
            )
        )

        item.vertexSelected.connect(
            lambda i: stylize_vertex(item, i, color="#00ff00", outline="black")
        )

        self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.setWindowTitle("External Styling + Animation via Signals (PySide6)")


# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = MainView()
    view.resize(400, 300)
    view.show()
    sys.exit(app.exec())
