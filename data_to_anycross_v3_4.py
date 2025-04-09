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
from tkcalendar import Calendar, DateEntry
from tkinter import ttk
import pandas as pd

# Các biến cài đặt mặc định ban đầu
COPYRIGHT = "MarCom - BThFord - 2025 © v3.4"

# Mặc định của nguồn Bình Thuận và Ninh Thuận
DEFAULT_BINH_THUAN_IP = "113.162.244.51"   # sẽ thay đổi qua input
DEFAULT_NINH_THUAN_IP = "14.227.240.34"      # sẽ thay đổi qua input
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
api_url_var.set("https://open-sg.larksuite.com/anycross/trigger/callback/MDA3YjJlZTE0MGEzMDllZmY3YzVjNjI3M2RmZTgwYmVj")
# IP, PORT Bình Thuận
ip_binhthuan_var = tk.StringVar()
ip_binhthuan_var.set(DEFAULT_BINH_THUAN_IP)
port_binhthuan_var = tk.IntVar()
port_binhthuan_var.set(DEFAULT_BINH_THUAN_PORT)
# IP, PORT Ninh Thuận
ip_ninhthuan_var = tk.StringVar()
ip_ninhthuan_var.set(DEFAULT_NINH_THUAN_IP)  # nếu để trống thì sẽ gọi get_second_ip()
port_ninhthuan_var = tk.IntVar()
port_ninhthuan_var.set(DEFAULT_NINH_THUAN_PORT)
# Base Token và Table ID
base_token_var = tk.StringVar()
base_token_var.set("CeSDbFSWvaRjAgsmCWclZ0UEgpc")
table_id_var = tk.StringVar()
table_id_var.set("tbliO12qpcXtPPc1")
remove_var = tk.IntVar()
remove_var.set(1)

# Log hiển thị
root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.minsize(800, 600)

# Các hàm không thay đổi
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
    try:
        # Kiểm tra nếu thư viện openpyxl đã được cài đặt
        import importlib.util
        openpyxl_spec = importlib.util.find_spec("openpyxl")
        if openpyxl_spec is None:
            log_box.insert(tk.END, "\n• Lỗi: Chưa cài đặt thư viện openpyxl")
            log_box.insert(tk.END, "\n• Vui lòng cài đặt bằng lệnh: pip install openpyxl")
            log_box.update()
            return
            
        batch = get_batch_data()
        df = pd.DataFrame(batch)
        excel_filename = f"Export_{int(round(time.time() * 1000))}.xlsx"
        df.to_excel(excel_filename, index=False)
        log_box.insert(tk.END, f"\n• Xuất file Excel thành công: {excel_filename}")
    except ImportError:
        log_box.insert(tk.END, "\n• Lỗi: Chưa cài đặt thư viện openpyxl")
        log_box.insert(tk.END, "\n• Vui lòng cài đặt bằng lệnh: pip install openpyxl")
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

def on_date_select(*args):
    global start_date, end_date
    start_date = start_date_entry.get_date()
    end_date = end_date_entry.get_date() + relativedelta(days=1)  # +1 ngày để bao gồm ngày cuối
    
    # Cập nhật nhãn hiển thị (thêm justify='center')
    date_range_label.config(
        text=f"{start_date.strftime('%d/%m/%Y')} → {end_date_entry.get_date().strftime('%d/%m/%Y')}",
        justify="center", 
        anchor="center")

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
        setup_frame.pack_forget()
        detail_button.config(text="Thiết lập")
    else:
        setup_frame.pack(fill="both", expand=True, padx=5, pady=5)
        detail_button.config(text="Ẩn đi")  

def on_close():
    global is_running
    is_running = False
    if log_box.winfo_exists():
        log_box.insert(tk.END, "\n\u2022 Đang thoát chương trình...")
        log_box.update()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
 

# Phân chia lưới với tỷ lệ mới
root.grid_rowconfigure(0, weight=2)  # Hàng chính cho nội dung
root.grid_rowconfigure(1, weight=0)  # Hàng mới cho footer
root.grid_columnconfigure(0, weight=1)    # Log box - giữ giá trị weight
root.grid_columnconfigure(1, weight=18)   # Điều khiển bên phải - tăng lên (từ 12 lên 18)

# UI: Khung hiển thị log (và thời gian ở dưới)
log_frame = ttk.Frame(root, padding="5")
log_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

