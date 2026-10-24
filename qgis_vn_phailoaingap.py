import os
import processing
from qgis.core import QgsProject, QgsMapLayerType, QgsRasterLayer
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)

class FloodDepthClassDialog(QDialog):
    def __init__(self, parent=None):
        super(FloodDepthClassDialog, self).__init__(parent)
        self.setWindowTitle("Tính và Phân loại Độ sâu Ngập (Tùy chọn Đầu vào/Đầu ra)")
        self.resize(520, 360)
        
        main_layout = QVBoxLayout()
        
        # 1. Nhóm Chọn Lớp Raster DEM đầu vào
        gb_input = QGroupBox("1. Chọn sản phẩm đầu vào (Raster DEM)")
        vbox_input = QVBoxLayout()
        self.cb_dem = QComboBox()
        vbox_input.addWidget(self.cb_dem)
        gb_input.setLayout(vbox_input)
        main_layout.addWidget(gb_input)
        
        # 2. Nhóm Thiết lập Thông số Mực nước Hf
        gb_param = QGroupBox("2. Thiết lập thông số ngập lũ")
        layout_water = QHBoxLayout()
        layout_water.addWidget(QLabel("Mực nước lũ cực đại Hf (m):"))
        self.txt_water_level = QLineEdit("2.5")
        layout_water.addWidget(self.txt_water_level)
        gb_param.setLayout(layout_water)
        main_layout.addWidget(gb_param)
        
        # 3. Nhóm Thiết lập Nơi lưu & Đặt tên sản phẩm đầu ra
        gb_output = QGroupBox("3. Cấu hình sản phẩm đầu ra")
        vbox_output = QVBoxLayout()
        
        # Thư mục lưu
        layout_dir = QHBoxLayout()
        layout_dir.addWidget(QLabel("Thư mục lưu:"))
        default_dir = os.path.join(os.path.expanduser("~"), "Flood_Outputs")
        self.lbl_dir = QLabel(default_dir)
        self.lbl_dir.setStyleSheet("border: 1px solid #ccc; padding: 4px; background: #f9f9f9;")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_folder)
        layout_dir.addWidget(self.lbl_dir)
        layout_dir.addWidget(btn_browse)
        vbox_output.addLayout(layout_dir)
        
        # Tên file sản phẩm đầu ra
        layout_filename = QHBoxLayout()
        layout_filename.addWidget(QLabel("Tên file sản phẩm (.tif):"))
        self.txt_out_name = QLineEdit("Flood_Depth_Class.tif")
        layout_filename.addWidget(self.txt_out_name)
        vbox_output.addLayout(layout_filename)
        
        gb_output.setLayout(vbox_output)
        main_layout.addWidget(gb_output)
        
        # Nút Thực thi
        self.btn_run = QPushButton("Chạy Tính Toán & Phân Loại (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_dem_layers()
        
    def populate_dem_layers(self):
        """Liệt kê toàn bộ các lớp Raster hiện có trong Project QGIS"""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                self.cb_dem.addItem(layer.name(), layer)
                
    def browse_folder(self):
        """Chọn thư mục lưu sản phẩm"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ sản phẩm đầu ra", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(os.path.normpath(folder))
            
    def validate_and_accept(self):
        """Kiểm tra điều kiện hợp lệ trước khi thực thi"""
        if self.cb_dem.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 lớp DEM đầu vào!")
            return
        try:
            float(self.txt_water_level.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập mực nước Hf hợp lệ (số)!")
            return
            
        filename = self.txt_out_name.text().strip()
        if not filename:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng đặt tên cho sản phẩm đầu ra!")
            return
            
        self.accept()

    def get_output_filepath(self):
        """Tạo đường dẫn file hoàn chỉnh"""
        folder = self.lbl_dir.text().strip()
        filename = self.txt_out_name.text().strip()
        if not filename.lower().endswith('.tif'):
            filename += '.tif'
        return os.path.normpath(os.path.join(folder, filename))


# --- CHẠY TOOL XỬ LÝ ---
dialog = FloodDepthClassDialog()
if dialog.exec_() == QDialog.Accepted:
    dem_layer = dialog.cb_dem.currentData()
    dem_name = dem_layer.name()
    h_f = float(dialog.txt_water_level.text().strip())
    output_path = dialog.get_output_filepath()
    
    # 1. Tự động khởi tạo thư mục lưu trữ nếu chưa tồn tại
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # 2. Xử lý trùng file bằng cách tự động đánh số thứ tự (tránh lỗi file bị lock/không ghi đè được)
    counter = 1
    base_path, ext = os.path.splitext(output_path)
    final_output_path = output_path
    while os.path.exists(final_output_path):
        final_output_path = f"{base_path}_{counter}{ext}"
        counter += 1
        
    # 3. Biểu thức tính toán phân loại ngập gộp
    expr = (
        f'(({h_f} - "{dem_name}@1") > 0 AND ({h_f} - "{dem_name}@1") <= 0.5) * 1 + '
        f'(({h_f} - "{dem_name}@1") > 0.5 AND ({h_f} - "{dem_name}@1") <= 1.0) * 2 + '
        f'(({h_f} - "{dem_name}@1") > 1.0 AND ({h_f} - "{dem_name}@1") <= 1.5) * 3 + '
        f'(({h_f} - "{dem_name}@1") > 1.5) * 4'
    )
    
    params = {
        'EXPRESSION': expr,
        'LAYERS': [dem_layer],
        'CELLSIZE': None,
        'EXTENT': dem_layer.extent(),
        'CRS': dem_layer.crs(),
        'OUTPUT': final_output_path
    }
    
    print(f"Đang phân loại ngập từ lớp '{dem_name}' với Hf = {h_f}m...")
    try:
        result = processing.run("qgis:rastercalculator", params)
        
        # 4. Tên hiển thị của sản phẩm trong danh sách Layers của QGIS
        out_title = os.path.splitext(os.path.basename(final_output_path))[0]
        result_layer = QgsRasterLayer(result['OUTPUT'], out_title)
        
        if result_layer.isValid():
            QgsProject.instance().addMapLayer(result_layer)
            print(f"-> Thành công! File kết quả lưu tại: {final_output_path}")
            QMessageBox.information(
                None, "Hoàn tất", 
                f"Đã tính toán phân loại ngập thành công!\n"
                f"Tên sản phẩm: {out_title}\n"
                f"Đường dẫn: {final_output_path}"
            )
        else:
            print("Lỗi: Không thể khởi tạo lớp kết quả.")
    except Exception as e:
        print(f"Thất bại khi thực thi Raster Calculator: {e}")