from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import aiosqlite
import os

# =======================
# CONFIG
# =======================
TOKEN = "8836838419:AAEmSkrIGvfbxwKeOH1IIT51ht6lY9ZiZzg"
ADMIN_ID = 5681523384
DB_FILE = "bot_data.db"          # فایل دیتابیس

bot = Bot(TOKEN)
dp = Dispatcher()

# =======================
# DATABASE SETUP
# =======================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                code TEXT PRIMARY KEY,
                file_id TEXT,
                downloads INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel TEXT PRIMARY KEY
            )
        """)
        await db.commit()


async def load_channels():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT channel FROM channels")
        rows = await cursor.fetchall()
        channels = [row[0] for row in rows]
        return channels if channels else ["@miragemix", "@SnowRemix"]


async def save_channel(channel: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT OR IGNORE INTO channels (channel) VALUES (?)", (channel,))
        await db.commit()


async def remove_channel(channel: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM channels WHERE channel = ?", (channel,))
        await db.commit()


async def get_song(code: str):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT file_id, downloads FROM songs WHERE code = ?", (code,))
        row = await cursor.fetchone()
        return row if row else None


async def save_song(code: str, file_id: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO songs (code, file_id, downloads) VALUES (?, ?, 0)",
            (code, file_id)
        )
        await db.commit()


async def increment_download(code: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE songs SET downloads = downloads + 1 WHERE code = ?",
            (code,)
        )
        await db.commit()


# =======================
# INITIALIZE
# =======================
CHANNELS = []


# =======================
# CHECK MEMBERSHIP
# =======================
async def is_member(user_id):
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


def join_button(code):
    kb = InlineKeyboardBuilder()
    for ch in CHANNELS:
        kb.button(text=f"📢 عضویت {ch}", url=f"https://t.me/{ch.replace('@','')}")
    kb.button(text="✅ عضو شدم", callback_data=f"check_{code}")
    kb.adjust(1)
    return kb.as_markup()


# =======================
# SEND SONG
# =======================
async def send_song(message, code):
    song = await get_song(code)
    if song:
        file_id, downloads_count = song
        await increment_download(code)
        new_count = downloads_count + 1
        await message.answer_audio(
            file_id,
            caption=f"🎵 دانلود شد | {new_count} بار"
        )
    else:
        await message.answer("❌ آهنگ پیدا نشد")


# =======================
# START COMMAND
# =======================
@dp.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ لینک اشتباهه")
        return

    code = args[1]

    if not await is_member(message.from_user.id):
        await message.answer(
            "❌ برای دریافت آهنگ باید عضو همه کانال‌ها بشی:",
            reply_markup=join_button(code)
        )
        return

    await send_song(message, code)


# =======================
# ADMIN COMMANDS
# =======================
@dp.message(Command("addchannel"))
async def add_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        channel = message.text.split()[1].strip()
        if not channel.startswith("@"):
            channel = "@" + channel

        if channel in CHANNELS:
            await message.answer(f"⚠️ کانال `{channel}` قبلاً اضافه شده.")
            return

        await save_channel(channel)
        CHANNELS.append(channel)
        await message.answer(f"✅ کانال `{channel}` اضافه شد.")
    except:
        await message.answer("❌ نحوه استفاده:\n`/addchannel @username`")


@dp.message(Command("removechannel"))
async def remove_channel_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        channel = message.text.split()[1].strip()
        if not channel.startswith("@"):
            channel = "@" + channel

        if channel not in CHANNELS:
            await message.answer(f"⚠️ کانال `{channel}` پیدا نشد.")
            return

        await remove_channel(channel)
        CHANNELS.remove(channel)
        await message.answer(f"✅ کانال `{channel}` حذف شد.")
    except:
        await message.answer("❌ نحوه استفاده:\n`/removechannel @username`")


@dp.message(Command("channels"))
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = "📋 **کانال‌های فعلی:**\n\n" + "\n".join(f"• {ch}" for ch in CHANNELS) if CHANNELS else "📭 هیچ کانالی ثبت نشده."
    await message.answer(text)


# =======================
# UPLOAD SONG
# =======================
@dp.message()
async def upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.audio:
        code = message.audio.file_unique_id
        await save_song(code, message.audio.file_id)

        link = f"https://t.me/{(await bot.get_me()).username}?start={code}"
        await message.answer(f"✅ لینک ساخته شد:\n{link}")


# =======================
# MAIN
# =======================
async def main():
    global CHANNELS
    await init_db()
    CHANNELS = await load_channels()
    
    print("✅ بات با SQLite شروع شد!")
    print(f"📀 تعداد آهنگ‌های ذخیره شده: {await get_song_count()}")
    print(f"📢 کانال‌ها: {CHANNELS}")
    await dp.start_polling(bot)


async def get_song_count():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM songs")
        count = (await cursor.fetchone())[0]
        return count


if __name__ == "__main__":
    asyncio.run(main())