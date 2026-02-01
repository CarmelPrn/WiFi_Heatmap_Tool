import sys
from pathlib import Path
import os
import numpy as np
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from PIL import Image
from PyQt6 import QtWidgets
from PyQt6.QtCore import QResource, QTimer, QProcess, Qt, QDir
from PyQt6.QtWidgets import QFileDialog, QApplication, QTableWidgetItem, QHeaderView, QListWidgetItem
from PyQt6.QtGui import QIcon
import math
import json
from map_scale import SetMapScale
from pathlib import Path
import csv
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ui_path = resource_path("wifi_UI.ui")
# https://www.pythonguis.com/tutorials/pyside6-embed-pyqtgraph-custom-widgets/
uiclass, baseclass = pg.Qt.loadUiType(ui_path)

UI_COLUMNS = ["Name", "SSID", "Signal", "Freq", "Ch", "Ch Width (MHz)", "Protocol", "Time"]
CSV_HEADERS = ["x", "y", "timestamp", "interface_mac", "bssid", "channel_frequency", "channel_number", "channel_width", "phy_type", "rssi", "ssid"]

class MainWindow(uiclass, baseclass):

    def __init__(self):
        super().__init__()
        base_dir = Path(__file__).resolve().parent
        self.temp_json_path = str((base_dir / "temp.json").resolve())
        self.image_item = None

        self.setupUi(self)
        self.actionNew.setIcon(QIcon(resource_path("icons/new.svg")))
        self.actionCapture.setIcon(QIcon(resource_path("icons/capture.svg")))
        self.actionStop.setIcon(QIcon(resource_path("icons/stop.svg")))
        self.actionExport.setIcon(QIcon(resource_path("icons/export-csv.svg")))
        self.actionExportScreenshot.setIcon(QIcon(resource_path("icons/export_screenshot.svg")))
        self.bannerFrame.hide()
        self._plot_click_connected = False
        self.clickable_toggle(False)
        self.initial_actions_state()
        self.actionNew.triggered.connect(self.open_file_dialog)
        self.actionExport.triggered.connect(self.save_csv_dialog)
        self.actionExportScreenshot.triggered.connect(self.save_screenshot_dialog)
        self.actionCapture.triggered.connect(self.on_capture_clicked)
        self.scan_location_marker = None
        self.settings_window = None
        self.scan_results = []
        self.map_scale_markers = []
        self.map_ui_markers = []
        #https://doc.qt.io/qtforpython-6/tutorials/basictutorial/tablewidget.html
        self.tableWidget.setColumnCount(len(UI_COLUMNS))
        self.tableWidget.setHorizontalHeaderLabels(UI_COLUMNS)
        header = self.tableWidget.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.latest_scan = []
        self._scan_running = False

        self.proc = QProcess(self) # käivitab lswifi
        self.proc.setWorkingDirectory(str(base_dir)) 
        self.proc.finished.connect(self.on_scan_finished)

        self.timer = QTimer()
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.passive_wifi_scan)
    

        self.actionStop.triggered.connect(self.on_stop_clicked)
        self.scale = None
        self.heatmap_item = None
        self.heatmap_items = {}
        self.listSSID.itemChanged.connect(self.list_changed)
        self.colorbar = None

    def closeEvent(self, event):
        try:
            if self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning:
                self.proc.kill()
                self.proc.waitForFinished(1000)
        except Exception:
            pass
        super().closeEvent(event)

    def list_changed(self, item):
        any_ssid_checked = False
        if self._scan_running:
            return
        bssid_list = item.data(Qt.ItemDataRole.UserRole)
        key = item.text()
        if item.checkState() == Qt.CheckState.Checked:
            any_ssid_checked = True
            self.plot_wifi_heatmap_griddata(bssid_list=bssid_list, key=key)
        else:
            if key in self.heatmap_items:
                self.graphWidget.removeItem(self.heatmap_items[key])
                del self.heatmap_items[key]

        if any_ssid_checked is False:
            self.bannerFrame.hide()

    def passive_wifi_scan(self):
         if self._scan_running:
             return
        
    
         p = Path(self.temp_json_path)
         if p.exists():
             p.unlink()
         self._scan_running = True
         self.proc.start("lswifi.exe", ["--json", self.temp_json_path])


    def on_scan_finished(self):
        self._scan_running = False
        p = Path(self.temp_json_path)
        if not p.exists():
            return
        
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError):
            return
        
        scan_data = data.get("scan_data", [])
        self.latest_scan = scan_data
        self.update_table_from_latest_scan()
        self.update_list_widget(scan_data)

    def update_table_from_latest_scan(self):
        results = self.latest_scan
        if not isinstance(results, list):
            return

        self.tableWidget.setUpdatesEnabled(False)
        try:
            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(len(results))
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    continue
                self.tableWidget.setItem(i, 0, QTableWidgetItem(str(result.get("bssid", ""))))
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(result.get("ssid", "") or "hidden")))
                self.tableWidget.setItem(i, 2, QTableWidgetItem(str(result.get("rssi", ""))))
                self.tableWidget.setItem(i, 3, QTableWidgetItem(str(result.get("channel_frequency", ""))))
                self.tableWidget.setItem(i, 4, QTableWidgetItem(str(result.get("channel_number", ""))))
                self.tableWidget.setItem(i, 5, QTableWidgetItem(str(result.get("channel_width", ""))))
                self.tableWidget.setItem(i, 6, QTableWidgetItem(str(result.get("phy_type", ""))))
                self.tableWidget.setItem(i, 7, QTableWidgetItem(str(result.get("timestamp", ""))))
        finally:
            self.tableWidget.setUpdatesEnabled(True)


    def open_settings(self):

        self.clickable_toggle(False)
        self.settings_window = SetMapScale(self)
        self.settings_window.setWindowModality(Qt.WindowModality.NonModal)
        self.settings_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        sig = self.graphWidget.scene().sigMouseClicked
        try: 
            sig.disconnect(self.measure_distance)
        except TypeError:
            pass
        sig.connect(self.measure_distance)


    def on_capture_clicked(self):
        self.scan_results.clear()
        self.latest_scan = []
        self.tableWidget.clearContents()
        self.listSSID.clear()
        self.bannerFrame.hide()
        for i in self.heatmap_items.values():
            self.graphWidget.removeItem(i)
        self.heatmap_items.clear()
        self.colorbar = None
        self.bannerLabel.setText("Click on your current location to start collecting data.\n" "Wi-Fi scan updates every 3 seconds.")
        self.bannerFrame.show()
        self.capture_state()
        self.clickable_toggle(True)
        self.statusBar().showMessage(f"Scan started")
        self.timer.start()
        self.passive_wifi_scan()
    
    def on_stop_clicked(self):
        self.timer.stop()
        self.clickable_toggle(False)
        self.bannerFrame.hide()
        self.statusBar().showMessage(f"Scan stopped")
        self.stopped_state()
        self.remove_ui_markers()


        try:
            if self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning:
                self.proc.kill()
                self.proc.waitForFinished(1000)
        except Exception:
            pass

        self._scan_running = False
        
    def open_file_dialog(self):
        file_dialog = QtWidgets.QFileDialog(self)

        file_dialog.setLabelText(QFileDialog.DialogLabel.FileName, "Open Floor plan Image File")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilters({"Image files (*.png *.jpg)"})
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                self.load_image(image_path)

