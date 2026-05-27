import os
import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
from dotenv import load_dotenv

# Load rahasia dari .env
load_dotenv()

# 1. Setup Kredensial Jira
JIRA_DOMAIN = 'https://bluerockdigital.atlassian.net'
JIRA_EMAIL = 'agung.ajus@staroster.com'
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')


# 2. Daftar Nama Tim
team_names = [
    "Abu Baskara", "Agung Ajus", "Alex Russo", "Andrew Branagan", 
    "Ben Stone", "Denny Ferdiansyah", "Kate Wiggins", "Tabatha Shaw", "Tom Adams"
]

# 3. Setup JQL (Jira Query Language)
jql_query = f'assignee IN ("{('", "').join(team_names)}") AND statusCategory != Done'

# URL Endpoint yang BARU
url = f"{JIRA_DOMAIN}/rest/api/3/search/jql"

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# 4. Payload yang BENAR
payload = json.dumps({
    "jql": jql_query,  # Menggunakan "jql" (bukan jqls)
    "maxResults": 100, # Direkomendasikan 100 untuk stabilitas Jira Cloud API
    "fields": [
        "summary", 
        "assignee", 
        "timeoriginalestimate", 
        "timeestimate",
        "timespent",
        "status"
    ]
})

print("Memulai ekstraksi data dari Jira...")
response = requests.post(url, data=payload, headers=headers, auth=auth)

if response.status_code == 200:
    data = response.json()
    
    # 5. Parsing Response yang Benar
    issues = data.get('issues', [])
    print(f"Berhasil menemukan {len(issues)} tiket aktif.")
    
    jira_data = []
    for issue in issues:
        key = issue.get('key')
        fields = issue.get('fields', {})
        assignee_data = fields.get('assignee')
        assignee_name = assignee_data.get('displayName', 'Unassigned') if assignee_data else 'Unassigned'
        status_name = fields.get('status', {}).get('name', 'Unknown')
        
        # Konversi detik ke Jam
        original_est_hrs = (fields.get('timeoriginalestimate') or 0) / 3600
        remaining_est_hrs = (fields.get('timeestimate') or 0) / 3600
        time_spent_hrs = (fields.get('timespent') or 0) / 3600
        
        jira_data.append({
            "Ticket_ID": key,
            "Assignee": assignee_name,
            "Status": status_name,
            "Summary": fields.get('summary'),
            "Original_Estimate_Hrs": original_est_hrs,
            "Remaining_Estimate_Hrs": remaining_est_hrs,
            "Time_Spent_Jira_Hrs": time_spent_hrs
        })
        
    # 6. Simpan ke CSV
    df = pd.DataFrame(jira_data)
    df.to_csv('jira_team_tickets.csv', index=False)
    print("Selesai! Data berhasil disimpan ke 'jira_team_tickets.csv'")
else:
    print(f"Gagal! Error {response.status_code}: {response.text}")