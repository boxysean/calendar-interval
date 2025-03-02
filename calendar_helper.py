#!/usr/bin/env python3
"""
Calendar Helper - A script to suggest available meeting times based on your Google Calendar.
"""

import os
import datetime
import pickle
from dateutil import parser
from dateutil.relativedelta import relativedelta
from dateutil import tz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Import configuration settings
try:
    import config
    WORK_START_HOUR = config.WORK_START_HOUR
    WORK_END_HOUR = config.WORK_END_HOUR
    MEETING_DURATION = config.MEETING_DURATION
    NUM_SLOTS = config.NUM_SLOTS
    DAYS_AHEAD = config.DAYS_AHEAD
    CALENDAR_ID = config.CALENDAR_ID
    COLLEAGUE_CALENDARS = config.COLLEAGUE_CALENDARS
    PREFERRED_DAYS = config.PREFERRED_DAYS
    PREFERRED_HOURS = config.PREFERRED_HOURS
except ImportError:
    # Default settings if config.py is not found
    WORK_START_HOUR = 9  # 9 AM
    WORK_END_HOUR = 17   # 5 PM
    MEETING_DURATION = 30
    NUM_SLOTS = 3
    DAYS_AHEAD = 7
    CALENDAR_ID = 'primary'
    COLLEAGUE_CALENDARS = []
    PREFERRED_DAYS = []
    PREFERRED_HOURS = []

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Define Central European Time zone
CET = tz.gettz('Europe/Berlin')  # Berlin is in Central European Time

