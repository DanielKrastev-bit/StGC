import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Use run_console() for CLI environments
            creds = flow.run_console()
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def delete_events(service, calendar_id):
    # Retrieve all events from the calendar
    page_token = None
    while True:
        events_result = service.events().list(calendarId=calendar_id, pageToken=page_token, singleEvents=True).execute()
        events = events_result.get('items', [])

        if not events:
            print("No more events to delete.")
            break

        for event in events:
            if 'description' in event and 'Created by StGC' in event['description']:
                # Uncomment to see which events are being deleted
                # print(f'Deleting event: {event["summary"]} at {event["start"].get("dateTime", event["start"].get("date"))}')
                service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()

        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

def main():
    service = authenticate_google_calendar()
    calendar_id = 'b8779324f29d709c197598ff6c362082049204000bdbceb809d85101f91d578a@group.calendar.google.com'
    delete_events(service, calendar_id)

if __name__ == '__main__':
    main()
