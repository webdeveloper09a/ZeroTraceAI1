import asyncio
import os
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

# Sticker categories with a larger variety
cute_stickers = [
    "CAACAgUAAxkBAAEEqK9mY8MprWjsJLSosd-NJgwW3zzcUwACXAIAAkHb6VcX22e6xQdRbjAE",
    "CAACAgUAAxkBAAEEqLFmY8Oa2Ns6jCL1bLFC-Fp5raJ7_QACVwIAAkHb6Vf6DeD0VaLzYTME",
    "CAACAgUAAxkBAAEEqLRmY8PKShjwfnk4QMNSEZsIk3w2lwACkQEAArVx2VdzI3aYO0OfsDME",
    # Add more cute stickers here
]

sigma_stickers = [
    "CAACAgUAAxkBAAEEqLsmY8JxIH0NDAJz35uHauUlNAGjyAAC9gIAAkHb6Vc6U0E2yhv6TYM",
    "CAACAgUAAxkBAAEEqLlmY8J4zDA4BZZZrkTKPz5mM90AfQAC2xwAAtVx2Vdz7Gp46g-X4ME",
    "CAACAgUAAxkBAAEEqLlmY8KkPm6gS9QyjsHjECN6bPvoWQACggIAAkHb6Vdydm2RZ4LkgcQ",
    # Add more sigma stickers here
]

savage_stickers = [
    "CAACAgUAAxkBAAEEqLn2Y8LX9_VpLV3BdF5jXdkFxVwR9QACWgIAAkHb6Vf-NuRUYN7IlKE",
    "CAACAgUAAxkBAAEEqLr1Y8M1b7Xq-wlgv9mcYX4w2X9zQwAC8xgAAlVx2VdzSOECa8ubao",
    "CAACAgUAAxkBAAEEqLpxY8MklRCDPbhDpRSvL5dA5YwYYQAC5woAApZy5Vd0u6uVPh_gqE",
    # Add more savage stickers here
]

angry_stickers = [
    "CAACAgUAAxkBAAEEqLn2Y8MZekBhA8_Z3NjCmD6mHscqTgAC7wIAAkHb6VdxeKgi3tjpFi0E",
    "CAACAgUAAxkBAAEEqLn2Y8MvQkdZYymu24mrz-UOGwm-KQACrAIAAkHb6VdzD-QxHfNhw4cE",
    "CAACAgUAAxkBAAEEqLn2Y8MxuR8J8nNr2Xh7-mgFHv6cYgAC8wIAAkHb6Vc2h9Wws2q8sjE",
    # Add more angry stickers here
]

funny_stickers = [
    "CAACAgUAAxkBAAEEqLn2Y8M5-fpqs0xyEvqIgGXYmH6wUgAC3AIAAkHb6VfthjKYyhsfOH4E",
    "CAACAgUAAxkBAAEEqLn2Y8M1b1G6NwaFV62v32pFJVVlbgAC0QIAAkHb6VcXp_7iJgfd8WA",
    "CAACAgUAAxkBAAEEqLn2Y8M1b7Xq-3uME0I1-yD3qZjGkAACwAIAAkHb6VdzZjD9P6YOYB8",
    # Add more funny stickers here
]

chill_stickers = [
    "CAACAgUAAxkBAAEEqLn2Y8LgRl0FhP_wmJbwUJ8kI9TzHgAC_QIAAkHb6Vdz7n0Zbs53lwo",
    "CAACAgUAAxkBAAEEqLn2Y8M0RmLQ2J6mmzVZjXY3FhTTfgACGAIAAkHb6VfzpMbTElTuA1c",
    "CAACAgUAAxkBAAEEqLn2Y8LOe8uQROItSoJ7zznQ8lnlAgACpQIAAkHb6Vfx2En-ymTpKSM",
    # Add more chill stickers here
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
            "Hello ji 🥰 ?",
            "Namaste ji 💖 Kaise ho aap?",
            "Heyy 😇 mood kaisa hai aaj?",
            "Hi ! 💕 Aapko dekh ke din ban gaya ✨"
        ])
    else:
        response = get_together_response(text)

    # 🟡 Reply directly to the message
    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        reply_to_message_id=message.message_id
    )

    # Occasionally send a random sticker as a reply
    if random.random() < 0.3:
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker=random.choice(cute_stickers),
            reply_to_message_id=message.message_id
        )


# Handle sticker replies
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id

    # Only respond if the sticker is a reply to the bot's message
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        
        # Send a random sticker from the available stickers
        sticker_list = cute_stickers + sigma_stickers + savage_stickers + angry_stickers + funny_stickers + chill_stickers
        
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.5, 1.0))

        # Reply with a random sticker from the entire list
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker=random.choice(sticker_list),
            reply_to_message_id=message.message_id
        )

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
