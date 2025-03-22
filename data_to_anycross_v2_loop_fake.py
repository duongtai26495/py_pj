import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta
import pandas as pd
# Bỏ import ZK vì không cần dùng nữa
from dateutil.relativedelta import relativedelta
import time
import requests
import threading
from threading import Thread
from tkcalendar import Calendar
from tkinter import ttk

is_running = False
stop_event = threading.Event()

def send_to_api(row):
    try:
        api_url = api_url_var.get()
        response = requests.post(api_url, json=row)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False
    
def send_batch_to_api(batch):
    try:
        api_url = api_url_var.get()
        response = requests.post(api_url, json=batch)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False

def download_data(log_box):
    try:
        log_box.insert(tk.END, "\n\u2022 Đang gọi API 127.0.0.1:3000/api/data...")
        log_box.update()
        response = requests.get("http://127.0.0.1:3000/api/data")
        if response.status_code == 200:
            attendance = response.text  # Giả sử API trả về danh sách các bản ghi
            log_box.insert(tk.END, "\n\u2022 Gọi API thành công!")
            log_box.update()
        else:
            log_box.insert(tk.END, "\n\u2022 Lỗi khi gọi API: " + str(response.status_code))
            log_box.update()
            return
        
        records = {}
        for record in attendance:
            if stop_event.is_set():
                break
            # Giả sử mỗi bản ghi là dict với các trường 'timestamp' và 'user_id'
            record_time = datetime.fromisoformat(record['timestamp'])
            if start_date <= record_time <= end_date:
                user_id = record['user_id']
                date_key = record_time.strftime("%Y-%m-%d")
                time_str = record_time.strftime("%Y-%m-%d %H:%M")
                if date_key not in records:
                    records[date_key] = {}
                if user_id not in records[date_key]:
                    records[date_key][user_id] = []
                records[date_key][user_id].append(time_str)
        
        rows = []
        for date, users in records.items():
            for user_id, timestamps in users.items():
                # Lấy tối đa 6 lần chấm công (nếu có)
                timestamps = sorted(timestamps)[:6]
                row = [user_id] + timestamps
                rows.append(row)

        total_rows = len(rows)
        if total_rows > 1000:
            batch_size = 1000
            batch = []
            sent_count = 0
            for index, row in enumerate(rows):
                if stop_event.is_set():
                    break
                if len(row) < 7:
                    row.extend([''] * (7 - len(row)))
                data_obj = {
                    "ID": int(row[0]),
                    "Time1": row[1] if len(row) > 1 else '',
                    "Time2": row[2] if len(row) > 2 else '',
                    "Time3": row[3] if len(row) > 3 else '',
                    "Time4": row[4] if len(row) > 4 else '',
                    "Time5": row[5] if len(row) > 5 else '',
                    "Time6": row[6] if len(row) > 6 else ''
                }
                batch.append(data_obj)
                if len(batch) == batch_size:
                    success = send_batch_to_api(batch)
                    if not success:
                        if log_box.winfo_exists():
                            for item in batch:
                                log_box.insert(tk.END, f"\n\u2022 Gửi dữ liệu của {item['ID']} thất bại.")
                                log_box.update()
                    sent_count += len(batch)
                    percentage = (sent_count / total_rows) * 100
                    log_box.insert(tk.END, f"\n\u2022 Đã gửi {percentage:.2f}% - {sent_count}/{total_rows}")
                    log_box.update()
                    batch = []
                    time.sleep(2)
                    log_box.yview_moveto(1)
            if batch:
                success = send_batch_to_api(batch)
                if not success:
                    if log_box.winfo_exists():
                        for item in batch:
                            log_box.insert(tk.END, f"\n\u2022 Gửi dữ liệu của {item['ID']} thất bại.")
                            log_box.update()
                sent_count += len(batch)
                percentage = (sent_count / total_rows) * 100
                log_box.insert(tk.END, f"\n\u2022 Đã gửi {percentage:.2f}% - {sent_count}/{total_rows}")
                log_box.update()
        else:
            batch = []
            for row in rows:
                if stop_event.is_set():
                    break
                if len(row) < 7:
                    row.extend([''] * (7 - len(row)))
                data_obj = {
                    "ID": int(row[0]),
                    "Time1": row[1] if len(row) > 1 else '',
                    "Time2": row[2] if len(row) > 2 else '',
                    "Time3": row[3] if len(row) > 3 else '',
                    "Time4": row[4] if len(row) > 4 else '',
                    "Time5": row[5] if len(row) > 5 else '',
                    "Time6": row[6] if len(row) > 6 else ''
                }
                batch.append(data_obj)
            success = send_batch_to_api(batch)
            if not success:
                if log_box.winfo_exists():
                    for item in batch:
                        log_box.insert(tk.END, f"\n\u2022 Gửi dữ liệu của {item['ID']} thất bại.")
                        log_box.update()
            log_box.insert(tk.END, f"\n\u2022 Đã gửi 100.00% - {len(batch)}/{len(batch)}")
            log_box.update()
        
        adjusted_end_date = end_date - relativedelta(days=1)
        log_box.insert(tk.END, f"\n\u2022 Quá trình xử lý hoàn tất.\nĐã tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} lên base.")
    except Exception as e:
        log_box.insert(tk.END, f"\n\u2022 Đã xảy ra lỗi: {e}")
    finally:
        pass

def on_date_select(event, start_date_cal, end_date_cal):
    global start_date, end_date
    start_date_str = start_date_cal.get_date()
    end_date_str = end_date_cal.get_date()
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
    end_date = datetime.strptime(end_date_str, '%m/%d/%Y')
    end_date += relativedelta(days=1)

