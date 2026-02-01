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
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.LengthInMeters.valueChanged.connect(self.set_scale)
        self.LengthInPixels.valueChanged.connect(self.set_scale)
        # https://www.pythonguis.com/tutorials/pyqt6-dialogs/
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QDialogButtonBox(QBtn)
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
        if len(self.parent.map_scale_markers) < 2:
            self.Scale.setValue(0)
            return
        if self.LengthInPixels.value() <= 0:
            return
        
        self.parent.scale = self.Scale.value()
        self.parent.actionCapture.setEnabled(True)
        self.parent.disconnect_measure_distance()
        for marker in self.parent.map_scale_markers:
            self.parent.graphWidget.removeItem(marker)
        self.parent.map_scale_markers.clear()
        super().accept()


    def reject(self):

        self.parent.disconnect_measure_distance()
        self.parent.scale = None
        self.parent.actionCapture.setEnabled(False)
        for marker in self.parent.map_scale_markers:
            self.parent.graphWidget.removeItem(marker)
        self.parent.map_scale_markers.clear()
        super().reject()



    