log_label = ttk.Label(log_frame, text="Nhật ký hoạt động:", font=("Arial", 9, "bold"))
log_label.pack(anchor="w", padx=3, pady=3)

log_box = ScrolledText(log_frame, wrap=tk.WORD, font=("Arial", 9), fg="green", bg="#f0fff0", height=20, bd=2, relief="ridge")
log_box.pack(fill="both", expand=True, padx=3, pady=3)

# Thời gian ở dưới log box
time_frame = ttk.Frame(log_frame, padding="2")
time_frame.pack(fill="x", padx=3, pady=5, anchor="s")
time_label = ttk.Label(time_frame, text="00:00", font=("Arial", 12), foreground="blue")
time_label.pack(side="left", padx=5)

# Tạo frame chính bên phải (thêm thuộc tính cho căn giữa)
right_frame = ttk.Frame(root, padding="5")
right_frame.grid(row=0, column=1, rowspan=1, padx=5, pady=5, sticky="nsew")

# Khung chọn ngày
date_frame = ttk.LabelFrame(right_frame, text="Chọn khoảng thời gian", padding="5")
date_frame.pack(fill="x", padx=5, pady=5, anchor="center")  # Thêm anchor="center" để căn giữa

# Thêm các nút chọn nhanh dựa trên yêu cầu thường xuyên lấy dữ liệu
quick_frame = ttk.Frame(date_frame)
quick_frame.pack(fill="x", padx=3, pady=3)

def set_date_range(option):
    today = datetime.now()
    
    if option == "current_month":
        # 28 tháng trước đến hiện tại (tháng hiện tại)
        start = (today.replace(day=1) - relativedelta(months=1)).replace(day=28)
        end = today
    elif option == "last_month":
        # 28 cách đây 2 tháng đến 27 của tháng trước
        start = (today.replace(day=1) - relativedelta(months=2)).replace(day=28)
        end = (today.replace(day=1) - relativedelta(months=1)).replace(day=27)
    elif option == "yesterday":
        # Hôm qua (0-23:59 hôm qua)
        start = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    elif option == "today":
        # Hôm nay (0 giờ sáng hôm nay đến hiện tại)
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = today
    else:
        return
    
    start_date_entry.set_date(start)
    end_date_entry.set_date(end)
    
    # Cập nhật biến toàn cục
    global start_date, end_date
    start_date = start
    end_date = end + relativedelta(days=1)  # Để bao gồm ngày cuối
    
    # Hiển thị khoảng ngày đã chọn (thêm justify='center')
    date_range_label.config(text=f"{start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}", justify="center", anchor="center")

# Thiết lập style cho các nút
style = ttk.Style()
style.configure("Date.TButton", font=("Arial", 8), padding=1)

# Tạo các nút chọn nhanh với căn giữa
date_buttons_frame = ttk.Frame(quick_frame)
date_buttons_frame.pack(fill="x", anchor="center")  # Căn giữa các nút

btn1 = ttk.Button(date_buttons_frame, text="Tháng hiện tại", style="Date.TButton", width=15, 
                 command=lambda: set_date_range("current_month"))
btn1.grid(row=0, column=0, padx=2, pady=2)

btn2 = ttk.Button(date_buttons_frame, text="Tháng trước", style="Date.TButton", width=15,
                 command=lambda: set_date_range("last_month"))
btn2.grid(row=0, column=1, padx=2, pady=2)

btn3 = ttk.Button(date_buttons_frame, text="Hôm qua", style="Date.TButton", width=15,
                 command=lambda: set_date_range("yesterday"))
btn3.grid(row=1, column=0, padx=2, pady=2)

btn4 = ttk.Button(date_buttons_frame, text="Hôm nay", style="Date.TButton", width=15,
                 command=lambda: set_date_range("today"))
btn4.grid(row=1, column=1, padx=2, pady=2)

# Cấu hình grid cho date_buttons_frame để căn giữa
date_buttons_frame.grid_columnconfigure(0, weight=1)
date_buttons_frame.grid_columnconfigure(1, weight=1)

# Tùy chỉnh thủ công với căn giữa
manual_frame = ttk.Frame(date_frame)
manual_frame.pack(fill="x", padx=3, pady=5, anchor="center")  # Thêm anchor="center"

# Tạo container để căn giữa phần nhập ngày
input_container = ttk.Frame(manual_frame)
input_container.pack(anchor="center")  # Đặt container vào giữa manual_frame

