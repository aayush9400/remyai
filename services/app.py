from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
import os
import json
import pytz
from schedule_utils import ScheduleUtils

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = r"C:\Users\Aayush\OneDrive\Desktop\projects\remy.ai\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://localhost:5000/callback"

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

@app.route('/')
def index():
    if 'credentials' in session:
        credentials = credentials_from_dict(session['credentials'])
        service = build('calendar', 'v3', credentials=credentials)
        events = get_all_events(service, get_user_timezone(service))
        user_info = session.get('user', {})
        return render_homepage(events, user_info)
    else:
        return 'Welcome! <a href="/login">Login</a>'

@app.route('/login')
def login():
    session.clear()
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session['state'] == request.args['state']:
        return redirect(url_for('index'))

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    user_info_service = build('oauth2', 'v2', credentials=credentials)
    try:
        user_info = user_info_service.userinfo().get().execute()
        session['user'] = user_info
    except HttpError as error:
        print(f"An error occurred: {error}")
        return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if 'credentials' not in session:
        return redirect('login')

    credentials = credentials_from_dict(session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)

    user_timezone = get_user_timezone(service)
    meal_calendar_id = get_or_create_meal_calendar(service)
    events = get_all_events(service, user_timezone)

    schedule_utils = ScheduleUtils()

    with open(r'C:\Users\Aayush\OneDrive\Desktop\projects\remy.ai\plan.json', 'r') as f:
        user_meal_plan = json.load(f)

    if not events:
        schedule = schedule_utils.create_schedule_with_default_times(user_meal_plan, user_timezone)
    else:
        free_slots = get_free_slots(events, user_timezone)
        schedule = schedule_utils.create_schedule(free_slots, user_meal_plan, user_timezone)
    
    add_meal_times_to_calendar(service, schedule, meal_calendar_id, user_timezone)

    start_of_week, end_of_week = get_current_week_range(user_timezone)
    events_result = service.events().list(calendarId=meal_calendar_id, timeMin=start_of_week.isoformat(),
                                          timeMax=end_of_week.isoformat(), singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    user_info = session.get('user', {})
    return render_calendar(events, user_info)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_user_timezone(service):
    user_settings = service.settings().get(setting='timezone').execute()
    return user_settings['value']

def get_or_create_meal_calendar(service):
    calendar_list = service.calendarList().list().execute()
    meal_calendar = None

    for calendar in calendar_list['items']:
        if calendar['summary'] == 'Meal Plan':
            meal_calendar = calendar
            break

    if not meal_calendar:
        meal_calendar = {
            'summary': 'Meal Plan',
            'timeZone': 'UTC'
        }
        created_calendar = service.calendars().insert(body=meal_calendar).execute()
        return created_calendar['id']
    
    return meal_calendar['id']

def get_all_events(service, user_timezone):
    events = []
    start_of_week, end_of_week = get_current_week_range(user_timezone)
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list['items']:
        events_result = service.events().list(calendarId=calendar['id'], timeMin=start_of_week.isoformat(),
                                              timeMax=end_of_week.isoformat(), singleEvents=True,
                                              orderBy='startTime', timeZone=user_timezone).execute()
        events.extend(events_result.get('items', []))
    
    for event in events:
        if 'dateTime' in event['start']:
            event['start']['dateTime'] = datetime.fromisoformat(event['start']['dateTime'])
        else:
            event['start']['dateTime'] = datetime.fromisoformat(event['start']['date']).replace(tzinfo=timezone.utc)
        
        if 'dateTime' in event['end']:
            event['end']['dateTime'] = datetime.fromisoformat(event['end']['dateTime'])
        else:
            event['end']['dateTime'] = datetime.fromisoformat(event['end']['date']).replace(tzinfo=timezone.utc) + timedelta(days=1)
    
    events.sort(key=lambda x: x['start']['dateTime'])
    return events

def get_free_slots(events, user_timezone, day_start='06:00', day_end='21:00', min_duration=30):
    free_slots = []
    tz = pytz.timezone(user_timezone)
    day_start_time = datetime.strptime(day_start, '%H:%M').time()
    day_end_time = datetime.strptime(day_end, '%H:%M').time()

    # Group events by day
    events_by_day = {}
    for event in events:
        event_date = event['start']['dateTime'].astimezone(tz).date()
        if event_date not in events_by_day:
            events_by_day[event_date] = []
        events_by_day[event_date].append(event)

    # Sort events by start time for each day
    for day in events_by_day:
        events_by_day[day].sort(key=lambda x: x['start']['dateTime'])

    # Get today's date and the start of the current week (Monday)
    today = datetime.now(tz).date()
    start_of_week = today - timedelta(days=today.weekday())  # Adjust to start from Monday

    # Process each day to find free slots
    for i in range(7):  # Process 7 days (1 week)
        current_day = start_of_week + timedelta(days=i)
        day_start_dt = tz.localize(datetime.combine(current_day, day_start_time))
        day_end_dt = tz.localize(datetime.combine(current_day, day_end_time))

        if current_day not in events_by_day:
            # No events for the day, entire day is free
            if (day_end_dt - day_start_dt).total_seconds() / 60 >= min_duration:
                free_slots.append((day_start_dt, day_end_dt))
        else:
            daily_events = events_by_day[current_day]

            # Add free slot before the first event of the day
            if (daily_events[0]['start']['dateTime'] - day_start_dt).total_seconds() / 60 >= min_duration:
                free_slots.append((day_start_dt, daily_events[0]['start']['dateTime']))

            # Add free slots between events
            for j in range(len(daily_events) - 1):
                end_current = daily_events[j]['end']['dateTime']
                start_next = daily_events[j + 1]['start']['dateTime']
                if (start_next - end_current).total_seconds() / 60 >= min_duration:
                    free_slots.append((end_current, start_next))

            # Add free slot after the last event of the day
            if (day_end_dt - daily_events[-1]['end']['dateTime']).total_seconds() / 60 >= min_duration:
                free_slots.append((daily_events[-1]['end']['dateTime'], day_end_dt))

    return free_slots

def get_current_week_range(user_timezone):
    tz = pytz.timezone(user_timezone)
    today = datetime.now(tz)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=7)
    return start_of_week, end_of_week

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def credentials_from_dict(credentials_dict):
    return Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )

