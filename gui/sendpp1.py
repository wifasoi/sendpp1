from ctypes.macholib import dyld
from dataclasses import dataclass
import sys
import pyembroidery
from uuid import uuid1
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QFileDialog
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QTransform
from PySide6.QtSvg import QSvgRenderer
import pyembroidery.SvgWriter
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
        self.pattern = pyembroidery.read(file)
        dom = pyembroidery.SvgWriter.create_svg_dom(self.pattern)
        self.render =  QSvgRenderer(dom)
        self.svg_item = QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.render)
        canvas.addAction(self.svg_item)

    @property
    def transform(self) -> QTransform:
        scale_factor = -1 if self.flip else 1
        return QTransform().translate(self._dx,self._dy).rotate(self._rotation).scale(scale_factor, scale_factor)

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
        raise NotImplementedError()
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
        self.stitchworks =[]

    def connect_sockets(self):
        self.gui.RefreshButton.clicked.connect(self.refresh_config)

    def refresh_config(self):
        pass

    def import_stitchwork(self):
        draw_area: QGraphicsView = self.gui.StitchView
        fileName = QFileDialog.getOpenFileName(
            self.gui,
            self.tr("Select an embroidery file"),
            "",
            filter=self.tr("Embroidery Files (*.dst *.exp *.jef *.pec *.pes *.sew *.vp3 *.xxx *.emd *.10o)"),
            options=QFileDialog.Option.DontUseNativeDialog
        )
        self.stitchworks.append(Stitchwork(fileName, self.gui.StitchView))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())