import requests
from zk import ZK, const
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import time as time_sleep  # Thư viện để quản lý thời gian chờ
import os
 
api_endpoint = "http://127.0.0.1:3000/api/upload_sheet"
# api_endpoint = "https://test-d3dv1mxr94fg.sg.larksuite.com/base/workflow/webhook/event/AxTIa3aKewjYzghsrTKlevxkgWc"

# Kết nối tới máy chấm công và xử lý dữ liệu
zk = ZK('14.164.169.207', port=4370, timeout=15)

conn = None

try:
    print("Đang kết nối tới máy chấm công...")
    conn = zk.connect()
    print("Kết nối thành công!")
    # Tiếp tục xử lý các bước khác ở đây

    attendance = conn.get_attendance()
    print("Đang lấy dữ liệu")

    if attendance:
        records = []

        start_time = time(1, 0)
        end_time = time(23, 59)
        today = datetime.now()

        # Cập nhật ngày bắt đầu và kết thúc
        start_date = (today.replace(day=1) - relativedelta(months=1)).replace(day=27)
        end_date = today + timedelta(days=1)

        # Kết hợp ngày và thời gian
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        print("Đang xử lý dữ liệu...")

        for record in attendance:
            record_time = record.timestamp
            # Lọc dữ liệu trong khoảng ngày và giờ
            if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
                user_id = record.user_id
                date_str = record_time.strftime("%Y/%m/%d")
                time_str = record_time.strftime("%H:%M:%S")
                # Thêm vào danh sách
                records.append({
                    "user_id": user_id,
                    "date": date_str,
                    "time": time_str
                })

        # Kiểm tra xem có dữ liệu không
        if records:
            total_records = len(records)  # Tổng số bản ghi
            count = 0  # Biến đếm số lần gửi dữ liệu
            max_value = 1000
            # Gửi từng dòng dữ liệu một lần, mỗi lần tối đa 20 bản ghi
            for i, record in enumerate(records):
                response = requests.post(api_endpoint, json={"attendance_records": [record]})
                
                if response.status_code != 200:
                    print(f"Đã xảy ra lỗi khi gửi bản ghi {i+1}: {response.status_code}, {response.text}")
                
                count += 1
                
                # Tính toán phần trăm tiến độ
                progress = (count / max_value) * 100
                os.system('cls')
                print(f"Đang tải dữ liệu\nTiến độ: {progress:.2f}%")

                # Mỗi 100 bản ghi, dừng một chút trước khi gửi tiếp
                if count % max_value == 0:
                    print(f"Đã gửi {max_value} bản ghi.")
                    break
                
                # Nghỉ giữa mỗi lần gửi request 0.5 giây
                # time_sleep.sleep(0.02)
            print(f"Số dòng đã gửi: {total_records}\nTừ {start_datetime} đến {end_datetime}")
        else:
            print("Không có dữ liệu chấm công trong khoảng thời gian đã chọn.")
    else:
        print("Không có dữ liệu chấm công trong khoảng thời gian đã chọn.")

    conn.disconnect()
    print("Ngắt kết nối với máy chấm công.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")
finally:
    if conn and conn.is_connect:
        conn.disconnect()
        print("Đã ngắt kết nối với máy chấm công.")
    else:
        print("Không có kết nối để ngắt.")

input("Nhấn Enter để thoát...")
