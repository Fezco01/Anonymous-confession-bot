import os
import threading
from flask import Flask
import telebot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


# --- Confession handling ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Send me your anonymous confession and I'll post it to the channel.")


@bot.message_handler(func=lambda m: True)
def handle_confession(message):
    if not message.text:
        return

    # Forward to admin for approval, or directly to channel
    text = f"🕊️ Anonymous Confession:\n\n{message.text}"

    try:
        # Post directly to channel - change to ADMIN_ID if you want approval first
        bot.send_message(CHANNEL_ID, text)
        bot.reply_to(message, "✅ Your confession was posted anonymously!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


# --- Fake website for Render Free Tier ---
@app.route('/')
def home():
    return "Bot is alive!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


def run_bot():
    print("Bot polling started...")
    bot.infinity_polling()


if __name__ == "__main__":
    # Run Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    # Run Telegram bot in main thread
    run_bot()
