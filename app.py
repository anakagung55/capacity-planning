from flask import Flask, render_template, request, jsonify
from flask_caching import Cache  # <-- TAMBAHAN BARU: Import library Caching
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- KONFIGURASI CACHE (OPTIMASI SUPER NGEBUT) ---
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Simpan memori selama 5 menit (300 detik)
cache = Cache(app)

CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')
WORKSPACE_ID = os.getenv('WORKSPACE_ID')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_DOMAIN = 'https://bluerockdigital.atlassian.net'
JIRA_EMAIL = 'agung.ajus@staroster.com'

team_users = {
    "Abu Baskara": "692cc9e25831f77701ac3344",
    "Agung Ajus": "69924903d96aea171725d0bf",
    "Alex Russo": "691e41d5e268e57a5174a94b",
    "Andrew Branagan": "68abc20baf2ceb7c58ddd4b8",
    "Denny Ferdiansyah": "68abc20baf2ceb7c58ddd4ba",
    "Kate Wiggins": "68abc20baf2ceb7c58ddd4b9",
    "Tabatha Shaw": "69646a1c3fcbbd3370cf0ce1",
    "Tom Adams": "68abc20baf2ceb7c58ddd4bb"
}
team_names = list(team_users.keys())

def fetch_clockify_realtime(start_date, end_date):
    start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_iso = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    all_entries = []

    for name, user_id in team_users.items():
        if user_id.startswith("<"): 
            continue 
            
        url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/user/{user_id}/time-entries"
        params = {"start": start_iso, "end": end_iso, "page-size": 200}
        
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                for entry in resp.json():
                    time_inv = entry.get('timeInterval', {})
                    all_entries.append({
                        "Name": name, 
                        "Description": entry.get('description', ''),
                        "Start_Time": time_inv.get('start'),
                        "End_Time": time_inv.get('end'),
                        "Is_Billable": entry.get('billable', False) 
                    })
            else:
                print(f"Gagal narik data {name}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Koneksi error ke Clockify untuk {name}: {e}")
            
    return pd.DataFrame(all_entries)

def fetch_jira_realtime():
    team_names_joined = '", "'.join(team_names)
    jql_query = f'assignee IN ("{team_names_joined}") AND statusCategory != Done'
    url = f"{JIRA_DOMAIN}/rest/api/3/search/jql"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = json.dumps({
        "jql": jql_query, "maxResults": 100,
        "fields": ["summary", "assignee", "timeestimate", "status"]
    })

    jira_data = []
    try:
        resp = requests.post(url, data=payload, headers=headers, auth=auth)
        if resp.status_code == 200:
            for issue in resp.json().get('issues', []):
                fields = issue.get('fields', {})
                assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
                jira_data.append({
                    "Ticket_ID": issue.get('key'),
                    "Assignee": assignee,
                    "Status": fields.get('status', {}).get('name', 'Unknown'),
                    "Summary": fields.get('summary'),
                    "Remaining_Estimate_Hrs": (fields.get('timeestimate') or 0) / 3600
                })
    except Exception as e:
         print(f"Connection Error ke Jira: {e}")
         
    return pd.DataFrame(jira_data)

