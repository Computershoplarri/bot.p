import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# Gemini AI setup
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Seen bonuses set
seen_bonuses = set()

# Scraper function
def scrape_bonuses():
    bonuses = []
    headers = {"User-Agent": "Mozilla/5.0"}

    # XM example
    try:
        url_xm = "https://www.xm.com/promotions"
        r = requests.get(url_xm, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.find_all("h3"):
            text = item.text.strip()
            if "bonus" in text.lower() and text not in seen_bonuses:
                seen_bonuses.add(text)
                bonuses.append(f"💰 XM: {text}")
    except Exception as e:
        print("Error XM:", e)

    return bonuses

# Bonus check function
async def check_new_bonuses(bot):
    while True:
        new_bonuses = scrape_bonuses()
        for bonus in new_bonuses:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=bonus)
        await asyncio.sleep(300)  # 5 min delay

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    if "bonus" in user_message:
        reply = "\n".join(scrape_bonuses())
    else:
        try:
            reply = llm.invoke(user_message).content
        except Exception:
            reply = "⚠️ AI service busy, try again later."
    await update.message.reply_text(reply)

# Bot setup
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bonus AI Bot is running...")

# Run bot + bonus checker
async def main():
    bot_task = asyncio.create_task(check_new_bonuses(app.bot))
    await app.run_polling()

asyncio.run(main())

