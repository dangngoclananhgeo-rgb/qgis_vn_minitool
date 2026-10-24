# QGIS VN Mini Tool

**QGIS VN Mini Tool** là bộ công cụ mã nguồn mở (PyQGIS scripts) được tạo ra chỉ để tác giả tự động hóa các tác vụ xử lý dữ liệu không gian, phân tích mô hình ngập lụt đô thị và chuẩn hóa cơ sở dữ liệu GIS. Bộ công cụ đặc biệt tối ưu cho các dự án nghiên cứu địa lý, viễn thám và môi trường tại Việt Nam, tích hợp sẵn các chức năng chuyển đổi hệ tọa độ VN2000 và kết xuất báo cáo thống kê diện tích rủi ro ngập lụt.

## 📂 Cấu trúc tính năng

Bộ công cụ bao gồm 8 module chính hoạt động trực tiếp trên nền tảng QGIS:

*   **`qgis_vn_catdem.py`**: Công cụ tự động cắt dữ liệu mô hình độ cao số (DEM) theo ranh giới lớp mask (hành chính hoặc khu vực nghiên cứu).
*   **`qgis_vn_cattheoranhgioi_line.py`**: Cắt bóc tách các lớp dữ liệu không gian dựa trên vector ranh giới dạng đường (line).
*   **`qgis_vn_chuyenhetoado_vn2000.py`**: Tự động hóa quá trình tái lập phép chiếu (reproject), đồng bộ hệ quy chiếu của các lớp dữ liệu về hệ tọa độ quốc gia VN2000.
*   **`qgis_vn_docvatinhdientichkhudanngap.py`**: Trích xuất lớp dữ liệu dân cư, chồng lớp với bản đồ ngập và tự động tính toán tổng diện tích khu vực bị ngập.
*   **`qgis_vn_phailoaingap.py`**: Xử lý và tái phân loại (reclassify) các khu vực không gian theo trạng thái ngập/không ngập.
*   **`qgis_vn_phanloaidongap.py`**: Phân ngưỡng các giá trị pixel để phân loại chi tiết độ sâu ngập thành các cấp độ/kịch bản rủi ro khác nhau.
*   **`qgis_vn_phantichkhudancubianhhuongngapnuocvavungnguycocao.py`**: Phân tích không gian đa tiêu chí để khoanh vùng các khu dân cư chịu ảnh hưởng nặng và đánh giá mức độ phơi nhiễm tại các vùng nguy cơ cao.
*   **`qgis_vn_thongkengap.py`**: Kết xuất báo cáo thống kê không gian về tình trạng ngập lụt.

## 🚀 Yêu cầu hệ thống
*   Hệ điều hành: Windows / macOS / Linux.
*   Phần mềm: QGIS 3.x trở lên.
*   Môi trường: Tích hợp sẵn Python 3 và thư viện GDAL đi kèm QGIS.

## ⚙️ Hướng dẫn sử dụng
1. Mở phần mềm QGIS.
2. Trên thanh công cụ, chọn **Plugins** > **Python Console** (hoặc nhấn `Ctrl + Alt + P`).
3. Mở biểu tượng **Show Editor** trong cửa sổ Python Console.
4. Tải xuống và mở bất kỳ file script `.py` nào từ kho lưu trữ này vào Editor.
5. Tùy chỉnh lại các đường dẫn file input/output trong đoạn mã theo cấu trúc thư mục máy tính của bạn.
6. Nhấn nút **Run script** (biểu tượng nút Play xanh lá) để thực thi tự động.

## 👤 Tác giả
*   **Đặng Ngọc Lan Anh**
*   GitHub: [@dangngoclananhgeo-rgb](https://github.com/dangngoclananhgeo-rgb)
