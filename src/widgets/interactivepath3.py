import sys
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QGraphicsEllipseItem
)
from PySide6.QtGui import QPolygonF, QPainterPath, QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QVariantAnimation, QEasingCurve, Signal

# -----------------------------
# Vertex Item
# -----------------------------
class VertexItem(QGraphicsEllipseItem):
    hovered = Signal(object)
    unhovered = Signal(object)
    clicked = Signal(object)

    def __init__(self, pos: QPointF, radius=3.0, color=QColor(255,0,0)):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.setPos(pos)
        self.radius = radius
        self.base_radius = radius
        self.color = color
        self.setBrush(QBrush(self.color))
        self.setPen(Qt.PenStyle.NoPen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.anim = None

    def hoverEnterEvent(self, event):
        self.hovered.emit(self)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.unhovered.emit(self)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def animate_radius(self, target_radius, duration=200):
        if self.anim:
            self.anim.stop()
        self.anim = QVariantAnimation()
        self.anim.setStartValue(self.radius)
        self.anim.setEndValue(target_radius)
        self.anim.setDuration(duration)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_value_changed(value):
            self.radius = value
            self.setRect(-value, -value, value*2, value*2)

        self.anim.valueChanged.connect(on_value_changed)
        self.anim.start()


# -----------------------------
# Polygon Item with automatic vertices
# -----------------------------
class PolygonItem(QGraphicsPathItem):
    def __init__(self, polygon: QPolygonF, parent=None):
        super().__init__(parent)
        self.polygon = polygon
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(QColor(100,200,255,80)))
        self.updatePath()

        # Instantiate vertices
        self.vertices = []
        for pt in self.polygon:
            v = VertexItem(pt)
            v.setParentItem(self)  # attach to polygon item
            self.vertices.append(v)

# -----------------------------
# Main View
# -----------------------------
class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()
        scene = QGraphicsScene()
        self.setScene(scene)

        polygon = QPolygonF([
            QPointF(50,50),
            QPointF(150,50),
            QPointF(150,150),
            QPointF(100,200),
            QPointF(50,150)
        ])

        self.poly_item = PolygonItem(polygon)
        scene.addItem(self.poly_item)

        # Connect vertex signals externally
        for v in self.poly_item.vertices:
            v.hovered.connect(self.on_vertex_hovered)
            v.unhovered.connect(self.on_vertex_unhovered)
            v.clicked.connect(self.on_vertex_clicked)

        self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.setWindowTitle("PolygonItem with Automatic Vertices")

    def on_vertex_hovered(self, vertex):
        vertex.animate_radius(6)
        vertex.setBrush(QBrush(QColor(255,80,80)))

    def on_vertex_unhovered(self, vertex):
        vertex.animate_radius(3)
        vertex.setBrush(QBrush(QColor(255,0,0)))

    def on_vertex_clicked(self, vertex):
        vertex.setBrush(QBrush(QColor(0,255,0)))

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = MainView()
    view.resize(400,300)
    view.show()
    sys.exit(app.exec())
