import sys
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QGraphicsEllipseItem
)
from PySide6.QtGui import QPolygonF, QPainterPath, QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QVariantAnimation, QPropertyAnimation, QEasingCurve, Signal,QObject, QEvent, Property

# -----------------------------
# Vertex Item
# -----------------------------
class VertexItem(QObject, QGraphicsEllipseItem):

    def __init__(self, pos: QPointF, radius=5.0, color=QColor(255,0,0)):
        QObject.__init__(self)
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius*2, radius*2)
        self.setPos(pos)
        self._radius = radius
        self._color = color
        self.setBrush(QBrush(self._color))
        self.setPen(Qt.PenStyle.NoPen)

    @Property(QColor)
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.setBrush(QBrush(color))

    @Property(float)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        self.setRect(-value, -value, value*2, value*2)

# -----------------------------
# Polygon Item with automatic vertices
# -----------------------------
class PolygonItem(QObject, QGraphicsPathItem):
    vertexHovered = Signal(object)
    vertexUnhovered = Signal(object)
    vertexClicked = Signal(object)
    clickedOutsideVertices = Signal(QPointF)

    def __init__(self, polygon: QPolygonF, parent=None):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self, parent)
        self.polygon = polygon
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.updatePath()
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        # self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)

        self.vertices = []
        for pt in self.polygon:
            v = VertexItem(pt)
            v.setParentItem(self)
            self.vertices.append(v)

    def updatePath(self):
        path = QPainterPath()
        path.addPolygon(self.polygon)
        self.setPath(path)

    def get_vertex(self, position):
        for v in self.vertices:
            if v.contains(v.mapFromParent(position)):
                return v

    def mousePressEvent(self, event):
        if vertex := self.get_vertex(event.pos()):
            self.vertexClicked.emit(vertex)
        else:
            self.clickedOutsideVertices.emit(event.pos())

        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        if vertex := self.get_vertex(event.pos()):
            self.vertexHovered.emit(vertex)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if vertex := self.get_vertex(event.pos()):
            self.vertexUnhovered.emit(vertex)
        super().hoverLeaveEvent(event)

# -----------------------------
# Main View
# -----------------------------
class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        polygon = QPolygonF([
            QPointF(50,50),
            QPointF(150,50),
            QPointF(150,150),
            QPointF(100,200),
        ])

        self.poly_item = PolygonItem(polygon)
        self.scene.addItem(self.poly_item)

        # Connect signals externally
        self.poly_item.vertexHovered.connect(self.on_vertex_hovered)
        self.poly_item.vertexUnhovered.connect(self.on_vertex_unhovered)
        self.poly_item.vertexClicked.connect(self.on_vertex_clicked)
        self.poly_item.clickedOutsideVertices.connect(self.on_polygon_clicked)

        #self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.setWindowTitle("Polygon with Vertex Signal Forwarding")
        self.active_anim = None
    # -----------------------------
    # External handlers
    # -----------------------------
    def on_vertex_hovered(self, vertex):
        print("hover")
        self.active_anim = QPropertyAnimation(vertex,b"radius")
        self.active_anim.setEndValue(20.0)
        self.active_anim.setDuration(200)
        self.active_anim.start()


    def on_vertex_unhovered(self, vertex):
        print("unhover")
        self.active_anim = QPropertyAnimation(vertex,b"radius")
        self.active_anim.setEndValue(5)
        self.active_anim.setDuration(200)
        self.active_anim.start()

    def on_vertex_clicked(self, vertex):
        print("clicked")
        vertex.color = QColor(0,255,0)


    def on_polygon_clicked(self, pos):
        print(f"Polygon clicked outside vertices at {pos}")

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = MainView()
    view.resize(400,300)
    view.show()
    sys.exit(app.exec())
