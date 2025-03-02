"""
Configuration settings for the Calendar Helper.
Modify these settings to customize the behavior of the script.
"""

# Working hours (24-hour format)
WORK_START_HOUR = 9  # 9 AM
WORK_END_HOUR = 17   # 5 PM

# Meeting duration in minutes
MEETING_DURATION = 30

# Number of meeting slots to suggest
NUM_SLOTS = 3

# Days to look ahead for available slots
DAYS_AHEAD = 7

# Calendar ID to use (default: 'primary' for your main calendar)
CALENDAR_ID = 'primary'

# Colleague calendars to consider (list of email addresses)
# Example: ['colleague1@example.com', 'colleague2@example.com']
COLLEAGUE_CALENDARS = []

# Preferred days of the week (0 = Monday, 6 = Sunday)
# Leave empty to consider all days
# Example: [0, 1, 2, 3, 4] for weekdays only
PREFERRED_DAYS = [0, 1, 2, 3, 4]

# Preferred time slots (in hours, 24-hour format)
# Leave empty to consider all slots within working hours
# Example: [9, 13, 16] to prefer 9 AM, 1 PM, and 4 PM
PREFERRED_HOURS = [10, 11, 12, 13, 14, 15, 16, 17] 