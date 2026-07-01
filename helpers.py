import datetime as dt
import json, requests, os, logging
from typing import Callable
from dotenv import set_key

logger = logging.getLogger(__name__)

url_strava_activities = "https://www.strava.com/api/v3/athlete/activities"
url_strava_token = "https://www.strava.com/oauth/token"

def generate_calendar(race_date: str) -> dict[str, str]:
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

def get_workout_id() -> str | None:
    today = dt.date.today()
    try:
        with open('calendar.json', 'r') as file:
            calendar = json.load(file)
    except FileNotFoundError:
        return None
    return calendar['schedule'][str(today)]

def get_workout_details(workout_id: str) -> dict:
    with open('plan.json', 'r') as file:
        plan = json.load(file)
    return plan[workout_id[0:3]][workout_id[3:]]

def get_activities(count: int = 1) -> list[dict]:
    logger.info("User requested activities.")
    STRAVA_ACCESS_TOKEN = get_strava_access_token()
    response = requests.get(
        url_strava_activities,
        headers={"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"},
        params={"per_page": count}
    )
    logger.info("Strava returned with %i", response.status_code)
    return trim_strava_activities(response.json())

def get_strava_access_token() -> str:
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
    logger.info("New access token generated")
    return response['access_token']

def trim_strava_activities(activities: list[dict]) -> list[dict]:
    fields = ["name", "type", "distance", "moving_time", "average_heartrate", "suffer_score", "start_date", "average_speed"]
    trimmed = []
    for activity in activities:
        trimmed.append({field: activity.get(field) for field in fields})
    return trimmed

async def get_brief(workout, activities, client, sleep, hrv, skipped_workouts):
    logger.info("User sent morning brief request to Claude")
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

def get_garmin_data(fetch_fn: Callable, key: str, fields: list[str]) -> dict:
    logger.info("Requested %s data from garmin", key)
    today = dt.date.today()
    data = fetch_fn(today.isoformat())
    data = data[key]
    trimmed = {field: data.get(field) for field in fields}
    return trimmed

def add_skip(workout_id: str, reason: str) -> None:
    with open('calendar.json', 'r') as file:
        calendar = json.load(file)
    if 'skipped' not in calendar:
        calendar['skipped'] = []
    calendar['skipped'].append({"workout": workout_id, "reason": reason})
    with open('calendar.json', 'w') as file:
        json.dump(calendar, file)
    logger.info("User skipped a workout")

def resolve_skips(activities: list[dict]) -> list[dict]:
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