#!/usr/bin/env python3
"""
Streamlit web interface for the Calendar Helper application.
"""

import streamlit as st
import datetime
import pandas as pd
import os
import sys
from dateutil import tz

# Add the current directory to the path so we can import the calendar_helper module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from calendar_helper
from calendar_helper import (
    get_calendar_service, 
    get_all_events, 
    find_available_slots, 
    format_time_slot,
    CET
)

# Import config values
try:
    import config
    DEFAULT_WORK_START_HOUR = config.WORK_START_HOUR
    DEFAULT_WORK_END_HOUR = config.WORK_END_HOUR
    DEFAULT_MEETING_DURATION = config.MEETING_DURATION
    DEFAULT_NUM_SLOTS = config.NUM_SLOTS
    DEFAULT_DAYS_AHEAD = config.DAYS_AHEAD
    DEFAULT_CALENDAR_ID = config.CALENDAR_ID
    DEFAULT_COLLEAGUE_CALENDARS = config.COLLEAGUE_CALENDARS
    DEFAULT_PREFERRED_DAYS = config.PREFERRED_DAYS
    DEFAULT_PREFERRED_HOURS = config.PREFERRED_HOURS
except ImportError:
    # Default settings if config.py is not found
    DEFAULT_WORK_START_HOUR = 9  # 9 AM
    DEFAULT_WORK_END_HOUR = 17   # 5 PM
    DEFAULT_MEETING_DURATION = 30
    DEFAULT_NUM_SLOTS = 3
    DEFAULT_DAYS_AHEAD = 7
    DEFAULT_CALENDAR_ID = 'primary'
    DEFAULT_COLLEAGUE_CALENDARS = []
    DEFAULT_PREFERRED_DAYS = []
    DEFAULT_PREFERRED_HOURS = []

# Set page config
st.set_page_config(
    page_title="Calendar Helper",
    page_icon="📅",
    layout="wide",
)

# Title and description
st.title("📅 Calendar Helper")
st.markdown("Find available times for meetings based on your Google Calendar.")

# Sidebar for settings
st.sidebar.header("⚙️ Settings")

# Meeting settings
st.sidebar.subheader("Meeting Settings")
meeting_duration = st.sidebar.slider(
    "Meeting Duration (minutes)", 
    min_value=15, 
    max_value=120, 
    value=DEFAULT_MEETING_DURATION,
    step=15
)

num_slots = st.sidebar.slider(
    "Number of Slots to Show", 
    min_value=1, 
    max_value=10, 
    value=DEFAULT_NUM_SLOTS
)

days_ahead = st.sidebar.slider(
    "Days to Look Ahead", 
    min_value=1, 
    max_value=30, 
    value=DEFAULT_DAYS_AHEAD
)

# Working hours settings
st.sidebar.subheader("Working Hours")
work_start_hour = st.sidebar.slider(
    "Work Start Hour", 
    min_value=0, 
    max_value=23, 
    value=DEFAULT_WORK_START_HOUR
)

work_end_hour = st.sidebar.slider(
    "Work End Hour", 
    min_value=work_start_hour + 1, 
    max_value=24, 
    value=DEFAULT_WORK_END_HOUR
)

# Preferred days settings
st.sidebar.subheader("Preferred Days")
day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
preferred_days = []

for i, day in enumerate(day_names):
    if i in DEFAULT_PREFERRED_DAYS:
        default = True
    else:
        default = False
    if st.sidebar.checkbox(day, value=default):
        preferred_days.append(i)

# Preferred hours settings
st.sidebar.subheader("Preferred Hours")
preferred_hours = []
for hour in range(work_start_hour, work_end_hour):
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "AM" if hour < 12 else "PM"
    if hour in DEFAULT_PREFERRED_HOURS:
        default = True
    else:
        default = False
    if st.sidebar.checkbox(f"{hour_12} {am_pm} ({hour}:00)", value=default):
        preferred_hours.append(hour)

# Colleague calendars
st.sidebar.subheader("Colleague Calendars")
colleague_text = st.sidebar.text_area(
    "Add colleague emails (one per line)",
    value="\n".join(DEFAULT_COLLEAGUE_CALENDARS)
)
colleague_calendars = [email.strip() for email in colleague_text.split("\n") if email.strip()]

# Main content
tab1, tab2 = st.tabs(["Find Available Times", "Instructions"])

