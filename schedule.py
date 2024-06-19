from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set up the Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'path_to_service_account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

# Get the user's calendar events
calendar_id = 'primary'
events_result = service.events().list(calendarId=calendar_id, timeMin='2024-06-01T00:00:00Z',
                                      timeMax='2024-07-01T00:00:00Z', singleEvents=True,
                                      orderBy='startTime').execute()
events = events_result.get('items', [])

def get_free_slots(events, day_start='06:00', day_end='21:00', min_duration=30):
    free_slots = []
    day_start = datetime.strptime(day_start, '%H:%M').time()
    day_end = datetime.strptime(day_end, '%H:%M').time()

    for i in range(len(events) - 1):
        end_current = datetime.strptime(events[i]['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
        start_next = datetime.strptime(events[i + 1]['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
        if (start_next - end_current).total_seconds() / 60 >= min_duration:
            free_slots.append((end_current, start_next))

    return free_slots

# Define recipes
recipes = {
    'quick_meals': {'salad': 15, 'sandwich': 20},
    'moderate_meals': {'pasta': 45, 'stir_fry': 40},
    'elaborate_meals': {'lasagna': 90, 'roast': 120}
}

# Get free slots from calendar events
free_slots = get_free_slots(events)

# Match recipes to meal times and free slots
schedule = match_recipes_to_meal_times(free_slots, recipes, meal_times)

for item in schedule:
    print(f"{item['meal'].capitalize()}: Cook {item['recipe']} from {item['start']} to {item['end']}")
