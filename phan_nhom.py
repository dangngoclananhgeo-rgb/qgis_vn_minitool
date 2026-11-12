import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import tkinter as tk
from tkinter import filedialog, simpledialog

# ------------------------------
# 🔹 HÀM PHỤ TRỢ
# ------------------------------

def chon_file_excel(root):
    """Mở hộp thoại chọn file Excel."""
    file_path = filedialog.askopenfilename(
        parent=root,
        title="Chọn file Excel dữ liệu dân số",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    return file_path

def tim_so_nhom_toi_uu(data, max_n=6):
    """Tìm số nhóm (K) tối ưu bằng phương pháp Elbow."""
    distortions = []
    # Loại bỏ giá trị NaN nếu có
    data_clean = data.dropna()
    if len(data_clean) < max_n:
        max_n = len(data_clean)
        if max_n < 2:
            return 1
            
    X = np.array(data_clean).reshape(-1, 1)
    for k in range(2, max_n + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
        kmeans.fit(X)
        distortions.append(kmeans.inertia_)
        
    diffs = np.diff(distortions)
    if len(diffs) == 0:
        return 3
    return np.argmin(diffs) + 2

def nhom_phan_doan(df, cot, so_nhom, phuong_phap):
    """Thực hiện chia nhóm dữ liệu theo phương pháp được chỉ định."""
    data = df[cot].dropna().sort_values().values
    
    # Trường hợp số lượng dữ liệu ít hơn số nhóm
    if len(data) < so_nhom:
        so_nhom = max(1, len(data))

    if phuong_phap == "Chia khoảng đều":
        bins = np.linspace(data.min(), data.max(), so_nhom + 1)
        
    elif phuong_phap == "Chia số đối tượng bằng nhau":
        bins = np.quantile(data, np.linspace(0, 1, so_nhom + 1))
        
    elif phuong_phap == "Xét độ chênh lệch":
        bins = [data.min()]
        step = (data.max() - data.min()) / so_nhom
        for _ in range(1, so_nhom):
            bins.append(bins[-1] + step * np.random.uniform(0.8, 1.2))
        bins.append(data.max())
        
    elif phuong_phap == "Cấp số cộng":
        bins = [data.min()]
        cong_sai = (data.max() - data.min()) / (so_nhom * (so_nhom + 1) / 2)
        for i in range(1, so_nhom + 1):
            bins.append(bins[-1] + cong_sai * i)
            
    elif phuong_phap == "Độ lệch chuẩn":
        mean, std = np.mean(data), np.std(data)
        bins = [mean + i * std for i in range(-so_nhom // 2, so_nhom // 2 + 1)]
        bins[0] = min(bins[0], data.min())
        bins[-1] = max(bins[-1], data.max())
        
    elif phuong_phap == "Chia phần giá trị bằng nhau":
        tong = data.sum()
        muc = tong / so_nhom
        bins = [data.min()]
        tong_tam = 0
        for val in data:
            tong_tam += val
            if tong_tam >= muc and len(bins) < so_nhom:
                bins.append(val)
                tong_tam = 0
        bins.append(data.max())
        
    else:
        raise ValueError("Phương pháp không hợp lệ.")
    
    # Đảm bảo các mốc ranh giới là duy nhất (pd.cut yêu cầu bins phải unique)
    bins = np.unique(bins)
    
    # Xử lý ngoại lệ nếu bins bị gom lại chỉ còn 1 phần tử
    if len(bins) == 1:
        bins = [data.min() - 0.1, data.max() + 0.1]
        
    nhom = pd.cut(df[cot], bins=bins, include_lowest=True, labels=False)
    return nhom, bins

# ------------------------------
# 🔹 XỬ LÝ CHÍNH
# ------------------------------
def main():
    # Khởi tạo Tkinter một lần
    root = tk.Tk()
    root.withdraw() # Ẩn cửa sổ chính

    print("🔹 Đang chọn và đọc dữ liệu...")
    file_path = chon_file_excel(root)
    if not file_path:
        print("❌ Không có file nào được chọn. Dừng chương trình.")
        root.destroy()
        return

    try:
        df = pd.read_excel(file_path)
        print(f"✅ Đã đọc dữ liệu: {len(df)} dòng, {len(df.columns)} cột.")
    except Exception as e:
        print(f"❌ Lỗi khi đọc file Excel: {e}")
        root.destroy()
        return

    # Xác định cột dân số
    cot_danso = next((c for c in df.columns if "dân" in c.lower() or "dan" in c.lower()), None)
    
    if not cot_danso:
        print("❌ Không tìm thấy cột dân số trong dữ liệu. Hãy đảm bảo cột có chứa từ 'dân' hoặc 'dan'.")
        root.destroy()
        return

    # ------------------------------
    # 🔹 NHẬP SỐ NHÓM RIÊNG CHO TỪNG PHƯƠNG PHÁP
    # ------------------------------
    phuong_phap_list = [
        "Chia khoảng đều",
        "Chia số đối tượng bằng nhau",
        "Xét độ chênh lệch",
        "Cấp số cộng",
        "Độ lệch chuẩn",
        "Chia phần giá trị bằng nhau"
    ]

    so_nhom_dict = {}
    for ten in phuong_phap_list:
        nhap = simpledialog.askstring(
            title=f"Số nhóm cho: {ten}",
            prompt=f"Nhập số nhóm cho phương pháp '{ten}'\n(Để trống để máy tự tính toán tối ưu):",
            parent=root
        )
        if nhap and nhap.strip().isdigit() and int(nhap.strip()) > 1:
            so_nhom_dict[ten] = int(nhap.strip())
        else:
            so_nhom_dict[ten] = None  # tự tính tối ưu

    # ------------------------------
    # 🔹 THỰC HIỆN PHÂN NHÓM
    # ------------------------------
    writer_path = os.path.splitext(file_path)[0] + "_phan_tich_tonghop.xlsx"
    
    tonghop = pd.DataFrame({cot_danso: df[cot_danso]})
    bang_ranh_gioi = []

    print("\n🔹 Bắt đầu phân tích...")
    try:
        with pd.ExcelWriter(writer_path, engine='openpyxl') as writer:
            for ten in phuong_phap_list:
                # Nếu người dùng để trống, tính toán tối ưu
                so_nhom = so_nhom_dict[ten] if so_nhom_dict[ten] else tim_so_nhom_toi_uu(df[cot_danso])
                print(f"  ➜ Đang xử lý: {ten} (Số nhóm: {so_nhom})")
                
                nhom, bins = nhom_phan_doan(df, cot_danso, so_nhom, ten)
                
                # Tạo bản sao df để ghi vào sheet riêng
                df_kq = df.copy()
                df_kq["Nhóm"] = nhom + 1 # Cộng 1 để tên nhóm bắt đầu từ 1 thay vì 0 (tuỳ chọn cho thân thiện hơn)
                
                # Lưu vào sheet riêng (giới hạn tên sheet 28 ký tự để không lỗi)
                sheet_name = ten[:28]
                df_kq.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Lưu vào bảng tổng hợp
                tonghop[ten] = nhom.astype(str)
                
                # Lưu ranh giới
                bang_ranh_gioi.append({
                    "Phương pháp": ten,
                    "Số nhóm": so_nhom,
                    "Ranh giới": ", ".join([f"{b:.2f}" for b in bins])
                })

            # Ghi các sheet tổng hợp
            tonghop.to_excel(writer, sheet_name="Tổng hợp", index=False)
            pd.DataFrame(bang_ranh_gioi).to_excel(writer, sheet_name="Ranh giới", index=False)

        print(f"\n✅ HOÀN TẤT! File kết quả đã được lưu tại:\n{writer_path}")
        
    except Exception as e:
        print(f"❌ Xảy ra lỗi trong quá trình xử lý/ghi file: {e}")
        
    finally:
        root.destroy() # Đảm bảo tiến trình Tkinter luôn được giải phóng

if __name__ == "__main__":
    main()