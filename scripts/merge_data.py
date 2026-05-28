import pandas as pd
import re
import numpy as np

# 1. Load Data
df_clockify = pd.read_csv('data/clockify_team_entries.csv')
df_jira = pd.read_csv('data/jira_team_tickets.csv')

# 2. Ekstrak Ticket_ID dari Deskripsi Clockify
def extract_ticket_id(text):
    if pd.isna(text):
        return None
    match = re.search(r'([A-Z]+-\d+)', str(text))
    return match.group(1) if match else None

df_clockify['Ticket_ID'] = df_clockify['Description'].apply(extract_ticket_id)

# 3. Hitung Durasi & Filter Waktu (PENTING!)
df_clockify['Start_Time'] = pd.to_datetime(df_clockify['Start_Time'], utc=True)
df_clockify['End_Time'] = pd.to_datetime(df_clockify['End_Time'], utc=True)

# FILTER UNTUK MINGGU LALU (Senin minggu lalu - Minggu kemarin)
today = pd.Timestamp.now(tz='UTC')
start_of_this_week = today - pd.Timedelta(days=today.dayofweek)
start_of_this_week = start_of_this_week.replace(hour=0, minute=0, second=0, microsecond=0)

start_of_last_week = start_of_this_week - pd.Timedelta(days=7)
end_of_last_week = start_of_this_week - pd.Timedelta(seconds=1)

# Ambil data minggu lalu
df_clockify_poc = df_clockify[(df_clockify['Start_Time'] >= start_of_last_week) & (df_clockify['Start_Time'] <= end_of_last_week)].copy()
df_clockify_poc['Duration_Hrs'] = (df_clockify_poc['End_Time'] - df_clockify_poc['Start_Time']).dt.total_seconds() / 3600

# 4. Agregasi Time Spent (Dari Clockify)
time_spent_per_user = df_clockify_poc.groupby('Name')['Duration_Hrs'].sum().reset_index()

# INI BARIS YANG TERLEWAT: Mengubah nama kolom agar sama dengan Jira
time_spent_per_user.rename(columns={'Name': 'Assignee', 'Duration_Hrs': 'Time_Spent_This_Week'}, inplace=True)

# 5. Agregasi Remaining Estimate per Orang (Dari Jira)
remaining_per_user = df_jira.groupby('Assignee')['Remaining_Estimate_Hrs'].sum().reset_index()

# 6. Gabungkan Data (Merge)
df_dashboard = pd.merge(time_spent_per_user, remaining_per_user, on='Assignee', how='outer').fillna(0)

# 7. Hitung Sisa Kapasitas (Asumsi Kapasitas Mingguan = 40 Jam)
WEEKLY_CAPACITY = 40
df_dashboard['Capacity_Left'] = WEEKLY_CAPACITY - (df_dashboard['Time_Spent_This_Week'] + df_dashboard['Remaining_Estimate_Hrs'])

# 8. Simpan
df_dashboard.to_csv('capacity_dashboard_final.csv', index=False)
print("Selesai! Bug filter waktu dan nama kolom sudah diperbaiki.")