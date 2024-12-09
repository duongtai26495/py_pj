import pymysql
from zk import ZK, const
from datetime import datetime, time

# Cấu hình kết nối MySQL
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "data_chamcong",
    "charset": "utf8mb4"
}

zk = ZK('172.16.17.106', port=4370, timeout=15)

try:    
    print("Đang kết nối tới máy chấm công...")
    conn = zk.connect()
    print("Kết nối thành công!")

    attendance = conn.get_attendance()
    print("Đang lấy dữ liệu")

    if attendance:
        records = []

        # Thiết lập thời gian lọc
        start_time = time(1, 0)
        end_time = time(23, 0)

        # Thiết lập ngày bắt đầu và kết thúc
        start_date = datetime.strptime("2024-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2024-12-05", "%Y-%m-%d")

        # Lọc dữ liệu
        for record in attendance:
            record_time = record.timestamp
            if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
                user_id = record.user_id
                date_str = record_time.strftime("%Y-%m-%d")
                time_str = record_time.strftime("%H:%M:%S")
                print(f'Dữ liệu: {record}')

                records.append({
                    "user_id": user_id,
                    "date": date_str,
                    "time": time_str
                })

        # Kết nối MySQL
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Tạo bảng nếu chưa tồn tại
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_attendance (user_id, date, time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_table_sql)
        print("Bảng 'attendance' đã được kiểm tra hoặc tạo mới với chỉ mục duy nhất.")

        # Chèn dữ liệu vào bảng với kiểm tra tồn tại
        for record in records:
            # Kiểm tra nếu bản ghi đã tồn tại
            check_sql = """
                SELECT COUNT(*) FROM attendance 
                WHERE user_id = %s AND date = %s AND time = %s
            """
            cursor.execute(check_sql, (record["user_id"], record["date"], record["time"]))
            result = cursor.fetchone()
            
            if result[0] == 0:  # Nếu bản ghi không tồn tại
                # Chèn dữ liệu vào bảng
                sql = """
                    INSERT INTO attendance (user_id, date, time) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (record["user_id"], record["date"], record["time"]))
                print(f"Đã chèn dữ liệu cho user {record['user_id']} vào {record['date']} {record['time']}.")
            else:
                print(f"Dữ liệu đã tồn tại cho user {record['user_id']} vào {record['date']} {record['time']}. Không chèn.")

        connection.commit()
        print("Dữ liệu đã được đẩy vào MySQL!")

        # Đóng kết nối MySQL
        cursor.close()
        connection.close()

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