@app.route('/')
@cache.cached(query_string=True) # <-- TAMBAHAN BARU: Simpan tampilan di memori berdasarkan filter (This Week/Last Week/dll)
def dashboard():
    timeframe = request.args.get('timeframe', 'this_week')
    
    today = datetime.now(timezone.utc)
    start_of_this_week = today - timedelta(days=today.weekday())
    start_of_this_week = start_of_this_week.replace(hour=0, minute=0, second=0, microsecond=0)

    if timeframe == 'last_week':
        start_date = start_of_this_week - timedelta(days=7)
        end_date = start_of_this_week - timedelta(seconds=1)
        capacity_baseline = 40
    elif timeframe == 'this_month':
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
        capacity_baseline = 160
    elif timeframe == 'forecast':
        start_date = today + timedelta(days=30) 
        end_date = today + timedelta(days=30)
        capacity_baseline = 40
    else: 
        start_date = start_of_this_week
        end_date = today
        capacity_baseline = 40

    df_clockify = fetch_clockify_realtime(start_date, end_date)
    df_jira = fetch_jira_realtime()

    if not df_clockify.empty:
        df_clockify['Start_Time'] = pd.to_datetime(df_clockify['Start_Time'])
        df_clockify['End_Time'] = pd.to_datetime(df_clockify['End_Time'])
        df_clockify['Duration_Hrs'] = (df_clockify['End_Time'] - df_clockify['Start_Time']).dt.total_seconds() / 3600
        
        # Hitung Total Time
        time_spent_per_user = df_clockify.groupby('Name')['Duration_Hrs'].sum().reset_index()
        time_spent_per_user.rename(columns={'Name': 'Assignee', 'Duration_Hrs': 'Time_Spent'}, inplace=True)

        # Hitung Billable Time
        df_billable = df_clockify[df_clockify['Is_Billable'] == True]
        billable_spent = df_billable.groupby('Name')['Duration_Hrs'].sum().reset_index()
        billable_spent.rename(columns={'Name': 'Assignee', 'Duration_Hrs': 'Billable_Hrs'}, inplace=True)

        # Hitung Non-Billable Time
        df_non_billable = df_clockify[df_clockify['Is_Billable'] == False]
        non_billable_spent = df_non_billable.groupby('Name')['Duration_Hrs'].sum().reset_index()
        non_billable_spent.rename(columns={'Name': 'Assignee', 'Duration_Hrs': 'Non_Billable_Hrs'}, inplace=True)

        df_clockify['Start_Time'] = df_clockify['Start_Time'].dt.strftime('%Y-%m-%d %H:%M')
    else:
        time_spent_per_user = pd.DataFrame(columns=['Assignee', 'Time_Spent'])
        billable_spent = pd.DataFrame(columns=['Assignee', 'Billable_Hrs'])
        non_billable_spent = pd.DataFrame(columns=['Assignee', 'Non_Billable_Hrs'])

    if not df_jira.empty:
        remaining_per_user = df_jira.groupby('Assignee')['Remaining_Estimate_Hrs'].sum().reset_index()
    else:
        remaining_per_user = pd.DataFrame(columns=['Assignee', 'Remaining_Estimate_Hrs'])

    all_users = pd.DataFrame({'Assignee': team_names})
    
    # Merge Total Waktu
    df_merged = pd.merge(all_users, time_spent_per_user, on='Assignee', how='left')
    df_merged['Time_Spent'] = df_merged['Time_Spent'].fillna(0)
    
    # Merge Billable Waktu
    df_merged = pd.merge(df_merged, billable_spent, on='Assignee', how='left')
    df_merged['Billable_Hrs'] = df_merged['Billable_Hrs'].fillna(0)
    
    # Merge Non-Billable Waktu
    df_merged = pd.merge(df_merged, non_billable_spent, on='Assignee', how='left')
    df_merged['Non_Billable_Hrs'] = df_merged['Non_Billable_Hrs'].fillna(0)
    
    # Merge Jira
    df_merged = pd.merge(df_merged, remaining_per_user, on='Assignee', how='left')
    df_merged['Remaining_Estimate_Hrs'] = df_merged['Remaining_Estimate_Hrs'].fillna(0)
    
    # Kalkulasi Kapasitas Sisa
    df_merged['Capacity_Left'] = capacity_baseline - (df_merged['Time_Spent'] + df_merged['Remaining_Estimate_Hrs'])

    team_count = len(df_merged)
    total_logged = round(df_merged['Time_Spent'].sum(), 1)
    total_remaining = round(df_merged['Remaining_Estimate_Hrs'].sum(), 1)
    capacity_free = round(df_merged[df_merged['Capacity_Left'] > 0]['Capacity_Left'].sum(), 1)

    team_data = []
    for _, row in df_merged.iterrows():
        name = row['Assignee']
        initials = "".join([n[0] for n in str(name).split()[:2]]).upper()
        time_spent = round(row['Time_Spent'], 1)
        billable_hrs = round(row['Billable_Hrs'], 1)
        non_billable_hrs = round(row['Non_Billable_Hrs'], 1)
        remaining = round(row['Remaining_Estimate_Hrs'], 1)
        capacity = round(row['Capacity_Left'], 1)
        util_pct = min(round((time_spent / capacity_baseline) * 100), 100) if capacity_baseline > 0 else 0
        
        if capacity < 0:
            status, color_var, badge_class, badge_text = 'overloaded', '--red', 'badge-red', 'Overloaded'
        elif capacity < (capacity_baseline * 0.2):
            status, color_var, badge_class, badge_text = 'at-risk', '--amber', 'badge-amber', 'At risk'
        else:
            status, color_var, badge_class, badge_text = 'on-track', '--green', 'badge-green', 'On track'

        team_data.append({
            'name': name, 'initials': initials, 'time_spent': time_spent,
            'billable_hrs': billable_hrs, 
            'non_billable_hrs': non_billable_hrs, 
            'remaining': remaining, 'capacity': capacity, 'util_pct': util_pct,
            'status': status, 'color_var': color_var, 'badge_class': badge_class,
            'badge_text': badge_text, 'cap_abs': abs(capacity), 'baseline': capacity_baseline
        })

    return render_template('dashboard.html', 
                           team_count=team_count, total_logged=total_logged,
                           total_remaining=total_remaining, capacity_free=capacity_free,
                           team_data=team_data, 
                           clockify_data=df_clockify.to_dict(orient='records') if not df_clockify.empty else [],
                           jira_data=df_jira.to_dict(orient='records') if not df_jira.empty else [], 
                           current_timeframe=timeframe)

@app.route('/api/sync', methods=['POST'])
def sync_data():
    cache.clear() # <-- TAMBAHAN BARU: Hapus memori saat tombol "Sync APIs" ditekan
    return jsonify({"status": "success", "message": "Cache dibersihkan! Data tersinkronisasi live."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)