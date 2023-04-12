import os
import sys
import json
import time
import datetime
import fitbit
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

# Set your Fitbit client ID and secret from your registered Fitbit App
FITBIT_CLIENT_ID = 'YOUR_FITBIT_CLIENT_ID'
FITBIT_CLIENT_SECRET = 'YOUR_FITBIT_CLIENT_SECRET'
FITBIT_REDIRECT_URI = 'http://127.0.0.1:8080/'

# Your OAuth 2.0 client ID and secret for Google API
GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID'
GOOGLE_CLIENT_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'
GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8080/'

# Google API Scope
GOOGLE_SCOPE = ['https://www.googleapis.com/auth/calendar.events']

# Sleep threshold in minutes
SLEEP_THRESHOLD = 1

# Main function to handle the overall process
def main():
    # Authenticate Fitbit and Google APIs
    fitbit_auth = fitbit_authenticate()
    google_auth = google_authenticate()

    # Keep checking for user sleep status
    while True:
        # Check if the user is asleep
        is_asleep = check_user_asleep(fitbit_auth)

        # If the user is asleep, create a Google Calendar event as an alarm
        if is_asleep:
            create_google_calendar_event(google_auth)
            break

        # Wait for 5 minutes before checking again
        time.sleep(5 * 60)

# Authenticate with the Fitbit API
def fitbit_authenticate():
    fitbit_auth = fitbit.FitbitOauth2Client(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, FITBIT_REDIRECT_URI)

    # Generate Fitbit authorization URL
    url, _ = fitbit_auth.authorize_token_url()
    print('Visit this URL to authorize the app:', url)

    # Prompt the user to enter the redirected URL
    redirected_uri = input('Enter the full redirected URL after you have authorized the app: ')

    # Fetch the access token using the redirected URI
    token = fitbit_auth.fetch_access_token(redirected_uri)
    return fitbit_auth

# Check if the user is asleep using the Fitbit API
def check_user_asleep(fitbit_auth):
    client = fitbit.Fitbit(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, oauth2=True, access_token=fitbit_auth.token['access_token'])
    now = datetime.datetime.now().strftime('%Y-%m-%d')

    # Get the user's sleep data for the current day
    sleep_data = client.get_sleep(now)
    
    # If total sleep time is above the threshold, the user is considered asleep
    if sleep_data['summary']['totalMinutesAsleep'] >= SLEEP_THRESHOLD:
        return True

    return False

# Authenticate with the Google API
def google_authenticate():
    flow = InstalledAppFlow.from_client_config({
        'installed': {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uris': [GOOGLE_REDIRECT_URI],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://accounts.google.com/o/oauth2/token',
        }
    }, scopes=GOOGLE_SCOPE)

    # Run a local server to get the authorization code
    credentials = flow.run_local_server(port=0)
    return credentials

# Create a Google Calendar event as an alarm/notification
def create_google_calendar_event(credentials):
    try:
        # Build a Google Calendar API service
        service = build('calendar', 'v3', credentials=credentials)

        # Calculate the alarm time, 90 minutes after the current time
        alarm_time = datetime.datetime.now() + datetime.timedelta(minutes=90)
        
        # Create a calendar event with a popup reminder at the start time
        event = {
            'summary': 'Sleep Alarm',
            'start': {
                'dateTime': alarm_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': (alarm_time + datetime.timedelta(minutes=1)).isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 0},
                ],
            },
        }

        # Insert the event into the user's primary calendar
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        # Print a confirmation message
        print(f"Alarm set for {event['start']['dateTime']}")

    except HttpError as error:
        print(f"An error occurred: {error}")
        sys.exit(1)

# Run the main function
if __name__ == '__main__':
    main()

