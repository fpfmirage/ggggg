from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

# =======================
# CONFIG
# =======================
TOKEN = "8836838419:AAEmSkrIGvfbxwKeOH1IIT51ht6lY9ZiZzg"

CHANNELS = ["@miragemix", "@SnowRemix","@daarkkheart"]
ADMIN_ID = [5681523384,7243699586]

bot = Bot(TOKEN)
dp = Dispatcher()

songs = {}       # code -> file_id
downloads = {}   # code -> count


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


# =======================
# JOIN BUTTON
# =======================
def join_button(code):
    kb = InlineKeyboardBuilder()

    for ch in CHANNELS:
        kb.button(
            text=f"📢 عضویت {ch}",
            url=f"https://t.me/{ch.replace('@','')}"
        )

    kb.button(
        text="✅ عضو شدم",
        callback_data=f"check_{code}"
    )

    kb.adjust(1)
    return kb.as_markup()


# =======================
# SEND SONG
# =======================
async def send_song(message, code):

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
            "❌ برای دریافت آهنگ باید عضو کانال‌ها بشی",
            reply_markup=join_button(code)
        )
        return

    await send_song(message, code)


# =======================
# CHECK JOIN BUTTON
# =======================
@dp.callback_query(lambda c: c.data.startswith("check_"))
async def check_join(callback: types.CallbackQuery):

    code = callback.data.split("_")[1]

    if await is_member(callback.from_user.id):

        await callback.message.delete()
        await send_song(callback.message, code)

    else:
        await callback.answer(
            "❌ هنوز عضو همه کانال‌ها نیستی",
            show_alert=True
        )


# =======================
# ADMIN UPLOAD SONG
# =======================
@dp.message()
async def upload(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    if message.audio:

        code = message.audio.file_unique_id

        songs[code] = message.audio.file_id
        downloads[code] = 0

        link = f"https://t.me/{(await bot.get_me()).username}?start={code}"

        await message.answer(f"✅ لینک ساخته شد:\n{link}")


# =======================
# MAIN
# =======================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())