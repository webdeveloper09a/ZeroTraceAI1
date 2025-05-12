import asyncio
import os
import re
import random
import logging
from together import Together
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ✅ Correct environment variable usage
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Check for missing token
if not TOGETHER_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("TOGETHER_API_KEY or TELEGRAM_TOKEN not set in environment variables.")

client = Together(api_key=TOGETHER_API_KEY)

# Logging setup
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# Greeting keywords
greeting_keywords = ["hi baby", "hello", "hey", "namaste", "hello there", "wassup", "kaise ho"]

# Cute sticker list
CUTE_STICKERS = [
    "CAACAgUAAxkBAAEEqK9mY8MprWjsJLSosd-NJgwW3zzcUwACXAIAAkHb6VcX22e6xQdRbjAE",
    "CAACAgUAAxkBAAEEqLFmY8Oa2Ns6jCL1bLFC-Fp5raJ7_QACVwIAAkHb6Vf6DeD0VaLzYTME",
    "CAACAgUAAxkBAAEEqLRmY8PKShjwfnk4QMNSEZsIk3w2lwACkQEAArVx2VdzI3aYO0OfsDME",
]

# Get reply from Together AI
def get_together_response(prompt):
    if any(word in prompt.lower() for word in ["where are you from", "kaha se ho", "kidhar se ho", "kaha ki ho"]):
        return "Main Mumbai se hoon ji 💖 Aap kaha se ho? 😊"

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-235B-A22B-fp8-tput",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tumhara naam Anaya hai. Tum ek smart, sweet, respectful aur bubbly Indian ladki ho. "
                        "Hamesha Hinglish me baat karti ho, emojis ka use karti ho (🥰💕✨😇) aur sabko 'aap' kehkar izzat se baat karti ho. "
                        "Thoda mazaak kar sakti ho lekin kabhi badtameezi nahi karti. "
                        "Kabhi bhi apne creator, backend, ya API ke baare me baat mat karo. "
                        "Sirf ladki wali vibe do, bilkul bhi ladke jaise baat mat karo."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content.strip()
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL)
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return "Maaf kijiye, mujhe samajh nahi aaya 😶"

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip().lower()

    should_reply = False

    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        should_reply = True
    elif "anaya" in text:
        should_reply = True
    elif any(greet in text for greet in greeting_keywords):
        should_reply = True

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.7, 1.5))

        if any(greet in text for greet in greeting_keywords):
            response = "Hello! 💖 Kese ho ji? 🥰"
        else:
            response = get_together_response(text)

        await context.bot.send_message(chat_id=chat_id, text=response)

        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

# Handle stickers
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id

    cute_replies = [
        "Ye sticker toh dil le gaya 💕",
        "Aap toh bade cute sticker bhejte ho 😍",
        "Aapka sticker dekh ke mood fresh ho gaya 😇",
        "Anaya blush kar gayi yeh dekh ke 😳💞",
    ]

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(random.uniform(0.5, 1.2))

    reply = random.choice(cute_replies)
    await context.bot.send_message(chat_id=chat_id, text=reply)
    await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

# Start bot
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    print("Anaya is live 💖 Ready to chat with respect and cuteness 😘")
    await application.run_polling(allowed_updates=None)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
