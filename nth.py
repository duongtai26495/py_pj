from zk import ZK, const
import csv
from datetime import datetime, timedelta
import os

def connect_device(ip, port, start_date, end_date):
    zk = ZK(ip, port=port, timeout=20, ommit_ping=True)
    try:
        conn = zk.connect()
        print("Đã kết nối thành công với máy chấm công!")

        now = datetime.now()
        print(f"Bắt đầu: {now}") 
        attendances = conn.get_attendance()
        users = conn.get_users()

        records = {}
        if attendances:
            for record in attendances:
                if start_date <= record.timestamp <= end_date:
                    uid = record.user_id
                    
                    date_str = record.timestamp.strftime("%Y-%m-%d")
                    key = (uid, date_str)
                    time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                    records.setdefault(key, set()).add(time_str)
        
        
        rows = []
        for user in users:
            uid = user.user_id 
            user_keys = [key for key in records if key[0] == uid]
            if user_keys: 
                for key in sorted(user_keys, key=lambda k: k[1]):
                    times = sorted(list(records[key]))[:6]
                    row = [uid] + times
                    if len(times) < 6:
                        row += [''] * (6 - len(times))
                    rows.append(row)
            else: 
                rows.append([uid] + [''] * 6)
         
        batch_data = []
        for row in rows: 
            if len(row) < 7:
                row.extend([''] * (7 - len(row)))
            data_obj = {
                "ID": "NT"+row[0],
                "Time1": row[1],
                "Time2": row[2],
                "Time3": row[3],
                "Time4": row[4],
                "Time5": row[5],
                "Time6": row[6]
            }
            batch_data.append(data_obj)
        
        total_rows = len(batch_data)
        print(f"Tổng số bản ghi cần gửi: {total_rows}")
        print(batch_data)
        conn.disconnect()

        now = datetime.now()
        print(f"Kết thúc: {now}")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")

# Địa chỉ IP và cổng của máy chấm công
ip_address = "14.179.55.199"
port = 4370


now = datetime.now()
start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
connect_device(ip_address, port, start_date, end_date)