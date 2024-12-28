import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import pandas as pd
import os
from zk import ZK
from dateutil.relativedelta import relativedelta
import gspread
import json

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


def download_data(log_box):
    zk = ZK('172.16.17.106', port=4370, timeout=15)
    try:
        log_box.insert(tk.END, "\n")
        log_box.insert(tk.END, "\n\u2022 Đang kết nối tới máy chấm công...")
        log_box.update()
        conn = zk.connect()
        log_box.insert(tk.END, "\n\u2022 Kết nối thành công!")

        attendance = conn.get_attendance()
        if attendance:
            records = {}
            start_date = datetime.strptime("2024-12-15", "%Y-%m-%d")
            # start_date = (datetime.now().replace(day=1) - relativedelta(months=1)).replace(day=28)
            end_date = datetime.now() + relativedelta(days=1)

            for record in attendance:
                
                log_box.insert(tk.END, f"\n\u2022 Đang tải dữ liệu {record}")
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
                    rows.append([user_id, "", *sorted(timestamps)[:6]])
                    
            df = pd.DataFrame(rows, columns=["ID", "Cột trống", "Timestamp 1", "Timestamp 2", "Timestamp 3", "Timestamp 4", "Timestamp 5", "Timestamp 6"])
            file_id = "1Z_eAq_5MshvWG1Ri_IbKlqFVuswhJTlHgJrN0nKrx64"
            sheet_name = "Data_ChamCong"

            link = upload_to_google_sheet(df.fillna(""), file_id, sheet_name)

            log_box.insert(tk.END, f"\n\u2022 Dữ liệu đã được đồng bộ thành công!")
        else:
            log_box.insert(tk.END, "\n\u2022 Không có dữ liệu chấm công nào.")

        conn.disconnect()
    except Exception as e:
        log_box.insert(tk.END, f"\n\u2022 Đã xảy ra lỗi: {e}")
    finally:
        if conn and conn.is_connect:
            conn.disconnect()
        log_box.insert(tk.END, "\n")
        log_box.insert(tk.END, "\n\u2022 Quá trình xử lý hoàn tất.")
        log_box.see(tk.END)

def start_process(log_box):
    log_box.insert(tk.END, "\nBắt đầu xử lý...")
    log_box.update()
    try:
        download_data(log_box)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")

root = tk.Tk()
root.title("Phần mềm tải lên dữ liệu chấm công (BThFord 2025)")
root.geometry("500x400")


log_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), fg="green", bg="#f7f7f7", height=15)
log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

frame = tk.Frame(root)
frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)

start_button = tk.Button(frame, text="Bắt đầu", command=lambda: start_process(log_box), font=("Arial", 12), width=15)
start_button.pack(side=tk.LEFT, expand=True, padx=5)

exit_button = tk.Button(frame, text="Thoát", command=root.quit, font=("Arial", 12), width=15)
exit_button.pack(side=tk.RIGHT, expand=True, padx=5)


root.mainloop()
