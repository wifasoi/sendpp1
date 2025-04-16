from ctypes.macholib import dyld
from dataclasses import dataclass
import sys
from uuid import uuid1
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QTransform
from PySide6.QtSvg import QSvgRenderer
from sendpp1.machine import EmbroideryBoundingBox, EmbroideryLayout

class Stitchwork:
    def __init__(self, file, canvas: QGraphicsView):
        super().__init__()
        self._rotation = 0
        self._dx = 0
        self._yx = 0
        self._flip = False
        self.file = file
        self.uuid = uuid1()
        self.render =  QSvgRenderer(file)
        self.svg_item = QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.render)
        canvas.addAction(self.svg_item)

    @property
    def transform(self) -> QTransform:
        scale_factor = -1 if self.flip else 1
        return QTransform().rotate(self._rotation).translate(self._dx,self._dy).scale(scale_factor, scale_factor)

    def translate(self, x: int, y: int) -> None:
        self._dx = x
        self._dy = y

    def rotate(self, angle: int) -> None:
        self._rotation = angle

    def flip(self, value: bool = True) -> None:
        self._flip = value
        raise NotImplementedError()

    @property
    def flipped(self) -> bool:
        return self._transformation.determinant < 0

    def apply_transform(self, canvas: QGraphicsView) -> None:
        canvas.setTransform(self.transform)

    def get_pp1_layout(self, frame) -> EmbroideryLayout:
        raise NotImplementedError()
        return EmbroideryLayout(
            self._dx,
            self._dy,
            100,
            100,
            self._flip,
            frame
        )
    
    def get_pp1_BoundingBox(self, frame) -> EmbroideryBoundingBox:
        #TODO
        raise NotImplementedError()
        return EmbroideryBoundingBox()
        

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile("ui/main_window.ui")
        ui_file.open(QFile.ReadOnly)
        self.gui = loader.load(ui_file, self)
        ui_file.close()

    def connect_sockets(self):
        self.gui.RefreshButton.clicked.connect(self.refresh_config)

    def refresh_config(self):
        pass

    def import_stitchwork(self, file):
        draw_area: QGraphicsView = self.gui.StitchView


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())