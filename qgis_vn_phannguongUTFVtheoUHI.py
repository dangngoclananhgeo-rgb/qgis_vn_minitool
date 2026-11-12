import os
from qgis.core import (
    QgsRasterBandStats,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsProject,
    QgsMapLayer,
    QgsRasterLayer,
    QgsRasterFileWriter,
    QgsRasterPipe
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QColorDialog, QHeaderView
)

class UTFVIClassifierDialog(QDialog):
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.provider = layer.dataProvider()
        self.band = 1
        
        self.setWindowTitle(f"Phân loại ngưỡng UTFVI (UHI) - {layer.name()}")
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)
        
        # Tính toán thống kê thực tế của layer
        self.stats = self.provider.bandStatistics(
            self.band, QgsRasterBandStats.All, self.layer.extent(), 0
        )
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. Nhóm thông số thống kê của Layer
        stats_group = QGroupBox("Thông số thống kê thực tế của Layer (Statistics)")
        stats_layout = QHBoxLayout()
        mean_str = f"{self.stats.mean:.6f}" if str(self.stats.mean) != 'nan' else "NaN"
        stats_layout.addWidget(QLabel(f"<b>Min:</b> {self.stats.minimumValue:.6f}"))
        stats_layout.addWidget(QLabel(f"<b>Max:</b> {self.stats.maximumValue:.6f}"))
        stats_layout.addWidget(QLabel(f"<b>Mean:</b> {mean_str}"))
        stats_layout.addWidget(QLabel(f"<b>Std Dev:</b> {self.stats.stdDev:.6f}"))
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # 2. Bảng phân loại ngưỡng UTFVI (Cho phép chỉnh sửa trực tiếp)
        table_group = QGroupBox("Bảng phân loại ngưỡng UTFVI (Nhấp đúp để sửa số/nhãn, nhấp vào ô màu để đổi màu)")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget(6, 4)
        self.table.setHorizontalHeaderLabels(["Màu sắc", "Giá trị trên (<=)", "Nhãn hiển thị (Label)", "Mức độ UHI (Tham khảo)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.handle_cell_clicked)
        
        # Lấy giá trị Min/Max thực tế để đưa vào nhãn và ngưỡng cuối (hoặc dùng mặc định nếu cần)
        min_v = self.stats.minimumValue
        max_v = max(self.stats.maximumValue, 0.058454)
        
        # Khởi tạo 6 mức chuẩn theo bảng ArcGIS Pro và Bảng 6 (Amiri et al., 2009)
        default_classes = [
            (QColor(38, 176, 0),    0.0,    f"{min_v:.3f} - 0",      "Không (< 0)"),
            (QColor(115, 223, 0),   0.005,  "0,001 - 0,005",         "Yếu (0 - 0,005)"),
            (QColor(197, 255, 0),   0.01,   "0,006 - 0,01",          "Trung bình (0,005 - 0,01)"),
            (QColor(255, 200, 0),   0.015,  "0,011 - 0,015",         "Mạnh (0,01 - 0,015)"),
            (QColor(255, 102, 0),   0.02,   "0,016 - 0,02",          "Rất mạnh (0,015 - 0,02)"),
            (QColor(255, 0, 0),     max_v,  f"0,021 - {max_v:.3f}",  "Mạnh nhất (> 0,02)")
        ]
        
        self.class_colors = []
        for row, (color, upper_val, label, uhi_level) in enumerate(default_classes):
            self.class_colors.append(color)
            
            # Cột 0: Ô màu
            color_item = QTableWidgetItem()
            color_item.setBackground(color)
            color_item.setFlags(Qt.ItemIsEnabled) # Không cho gõ chữ vào ô màu
            self.table.setItem(row, 0, color_item)
            
            # Cột 1: Upper value (<=)
            val_str = f"{upper_val:.6f}".rstrip('0').rstrip('.') if upper_val != 0 else "0.0"
            val_item = QTableWidgetItem(val_str)
            self.table.setItem(row, 1, val_item)
            
            # Cột 2: Nhãn (Label)
            label_item = QTableWidgetItem(label)
            self.table.setItem(row, 2, label_item)
            
            # Cột 3: Mức độ UHI
            uhi_item = QTableWidgetItem(uhi_level)
            self.table.setItem(row, 3, uhi_item)
            
        table_layout.addWidget(self.table)
        
        # Các nút tiện ích cho bảng
        table_btn_layout = QHBoxLayout()
        btn_set_exact_img = QPushButton("Đặt nhãn giống hệt ảnh mẫu (-0,029 đến 0,058)")
        btn_set_exact_img.clicked.connect(self.set_exact_sample_values)
        
        btn_preview = QPushButton("Xem trước màu trên bản đồ (Preview)")
        btn_preview.setStyleSheet("font-weight: bold;")
        btn_preview.clicked.connect(self.apply_symbology)
        
        table_btn_layout.addWidget(btn_set_exact_img)
        table_btn_layout.addWidget(btn_preview)
        table_layout.addLayout(table_btn_layout)
        
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # 3. Nhóm thiết lập Lưu trữ & Định dạng xuất
        save_group = QGroupBox("Tùy chọn Lưu trữ đầu ra")
        save_layout = QFormLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "GeoTIFF - Dữ liệu số gốc kèm bảng màu (.tif)",
            "GeoTIFF - Ảnh màu RGB đã render (.tif)",
            "QGIS Layer Style (.qml)"
        ])
        self.format_combo.setCurrentIndex(0) # Mặc định là .tif
        self.format_combo.currentIndexChanged.connect(self.update_file_extension)
        
        path_layout = QHBoxLayout()
        default_dir = os.path.dirname(self.layer.source()) if os.path.exists(self.layer.source()) else os.path.expanduser("~")
        default_path = os.path.join(default_dir, f"{self.layer.name()}_classified.tif")
        self.path_input = QLineEdit(default_path)
        
        btn_browse = QPushButton("Chọn nơi lưu...")
        btn_browse.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(btn_browse)
        
        self.auto_load_check = QCheckBox("Tự động mở layer đã lưu lên Project sau khi hoàn tất")
        self.auto_load_check.setChecked(True)
        
        save_layout.addRow("Định dạng file lưu:", self.format_combo)
        save_layout.addRow("Đường dẫn lưu:", path_layout)
        save_layout.addRow("", self.auto_load_check)
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)
        
        # 4. Nút Thực thi & Đóng
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Áp dụng & Lưu File")
        self.btn_save.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_save.clicked.connect(self.process_and_save)
        
        btn_cancel = QPushButton("Đóng")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

    def handle_cell_clicked(self, row, col):
        # Mở bảng chọn màu nếu người dùng click vào cột 0 (Màu sắc)
        if col == 0:
            new_color = QColorDialog.getColor(self.class_colors[row], self, "Chọn màu cho phân lớp")
            if new_color.isValid():
                self.class_colors[row] = new_color
                self.table.item(row, 0).setBackground(new_color)

    def set_exact_sample_values(self):
        # Điền chính xác bộ số và nhãn như ảnh chụp màn hình ArcGIS Pro của bạn
        sample_vals = [
            ("0.0",      "-0,029 - 0"),
            ("0.005",    "0,001 - 0,005"),
            ("0.01",     "0,006 - 0,01"),
            ("0.015",    "0,011 - 0,015"),
            ("0.02",     "0,016 - 0,02"),
            ("0.058454", "0,021 - 0,058")
        ]
        for row, (val, label) in enumerate(sample_vals):
            self.table.item(row, 1).setText(val)
            self.table.item(row, 2).setText(label)

    def update_file_extension(self):
        current_path = self.path_input.text().strip()
        if not current_path:
            return
        base, _ = os.path.splitext(current_path)
        if self.format_combo.currentIndex() in [0, 1]:
            self.path_input.setText(base + ".tif")
        else:
            self.path_input.setText(base + ".qml")

    def browse_save_path(self):
        idx = self.format_combo.currentIndex()
        file_filter = "GeoTIFF (*.tif *.tiff)" if idx in [0, 1] else "QGIS Layer Style (*.qml)"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Chọn nơi lưu trữ file", self.path_input.text(), file_filter
        )
        if save_path:
            self.path_input.setText(save_path)

    def apply_symbology(self):
        color_stops = []
        try:
            for row in range(self.table.rowCount()):
                val_text = self.table.item(row, 1).text().strip().replace(',', '.')
                upper_val = float(val_text)
                label_text = self.table.item(row, 2).text().strip()
                color = self.class_colors[row]
                
                color_stops.append(
                    QgsColorRampShader.ColorRampItem(upper_val, color, label_text)
                )
        except ValueError:
            QMessageBox.warning(self, "Lỗi nhập liệu", "Cột 'Giá trị trên (<=)' phải chứa số hợp lệ!")
            return False

        # Sử dụng chế độ Discrete (Rời rạc) để phân ngưỡng <= giống hệt ArcGIS Pro
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Discrete)
        fnc.setColorRampItemList(color_stops)
        
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(self.provider, self.band, shader)
        
        self.layer.setRenderer(renderer)
        self.layer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(self.layer.id())
        return True

    def process_and_save(self):
        if not self.apply_symbology():
            return
            
        save_path = self.path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "Thiếu đường dẫn", "Vui lòng chọn nơi lưu trữ file!")
            return
            
        idx = self.format_combo.currentIndex()
        
        if idx in [0, 1]:
            if not save_path.lower().endswith(('.tif', '.tiff')):
                save_path += '.tif'
                
            pipe = QgsRasterPipe()
            pipe.set(self.provider.clone())
            
            if idx == 1:
                pipe.set(self.layer.renderer().clone())
                
            writer = QgsRasterFileWriter(save_path)
            error = writer.writeRaster(
                pipe,
                self.layer.width(),
                self.layer.height(),
                self.layer.extent(),
                self.layer.crs()
            )
            
            if error == QgsRasterFileWriter.NoError:
                qml_sidecar = os.path.splitext(save_path)[0] + ".qml"
                self.layer.saveNamedStyle(qml_sidecar)
                
                if self.auto_load_check.isChecked():
                    new_name = os.path.basename(save_path)
                    new_layer = QgsRasterLayer(save_path, new_name)
                    if new_layer.isValid():
                        if idx == 0:
                            new_layer.loadNamedStyle(qml_sidecar)
                        QgsProject.instance().addMapLayer(new_layer)
                        
                QMessageBox.information(self, "Thành công", f"Đã lưu và mở thành công file tại:\n{save_path}")
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file TIF (Mã lỗi: {error}).")
        else:
            if not save_path.lower().endswith('.qml'):
                save_path += '.qml'
            self.layer.saveNamedStyle(save_path)
            QMessageBox.information(self, "Thành công", f"Đã lưu file Style QML tại:\n{save_path}")
            self.accept()

def run_utfvi_classifier():
    layer = iface.activeLayer()
    if not layer or layer.type() != QgsMapLayer.RasterLayer:
        QMessageBox.warning(None, "Cảnh báo", "Vui lòng chọn lớp Raster (ví dụ: UTFVI_Mua_Mua) trước khi chạy!")
        return
    dialog = UTFVIClassifierDialog(layer, iface.mainWindow())
    dialog.exec_()

run_utfvi_classifier()