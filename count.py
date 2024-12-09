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

        start_time = time(7, 0)
        end_time = time(18, 0)

        start_date = datetime.strptime("2024-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2024-12-05", "%Y-%m-%d")

        for record in attendance:
            record_time = record.timestamp
            if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
                user_id = record.user_id
                date_str = record_time.strftime("%Y-%m-%d")
                time_str = record_time.strftime("%H:%M:%S")
                print(f'Dữ liệu: {record}')

                records.append({
                    "User ID": user_id,
                    "Date": date_str,
                    "Time": time_str
                })
        df = pd.DataFrame(records)

        # Thêm cột định danh duy nhất cho mỗi lần chấm công
        df["UniqueID"] = df.groupby(["User ID", "Date"]).cumcount() + 1

        # Pivot dữ liệu với mỗi lần chấm công là một dòng riêng biệt
        df_pivot = df.pivot(index=["User ID", "UniqueID"], columns="Date", values="Time").reset_index()

        # Loại bỏ cột UniqueID nếu không cần hiển thị
        df_pivot = df_pivot.drop(columns=["UniqueID"])

        df_pivot = df_pivot.reindex(columns=["User ID"] + sorted(df["Date"].unique()))
        print(f'Đang ghi dữ liệu vào file')
      
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")  
        file_name = f"Data_cham_cong_{timestamp}.xlsx"

        df_pivot.to_excel(file_name, index=False)
        print(f"Dữ liệu đã được ghi vào file Excel: {file_name}")
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
