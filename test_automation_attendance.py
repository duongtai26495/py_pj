import time
import schedule
import threading
import requests
from datetime import datetime, timedelta
from zk import ZK

API_URL = "https://open-sg.larksuite.com/anycross/trigger/callback/MGFlYTc5ZGI3ZmI5ZjgxZDFkYjUxZDgyMDY3ZGY5Njgw"
LARKBOT_URL = 'https://open.larksuite.com/open-apis/bot/v2/hook/992413a8-ee5f-4a62-8742-aca039cf5263'
IP = "172.16.17.106"
PORT = 4370

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

def send_batch_to_api(batch):
    try:
        response = requests.post(API_URL, json=batch)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi khi gửi batch: {e}")
        return False

def download_data_bg(start_date, end_date):
    send_notify(f"Đang kết nối tới máy chấm công {IP}:{PORT}...")
    zk = ZK(IP, PORT, timeout=15)
    conn = None
    try:
        conn = zk.connect()
        send_notify("Kết nối thành công!")
        
        # Lấy attendance và danh sách user
        attendance = conn.get_attendance()
        users = conn.get_users()
        
        # Tạo dict lưu attendance theo cặp (user_id, ngày)
        # key: (uid, date_str), value: set(mốc thời gian định dạng "YYYY-MM-DD HH:MM")
        records = {}
        if attendance:
            for record in attendance:
                if start_date <= record.timestamp <= end_date:
                    uid = record.user_id
                    # Lấy ngày theo định dạng "YYYY-MM-DD" để phân nhóm theo ngày
                    date_str = record.timestamp.strftime("%Y-%m-%d")
                    key = (uid, date_str)
                    time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                    records.setdefault(key, set()).add(time_str)
        
        # Tạo danh sách rows:
        # - Nếu user có attendance: tạo 1 row cho mỗi ngày có data.
        # - Nếu user không có attendance: chỉ tạo 1 row trống duy nhất.
        rows = []
        for user in users:
            uid = user.user_id
            # Tìm các key có uid này
            user_keys = [key for key in records if key[0] == uid]
            if user_keys:
                # Nếu có, tạo 1 row cho mỗi ngày có data
                for key in sorted(user_keys, key=lambda k: k[1]):
                    times = sorted(list(records[key]))[:6]
                    row = [uid] + times
                    if len(times) < 6:
                        row += [''] * (6 - len(times))
                    rows.append(row)
            else:
                # Nếu không có attendance, chỉ tạo 1 row trống duy nhất
                rows.append([uid] + [''] * 6)
        
        # Tạo payload cho API: mỗi row gồm 7 trường: ID, Time1 ... Time6
        batch_data = []
        for row in rows:
            # Đảm bảo row có đủ 7 phần tử
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
            batch_data.append(data_obj)
        
        total_rows = len(batch_data)
        print(f"Tổng số bản ghi cần gửi: {total_rows}")
        
        # Gửi dữ liệu theo batch (payload là list)
        if total_rows > 1000:
            batch_size = 1000
            sent_count = 0
            batch = []
            for data_obj in batch_data:
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
            if batch:
                if not send_batch_to_api(batch):
                    for item in batch:
                        print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
                sent_count += len(batch)
                percentage = (sent_count / total_rows) * 100
                print(f"Đã gửi {percentage:.2f}% - {sent_count}/{total_rows}")
        else:
            if not send_batch_to_api(batch_data):
                for item in batch_data:
                    print(f"Gửi dữ liệu của ID {item['ID']} thất bại.")
            print(f"Đã gửi 100.00% - {total_rows}/{total_rows}")
        
        print(f"Quá trình xử lý hoàn tất. Đã tải dữ liệu từ {start_date.strftime('%d/%m/%Y %H:%M')} đến {end_date.strftime('%d/%m/%Y %H:%M')} lên base.")
        
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        if conn and conn.is_connect:
            conn.disconnect()
def job_9():
    now = datetime.now()
    # Lấy dữ liệu từ 00:00 đến 09:00 hôm nay
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=9, minute=0, second=0, microsecond=0)
    send_notify("Chạy job 09:00 - Lấy dữ liệu từ 00:00 đến 09:00 hôm nay.")
    download_data_bg(start_date, end_date, "1")

def job_14():
    now = datetime.now()
    # Lấy dữ liệu từ 00:00 đến 14:00 hôm nay
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=14, minute=0, second=0, microsecond=0)
    send_notify("Chạy job 14:00 - Lấy dữ liệu từ 00:00 đến 14:00 hôm nay.")
    download_data_bg(start_date, end_date,"2")

def job_20():
    now = datetime.now()
    # Lấy dữ liệu từ 18:00 của ngày hôm qua đến 18:00 hôm nay
    start_date = (now - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=18, minute=0, second=0, microsecond=0)
    send_notify("Chạy job 18:00 - Lấy dữ liệu từ 18:00 ngày hôm qua đến 18:00 hôm nay.")
    download_data_bg(start_date, end_date,"3")

def main():
    send_notify("Chương trình lấy chấm công đã khởi động")
    schedule.every().day.at("09:00").do(job_9)
    schedule.every().day.at("15:37").do(job_14)
    schedule.every().day.at("18:00").do(job_20)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