def add_meal_times_to_calendar(service, schedule, calendar_id, user_timezone):
    for item in schedule:
        event = {
            'summary': f"Cook {item['dish']} for {item['meal']}",
            'start': {
                'dateTime': item['start'].isoformat(),
                'timeZone': user_timezone,
            },
            'end': {
                'dateTime': item['end'].isoformat(),
                'timeZone': user_timezone,
            },
        }
        service.events().insert(calendarId=calendar_id, body=event).execute()

def render_homepage(events, user_info):
    html = f"<h1>Welcome, {user_info.get('email', 'Unknown')}!</h1>"
    html += '<a href="/logout">Logout</a><br><br>'
    html += '<h2>Your Current Calendar</h2>'
    for event in events:
        start = event['start']['dateTime']
        end = event['end']['dateTime']
        html += f"<p>{start} - {end}: {event['summary']}</p>"
    html += '''
        <form action="/calendar" method="post">
            <button type="submit">Plan Meals</button>
        </form>
    '''
    return html

def render_calendar(events, user_info):
    html = f"<h1>Meal Plan Calendar</h1>"
    html += f"<p>Logged in as: {user_info.get('email', 'Unknown')}</p>"
    html += '<a href="/logout">Logout</a>'
    for event in events:
        start = event['start']['dateTime']
        end = event['end']['dateTime']
        html += f"<p>{start} - {end}: {event['summary']}</p>"
    return html

if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
