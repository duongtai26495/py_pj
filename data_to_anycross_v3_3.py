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

# Các biến cài đặt mặc định ban đầu
COPYRIGHT = "Kai © v3.3"

# Mặc định của nguồn Bình Thuận và Ninh Thuận
DEFAULT_BINH_THUAN_IP = "113.162.244.51"   # sẽ thay đổi qua input
DEFAULT_NINH_THUAN_IP = "14.179.55.199"      # sẽ thay đổi qua input
# Các PORT mặc định, sẽ thay đổi qua input
DEFAULT_BINH_THUAN_PORT = 24370  
DEFAULT_NINH_THUAN_PORT = 4370

# Endpoint lấy IP cho Ninh Thuận (nếu không nhập IP)
SECOND_IP_API = "https://endpoint.binhthuanford.com/api/get_ip_nt"

# Các biến toàn cục cho ngày
start_date = None
end_date = None

# Các biến chạy và stop
is_running = False
stop_event = threading.Event()

# --- Các biến UI cho input mới ---

root = tk.Tk()
# API gửi data
api_url_var = tk.StringVar()
api_url_var.set("https://open-sg.larksuite.com/anycross/trigger/callback/MDFiOGNkYjU3M2YxMWNkM2RlODlmOWY3OGZmYjE3N2Yw")
# IP, PORT Bình Thuận
ip_binhthuan_var = tk.StringVar()
ip_binhthuan_var.set(DEFAULT_BINH_THUAN_IP)
port_binhthuan_var = tk.IntVar()
port_binhthuan_var.set(DEFAULT_BINH_THUAN_PORT)
# IP, PORT Ninh Thuận
ip_ninhthuan_var = tk.StringVar()
ip_ninhthuan_var.set("")  # nếu để trống thì sẽ gọi get_second_ip()
port_ninhthuan_var = tk.IntVar()
port_ninhthuan_var.set(DEFAULT_NINH_THUAN_PORT)
# Base Token và Table ID
base_token_var = tk.StringVar()
base_token_var.set("CeSDbFSWvaRjAgsmCWclZ0UEgpc")
table_id_var = tk.StringVar()
table_id_var.set("tbliO12qpcXtPPc1")
# Checkbox Xoá dữ liệu: nếu check thì remove = 1, không check = 0.
remove_var = tk.IntVar()
remove_var.set(1)

# Log hiển thị
root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.minsize(600, 500)

log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=10, bd=2, relief="sunken")
log_box.grid(row=0, column=0, columnspan=5, padx=15, pady=10, sticky="nsew")

