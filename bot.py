import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

load_dotenv()  # loads from .env file on your laptop

# --- CONFIG - Now reads from environment (safe for GitHub) ---
TOKEN = os.getenv("BOT_TOKEN")  # we get it from env, not hardcoded
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
# ------------------------------------------------------------

if not TOKEN:
    raise ValueError("BOT_TOKEN not found! Set it in .env file or Render dashboard")

pending = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await update.effective_message.reply_text(
            "👋 Send me your confession — text, photo, video, voice.\n"
            "It will be posted ANONYMOUSLY after review."
        )

async def receive_confession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    msg_id = str(update.message.message_id)
    pending[msg_id] = update.message

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{msg_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{msg_id}")
    ]])

    try:
        await update.message.copy(chat_id=ADMIN_ID, caption=f"🕵️ New confession ID {msg_id}\n\n{update.message.text or update.message.caption or ''}", reply_markup=keyboard)
        await update.effective_message.reply_text("✅ Received! Pending admin review.")
    except Exception as e:
        print(f"Admin send failed: {e}")
        await update.effective_message.reply_text(f"❌ Failed to send to admin. Check ADMIN_ID.")

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    try:
        action, msg_id = query.data.split("_", 1)
    except:
        return
    original = pending.get(msg_id)
    if not original:
        await query.edit_message_caption(caption="Already handled.")
        return
    if action == "approve":
        try:
            if original.text:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🤫 Anonymous Confession:\n\n{original.text}")
            else:
                await original.copy(chat_id=CHANNEL_ID, caption=f"🤫 Anonymous Confession\n\n{original.caption or ''}")
            await query.edit_message_caption(caption=f"✅ Posted - {msg_id}")
        except Exception as e:
            await query.edit_message_caption(caption=f"❌ Failed to post: {e}")
    else:
        await query.edit_message_caption(caption=f"❌ Rejected - {msg_id}")
    pending.pop(msg_id, None)

request = HTTPXRequest(connect_timeout=30, read_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_admin))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, receive_confession))
print("Anonymous bot running...")
app.run_polling()