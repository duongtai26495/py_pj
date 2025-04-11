import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import requests
from datetime import datetime, timedelta
from calendar import monthrange
import json
from tkcalendar import DateEntry
import threading

# Khởi tạo cửa sổ chính
root = tk.Tk()
root.title("Báo cáo Quảng cáo v1.0")
root.minsize(600, 400)

# Biến để lưu trữ ngày bắt đầu và kết thúc
start_date = None
end_date = None

# Thêm biến để theo dõi trạng thái
is_fetching = False

# Thay đổi cấu hình lưới cho layout 2 cột
root.grid_columnconfigure(0, weight=1)  # Cột trái (Log box)
root.grid_columnconfigure(1, weight=1)  # Cột phải (Các điều khiển)
root.grid_rowconfigure(0, weight=1)     # Hàng chính
root.grid_rowconfigure(1, weight=0)     # Hàng footer

# Frame chứa log box (đặt vào cột trái)
log_frame = ttk.LabelFrame(root, text="Nhật ký hoạt động", padding="10")
log_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Log box
log_box = ScrolledText(log_frame, wrap=tk.WORD, font=("Arial", 9), height=20)
log_box.pack(fill="both", expand=True)
log_box.insert(tk.END, "Sẵn sàng lấy dữ liệu báo cáo quảng cáo...")

# Frame chứa tất cả các điều khiển bên phải
right_frame = ttk.Frame(root, padding="10")
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Frame chọn ngày (đặt vào frame phải)
date_frame = ttk.LabelFrame(right_frame, text="Chọn khoảng thời gian", padding="10")
date_frame.pack(fill="x", pady=10, padx=5, anchor="center")

# Các nút chọn nhanh thời gian
quick_date_frame = ttk.Frame(date_frame)
quick_date_frame.pack(fill="x", padx=5, pady=5)

def set_current_month():
    global start_date, end_date
    today = datetime.now()
    
    # Quy tắc chọn ngày tháng tự động
    if today.day == 1:
        # Nếu là ngày 1: lấy từ ngày 1 đến cuối tháng trước
        if today.month == 1:
            start_month = 12
            start_year = today.year - 1
        else:
            start_month = today.month - 1
            start_year = today.year
            
        days_in_month = monthrange(start_year, start_month)[1]
        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(start_year, start_month, days_in_month)
        
        date_range_label.config(text=f"Từ 01/{start_month}/{start_year} đến {days_in_month}/{start_month}/{start_year}")
        log_box.insert(tk.END, f"\n• Đã chọn: 01/{start_month}/{start_year} - {days_in_month}/{start_month}/{start_year}")
    
    elif 2 <= today.day <= 16:
        # Nếu từ ngày 2-16: lấy từ ngày 1 đến 15 của tháng hiện tại
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month, 15)
        
        date_range_label.config(text=f"Từ 01/{today.month}/{today.year} đến 15/{today.month}/{today.year}")
        log_box.insert(tk.END, f"\n• Đã chọn: 01/{today.month}/{today.year} - 15/{today.month}/{today.year}")
    
    else:
        # Nếu sau ngày 16: lấy từ ngày 1 đến cuối tháng hiện tại
        days_in_month = monthrange(today.year, today.month)[1]
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month, days_in_month)
        
        date_range_label.config(text=f"Từ 01/{today.month}/{today.year} đến {days_in_month}/{today.month}/{today.year}")
        log_box.insert(tk.END, f"\n• Đã chọn: 01/{today.month}/{today.year} - {days_in_month}/{today.month}/{today.year}")
    
    log_box.see(tk.END)

