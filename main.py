import re, os, requests, tempfile, shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

def download_with_ytdlp(url):
    import yt_dlp
    tmpdir = tempfile.mkdtemp()
    out = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {'outtmpl': out,'format': 'mp4/best/bestvideo+bestaudio','noplaylist': True,'quiet': True,'no_warnings': True,'max_filesize': 50*1024*1024,}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    return os.path.join(root, f), info.get('title','video')
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise e
    return None, None

def download_tiktok(url):
    try:
        r = requests.post("https://www.tikwm.com/api/", headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/","Content-Type":"application/x-www-form-urlencoded"}, data={"url":url,"count":12,"cursor":0,"web":1,"hd":1}, timeout=30)
        j = r.json()
        video_url = j["data"]["play"]
        tmp = tempfile.mktemp(suffix=".mp4")
        data = requests.get(video_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=60).content
        open(tmp,"wb").write(data)
        return tmp, "tiktok video"
    except:
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ابعت لينك فيديو من اي موقع وهنزلهولك:\n✅ تيك توك\n✅ انستجرام\n✅ فيسبوك\n✅ يوتيوب\n✅ تويتر X")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = re.search(r"https?://\S+", text)
    if not m:
        await update.message.reply_text("ابعت لينك صحيح")
        return
    url = m.group(0)
    msg = await update.message.reply_text("⏳ بحمل الفيديو...")
    file_path = None
    title = "فيديو"
    try:
        if "tiktok.com" in url:
            file_path, title = download_tiktok(url)
        if not file_path or not os.path.exists(file_path):
            file_path, title = download_with_ytdlp(url)
        if not file_path or not os.path.exists(file_path):
            raise Exception("مقدرتش احمل")
        await msg.edit_text("✅ ببعت الفيديو...")
        with open(file_path, "rb") as f:
            await update.message.reply_video(video=f, caption=f"{title}\nتم التحميل ✅ @{context.bot.username}", supports_streaming=True)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ مقدرتش احمل\n{e}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
            except:
                pass

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
print("Universal bot running...")
app.run_polling()