# https://www.geeksforgeeks.org/python/writing-csv-files-in-python/
# https://stackoverflow.com/questions/12546031/qfiledialoggetsavefilename-and-default-selectedfilter
# https://stackoverflow.com/questions/42988983/qfiledialog-getsavefilename-is-not-saving-into-any-kind-of-file

    def save_csv_dialog(self):
        filename, filter = QtWidgets.QFileDialog.getSaveFileName(self, "Save file", QDir.currentPath(), "All Files (*);; CSV Files (*.csv)")
        if filename and self.scan_results:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(self.scan_results)

    def load_image(self, file_path):

        self.scale = None
        self.scan_results.clear()
        self.latest_scan = []
        self.tableWidget.clearContents()
        self.listSSID.clear()
        self.bannerFrame.hide()

        for i in self.heatmap_items.values():
            self.graphWidget.removeItem(i)
        self.heatmap_items.clear()
        self.colorbar = None
        self.remove_ui_markers()

        for m in self.map_scale_markers:
            self.graphWidget.removeItem(m)
        self.map_scale_markers.clear()

        img = Image.open(file_path).convert("RGB")
        self.image_array = np.array(img)
        self.image_height_pixels, self.image_width_pixels = (
            self.image_array.shape[:2]
        )

        if self.image_item is not None:
            self.graphWidget.removeItem(self.image_item)
        img_flipped = np.flipud(self.image_array)
        img_data = img_flipped.transpose((1, 0, 2))

        self.image_item = pg.ImageItem(img_data)
        self.graphWidget.setAspectLocked(True)
        self.graphWidget.addItem(self.image_item)
        self.image_item.setRect(pg.QtCore.QRectF(
            0, 0,
            self.image_width_pixels,
            self.image_height_pixels
        ))
        self.image_loaded_state()
        self.open_settings()

        
    def measure_distance(self, event):
        pos = self.graphWidget.getPlotItem().vb.mapSceneToView(
            event.scenePos()
        )
        x_pos = pos.x()
        y_pos = pos.y()
        if not self.is_click_within_bounds(x_pos=x_pos, y_pos=y_pos):
            return
        
        # https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/targetitem.html
        if len(self.map_scale_markers) < 2:
            m = pg.TargetItem(pos=(x_pos, y_pos), movable=True, size=10, symbol='o', pen=pg.mkPen(color='g', width=1), brush=pg.mkBrush(color='g'))
            self.graphWidget.addItem(m)
            self.map_scale_markers.append(m)
            m.sigPositionChanged.connect(self.update_marker_distance)

        self.update_marker_distance()
        
    def update_marker_distance(self):
        if len(self.map_scale_markers) < 2:
            return
        
        pos1 = self.map_scale_markers[0].pos()
        pos2 = self.map_scale_markers[1].pos()

        x = float(pos2.x() - pos1.x())
        y = float(pos2.y() - pos1.y())
        
        self.distance = math.sqrt(x * x + y * y) # https://www.mathsisfun.com/pythagoras.html

        self.settings_window.LengthInPixels.setValue(int(self.distance))


    def disconnect_measure_distance(self):
        self.graphWidget.scene().sigMouseClicked.disconnect(self.measure_distance)

    def clickable_toggle(self, clickable: bool):
        sig = self.graphWidget.scene().sigMouseClicked
        if clickable and not self._plot_click_connected:
            sig.connect(self.on_plot_clicked)
            self._plot_click_connected = True
        elif not clickable and self._plot_click_connected:
            sig.disconnect(self.on_plot_clicked)
            self._plot_click_connected = False

    def on_plot_clicked(self, event):
        pos = self.graphWidget.getPlotItem().vb.mapSceneToView(event.scenePos())
        x_pos = pos.x()
        y_pos = pos.y()
        if not self.is_click_within_bounds(x_pos=x_pos, y_pos=y_pos):
            return
        self.scan_location = (x_pos, y_pos)
        self.update_scan_location_marker()

    def update_scan_location_marker(self):
        x, y = self.scan_location
        self.scan_location_marker = pg.ScatterPlotItem(
            [x], [y],
            symbol='x',
            size=20,
            pen=pg.mkPen(color='r', width=3),
            brush=pg.mkBrush(color='r')
        )
        self.graphWidget.addItem(self.scan_location_marker)
        self.map_ui_markers.append(self.scan_location_marker)
        results = getattr(self, "latest_scan", [])

        if isinstance(results, dict): 
            results = [results]

        results = [{"x": x, "y": y, **r} for r in results]
        results = [{key : val for key, val in result.items()
                   if key in CSV_HEADERS} for result in results]

        self.scan_results.extend(results)
        

    def update_list_widget(self, results):
        self.listSSID.blockSignals(True)
        # https://forum.qt.io/topic/113630/item-in-qlistwidget-cannot-be-checked-even-set-the-flags

        self.listSSID.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QListWidget.html#PySide6.QtWidgets.QListWidget.addItem
        # https://forum.qt.io/topic/113710/remove-duplicate-entries-from-qlistwidget?_=1766934140002
        networks = {}
        for result in results:
            ssid = result.get("ssid", "") or "hidden"
            frequency = self.convert_frequency(frequency=result.get("channel_frequency"))
            bssid = result.get("bssid")
            text = f"{ssid} {frequency}"

            networks.setdefault(text, []).append(bssid)

        for text, bssid in networks.items():
            if not self.listSSID.findItems(text, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive):
                item_ssid = QListWidgetItem(text)
                item_ssid.setFlags(item_ssid.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item_ssid.setCheckState(Qt.CheckState.Unchecked)
                item_ssid.setData(Qt.ItemDataRole.UserRole, bssid)
                self.listSSID.addItem(item_ssid)

        self.listSSID.blockSignals(False)

    def convert_frequency(self, frequency:str):
        freq = float(frequency)
        if 2.400 <= freq <= 2.500:
            return "2.4 GHz"
        elif 5.000 <= freq < 6.000:
            return "5 GHz"
        elif 6.000 <= freq < 7.000:
            return "6 GHz"
        else:
            return "Unknown"

    def is_click_within_bounds(self, x_pos, y_pos):
        if (0 > x_pos or x_pos >= self.image_width_pixels) or (0 > y_pos or y_pos >= self.image_height_pixels):
            self.statusBar().showMessage("Clicked position is outside the image bounds.", 5000)
            return False
        return True
    
    def remove_ui_markers(self):
        for marker in self.map_ui_markers:
            self.graphWidget.removeItem(marker)
        self.map_ui_markers.clear()

    def remove_map_scale_markers(self):
        for marker in self.map_scale_markers:
            self.graphWidget.removeItem(marker)
        self.map_scale_markers.clear()

    def image_loaded_state(self):
        self.actionNew.setEnabled(True)
        self.actionCapture.setEnabled(False)
        self.actionStop.setEnabled(False)
        self.actionExport.setEnabled(False)
        self.actionExportScreenshot.setEnabled(False)

    def capture_state(self):
        self.actionNew.setEnabled(True)
        self.actionCapture.setEnabled(False)
        self.actionStop.setEnabled(True)
        self.actionExport.setEnabled(False)
        self.actionExportScreenshot.setEnabled(False)

    def initial_actions_state(self):
        self.actionNew.setEnabled(True)
        self.actionCapture.setEnabled(False)
        self.actionStop.setEnabled(False)
        self.actionExport.setEnabled(False)
        self.actionExportScreenshot.setEnabled(False)
    
    def stopped_state(self):
        self.actionNew.setEnabled(True)
        if self.image_item is not None and self.scale is not None:
            self.actionCapture.setEnabled(True)
        else:
            self.actionCapture.setEnabled(False)
        self.actionStop.setEnabled(False)
        self.actionExport.setEnabled(bool(self.scan_results))
        self.actionExportScreenshot.setEnabled(True)

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html
    def plot_wifi_heatmap_griddata(self, bssid_list, key):
        self.remove_ui_markers()
        self.bannerFrame.hide()
        unique_bssid_results = []

        grid_scale = 200
        X_grid = np.linspace(0, self.image_width_pixels * self.scale, grid_scale)
        Y_grid = np.linspace(0, self.image_height_pixels * self.scale, grid_scale)

        X_grid, Y_grid = np.meshgrid(X_grid, Y_grid)


        for result in self.scan_results:
            if result.get('bssid') in bssid_list:
                unique_bssid_results.append(result)

        if not self.scan_results or len(unique_bssid_results) < 3:
            self.bannerLabel.setText(f"Not enough data to create heatmap for {key} network")
            self.bannerFrame.show()
            return

        X = []
        Y = []
        X_m = []
        Y_m = []
        rssi_values = []
        for result in unique_bssid_results:
            x = float(result.get('x'))
            y = float(result.get('y'))
            rssi = int(result.get('rssi'))
            scale = self.scale
            X_meters = x * scale
            Y_meters = y * scale

            X.append(x)
            Y.append(y)
            X_m.append(X_meters)
            Y_m.append(Y_meters)
            rssi_values.append(rssi)
        
    # https://numpy.org/doc/stable/reference/generated/numpy.column_stack.html

        grid_z0 = griddata(np.column_stack([X_m, Y_m]), rssi_values, (X_grid, Y_grid), method='nearest')

        RSSI_MIN = -90
        RSSI_MAX = -30

        grid_z0 = gaussian_filter(grid_z0, sigma=3) # https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html

        if key in self.heatmap_items:
            self.graphWidget.removeItem(self.heatmap_items[key])

        heatmap_item = pg.ImageItem(grid_z0.transpose())
        heatmap_item.setRect(pg.QtCore.QRectF(0, 0, self.image_width_pixels, self.image_height_pixels))

                
        cmap = pg.colormap.get("turbo")
        heatmap_item.setLookupTable(cmap.getLookupTable(0.0, 1.0, 256))
        heatmap_item.setLevels((RSSI_MIN, RSSI_MAX))
        heatmap_item.setOpacity(0.5)

        self.graphWidget.addItem(heatmap_item)
        # https://pyqtgraph.readthedocs.io/en/pyqtgraph-0.13.0/colormap.html

        if self.colorbar is None:
            self.colorbar = pg.ColorBarItem(values=(RSSI_MIN, RSSI_MAX), colorMap=cmap, interactive=False)
            self.colorbar.setImageItem(heatmap_item, insert_in=self.graphWidget.getPlotItem())
        self.heatmap_items[key] = heatmap_item

    def save_screenshot_dialog(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save screenshot", QDir.currentPath(), "Image files (*.png *.jpg)")
        if not filename:
            return
        #exporter = ImageExporter(self.graphWidget.scene())
        #exporter.export(filename)
        pic = self.grab()
        pic.save(filename)



app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
