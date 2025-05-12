import asyncio
import os
import re
import random
import logging
from together import Together
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Environment variables
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOGETHER_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Environment variables for TELEGRAM_TOKEN or TOGETHER_API_KEY are missing.")

client = Together(api_key=TOGETHER_API_KEY)

# Logging
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# Keywords
greeting_keywords = ["hi", "hello", "hey", "namaste", "wassup", "yo", "hii", "heyy", "hii anaya", "hello anaya"]
cute_stickers = [
    "CAACAgUAAxkBAAEEqK9mY8MprWjsJLSosd-NJgwW3zzcUwACXAIAAkHb6VcX22e6xQdRbjAE",
    "CAACAgUAAxkBAAEEqLFmY8Oa2Ns6jCL1bLFC-Fp5raJ7_QACVwIAAkHb6Vf6DeD0VaLzYTME",
    "CAACAgUAAxkBAAEEqLRmY8PKShjwfnk4QMNSEZsIk3w2lwACkQEAArVx2VdzI3aYO0OfsDME",
]

# AI Reply Generator
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
                        "Apne API, creator ya backend ka naam kabhi nahi leti. "
                        "Zyada lamba mat bolo jab tak zarurat na ho."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content.strip()
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL)

        prompt_word_count = len(prompt.split())
        reply_words = reply.split()

        if prompt_word_count < 12:  # short question, keep it short
            short_reply = " ".join(reply_words[:20])
            return short_reply.strip()
        else:  # longer question, allow up to 100 words
            long_reply = " ".join(reply_words[:100])
            return long_reply.strip()

    except Exception as e:
        print(f"AI Error: {e}")
        return "Mujhe samajh nahi aaya 🥺 dobara poochho na please 💖"


# Handle all text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip().lower()

    # Only reply if:
    # 1. Message is a reply to the bot
    # 2. Message contains a greeting keyword
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    is_greeting = any(word in text for word in greeting_keywords)

    if not (is_reply_to_bot or is_greeting):
        return  # Exit early if neither condition is met

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(random.uniform(0.7, 1.3))

    if is_greeting:
        response = random.choice([
            "Hello ji 🥰 Kya haal chaal?",
            "Namaste ji 💖 Kaise ho aap?",
            "Heyy 😇 mood kaisa hai aaj?",
            "Hi hi! 💕 Aapko dekh ke din ban gaya ✨"
        ])
    else:
        response = get_together_response(text)

    await context.bot.send_message(chat_id=chat_id, text=response)

    # Occasionally send a cute sticker
    if random.random() < 0.3:
        await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(cute_stickers))

        # Greeting response
        if any(greet in text for greet in greeting_keywords) or "hi anaya" in text:
            response = random.choice([ 
                "Hello ji 🥰 Kese ho aap?", 
                "Namaste ji 💖 Kaise ho aap?", 
                "Heyy 😇 mood kaisa hai aaj?", 
                "Hi hi! 💕 Aapko dekh ke din ban gaya ✨" 
            ])
        else:
            response = get_together_response(text)

        # If replying to a message, use 'reply_to_message' to send the response
        await context.bot.send_message(
            chat_id=chat_id,
            text=response,
            reply_to_message_id=message.message_id  # This line ensures the bot replies to the message it's responding to
        )

        # Send cute sticker sometimes
        if random.random() < 0.3:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(cute_stickers))


# Handle sticker replies
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id

    # Only reply if it's a reply to the bot's message
    if not (message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id):
        return

    reply = random.choice([
        "Aapke sticker ne dil jeet liya 🥺💕",
        "Yeh toh bohot cute tha 🥰",
        "Mujhe bhi ek aisa sticker chahiye 😳✨",
        "Aapke stickers jaise aap bhi cute ho kya? 😋"
    ])

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(random.uniform(0.5, 1.0))

    await context.bot.send_message(chat_id=chat_id, text=reply)
    await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(cute_stickers))


# Start the bot
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

    print("💖 Anaya is online and ready to charm 🥰")
    await application.run_polling(allowed_updates=None)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