def stop_process():
    global is_running
    stop_event.set()
    is_running = False
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Quá trình đã dừng.")
        log_box.update()
    root.quit()

def update_timer(start_time, time_label):
    if is_running and not stop_event.is_set() and root.winfo_exists():
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        if time_label.winfo_exists():
            time_label.config(text=f"{minutes:02}:{seconds:02}")
        root.after(1000, update_timer, start_time, time_label)

def start_process(log_box, time_label):
    global is_running
    stop_event.clear()
    is_running = True
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\nBắt đầu xử lý... Vui lòng không thao tác gì thêm cho tới khi hoàn tất.")
        adjusted_end_date = end_date - relativedelta(days=1)
        log_box.insert(tk.END, f"\n\u2022 Tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')} về.")
        log_box.update()
    start_time = time.time()
    threading.Thread(target=update_timer, args=(start_time, time_label), daemon=True).start()
    try:
        download_data(log_box)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
    finally:
        is_running = False

def toggle_details():
    if api_url_entry.winfo_ismapped():
        setup_frame.grid_forget()
        api_url_entry.grid_forget()
        ip_entry.grid_forget()
        port_entry.grid_forget()
        api_url_label.grid_forget()
        ip_label.grid_forget()
        port_label.grid_forget()
        detail_button.config(text="Thiết lập")
    else:
        setup_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10)
        api_url_entry.grid(row=4, column=1, padx=5, pady=5)
        ip_entry.grid(row=5, column=1, padx=5, pady=5)
        port_entry.grid(row=6, column=1, padx=5, pady=5)
        api_url_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ip_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        port_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
        detail_button.config(text="Ẩn thiết lập")

root = tk.Tk()

def on_close():
    global is_running
    is_running = False
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Đang thoát chương trình...")
        log_box.update()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.update_idletasks()
root.minsize(600, 400)

log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=10, bd=2, relief="sunken")
log_box.grid(row=0, column=0, columnspan=4, padx=15, pady=10, sticky="nsew")

frame = ttk.Frame(root, padding="10 5 10 5")
frame.grid(row=1, column=0, columnspan=4, padx=15, pady=10, sticky="ew")

start_date_label = ttk.Label(frame, text="Ngày bắt đầu:", font=("Arial", 12))
start_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

start_date_cal = Calendar(frame, selectmode="day", date_pattern="mm/dd/yyyy", font=("Arial", 12), bd=2, relief="sunken")
start_date_cal.grid(row=1, column=0, padx=5, pady=5)

end_date_label = ttk.Label(frame, text="Ngày kết thúc:", font=("Arial", 12))
end_date_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

end_date_cal = Calendar(frame, selectmode="day", date_pattern="mm/dd/yyyy", font=("Arial", 12), bd=2, relief="sunken")
end_date_cal.grid(row=1, column=1, padx=5, pady=5)

start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=27)
end_date = datetime.now() + relativedelta(days=1)

start_date_cal.selection_set(start_date.strftime('%m/%d/%Y'))
end_date_cal.selection_set(end_date.strftime('%m/%d/%Y'))

start_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))
end_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))

time_label = ttk.Label(root, text="00:00", font=("Arial", 14), foreground="blue")
time_label.grid(row=2, column=0, columnspan=4, pady=10)

button_frame = ttk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

start_button = ttk.Button(button_frame, text="Bắt đầu", width=20, command=lambda: start_process(log_box, time_label))
start_button.grid(row=0, column=0, padx=5)

stop_button = ttk.Button(button_frame, text="Thoát", width=20, style="TButton", command=stop_process)
stop_button.grid(row=0, column=1, padx=5)

detail_button = ttk.Button(button_frame, text="Thiết lập", width=20, style="TButton", command=toggle_details)
detail_button.grid(row=0, column=2, padx=5)

ip_var = tk.StringVar()
port_var = tk.IntVar()
api_url_var = tk.StringVar()
ip_var.set("127.0.0.1")
port_var.set(3000)
api_url_var.set("http://127.0.0.1:3000/api/data")

setup_frame = ttk.Frame(root)
setup_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10)
api_url_label = ttk.Label(setup_frame, text="API URL:", font=("Arial", 12))
api_url_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
ip_label = ttk.Label(setup_frame, text="IP:", font=("Arial", 12))
ip_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
port_label = ttk.Label(setup_frame, text="PORT:", font=("Arial", 12))
port_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
api_url_entry = ttk.Entry(setup_frame, textvariable=api_url_var, font=("Arial", 12), width=50)
api_url_entry.grid(row=4, column=1, padx=5, pady=5)
ip_entry = ttk.Entry(setup_frame, textvariable=ip_var, font=("Arial", 12), width=50)
ip_entry.grid(row=5, column=1, padx=5, pady=5)
port_entry = ttk.Entry(setup_frame, textvariable=port_var, font=("Arial", 12), width=50)
port_entry.grid(row=6, column=1, padx=5, pady=5)

info_frame = ttk.Frame(root)
info_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=10)
info_label = ttk.Label(info_frame, text="Kai © Bình Thuận Ford 2025", font=("Arial", 9))
info_label.grid(row=0, column=0, padx=5)

# Ẩn các trường nhập thiết lập theo mặc định
setup_frame.grid_forget()
api_url_label.grid_forget()
ip_label.grid_forget()
port_label.grid_forget()
api_url_entry.grid_forget()
ip_entry.grid_forget()
port_entry.grid_forget()

root.grid_rowconfigure(1000, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=1)
root.grid_columnconfigure(5, weight=1)
root.grid_rowconfigure(6, weight=1)
root.grid_columnconfigure(6, weight=1)
root.grid_rowconfigure(7, weight=1)
root.grid_columnconfigure(7, weight=1)

root.mainloop()