# Hàm gửi batch data đến API theo định dạng đã cho.
def send_batch_to_api(all_data, table_id, remove):
    payload = {
        "data": {},
        "length": len(all_data),
        "base_token": base_token_var.get(),
        "table_id": table_id,
        "remove": remove,
        "common":0
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
        response = requests.post(api_url_var.get(), json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi khi gửi batch: {e}")
        return False

def get_second_ip():
    try:
        response = requests.get(SECOND_IP_API, timeout=30)
        if response.status_code == 200:
            data = response.json()
            second_ip = data.get("ip", DEFAULT_NINH_THUAN_IP)
            if log_box.winfo_exists():
                log_box.insert(tk.END, f"\n• Đã lấy thành công IP: {second_ip}")
                log_box.update()
            return second_ip
        else:
            if log_box.winfo_exists():
                log_box.insert(tk.END, "\n• Lấy IP mới không thành công. Sử dụng mặc định")
                log_box.update()
            return DEFAULT_NINH_THUAN_IP
    except Exception as e:
        if log_box.winfo_exists():
            log_box.insert(tk.END, f"\nLỗi khi lấy IP: {e}. Sử dụng mặc định.")
            log_box.update()
        return DEFAULT_NINH_THUAN_IP

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
        ip_bt = ip_binhthuan_var.get().strip() or DEFAULT_BINH_THUAN_IP
        port_bt = port_binhthuan_var.get()
        attendance, users = get_data_from_device(ip_bt, port_bt, prefix="")
        combined_users = users
    elif data_source == "NinhThuan":
        ip_nt = ip_ninhthuan_var.get().strip() or get_second_ip()
        port_nt = port_ninhthuan_var.get()
        attendance, users = get_data_from_device(ip_nt, port_nt, prefix="NT")
        combined_users = users
    else:  # Both
        ip_bt = ip_binhthuan_var.get().strip() or DEFAULT_BINH_THUAN_IP
        port_bt = port_binhthuan_var.get()
        ip_nt = ip_ninhthuan_var.get().strip() or get_second_ip()
        port_nt = port_ninhthuan_var.get()
        attendance1, users1 = get_data_from_device(ip_bt, port_bt, prefix="")
        attendance2, users2 = get_data_from_device(ip_nt, port_nt, prefix="NT")
        attendance = attendance1 + attendance2
        # Gom hợp users theo user_id
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

def export_excel():
    batch = get_batch_data()
    df = pd.DataFrame(batch)
    excel_filename = f"Export_{int(round(time.time() * 1000))}.xlsx"
    try:
        df.to_excel(excel_filename, index=False)
        log_box.insert(tk.END, f"\n• Xuất file Excel thành công: {excel_filename}")
    except Exception as e:
        log_box.insert(tk.END, f"\n• Xuất file Excel thất bại: {e}")
    log_box.update()

def push_to_base():
    batch = get_batch_data()
    total = len(batch)
    # Nếu data trên 1000 dòng thì chia nhóm thành data1, data2, ...
    if total > 1000:
        payload = {}
        for i in range(0, total, 1000):
            batch_index = i // 1000 + 1
            payload[f"data{batch_index}"] = batch[i:i+1000]
    else:
        payload = {"data1": batch}
    success = send_batch_to_api(batch, table_id_var.get(), remove_var.get())
    if success:
        log_box.insert(tk.END, f"\n• Đã đẩy {total} bản ghi lên base thành công.")
    else:
        log_box.insert(tk.END, "\n• Đẩy dữ liệu lên base thất bại.")
    adjusted_end_date = end_date - relativedelta(days=1)
    log_box.insert(tk.END, f"\n• Xử lý hoàn tất. Dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')}.")
    log_box.update()

def open_file_folder():
    try:
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

def start_process():
    global is_running
    stop_event.clear()
    is_running = True
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
                export_excel()
            elif opt == "base":
                push_to_base()
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}"))
        finally:
            global is_running
            is_running = False

    threading.Thread(target=task, daemon=True).start()

def toggle_details():
    if setup_frame.winfo_ismapped():
        setup_frame.grid_forget()
        detail_button.config(text="Thiết lập")
    else:
        setup_frame.grid(row=9, column=0, columnspan=5, padx=10, pady=10)
        detail_button.config(text="Ẩn thiết lập")

def on_close():
    global is_running
    is_running = False
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Đang thoát chương trình...")
        log_box.update()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# UI: Khung hiển thị log
log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=10, bd=2, relief="sunken")
log_box.grid(row=0, column=0, columnspan=5, padx=15, pady=10, sticky="nsew")

# UI: Khung chọn ngày và nguồn dữ liệu
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

# Thiết lập mặc định cho ngày
start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=27)
end_date = datetime.now() + relativedelta(days=1)
start_date_cal.selection_set(start_date.strftime('%m/%d/%Y'))
end_date_cal.selection_set(end_date.strftime('%m/%d/%Y'))
start_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))
end_date_cal.bind("<<CalendarSelected>>", lambda event: on_date_select(event, start_date_cal, end_date_cal))

time_label = ttk.Label(root, text="00:00", font=("Arial", 14), foreground="blue")
time_label.grid(row=2, column=0, columnspan=5, pady=10)

