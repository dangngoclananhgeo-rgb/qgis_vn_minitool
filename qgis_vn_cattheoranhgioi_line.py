import os
import processing
from qgis.core import (
    QgsProject, QgsMapLayerType, QgsVectorLayer, QgsRasterLayer
)
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QPushButton, QFileDialog, QMessageBox, 
    QLineEdit, QGroupBox, QAbstractItemView
)

class ClipMultiLayersDialog(QDialog):
    def __init__(self, parent=None):
        super(ClipMultiLayersDialog, self).__init__(parent)
        self.setWindowTitle("Công cụ Cắt dữ liệu tùy chọn theo Ranh giới hành chính")
        self.resize(550, 500)
        
        main_layout = QVBoxLayout()
        
        # 1. Chọn Lớp Ranh giới hành chính (Mask)
        gb_mask = QGroupBox("1. Chọn lớp Ranh giới hành chính cắt (Mask layer):")
        vbox_mask = QVBoxLayout()
        self.cb_mask = QComboBox()
        vbox_mask.addWidget(self.cb_mask)
        gb_mask.setLayout(vbox_mask)
        main_layout.addWidget(gb_mask)
        
        # 2. Danh sách các file cần cắt (Waterway, Landuse, Highway, DEM...)
        gb_layers = QGroupBox("2. Chọn các lớp cần cắt (Giữ Ctrl hoặc kéo chọn nhiều file):")
        vbox_layers = QVBoxLayout()
        self.list_layers = QListWidget()
        self.list_layers.setSelectionMode(QAbstractItemView.MultiSelection)
        vbox_layers.addWidget(self.list_layers)
        gb_layers.setLayout(vbox_layers)
        main_layout.addWidget(gb_layers)
        
        # 3. Đặt tên tiền tố cho sản phẩm đầu ra
        gb_naming = QGroupBox("3. Cấu hình tên sản phẩm đầu ra:")
        layout_naming = QHBoxLayout()
        layout_naming.addWidget(QLabel("Tiền tố tên file mới:"))
        self.txt_prefix = QLineEdit("Clipped_")
        layout_naming.addWidget(self.txt_prefix)
        gb_naming.setLayout(layout_naming)
        main_layout.addWidget(gb_naming)
        
        # 4. Chọn thư mục đầu ra
        gb_output = QGroupBox("4. Chọn thư mục lưu sản phẩm đầu ra:")
        vbox_output = QVBoxLayout()
        dir_layout = QHBoxLayout()
        default_dir = os.path.join(os.path.expanduser("~"), "QGIS_Clipped_Output")
        self.lbl_dir = QLabel(default_dir)
        self.lbl_dir.setStyleSheet("border: 1px solid #ccc; padding: 4px; background: #f9f9f9;")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.lbl_dir)
        dir_layout.addWidget(btn_browse)
        vbox_output.addLayout(dir_layout)
        gb_output.setLayout(vbox_output)
        main_layout.addWidget(gb_output)
        
        # Nút Chạy
        self.btn_run = QPushButton("Thực Hiện Cắt Dữ Liệu (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_layers()
        
    def populate_layers(self):
        """Liệt kê toàn bộ Vector và Raster đang mở trong project"""
        layers = QgsProject.instance().mapLayers().values()
        
        for layer in layers:
            # Lớp Mask chỉ lấy Vector
            if layer.type() == QgsMapLayerType.VectorLayer:
                self.cb_mask.addItem(f"[Vector] {layer.name()}", layer)
            
            # Thêm vào danh sách các lớp có thể cắt (bỏ qua ranh giới)
            self.list_layers.addItem(layer.name())
            
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file kết quả", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(os.path.normpath(folder))
            
    def validate_and_accept(self):
        if self.cb_mask.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 lớp ranh giới hành chính!")
            return
        if not self.list_layers.selectedItems():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất 1 lớp dữ liệu để cắt!")
            return
        self.accept()

    def get_selected_layer_names(self):
        return [item.text() for item in self.list_layers.selectedItems()]


# --- THỰC THI CÔNG CỤ TRÊN CONSOLE ---
dialog = ClipMultiLayersDialog()
if dialog.exec_() == QDialog.Accepted:
    mask_layer = dialog.cb_mask.currentData()
    selected_names = dialog.get_selected_layer_names()
    prefix = dialog.txt_prefix.text().strip()
    output_dir = dialog.lbl_dir.text().strip()
    
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    print("\n--- BẮT ĐẦU CẮT DỮ LIỆU TÙY CHỌN ---")
    
    for layer_name in selected_names:
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            continue
        
        target_layer = layers[0]
        out_filename = f"{prefix}{target_layer.name()}"
        
        # 1. Nếu là lớp VECTOR (waterway, landuse, highway...)
        if target_layer.type() == QgsMapLayerType.VectorLayer:
            out_path = os.path.normpath(os.path.join(output_dir, f"{out_filename}.shp"))
            params = {
                'INPUT': target_layer,
                'OVERLAY': mask_layer,
                'OUTPUT': out_path
            }
            print(f"Đang cắt Vector '{target_layer.name()}'...")
            try:
                res = processing.run("native:clip", params)
                res_layer = QgsVectorLayer(res['OUTPUT'], out_filename, "ogr")
                if res_layer.isValid():
                    QgsProject.instance().addMapLayer(res_layer)
                    print(f"-> Thành công! Đã nạp Vector: {out_filename}")
                    success_count += 1
            except Exception as e:
                print(f"Lỗi khi cắt Vector {target_layer.name()}: {e}")
                
        # 2. Nếu là lớp RASTER (DEM, Hillshade...)
        elif target_layer.type() == QgsMapLayerType.RasterLayer:
            out_path = os.path.normpath(os.path.join(output_dir, f"{out_filename}.tif"))
            params = {
                'INPUT': target_layer,
                'MASK': mask_layer,
                'SOURCE_CRS': target_layer.crs(),
                'TARGET_CRS': mask_layer.crs(),
                'NODATA': -9999,
                'ALPHA_BAND': True,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OUTPUT': out_path
            }
            print(f"Đang cắt Raster '{target_layer.name()}'...")
            try:
                res = processing.run("gdal:cliprasterbymasklayer", params)
                res_layer = QgsRasterLayer(res['OUTPUT'], out_filename)
                if res_layer.isValid():
                    QgsProject.instance().addMapLayer(res_layer)
                    print(f"-> Thành công! Đã nạp Raster: {out_filename}")
                    success_count += 1
            except Exception as e:
                print(f"Lỗi khi cắt Raster {target_layer.name()}: {e}")

    QMessageBox.information(
        None, "Hoàn tất", 
        f"Đã cắt thành công {success_count}/{len(selected_names)} file!\n"
        f"Các sản phẩm mới đã được nạp trực tiếp vào Project đang làm việc."
    )