import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from datetime import datetime

TOKEN_FILE = 'access_token.txt'

def save_token(token, expiration_time):
    with open(TOKEN_FILE, 'w') as f:
        f.write(f"{token}\n{expiration_time}")

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            lines = f.readlines()
            token = lines[0].strip()
            expiration_time_str = lines[1].strip()
            expiration_time = datetime.strptime(expiration_time_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            return token, expiration_time
    return None, None

def refresh_access_token(app_id, app_secret, access_token):
    print("Đang làm mới Access Token...")
    url = f"https://graph.facebook.com/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': access_token
    }
    response = requests.get(url, params=params)
    data = response.json()
    if 'access_token' in data:
        new_token = data['access_token']
        expiration_time = datetime.now() + timedelta(days=60)
        return new_token, expiration_time
    else:
        print(f"Lỗi khi làm mới Access Token: {data}")
        return None, None

def get_access_token(app_id, app_secret, access_token):
    token, expiration_time = load_token()
    if token and expiration_time > datetime.now():
        print("Sử dụng Access Token cũ.")
        return token
    else:
        print("Access Token hết hạn hoặc không tồn tại, đang làm mới token...")
        new_token, expiration_time = refresh_access_token(app_id, app_secret, access_token)
        if new_token:
            save_token(new_token, expiration_time)
            return new_token
        else:
            print("Không thể lấy Access Token mới.")
            return None

my_app_id = '3377789839181723'
my_app_secret = 'b16e370dc99305b0a74bad6b97c81453'
my_access_token = 'EAAwAFPt9h5sBO2nAUFzQLNUKQzZBLIqDEEMGdlgES0u8Si38QVJpIAOUZC8XnJNKuBGKapNQG2THfCjT6NsbJCjypnsyJz65eVtgP3a4ZAkZCtJHm2NMY32kTcnZBhwf9dqdqoeyiaX4DkZB4OedoVq00nV6q9faEqYSs6lrx1ZAC0UqZCKcH6tVK01YibwS4JyFbEdCRTeXgMWEimdlvQZBc6jy6YiAvJ0cSLwZDZD'
my_ad_account_id = 'act_751257057052786'

my_access_token = get_access_token(my_app_id, my_app_secret, my_access_token)

if my_access_token:
    FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)

    since = '2024-11-11'
    until = '2024-11-12'

    ad_account = AdAccount(my_ad_account_id)

    params = {
        'fields': [
            'campaign_name',
            'date_start',
            'date_stop',
            'reach',
            'impressions',
            'frequency',
            'objective',
            'actions',
            'spend',
            'cost_per_action_type',
            'inline_link_clicks',
            'unique_clicks',  
            'cpc',
            'cpm',
            'cost_per_thruplay',
            'cost_per_inline_post_engagement',
            'inline_post_engagement'
        ],
        'time_range': {'since': since, 'until': until},
        'level': 'ad',
        'breakdowns': ['region'],
        'time_increment': 1
    }

    try:
        print('Đang lấy dữ liệu từ Meta Ads...')
        insights = ad_account.get_insights(params=params)
        data = [insight for insight in insights]

        if not data:
            print("Không có dữ liệu trả về từ API.")
        else:
            print('Đang sắp xếp dữ liệu...')
            for insight in data:
                actions = insight.get('actions', [])
                results = next((x['value'] for x in actions if x['action_type'] == 'offsite_conversion.fb_pixel_purchase'), 0)
                cost_per_result = next((x['value'] for x in insight.get('cost_per_action_type', []) if x['action_type'] == 'offsite_conversion.fb_pixel_purchase'), 0)
                photo_views = next((x['value'] for x in actions if x['action_type'] == 'photo_view'), 0)  

                insight['results'] = results
                insight['cost_per_result'] = cost_per_result
                insight['photo_views'] = photo_views
                insight['unique_clicks'] = int(insight.get('unique_clicks', 0))  

                clicks = int(insight.get('inline_link_clicks', 0))
                spend = float(insight.get('spend', 0))
                reach = int(insight.get('reach', 0))
                post_engagements = int(insight.get('inline_post_engagement', 0))

                cpc_all = spend / clicks if clicks > 0 else 0
                cpm_reach = (spend / reach * 1000) if reach > 0 else 0  
                cost_per_engagement = spend / post_engagements if post_engagements > 0 else 0  

                insight['cpc_all'] = cpc_all
                insight['cpm_reach'] = cpm_reach  
                insight['cost_per_engagement'] = cost_per_engagement  
                insight['post_engagements'] = post_engagements  

            df = pd.DataFrame(data)

            df.rename(columns={
                'campaign_name': 'Tên chiến dịch',
                'region': 'Vùng',
                'date_start': 'Ngày',
                'reach': 'Người tiếp cận',
                'impressions': 'Lượt hiển thị',
                'frequency': 'Tần suất',
                'objective': 'Loại kết quả',
                'results': 'Kết quả',
                'spend': 'Số tiền đã chi tiêu (VND)',
                'cost_per_result': 'Chi phí trên mỗi kết quả',
                'inline_link_clicks': 'Lượt click vào liên kết',
                'cpc': 'CPC (Chi phí trên mỗi lượt click)',
                'photo_views': 'Lượt xem ảnh',
                'unique_clicks': 'Số lần nhấp vào liên kết duy nhất',
                'cpm': 'CPM (Chi phí trên mỗi 1000 lần hiển thị)',
                'cpc_all': 'CPC (tất cả)',
                'cpm_reach': 'Chi phí trên mỗi 1000 tài khoản tiếp cận',  
                'cost_per_engagement': 'Chi phí trên mỗi lượt tương tác trên bài viết', 
                'post_engagements': 'Lượt tương tác với bài viết'  # Cột mới
            }, inplace=True)

            df['Bắt đầu báo cáo'] = since
            df['Kết thúc báo cáo'] = until


            desired_order = [
                'Tên chiến dịch',
                'Vùng',
                'Ngày',
                'Người tiếp cận',
                'Lượt hiển thị',
                'Tần suất',
                'Loại kết quả',
                'Kết quả',
                'Số tiền đã chi tiêu (VND)',
                'Chi phí trên mỗi kết quả',
                'Lượt click vào liên kết',
                'CPC (Chi phí trên mỗi lượt click)',
                'Lượt xem ảnh',
                'Số lần nhấp vào liên kết duy nhất',
                'CPM (Chi phí trên mỗi 1000 lần hiển thị)',
                'Chi phí trên mỗi 1000 tài khoản tiếp cận',  
                'Chi phí trên mỗi lượt tương tác trên bài viết',
                'Lượt tương tác với bài viết',
                'Bắt đầu báo cáo',
                'Kết thúc báo cáo'
            ]

            df = df[desired_order]

            print('Đang ghi dữ liệu vào file Excel...')

            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")  

            file_name = f"report_{since}_to_{until}_{timestamp}.xlsx"
            df.to_excel(file_name, index=False, engine='openpyxl')
            print(f"Dữ liệu đã được xuất ra file {file_name}")


    except Exception as e:
        print(f"Đã xảy ra lỗi khi lấy dữ liệu: {e}")
else:
    print("Không thể lấy Access Token hợp lệ.")
