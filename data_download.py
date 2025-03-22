import requests
from zk import ZK, const
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import time as time_sleep  # Thư viện để quản lý thời gian chờ
import os
 
# api_endpoint = "http://127.0.0.1:3000/api/upload_sheet"
# api_endpoint = "https://test-d3dv1mxr94fg.sg.larksuite.com/base/workflow/webhook/event/AxTIa3aKewjYzghsrTKlevxkgWc"

# Kết nối tới máy chấm công và xử lý dữ liệu
zk = ZK('172.16.17.106', port=4370, timeout=15)

conn = None

try:
    print("Đang kết nối tới máy chấm công...")
    conn = zk.connect()
    print("Kết nối thành công!")
    # Tiếp tục xử lý các bước khác ở đây

    attendance = conn.get_attendance()
    users = conn.get_users()
    
    print("Đang lấy dữ liệu user")

    if attendance:
        records = []

        start_time = time(18, 0)
        end_time = time(18, 0)
        today = datetime.now()

        # Cập nhật ngày bắt đầu và kết thúc
        start_date = today - timedelta(days=2)
        end_date = today + timedelta(days=1)

        # Kết hợp ngày và thời gian
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        print("Đang xử lý dữ liệu...")
        for record in attendance:
            print(record)
            # print(record)
            # record_time = record.timestamp
            # # Lọc dữ liệu trong khoảng ngày và giờ
            # if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
            #     user_id = record.user_id
            #     date_str = record_time.strftime("%Y/%m/%d")
            #     time_str = record_time.strftime("%H:%M:%S")
            #     # Thêm vào danh sách
            #     records.append({
            #         "user_id": user_id,
            #         "date": date_str,
            #         "time": time_str
            #     })
        # else:
    #     #     print("Không có dữ liệu chấm công trong khoảng thời gian đã chọn.")
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
    # else:
    #     print("Không có kết nối để ngắt.")

# input("Nhấn Enter để thoát...")
