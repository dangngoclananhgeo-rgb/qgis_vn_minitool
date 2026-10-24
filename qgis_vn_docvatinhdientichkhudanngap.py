import os
import numpy as np
from qgis.core import QgsProject, QgsMapLayerType
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)

class HighRiskAreaCalcDialog(QDialog):
    def __init__(self, parent=None):
        super(HighRiskAreaCalcDialog, self).__init__(parent)
        self.setWindowTitle("Tính Diện Tích Vùng Nguy Cơ Ngập Cao (Tùy Chọn I/O)")
        self.resize(520, 320)
        
        main_layout = QVBoxLayout()
        
        # 1. Nhóm Chọn Sản phẩm Đầu vào (Raster Nguy cơ ngập)
        gb_input = QGroupBox("1. Chọn sản phẩm đầu vào (Raster Nguy cơ ngập)")
        vbox_input = QVBoxLayout()
        self.cb_raster = QComboBox()
        vbox_input.addWidget(self.cb_raster)
        gb_input.setLayout(vbox_input)
        main_layout.addWidget(gb_input)
        
        # 2. Nhóm Cấu hình Báo cáo Đầu ra (.csv / .txt)
        gb_output = QGroupBox("2. Cấu hình sản phẩm báo cáo đầu ra")
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
        
        # Tên file báo cáo sản phẩm đầu ra
        layout_filename = QHBoxLayout()
        layout_filename.addWidget(QLabel("Tên file sản phẩm:"))
        self.txt_out_name = QLineEdit("ThongKe_NguyCoNgapCao_DanCu.csv")
        layout_filename.addWidget(self.txt_out_name)
        vbox_output.addLayout(layout_filename)
        
        gb_output.setLayout(vbox_output)
        main_layout.addWidget(gb_output)
        
        # Nút Thực thi
        self.btn_run = QPushButton("Tính Toán & Xuất Báo Cáo (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #009688; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_raster_layers()
        
    def populate_raster_layers(self):
        """Liệt kê danh sách tất cả các lớp Raster đang mở trong QGIS Project"""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                self.cb_raster.addItem(layer.name(), layer)
                
    def browse_folder(self):
        """Chọn thư mục lưu báo cáo"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file báo cáo", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(os.path.normpath(folder))
            
    def validate_and_accept(self):
        if self.cb_raster.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 lớp Raster nguy cơ ngập đầu vào!")
            return
            
        filename = self.txt_out_name.text().strip()
        if not filename:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng đặt tên cho sản phẩm báo cáo đầu ra!")
            return
            
        self.accept()

    def get_output_filepath(self):
        folder = self.lbl_dir.text().strip()
        filename = self.txt_out_name.text().strip()
        if not (filename.lower().endswith('.csv') or filename.lower().endswith('.txt')):
            filename += '.csv'
        return os.path.normpath(os.path.join(folder, filename))


# --- CHẠY TOOL XỬ LÝ TÍNH TOÁN VÀ XUẤT BÁO CÁO ---
dialog = HighRiskAreaCalcDialog()
if dialog.exec_() == QDialog.Accepted:
    layer = dialog.cb_raster.currentData()
    layer_name = layer.name()
    output_path = dialog.get_output_filepath()
    
    # 1. Tự động tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # 2. Xử lý trùng file tự động (thêm _1, _2...)
    counter = 1
    base_path, ext = os.path.splitext(output_path)
    final_output_path = output_path
    while os.path.exists(final_output_path):
        final_output_path = f"{base_path}_{counter}{ext}"
        counter += 1

    provider = layer.dataProvider()
    
    # Tính kích thước ô lưới pixel
    pixel_w = layer.rasterUnitsPerPixelX()
    pixel_h = layer.rasterUnitsPerPixelY()
    cell_area_m2 = abs(pixel_w * pixel_h)
    
    block = provider.block(1, layer.extent(), layer.width(), layer.height())
    nodata_val = provider.sourceNoDataValue(1)
    
    high_risk_pixel_count = 0
    total_valid_pixels = 0
    
    print(f"Đang tiến hành phân tích số liệu từ lớp '{layer_name}'...")
    
    for row in range(layer.height()):
        for col in range(layer.width()):
            val = block.value(row, col)
            if val != nodata_val and not np.isnan(val):
                total_valid_pixels += 1
                if val == 1: # Giá trị 1 là vùng nguy cơ ngập cao
                    high_risk_pixel_count += 1
                
    area_m2 = high_risk_pixel_count * cell_area_m2
    area_ha = area_m2 / 10000.0
    percentage = (high_risk_pixel_count / total_valid_pixels * 100) if total_valid_pixels > 0 else 0

    # 3. In kết quả trực tiếp ra cửa sổ Python Console
    print("\n" + "="*75)
    print(f"{'KẾT QUẢ PHÂN TÍCH DIỆN TÍCH KHU DÂN CƯ NGUY CƠ NGẬP CAO (D > 1m)':^75}")
    print("="*75)
    print(f"Lớp dữ liệu nguồn         : {layer_name}")
    print(f"Số ô pixel ngập nguy cơ cao : {high_risk_pixel_count:,} ô")
    print(f"Diện tích ngập nguy cơ cao  : {area_m2:,.2f} m²")
    print(f"Diện tích ngập nguy cơ cao  : {area_ha:,.2f} ha")
    print(f"Tỷ lệ so với toàn khu vực  : {percentage:.2f} %")
    print("="*75 + "\n")

    # 4. Ghi file báo cáo sản phẩm đầu ra (.csv / .txt)
    csv_content = [
        "Chỉ tiêu phân tích,Giá trị,Đơn vị",
        f"Lớp dữ liệu nguồn,\"{layer_name}\",-",
        f"Số ô pixel ngập nguy cơ cao,{high_risk_pixel_count},ô",
        f"Diện tích ngập nguy cơ cao,{area_m2:.2f},m²",
        f"Diện tích ngập nguy cơ cao,{area_ha:.2f},ha",
        f"Tỷ lệ so với tổng khu vực,{percentage:.2f},%"
    ]

    try:
        with open(final_output_path, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(csv_content))
            
        out_filename = os.path.basename(final_output_path)
        print(f"-> Thành công! File báo cáo sản phẩm đã được lưu tại: {final_output_path}")
        QMessageBox.information(
            None, "Hoàn tất", 
            f"Đã hoàn thành tính toán diện tích ngập nguy cơ cao!\n\n"
            f"Tên báo cáo: {out_filename}\n"
            f"Lưu tại: {final_output_path}"
        )
    except Exception as e:
        print(f"Lỗi khi lưu file sản phẩm báo cáo: {e}")