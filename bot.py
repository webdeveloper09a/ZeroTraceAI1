

import re
import asyncio
import os
import random
import json
import logging
from together import Together
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# 🔐 Environment variables
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOGETHER_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN or TOGETHER_API_KEY.")

# ✅ Only you can trigger /start and save stickers
OWNER_ID = 7796598050

# 🤖 Together API Client
client = Together(api_key=TOGETHER_API_KEY)

# 📜 Log settings
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# 📁 File to store saved stickers
SAVED_STICKERS_FILE = "saved_stickers.json"
if os.path.exists(SAVED_STICKERS_FILE):
    with open(SAVED_STICKERS_FILE, "r") as f:
        saved_stickers = json.load(f)
else:
    saved_stickers = []

def save_sticker(file_id):
    if file_id not in saved_stickers:
        saved_stickers.append(file_id)
        with open(SAVED_STICKERS_FILE, "w") as f:
            json.dump(saved_stickers, f)

# 👋 Greeting keywords
greeting_keywords = ["hi", "hello", "hey", "namaste", "wassup", "yo", "hii", "heyy", "hii anaya", "hello anaya"]

# 🤖 AI Response Logic (filtered and smart)
def get_together_response(prompt):
    if any(q in prompt.lower() for q in ["where are you from", "kaha se ho", "kidhar se ho"]):
        return "Main Mumbai se hoon ji 💖 Aap kaha se ho?"

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-235B-A22B-fp8-tput",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tumhara naam Anaya hai. Tum ek sweet, smart, aur respectful Indian ladki ho. "
                        "Sirf Hinglish me baat karti ho, emojis ka use karti ho (🥰💕✨), aur kabhi bhi 'How can I help you today' jaisi line nahi bolti. "
                        "Apne API, creator ya backend ka naam kabhi nahi leti. Zyada lamba mat bolo jab tak zarurat na ho."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content.strip()
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL)

        # Remove any assistant-style generic replies
        banned_phrases = [
            "how can i help","kya help chaiye", "how may i assist", "kya madad", "need any help", "need assistance", "kaise madad", "can i help"
        ]
        for phrase in banned_phrases:
            if phrase in reply.lower():
                return "Kya bol rahe ho 😅 thoda clearly poochho na 💖"

        prompt_word_count = len(prompt.split())
        reply_words = reply.split()
        return " ".join(reply_words[:20 if prompt_word_count < 12 else 100]).strip()

    except Exception as e:
        print(f"AI Error: {e}")
        return "Mujhe samajh nahi aaya 🥺 dobara poochho na please 💖"

# 🟡 Handle /start in private chat only if from owner
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private" and update.effective_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🥰 Send me stickers to save!"
        )

# 🗨️ Handle text (only if replied to Anaya or contains 'anaya')
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip().lower()

    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    mentions_anaya = "anaya" in text

    # Only respond if message is a reply to bot or contains "anaya"
    if not (is_reply_to_bot or mentions_anaya):
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(random.uniform(0.7, 1.3))

    response = get_together_response(text)

    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        reply_to_message_id=message.message_id
    )

# 🧸 Handle sticker messages
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    user_id = update.effective_user.id

    if not message.sticker:
        return

    file_id = message.sticker.file_id

    # Save stickers ONLY in private chat and ONLY from OWNER
    if message.chat.type == "private" and user_id == OWNER_ID:
        if file_id not in saved_stickers:
            save_sticker(file_id)

    # Only reply to sticker if it was a reply to bot AND there's at least 1 saved sticker
    is_reply_to_bot = (
        message.reply_to_message and 
        message.reply_to_message.from_user and 
        message.reply_to_message.from_user.id == context.bot.id
    )

    if is_reply_to_bot and saved_stickers:
        # Avoid replying with the same sticker
        choices = [s for s in saved_stickers if s != file_id]
        if not choices:
            return  # No other sticker to reply with

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.5, 1.0))
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker=random.choice(choices),
            reply_to_message_id=message.message_id
        )

    # If it's a reply to bot, respond with random sticker
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    if is_reply_to_bot and saved_stickers:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.5, 1.0))
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker=random.choice(saved_stickers),
            reply_to_message_id=message.message_id
        )

# 🚀 Start the bot
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    print("💖 Anaya is online and ready to charm 🥰")
    print("🧸 Send me stickers to save!")

    await application.run_polling(allowed_updates=None)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
