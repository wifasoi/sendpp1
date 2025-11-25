import sys
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QMenu, QAction
)
from PySide6.QtGui import QPainterPath, QPolygonF, QBrush, QColor, QPen
from PySide6.QtCore import QPointF, Qt


class InteractivePolygonItem(QGraphicsPathItem):
    def __init__(self, polygon, parent=None):
        super().__init__(parent)
        self.polygon = polygon
        self.hovered_vertex = None  # Index of hovered vertex
        self.setAcceptHoverEvents(True)

        self.setBrush(QBrush(QColor(100, 200, 255, 80)))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.updatePath()

    def updatePath(self):
        path = QPainterPath()
        path.addPolygon(self.polygon)
        path.closeSubpath()
        self.setPath(path)
        self.update()

    def paint(self, painter, option, widget):
        """Draw polygon + small circles at each vertex."""
        super().paint(painter, option, widget)

        for i, pt in enumerate(self.polygon):
            # Default radius and color
            radius = 3
            color = QColor(255, 0, 0)

            # Enlarge + recolor hovered vertex
            if i == self.hovered_vertex:
                radius = 6
                color = QColor(255, 80, 80)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt, radius, radius)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        new_hover = self.findClosestVertex(pos, radius=8)
        if new_hover != self.hovered_vertex:
            self.hovered_vertex = new_hover
            self.update()

    def hoverLeaveEvent(self, event):
        """Reset highlight when mouse leaves polygon area."""
        if self.hovered_vertex is not None:
            self.hovered_vertex = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            clicked_point = event.pos()
            idx = self.findClosestVertex(clicked_point)
            if idx is not None:
                self.showContextMenu(event.screenPos(), idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def findClosestVertex(self, point, radius=8):
        """Return index of vertex if within radius, else None"""
        for i, vertex in enumerate(self.polygon):
            if (vertex - point).manhattanLength() < radius:
                return i
        return None

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
            self.updatePath()


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

        self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.setWindowTitle("Polygon with Hover-Responsive Points (PySide6)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = MainView()
    view.resize(400, 300)
    view.show()
    sys.exit(app.exec())
