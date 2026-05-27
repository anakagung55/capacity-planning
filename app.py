import streamlit as st
import pandas as pd
from jinja2 import Template
import streamlit.components.v1 as components

# Konfigurasi Halaman (Hapus semua padding bawaan Streamlit)
st.set_page_config(page_title="Team Capacity Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; padding-left: 0rem !important; padding-right: 0rem !important; max-width: 100% !important; }
        header { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df_merged = pd.read_csv('data/capacity_dashboard_final.csv')
        df_clockify = pd.read_csv('data/clockify_team_entries.csv').fillna("-")
        df_jira = pd.read_csv('data/jira_team_tickets.csv').fillna("-")
        return df_merged, df_clockify, df_jira
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, df_clockify, df_jira = load_data()

if not df.empty:
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

        # SOLUSI FINAL: Gunakan cara rendering resmi Streamlit.
        # Height di-set ke 850px (ukuran wajar layar monitor), scrolling dimatikan
        # karena HTML buatan kita sudah bisa scrolling sendiri di dalamnya!
        components.html(html_ready, height=850, scrolling=False)

    except FileNotFoundError:
        st.error("File 'templates/dashboard.html' tidak ditemukan!")
else:
    st.error("Data CSV tidak ditemukan.")