import datetime as dt
import json, requests, os
from dotenv import set_key

url_strava_activities = "https://www.strava.com/api/v3/athlete/activities"
url_strava_token = "https://www.strava.com/oauth/token"

def generate_calendar(race_date):
    today = dt.date.today()
    date = dt.date.fromisoformat(race_date)
    d = dt.timedelta(days=1)
    schedule = {}

    for i in range(12, 0, -1):
        for y in range(7, 0, -1):
            schedule[str(date)] = f"W{i:02d}D{y}"
            if (date == today):
                return schedule # Generate the schedule until today only
            date = date - d
    
    return schedule

def get_workout_id():
    today = dt.date.today()
    try:
        with open('calendar.json', 'r') as file:
            calendar = json.load(file)
    except FileNotFoundError:
        return 1
    return calendar['schedule'][str(today)]

def get_workout_details(workout_id):
    with open('plan.json', 'r') as file:
        plan = json.load(file)
    return plan[workout_id[0:3]][workout_id[3:]]

def get_activities(count=1):
    STRAVA_ACCESS_TOKEN = get_strava_access_token()
    response = requests.get(
        url_strava_activities,
        headers={"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"},
        params={"per_page": count}
    )
    return trim_strava_activities(response.json())

def get_strava_access_token():
    response = requests.post(
        url_strava_token, data={
            "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"),
            "client_id": os.getenv("STRAVA_CLIENT_ID"),
            "client_secret": os.getenv("STRAVA_SECRET"),
            "grant_type": "refresh_token",
        }
    ).json()
    set_key(".env", "STRAVA_ACCESS_TOKEN", response['access_token'])
    set_key(".env", "STRAVA_REFRESH_TOKEN", response['refresh_token'])
    return response['access_token']

def trim_strava_activities(activities):
    fields = ["name", "type", "distance", "moving_time", "average_heartrate", "suffer_score", "start_date", "average_speed"]
    trimmed = []
    for activity in activities:
        trimmed.append({field: activity.get(field) for field in fields})
    return trimmed

async def get_brief(workout, activities, client, sleep, hrv, skipped_workouts):
    return await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=(
            "You are a triathlon coach sending a daily morning brief via Telegram. "
            "Be concise, direct and do not be afraid to be harsh. Formatting symbols, such as: '*' or '\' do not work! "
            "Cover: today's workout, any recovery notes based on recent training, and one motivational sentence. "
            "If the athlete looks well rested based on sleep and HRV and there are skipped workouts, "
            "suggest the single skipped workout that fits best alongside his training — pick based on type, fatigue, past workouts, not just order. "
            "Do not suggest a makeup if recovery looks poor. Keep it under 200 words."
        ),
        messages=[{"role": "user", "content": (
            f"Date: {dt.date.today()}\n"
            f"Today's workout: {workout}\n"
            f"Recent activities: {activities}\n"
            f"Sleep: {sleep}\n"
            f"HRV: {hrv}\n"
            f"Skipped workouts: {skipped_workouts}"
        )}]
    )

def get_garmin_data(fetch_fn, key, fields):
    today = dt.date.today()
    data = fetch_fn(today.isoformat())
    data = data[key]
    trimmed = {field: data.get(field) for field in fields}
    return trimmed

def add_skip(workout, reason):
    with open('calendar.json', 'r') as file:
        calendar = json.load(file)
    if 'skipped' not in calendar:
        calendar['skipped'] = []
    calendar['skipped'].append({"workout": workout, "reason": reason})
    with open('calendar.json', 'w') as file:
        json.dump(calendar, file)

def resolve_skips(activities):
    completed_workouts = []
    with open('calendar.json', 'r') as file:
        calendar = json.load(file)
    if 'skipped' not in calendar:
        return []
    skipped_workouts = calendar['skipped']
    for activity in activities:
        if "skip" in activity['name'].lower():
            completed_workouts.append(activity['name'].split()[0])
    for workout in completed_workouts:
        skipped_workouts = [s for s in skipped_workouts if s['workout'] != workout]
    calendar['skipped'] = skipped_workouts
    with open('calendar.json', 'w') as file:
        json.dump(calendar, file)
    return skipped_workouts