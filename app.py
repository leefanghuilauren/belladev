import streamlit as st
import streamlit.components.v1 as components

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
    
    # Your specific Google Form src link
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdDpKJUHwJrlvpogw00KApeINNN_FucbYxdWu4n40RCOjeqtg/viewform?embedded=true"
    
    # Embed the form using an iframe, matching the height from your embed code
    components.iframe(form_url, height=968, scrolling=True)

# -----------------------------------------
# PAGE 2: DASHBOARD & LLM SUMMARIES
# -----------------------------------------
elif page == "📊 Development Dashboard":
    st.title("Isabella's Development Dashboard")
    
    # 1. Connect to the Google Sheet (Requires secrets configured in Streamlit)
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Read the raw data and the LLM summaries, caching for 10 minutes
    raw_data = conn.read(worksheet="Form Responses 1", ttl="10m")
    llm_data = conn.read(worksheet="LLM_Summaries", ttl="10m")
    
    # 2. Sidebar Filters
    # Assuming your data has a 'Week' column 
    week_list = raw_data['Week'].dropna().unique()
    selected_week = st.sidebar.selectbox("Select Week to View", week_list)
    
    # Filter data for the selected week
    weekly_feeds = raw_data[raw_data['Week'] == selected_week]
    
    # 3. LLM Summary Section
    st.subheader(f"Development Insights: Week {selected_week}")
    # Extract the text summary for this specific week
    summary_text = llm_data[llm_data['Week'] == selected_week]['Summary'].iloc[0]
    st.info(summary_text)
    
    # 4. Key Metrics Layout
    st.subheader("Weekly Snapshot")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Feeds", len(weekly_feeds))
    col2.metric("Avg Ounces per Feed", round(weekly_feeds['Ounces'].mean(), 1))
    col3.metric("Total Ounces", weekly_feeds['Ounces'].sum())
    
    # 5. Visual Trends
    st.subheader("Daily Intake Trend")
    # Group by date for a clean chart
    daily_intake = weekly_feeds.groupby('Timestamp')['Ounces'].sum()
    st.bar_chart(daily_intake)
