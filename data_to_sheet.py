from zk import ZK, const
import pandas as pd
from datetime import datetime, time, timedelta
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from dateutil.relativedelta import relativedelta 

def upload_to_google_sheet(df, file_id, sheet_name):
    # Đăng nhập và kết nối tới Google Sheets API
    gc = gspread.service_account(filename="creds.json")

    # Mở file Google Sheets đã có
    try:
        spreadsheet = gc.open_by_key(file_id)  # Mở file dựa trên ID
    except Exception as e:
        raise Exception(f"Lỗi khi mở file Google Sheet: {e}")

    # Tạo một sheet mới trong file đã có
    try:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=df.shape[0] + 1, cols=df.shape[1])  # Thêm sheet mới
    except Exception as e:
        raise Exception(f"Lỗi khi tạo sheet mới trong file: {e}")

    # Ghi dữ liệu vào sheet mới
    try:
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        os.system('cls')
        print(f"Dữ liệu đã được ghi vào sheet {sheet_name} trong file Google Sheets.")
    except Exception as e:
        raise Exception(f"Lỗi khi ghi dữ liệu vào sheet: {e}")

    # Đặt sheet mới lên đầu tiên
    try:
        # Lấy danh sách worksheet
        worksheets = spreadsheet.worksheets()  # Lấy tất cả các worksheets

        # Xác định ID của sheet vừa thêm
        new_sheet_id = next((ws._properties['sheetId'] for ws in worksheets if ws.title == sheet_name), None)

        if not new_sheet_id:
            raise Exception("Không tìm thấy ID của sheet mới tạo.")

        # Tạo danh sách các ID để sắp xếp lại
        reordered_ids = [new_sheet_id] + [
            ws._properties['sheetId'] for ws in worksheets if ws._properties['sheetId'] != new_sheet_id
        ]

        # Sắp xếp lại worksheets
        spreadsheet.batch_update({
            "requests": [{"updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "index": index},
                "fields": "index"
            }} for index, sheet_id in enumerate(reordered_ids)]
        })

        # print(f"Đã đặt sheet {sheet_name} lên đầu tiên.")
    except Exception as e:
        raise Exception(f"Lỗi khi sắp xếp lại sheet: {e}")

    # Trả về link Google Sheet
    sheet_link = f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
    print(f"Dữ liệu đã được đồng bộ thành công từ ngày 27 tháng trước đến hôm nay.")
    return sheet_link

# Kết nối tới máy chấm công và xử lý dữ liệu
zk = ZK('172.16.17.106', port=4370, timeout=15)

try:
    print("Đang kết nối tới máy chấm công...")
    conn = zk.connect()
    print("Kết nối thành công!")

    attendance = conn.get_attendance()
    print("Đang lấy dữ liệu")

    if attendance:
        records = []

        start_time = time(1, 0)
        end_time = time(23, 59)

        today = datetime.now()
        start_date = (today.replace(day=1) - relativedelta(months=1)).replace(day=27)
        end_date = today + timedelta(days=1)
        for record in attendance:
            record_time = record.timestamp
            if start_date <= record_time <= end_date and start_time <= record_time.time() <= end_time:
                user_id = record.user_id
                date_str = record_time.strftime("%Y-%m-%d")
                time_str = record_time.strftime("%H:%M:%S")
                print(f'Dữ liệu: {record}')

                records.append({
                    "User ID": user_id,
                    "Date": date_str,
                    "Time": time_str
                })
        df = pd.DataFrame(records)

        # Thêm cột định danh duy nhất cho mỗi lần chấm công
        df["UniqueID"] = df.groupby(["User ID", "Date"]).cumcount() + 1

        # Pivot dữ liệu với mỗi lần chấm công là một dòng riêng biệt
        df_pivot = df.pivot(index=["User ID", "UniqueID"], columns="Date", values="Time").reset_index()

        # Loại bỏ cột UniqueID nếu không cần hiển thị
        df_pivot = df_pivot.drop(columns=["UniqueID"])

        df_pivot = df_pivot.reindex(columns=["User ID"] + sorted(df["Date"].unique()))
        # print(f'Đang ghi dữ liệu vào file')

        # Lưu file Excel
        now = datetime.now()
        timestamp = now.strftime("%H%M%S")
        file_name = f"Data_cham_cong_{timestamp}.xlsx"
        # df_pivot.to_excel(file_name, index=False)
        # print(f"Dữ liệu đã được ghi vào file Excel: {file_name}")

        # Đưa dữ liệu lên Google Sheet
        # Xử lý NaN trong DataFrame
        df_pivot = df_pivot.fillna("")  # Thay thế NaN bằng chuỗi rỗng
        
        # Đưa dữ liệu lên Google Sheets
        # ID của file Google Sheet đã có sẵn
        file_id = "1Z_eAq_5MshvWG1Ri_IbKlqFVuswhJTlHgJrN0nKrx64" 

        # Tạo tên sheet với thời gian hiện tại
        sheet_name = f"Data_{start_date.strftime('%d-%m')}_{today.strftime('%d-%m')}_{timestamp}"

        upload_to_google_sheet(df_pivot, file_id, sheet_name)

    else:
        print("Không có dữ liệu chấm công nào.")

    conn.disconnect()
    print("Ngắt kết nối với máy chấm công.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")

finally:
    if conn and conn.is_connect:
        conn.disconnect()
        print("Đã ngắt kết nối với máy chấm công.")
    else:
        print("Đã ngắt kết nối thành công.")

input("Nhấn Enter để thoát...")