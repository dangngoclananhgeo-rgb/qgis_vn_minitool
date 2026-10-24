import os
import processing
from qgis.core import QgsProject, QgsMapLayerType, QgsRasterLayer
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QListWidget, 
    QPushButton, QFileDialog, QHBoxLayout, QMessageBox, QAbstractItemView
)

class ClipRasterDialog(QDialog):
    def __init__(self, parent=None):
        super(ClipRasterDialog, self).__init__(parent)
        self.setWindowTitle("Công cụ cắt DEM / Hillshade (Trong suốt Alpha)")
        self.resize(480, 420)
        
        layout = QVBoxLayout()
        
        # 1. Chọn Lớp Ranh giới
        layout.addWidget(QLabel("<b>1. Chọn lớp Ranh giới hành chính (Mask):</b>"))
        self.cb_mask = QComboBox()
        layout.addWidget(self.cb_mask)
        
        # 2. Chọn danh sách các file Raster cần cắt
        layout.addWidget(QLabel("<b>2. Chọn các lớp Raster cần cắt (Giữ Ctrl để chọn nhiều):</b>"))
        self.list_rasters = QListWidget()
        self.list_rasters.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.list_rasters)
        
        # 3. Chọn thư mục lưu Output
        layout.addWidget(QLabel("<b>3. Nơi lưu kết quả (Output Directory):</b>"))
        dir_layout = QHBoxLayout()
        self.lbl_dir = QLabel(os.path.expanduser("~"))
        self.lbl_dir.setStyleSheet("border: 1px solid #ccc; padding: 4px; background: #f9f9f9;")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.lbl_dir)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)
        
        # Nút Run
        self.btn_run = QPushButton("Chạy (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white; padding: 8px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_run)
        
        self.setLayout(layout)
        self.populate_layers()
        
    def populate_layers(self):
        """Lấy danh sách các lớp trong project và tự động chọn tất cả Raster"""
        layers = QgsProject.instance().mapLayers().values()
        
        for layer in layers:
            if layer.type() == QgsMapLayerType.VectorLayer:
                self.cb_mask.addItem(layer.name(), layer)
            elif layer.type() == QgsMapLayerType.RasterLayer:
                self.list_rasters.addItem(layer.name())
                
        # Tự động chọn tất cả các Raster tìm thấy
        for i in range(self.list_rasters.count()):
            self.list_rasters.item(i).setSelected(True)
                
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file kết quả", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(folder)
            
    def validate_and_accept(self):
        if self.cb_mask.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 lớp ranh giới (Vector)!")
            return
        if not self.list_rasters.selectedItems():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất 1 lớp Raster cần cắt!")
            return
        self.accept()

    def get_selected_rasters(self):
        return [item.text() for item in self.list_rasters.selectedItems()]

# --- CHẠY TOOL ---
dialog = ClipRasterDialog()
if dialog.exec_() == QDialog.Accepted:
    mask_layer = dialog.cb_mask.currentData()
    selected_raster_names = dialog.get_selected_rasters()
    output_dir = dialog.lbl_dir.text()
    
    # 1. Tự động khởi tạo cây thư mục nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    
    use_selected = mask_layer.selectedFeatureCount() > 0
    if use_selected:
        print(f"-> Đang cắt theo {mask_layer.selectedFeatureCount()} đối tượng được CHỌN trong '{mask_layer.name()}'.")
    else:
        print(f"-> Đang cắt theo TOÀN BỘ ranh giới của lớp '{mask_layer.name()}'.")
        
    project = QgsProject.instance()
    success_count = 0
    
    for r_name in selected_raster_names:
        r_layers = project.mapLayersByName(r_name)
        if not r_layers:
            continue
            
        raster_layer = r_layers[0]
        
        # 2. Chuẩn hóa tên file và đường dẫn tương thích hệ điều hành
        file_name = f"clipped_{r_name}" if r_name.endswith(".tif") else f"clipped_{r_name}.tif"
        output_path = os.path.normpath(os.path.join(output_dir, file_name))
        
        print(f"Đang xử lý cắt file: {r_name}...")
        
        # 3. Đồng bộ CRS của Raster sang CRS của Mask nếu lệch Hệ tọa độ
        working_raster = raster_layer
        if mask_layer.crs() != raster_layer.crs():
            print(f"   [!] Tự động chuyển CRS của '{r_name}' sang '{mask_layer.name()}'...")
            warp_params = {
                'INPUT': raster_layer,
                'SOURCE_CRS': raster_layer.crs(),
                'TARGET_CRS': mask_layer.crs(),
                'RESAMPLING': 0, # Nearest Neighbor
                'NODATA': None,
                'TARGET_RESOLUTION': None,
                'OPTIONS': '',
                'DATA_TYPE': 0,
                'OUTPUT': 'memory:reprojected_raster'
            }
            warp_res = processing.run("gdal:warpreproject", warp_params)
            working_raster = warp_res['OUTPUT']

        # 4. Cấu hình các tham số cắt với GDAL (Khắc phục viền đen)
        params = {
            'INPUT': working_raster,
            'MASK': mask_layer,
            'SOURCE_CRS': mask_layer.crs(),
            'TARGET_CRS': mask_layer.crs(),
            'NODATA': -9999,           # Gán giá trị NoData để khử viền đen
            'ALPHA_BAND': True,        # Tạo kênh Alpha làm vùng viền ngoài trong suốt 100%
            'CROP_TO_CUTLINE': True,   # Cắt sát viền polygon
            'KEEP_RESOLUTION': True,   # Giữ nguyên độ phân giải pixel gốc
            'SET_RESOLUTION': False,
            'MULTITHREADING': True,
            'OUTPUT': output_path
        }
        
        if use_selected:
            params['SELECTED_FEATURES_ONLY'] = True
            
        try:
            result = processing.run("gdal:cliprasterbymasklayer", params)
            
            # 5. Nạp kết quả đã cắt vào màn hình QGIS
            clipped_layer = QgsRasterLayer(result['OUTPUT'], f"Clipped_{r_name}")
            if clipped_layer.isValid():
                project.addMapLayer(clipped_layer)
                success_count += 1
                print(f"-> Cắt thành công: 'Clipped_{r_name}'!")
            else:
                print(f"Lỗi: Không thể khởi tạo file '{output_path}'.")
        except Exception as e:
            print(f"Thất bại khi cắt '{r_name}': {e}")
            
    QMessageBox.information(None, "Hoàn tất", f"Đã cắt thành công {success_count}/{len(selected_raster_names)} file Raster và nạp vào QGIS!")