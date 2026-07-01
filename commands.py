import json, anthropic, os
from garminconnect import Garmin
from helpers import generate_calendar, get_workout_id, get_workout_details, get_activities, get_brief, get_garmin_data, add_skip, resolve_skips

CLAUDE_TOKEN = os.getenv("CLAUDE_TOKEN")
GARMIN_EMAIL= os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

conversation = []
fields_sleep = [
    "sleepTimeSeconds",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "remSleepSeconds",
    "awakeSleepSeconds",
    "avgSleepStress",
    "avgHeartRate",
    "awakeCount",
    "sleepScoreFeedback",
    "sleepScoreInsight"
]
fields_hrv = [
    "lastNightAvg",
    "weeklyAvg",
    "status"
]

client_claude = anthropic.AsyncAnthropic(api_key=CLAUDE_TOKEN)

client_garmin = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)

async def respond(update, context):
    conversation.append({"role": "user", "content": update.message.text})
    response = await client_claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a helpful triathlon coach.",
        messages=conversation
    )
    conversation.append({"role": "assistant", "content": response.content[0].text})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response.content[0].text)

async def set_race(update, context):
    if not context.args:
        await update.message.reply_text("Please provide a race date! \nUsage: /setrace YYYY-MM-DD")
        return
    
    calendar = {}
    calendar['race_day'] = context.args[0]
    calendar['schedule'] = generate_calendar(calendar['race_day'])

    with open('calendar.json', 'w') as file:
        json.dump(calendar, file)
    await update.message.reply_text("Race Day and Calendar updated!")
    
async def today(update, context):
    client_garmin.login()
    skipped_workouts_details = []
    workout_id = get_workout_id()
    if workout_id == 1:
        await update.message.reply_text("Please set a race day first! \nUsage: /setrace YYYY-MM-DD")
        return
    workout = get_workout_details(workout_id)
    activities = get_activities(5)
    sleep = get_garmin_data(client_garmin.get_sleep_data, "dailySleepDTO", fields_sleep)
    hrv = get_garmin_data(client_garmin.get_hrv_data, "hrvSummary", fields_hrv)
    skipped_workouts = resolve_skips(activities)
    for s in skipped_workouts:
        skipped_workouts_details.append({"details": get_workout_details(s['workout']), "reason": s['reason']})
    brief = await get_brief(workout, activities, client_claude, sleep, hrv, skipped_workouts_details)
    conversation.clear()
    conversation.append({"role": "assistant", "content": brief.content[0].text})
    await update.message.reply_text(brief.content[0].text)

async def skip(update, context):
    if not context.args:
        await update.message.reply_text("Please provide a reason for skipping today's workout! \nUsage: /skip REASON FOR SKIPPING")
        return
    workout_id = get_workout_id()
    if workout_id == 1:
        await update.message.reply_text("Please set a race day first! \nUsage: /setrace YYYY-MM-DD")
        return
    add_skip(workout_id, " ".join(context.args))
    await update.message.reply_text("Skipped todays workout! We will make up for it!")
