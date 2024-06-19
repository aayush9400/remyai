from flask import redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os

from utils import ScheduleUtils, GoogleUtils
from utils import Utils as ut

CLIENT_SECRETS_FILE = r"C:\Users\Aayush\OneDrive\Desktop\projects\remy.ai\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://localhost:5000/callback"

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

def initialize_routes(app):

    @app.route('/')
    def index():
        if 'credentials' in session:
            credentials = ut.credentials_from_dict(session['credentials'])
            service = build('calendar', 'v3', credentials=credentials)
            google_utils = GoogleUtils(service)
            events = google_utils.get_all_events(google_utils.get_user_timezone())
            user_info = session.get('user', {})
            return ut.render_homepage(events, user_info)
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
        session['credentials'] = ut.credentials_to_dict(credentials)

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

        credentials = ut.credentials_from_dict(session['credentials'])
        service = build('calendar', 'v3', credentials=credentials)
        google_utils = GoogleUtils(service)
        user_timezone = google_utils.get_user_timezone()
        meal_calendar_id = google_utils.get_or_create_meal_calendar()
        events = google_utils.get_all_events(user_timezone)

        schedule_utils = ScheduleUtils()

        with open(r'C:\Users\Aayush\OneDrive\Desktop\projects\remy.ai\plan.json', 'r') as f:
            user_meal_plan = json.load(f)

        if not events:
            schedule = schedule_utils.create_schedule_with_default_times(user_meal_plan, user_timezone)
        else:
            free_slots = schedule_utils.get_free_slots(events, user_timezone)
            schedule = schedule_utils.create_schedule(free_slots, user_meal_plan, user_timezone)
        
        google_utils.add_meal_times_to_calendar(schedule, meal_calendar_id, user_timezone)

        start_of_week, end_of_week = schedule_utils.get_current_week_range(user_timezone)
        events_result = service.events().list(calendarId=meal_calendar_id, timeMin=start_of_week.isoformat(),
                                              timeMax=end_of_week.isoformat(), singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        user_info = session.get('user', {})
        return ut.render_calendar(events, user_info)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))
