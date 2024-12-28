from zk import ZK, const
import pandas as pd
from datetime import datetime, time

# zk = ZK('172.16.17.101', port=4370, timeout=15)
zk = ZK('172.16.17.106', port=4370, timeout=15)

try:
    print("Đang kết nối tới máy chấm công...")
    conn = zk.connect()
    print("Kết nối thành công!")

    attendance = conn.get_attendance()
    print("Đang đang lấy dữ liệu")

    if attendance:
        records = []

        start_time = time(1, 0)
        end_time = time(23, 59)

        start_date = datetime.strptime("2024-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2024-12-05", "%Y-%m-%d")

        for record in attendance:
            record_time = record.timestamp
            if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
                user_id = record.user_id
                date_str = record_time.strftime("%Y-%m-%d")
                time_str = record_time.strftime("%H:%M:%S")
                print(f'Dữ liệu: {record}')

    else:
        print("Không có dữ liệu chấm công nào.")

    conn.disconnect()
    print("Ngắt kết nối với máy chấm công.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")

finally:
    if conn and conn.is_connect:
        conn.disconnect()
        print("Đã ngắt kết nối với máy chấm công.")
    else:
        print("Đã ngắt kết nối thành công.")
