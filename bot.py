import os
import threading
from flask import Flask
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Store pending confessions
pending = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Send me your anonymous confession — admin will review it.")


@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_confession(message):
    # Send to admin for approval
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.chat.id}_{message.message_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.chat.id}_{message.message_id}")
    )

    # Save text
    pending[f"{message.chat.id}_{message.message_id}"] = message.text

    bot.send_message(ADMIN_ID, f"🕊️ New Confession:\n\n{message.text}", reply_markup=markup)
    bot.reply_to(message, "✅ Sent for review. You'll stay anonymous.")


@bot.callback_query_handler(func=lambda call: True)
def handle_approval(call):
    data = call.data
    key = data.split('_', 1)[1]  # chatid_msgid

    if key not in pending:
        bot.answer_callback_query(call.id, "Already handled")
        return

    confession_text = pending[key]

    if data.startswith("approve_"):
        bot.send_message(CHANNEL_ID, f"🕊️ Anonymous Confession:\n\n{confession_text}")
        bot.edit_message_text(f"✅ APPROVED & Posted:\n\n{confession_text}", ADMIN_ID, call.message.message_id)
        # Notify user
        try:
            user_id = key.split('_')[0]
            bot.send_message(user_id, "✅ Your confession was approved and posted!")
        except:
            pass
    else:
        bot.edit_message_text(f"❌ REJECTED:\n\n{confession_text}", ADMIN_ID, call.message.message_id)
        try:
            user_id = key.split('_')[0]
            bot.send_message(user_id, "❌ Your confession was not approved.")
        except:
            pass

    del pending[key]
    bot.answer_callback_query(call.id, "Done")


# --- For Render FREE tier ---
@app.route('/')
def home():
    return "Bot is alive!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()