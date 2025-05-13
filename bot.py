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

# ✅ Only owner can save stickers
OWNER_ID = 7796598050

# 🤖 Together API client
client = Together(api_key=TOGETHER_API_KEY)

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

# 🔊 Greeting triggers
greeting_keywords = ["hi", "hello", "hey", "namaste", "wassup", "yo", "hii", "heyy", "hello anaya", "hii anaya"]

# 🧠 AI reply generator
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

        banned_phrases = [
            "how can i help", "kya help chaiye", "how may i assist",
            "kya madad", "need any help", "need assistance", "kaise madad", "can i help"
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

# /start command for owner in private
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private" and update.effective_user.id == OWNER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🥰 Send me stickers to save!")

# ✍️ Handle messages to Anaya or replies to her
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip().lower()

    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    mentions_anaya = "anaya" in text

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

# 🧸 Handle sticker replies
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.sticker:
        return

    chat = message.chat
    user_id = message.from_user.id
    file_id = message.sticker.file_id

    # 🏠 Save sticker if owner sends it in private chat
    if chat.type == "private" and user_id == OWNER_ID:
        save_sticker(file_id)

    # 💬 Only reply if it's a reply to bot
    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == context.bot.id
        and saved_stickers
    ):
        choices = [s for s in saved_stickers if s != file_id]
        if not choices:
            choices = saved_stickers

        await context.bot.send_chat_action(chat.id, ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.4, 0.7))
        await context.bot.send_sticker(
            chat_id=chat.id,
            sticker=random.choice(choices),
            reply_to_message_id=message.message_id
        )

# 🚀 Run the bot
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    print("💖 Anaya is online and ready 🥰")
    await application.run_polling(allowed_updates=None)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
