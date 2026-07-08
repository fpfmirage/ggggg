from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ContentType
import asyncio
import json
import os

# =======================
# CONFIG
# =======================
TOKEN = "8836838419:AAEmSkrIGvfbxwKeOH1IIT51ht6lY9ZiZzg"          # ← توکن ربات رو اینجا بذار

ADMIN_ID = 5681523384                       # ← آیدی عددی خودت رو اینجا بذار
CHANNELS_FILE = "channels.json"

bot = Bot(TOKEN)
dp = Dispatcher()

songs = {}
downloads = {}


# =======================
# LOAD / SAVE CHANNELS
# =======================
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return ["@miragemix", "@SnowRemix"]


def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)


CHANNELS = load_channels()


# =======================
# CHECK MEMBERSHIP
# =======================
async def is_member(user_id: int) -> bool:
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


# =======================
# JOIN BUTTON
# =======================
def join_button(code: str):
    kb = InlineKeyboardBuilder()
    for ch in CHANNELS:
        kb.button(text=f"📢 عضویت {ch}", url=f"https://t.me/{ch.replace('@','')}")
    kb.button(text="✅ عضو شدم", callback_data=f"check_{code}")
    kb.adjust(1)
    return kb.as_markup()


# =======================
# SEND SONG
# =======================
async def send_song(message: types.Message, code: str):
    if code in songs:
        downloads[code] = downloads.get(code, 0) + 1
        await message.answer_audio(
            songs[code],
            caption=f"🎵 دانلود شد | {downloads[code]} بار"
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
    if message.from_user.id != ADMIN_ID:
        return
    try:
        channel = message.text.split()[1].strip()
        if not channel.startswith("@"):
            channel = "@" + channel

        if channel in CHANNELS:
            await message.answer(f"⚠️ کانال `{channel}` قبلاً اضافه شده.")
            return

        CHANNELS.append(channel)
        save_channels(CHANNELS)
        await message.answer(f"✅ کانال `{channel}` اضافه شد.")
    except:
        await message.answer("❌ نحوه استفاده:\n`/addchannel @username`")


@dp.message(Command("removechannel"))
async def remove_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        channel = message.text.split()[1].strip()
        if not channel.startswith("@"):
            channel = "@" + channel

        if channel not in CHANNELS:
            await message.answer(f"⚠️ کانال `{channel}` پیدا نشد.")
            return

        CHANNELS.remove(channel)
        save_channels(CHANNELS)
        await message.answer(f"✅ کانال `{channel}` حذف شد.")
    except:
        await message.answer("❌ نحوه استفاده:\n`/removechannel @username`")


@dp.message(Command("channels"))
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ فقط ادمین اجازه دسترسی داره.")
        return

    if not CHANNELS:
        await message.answer("📭 هیچ کانالی ثبت نشده.")
        return

    text = "📋 **کانال‌های فعلی:**\n\n" + "\n".join(f"• {ch}" for ch in CHANNELS)
    await message.answer(text)


# =======================
# ADMIN UPLOAD SONG
# =======================
@dp.message(F.content_type == ContentType.AUDIO)
async def upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    code = message.audio.file_unique_id
    songs[code] = message.audio.file_id
    downloads[code] = 0

    link = f"https://t.me/{(await bot.get_me()).username}?start={code}"
    await message.answer(f"✅ لینک ساخته شد:\n{link}")


# =======================
# MAIN
# =======================
async def main():
    print("✅ بات با موفقیت شروع شد!")
    print(f"👤 ADMIN_ID: {ADMIN_ID}")
    print(f"📢 کانال‌های فعلی: {CHANNELS}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())