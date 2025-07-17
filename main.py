import os
import cv2
import csv
from datetime import datetime
from ultralytics import YOLO  # type: ignore
from paddleocr import PaddleOCR  # type: ignore
import torch  # type: ignore
import pymysql
import re

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

class LicensePlateRecognizer:
    def __init__(self, model_path, csv_file, resolution=(640, 360)):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(model_path).to(self.device)
        self.ocr = PaddleOCR(
    lang='en',
    use_textline_orientation=False,  # tat tinh nang tu dong xoay
    ocr_version='PP-OCRv3',
    use_doc_orientation_classify=False, #tat tinh nang phan loai huong
    use_doc_unwarping=False   #Tat tu dong hieu chinh van ban
)
        self.csv_file = csv_file
        self.resolution = resolution
        self.confidence_threshold = 0.8
        self.setup_csv()
        self.cap = self.setup_camera()

        cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        self.display_resolution = (360, 360)  # Nhẹ hơn cho hiển thị
        cv2.resizeWindow('Camera Feed', *self.display_resolution)

    def setup_csv(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Ngay', 'Gio_vao_ra', 'Anh', 'Bien_so'])

    def setup_camera(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Backend nhanh hơn
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        return cap

    def detect_license_plate(self, frame):
        results = self.model(frame, conf=self.confidence_threshold)
        return results[0]

    def perform_ocr(self, roi):
        try:
        # Kiểm tra nếu ảnh vẫn là BGR thì chuyển sang grayscale
            if len(roi.shape) == 3:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_roi = roi

        # Tiền xử lý ảnh
            enhanced = self.enhance_image(gray_roi)
            denoised = self.denoise_image(enhanced)
            resized = self.resize_image(denoised, (320, 160))
            processed = self.preprocess_image(resized)

        # Lưu ROI đã tiền xử lý ra file để test nếu cần
            cv2.imwrite("test_roi.jpg", processed)

        # Chuyển về 3 kênh để đưa vào OCR
            final_roi = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

        # Gọi OCR (predict trả về dict)
            ocr_result = self.ocr.ocr(final_roi)
            print("OCR result raw:", ocr_result)

        # ✅ Dành cho PaddleOCR >= 2.6 (3.1 hiện tại)
            recognized_texts = []
            if ocr_result and isinstance(ocr_result[0], dict):
                texts = ocr_result[0].get('rec_texts', [])
                scores = ocr_result[0].get('rec_scores', [])
                for text, score in zip(texts, scores):
                    if score >= 0.5:
                        recognized_texts.append(text)

            #print("Kết quả OCR:", recognized_texts)
            #return ' '.join(recognized_texts) if recognized_texts else 'Not detected'
            if recognized_texts:
                cleaned = re.sub(r'[^A-Z0-9]', '', ''.join(recognized_texts).upper())
                print("Biển số đã xử lý:", cleaned)
                return cleaned
            else:
                return 'Not detected'

        except Exception as e:
            print(f"OCR Error: {e}")
            return 'Error'


# Các hàm hỗ trợ
    def enhance_image(self, image):
    # Tăng độ sáng và tương phản
        enhanced = cv2.convertScaleAbs(image, alpha=1.5, beta=20)
        return enhanced

    def denoise_image(self, image):
    # Áp dụng lọc GaussianBlur
        denoised = cv2.GaussianBlur(image, (5, 5), 0)
        return denoised

    def resize_image(self, image, target_size=(320, 160)):
        resized = cv2.resize(image, target_size)
        return resized

    def preprocess_image(self, image):
    # Dùng adaptive threshold để phù hợp nhiều điều kiện sáng
        thresholded = cv2.adaptiveThreshold(
        image, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # Dùng giá trị trung bình có trọng số (Gaussian) của vùng lân cận
        cv2.THRESH_BINARY, # Nếu giá trị pixel > ngưỡng cục bộ → đặt thành 255 (trắng), ngược lại → 0 (đen)
        11, 2
    )
        return thresholded

    def save_results(self, frame, timestamp, boxes, names):
        current_datetime = datetime.now()
        Ngay = current_datetime.strftime('%Y-%m-%d')
        Gio_vao = current_datetime.strftime('%H:%M:%S')

        annotated_frame = frame.copy()
        Bien_so = 'Not detected'

        if len(boxes) > 0:
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                roi = frame[y1:y2, x1:x2]
                Bien_so = self.perform_ocr(roi)
                if Bien_so not in ['Not detected', 'Error'] and Bien_so.strip():
                    print(f"📤 Gửi {Bien_so} lên MySQL...")
                    try:
                        send_to_mysql(Bien_so)
                    except Exception as e:
                        print("❌ Gặp lỗi khi gửi MySQL:", e)
                else:
                    print("❗ Không gửi lên MySQL vì kết quả không hợp lệ:", Bien_so)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, Bien_so, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    # Nếu không có box, giữ nguyên Bien_so = 'Not detected'

        Ket_qua = f'Ket_qua_{timestamp}.jpg'
        cv2.imwrite(Ket_qua, annotated_frame)
        return Ket_qua, Ngay, Gio_vao, Bien_so
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            result = self.detect_license_plate(frame)
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            resized_frame = cv2.resize(frame, self.display_resolution)
            cv2.imshow('Camera Feed', resized_frame)
            key = cv2.waitKey(1)

            if key & 0xFF == ord('s'):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
                Ket_qua_path, Ngay, Gio_vao, Bien_so = self.save_results(frame, timestamp, result.boxes, result.names)
                with open(self.csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([Ngay, Gio_vao, Ket_qua_path, Bien_so])

                annotated_image = cv2.imread(Ket_qua_path)
                resized_annotated_image = cv2.resize(annotated_image, self.display_resolution)
                cv2.imshow('Ket qua', resized_annotated_image)
                #cv2.waitKey(0)
                cv2.destroyWindow('Ket qua')

            elif key & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
        

def send_to_mysql(number_plate):
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="parking",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            sql_check = "SELECT * FROM vehicles WHERE number_plate=%s AND date_out IS NULL"
            cursor.execute(sql_check, (number_plate,))
            result = cursor.fetchone()

            if result:
                sql_update = "UPDATE vehicles SET date_out=NOW(), status=0 WHERE id=%s"
                cursor.execute(sql_update, (result['id'],))
                print(f"🚗 Xe {number_plate} đã ra lúc:", datetime.now())
            else:
                sql_insert = "INSERT INTO vehicles (number_plate, status, date_in) VALUES (%s, %s, NOW())"
                cursor.execute(sql_insert, (number_plate, 1))
                print(f"🚗 Xe {number_plate} đã vào lúc:", datetime.now())

            conn.commit()
    except Exception as e:
        print("❌ MySQL error:", e)
    finally:
        conn.close()
  

if __name__ == "__main__":
    recognizer = LicensePlateRecognizer(model_path='best.pt', csv_file='Xe_vao.csv')
    recognizer.run()

