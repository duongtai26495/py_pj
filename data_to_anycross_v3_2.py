import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta
from zk import ZK
from dateutil.relativedelta import relativedelta
import time
import requests
import threading
from tkcalendar import Calendar
from tkinter import ttk
import pandas as pd

is_running = False
stop_event = threading.Event()
COPYRIGHT = "Kai © v3.2.5"
DEFAULT_BINH_THUAN_IP = "113.162.244.51"
DEFAULT_SECOND_IP = "14.179.55.199"
SECOND_PORT = 4370
SECOND_PREFIX = "NT"
SECOND_IP_API = "https://endpoint.binhthuanford.com/api/get_ip_nt"

def send_batch_to_api(data, length, url):
    try:
        response = requests.post(url, json={'data': data, 'length': length})
        return response.status_code == 200
    except Exception as e:
        return False

def get_second_ip():
    try:
        response = requests.get(SECOND_IP_API, timeout=30)
        if response.status_code == 200:
            data = response.json()
            second_ip = data.get("ip", DEFAULT_SECOND_IP)
            if log_box.winfo_exists():
                log_box.insert(tk.END, f"\n• Đã lấy thành công IP {second_ip}")
                log_box.update()
            return second_ip
        else:
            if log_box.winfo_exists():
                log_box.insert(tk.END, "\n• Lấy IP mới không thành công. Sử dụng mặc định")
                log_box.update()
            return DEFAULT_SECOND_IP
    except Exception as e:
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\nLỗi khi lấy second ip: {e}. Sử dụng mặc định.")
            log_box.update()
        return DEFAULT_SECOND_IP

def get_data_from_device(ip, port, prefix=""):
    zk = ZK(ip, port, timeout=30, ommit_ping=True)
    conn = None
    attendance = []
    users = []
    try:
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\n• Đang kết nối tới máy chấm công {ip}:{port}...")
            log_box.update()
        conn = zk.connect()
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\n• Kết nối tới {ip}:{port} thành công!")
            log_box.update()
        attendance = conn.get_attendance()
        users = conn.get_users()
        if prefix:
            for record in attendance:
                record.user_id = f"{prefix}{record.user_id}"
            for user in users:
                user.user_id = f"{prefix}{user.user_id}"
        return attendance, users
    except Exception as e:
        log_box.insert(tk.END, f"\n• Lỗi kết nối {ip}:{port} - {e}")
        log_box.update()
        return [], []
    finally:
        if conn and conn.is_connect:
            conn.disconnect()

def get_batch_data():
    data_source = data_source_var.get()
    attendance = []
    combined_users = []
    if data_source == "BinhThuan":
        attendance, users = get_data_from_device(DEFAULT_BINH_THUAN_IP, port_var.get(), prefix="")
        combined_users = users
    elif data_source == "NinhThuan":
        second_ip = ip_ninhthuan_var.get().strip() if ip_ninhthuan_var.get().strip() else get_second_ip()
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\n• Sử dụng IP nhập: {second_ip} cho nguồn Ninh Thuận.")
            log_box.update()
        attendance, users = get_data_from_device(second_ip, SECOND_PORT, prefix=SECOND_PREFIX)
        combined_users = users
    else:
        second_ip = ip_ninhthuan_var.get().strip() if ip_ninhthuan_var.get().strip() else get_second_ip()
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\n• Sử dụng IP nhập: {second_ip} cho nguồn Ninh Thuận.")
            log_box.update()
        attendance1, users1 = get_data_from_device(DEFAULT_BINH_THUAN_IP, port_var.get(), prefix="")
        attendance2, users2 = get_data_from_device(second_ip, SECOND_PORT, prefix=SECOND_PREFIX)
        attendance = attendance1 + attendance2
        combined_users = {user.user_id: user for user in (users1 + users2)}.values()

    records = {}
    if attendance:
        for record in attendance:
            if stop_event.is_set():
                break
            if start_date <= record.timestamp <= end_date:
                uid = record.user_id
                date_str = record.timestamp.strftime("%Y-%m-%d")
                key = (uid, date_str)
                time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                records.setdefault(key, set()).add(time_str)

    rows = []
    current_date = start_date.date()
    end_date_only = (end_date - relativedelta(days=1)).date()
    for user in combined_users:
        uid = user.user_id
        current_day = current_date
        while current_day <= end_date_only:
            key = (uid, current_day.strftime("%Y-%m-%d"))
            times = sorted(list(records.get(key, [])))[:6]
            row = [uid] + times
            if len(times) < 6:
                row += [''] * (6 - len(times))
            rows.append(row)
            current_day += timedelta(days=1)

    batch = []
    for row in rows:
        data_obj = {
            "ID": row[0],
            "Time1": row[1],
            "Time2": row[2],
            "Time3": row[3],
            "Time4": row[4],
            "Time5": row[5],
            "Time6": row[6]
        }
        batch.append(data_obj)
    return batch

