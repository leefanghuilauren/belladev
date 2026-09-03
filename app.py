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
    
    # Placeholder for where you will connect the Google Sheet
    # conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.subheader("Weekly LLM Insights")
    # Fetch and display the markdown summaries here
    st.info("Week 12: Isabella is showing increased head control and transitioning to...")
    
    st.subheader("Feeding Trends")
    # Fetch raw data and display charts here
    # st.bar_chart(feeding_data)
