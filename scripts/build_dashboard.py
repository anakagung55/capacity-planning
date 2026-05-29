import pandas as pd
from jinja2 import Template

def generate_html():
    print("Memuat data CSV...")
    try:
        df = pd.read_csv('data/capacity_dashboard_final.csv')
        df_clockify = pd.read_csv('data/clockify_team_entries.csv').fillna("-")
        df_jira = pd.read_csv('data/jira_team_tickets.csv').fillna("-")
    except Exception as e:
        print(f"Error membaca data: {e}")
        return

    if df.empty:
        print("Data kosong!")
        return

    # Proses Metrik
    team_count = len(df)
    total_logged = round(df['Time_Spent_This_Week'].sum(), 1)
    total_remaining = round(df['Remaining_Estimate_Hrs'].sum(), 1)
    capacity_free = round(df[df['Capacity_Left'] > 0]['Capacity_Left'].sum(), 1)

    team_data = []
    for _, row in df.iterrows():
        name = row['Assignee']
        initials = "".join([n[0] for n in str(name).split()[:2]]).upper() if pd.notna(name) else "??"
        time_spent = round(row['Time_Spent_This_Week'], 1)
        remaining = round(row['Remaining_Estimate_Hrs'], 1)
        capacity = round(row['Capacity_Left'], 1)
        util_pct = min(round((time_spent / 40) * 100), 100)
        
        if capacity < 0:
            status, color_var, badge_class, badge_text = 'overloaded', '--red', 'badge-red', 'Overloaded'
        elif capacity < 8:
            status, color_var, badge_class, badge_text = 'at-risk', '--amber', 'badge-amber', 'At risk'
        else:
            status, color_var, badge_class, badge_text = 'on-track', '--green', 'badge-green', 'On track'

        team_data.append({
            'name': name, 'initials': initials, 'time_spent': time_spent,
            'remaining': remaining, 'capacity': capacity, 'util_pct': util_pct,
            'status': status, 'color_var': color_var, 'badge_class': badge_class,
            'badge_text': badge_text, 'cap_abs': abs(capacity)
        })

    clockify_list = df_clockify.to_dict(orient='records')
    jira_list = df_jira.to_dict(orient='records')

    print("Merender template HTML...")
    try:
        with open('templates/dashboard.html', 'r', encoding='utf-8') as file:
            template_str = file.read()
            
        template = Template(template_str)
        html_ready = template.render(
            team_count=team_count,
            total_logged=total_logged,
            total_remaining=total_remaining,
            capacity_free=capacity_free,
            team_data=team_data,
            clockify_data=clockify_list,
            jira_data=jira_list
        )

        # SIMPAN SEBAGAI FILE HTML MURNI
        with open('index.html', 'w', encoding='utf-8') as output_file:
            output_file.write(html_ready)
            
        print("✅ SUKSES! File 'index.html' berhasil dibuat.")

    except Exception as e:
        print(f"Gagal merender HTML: {e}")

if __name__ == "__main__":
    generate_html()