start_date_label = ttk.Label(input_container, text="Từ:", font=("Arial", 9))
start_date_label.pack(side="left", padx=2)
start_date_entry = DateEntry(input_container, width=12, background='darkblue', 
                           foreground='white', borderwidth=1, date_pattern="dd/mm/yyyy", 
                           font=("Arial", 9))
start_date_entry.pack(side="left", padx=2)

end_date_label = ttk.Label(input_container, text="Đến:", font=("Arial", 9))
end_date_label.pack(side="left", padx=5)
end_date_entry = DateEntry(input_container, width=12, background='darkblue', 
                         foreground='white', borderwidth=1, date_pattern="dd/mm/yyyy", 
                         font=("Arial", 9))
end_date_entry.pack(side="left", padx=2)

# Hiển thị khoảng thời gian đã chọn (căn giữa văn bản)
date_range_label = ttk.Label(date_frame, text="", font=("Arial", 8, "italic"), foreground="blue", anchor="center", justify="center")
date_range_label.pack(fill="x", padx=3, pady=3)

# Khung chọn nguồn và xử lý
options_frame = ttk.Frame(right_frame)
options_frame.pack(fill="x", padx=5, pady=2, anchor="center")

# Khung nguồn dữ liệu (căn giữa nội dung)
source_frame = ttk.LabelFrame(options_frame, text="Nguồn dữ liệu", padding="3")
source_frame.pack(fill="x", padx=3, pady=3)

# Container để chứa các radio button và căn giữa
source_container = ttk.Frame(source_frame)
source_container.pack(anchor="center")  # Căn giữa container

data_source_var = tk.StringVar(value="Both")
rb1 = ttk.Radiobutton(source_container, text="Bình Thuận", variable=data_source_var, value="BinhThuan", padding=0)
rb1.pack(side="left", padx=2, pady=2)
rb2 = ttk.Radiobutton(source_container, text="Ninh Thuận", variable=data_source_var, value="NinhThuan", padding=0)
rb2.pack(side="left", padx=2, pady=2)
rb3 = ttk.Radiobutton(source_container, text="Tất cả", variable=data_source_var, value="Both", padding=0)
rb3.pack(side="left", padx=2, pady=2)

# Khung lựa chọn xử lý (căn giữa nội dung)
option_frame = ttk.LabelFrame(options_frame, text="Chọn xử lý", padding="3")
option_frame.pack(fill="x", padx=3, pady=3)

# Container để chứa các radio button và căn giữa
process_container = ttk.Frame(option_frame)
process_container.pack(anchor="center")  # Căn giữa container

process_option_var = tk.StringVar(value="excel")
rb_excel = ttk.Radiobutton(process_container, text="Xuất Excel", variable=process_option_var, value="excel", padding=0)
rb_excel.pack(side="left", padx=2, pady=2)
rb_base = ttk.Radiobutton(process_container, text="Đẩy lên Base", variable=process_option_var, value="base", padding=0)
rb_base.pack(side="left", padx=2, pady=2)

# Các nút hành động (căn giữa)
button_frame = ttk.Frame(right_frame)
button_frame.pack(fill="x", padx=5, pady=5)

# Container để chứa các nút và căn giữa
button_container = ttk.Frame(button_frame)
button_container.pack(anchor="center")  # Căn giữa container

style.configure("Action.TButton", font=("Arial", 9), padding=2)

start_button = ttk.Button(button_container, text="Bắt đầu", width=8, style="Action.TButton", command=start_process)
start_button.pack(side="left", padx=2, pady=2)
open_folder_button = ttk.Button(button_container, text="Mở thư mục", width=10, style="Action.TButton", command=lambda: os.startfile(os.getcwd()))
open_folder_button.pack(side="left", padx=2, pady=2)
stop_button = ttk.Button(button_container, text="Kết thúc", width=8, style="Action.TButton", command=stop_process)
stop_button.pack(side="left", padx=2, pady=2)
detail_button = ttk.Button(button_container, text="Thiết lập", width=10, style="Action.TButton", command=toggle_details)
detail_button.pack(side="left", padx=2, pady=2)

# UI: Khung thiết lập nâng cao (không cần căn giữa)
setup_frame = ttk.LabelFrame(right_frame, text="Thiết lập nâng cao", padding="5")

# Các thành phần thiết lập (giữ nguyên)
setup_font = ("Arial", 9)

