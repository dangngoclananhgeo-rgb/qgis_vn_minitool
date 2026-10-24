import os
import processing
from qgis.core import (
    QgsProject, QgsMapLayerType, QgsCoordinateReferenceSystem, 
    QgsVectorLayer, QgsRasterLayer
)
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QListWidget, QPushButton, QFileDialog, QMessageBox, 
    QAbstractItemView, QGroupBox, QListWidgetItem
)

class ReprojectVN2000Dialog(QDialog):
    def __init__(self, parent=None):
        super(ReprojectVN2000Dialog, self).__init__(parent)
        self.setWindowTitle("Chuyển Hệ Tọa Độ Sang VN2000")
        self.resize(520, 580)
        
        main_layout = QVBoxLayout()
        
        # 1. Nhóm chọn các lớp dữ liệu đầu vào
        gb_layers = QGroupBox("1. Chọn các lớp dữ liệu cần chuyển tọa độ:")
        vbox_layers = QVBoxLayout()
        
        self.list_layers = QListWidget()
        self.list_layers.setSelectionMode(QAbstractItemView.MultiSelection)
        vbox_layers.addWidget(self.list_layers)
        
        btn_layer_layout = QHBoxLayout()
        btn_select_all = QPushButton("Chọn tất cả")
        btn_select_all.clicked.connect(self.select_all)
        btn_deselect_all = QPushButton("Bỏ chọn tất cả")
        btn_deselect_all.clicked.connect(self.deselect_all)
        btn_layer_layout.addWidget(btn_select_all)
        btn_layer_layout.addWidget(btn_deselect_all)
        vbox_layers.addLayout(btn_layer_layout)
        
        gb_layers.setLayout(vbox_layers)
        main_layout.addWidget(gb_layers)
        
        # 2. Nhóm chọn Hệ tọa độ VN2000 (Target CRS)
        gb_crs = QGroupBox("2. Chọn Hệ tọa độ VN2000 đầu ra:")
        vbox_crs = QVBoxLayout()
        
        self.cb_crs = QComboBox()
        self.crs_dict = {
            "VN-2000 / UTM zone 48N (EPSG:3405) - Miền Tây / An Giang / TP.HCM": "EPSG:3405",
            "VN-2000 / UTM zone 49N (EPSG:3406) - Miền Trung / Miền Bắc": "EPSG:3406",
            "VN-2000 / TM-3 zone 48N (EPSG:5381) - Múi 3 độ Zone 48N": "EPSG:5381",
            "Tự nhập mã EPSG thủ công...": "CUSTOM"
        }
        for label in self.crs_dict.keys():
            self.cb_crs.addItem(label)
        self.cb_crs.currentIndexChanged.connect(self.toggle_custom_crs)
        vbox_crs.addWidget(self.cb_crs)
        
        self.txt_custom_crs = QLineEdit()
        self.txt_custom_crs.setPlaceholderText("Nhập mã EPSG (Ví dụ: EPSG:3405 hoặc 3405)")
        self.txt_custom_crs.setVisible(False)
        vbox_crs.addWidget(self.txt_custom_crs)
        
        gb_crs.setLayout(vbox_crs)
        main_layout.addWidget(gb_crs)
        
        # 3. Nhóm Quy tắc đặt tên file đầu ra
        gb_naming = QGroupBox("3. Quy tắc đặt tên file sản phẩm đầu ra:")
        vbox_naming = QVBoxLayout()
        
        layout_prefix = QHBoxLayout()
        layout_prefix.addWidget(QLabel("Tiền tố (Prefix):"))
        self.txt_prefix = QLineEdit("VN2000_")
        layout_prefix.addWidget(self.txt_prefix)
        
        layout_suffix = QHBoxLayout()
        layout_suffix.addWidget(QLabel("Hậu tố (Suffix):"))
        self.txt_suffix = QLineEdit("")
        self.txt_suffix.setPlaceholderText("Ví dụ: _vn2000")
        layout_suffix.addWidget(self.txt_suffix)
        
        vbox_naming.addLayout(layout_prefix)
        vbox_naming.addLayout(layout_suffix)
        gb_naming.setLayout(vbox_naming)
        main_layout.addWidget(gb_naming)
        
        # 4. Nhóm chọn Thư mục lưu Output
        gb_dir = QGroupBox("4. Nơi lưu kết quả sản phẩm:")
        dir_layout = QHBoxLayout()
        self.lbl_dir = QLabel(os.path.expanduser("~"))
        self.lbl_dir.setStyleSheet("border: 1px solid #ccc; padding: 4px; background: #f9f9f9;")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.lbl_dir)
        dir_layout.addWidget(btn_browse)
        gb_dir.setLayout(dir_layout)
        main_layout.addWidget(gb_dir)
        
        # Nút Thực thi
        self.btn_run = QPushButton("Chuyển Tọa Độ (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_layers()
        
    def populate_layers(self):
        """Liệt kê toàn bộ Vector và Raster trong Project QGIS"""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayerType.VectorLayer:
                type_str = "Vector"
            elif layer.type() == QgsMapLayerType.RasterLayer:
                type_str = "Raster"
            else:
                type_str = "Other"
                
            item = QListWidgetItem(f"[{type_str}] {layer.name()}")
            item.setData(32, layer)
            self.list_layers.addItem(item)
            item.setSelected(True)
            
    def select_all(self):
        for i in range(self.list_layers.count()):
            self.list_layers.item(i).setSelected(True)
            
    def deselect_all(self):
        for i in range(self.list_layers.count()):
            self.list_layers.item(i).setSelected(False)
            
    def toggle_custom_crs(self):
        selected_text = self.cb_crs.currentText()
        if self.crs_dict.get(selected_text) == "CUSTOM":
            self.txt_custom_crs.setVisible(True)
        else:
            self.txt_custom_crs.setVisible(False)
            
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file sản phẩm", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(folder)
            
    def validate_and_accept(self):
        if not self.list_layers.selectedItems():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất 1 lớp dữ liệu để chuyển đổi!")
            return
            
        selected_text = self.cb_crs.currentText()
        if self.crs_dict.get(selected_text) == "CUSTOM":
            crs_input = self.txt_custom_crs.text().strip()
            if not crs_input:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập mã EPSG cho Hệ tọa độ VN2000!")
                return
        self.accept()

    def get_target_crs(self):
        selected_text = self.cb_crs.currentText()
        val = self.crs_dict.get(selected_text)
        if val == "CUSTOM":
            crs_str = self.txt_custom_crs.text().strip()
            return crs_str if crs_str.upper().startswith("EPSG:") else f"EPSG:{crs_str}"
        return val

    def get_selected_layers(self):
        return [item.data(32) for item in self.list_layers.selectedItems()]


# --- CHẠY TOOL XỬ LÝ CHUYỂN TỌA ĐỘ ---
dialog = ReprojectVN2000Dialog()
if dialog.exec_() == QDialog.Accepted:
    selected_layers = dialog.get_selected_layers()
    target_crs_str = dialog.get_target_crs()
    output_dir = dialog.lbl_dir.text()
    prefix = dialog.txt_prefix.text().strip()
    suffix = dialog.txt_suffix.text().strip()
    
    os.makedirs(output_dir, exist_ok=True)
    
    target_crs = QgsCoordinateReferenceSystem(target_crs_str)
    if not target_crs.isValid():
        QMessageBox.critical(None, "Lỗi", f"Hệ tọa độ '{target_crs_str}' không hợp lệ trên QGIS!")
    else:
        project = QgsProject.instance()
        success_count = 0
        
        print(f"--- BẮT ĐẦU CHUYỂN ĐỔI SANG HỆ TỌA ĐỘ: {target_crs.authid()} ---")
        
        for layer in selected_layers:
            layer_name = layer.name()
            out_base_name = f"{prefix}{layer_name}{suffix}"
            
            # Xử lý Lớp Vector
            if layer.type() == QgsMapLayerType.VectorLayer:
                output_path = os.path.normpath(os.path.join(output_dir, f"{out_base_name}.shp"))
                
                # TỰ ĐỘNG KHẮC PHỤC TRÙNG TÊN FILE VECTOR
                counter = 1
                unique_base_name = out_base_name
                while os.path.exists(output_path):
                    unique_base_name = f"{out_base_name}_{counter}"
                    output_path = os.path.normpath(os.path.join(output_dir, f"{unique_base_name}.shp"))
                    counter += 1
                
                print(f"Đang chuyển Vector '{layer_name}' -> '{output_path}'...")
                
                params = {
                    'INPUT': layer,
                    'TARGET_CRS': target_crs,
                    'OUTPUT': output_path
                }
                
                try:
                    result = processing.run("native:reprojectlayer", params)
                    reprojected_layer = QgsVectorLayer(result['OUTPUT'], unique_base_name, "ogr")
                    if reprojected_layer.isValid():
                        project.addMapLayer(reprojected_layer)
                        success_count += 1
                        print(f"-> Thành công: Đã nạp lớp '{unique_base_name}' vào QGIS.")
                    else:
                        print(f"Lỗi: Lớp Vector đầu ra '{unique_base_name}' không hợp lệ.")
                except Exception as e:
                    print(f"Thất bại khi chuyển Vector '{layer_name}': {e}")
            
            # Xử lý Lớp Raster
            elif layer.type() == QgsMapLayerType.RasterLayer:
                output_path = os.path.normpath(os.path.join(output_dir, f"{out_base_name}.tif"))
                
                # TỰ ĐỘNG KHẮC PHỤC TRÙNG TÊN FILE RASTER
                counter = 1
                unique_base_name = out_base_name
                while os.path.exists(output_path):
                    unique_base_name = f"{out_base_name}_{counter}"
                    output_path = os.path.normpath(os.path.join(output_dir, f"{unique_base_name}.tif"))
                    counter += 1
                
                print(f"Đang chuyển Raster '{layer_name}' -> '{output_path}'...")
                
                params = {
                    'INPUT': layer,
                    'SOURCE_CRS': layer.crs(),
                    'TARGET_CRS': target_crs,
                    'RESAMPLING': 0, # Nearest Neighbor
                    'NODATA': None,
                    'TARGET_RESOLUTION': None,
                    'OPTIONS': '',
                    'DATA_TYPE': 0,
                    'OUTPUT': output_path
                }
                
                try:
                    result = processing.run("gdal:warpreproject", params)
                    reprojected_layer = QgsRasterLayer(result['OUTPUT'], unique_base_name)
                    if reprojected_layer.isValid():
                        project.addMapLayer(reprojected_layer)
                        success_count += 1
                        print(f"-> Thành công: Đã nạp lớp '{unique_base_name}' vào QGIS.")
                    else:
                        print(f"Lỗi: Lớp Raster đầu ra '{unique_base_name}' không hợp lệ.")
                except Exception as e:
                    print(f"Thất bại khi chuyển Raster '{layer_name}': {e}")
                    
        QMessageBox.information(
            None, "Hoàn tất", 
            f"Đã chuyển đổi thành công {success_count}/{len(selected_layers)} lớp sang Hệ tọa độ VN2000 ({target_crs.authid()})!"
        )