def set_last_month():
    global start_date, end_date
    today = datetime.now()
    # Tháng trước
    if today.month == 1:
        last_month = 12
        last_month_year = today.year - 1
    else:
        last_month = today.month - 1
        last_month_year = today.year
    
    days_in_month = monthrange(last_month_year, last_month)[1]
    
    start_date = datetime(last_month_year, last_month, 1)
    end_date = datetime(last_month_year, last_month, days_in_month)
    
    date_range_label.config(text=f"Từ 01/{last_month}/{last_month_year} đến {days_in_month}/{last_month}/{last_month_year}")
    log_box.insert(tk.END, f"\n• Đã chọn: Tháng {last_month}/{last_month_year}")
    log_box.see(tk.END)

def set_two_months_ago():
    global start_date, end_date
    today = datetime.now()
    # 2 tháng trước
    if today.month == 1:
        two_months_ago = 11
        two_months_ago_year = today.year - 1
    elif today.month == 2:
        two_months_ago = 12
        two_months_ago_year = today.year - 1
    else:
        two_months_ago = today.month - 2
        two_months_ago_year = today.year
    
    days_in_month = monthrange(two_months_ago_year, two_months_ago)[1]
    
    start_date = datetime(two_months_ago_year, two_months_ago, 1)
    end_date = datetime(two_months_ago_year, two_months_ago, days_in_month)
    
    date_range_label.config(text=f"Từ 01/{two_months_ago}/{two_months_ago_year} đến {days_in_month}/{two_months_ago}/{two_months_ago_year}")
    log_box.insert(tk.END, f"\n• Đã chọn: Tháng {two_months_ago}/{two_months_ago_year}")
    log_box.see(tk.END)

# Style cho nút
date_button_style = ttk.Style()
date_button_style.configure("Date.TButton", font=("Arial", 9), padding=2)

# Nút chọn nhanh thời gian
btn_current_month = ttk.Button(
    quick_date_frame, 
    text="Tháng này", 
    style="Date.TButton",
    command=set_current_month
)
btn_current_month.pack(side=tk.LEFT, padx=5, pady=5, expand=True)

btn_last_month = ttk.Button(
    quick_date_frame, 
    text="Tháng trước", 
    style="Date.TButton",
    command=set_last_month
)
btn_last_month.pack(side=tk.LEFT, padx=5, pady=5, expand=True)

btn_two_months_ago = ttk.Button(
    quick_date_frame, 
    text="2 tháng trước", 
    style="Date.TButton",
    command=set_two_months_ago
)
btn_two_months_ago.pack(side=tk.LEFT, padx=5, pady=5, expand=True)

# Bộ chọn ngày tháng thủ công
manual_date_frame = ttk.Frame(date_frame)
manual_date_frame.pack(fill="x", padx=5, pady=5)

# Label và DateEntry cho ngày bắt đầu
start_date_label = ttk.Label(manual_date_frame, text="Từ ngày:", font=("Arial", 9))
start_date_label.pack(side=tk.LEFT, padx=5, pady=5)

