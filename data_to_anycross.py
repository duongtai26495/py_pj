import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import pandas as pd
import os
from zk import ZK
from dateutil.relativedelta import relativedelta
import time
import requests
import threading
import gspread
import json
from threading import Thread
# Biến toàn cục để kiểm soát trạng thái
is_running = False

start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=27)
end_date = datetime.now() + relativedelta(days=1)

def stop_process():
    global is_running
    is_running = False  # Dừng tiến trình
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Quá trình đã dừng.")
        log_box.update()
    root.quit()  # Đảm bảo thoát khỏi vòng lặp chính của Tkinter



CREDENTIALS_JSON = """
{
  "type": "service_account",
  "project_id": "euphoric-anchor-443703-u8",
  "private_key_id": "7df72c6d1e798bb26dc900cc22638655424b4a0b",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDqpuQjo/skRSGM\\ny7fpnPuxdpb0fvzi/epRYGmSMf+1qyLFlaSG7rQcsd3MUld3zZox4993XTtfsLve\\n0EqubyNcefZNMqjGyAilx/J1HBfeA2qtJvdYpWimY77poBn13Snd78M6TTi2uTPF\\nDUbiN+3yfN8jZGhBhRotqeySRSLJdVd/8xLAHdnFwJiKZhdCBQy312I+sjqbwAmZ\\nlGCP5cDdMbY4thF5HIDYpwrW2TQMQlHvoCuASFec674d1w/UUtaNrHgqTbkpO8wx\\nX/D05Kzwj6eoJBZw5MM6COBThAd4eKkOoRTf6rPtfeGSVHuPtrlYiAUKjWgGAU5C\\n/Hjswo4bAgMBAAECggEAGOsLHAvMXiAnPWvexmSgx8onoqQfl71OFkEuRNOha3nW\\ncfP/qkKMBuYOfyWZW0QOpVClCOhyJym98Z3d6GMt9qKO+Mix6pYQcQZoJW6LzExB\\nlkymhJfgIpdCDU4uo5DOYt6UtUrBBIprSHgt+FTnJFKFYZ1Ggvqu+n1qfWfxF0J2\\nLxaYJh5UDRN0fvxxlRqPpf71AaI/UNrMXXW+EhGkNLDSe4Ocbndmlc5aQ44zIfy5\\nMIuNfz3WpI3ap+M21x9mCWn6JnLy6+zIBiEF2796BCdc8taWzl6IGQbC30cC1YO6\\nI0aFMgnvz2LUBa2wVhbtGH2yerKxKPbz3zEoxeKkrQKBgQD3kMDlQRKunyHA6HTP\\nIgeK36Up6eylTlC8evpCSLDaTVXuF6W9X2JXuK98WsaJtmm2Vv/d451I8fvsubrn\\nNuvdMV3aEfdKt2SFuEqisoAASjUzyJfdTAogDaW2pEVRW14bDkorsMLYgRGz6sGf\\nK0Hlzg+YHKzjPCnOLZJUtEfhtwKBgQDypYHFJmBDP4E6dKUZWh9bmu2ZU+9RGckV\\nYcQf8LzKOdGyTcDSRINxMi1xZEZb1LOwNDI+PmVt0GuItwIR+urbrr127Cyq7DI+\\nn3KN4tosB2UGOvk/Fg3qdYm8HwlewAmOBQYPZp8ZTRh/XtyhlSFysOYw2JKYs4vg\\nv1Hm5k5mvQKBgQDMzeLWhcv3zEv3NBeWWBeXSsdvckdExhJCqxYoCczM/FePXd7O\\nWH+aBH6gyNQgj1jK8RRBs5CmDRKV110I9MWRuspioqRLGoa9nSWZjUQZeUqkKVmB\\nSOvDcqbZ/vIdiRHEHkE7/cJjq/tCNX6yt+2POLZr56UbY+VN3SOGkZI55wKBgGqs\\nsJyH/pIR/TJBzcOTh22ycvqRmAjDmU+5J4wTPix5tuL4o+jNDixZrvjG6Ne+bzDs\\nAZqzu8vHcT8tlc9pzI7AB7OcqRaLuJsnZilSri/lIFjY3HMLsxp8ig0WZ/wr2QeC\\n1eM3boKlDjwQ7FZtRcMyWkDnNavEY55u/gbRAW7RAoGBANZ/B9a4pNqZIiyX2qmU\\nJyMWXBnt9dpU4Tn7pjh2ZBw2cNijbiu45tyOg2Ip5NSw+qaeaeCjOX1LDTOqto9m\\n2znLCwGOTl/bwUNZANIv1KitTQA32Q8ZqMU0ceZ6ip09v9dXgh7MVNtXk0dcmhmm\\nE+LF8DR2VrBzjmE+4XrndRpn\\n-----END PRIVATE KEY-----\\n",
  "client_email": "tech-marcom@euphoric-anchor-443703-u8.iam.gserviceaccount.com",
  "client_id": "100128971919198032941",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tech-marcom%40euphoric-anchor-443703-u8.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""

# Sử dụng JSON làm dữ liệu chứng thực
CREDENTIALS = json.loads(CREDENTIALS_JSON)


def upload_to_google_sheet(df, file_id, sheet_name):
    try:
        # Khởi tạo client Google Sheets
        gc = gspread.service_account_from_dict(CREDENTIALS)
        spreadsheet = gc.open_by_key(file_id)

        # Xóa các worksheet cũ, chỉ giữ lại một worksheet duy nhất
        worksheets = spreadsheet.worksheets()
        for worksheet in worksheets[:-1]:
            spreadsheet.del_worksheet(worksheet)

        remaining_sheet = spreadsheet.worksheets()[-1]
        remaining_sheet.update_title(sheet_name)

        remaining_sheet.clear()
        remaining_sheet.update(df.values.tolist())

        sheet_link = f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
        return sheet_link

    except Exception as e:
        raise Exception(f"Lỗi khi thao tác với Google Sheets: {e}")

def send_to_api(row):
    try:
        api_url = "https://open-sg.larksuite.com/anycross/trigger/callback/MDgxNDZlMWMyNzNhODVlMzI5NjViNmZhNWFiY2UzMzBj"  # Thay đổi URL API của bạn tại đây
        response = requests.post(api_url, json=row)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False
    
def download_data(log_box):
    # zk = ZK('172.16.17.106', port=4370, timeout=15)
    zk = ZK('27.70.151.180', port=4370, timeout=15)
    try:
        if log_box.winfo_exists():
            log_box.insert(tk.END, "\n\u2022 Đang kết nối tới máy chấm công...")
            log_box.update()
        conn = zk.connect()
        if log_box.winfo_exists():
            log_box.insert(tk.END, "\n\u2022 Kết nối thành công!")


        attendance = conn.get_attendance()
        if attendance:
            records = {}
            

            for record in attendance:
                if start_date <= record.timestamp <= end_date:
                    user_id = record.user_id
                    date_key = record.timestamp.strftime("%Y-%m-%d")
                    time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")

                    if date_key not in records:
                        records[date_key] = {}
                    if user_id not in records[date_key]:
                        records[date_key][user_id] = []
                    records[date_key][user_id].append(time_str)

            rows = []
            for date, users in records.items():
                for user_id, timestamps in users.items():
                    timestamps = sorted(timestamps)[:6]
                    row = [user_id] + timestamps  # Dữ liệu sẽ bao gồm ID và các mốc thời gian đã lọc
                    rows.append(row)

            df = pd.DataFrame(rows, columns=["ID", "Timestamp 1", "Timestamp 2", "Timestamp 3", "Timestamp 4", "Timestamp 5", "Timestamp 6"])
            file_id = "1Z_eAq_5MshvWG1Ri_IbKlqFVuswhJTlHgJrN0nKrx64"
            sheet_name = "Data_ChamCong"

            link = upload_to_google_sheet(df.fillna(""), file_id, sheet_name)

            total_rows = len(rows)
            for index, row in enumerate(rows):
                if len(row) < 7:
                    row.extend([''] * (7 - len(row)))  # Thêm các giá trị trống để đủ 7 phần tử

                if send_to_api({
                    "ID": int(row[0]),  # Chuyển ID thành số
                    "Time1": row[1] if len(row) > 1 else '',
                    "Time2": row[2] if len(row) > 2 else '',
                    "Time3": row[3] if len(row) > 3 else '',
                    "Time4": row[4] if len(row) > 4 else '',
                    "Time5": row[5] if len(row) > 5 else '',
                    "Time6": row[6] if len(row) > 6 else ''
                }):
                    pass
                else:
                    if log_box.winfo_exists():
                        log_box.insert(tk.END, f"\n\u2022 Gửi dữ liệu của {row[0]} thất bại.")
                        log_box.update()
                log_box.update()

                percentage = (index + 1) / total_rows * 100
                first = index + 1
                log_box.insert(tk.END, f"\n\u2022 Đã gửi {percentage:.2f}% - {first}/{total_rows}")
                log_box.update()

                if (index + 1) % 400 == 0:
                    time.sleep(5)

                log_box.yview_moveto(1)

                adjusted_end_date = end_date - relativedelta(days=1)


            log_box.insert(
                tk.END,
                f"\n\u2022 Quá trình xử lý hoàn tất.\nĐã tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} lên base."
            )
        else:
            log_box.insert(tk.END, "\n\u2022 Không có dữ liệu chấm công nào.")

        conn.disconnect()
    except Exception as e:
        log_box.insert(tk.END, f"\n\u2022 Đã xảy ra lỗi: {e}")
    finally:
        if conn and conn.is_connect:
            conn.disconnect()
def start_process(log_box, time_label):
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\nBắt đầu xử lý... Vui lòng không thao tác gì thêm cho tới khi hoàn tất.")
        adjusted_end_date = end_date - relativedelta(days=1)
        log_box.insert(tk.END, f"\n\u2022 Tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} về.")
        log_box.update()

    
    # Bắt đầu thời gian từ khi bấm nút
    start_time = time.time()

    # Hàm cập nhật thời gian
    def update_timer():
        while is_running and root.winfo_exists():
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(int(elapsed_time), 60)
            if time_label.winfo_exists():
                time_label.config(text=f"{minutes:02}:{seconds:02}")
            time.sleep(0.1)  # Kiểm tra thường xuyên hơn để phản hồi nhanh



    # Chạy bộ đếm thời gian trong nền
    threading.Thread(target=update_timer, daemon=True).start()

    try:
        download_data(log_box)  # Tiến hành tải dữ liệu
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")


root = tk.Tk()

def on_close():
    global is_running
    is_running = False  # Dừng các tiến trình đang chạy
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Đang thoát chương trình...")
        log_box.update()
    root.destroy()  # Phá hủy cửa sổ Tkinter


root.protocol("WM_DELETE_WINDOW", on_close)


root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.geometry("500x400")

log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=15)
log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Continue the UI setup for buttons and labels
frame = tk.Frame(root)
frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)

# Start Button
start_button = tk.Button(frame, text="Bắt đầu", width=50, command=lambda: start_process(log_box, time_label))
start_button.pack(side=tk.LEFT, padx=5)

# Chỉ giữ lại nút "Thoát"
stop_button = tk.Button(frame, text="Thoát", width=50, command=stop_process)
stop_button.pack(side=tk.LEFT, padx=5)


# Timer Label
time_label = tk.Label(root, text="00:00", font=("Arial", 14))
time_label.pack(side=tk.BOTTOM, pady=10)


root.mainloop()
