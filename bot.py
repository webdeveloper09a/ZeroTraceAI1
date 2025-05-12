
import asyncio
import os
import re
import random
import logging
from together import Together
from telegram import Update, ChatAction
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Load API keys (for Railway or environment)
TOGETHER_API_KEY = os.getenv("35bf12819e431ac91422d71a558ee11b8cbfc82b259dbdc2b9c03e34e7ebd81c")
TELEGRAM_TOKEN = os.getenv("7484026532:AAFsfVdVhs2Ul3vGK15qVtUZo60h5Wu7UGU")

client = Together(api_key=TOGETHER_API_KEY)

# Logging setup
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# Greeting words (girly vibe)
greeting_keywords = ["hi baby", "hello", "hey", "namaste", "hello there", "wassup", "kaise ho"]

# Cute stickers list
CUTE_STICKERS = [
    "CAACAgUAAxkBAAEEqK9mY8MprWjsJLSosd-NJgwW3zzcUwACXAIAAkHb6VcX22e6xQdRbjAE",
    "CAACAgUAAxkBAAEEqLFmY8Oa2Ns6jCL1bLFC-Fp5raJ7_QACVwIAAkHb6Vf6DeD0VaLzYTME",
    "CAACAgUAAxkBAAEEqLRmY8PKShjwfnk4QMNSEZsIk3w2lwACkQEAArVx2VdzI3aYO0OfsDME",
]

# Reply generator
def get_together_response(prompt):
    # Hardcoded reply if someone asks where she's from
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

    # Anaya only replies if "Anaya" is mentioned or a reply to her message
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        # Reply if it's a direct reply to Anaya
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.7, 1.5))

        response = get_together_response(message.text)
        await context.bot.send_message(chat_id=chat_id, text=response)

        # Random sticker with message
        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

    elif "anaya" in text:
        # Reply when "Anaya" is mentioned anywhere
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.7, 1.5))

        response = get_together_response(text)
        await context.bot.send_message(chat_id=chat_id, text=response)

        # Random sticker with message
        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

    elif any(greeting in text for greeting in greeting_keywords):
        # Respond to greetings
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.7, 1.5))

        response = "Hello! 💖 Kese ho ji? 🥰"
        await context.bot.send_message(chat_id=chat_id, text=response)

        # Send a cute sticker for greetings
        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

    else:
        # General message reply
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.7, 1.5))

        response = get_together_response(text)
        await context.bot.send_message(chat_id=chat_id, text=response)

        # Random sticker with message
        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(CUTE_STICKERS))

# Handle incoming stickers
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

# Start the bot
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
