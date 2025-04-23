import asyncio
from ctypes.macholib import dyld
from dataclasses import dataclass
import sys
from venv import logger
from xml.etree import ElementTree
import pyembroidery
from uuid import uuid1
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QFileDialog, QWidget, QGraphicsScene
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QTransform
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtBluetooth import QBluetoothDeviceDiscoveryAgent
from PySide6.QtStateMachine import QStateMachine, QState
import pyembroidery.SvgWriter
from sendpp1.core.machine import EmbroideryBoundingBox, EmbroideryLayout
import importlib.resources
from loguru import logger

logger.add(sys.stdout, level="TRACE", colorize=True, backtrace=True, diagnose=True)


def load_ui_widget(filename: str, parent: QWidget = None) -> QWidget:
    # Use importlib.resources to get the path to the .ui file
    with importlib.resources.path("sendpp1.gui.ui", filename) as ui_path:
        logger.trace("Loading {} widget from path {}", filename, ui_path)
        file = QFile(str(ui_path))
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        widget = loader.load(file, parent)
        file.close()
        return widget

class Stitchwork:
    def __init__(self, file, canvas: QGraphicsScene):
        super().__init__()
        self._rotation = 0
        self._dx = 0
        self._yx = 0
        self._flip = False
        self.file = file
        self.uuid = uuid1()
        logger.trace("Loading pattern {}", file)
        self.pattern = pyembroidery.read(file)
        dom = pyembroidery.SvgWriter.create_svg_dom(self.pattern)
        self.render =  QSvgRenderer(ElementTree.tostring(dom.getroot(), encoding='utf8'))
        self.svg_item = QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.render)
        canvas.addItem(self.svg_item)

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


class MyMainWindow:
    def __init__(self):
        super().__init__()

        self.ui = load_ui_widget("main_window.ui")
        self.connect_sockets()
        self.scene = QGraphicsScene()
        self.ui.StitchView.setScene(self.scene)
        self. bt = QBluetoothDeviceDiscoveryAgent(self.ui)
        self.bt.setLowEnergyDiscoveryTimeout(10000)
        self.connection_sm = QStateMachine(self.ui)
        self.setup_conenction_statemachine()
        self.connection_sm.start()
        self.stitchworks =[]

    def show(self):
        self.ui.show()

    def connect_sockets(self):
        self.ui.actionImport.triggered.connect(self.import_stitchwork)
        self.ui.RefreshButton.clicked.connect(self.refresh_config)

    def setup_conenction_statemachine(self):
        conencted = QState()
        searching = QState()
        discovered = QState()
        disconencted = QState()

        disconencted.assignProperty(self.ui.bt_button, "text", self.ui.tr("Scan"))
        disconencted.assignProperty(self.ui.bt_button, "enabled", True)
        disconencted.assignProperty(self.ui.MachineSelection, "enabled", False)
        disconencted.addTransition(self.ui.bt_button.clicked, searching)

        searching.assignProperty(self.ui.bt_button, "text", self.ui.tr("Searching..."))
        searching.assignProperty(self.ui.bt_button, "enabled", False)
        searching.assignProperty(self.ui.MachineSelection, "enabled", False)
        searching.entered.connect(self.bt.start)
        searching.addTransition(self.bt.finished, discovered)
        searching.addTransition(self.bt.errorOccurred, disconencted)

        discovered.assignProperty(self.ui.bt_button, "enabled", True)
        discovered.assignProperty(self.ui.MachineSelection, "enabled", True)
        discovered.assignProperty(self.ui.bt_button, "text", self.ui.tr("Connect"))

        conencted.assignProperty(self.ui.bt_button, "text", self.ui.tr("Connected"))
        conencted.assignProperty(self.ui.bt_button, "enabled", False)
        conencted.assignProperty(self.ui.MachineSelection, "enabled", False)

        self.connection_sm.addState(conencted)
        self.connection_sm.addState(searching)
        self.connection_sm.addState(discovered)
        self.connection_sm.addState(disconencted)
        self.connection_sm.setInitialState(disconencted)

    def refresh_config(self):
        pass

    def import_stitchwork(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self.ui,
            self.ui.tr("Select an embroidery file"),
            "",
            filter=self.ui.tr("Embroidery Files (*.dst *.exp *.jef *.pec *.pes *.sew *.vp3 *.xxx *.emd *.10o)"),
            #options=QFileDialog.Option.DontUseNativeDialog
        )
        if file_name:
            self.stitchworks.append(Stitchwork(file_name, self.scene))

def main():
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()