def export_excel(log_box):
    batch = get_batch_data()
    df = pd.DataFrame(batch)
    excel_filename = f"Export_{int(round(time.time() * 1000))}.xlsx"
    try:
        df.to_excel(excel_filename, index=False)
        log_box.insert(tk.END, f"\n• Xuất file Excel thành công: {excel_filename}")
    except Exception as e:
        log_box.insert(tk.END, f"\n• Xuất file Excel thất bại: {e}")
    log_box.update()

def push_to_base(log_box):
    batch = get_batch_data()
    total = len(batch)
    if total > 1000:
        payload = {}
        for i in range(0, total, 1000):
            batch_index = i // 1000 + 1
            payload[f"data{batch_index}"] = batch[i:i+1000]
    else:
        payload = {"data1": batch}
    success = send_batch_to_api(payload, total, api_url_var.get())
    if success:
        log_box.insert(tk.END, f"\n• Đã đẩy {total} bản ghi lên base thành công.")
    else:
        log_box.insert(tk.END, "\n• Đẩy dữ liệu lên base thất bại.")
    adjusted_end_date = end_date - relativedelta(days=1)
    log_box.insert(tk.END, f"\n• Xử lý hoàn tất. Dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')}.")
    log_box.update()

def open_file_folder(log_box):
    try:
        # Mở thư mục hiện tại chứa file theo hệ điều hành
        if sys.platform.startswith('win'):
            os.startfile(os.getcwd())
        elif sys.platform.startswith('darwin'):
            subprocess.call(["open", os.getcwd()])
        else:
            subprocess.call(["xdg-open", os.getcwd()])
        log_box.insert(tk.END, "\n• Mở thành công thư mục chứa file.")
    except Exception as e:
        log_box.insert(tk.END, f"\n• Mở thư mục chứa file thất bại: {e}")
    log_box.update()

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
    # Cập nhật UI ban đầu
    log_box.insert(tk.END, "\nBắt đầu xử lý... Vui lòng không thao tác gì thêm cho tới khi hoàn tất.")
    selected_source = data_source_var.get()
    if selected_source == "BinhThuan":
        log_box.insert(tk.END, "\n\u2022 Đang tải dữ liệu từ Bình Thuận.")
    elif selected_source == "NinhThuan":
        log_box.insert(tk.END, "\n\u2022 Đang tải dữ liệu từ Ninh Thuận.")
    else:
        log_box.insert(tk.END, "\n\u2022 Đang tải dữ liệu từ cả hai nguồn: Bình Thuận và Ninh Thuận.")
    adjusted_end_date = end_date - relativedelta(days=1)
    log_box.insert(tk.END, f"\n\u2022 Dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')}.")
    log_box.update()

    start_time = time.time()
    threading.Thread(target=update_timer, args=(start_time, time_label), daemon=True).start()

    def task():
        try:
            opt = process_option_var.get()
            if opt == "excel":
                export_excel(log_box)
            elif opt == "base":
                push_to_base(log_box)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}"))
        finally:
            global is_running
            is_running = False

    threading.Thread(target=task, daemon=True).start()

def toggle_details():
    if api_url_entry.winfo_ismapped():
        setup_frame.grid_forget()
        api_url_entry.grid_forget()
        ip_ninhthuan_entry.grid_forget()
        port_entry.grid_forget()
        api_url_label.grid_forget()
        ip_ninhthuan_label.grid_forget()
        port_label.grid_forget()
        detail_button.config(text="Thiết lập")
    else:
        setup_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=10)
        api_url_entry.grid(row=4, column=1, padx=5, pady=5)
        ip_ninhthuan_entry.grid(row=5, column=1, padx=5, pady=5)
        port_entry.grid(row=6, column=1, padx=5, pady=5)
        api_url_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ip_ninhthuan_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
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
root.minsize(600, 500)

# Khung hiển thị log
log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=10, bd=2, relief="sunken")
log_box.grid(row=0, column=0, columnspan=5, padx=15, pady=10, sticky="nsew")

# Khung chọn ngày và nguồn dữ liệu
frame = ttk.Frame(root, padding="10 5 10 5")
frame.grid(row=1, column=0, columnspan=5, padx=15, pady=10, sticky="ew")

start_date_label = ttk.Label(frame, text="Ngày bắt đầu:", font=("Arial", 12))
start_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
start_date_cal = Calendar(frame, selectmode="day", date_pattern="mm/dd/yyyy", font=("Arial", 12), bd=2, relief="sunken")
start_date_cal.grid(row=1, column=0, padx=5, pady=5)

end_date_label = ttk.Label(frame, text="Ngày kết thúc:", font=("Arial", 12))
end_date_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
end_date_cal = Calendar(frame, selectmode="day", date_pattern="mm/dd/yyyy", font=("Arial", 12), bd=2, relief="sunken")
end_date_cal.grid(row=1, column=1, padx=5, pady=5)

