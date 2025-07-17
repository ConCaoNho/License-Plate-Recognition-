Bước 1: Lấy file data trên roboflow https://universe.roboflow.com/vietnam-license/vietnam-license-plate-hjswj 
Bước 2: Training model trên google colab bằng file Training_data.ipynb
Bước 3: Lấy file best.pt sau khi training được nhúng vào code chính tại file main.py
Bước 4: Chạy chương trình, khi detect được biển số xe thì nhấn "s"
Bước 5: Kết quả được gửi lên MySQL, lưu tại file Xe_vao.csv, tên database là parking, bảng dữ liệu là vehicles gồm 5 cột id, status, number_plate, date_in, date_out
Bước 6: Tính toán tiền khi gửi xe quá 30p trên app
