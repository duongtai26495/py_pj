from zk import ZK
from datetime import datetime, timedelta
import requests


SECOND_IP_API = "https://endpoint.binhthuanford.com/api/get_ip_nt"
def get_second_ip():

    try:
        response = requests.get(SECOND_IP_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            second_ip = data.get("ip", "DEFAULT_SECOND_IP")
            return second_ip
       
    except Exception as e:
            return "Secon IP"
    

def connect_device(port, start_date, end_date):
    # second_ip = get_second_ip()
    print(f"Đang kết nối: 113.162.244.51 {port}")
    zk = ZK("113.162.244.51", port=port, timeout=15, ommit_ping=True)
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
port = 24370


now = datetime.now()
start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
connect_device(port, start_date, end_date)