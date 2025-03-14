import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext  # Thêm dòng này nếu chưa có import
from datetime import datetime, timedelta
import pandas as pd
from zk import ZK
from dateutil.relativedelta import relativedelta
import time
import requests
import threading
import json
from threading import Thread
from tkcalendar import Calendar
from tkinter import ttk
# Biến toàn cục để kiểm soát trạng thái
is_running = False
stop_event = threading.Event()  # Để kiểm soát việc dừng

start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=27)
end_date = datetime.now() + relativedelta(days=1)


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
    zk = ZK('172.16.17.106', port=4370, timeout=15)
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
                if stop_event.is_set():  # Kiểm tra dừng ngay tại đây
                    break
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
                    row = [user_id] + timestamps
                    rows.append(row)

            total_rows = len(rows)
            for index, row in enumerate(rows):
                if stop_event.is_set():  # Kiểm tra dừng tại mỗi lần gửi
                    break
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

def on_date_select(event, start_date_cal, end_date_cal):
    global start_date, end_date
    start_date_str = start_date_cal.get_date()
    end_date_str = end_date_cal.get_date()

    # Chuyển đổi ngày theo định dạng mong muốn
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
    end_date = datetime.strptime(end_date_str, '%m/%d/%Y')

    end_date += relativedelta(days=1)


def stop_process():
    global is_running
    stop_event.set()  # Đánh dấu sự kiện dừng
    is_running = False  # Dừng tiến trình và đồng hồ
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Quá trình đã dừng.")
        log_box.update()
    root.quit()  # Đảm bảo thoát khỏi vòng lặp chính của Tkinter


def update_timer(start_time, time_label):
    if is_running and not stop_event.is_set() and root.winfo_exists():
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        if time_label.winfo_exists():
            time_label.config(text=f"{minutes:02}:{seconds:02}")
        root.after(1000, update_timer, start_time, time_label)  # Gọi lại sau 1 giây

def start_process(log_box, time_label):
    global is_running
    stop_event.clear()  # Xóa sự kiện dừng
    is_running = True  # Bắt đầu tiến trình
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\nBắt đầu xử lý... Vui lòng không thao tác gì thêm cho tới khi hoàn tất.")
        adjusted_end_date = end_date - relativedelta(days=1)
        log_box.insert(tk.END, f"\n\u2022 Tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} về.")
        log_box.update()

    start_time = time.time()

    # Bắt đầu cập nhật đồng hồ
    threading.Thread(target=update_timer, args=(start_time, time_label), daemon=True).start()

    # Tiến hành tải dữ liệu
    try:
        download_data(log_box)  # Tiến hành tải dữ liệu
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
    finally:
        is_running = False  # Kết thúc quá trình


root = tk.Tk()


def on_close():
    global is_running
    is_running = False  # Dừng đồng hồ và tiến trình
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Đang thoát chương trình...")
        log_box.update()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.geometry("600x500")  # Adjust the window size as needed

# UI Setup (Center all elements)
log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=15, bd=2, relief="sunken")
log_box.grid(row=0, column=0, columnspan=4, padx=15, pady=10, sticky="nsew")

# Frame for date selection widgets
frame = ttk.Frame(root, padding="10 5 10 5")
frame.grid(row=1, column=0, columnspan=4, padx=15, pady=10, sticky="ew")

# Start date selection (day, month, year)
start_date_label = ttk.Label(frame, text="Ngày bắt đầu:", font=("Arial", 12))
start_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Day, Month, Year comboboxes for start date
start_day_combobox = ttk.Combobox(frame, values=[str(i).zfill(2) for i in range(1, 32)], width=5, state="readonly")
start_day_combobox.grid(row=1, column=0, padx=5, pady=5)

start_month_combobox = ttk.Combobox(frame, values=[str(i).zfill(2) for i in range(1, 13)], width=5, state="readonly")
start_month_combobox.grid(row=1, column=1, padx=5, pady=5)

start_year_combobox = ttk.Combobox(frame, values=[str(i) for i in range(1900, datetime.now().year+1)], width=7, state="readonly")
start_year_combobox.grid(row=1, column=2, padx=5, pady=5)

# End date selection (day, month, year)
end_date_label = ttk.Label(frame, text="Ngày kết thúc:", font=("Arial", 12))
end_date_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")

# Day, Month, Year comboboxes for end date
end_day_combobox = ttk.Combobox(frame, values=[str(i).zfill(2) for i in range(1, 32)], width=5, state="readonly")
end_day_combobox.grid(row=1, column=3, padx=5, pady=5)

end_month_combobox = ttk.Combobox(frame, values=[str(i).zfill(2) for i in range(1, 13)], width=5, state="readonly")
end_month_combobox.grid(row=1, column=4, padx=5, pady=5)

end_year_combobox = ttk.Combobox(frame, values=[str(i) for i in range(1900, datetime.now().year+1)], width=7, state="readonly")
end_year_combobox.grid(row=1, column=5, padx=5, pady=5)

# Set default values for comboboxes
start_day_combobox.set(str((datetime.now() - timedelta(days=30)).day).zfill(2))
start_month_combobox.set(str((datetime.now() - timedelta(days=30)).month).zfill(2))
start_year_combobox.set(str((datetime.now() - timedelta(days=30)).year))

end_day_combobox.set(str(datetime.now().day).zfill(2))
end_month_combobox.set(str(datetime.now().month).zfill(2))
end_year_combobox.set(str(datetime.now().year))

# Timer Label
time_label = ttk.Label(root, text="00:00", font=("Arial", 14), foreground="blue")
time_label.grid(row=2, column=0, columnspan=4, pady=10)

# Frame for Start and Stop Buttons to make them appear side by side
button_frame = ttk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

# Start Button
start_button = ttk.Button(button_frame, text="Bắt đầu", width=20, command=lambda: start_process(log_box, time_label))
start_button.grid(row=0, column=0, padx=5)

# Stop Button
stop_button = ttk.Button(button_frame, text="Thoát", width=20, style="TButton", command=stop_process)
stop_button.grid(row=0, column=1, padx=5)

# Centering the widgets
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# You can also add these for the other rows/columns if necessary:
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(4, weight=1)

root.mainloop()