source_frame = ttk.Frame(frame, padding="5")
source_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="w")
source_label = ttk.Label(source_frame, text="Chọn nguồn dữ liệu:", font=("Arial", 12))
source_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
data_source_var = tk.StringVar(value="Both")
rb1 = ttk.Radiobutton(source_frame, text="Bình Thuận", variable=data_source_var, value="BinhThuan")
rb1.grid(row=0, column=1, padx=5, pady=5)
rb2 = ttk.Radiobutton(source_frame, text="Ninh Thuận", variable=data_source_var, value="NinhThuan")
rb2.grid(row=0, column=2, padx=5, pady=5)
rb3 = ttk.Radiobutton(source_frame, text="Tất cả", variable=data_source_var, value="Both")
rb3.grid(row=0, column=3, padx=5, pady=5)

# Radio button lựa chọn xử lý: Xuất Excel hay Đẩy lên Base
process_option_var = tk.StringVar(value="excel")
option_frame = ttk.Frame(frame, padding="5")
option_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="w")
option_label = ttk.Label(option_frame, text="Chọn xử lý:", font=("Arial", 12))
option_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
rb_excel = ttk.Radiobutton(option_frame, text="Xuất Excel", variable=process_option_var, value="excel")
rb_excel.grid(row=0, column=1, padx=5, pady=5)
rb_base = ttk.Radiobutton(option_frame, text="Đẩy lên Base", variable=process_option_var, value="base")
rb_base.grid(row=0, column=2, padx=5, pady=5)

start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=27)
end_date = datetime.now() + relativedelta(days=1)
start_date_cal.selection_set(start_date.strftime('%m/%d/%Y'))
end_date_cal.selection_set(end_date.strftime('%m/%d/%Y'))
start_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))
end_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))

time_label = ttk.Label(root, text="00:00", font=("Arial", 14), foreground="blue")
time_label.grid(row=2, column=0, columnspan=5, pady=10)

# Khung nhóm nút: nhóm 1 chứa "Bắt đầu" và "Mở thư mục"
button_frame1 = ttk.Frame(root)
button_frame1.grid(row=3, column=0, columnspan=5, padx=10, pady=10)
start_button = ttk.Button(button_frame1, text="Bắt đầu", width=20, command=lambda: start_process(log_box, time_label))
start_button.grid(row=0, column=0, padx=5)
open_folder_button = ttk.Button(button_frame1, text="Mở thư mục", width=20, command=lambda: open_file_folder(log_box))
open_folder_button.grid(row=0, column=1, padx=5)

# Khung nhóm nút: nhóm 2 chứa "Kết thúc" và "Thiết lập"
button_frame2 = ttk.Frame(root)
button_frame2.grid(row=4, column=0, columnspan=5, padx=10, pady=10)
stop_button = ttk.Button(button_frame2, text="Kết thúc", width=20, command=stop_process)
stop_button.grid(row=0, column=0, padx=5)
detail_button = ttk.Button(button_frame2, text="Thiết lập", width=20, command=toggle_details)
detail_button.grid(row=0, column=1, padx=5)

ip_ninhthuan_var = tk.StringVar()
ip_ninhthuan_var.set(get_second_ip())
port_var = tk.IntVar()
api_url_var = tk.StringVar()
port_var.set(24370)
api_url_var.set("https://open-sg.larksuite.com/anycross/trigger/callback/MDFiOGNkYjU3M2YxMWNkM2RlODlmOWY3OGZmYjE3N2Yw")

setup_frame = ttk.Frame(root)
setup_frame.grid(row=7, column=0, columnspan=5, padx=10, pady=10)
api_url_label = ttk.Label(setup_frame, text="API URL:", font=("Arial", 12))
api_url_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
ip_ninhthuan_label = ttk.Label(setup_frame, text="IP Ninh Thuận:", font=("Arial", 12))
ip_ninhthuan_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
port_label = ttk.Label(setup_frame, text="PORT:", font=("Arial", 12))
port_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
api_url_entry = ttk.Entry(setup_frame, textvariable=api_url_var, font=("Arial", 12), width=50)
api_url_entry.grid(row=4, column=1, padx=5, pady=5)
ip_ninhthuan_entry = ttk.Entry(setup_frame, textvariable=ip_ninhthuan_var, font=("Arial", 12), width=50)
ip_ninhthuan_entry.grid(row=5, column=1, padx=5, pady=5)
port_entry = ttk.Entry(setup_frame, textvariable=port_var, font=("Arial", 12), width=50)
port_entry.grid(row=6, column=1, padx=5, pady=5)

info_frame = ttk.Frame(root)
info_frame.grid(row=8, column=0, columnspan=5, padx=10, pady=10)
info_label = ttk.Label(info_frame, text=COPYRIGHT, font=("Arial", 9))
info_label.grid(row=0, column=0, padx=5)

setup_frame.grid_forget()
api_url_label.grid_forget()
ip_ninhthuan_label.grid_forget()
port_label.grid_forget()
api_url_entry.grid_forget()
ip_ninhthuan_entry.grid_forget()
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
root.grid_rowconfigure(8, weight=1)
root.grid_columnconfigure(8, weight=1)

root.mainloop()
