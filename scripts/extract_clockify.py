import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

# 1. Setup Kredensial
CLOCKIFY_API_KEY = 'MDg3MjBlZTctODZmNi00NGNlLWFlMjQtYWEzZjVhMmViODY0'
WORKSPACE_ID = '68abc134af2ceb7c58ddcb22' # <-- INI WORKSPACE ASLI YANG BENAR!

# 2. Daftar User ID Tim 
team_users = {
    "Abu Baskara": "692cc9e25831f77701ac3344",
    "Agung Ajus": "69924903d96aea171725d0bf",
    "Alex Russo": "691e41d5e268e57a5174a94b",
    "Andrew Branagan": "68abc20baf2ceb7c58ddd4b8",
    "Ben Stone": "68abc135af2ceb7c58ddcb23",
    "Denny Ferdiansyah": "68abc20baf2ceb7c58ddd4ba",
    "Tom Adams": "68abc20baf2ceb7c58ddd4bb"
}

# 3. Setup Timeframe (30 Hari Terakhir / 1 Bulan)
# Memperbaiki warning deprecation UTC
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=30)
start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
end_iso = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

headers = {
    "X-Api-Key": CLOCKIFY_API_KEY
}

all_time_entries = []

# 4. Looping untuk menarik data tiap user
print("Memulai ekstraksi data Clockify untuk 30 HARI TERAKHIR...")
for name, user_id in team_users.items():
    print(f"Menarik data untuk: {name}")
    url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/user/{user_id}/time-entries"
    params = {
        "start": start_iso,
        "end": end_iso,
        "page-size": 1000 # Diperbesar agar muat log satu bulan penuh
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        entries = response.json()
        for entry in entries:
            # Ekstraksi field penting
            description = entry.get('description', '')
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