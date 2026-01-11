import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus
import yt_dlp

# =====================
# 🔧 SOZLAMALAR
# =====================
BOT_TOKEN = "7621552741:AAGjJP3EJ_zEuB4j7hl3PRy8jbJwY3HgTkI" # O'z tokeningizni qo'ying
KANAL = "@QiziqUz_IT"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchi linklarini vaqtinchalik saqlash
USERS = {}

# =====================
# 📌 KANAL TEKSHIRISH
# =====================
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(KANAL, user_id)
        return member.status in [ChatMemberStatus.MEMBER,
                                 ChatMemberStatus.ADMINISTRATOR,
                                 ChatMemberStatus.CREATOR]
    except Exception:
        return False

# =====================
# 🚀 START
# =====================
@dp.message(CommandStart())
async def start(message: Message):
    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanalga aʼzo bo‘lish", url=f"https://t.me/{KANAL[1:]}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")]
        ])
        await message.answer(f"❗ Botdan foydalanish uchun {KANAL} kanaliga aʼzo bo‘ling", reply_markup=kb)
        return

    await message.answer(
        "👋 Xush kelibsiz!\n\n"
        "🎥 YouTube / TikTok / Instagram / Facebook link yuboring\n"
        "🎵 Video yoki Musiqa tanlab yuklab olasiz"
    )

# =====================
# 🔄 OBUNA TEKSHIRISH
# =====================
@dp.callback_query(F.data == "check")
async def check(callback: CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.edit_text("✅ Obuna tasdiqlandi!\nLink yuboring")
    else:
        await callback.answer("❌ Hali obuna emassiz", show_alert=True)

# =====================
# 🔗 LINK QABUL QILISH
# =====================
@dp.message(F.text.startswith("http"))
async def link_handler(message: Message):
    # Obunani har gal link yuborganda tekshirish (ixtiyoriy)
    if not await check_sub(message.from_user.id):
        await message.answer("❗ Avval kanalga a'zo bo'ling!")
        return

    USERS[message.from_user.id] = message.text

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎥 Video", callback_data="video"),
            InlineKeyboardButton(text="🎵 Musiqa", callback_data="audio")
        ]
    ])

    await message.answer("📥 Qanday formatda yuklab beray?", reply_markup=kb)

# =====================
# ⬇️ YUKLASH
# =====================
@dp.callback_query(F.data.in_(["video", "audio"]))
async def download(callback: CallbackQuery):
    url = USERS.get(callback.from_user.id)
    if not url:
        await callback.answer("❌ Link topilmadi, qaytadan yuboring", show_alert=True)
        return

    status_msg = await callback.message.edit_text("⏳ Yuklanmoqda, kuting...")

    # Fayl nomi uchun vaqtinchalik ID
    file_id = f"file_{callback.from_user.id}"
    
    ydl_opts = {
        "outtmpl": f"{file_id}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
    }

    if callback.data == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        # Video uchun eng yaxshi formatni tanlash (MP4 bo'lishi uchun)
        ydl_opts["format"] = "best[ext=mp4]/best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Haqiqiy fayl nomini aniqlash
            filename = ydl.prepare_filename(info)
            
            # Agar audio bo'lsa, extension o'zgarishi mumkin
            if callback.data == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

        if callback.data == "audio":
            await bot.send_audio(callback.from_user.id, audio=FSInputFile(filename))
        else:
            await bot.send_video(callback.from_user.id, video=FSInputFile(filename))

        await status_msg.delete()
        
        # Faylni o'chirish
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await bot.send_message(callback.from_user.id, f"❌ Xato yuz berdi: {str(e)[:100]}")
    finally:
        # Foydalanuvchi linkini tozalash
        if callback.from_user.id in USERS:
            del USERS[callback.from_user.id]

# =====================
# ▶️ ISHGA TUSHIRISH
# =====================
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
  
