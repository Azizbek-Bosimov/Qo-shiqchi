import os
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

# --- WEB SERVER (Render o'chib qolmasligi uchun) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- BOT SOZLAMALARI ---
API_TOKEN = '8679477302:AAEN9lvYl8Er4x1NQC_mRe7NLGKrya-ocT0'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Yuklab olish funksiyasi
def download_media(url, mode='video'):
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'restrictfilenames': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Video + Audio birga, maksimal 720p (Render xotirasi uchun xavfsizroq)
        ydl_opts.update({'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if mode == 'audio':
            return filename.rsplit('.', 1)[0] + '.mp3'
        return filename

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Link yuboring, men uni Video va MP3 qilib beraman.\n\n"
                         "⚠️ Render bepul tarifida katta videolar yuklanmasligi mumkin.")

@dp.message()
async def handle_message(message: types.Message):
    url = message.text
    if not url.startswith("http"):
        return

    status_msg = await message.answer("Yuklanmoqda... (Bu biroz vaqt olishi mumkin)")

    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # 1. Audioni yuklash va yuborish
        audio_path = download_media(url, mode='audio')
        await message.answer_audio(types.FSInputFile(audio_path), caption="🎵 @tingla_bot uslubida")
        if os.path.exists(audio_path): os.remove(audio_path)

        # 2. Videoni yuklash va yuborish
        video_path = download_media(url, mode='video')
        await message.answer_video(types.FSInputFile(video_path), caption="🎬 Video tayyor!")
        if os.path.exists(video_path): os.remove(video_path)

        await status_msg.delete()

    except Exception as e:
        await message.answer(f"Xatolik: Link noto'g'ri yoki fayl juda katta.\nDetallar: {str(e)[:100]}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    keep_alive() # Veb-serverni fonda ishga tushirish
    asyncio.run(main())
