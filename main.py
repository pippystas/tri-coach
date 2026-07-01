import os
from dotenv import load_dotenv
load_dotenv()
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from commands import set_race, today, respond, skip

if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("setrace", set_race))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(MessageHandler(filters.TEXT, respond))

    app.run_polling()

