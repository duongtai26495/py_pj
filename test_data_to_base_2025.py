import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta
import pandas as pd
from zk import ZK
from dateutil.relativedelta import relativedelta
import time
import requests
import threading
from threading import Thread
from tkcalendar import Calendar
from tkinter import ttk

is_running = False
stop_event = threading.Event()



def send_batch_to_api(data, length, url):
    try:
        response = requests.post(url, json={'data': data, 'length': length})
        return response.status_code == 200
    except Exception as e:
        return False

def download_data(log_box):
    zk = ZK(ip_var.get(), port=port_var.get(), timeout=15)
    conn = None
    try:
        # Kết nối tới máy chấm công
        if log_box.winfo_exists():
            log_box.insert(tk.END, "\n• Đang kết nối tới máy chấm công...")
            log_box.update()
        conn = zk.connect()
        if log_box.winfo_exists():
            log_box.insert(tk.END, "\n• Kết nối thành công!")
            log_box.update()

        # Lấy attendance và danh sách user
        attendance = conn.get_attendance()
        users = conn.get_users()

        # Tạo dict lưu attendance theo cặp (user_id, ngày) – chỉ dùng để phân nhóm
        # key: (uid, date_str), value: set(mốc thời gian định dạng "YYYY-MM-DD HH:MM")
        records = {}
        # Lưu user có dữ liệu để xác định nếu không có data thì chỉ tạo 1 row trống
        user_has_data = set()

        if attendance:
            for record in attendance:
                if stop_event.is_set():
                    break
                if start_date <= record.timestamp <= end_date:
                    uid = record.user_id
                    # Dùng date_str để nhóm theo ngày (mặc dù sau này không đưa vào payload)
                    date_str = record.timestamp.strftime("%Y-%m-%d")
                    key = (uid, date_str)
                    time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
                    records.setdefault(key, set()).add(time_str)
                    user_has_data.add(uid)

        # Tạo danh sách rows
        rows = []
        for user in users:
            uid = user.user_id
            # Nếu user có data, tạo 1 row cho mỗi ngày có data
            keys = [key for key in records if key[0] == uid]
            if keys:
                # Sắp xếp theo ngày (mặc dù không dùng hiển thị)
                for key in sorted(keys, key=lambda k: k[1]):
                    times = sorted(list(records[key]))[:6]
                    # Row gồm: [ID, Time1, Time2, ..., Time6]
                    row = [uid] + times
                    if len(times) < 6:
                        row += [''] * (6 - len(times))
                    rows.append(row)
            else:
                # User không có data, chỉ tạo duy nhất 1 row trống
                rows.append([uid] + [''] * 6)

        # Tạo payload: mỗi row có 7 trường
        batch = []
        for row in rows:
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

        total = len(batch)
        # Nếu cần chia payload theo batch (ở đây payload vẫn được bọc trong key "data1")
        if total > 1000:
            payload = {}
            for i in range(0, total, 1000):
                batch_index = i // 1000 + 1
                payload[f"data{batch_index}"] = batch[i:i+1000]
        else:
            payload = {"data1": batch}

        success = send_batch_to_api(payload, total, api_url_var.get())
        if success:
            log_box.insert(tk.END, f"\n• Đã gửi {total} bản ghi thành công.")
        else:
            log_box.insert(tk.END, "\n• Gửi dữ liệu thất bại.")

        adjusted_end_date = end_date - relativedelta(days=1)
        log_box.insert(
            tk.END,
            f"\n• Xử lý hoàn tất. Đã tải dữ liệu từ {start_date.strftime('%d/%m/%Y')} đến {adjusted_end_date.strftime('%d/%m/%Y')}."
        )
        log_box.update()

    except Exception as e:
        log_box.insert(tk.END, f"\n• Đã xảy ra lỗi: {e}")
    finally:
        if conn and conn.is_connect:
            conn.disconnect()



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
ip_var.set("14.179.55.199")
port_var.set(4370)
api_url_var.set("https://open-sg.larksuite.com/anycross/trigger/callback/MGM1NmVkYTJhY2YxYjE0MDQ2M2I2MDAzYTZhOTYxM2Jm") 

setup_frame = ttk.Frame(root)
setup_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10)
# Label for API URL
api_url_label = ttk.Label(setup_frame, text="API URL:", font=("Arial", 12))
api_url_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")

# Label for IP
ip_label = ttk.Label(setup_frame, text="IP:", font=("Arial", 12))
ip_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")

# Label for PORT
port_label = ttk.Label(setup_frame, text="PORT:", font=("Arial", 12))
port_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")

# Entry for API URL
api_url_entry = ttk.Entry(setup_frame, textvariable=api_url_var, font=("Arial", 12), width=50)
api_url_entry.grid(row=4, column=1, padx=5, pady=5)

# Entry for IP
ip_entry = ttk.Entry(setup_frame, textvariable=ip_var, font=("Arial", 12), width=50)
ip_entry.grid(row=5, column=1, padx=5, pady=5)

# Entry for PORT
port_entry = ttk.Entry(setup_frame, textvariable=port_var, font=("Arial", 12), width=50)
port_entry.grid(row=6, column=1, padx=5, pady=5)




info_frame = ttk.Frame(root)
info_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=10)

info_label = ttk.Label(info_frame, text="Kai © Bình Thuận Ford 2025", font=("Arial", 9))
info_label.grid(row=0, column=0, padx=5)

# Ẩn các trường nhập khẩu theo mặc định
setup_frame.grid_forget()
api_url_label.grid_forget()
ip_label.grid_forget()
port_label.grid_forget()
api_url_entry.grid_forget()
ip_entry.grid_forget()
port_entry.grid_forget()

root.grid_rowconfigure(1000, weight=1)  # Cấu hình dòng dưới cùng
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
