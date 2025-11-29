import asyncio
import pyrogram
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from aiohttp import web
import motor.motor_asyncio # MongoDB লাইব্রেরি

# --- কনফিগারেশন ---
API_ID = 31901417  
API_HASH = "28895c2d7e9f19d3c1bb3da41d392ba2"
BOT_TOKEN = "8452576663:AAG-fJQrq6_SXCw1l1Oj3I2ZI8VEUxPVPLY"
ADMIN_ID = 6201674394  # <--- আপনার টেলিগ্রাম আইডি
AUTO_DELETE_TIME = 3600

# ⚠️ MongoDB লিংক (পাসওয়ার্ড বসাতে ভুলবেন না)
MONGODB_URL = "mongodb+srv://Jk_movee:pradip123@cluster0.mongodb.net/?retryWrites=true&w=majority"

# --- মঙ্গোডিবি সেটআপ ---
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = mongo_client["movie_bot_db"]
collection = db["files"]

# --- বট সেটআপ ---
app = Client("my_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ওয়েব সার্ভার ---
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Running Successfully!")
    app_web = web.Application()
    app_web.router.add_get("/", handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# --- ১. ফাইল স্টোর করা (MongoDB তে সেভ হবে) ---
@app.on_message(filters.command("store") & filters.private)
async def store_file(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply_text("❌ Sorry! Only the admin can add files.")
        return

    reply = message.reply_to_message
    if not reply:
        await message.reply_text("Please reply to a video or file.")
        return

    media = reply.video or reply.document
    if not media:
        await message.reply_text("❌ Not a valid file.")
        return

    file_id = media.file_id
    
    # ডাটাবেসে চেক করা হচ্ছে কতগুলো ফাইল আছে
    total_files = await collection.count_documents({})
    unique_code = f"movie_{total_files + 1}"
    
    # ডাটাবেসে সেভ করা
    await collection.insert_one({"code": unique_code, "file_id": file_id})
    
    bot_username = (await client.get_me()).username
    shareable_link = f"https://t.me/{bot_username}?start={unique_code}"
    
    await message.reply_text(f"✅ Link:\n`{shareable_link}`", disable_web_page_preview=True)

# --- ২. ফাইল দেওয়া (MongoDB থেকে খুঁজে আনবে) ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    if len(message.command) > 1:
        payload = message.command[1]
        
        # ডাটাবেস থেকে খোঁজা হচ্ছে
        file_data = await collection.find_one({"code": payload})
        
        if file_data:
            file_id = file_data["file_id"]
            msg = await message.reply_text("📥 Processing...")
            
            caption_text = f"🎬 Enjoy!\n⚠️ Auto-delete in {AUTO_DELETE_TIME}s.\n🔥 Join: @Rock_pro1"

            try:
                sent_msg = await message.reply_video(video=file_id, caption=caption_text)
            except:
                sent_msg = await message.reply_document(document=file_id, caption=caption_text)
            
            await msg.delete()
            await asyncio.sleep(AUTO_DELETE_TIME)
            try:
                await sent_msg.delete()
            except:
                pass
        else:
            await message.reply_text("❌ Invalid link.")
    else:
        await message.reply_text("👋 Welcome!")

# --- মেইন ফাংশন ---
async def main():
    await app.start()
    print("বট চালু হয়েছে...")
    await web_server()
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
            
