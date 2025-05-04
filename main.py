import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

# تنظیمات
TOKEN = '8066681959:AAHe5wbH7gHivg7296Iy9URQnfNEIMvsrJI'
CHAT_ID = '@FM_MIRAGE'

# تابع زمان‌بندی‌شده
async def send_message():
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="سلام دختر بابایییی صبحتر بخیر بابیی عاشقته")
    print(f"پیام روزانه فرستاده شد: {datetime.now()}")

# تابع هندلر برای /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من دستیار متینم، برای اینکه هرروز از طرف متین صبح بخیر بگم.")
    print(f"کاربر /start زد - Chat ID: {update.effective_chat.id}")

# تابع اصلی
async def main():
    # ساخت Application و تنظیم توکن
    application = ApplicationBuilder().token(TOKEN).build()

    # هندلر /start
    application.add_handler(CommandHandler("start", start))

    # زمان‌بندی روزانه
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Tehran'))
    scheduler.add_job(send_message, 'cron', hour=6, minute=0)
    scheduler.start()

    # شروع ربات و گوش دادن به پیام‌ها
    await application.run_polling()

if _name_ == '_main_':
    asyncio.run(main())