with tab1:
    st.subheader("Find Available Meeting Times")
    
    # Create a placeholder for the results
    result_placeholder = st.empty()
    
    if st.button("Find Available Times", type="primary"):
        with st.spinner("Authenticating with Google Calendar..."):
            try:
                service = get_calendar_service()
                
                # Update the placeholder with a status message
                result_placeholder.info("Connected to Google Calendar. Fetching events...")
                
                # Define time range in UTC
                now = datetime.datetime.now(datetime.timezone.utc)
                end_date = now + datetime.timedelta(days=days_ahead)
                
                # Fetch events
                events = get_all_events(service, now, end_date)
                
                if not events:
                    result_placeholder.info(f"No upcoming events found in the next {days_ahead} days!")
                else:
                    # Update status
                    result_placeholder.info(f"Found {len(events)} events. Analyzing schedules to find available meeting times...")
                    
                    # Override global variables with the UI settings
                    import calendar_helper
                    calendar_helper.WORK_START_HOUR = work_start_hour
                    calendar_helper.WORK_END_HOUR = work_end_hour
                    calendar_helper.MEETING_DURATION = meeting_duration
                    calendar_helper.NUM_SLOTS = num_slots
                    calendar_helper.PREFERRED_DAYS = preferred_days
                    calendar_helper.PREFERRED_HOURS = preferred_hours
                    calendar_helper.COLLEAGUE_CALENDARS = colleague_calendars
                    
                    # Find available slots
                    available_slots = find_available_slots(events, now, end_date, num_slots)
                    
                    if available_slots:
                        # Clear the placeholder
                        result_placeholder.empty()
                        
                        # Display results
                        st.success(f"Found {len(available_slots)} available times for your {meeting_duration}-minute meeting!")
                        
                        # Show which colleagues were considered
                        if colleague_calendars:
                            st.info(f"Colleagues considered ({len(colleague_calendars)}):")
                            for colleague in colleague_calendars:
                                st.markdown(f"- {colleague}")
                        else:
                            st.info("No colleague calendars were considered. Add colleagues in the sidebar to find mutually available times.")
                        
                        # Display as bulleted list instead of DataFrame
                        st.markdown("### Available Meeting Times:")
                        for i, slot in enumerate(available_slots, 1):
                            # Calculate end time
                            end_slot = slot + datetime.timedelta(minutes=meeting_duration)
                            
                            # Format times
                            slot_str = format_time_slot(slot)
                            timezone_label = "CET" if slot.dst().total_seconds() == 0 else "CEST"
                            
                            # Format end time
                            end_time = end_slot.strftime("%-I:%M %p")
                            
                            # Display with both start and end times
                            st.markdown(f"- {slot_str} - {end_time} {timezone_label}")
                        
                        # Add ICS download functionality in the future
                        st.info("Tip: Copy these times to your email or calendar invitation.")
                    else:
                        result_placeholder.warning(f"No available {meeting_duration}-minute slots found in your working hours for the next {days_ahead} days. Try adjusting your settings.")
            
            except Exception as e:
                result_placeholder.error(f"Error: {str(e)}")
                st.error("Make sure you have credentials.json file in the same directory and proper Google Calendar API access.")

with tab2:
    st.subheader("Instructions")
    
    st.markdown("""
    ### Setup Requirements
    
    1. **Create a Google Cloud Project**:
       - Go to the [Google Cloud Console](https://console.cloud.google.com/)
       - Create a new project
       - Enable the Google Calendar API
    
    2. **Create OAuth 2.0 Credentials**:
       - Go to "APIs & Services" > "Credentials"
       - Click "Create Credentials" > "OAuth client ID"
       - Select "Desktop app" as the application type
       - Download the JSON file and rename it to `credentials.json`
       - Place it in the same directory as this application
    
    3. **Configure Settings**:
       - Use the sidebar to adjust your preferences
       - Add colleague emails to find mutually available times
    
    4. **Find Available Times**:
       - Click the "Find Available Times" button
       - The first time you run it, you'll need to authorize access to your Google Calendar
    
    ### Features
    
    - Analyzes your Google Calendar for the specified days ahead
    - Considers your working hours and preferences
    - Finds times that work for you and your colleagues
    - Suggests optimal meeting slots based on preferences
    
    ### Tips
    
    - If no slots are found, try:
      - Extending the days to look ahead
      - Broadening your working hours
      - Reducing the meeting duration
      - Adjusting preferred days and hours
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Calendar Helper App v1.0")
st.sidebar.caption("Made with Streamlit and Google Calendar API") 