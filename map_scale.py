import pyqtgraph as pg
from PyQt6.QtWidgets import QDialogButtonBox
import os
import sys

# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ui_path = resource_path("SetMapScale.ui")
# https://www.pythonguis.com/tutorials/pyside6-embed-pyqtgraph-custom-widgets/
uiclass, baseclass = pg.Qt.loadUiType(ui_path)

class SetMapScale(baseclass, uiclass):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.main_window = parent
        self.LengthInMeters.valueChanged.connect(self.set_scale)
        self.LengthInPixels.valueChanged.connect(self.set_scale)
        # https://www.pythonguis.com/tutorials/pyqt6-dialogs/
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def set_scale(self):
        meters = self.LengthInMeters.value()
        pixels = self.LengthInPixels.value()
        if pixels <= 0:
            self.Scale.setValue(0)
            return
        self.Scale.setValue(meters / pixels)

    def accept(self):
        if len(self.main_window.map_scale_markers) < 2:
            self.Scale.setValue(0)
            return

        meters = self.LengthInMeters.value()
        pixels = self.LengthInPixels.value()

        if meters <= 0 or pixels <= 0:
            return
        
        self.main_window.scale = float(meters) / float(pixels)
        self.main_window.actionCapture.setEnabled(True)
        self.main_window.actionNew.setEnabled(True)
        self.main_window.actionOpenProject.setEnabled(True)
        self.main_window.disconnect_measure_distance()
        self.main_window.remove_map_scale_markers()
        for marker in self.main_window.map_scale_markers:
            self.main_window.graphWidget.removeItem(marker)
        self.main_window.map_scale_markers.clear()
        super().accept()


    def reject(self):

        self.main_window.disconnect_measure_distance()
        self.main_window.scale = None
        self.main_window.actionCapture.setEnabled(False)
        self.main_window.actionOpenProject.setEnabled(True)
        for marker in self.main_window.map_scale_markers:
            self.main_window.graphWidget.removeItem(marker)
        self.main_window.map_scale_markers.clear()
        super().reject()



    



