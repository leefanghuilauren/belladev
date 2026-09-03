import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Set up the app layout and title
st.set_page_config(page_title="Isabella's Tracker", layout="wide")

# Create Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📝 Log a Feed", "📊 Development Dashboard"])

# -----------------------------------------
# PAGE 1: GOOGLE FORM EMBEDDING
# -----------------------------------------
if page == "📝 Log a Feed":
    st.title("Log Isabella's Feed")
    st.write("Fill out the form below. Data automatically syncs to the Google Sheet.")
    
    # The specific Google Form src link without extra spaces or line breaks
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdDpKJUHwJrlvpogw00KApeINNN_FucbYxdWu4n40RCOjeqtg/viewform?embedded=true"
    
    # Embed the form using an iframe
    components.iframe(form_url, height=968, scrolling=True)

# -----------------------------------------
# PAGE 2: DASHBOARD & LLM SUMMARIES
# -----------------------------------------
elif page == "📊 Development Dashboard":
    st.title("Isabella's Development Dashboard")
    
    # Connect to the Google Sheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # The cleaned Google Sheet URL without ?gid tracking tags
    sheet_url = "https://docs.google.com/spreadsheets/d/1hPtZ-gEO0uguGBA_y8_DciILJNdL7RajMeoEy6bRIZY/edit"
    
    # Read the raw data and the LLM summaries, caching for 10 minutes
    raw_data = conn.read(spreadsheet=sheet_url, worksheet="Form Responses 1", ttl="10m")
    llm_data = conn.read(spreadsheet=sheet_url, worksheet="LLM_Summaries", ttl="10m")
    
    # Clean the date and generate a 'Week' column for filtering
    raw_data['Date'] = pd.to_datetime(raw_data['Date'])
    raw_data['Week'] = raw_data['Date'].dt.isocalendar().week
    
    # Sidebar Filters
    week_list = raw_data['Week'].dropna().unique()
    
    if len(week_list) > 0:
        selected_week = st.sidebar.selectbox("Select Week to View", week_list)
        weekly_feeds = raw_data[raw_data['Week'] == selected_week]
        
        # LLM Summary Section
        st.subheader(f"Development Insights: Week {selected_week}")
        try:
            summary_text = llm_data[llm_data['Week'] == selected_week]['Summary'].iloc[0]
            st.info(summary_text)
        except (IndexError, KeyError):
            st.info("No LLM summary has been generated for this week yet.")
        
        # Key Metrics Layout
        st.subheader("Weekly Snapshot")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Feeds", len(weekly_feeds))
        
        # Handle the math safely in case the week has no numeric data yet
        avg_intake = round(weekly_feeds['Amount'].mean(), 1) if not weekly_feeds['Amount'].empty else 0
        total_intake = weekly_feeds['Amount'].sum() if not weekly_feeds['Amount'].empty else 0
        
        col2.metric("Avg Intake per Feed (ml)", avg_intake)
        col3.metric("Total Intake (ml)", total_intake)
        
        # Visual Trends: Breast Milk vs. Formula
        st.subheader("Intake Trends: Breast Milk vs. Formula")
        
        if not weekly_feeds.empty:
            # Group the data by the exact Date and Type, summing the Amount
            intake_by_type = weekly_feeds.groupby([weekly_feeds['Date'].dt.date, 'Type'])['Amount'].sum().reset_index()
            
            # Pivot so Date is the X-axis, and Type provides the distinct bars
            trend_data = intake_by_type.pivot(index='Date', columns='Type', values='Amount').fillna(0)
            
            # Render the chart
            st.bar_chart(trend_data)
        else:
            st.write("No feeding data logged for this timeframe.")
    else:
        st.warning("No data found in the spreadsheet yet. Submit a test response through the form!")
