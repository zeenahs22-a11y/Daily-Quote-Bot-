import os
import logging
import random
from datetime import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from quotes import QUOTES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# In-memory subscriber set (resets on redeploy).
# For persistence, see the note at the bottom of this message.
SUBSCRIBERS = set()


def format_quote(quote: dict) -> str:
    return f"💬 \"{quote['text']}\"\n\n— {quote['author']}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Daily Quote Bot! 📜\n\n"
        "Commands:\n"
        "/quote — Get a random quote now\n"
        "/subscribe — Receive a quote every day at 08:00 UTC\n"
        "/unsubscribe — Stop daily quotes"
    )


async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    quote = random.choice(QUOTES)
    await update.message.reply_text(format_quote(quote))


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    SUBSCRIBERS.add(chat_id)
    await update.message.reply_text(
        "✅ Subscribed! You'll get a daily quote at 08:00 UTC."
    )
    logger.info("User %s subscribed. Total: %d", chat_id, len(SUBSCRIBERS))


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    SUBSCRIBERS.discard(chat_id)
    await update.message.reply_text("❌ Unsubscribed. Send /subscribe anytime to rejoin.")


async def send_daily_quote(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SUBSCRIBERS:
        logger.info("Daily quote tick: no subscribers yet.")
        return
    quote = random.choice(QUOTES)
    message = format_quote(quote)
    for chat_id in list(SUBSCRIBERS):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.warning("Failed to send to %s: %s", chat_id, e)


def main() -> None:
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing!")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Schedule daily quote at 08:00 UTC
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_quote, time=time(hour=8, minute=0))

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