def get_calendar_service():
    """Authenticate and create a Google Calendar service object."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_events(service, time_min, time_max, calendar_id=CALENDAR_ID):
    """Fetch events from a specific calendar within the specified time range."""
    # Ensure we're using UTC for the API request
    if time_min.tzinfo is not None:
        # Format as RFC3339 timestamp with Z suffix for UTC
        time_min_str = time_min.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        time_max_str = time_max.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        # If no timezone, assume UTC and add Z
        time_min_str = time_min.strftime('%Y-%m-%dT%H:%M:%SZ')
        time_max_str = time_max.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_str,
            timeMax=time_max_str,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        print(f"Error fetching events from calendar {calendar_id}: {str(e)}")
        return []

def get_all_events(service, time_min, time_max):
    """Fetch events from your calendar and all colleague calendars."""
    all_events = get_events(service, time_min, time_max, CALENDAR_ID)
    
    # Fetch events from colleague calendars if specified
    if COLLEAGUE_CALENDARS:
        print(f"Checking availability for {len(COLLEAGUE_CALENDARS)} colleague(s)...")
        for colleague_email in COLLEAGUE_CALENDARS:
            colleague_events = get_events(service, time_min, time_max, colleague_email)
            if colleague_events:
                print(f"  - Found {len(colleague_events)} events for {colleague_email}")
                all_events.extend(colleague_events)
            else:
                print(f"  - No events found or no access to calendar for {colleague_email}")
    
    return all_events

def is_time_available(time_slot_start, time_slot_end, events):
    """Check if a time slot conflicts with any existing events."""
    for event in events:
        # Skip events without start or end times (all-day events)
        if 'dateTime' not in event.get('start', {}) or 'dateTime' not in event.get('end', {}):
            continue
        
        # Skip events marked as "free" (transparent)
        if event.get('transparency') == 'transparent':
            continue
        
        event_start = parser.parse(event['start']['dateTime'])
        event_end = parser.parse(event['end']['dateTime'])
        
        # Ensure timezone consistency by converting to UTC if needed
        if time_slot_start.tzinfo is None and event_start.tzinfo is not None:
            time_slot_start = time_slot_start.replace(tzinfo=datetime.timezone.utc)
            time_slot_end = time_slot_end.replace(tzinfo=datetime.timezone.utc)
        elif time_slot_start.tzinfo is not None and event_start.tzinfo is None:
            event_start = event_start.replace(tzinfo=datetime.timezone.utc)
            event_end = event_end.replace(tzinfo=datetime.timezone.utc)
        
        # Check for overlap
        if (time_slot_start < event_end and time_slot_end > event_start):
            return False
    
    return True

def is_within_working_hours(time_slot):
    """Check if a time slot is within defined working hours."""
    hour = time_slot.hour
    weekday = time_slot.weekday()
    
    # Check if it's a preferred day (if specified)
    if PREFERRED_DAYS and weekday not in PREFERRED_DAYS:
        return False
    
    # Check if it's within working hours
    if not (WORK_START_HOUR <= hour < WORK_END_HOUR):
        return False
    
    # Check if it's a preferred hour (if specified)
    if PREFERRED_HOURS and hour not in PREFERRED_HOURS:
        return False
    
    return True

def calculate_slot_score(slot):
    """Calculate a score for a time slot based on preferences."""
    score = 0
    
    # Prefer slots in the middle of the day
    hour = slot.hour
    mid_day = (WORK_START_HOUR + WORK_END_HOUR) / 2
    score -= abs(hour - mid_day)  # Higher score for hours closer to mid-day
    
    # Prefer earlier days
    days_from_now = (slot.date() - datetime.datetime.now().date()).days
    score -= days_from_now * 0.5  # Slight preference for earlier days
    
    # Prefer preferred hours if specified
    if PREFERRED_HOURS and hour in PREFERRED_HOURS:
        score += 10  # Big boost for preferred hours
    
    # Prefer preferred days if specified
    if PREFERRED_DAYS and slot.weekday() in PREFERRED_DAYS:
        score += 5  # Boost for preferred days
    
    return score

def find_available_slots(events, start_date, end_date, num_slots=NUM_SLOTS):
    """Find available time slots for meetings."""
    all_available_slots = []
    
    # Ensure start_date has timezone info
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=datetime.timezone.utc)
    
    # Convert to CET for working hours calculation
    current_date = start_date.astimezone(CET)
    end_date_cet = end_date.astimezone(CET) if end_date.tzinfo else end_date.replace(tzinfo=datetime.timezone.utc).astimezone(CET)
    
    # Iterate through each day
    while current_date < end_date_cet:
        # Reset to start of day in CET
        day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Iterate through each hour of the working day
        for hour in range(WORK_START_HOUR, WORK_END_HOUR):
            # Check every 30 minutes (0 and 30)
            for minute in [0, 30]:
                # Create the potential time slot in CET
                slot_start = day_start.replace(hour=hour, minute=minute)
                
                # Skip if the slot is in the past
                now_cet = datetime.datetime.now(CET)
                if slot_start < now_cet:
                    continue
                
                # Skip if not within working hours
                if not is_within_working_hours(slot_start):
                    continue
                
                slot_end = slot_start + datetime.timedelta(minutes=MEETING_DURATION)
                
                # Convert to UTC for checking against calendar events
                slot_start_utc = slot_start.astimezone(datetime.timezone.utc)
                slot_end_utc = slot_end.astimezone(datetime.timezone.utc)
                
                # Check if the slot is available
                if is_time_available(slot_start_utc, slot_end_utc, events):
                    all_available_slots.append(slot_start)  # Store in CET
        
        # Move to the next day
        current_date = (current_date + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Sort slots by score
    scored_slots = [(slot, calculate_slot_score(slot)) for slot in all_available_slots]
    scored_slots.sort(key=lambda x: x[1], reverse=True)  # Sort by score (descending)
    
    # Get top slots based on score
    top_slots = [slot for slot, _ in scored_slots[:num_slots]]
    
    # Sort chronologically for display
    top_slots.sort()
    
    return top_slots

def format_time_slot(time_slot):
    """Format a datetime object into a human-readable string."""
    # Format: "Monday 1 January at 10:00 AM"
    return time_slot.strftime(f"%A %-d %B at %-I:%M %p")

def main():
    """Main function to run the calendar helper."""
    # Get authenticated calendar service
    service = get_calendar_service()
    
    # Define time range (next N days) in UTC
    now = datetime.datetime.now(datetime.timezone.utc)
    end_date = now + datetime.timedelta(days=DAYS_AHEAD)
    
    # Get events from your calendar and colleague calendars
    print("Fetching your calendar events...")
    events = get_all_events(service, now, end_date)
    
    if not events:
        print(f"No upcoming events found in the next {DAYS_AHEAD} days!")
    else:
        print(f"Found {len(events)} total events in the next {DAYS_AHEAD} days.")
    
    # Find available slots
    print("\nAnalyzing schedules to find available meeting times...")
    available_slots = find_available_slots(events, now, end_date)
    
    # Display results
    if available_slots:
        print(f"\nHere are {len(available_slots)} suggested times for your {MEETING_DURATION}-minute meeting (Central European Time):")
        for i, slot in enumerate(available_slots, 1):
            print(f"{i}. {format_time_slot(slot)}")
    else:
        print(f"\nNo available {MEETING_DURATION}-minute slots found in your working hours for the next {DAYS_AHEAD} days.")
        print("Consider adjusting your working hours or checking a wider time range in config.py.")

if __name__ == "__main__":
    main() 