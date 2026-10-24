import os
import numpy as np
from qgis.core import QgsProject, QgsMapLayerType
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)

class FloodStatisticsDialog(QDialog):
    def __init__(self, parent=None):
        super(FloodStatisticsDialog, self).__init__(parent)
        self.setWindowTitle("Thống kê Diện tích Ngập Lũ (Bảng 13)")
        self.resize(520, 320)
        
        main_layout = QVBoxLayout()
        
        # 1. Nhóm Chọn Lớp Raster Phân Loại Ngập Đầu Vào
        gb_input = QGroupBox("1. Chọn sản phẩm đầu vào (Raster Phân Loại Ngập)")
        vbox_input = QVBoxLayout()
        self.cb_raster = QComboBox()
        vbox_input.addWidget(self.cb_raster)
        gb_input.setLayout(vbox_input)
        main_layout.addWidget(gb_input)
        
        # 2. Nhóm Cấu Hình Sản Phẩm Báo Cáo Đầu Ra
        gb_output = QGroupBox("2. Cấu hình sản phẩm báo cáo đầu ra (.csv / .txt)")
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
        
        # Tên file báo cáo sản phẩm đầu ra
        layout_filename = QHBoxLayout()
        layout_filename.addWidget(QLabel("Tên file sản phẩm:"))
        self.txt_out_name = QLineEdit("ThongKe_DienTich_NgapLu.csv")
        layout_filename.addWidget(self.txt_out_name)
        vbox_output.addLayout(layout_filename)
        
        gb_output.setLayout(vbox_output)
        main_layout.addWidget(gb_output)
        
        # Nút Thực thi
        self.btn_run = QPushButton("Tính Toán & Xuất Báo Cáo (Run)")
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_run.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.btn_run)
        
        self.setLayout(main_layout)
        self.populate_raster_layers()
        
    def populate_raster_layers(self):
        """Liệt kê tất cả các lớp Raster hiện có trong QGIS Project"""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                self.cb_raster.addItem(layer.name(), layer)
                
    def browse_folder(self):
        """Chọn thư mục lưu báo cáo"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu sản phẩm báo cáo", self.lbl_dir.text())
        if folder:
            self.lbl_dir.setText(os.path.normpath(folder))
            
    def validate_and_accept(self):
        if self.cb_raster.currentIndex() == -1:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 lớp Raster phân loại ngập đầu vào!")
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


# --- CHẠY TOOL XỬ LÝ THỐNG KÊ ---
dialog = FloodStatisticsDialog()
if dialog.exec_() == QDialog.Accepted:
    raster_layer = dialog.cb_raster.currentData()
    layer_name = raster_layer.name()
    output_path = dialog.get_output_filepath()
    
    # 1. Tự động khởi tạo thư mục lưu trữ nếu chưa có
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # 2. Xử lý trùng file bằng cách tự động đánh số thứ tự (_1, _2...)
    counter = 1
    base_path, ext = os.path.splitext(output_path)
    final_output_path = output_path
    while os.path.exists(final_output_path):
        final_output_path = f"{base_path}_{counter}{ext}"
        counter += 1

    provider = raster_layer.dataProvider()
    
    # Kích thước ô lưới pixel
    pixel_width = raster_layer.rasterUnitsPerPixelX()
    pixel_height = raster_layer.rasterUnitsPerPixelY()
    cell_area_m2 = abs(pixel_width * pixel_height)
    
    # Đọc dữ liệu pixel từ Band 1
    block = provider.block(1, raster_layer.extent(), raster_layer.width(), raster_layer.height())
    nodata_val = provider.sourceNoDataValue(1)
    
    stats = {}
    total_valid_pixels = 0
    
    print(f"Đang tiến hành thống kê diện tích từ lớp '{layer_name}'...")
    
    for row in range(raster_layer.height()):
        for col in range(raster_layer.width()):
            val = block.value(row, col)
            if val != nodata_val and not np.isnan(val):
                val_int = int(val)
                stats[val_int] = stats.get(val_int, 0) + 1
                total_valid_pixels += 1

    class_labels = {
        0: ("Không ngập", "≤ 0 m"),
        1: ("Ngập nông", "0 – 0,5 m"),
        2: ("Ngập trung bình", "0,5 – 1,0 m"),
        3: ("Ngập sâu", "1,0 – 1,5 m"),
        4: ("Ngập rất sâu", "> 1,5 m")
    }

    total_area_m2 = total_valid_pixels * cell_area_m2
    total_area_ha = total_area_m2 / 10000.0

    # In kết quả trực tiếp ra cửa sổ Python Console
    print("\n" + "="*85)
    print(f"{'BẢNG 13: KẾT QUẢ THỐNG KÊ DIỆN TÍCH NGẬP LŨ':^85}")
    print("="*85)
    print(f"{'Mã':<4} | {'Mức độ ngập':<18} | {'Độ sâu':<12} | {'Số pixel':<10} | {'Diện tích (m²)':<16} | {'Diện tích (ha)':<15} | {'Tỷ lệ (%)':<10}")
    print("-" * 85)

    # Đưa dữ liệu vào danh sách để ghi file CSV
    csv_rows = ["Mã,Mức độ ngập,Độ sâu,Số pixel,Diện tích (m²),Diện tích (ha),Tỷ lệ (%)"]

    for code in range(5):
        count = stats.get(code, 0)
        area_m2 = count * cell_area_m2
        area_ha = area_m2 / 10000.0
        percentage = (count / total_valid_pixels * 100) if total_valid_pixels > 0 else 0
        
        label_info = class_labels.get(code, ("Không xác định", "-"))
        
        print(f"{code:<4} | {label_info[0]:<18} | {label_info[1]:<12} | {count:<10,d} | {area_m2:<16,.2f} | {area_ha:<15,.2f} | {percentage:<10.2f}")
        csv_rows.append(f'{code},"{label_info[0]}","{label_info[1]}",{count},{area_m2:.2f},{area_ha:.2f},{percentage:.2f}')

    print("-" * 85)
    print(f"{'TỔNG CỘNG':<38} | {total_valid_pixels:<10,d} | {total_area_m2:<16,.2f} | {total_area_ha:<15,.2f} | 100.00%")
    print("="*85 + "\n")
    csv_rows.append(f'TỔNG,TỔNG CỘNG,-,{total_valid_pixels},{total_area_m2:.2f},{total_area_ha:.2f},100.00')

    # 3. Ghi file sản phẩm báo cáo đầu ra (.csv / .txt)
    try:
        with open(final_output_path, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(csv_rows))
            
        out_filename = os.path.basename(final_output_path)
        print(f"-> Thành công! Báo cáo đã được xuất ra file: {final_output_path}")
        QMessageBox.information(
            None, "Hoàn tất", 
            f"Đã hoàn thành thống kê diện tích ngập lũ!\n\n"
            f"Sản phẩm báo cáo: {out_filename}\n"
            f"Lưu tại: {final_output_path}"
        )
    except Exception as e:
        print(f"Lỗi khi lưu file sản phẩm báo cáo: {e}")