# API gửi data
api_url_label = ttk.Label(setup_frame, text="API gửi data:", font=setup_font)
api_url_label.grid(row=0, column=0, padx=3, pady=3, sticky="w")
api_url_entry = ttk.Entry(setup_frame, textvariable=api_url_var, font=setup_font, width=32)
api_url_entry.grid(row=0, column=1, padx=3, pady=3, sticky="ew")

# IP và PORT Bình Thuận
ip_binhthuan_label = ttk.Label(setup_frame, text="IP Bình Thuận:", font=setup_font)
ip_binhthuan_label.grid(row=1, column=0, padx=3, pady=3, sticky="w")
ip_binhthuan_entry = ttk.Entry(setup_frame, textvariable=ip_binhthuan_var, font=setup_font, width=32)
ip_binhthuan_entry.grid(row=1, column=1, padx=3, pady=3, sticky="ew")

port_binhthuan_label = ttk.Label(setup_frame, text="PORT Bình Thuận:", font=setup_font)
port_binhthuan_label.grid(row=2, column=0, padx=3, pady=3, sticky="w")
port_binhthuan_entry = ttk.Entry(setup_frame, textvariable=port_binhthuan_var, font=setup_font, width=32)
port_binhthuan_entry.grid(row=2, column=1, padx=3, pady=3, sticky="ew")

# IP và PORT Ninh Thuận
ip_ninhthuan_label = ttk.Label(setup_frame, text="IP Ninh Thuận:", font=setup_font)
ip_ninhthuan_label.grid(row=3, column=0, padx=3, pady=3, sticky="w")
ip_ninhthuan_entry = ttk.Entry(setup_frame, textvariable=ip_ninhthuan_var, font=setup_font, width=32)
ip_ninhthuan_entry.grid(row=3, column=1, padx=3, pady=3, sticky="ew")

port_ninhthuan_label = ttk.Label(setup_frame, text="PORT Ninh Thuận:", font=setup_font)
port_ninhthuan_label.grid(row=4, column=0, padx=3, pady=3, sticky="w")
port_ninhthuan_entry = ttk.Entry(setup_frame, textvariable=port_ninhthuan_var, font=setup_font, width=32)
port_ninhthuan_entry.grid(row=4, column=1, padx=3, pady=3, sticky="ew")

# Base Token và Table ID
base_token_label = ttk.Label(setup_frame, text="Base Token:", font=setup_font)
base_token_label.grid(row=5, column=0, padx=3, pady=3, sticky="w")
base_token_entry = ttk.Entry(setup_frame, textvariable=base_token_var, font=setup_font, width=32)
base_token_entry.grid(row=5, column=1, padx=3, pady=3, sticky="ew")

table_id_label = ttk.Label(setup_frame, text="Table ID:", font=setup_font)
table_id_label.grid(row=6, column=0, padx=3, pady=3, sticky="w")
table_id_entry = ttk.Entry(setup_frame, textvariable=table_id_var, font=setup_font, width=32)
table_id_entry.grid(row=6, column=1, padx=3, pady=3, sticky="ew")

# Checkbox Xoá dữ liệu
remove_checkbox = ttk.Checkbutton(setup_frame, text="Xoá dữ liệu", variable=remove_var)
remove_checkbox.grid(row=7, column=0, padx=3, pady=3, sticky="w")

# Thiết lập mặc định cho ngày (tháng hiện tại - 28 tháng trước đến hiện tại)
today = datetime.now()
start_date = (today.replace(day=1) - relativedelta(months=1)).replace(day=28)
end_date = today + relativedelta(days=1)  # Thêm 1 ngày để bao gồm ngày hiện tại
start_date_entry.set_date(start_date)
end_date_entry.set_date(today)

# Hiển thị khoảng thời gian ban đầu
date_range_label.config(
    text=f"{start_date.strftime('%d/%m/%Y')} → {today.strftime('%d/%m/%Y')}")

# Footer hiển thị phiên bản
footer_frame = ttk.Frame(root)
footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

# Thêm dòng kẻ ngăn cách phía trên
separator = ttk.Separator(footer_frame, orient="horizontal")
separator.pack(fill="x", pady=5)

# Hiển thị phiên bản ở giữa
version_label = ttk.Label(footer_frame, text=COPYRIGHT, font=("Arial", 8), foreground="gray")
version_label.pack(anchor="center")

root.mainloop()