start_date_picker = DateEntry(manual_date_frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
start_date_picker.pack(side=tk.LEFT, padx=5, pady=5)

# Label và DateEntry cho ngày kết thúc
end_date_label = ttk.Label(manual_date_frame, text="Đến ngày:", font=("Arial", 9))
end_date_label.pack(side=tk.LEFT, padx=5, pady=5)

end_date_picker = DateEntry(manual_date_frame, width=12, background='darkblue',
                           foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
end_date_picker.pack(side=tk.LEFT, padx=5, pady=5)

# Nút áp dụng khoảng thời gian
def apply_custom_date_range():
    global start_date, end_date
    start_date = start_date_picker.get_date()
    end_date = end_date_picker.get_date()
    date_range_label.config(text=f"Từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}")
    log_box.insert(tk.END, f"\n• Đã chọn thủ công: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    log_box.see(tk.END)

apply_date_button = ttk.Button(manual_date_frame, text="Áp dụng", command=apply_custom_date_range)
apply_date_button.pack(side=tk.LEFT, padx=10, pady=5)

# Hiển thị khoảng thời gian đã chọn
date_range_label = ttk.Label(date_frame, text="Chưa chọn khoảng thời gian", font=("Arial", 9, "italic"))
date_range_label.pack(fill="x", padx=5, pady=5)

# Frame chứa các nút chức năng
button_frame = ttk.Frame(right_frame, padding="10")
button_frame.pack(fill="x", pady=10, padx=5, anchor="center")

# Cập nhật hàm xử lý nút Facebook Ads
def get_facebook_ads_data():
    global is_fetching
    if is_fetching:
        log_box.insert(tk.END, "\n• Đang có yêu cầu đang xử lý, vui lòng đợi...")
        log_box.see(tk.END)
        return
    
    is_fetching = True
    log_box.insert(tk.END, "\n• Đang gửi yêu cầu lấy dữ liệu Facebook Ads...")
    log_box.see(tk.END)
    
    # Cập nhật trạng thái nút để hiển thị cho người dùng
    btn_facebook.config(state="disabled")
    
    def fetch_data():
        global is_fetching
        data = {}
        if start_date and end_date:
            data = {
                "start": start_date.strftime("%d/%m/%Y"),
                "end": end_date.strftime("%d/%m/%Y")
            }
        
        try:
            response = requests.post("https://endpoint.binhthuanford.com/api/fb_report", json=data)
            result = response.json()
            
            # Cập nhật UI từ luồng chính
            root.after(0, lambda: update_ui(result))
        except Exception as e:
            # Cập nhật UI từ luồng chính khi có lỗi
            root.after(0, lambda: update_ui_error(str(e)))
        finally:
            # Đặt lại trạng thái
            is_fetching = False
    
    def update_ui(result):
        if result.get("status") == "success":
            log_box.insert(tk.END, "\n• Lấy dữ liệu Facebook Ads thành công!")
        else:
            log_box.insert(tk.END, f"\n• Lỗi: {result.get('message', 'Không xác định')}")
        log_box.see(tk.END)
        btn_facebook.config(state="normal")
    
    def update_ui_error(error_msg):
        log_box.insert(tk.END, f"\n• Lỗi kết nối: {error_msg}")
        log_box.see(tk.END)
        btn_facebook.config(state="normal")
    
    # Bắt đầu một luồng mới để thực hiện tác vụ
    threading.Thread(target=fetch_data, daemon=True).start()

# Cập nhật lại hàm xử lý nút Google Ads
def get_google_ads_data():
    # Hiển thị thông báo thay vì gọi API
    log_box.insert(tk.END, "\n• Nút này Tạm thời chưa hoạt động")
    log_box.see(tk.END)

# Style cho nút chức năng
button_style = ttk.Style()
button_style.configure("Action.TButton", font=("Arial", 10, "bold"), padding=5)

# Nút lấy dữ liệu Facebook Ads
btn_facebook = ttk.Button(
    button_frame, 
    text="Lấy dữ liệu Facebook Ads", 
    style="Action.TButton",
    command=get_facebook_ads_data
)
btn_facebook.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

# Nút lấy dữ liệu Google Ads
btn_google = ttk.Button(
    button_frame, 
    text="Lấy dữ liệu Google Ads", 
    style="Action.TButton",
    command=get_google_ads_data
)
btn_google.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

# Nút thoát ứng dụng
btn_exit = ttk.Button(
    button_frame, 
    text="Thoát", 
    style="Action.TButton",
    command=root.destroy  # Gọi phương thức destroy để đóng ứng dụng
)
btn_exit.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

# Footer (thay đổi vị trí)
footer_frame = ttk.Frame(root)
footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

separator = ttk.Separator(footer_frame, orient="horizontal")
separator.pack(fill="x", pady=5)

version_label = ttk.Label(footer_frame, text="Báo cáo Quảng cáo v1.0", font=("Arial", 8), foreground="gray")
version_label.pack(anchor="center")

# Khởi tạo mặc định là tháng hiện tại
set_current_month()

# Chạy ứng dụng
root.mainloop()
