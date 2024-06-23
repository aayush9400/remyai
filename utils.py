import pytz
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials


class ScheduleUtils:
    def __init__(self, meal_times=None):
        self.meal_times = meal_times if meal_times else {
            'breakfast': {'start': '06:00', 'end': '10:00'},
            'lunch': {'start': '11:00', 'end': '14:00'},
            'dinner': {'start': '18:00', 'end': '21:00'}
        }

        # Convert meal time ranges to datetime.time objects
        for meal, times in self.meal_times.items():
            self.meal_times[meal]['start'] = datetime.strptime(times['start'], '%H:%M').time()
            self.meal_times[meal]['end'] = datetime.strptime(times['end'], '%H:%M').time()
    
    def filter_slots_by_meal_time(self, free_slots, meal_time_range, cook_time_minutes):
        filtered_slots = []
        for slot in free_slots:
            start, end = slot
            meal_start = datetime.combine(start.date(), meal_time_range['start']).replace(tzinfo=start.tzinfo)
            meal_end = datetime.combine(start.date(), meal_time_range['end']).replace(tzinfo=start.tzinfo)
            
            # Ensure the slot is within the meal time range and has enough duration for cooking
            if start < meal_end and end > meal_start:
                # Calculate the latest possible start time for the dish
                latest_start_time = min(end, meal_end) - timedelta(minutes=cook_time_minutes)
                if latest_start_time >= max(start, meal_start):
                    filtered_slots.append((max(start, meal_start), min(end, meal_end)))
        return filtered_slots
    
    def create_schedule(self, free_slots, meal_plan, user_timezone):
        schedule = []
        tz = pytz.timezone(user_timezone)
        today = datetime.now(tz)
        start_of_week = today - timedelta(days=today.weekday())  # Monday of the current week
        used_slots = []

        for day, meals in meal_plan['week'].items():
            day_start = tz.localize(datetime.combine(start_of_week + timedelta(days=list(meal_plan['week'].keys()).index(day)), datetime.min.time()))
            day_end = tz.localize(datetime.combine(start_of_week + timedelta(days=list(meal_plan['week'].keys()).index(day)), datetime.max.time()))

            day_free_slots = [slot for slot in free_slots if day_start <= slot[0] < day_end]

            for meal, details in meals.items():
                meal_time_range = self.meal_times[meal]
                cook_time_minutes = int(details['time'].split(':')[0]) * 60 + int(details['time'].split(':')[1])
                meal_slots = self.filter_slots_by_meal_time(day_free_slots, meal_time_range, cook_time_minutes)
                
                for slot in meal_slots:
                    start, end = slot
                    duration = (end - start).seconds // 60  # Duration in minutes

                    if cook_time_minutes <= duration:
                        schedule.append({
                            'day': day,
                            'meal': meal,
                            'dish': details['dish'],
                            'start': start,
                            'end': start + timedelta(minutes=cook_time_minutes)
                        })
                        used_slots.append(slot)
                        break
        
        # Remove used slots from free_slots
        free_slots = [slot for slot in free_slots if slot not in used_slots]
        return schedule
    
    def create_schedule_with_default_times(self, meal_plan, user_timezone):
        schedule = []
        tz = pytz.timezone(user_timezone)  # Convert user timezone string to tzinfo object
        today = datetime.now(tz)
        start_of_week = today - timedelta(days=today.weekday())  # Monday of the current week
        for day, meals in meal_plan['week'].items():
            day_offset = list(meal_plan['week'].keys()).index(day)
            for meal, details in meals.items():
                start_time = self.meal_times[meal]['start']
                cook_time = int(details['time'].split(':')[0]) * 60 + int(details['time'].split(':')[1])
                start = tz.localize(datetime.combine(start_of_week + timedelta(days=day_offset), start_time))
                end = start + timedelta(minutes=cook_time)
                schedule.append({
                    'day': day,
                    'meal': meal,
                    'dish': details['dish'],
                    'start': start,
                    'end': end
                })
        return schedule
    
    def get_free_slots(self, events, user_timezone, day_start='06:00', day_end='21:00', min_duration=30):
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

    def get_current_week_range(self, user_timezone):
        tz = pytz.timezone(user_timezone)
        today = datetime.now(tz)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return start_of_week, end_of_week

class GoogleUtils():
    def __init__(self, service) -> None:
        self.service = service
        pass

    def get_user_timezone(self):
        user_settings = self.service.settings().get(setting='timezone').execute()
        return user_settings['value']

    def get_or_create_meal_calendar(self):
        calendar_list = self.service.calendarList().list().execute()
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
            created_calendar = self.service.calendars().insert(body=meal_calendar).execute()
            return created_calendar['id']
        
        return meal_calendar['id']

    def get_all_events(self, user_timezone):
        events = []
        start_of_week, end_of_week = self.get_current_week_range(user_timezone)
        calendar_list = self.service.calendarList().list().execute()
        for calendar in calendar_list['items']:
            events_result = self.service.events().list(calendarId=calendar['id'], timeMin=start_of_week.isoformat(),
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

    def add_meal_times_to_calendar(self, schedule, calendar_id, user_timezone):
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
            self.service.events().insert(calendarId=calendar_id, body=event).execute()

    def get_current_week_range(self, user_timezone):
        tz = pytz.timezone(user_timezone)
        today = datetime.now(tz)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return start_of_week, end_of_week

class Utils():
    @staticmethod
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
    @staticmethod
    def render_calendar(events, user_info):
        html = f"<h1>Meal Plan Calendar</h1>"
        html += f"<p>Logged in as: {user_info.get('email', 'Unknown')}</p>"
        html += '<a href="/logout">Logout</a>'
        for event in events:
            start = event['start']['dateTime']
            end = event['end']['dateTime']
            html += f"<p>{start} - {end}: {event['summary']}</p>"
        return html
    @staticmethod  
    def credentials_to_dict(credentials):
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    @staticmethod
    def credentials_from_dict(credentials_dict):
        return Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )
