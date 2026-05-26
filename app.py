import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Capacity Planning PoC", layout="wide", initial_sidebar_state="expanded")

st.title("BlueRock Capacity Planning & Forecasting")
st.write("Real-time workload visibility integrating Clockify & Jira data.")

# 2. Load Semua Data
@st.cache_data
def load_data():
    df_merged = pd.read_csv('data/capacity_dashboard_final.csv')
    df_clockify = pd.read_csv('data/clockify_team_entries.csv')
    df_jira = pd.read_csv('data/jira_team_tickets.csv')
    return df_merged, df_clockify, df_jira

df_merged, df_clockify, df_jira = load_data()

# --- SIDEBAR & FILTERS ---
st.sidebar.header("⚙️ Configuration & Filters")
api_key = st.sidebar.text_input("Insert Gemini API Key for Smart Narrative:", type="password")

st.sidebar.divider()
st.sidebar.subheader("Filter Data")

# Filter by Person
assignee_list = df_merged['Assignee'].unique().tolist()
selected_assignees = st.sidebar.multiselect(
    "Select Team Members:",
    options=assignee_list,
    default=assignee_list
)

# Terapkan Filter ke Ketiga Data
filtered_merged = df_merged[df_merged['Assignee'].isin(selected_assignees)]
filtered_clockify = df_clockify[df_clockify['Name'].isin(selected_assignees)]
filtered_jira = df_jira[df_jira['Assignee'].isin(selected_assignees)]

# --- METRICS BANNERS ---
st.markdown("### 📊 Quick Metrics")
met1, met2, met3 = st.columns(3)
with met1:
    overloaded_count = len(filtered_merged[filtered_merged['Capacity_Left'] < 0])
    st.metric(label="Overloaded Members", value=overloaded_count)
with met2:
    total_time_spent = round(filtered_merged['Time_Spent_This_Week'].sum(), 1)
    st.metric(label="Total Time Spent (Hrs)", value=total_time_spent)
with met3:
    total_remaining = round(filtered_merged['Remaining_Estimate_Hrs'].sum(), 1)
    st.metric(label="Total Remaining Estimates", value=total_remaining)

st.divider()

# --- AI SMART NARRATIVE ---
st.markdown("### ✨ AI Workload Summary")
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        data_string = filtered_merged.to_string(index=False)
        prompt = f"""
        You are an AI assistant for a tech team. Analyze the following capacity planning data and provide a concise, bulleted summary (max 3 bullets).
        Focus on: 1. Who is overloaded (Capacity_Left < 0). 2. Who has the most free capacity. 3. A brief note if 'Remaining_Estimate_Hrs' is mostly 0.
        Keep it professional, sharp, and Claude-like.
        Data: {data_string}
        """
        
        if st.button("Generate AI Insights 🤖"):
            with st.spinner("Analyzing workload data..."):
                response = model.generate_content(prompt)
                st.info(response.text)
    except Exception as e:
        st.error(f"Failed to generate AI narrative. Error: {e}")
else:
    st.warning("👈 Please enter your Gemini API Key in the sidebar to unlock the AI Smart Narrative.")

st.divider()

# --- TABS UNTUK MENGAKOMODASI SEMUA DATA ---
tab1, tab2, tab3 = st.tabs(["📌 Overview (Merged)", "⏱️ Clockify (Time Logged)", "🎯 Jira Pipeline (Remaining)"])

# TAB 1: OVERVIEW (Grafik & Ringkasan)
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Merged Capacity Data**")
        st.dataframe(filtered_merged, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Workload vs Capacity Chart**")
        if not filtered_merged.empty:
            chart_data = filtered_merged.set_index('Assignee')[['Time_Spent_This_Week', 'Capacity_Left']]
            st.bar_chart(chart_data)

# TAB 2: CLOCKIFY DETAILS
with tab2:
    st.markdown("### ⏱️ Time Entries Detail (What was done)")
    st.write("Daftar aktivitas yang telah dicatat oleh tim berdasarkan filter.")
    st.dataframe(filtered_clockify[['Name', 'Description', 'Start_Time', 'Is_Billable']], use_container_width=True, hide_index=True)

# TAB 3: JIRA PIPELINE DETAILS
with tab3:
    st.markdown("### 🎯 Jira Pipeline (What's left)")
    st.write("Daftar tiket aktif yang belum berstatus 'Done'.")
    st.dataframe(filtered_jira[['Assignee', 'Ticket_ID', 'Summary', 'Status', 'Remaining_Estimate_Hrs']], use_container_width=True, hide_index=True)