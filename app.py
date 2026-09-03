import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai

# Set up the app layout and title
st.set_page_config(page_title="Isabella's Tracker", layout="wide")

# Configure the API key from Streamlit secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Create Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📝 Log a Feed", "📊 Development Dashboard"])

# -----------------------------------------
# PAGE 1: GOOGLE FORM EMBEDDING
# -----------------------------------------
if page == "📝 Log a Feed":
    st.title("Log Isabella's Feed")
    st.write("Fill out the form below. Data automatically syncs to the Google Sheet.")
    
    # Embed the form using an iframe
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdDpKJUHwJrlvpogw00KApeINNN_FucbYxdWu4n40RCOjeqtg/viewform?embedded=true"
    components.iframe(form_url, height=968, scrolling=True)

# -----------------------------------------
# PAGE 2: DASHBOARD & LLM SUMMARIES
# -----------------------------------------
elif page == "📊 Development Dashboard":
    st.title("Isabella's Development Dashboard")
    
    # Connect to the Google Sheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    sheet_url = "https://docs.google.com/spreadsheets/d/1hPtZ-gEO0uguGBA_y8_DciILJNdL7RajMeoEy6bRIZY/edit"
    
    # Read the raw data
    raw_data = conn.read(spreadsheet=sheet_url, worksheet="Form Responses 1", ttl="10m")
    llm_data = conn.read(spreadsheet=sheet_url, worksheet="LLM_Summaries", ttl="10m")
    
    # 1. Process the ENTIRE dataset for accurate moving averages
    raw_data['Date'] = pd.to_datetime(raw_data['Date'])
    
    # Group by Date and Type
    daily_pivot = raw_data.groupby([raw_data['Date'].dt.date, 'Type'])['Amount'].sum().reset_index()
    daily_stats = daily_pivot.pivot(index='Date', columns='Type', values='Amount').fillna(0)
    
    # Ensure both columns exist safely
    if 'Breast Milk' not in daily_stats.columns: daily_stats['Breast Milk'] = 0
    if 'Formula' not in daily_stats.columns: daily_stats['Formula'] = 0
    
    # 2. Calculate New Metrics
    daily_stats['Total Volume'] = daily_stats['Breast Milk'] + daily_stats['Formula']
    
    # Calculate BM %, handling division by zero
    daily_stats['BM %'] = (daily_stats['Breast Milk'] / daily_stats['Total Volume']) * 100
    daily_stats['BM %'] = daily_stats['BM %'].fillna(0)
    
    # Calculate 3-Day Moving Averages
    daily_stats['3-Day Avg Volume'] = daily_stats['Total Volume'].rolling(window=3, min_periods=1).mean()
    daily_stats['3-Day Avg BM %'] = daily_stats['BM %'].rolling(window=3, min_periods=1).mean()
    
    # Reattach Week number for filtering
    daily_stats['Week'] = pd.to_datetime(daily_stats.index).isocalendar().week
    
    # 3. Sidebar Filters
    week_list = daily_stats['Week'].dropna().unique()
    
    if len(week_list) > 0:
        selected_week = st.sidebar.selectbox("Select Week to View", week_list)
        
        # Filter down to the selected week for display
        weekly_stats = daily_stats[daily_stats['Week'] == selected_week]
          
        if not weekly_stats.empty:
            # 4. Calculate Exact Developmental Ages
            latest_day = weekly_stats.iloc[-1]
            current_reference_date = latest_day.name
            
            DOB = pd.to_datetime("2026-07-23").date()
            DUE_DATE = DOB + pd.Timedelta(days=23) # 40 weeks - 36w5d = 23 days premature
            
            chronological_days = (current_reference_date - DOB).days
            chronological_weeks = chronological_days // 7
            
            corrected_days = (current_reference_date - DUE_DATE).days
            corrected_weeks = corrected_days // 7 if corrected_days >= 0 else 0
            
            # 5. Key Metrics Layout
            st.subheader("Current Snapshot (Latest Day in Week)")
            st.write(f"**Chronological Age:** {chronological_weeks} weeks | **Corrected Age:** {corrected_weeks} weeks")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Daily Volume", f"{int(latest_day['Total Volume'])} ml")
            col2.metric("3-Day Avg Volume", f"{int(latest_day['3-Day Avg Volume'])} ml")
            col3.metric("3-Day Avg Breast Milk", f"{int(latest_day['3-Day Avg BM %'])}%")
            
            st.subheader("Daily Intake Breakdown")
            # Keeping only the bar chart for the raw BM vs Formula split
            st.bar_chart(weekly_stats[['Breast Milk', 'Formula']])
            
            # 6. LLM Summary Section
            st.subheader(f"Development Insights: Week {selected_week}")
            try:
                summary_text = llm_data[llm_data['Week'] == selected_week]['Summary'].iloc[0]
                st.info(summary_text)
            except (IndexError, KeyError):
                st.info("No LLM summary has been generated for this week yet.")

            # On-Demand LLM Generation and Saving
            if st.button(f"Generate & Save Insight for Week {selected_week}"):
                
                if not user_api_key:
                    st.error("Please paste your Gemini API key in the sidebar first.")
                else:
                    # Configure using the text input field
                    genai.configure(api_key=user_api_key)
                    
                    with st.spinner("Analyzing developmental data & writing to Google Sheets..."):
                        
                        prompt = f"""
                        Isabella was born prematurely at 36 weeks and 5 days. 
                        Her chronological age is {chronological_weeks} weeks.
                        Her corrected age is {corrected_weeks} weeks.
                        
                        This week, she averaged {int(latest_day['3-Day Avg Volume'])} ml of milk per day.
                        Her intake is {int(latest_day['3-Day Avg BM %'])}% breast milk.
                        
                        Analyze this feeding data. Correlate it with standard developmental milestones, 
                        physical growth spurts, and cognitive changes, explicitly comparing expectations 
                        for her chronological age versus her corrected premature age. 
                        Keep the tone supportive and informative.
                        """
                        
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt)
                        new_summary = response.text
                        
                        # Save to Google Sheets
                        current_llm_df = conn.read(spreadsheet=sheet_url, worksheet="LLM_Summaries", ttl=0)
                        
                        if not current_llm_df.empty and 'Week' in current_llm_df.columns:
                            current_llm_df = current_llm_df[current_llm_df['Week'] != selected_week]
                            
                        new_row = pd.DataFrame([{"Week": selected_week, "Summary": new_summary}])
                        updated_llm_df = pd.concat([current_llm_df, new_row], ignore_index=True)
                        
                        conn.update(worksheet="LLM_Summaries", data=updated_llm_df)
                        st.cache_data.clear()
                        
                        st.success("Analysis Complete & Saved permanently to your Google Sheet!")
                        st.write(new_summary)
