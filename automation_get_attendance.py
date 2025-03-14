import time
import schedule
import threading
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from zk import ZK  # Thư viện kết nối máy chấm công

# Cấu hình cố định
API_URL = "https://open-sg.larksuite.com/anycross/trigger/callback/MDcyOWY1ZjgyMThmNTBhYWM2NWUyMzZkNGM3NWJkMjZm"
IP = "172.16.17.106"
PORT = 4370

def send_notify(message):
    """
    Gửi thông báo tới API (ở đây là check_attendance_status).
    """
    endpoint = 'https://bthfapiservices-production.up.railway.app/api/check_attendance_status'
    payload = {
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            print("Thông báo gửi thành công.")
        else:
            print(f"Thông báo gửi thất bại, mã lỗi: {response.status_code}")
    except Exception as e:
        print(f"Lỗi khi gửi thông báo: {e}")

def send_batch_to_api(batch):
    """
    Gửi một batch dữ liệu đến API.
    """
    try:
        response = requests.post(API_URL, json=batch)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi khi gửi batch: {e}")
        return False

def download_data_bg(start_date, end_date):
    """
    Kết nối tới máy chấm công, lấy dữ liệu chấm công trong khoảng thời gian [start_date, end_date]
    và gửi lên API theo dạng batch.
    """
    print(f"Đang kết nối tới máy chấm công {IP}:{PORT}...")
    zk = ZK(IP, PORT, timeout=15)
    conn = None
    try:
        conn = zk.connect()
        print("Kết nối thành công!")
        attendance = conn.get_attendance()
        if attendance:
            records = {}
            for record in attendance:
                # Lọc dữ liệu trong khoảng thời gian
                if start_date <= record.timestamp <= end_date:
                    user_id = record.user_id
                    date_key = record.timestamp.strftime("%Y-%m-%d")
                    time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                    records.setdefault(date_key, {}).setdefault(user_id, []).append(time_str)
            
            # Tạo mảng rows với mỗi dòng gồm: [user_id, time1, time2, ..., time6]
            rows = []
            for date, users in records.items():
                for user_id, timestamps in users.items():
                    timestamps = sorted(timestamps)[:6]  # Lấy tối đa 6 lần chấm công
                    row = [user_id] + timestamps
                    rows.append(row)
            
            total_rows = len(rows)
            if total_rows > 400:
                batch_size = 400
                batch = []
                sent_count = 0
                for row in rows:
                    if len(row) < 7:
                        row.extend([''] * (7 - len(row)))
                    data_obj = {
                        "ID": int(row[0]),
                        "Time1": row[1],
                        "Time2": row[2],
                        "Time3": row[3],
                        "Time4": row[4],
                        "Time5": row[5],
                        "Time6": row[6]
                    }
                    batch.append(data_obj)
                    if len(batch) == batch_size:
                        if not send_batch_to_api(batch):
                            for item in batch:
                                print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
                        sent_count += len(batch)
                        percentage = (sent_count / total_rows) * 100
                        print(f"Đã gửi {percentage:.2f}% - {sent_count}/{total_rows}")
                        batch = []
                        time.sleep(2)
                # Gửi phần dư nếu có
                if batch:
                    if not send_batch_to_api(batch):
                        for item in batch:
                            print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
                    sent_count += len(batch)
                    percentage = (sent_count / total_rows) * 100
                    print(f"Đã gửi {percentage:.2f}% - {sent_count}/{total_rows}")
            else:
                # Nếu dữ liệu nhỏ, gửi 1 lần
                batch = []
                for row in rows:
                    if len(row) < 7:
                        row.extend([''] * (7 - len(row)))
                    data_obj = {
                        "ID": int(row[0]),
                        "Time1": row[1],
                        "Time2": row[2],
                        "Time3": row[3],
                        "Time4": row[4],
                        "Time5": row[5],
                        "Time6": row[6]
                    }
                    batch.append(data_obj)
                if not send_batch_to_api(batch):
                    for item in batch:
                        print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
                print(f"Đã gửi 100.00% - {len(batch)}/{len(batch)}")
            
            adjusted_end_date = end_date - relativedelta(days=1)
            print(f"Quá trình xử lý hoàn tất. Đã tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} lên base.")
        else:
            print("Không có dữ liệu chấm công nào.")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        if conn and conn.is_connect:
            conn.disconnect()

def job_update_range():
  
    now = datetime.now()
    if now.month == 1:
        start_date = datetime(now.year - 1, 12, 27)
    else:
        start_date = datetime(now.year, now.month - 1, 27)
    end_date = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    print(f"Chạy job: từ {start_date} đến {end_date}")
    download_data_bg(start_date, end_date)

def main():
    print("Ứng dụng chạy ngầm. Đang lên lịch các job...")
    # Ví dụ lên lịch job vào 17:15 và 21:00 hàng ngày (bạn có thể điều chỉnh theo ý muốn)
    schedule.every().day.at("17:32").do(job_update_range)
    schedule.every().day.at("21:00").do(job_update_range)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
