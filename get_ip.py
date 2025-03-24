
import requests

SECOND_IP_API = "https://bthfapiservices-production.up.railway.app/api/get_ip_nt"
DEFAULT_SECOND_IP = "null"

def get_second_ip():
    try:
        response = requests.get(SECOND_IP_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            second_ip = data.get("ip", DEFAULT_SECOND_IP)
            print(f"Lấy second ip thành công: {second_ip}")
            return second_ip
        else:
            print(f"Lỗi khi lấy second ip, mã lỗi: {response.status_code}. Sử dụng mặc định.")
            return DEFAULT_SECOND_IP
    except Exception as e:
        print(f"Lỗi khi lấy second ip: {e}. Sử dụng mặc định.")
        return DEFAULT_SECOND_IP
    

get_second_ip()