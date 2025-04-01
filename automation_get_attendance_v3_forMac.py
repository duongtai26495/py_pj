import time
import schedule
import threading
from pync import Notifier
import requests
from datetime import datetime, timedelta
from zk import ZK

# URL API và base_token dùng chung
API_URL = "https://open-sg.larksuite.com/anycross/trigger/callback/MDA3YjJlZTE0MGEzMDllZmY3YzVjNjI3M2RmZTgwYmVj"
API_URL_MONTHLY = "https://open-sg.larksuite.com/anycross/trigger/callback/MGVhNGJkZWU3MzIyZjI2MTg0YWE1NjIzM2M4NDk3YTU5"
LARKBOT_URL = 'https://open.larksuite.com/open-apis/bot/v2/hook/992413a8-ee5f-4a62-8742-aca039cf5263'
BASE_TOKEN = "CeSDbFSWvaRjAgsmCWclZ0UEgpc"

# Cấu hình table_id cho từng khoảng thời gian
TABLE_ID_COMMON = "tblpoL5MDY8cbM3b"         # Dùng cho 9h, 14h, 18h (có step)
TABLE_ID_20 = "tblIde0y5kgOeRXr"               # Dùng cho 20h (không có step)
TABLE_ID_MONTHLY = "tbleADv6H7H0olJo"          # Dùng cho monthly job (không có step)

# Cấu hình máy chấm công
IP = "172.16.17.106"
PORT = 4370
DEFAULT_SECOND_IP = "14.179.55.199"
SECOND_PORT = 4370
SECOND_PREFIX = "NT"

# Endpoint lấy second ip
SECOND_IP_API = "https://endpoint.binhthuanford.com/api/get_ip_nt"

def get_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip_data = response.json()
        return ip_data['ip']
    except Exception as e:
        print(f"Error fetching IP: {e}")
        return None

def send_notify(message):
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    try:
        response = requests.post(LARKBOT_URL, json=payload)
        if response.status_code == 200:
            print("Thông báo gửi thành công.")
        else:
            print(f"Thông báo gửi thất bại, mã lỗi: {response.status_code}")
    except Exception as e:
        print(f"Lỗi khi gửi thông báo: {e}")

