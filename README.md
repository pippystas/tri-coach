# Tri-Coach

A personal triathlon coaching Telegram bot. Following a plan for your training is great, however if its static, it will not be able to dynamically adapt to you and your body. Tri-Coach gives you a smart morning brief using your Garmin sleep/HRV data and recent Strava activities, and supports ongoing conversation with your coach throughout the day.

Any suggestions on how to improve it are more than welcome!

Thank you for stopping by - Pippy

## What it does

- `/today` — morning brief with today's planned workout, recovery analysis from last night's sleep and HRV, and notes on recent training load. Seeds a conversation so follow-up chat has full context.
- `/skip <reason>` — logs a skipped workout. On the next `/today`, the bot checks Strava for makeup activities and clears resolved skips automatically. Unresolved skips are passed to Claude, which suggests a makeup if recovery looks good.
- `/done [how you felt]` — fetches your latest Strava activity and asks Claude for feedback. Optionally add a note on how you felt.
- `/setrace YYYY-MM-DD` — generates a 12-week training calendar counting back from your race date.
- Free chat — talk to your coach anytime. Remembers the morning brief for the rest of the day.

## Stack

- Python 3
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 22.8
- [Anthropic API](https://docs.anthropic.com) — claude-sonnet-4-6
- [Strava API](https://developers.strava.com)
- [garminconnect](https://github.com/cyberjunky/python-garmin-connect)
- python-dotenv

## Setup

**1. Clone and install dependencies**

```bash
git clone https://github.com/pippystas/tri-coach.git
cd tri-coach
pip install -r requirements.txt
```

**2. Create a `.env` file**

```
TELEGRAM_TOKEN=
CLAUDE_TOKEN=
GARMIN_EMAIL=
GARMIN_PASSWORD=
STRAVA_CLIENT_ID=
STRAVA_SECRET=
STRAVA_REFRESH_TOKEN=
```

**3. Set your race date**

Start the bot, then send `/setrace YYYY-MM-DD` in Telegram. This generates your 12-week training calendar (based on a Garmin triathlon plan).

**4. Run**

```bash
python main.py
```

## Skipping workouts

When you skip a workout, log it with `/skip <reason>`:

```
/skip bike trip
```

To mark a skipped workout as completed, name the activity on Strava as `<workout-id> skip`, e.g. `W7D2 skip`. The next `/today` will detect it and clear it from the list automatically.

## File structure

```
main.py          — bot setup and polling
commands.py      — Telegram command and message handlers
helpers.py       — API calls and data processing
plan.json        — 12-week training plan
calendar.json    — generated schedule (gitignored)
.env             — secrets (gitignored)
```
