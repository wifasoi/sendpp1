import sys
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtSvgWidgets import QGraphicsSvgItem

class Stitchwork:
    def __init__(self):
        super().__init__()
        super().__init__()

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