def send_batch_to_api(all_data, table_id, remove, common):

    payload = {
        "data": {},
        "length": len(all_data),
        "base_token": BASE_TOKEN,
        "table_id": table_id,
        "remove": remove,
        "common": common
    }
    batch_size = 1000
    total = len(all_data)
    num_batches = (total + batch_size - 1) // batch_size
    for i in range(num_batches):
        start = i * batch_size
        end = start + batch_size
        key = f"data{i+1}"
        payload["data"][key] = all_data[start:end]
    
    try:
        response = requests.post(API_URL, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi khi gửi batch: {e}")
        return False

def get_second_ip():
    try:
        response = requests.get(SECOND_IP_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            second_ip = data.get("ip", DEFAULT_SECOND_IP)
            send_notify(f"Lấy second ip thành công: {second_ip}")
            return second_ip
        else:
            send_notify(f"Lỗi khi lấy second ip, mã lỗi: {response.status_code}. Sử dụng mặc định.")
            return DEFAULT_SECOND_IP
    except Exception as e:
        send_notify(f"Lỗi khi lấy second ip: {e}. Sử dụng mặc định.")
        return DEFAULT_SECOND_IP

def get_data_from_device(ip, port, prefix=""):
    zk = ZK(ip, port, timeout=30, ommit_ping=True)
    conn = None
    try:
        conn = zk.connect()
        attendance = conn.get_attendance()
        users = conn.get_users()
        if prefix:
            for record in attendance:
                record.user_id = prefix + str(record.user_id)
            for user in users:
                user.user_id = prefix + str(user.user_id)
        return attendance, users
    except Exception as e:
        send_notify(f"Lỗi khi kết nối tới máy chấm công {ip}:{port} - {e}")
        return [], []
    finally:
        if conn and conn.is_connect:
            try:
                conn.disconnect()
                send_notify(f"Đã ngắt kết nối máy {ip}:{port}")
            except Exception as e:
                send_notify(f"Lỗi khi ngắt kết nối máy {ip}:{port}: {e}")

def download_data_bg_combined(start_date, end_date, step, table_id, remove, common):
    # Lấy second ip từ API
    second_ip = get_second_ip()
    send_notify(f"Đang kết nối tới máy chấm công {IP}:{PORT} và {second_ip}:{SECOND_PORT}...")
    
    attendance1, users1 = get_data_from_device(IP, PORT, prefix="")
    attendance2, users2 = get_data_from_device(second_ip, SECOND_PORT, prefix=SECOND_PREFIX)
    
    attendance = attendance1 + attendance2
    combined_users = users1 + users2
    
    records = {}
    if attendance:
        for record in attendance:
            if start_date <= record.timestamp <= end_date:
                uid = record.user_id
                date_str = record.timestamp.strftime("%Y-%m-%d")
                key = (uid, date_str)
                time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                records.setdefault(key, set()).add(time_str)
                
    rows = []
    for user in combined_users:
        uid = user.user_id
        keys = [key for key in records if key[0] == uid]
        if keys:
            for key in sorted(keys, key=lambda k: k[1]):
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
            "ID": row[0],
            "Time1": row[1],
            "Time2": row[2],
            "Time3": row[3],
            "Time4": row[4],
            "Time5": row[5],
            "Time6": row[6]
        }
        if step is not None:
            data_obj["Step"] = step
        batch_data.append(data_obj)
        
    total_rows = len(batch_data)
    print(f"Tổng số bản ghi cần gửi: {total_rows}")
    
    if not send_batch_to_api(batch_data, table_id, remove, common):
        for item in batch_data:
            print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
    else:
        print(f"Đã gửi {total_rows} bản ghi.")
        
    send_notify(f"Quá trình xử lý hoàn tất. Đã tải dữ liệu từ {start_date.strftime('%d/%m/%Y %H:%M')} đến {end_date.strftime('%d/%m/%Y %H:%M')} lên base.")

def monthly_job():
    now = datetime.now()
    if now.month == 1:
        start_date = datetime(now.year - 1, 12, 28, 0, 0, 0)
    else:
        start_date = datetime(now.year, now.month - 1, 28, 0, 0, 0)
    end_date = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
    
    step = None    # Monthly job không có step
    table_id = TABLE_ID_MONTHLY
    remove = 1
    common = 0   # Monthly job không phải common
    send_notify(f"Lấy dữ liệu từ {start_date.strftime('%d/%m/%Y %H:%M')} đến {end_date.strftime('%d/%m/%Y %H:%M')}")
    download_data_bg_combined(start_date, end_date, step, table_id, remove, common)
    
def job(target_hour):
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    
    # Với 9,14,18 giờ: có step và common=1; với 20 giờ: không có step và common=0.
    if target_hour in [9, 14, 18]:
        step = {9: "1", 14: "2", 18: "3"}[target_hour]
        table_id = TABLE_ID_COMMON
        remove = 1
        common = 1
    elif target_hour == 20:
        step = None
        table_id = TABLE_ID_20
        remove = 0
        common = 0
    else:
        step = None
        table_id = TABLE_ID_COMMON
        remove = 1
        common = 0

    send_notify(f"Lấy dữ liệu đến {target_hour}h hôm nay.")
    download_data_bg_combined(start_date, end_date, step, table_id, remove, common)

def show_startup_notification():
    Notifier.notify("Ứng dụng đã được khởi động", title="Chương trình lấy chấm công")

def main():
    show_startup_notification()
    current_ip = get_ip()
    send_notify(f"Chương trình lấy chấm công đã được khởi động tại: {current_ip}")
    
    # Thiết lập trigger cho các thời điểm
    schedule.every().day.at("09:00").do(lambda: job(9))
    schedule.every().day.at("15:19").do(lambda: job(14))
    schedule.every().day.at("18:00").do(lambda: job(18))
    schedule.every().day.at("20:00").do(lambda: job(20))
    
    # Trigger monthly job lúc 09:05 hàng ngày
    schedule.every().day.at("09:05").do(monthly_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
