import requests
import schedule
import time
import datetime

def get_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip_data = response.json()
        return ip_data['ip']
    except Exception as e:
        print(f"Error fetching IP: {e}")
        return None

def send_ip(ip, startup):
    endpoint = 'https://bthfapiservices-production.up.railway.app/api/update_ip_nt'
    if startup:
        endpoint = 'https://bthfapiservices-production.up.railway.app/api/send_check_notify'

    payload = {'ip': ip}
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            print(f"IP {ip} sent successfully to {endpoint} at {datetime.datetime.now()}")
        else:
            print(f"Failed to send IP {ip} to {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"Error sending IP to {endpoint}: {e}")

def job():
    ip = get_ip()
    if ip:
        send_ip(ip, False)

def startup():
    print("Sending IP immediately after program starts...")
    ip = get_ip()
    if ip:
        send_ip(ip, True)

schedule.every().day.at("07:45").do(job)
schedule.every().day.at("13:45").do(job)
schedule.every().day.at("17:30").do(job)
schedule.every().day.at("19:45").do(job)

startup()

while True:
    schedule.run_pending()
    time.sleep(60)
