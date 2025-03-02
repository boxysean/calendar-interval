# Calendar Helper

A Python application that connects to your Google Calendar and suggests available meeting times.

## Features

- Analyzes your Google Calendar for the next 7 days (customizable)
- Considers your working hours (default: 9 AM to 5 PM)
- Suggests 3 optimal 30-minute meeting slots
- Avoids scheduling during existing events
- Customizable preferences for days and times
- Prioritizes slots based on a scoring system
- Checks availability against colleagues' calendars
- Web interface built with Streamlit for easy interaction

## Setup

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as the application type
4. Give it a name (e.g., "Calendar Helper")
5. Click "Create"
6. Download the JSON file by clicking the download icon

### 3. Set Up the Application

1. Rename the downloaded JSON file to `credentials.json`
2. Place it in the same directory as the script

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

```bash
python calendar_helper.py
```

The first time you run the script, it will open a browser window asking you to authorize the application to access your Google Calendar. After authorization, the script will suggest available meeting slots based on your calendar.

### Web Interface (Recommended)

```bash
streamlit run app.py
```

This launches a web interface where you can:
- Adjust all settings through an interactive UI
- Add colleague calendars
- View results in a nicely formatted table
- Read setup instructions

## Customization

You can customize the application's behavior by editing the `config.py` file:

- `WORK_START_HOUR` and `WORK_END_HOUR`: Define your working hours
- `MEETING_DURATION`: Set the desired meeting length in minutes
- `NUM_SLOTS`: Number of meeting slots to suggest
- `DAYS_AHEAD`: How many days to look ahead
- `CALENDAR_ID`: Which calendar to use (default: 'primary')
- `COLLEAGUE_CALENDARS`: List of colleague email addresses to check availability against
- `PREFERRED_DAYS`: Specify preferred days of the week (0 = Monday, 6 = Sunday)
- `PREFERRED_HOURS`: Specify preferred hours of the day

## Example Output (Command Line)

```
Fetching your calendar events...
Found 12 events in the next 7 days.

Analyzing your schedule to find available meeting times...

Here are 3 suggested times for your 30-minute meeting (Central European Time):
1. Monday 10 June at 11:00 AM (CEST)
2. Tuesday 11 June at 2:30 PM (CEST)
3. Thursday 13 June at 10:00 AM (CEST)
```

## Troubleshooting

- If you encounter authentication issues, delete the `token.pickle` file and run the script again
- If no slots are found, try adjusting the working hours or increasing the number of days to look ahead
- For any other issues, check the Google Calendar API documentation 