# UI: Nhóm nút
button_frame1 = ttk.Frame(root)
button_frame1.grid(row=3, column=0, columnspan=5, padx=10, pady=10)
start_button = ttk.Button(button_frame1, text="Bắt đầu", width=20, command=start_process)
start_button.grid(row=0, column=0, padx=5)
open_folder_button = ttk.Button(button_frame1, text="Mở thư mục", width=20, command=lambda: os.startfile(os.getcwd()))
open_folder_button.grid(row=0, column=1, padx=5)

button_frame2 = ttk.Frame(root)
button_frame2.grid(row=4, column=0, columnspan=5, padx=10, pady=10)
stop_button = ttk.Button(button_frame2, text="Kết thúc", width=20, command=stop_process)
stop_button.grid(row=0, column=0, padx=5)
detail_button = ttk.Button(button_frame2, text="Thiết lập", width=20, command=toggle_details)
detail_button.grid(row=0, column=1, padx=5)

# UI: Khung thiết lập nâng cao (input mới)
setup_frame = ttk.Frame(root, padding="10")
# API gửi data
api_url_label = ttk.Label(setup_frame, text="API gửi data:", font=("Arial", 12))
api_url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
api_url_entry = ttk.Entry(setup_frame, textvariable=api_url_var, font=("Arial", 12), width=50)
api_url_entry.grid(row=0, column=1, padx=5, pady=5)
# IP Bình Thuận
ip_binhthuan_label = ttk.Label(setup_frame, text="IP Bình Thuận:", font=("Arial", 12))
ip_binhthuan_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
ip_binhthuan_entry = ttk.Entry(setup_frame, textvariable=ip_binhthuan_var, font=("Arial", 12), width=50)
ip_binhthuan_entry.grid(row=1, column=1, padx=5, pady=5)
# PORT Bình Thuận
port_binhthuan_label = ttk.Label(setup_frame, text="PORT Bình Thuận:", font=("Arial", 12))
port_binhthuan_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
port_binhthuan_entry = ttk.Entry(setup_frame, textvariable=port_binhthuan_var, font=("Arial", 12), width=50)
port_binhthuan_entry.grid(row=2, column=1, padx=5, pady=5)
# IP Ninh Thuận
ip_ninhthuan_label = ttk.Label(setup_frame, text="IP Ninh Thuận:", font=("Arial", 12))
ip_ninhthuan_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
ip_ninhthuan_entry = ttk.Entry(setup_frame, textvariable=ip_ninhthuan_var, font=("Arial", 12), width=50)
ip_ninhthuan_entry.grid(row=3, column=1, padx=5, pady=5)
# PORT Ninh Thuận
port_ninhthuan_label = ttk.Label(setup_frame, text="PORT Ninh Thuận:", font=("Arial", 12))
port_ninhthuan_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
port_ninhthuan_entry = ttk.Entry(setup_frame, textvariable=port_ninhthuan_var, font=("Arial", 12), width=50)
port_ninhthuan_entry.grid(row=4, column=1, padx=5, pady=5)
# Base Token
base_token_label = ttk.Label(setup_frame, text="Base Token:", font=("Arial", 12))
base_token_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
base_token_entry = ttk.Entry(setup_frame, textvariable=base_token_var, font=("Arial", 12), width=50)
base_token_entry.grid(row=5, column=1, padx=5, pady=5)
# Table ID
table_id_label = ttk.Label(setup_frame, text="Table ID:", font=("Arial", 12))
table_id_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
table_id_entry = ttk.Entry(setup_frame, textvariable=table_id_var, font=("Arial", 12), width=50)
table_id_entry.grid(row=6, column=1, padx=5, pady=5)
# Checkbox Xoá dữ liệu
remove_checkbox = ttk.Checkbutton(setup_frame, text="Xoá dữ liệu (remove=1)", variable=remove_var)
remove_checkbox.grid(row=7, column=0, padx=5, pady=5, sticky="w")

# Ẩn ban đầu
setup_frame.grid_forget()

# Bind các thuộc tính ngày
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.mainloop()
