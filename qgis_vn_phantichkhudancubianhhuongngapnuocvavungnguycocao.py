import os
import processing
from qgis.core import (
    QgsProject, QgsMapLayerType, QgsRasterLayer, QgsVectorLayer
)
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)

class HighRiskFloodDialog(QDialog):
    def __init__(self, parent=None):
        super(HighRiskFloodDialog, self).__init__(parent)
        self.setWindowTitle("Tính Vùng Nguy Cơ Ngập Cao (Dân Cư & Ngập > 1m)")
        self.resize(520, 380)
        
        main_layout = QVBoxLayout()
        
        # 1. Nhóm Chọn Sản phẩm Đầu vào
        gb_input = QGroupBox("1. Chọn sản phẩm đầu vào")
        vbox_input = QVBoxLayout()
        
        vbox_input.addWidget(QLabel("Lớp Phân loại / Độ sâu ngập (Raster):"))
        self.cb_flood = QComboBox()
        vbox_input.addWidget(self.cb_flood)
        
        vbox_input.addWidget(QLabel("Lớp Sử dụng đất / Khu dân cư (Vector hoặc Raster):"))
        self.cb_landuse = QComboBox()
        vbox_input.addWidget(self.cb_landuse)
        
        gb_input.setLayout(vbox_input)
        main_layout.addWidget(gb_input)
        
        # 2. Nhóm Cấu hình Sản phẩm Đầu ra
        gb_output = QGroupBox("2. Cấu hình sản phẩm đầu ra (.tif)")
        vbox_output = QVBoxLayout()
        
        # Thư mục lưu
        layout_dir = QHBoxLayout()
        layout_dir.addWidget(QLabel("Thư mục lưu:"))
        default_dir = r"C:\Users\DANG NGOC LAN ANH\Downloads\angiang\map\output\vn2000_dem_angiang_gis\tinhtoan"
        self.lbl_dir = QLabel(default_dir)
        self.lbl_dir.setStyleSheet("border: 1px solid #ccc; padding: 4px; background: #f9f9f9;")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_folder)
        layout_dir.addWidget(self.lbl_dir)
        layout_dir.addWidget(btn_browse)
        vbox_output.addLayout(layout_dir)
        
        # Tên file sản phẩm đầu ra
        layout_filename = QHBoxLayout()
        layout_filename.addWidget(QLabel("Tên file sản phẩm:"))
        self.txt_out_name = QLineEdit("NguyCoNgapCao_DanCu.tif")
        layout_filename.addWidget(self.txt_out_name)
        vbox_output.addLayout(layout_filename)
        
        gb_output.setLayout(vbox_output)
        main_layout.addWidget(gb_output)
        
        # Nút Thực thi
        self.btn_run = QPushButton("Tính Toán Vùng Nguy Cơ (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #E91E63; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_layers()
        
    def populate_layers(self):
        """Liệt kê danh sách các lớp phù hợp hiện có trong QGIS Project"""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                self.cb_flood.addItem(f"[Raster] {layer.name()}", layer)
                self.cb_landuse.addItem(f"[Raster] {layer.name()}", layer)
            elif layer.type() == QgsMapLayerType.VectorLayer:
                self.cb_landuse.addItem(f"[Vector] {layer.name()}", layer)
                
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file sản phẩm đầu ra", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(os.path.normpath(folder))
            
    def validate_and_accept(self):
        if self.cb_flood.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn lớp phân loại ngập đầu vào!")
            return
        if self.cb_landuse.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn lớp Khu dân cư / Landuse!")
            return
            
        filename = self.txt_out_name.text().strip()
        if not filename:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng đặt tên cho sản phẩm đầu ra!")
            return
            
        self.accept()

    def get_output_filepath(self):
        folder = self.lbl_dir.text().strip()
        filename = self.txt_out_name.text().strip()
        if not filename.lower().endswith('.tif'):
            filename += '.tif'
        return os.path.normpath(os.path.join(folder, filename))


# --- CHẠY TOOL XỬ LÝ VÙNG NGUY CƠ NGẬP CAO ---
dialog = HighRiskFloodDialog()
if dialog.exec_() == QDialog.Accepted:
    flood_layer = dialog.cb_flood.currentData()
    landuse_layer = dialog.cb_landuse.currentData()
    output_path = dialog.get_output_filepath()
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    counter = 1
    base_path, ext = os.path.splitext(output_path)
    final_output_path = output_path
    while os.path.exists(final_output_path):
        final_output_path = f"{base_path}_{counter}{ext}"
        counter += 1

    project = QgsProject.instance()
    
    # 1. Chuyển đổi lớp Landuse sang Raster nếu đang ở dạng Vector
    if isinstance(landuse_layer, QgsVectorLayer):
        print(f"Đang tự động Rasterize lớp Vector '{landuse_layer.name()}'...")
        temp_landuse_raster = os.path.normpath(os.path.join(output_dir, "temp_landuse_raster.tif"))
        
        params_rasterize = {
            'INPUT': landuse_layer,
            'FIELD': None,
            'BURN': 1,
            'UNITS': 1, # Georeferenced units
            'WIDTH': flood_layer.rasterUnitsPerPixelX(),
            'HEIGHT': flood_layer.rasterUnitsPerPixelY(),
            'EXTENT': flood_layer.extent(),
            'NODATA': 0,
            'OUTPUT': temp_landuse_raster
        }
        res = processing.run("gdal:rasterize", params_rasterize)
        landuse_raster = QgsRasterLayer(res['OUTPUT'], "temp_landuse_raster")
    else:
        landuse_raster = landuse_layer

    # 2. Sử dụng GDAL Raster Calculator để tránh lỗi "Error parsing formula"
    print(f"Đang tính toán vùng nguy cơ ngập cao kết hợp '{flood_layer.name()}' và '{landuse_layer.name()}'...")
    
    # Công thức GDAL: (A >= 3) * (B == 1)
    # A: Lớp ngập (Mã >= 3 tương ứng độ sâu ngập > 1m)
    # B: Lớp dân cư/landuse (Giá trị == 1)
    gdal_calc_expr = "(A >= 3) * (B == 1)"
    
    params_gdal_calc = {
        'INPUT_A': flood_layer,
        'BAND_A': 1,
        'INPUT_B': landuse_raster,
        'BAND_B': 1,
        'FORMULA': gdal_calc_expr,
        'NO_DATA': 0,
        'RTYPE': 5, # Float32
        'OUTPUT': final_output_path
    }
    
    try:
        result_risk = processing.run("gdal:rastercalculator", params_gdal_calc)
        
        # 3. Nạp sản phẩm vào QGIS
        out_title = os.path.splitext(os.path.basename(final_output_path))[0]
        risk_layer = QgsRasterLayer(result_risk['OUTPUT'], out_title)
        
        if risk_layer.isValid():
            project.addMapLayer(risk_layer)
            print(f"-> Thành công! File kết quả lưu tại: {final_output_path}")
            QMessageBox.information(
                None, "Hoàn tất", 
                f"Đã tính toán thành công vùng nguy cơ ngập cao!\n"
                f"Tên sản phẩm: {out_title}\n"
                f"Lưu tại: {final_output_path}"
            )
        else:
            print("Lỗi: Không thể nạp sản phẩm đầu ra vào QGIS.")
    except Exception as e:
        print(f"Thất bại khi tính toán Raster Calculator: {e}")