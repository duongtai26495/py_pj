from datetime import datetime, timedelta

start_date = datetime(2024, 10, 31)
date_past = start_date - timedelta(days=1438)
date_past.strftime("%d/%m/%Y")


print(date_past)