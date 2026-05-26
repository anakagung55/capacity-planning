import requests
import pandas as pd
from datetime import datetime, timedelta

# 1. Setup Kredensial
CLOCKIFY_API_KEY = '<YOUR_CLOCKIFY_API_KEY>'
WORKSPACE_ID = '<YOUR_WORKSPACE_ID>'

# 2. Daftar User ID Tim 
team_users = {
    "Abu Baskara": "<USER_ID>",
    "Agung Ajus": "<USER_ID>",
    "Alex Russo": "<USER_ID>",
    "Andrew Branagan": "<USER_ID>",
    "Ben Stone": "<USER_ID>",
    "Denny Ferdiansyah": "<USER_ID>",
    "Kate Wiggins": "<USER_ID>",   
    "Tabatha Shaw": "<USER_ID>",
    "Tom Adams": "<USER_ID>"
}

# 3. Setup Timeframe (14 Hari Terakhir)
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=14)
start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
end_iso = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

headers = {
    "X-Api-Key": CLOCKIFY_API_KEY
}

all_time_entries = []

# 4. Looping untuk menarik data tiap user
print("Memulai ekstraksi data Clockify...")
for name, user_id in team_users.items():
    print(f"Menarik data untuk: {name}")
    url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/user/{user_id}/time-entries"
    params = {
        "start": start_iso,
        "end": end_iso,
        "page-size": 200 # Ambil maksimal 200 log per orang
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        entries = response.json()
        for entry in entries:
            # Ekstraksi field penting
            description = entry.get('description', '')
            # Menghitung durasi (Clockify pakai format PTxHxMxS, lebih aman tarik start & end time lalu hitung di pandas nanti)
            time_interval = entry.get('timeInterval', {})
            start_time = time_interval.get('start')
            end_time = time_interval.get('end')
            
            all_time_entries.append({
                "Name": name,
                "Description": description,
                "Start_Time": start_time,
                "End_Time": end_time,
                "Is_Billable": entry.get('billable', False)
            })
    else:
        print(f"Gagal menarik data {name}. Error: {response.text}")

# 5. Export ke CSV
df = pd.DataFrame(all_time_entries)
df.to_csv('clockify_team_entries.csv', index=False)
print(f"Selesai! {len(df)} baris data berhasil disimpan ke 'clockify_team_entries.csv'")