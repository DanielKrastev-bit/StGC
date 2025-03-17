import os
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
calendar_id = 'b8779324f29d709c197598ff6c362082049204000bdbceb809d85101f91d578a@group.calendar.google.com'
COLORS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def clear_existing_events(service, calendar_id):
    events = []
    page_token = None
    while True:
        events_result = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        events.extend(events_result.get('items', []))
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

    print(f"Found {len(events)} events to delete.")
    for event in events:
        try:
            event_id = event['id']
            summary = event.get('summary', 'No summary')
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            print(f"Deleted event: {summary}")
        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")

def create_event(service, date, start_time, end_time, summary, color_id):
    event = {
        'summary': summary,
        'start': {
            'dateTime': f'{date}T{start_time}:00',
            'timeZone': 'Europe/Sofia',
        },
        'end': {
            'dateTime': f'{date}T{end_time}:00',
            'timeZone': 'Europe/Sofia',
        },
        'colorId': color_id,
        'description': 'Created by StGC',
    }
    service.events().insert(calendarId=calendar_id, body=event).execute()

def extract_date(line):
    match = re.search(r'Date: (\d{2}\.\d{2}\.\d{4})', line)
    if match:
        return datetime.strptime(match.group(1), '%d.%m.%Y').strftime('%Y-%m-%d')
    return None

def extract_time_range(line):
    match = re.search(r'Time range: (\d{2}:\d{2}) - (\d{2}:\d{2})', line)
    if match:
        return match.group(1), match.group(2)
    return None

def parse_class_line(line):
    """
    Parses a line like:
    "Class: 1. Промишлена електроника (ИУЧ - СПП) Митко В. Димитров 81 (Приземен 7)"
    Returns a tuple: (class_number, cleaned_title).
    If no leading number is found (like in vacation entries) returns (None, full_text).
    """
    content = line[len("Class: "):].strip()
    m = re.match(r'(\d+)\.\s*(.+)', content)
    if m:
        number = m.group(1)
        title_full = m.group(2).strip()
        # Remove trailing parentheses block (typically room info)
        title_clean = re.sub(r'\s*\([^)]*\)\s*$', '', title_full).strip()
        # Optionally, remove an ellipsis block if present
        title_clean = re.sub(r'\s*\([^)]*…[^)]*\)', '', title_clean).strip()
        return number, title_clean
    return None, content

def get_color_for_class(title, class_color_map):
    # For free day/vacation, force gray (color id "8")
    if "свободен час" in title.lower() or "ваканция" in title.lower():
        return "8"
    if title not in class_color_map:
        color_index = len(class_color_map)
        # Skip gray (index 7) if needed
        if color_index >= 7:
            color_index += 1
        class_color_map[title] = COLORS[color_index % len(COLORS)]
    return class_color_map[title]

def process_day(service, date, classes, class_color_map):
    """
    Groups consecutive classes with the same title (if continuous in time)
    and creates one event for each group. The summary uses the class numbers.
    """
    if not classes:
        return

    groups = []
    current_group = {
        'numbers': [],
        'title': None,
        'start': None,
        'end': None
    }
    for cls in classes:
        if current_group['title'] is None:
            current_group['numbers'] = [cls['number']] if cls['number'] else []
            current_group['title'] = cls['title']
            current_group['start'] = cls['start']
            current_group['end'] = cls['end']
        else:
            # Check if same title and continuous in time
            if cls['title'] == current_group['title'] and cls['start'] == current_group['end']:
                if cls['number']:
                    current_group['numbers'].append(cls['number'])
                current_group['end'] = cls['end']
            else:
                groups.append(current_group)
                current_group = {
                    'numbers': [cls['number']] if cls['number'] else [],
                    'title': cls['title'],
                    'start': cls['start'],
                    'end': cls['end']
                }
    if current_group['title'] is not None:
        groups.append(current_group)

    # Create events for each group
    for group in groups:
        if group['numbers']:
            if len(group['numbers']) == 1:
                summary = f"{group['numbers'][0]} {group['title']}"
            else:
                summary = f"{group['numbers'][0]}-{group['numbers'][-1]} {group['title']}"
        else:
            summary = group['title']
        color_id = get_color_for_class(group['title'], class_color_map)
        create_event(service, date, group['start'], group['end'], summary, color_id)

def next_workday(date_obj):
    """Returns the next work day (skipping Saturday and Sunday)."""
    next_day = date_obj + timedelta(days=1)
    while next_day.weekday() >= 5:  # Saturday=5, Sunday=6
        next_day += timedelta(days=1)
    return next_day

def get_workdays(start_date_str, end_date_str):
    """
    Returns a list of workday dates (as strings in YYYY-MM-DD format) 
    between start_date (exclusive) and end_date (exclusive).
    """
    workdays = []
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current = next_workday(start_date)
    while current < end_date:
        if current.weekday() < 5:
            workdays.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return workdays

def main():
    service = authenticate_google_calendar()
    clear_existing_events(service, calendar_id)

    with open('schedule.html', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    current_date = None           # Last valid (school) day
    last_valid_date = None        # For vacation calculation
    daily_classes = []            # Normal classes for a valid day
    class_color_map = {}
    current_class = None
    in_vacation_block = False
    vacation_event = None         # Dict with keys: title, start, end

    for line in lines:
        line = line.strip()
        if line.startswith("Date:"):
            new_date = extract_date(line)
            if new_date is not None:
                # If we are leaving a vacation block, create vacation events on workdays
                if in_vacation_block and vacation_event and last_valid_date:
                    workdays = get_workdays(last_valid_date, new_date)
                    print(f"Creating vacation events for workdays: {workdays}")
                    for d in workdays:
                        # Vacation events always use gray ("8")
                        create_event(service, d, vacation_event['start'], vacation_event['end'], vacation_event['title'], "8")
                    in_vacation_block = False
                    vacation_event = None
                # Before switching to new date, process normal classes of previous valid day.
                if current_date and daily_classes:
                    process_day(service, current_date, daily_classes, class_color_map)
                current_date = new_date
                last_valid_date = new_date
                daily_classes = []
            else:
                # "Date: None" indicates a vacation/free block.
                in_vacation_block = True
                # Do not update current_date; vacation events will be assigned to workdays after last_valid_date.
        elif line.startswith("Class:"):
            number, title = parse_class_line(line)
            if in_vacation_block:
                # Set vacation event details (only once)
                if vacation_event is None:
                    vacation_event = {'title': title, 'start': None, 'end': None}
            else:
                current_class = {'number': number, 'title': title, 'start': None, 'end': None}
        elif line.startswith("Time range:"):
            time_range = extract_time_range(line)
            if time_range:
                start, end = time_range
                if in_vacation_block and vacation_event is not None:
                    vacation_event['start'] = start
                    vacation_event['end'] = end
                elif not in_vacation_block and current_class is not None:
                    current_class['start'] = start
                    current_class['end'] = end
                    daily_classes.append(current_class)
                    current_class = None

    # End of file processing:
    # If still in a vacation block, schedule the vacation event for the next workday after last_valid_date.
    if in_vacation_block and vacation_event and last_valid_date:
        next_day = next_workday(datetime.strptime(last_valid_date, '%Y-%m-%d')).strftime('%Y-%m-%d')
        print(f"Creating vacation event for next workday: {next_day}")
        create_event(service, next_day, vacation_event['start'], vacation_event['end'], vacation_event['title'], "8")
    # Process any remaining normal day events if present.
    if current_date and daily_classes:
        process_day(service, current_date, daily_classes, class_color_map)

if __name__ == '__main__':
    main()
