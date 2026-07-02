import os, logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

from commands import set_race, today, respond, skip, done

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("setrace", set_race))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.TEXT, respond))

    app.run_polling()

