from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import asyncio
import re

TOKEN = "8571783970:AAGTeagJnjzpX7ebNrdeaQHBpLIP51zci5Y"

SOURCE_CHAT_ID = -1001680236501

TARGET_CHANNELS = [
    -1003764974352
]

media_groups = {}
media_tasks = {}


# XÓA USERNAME + LINK 
def clean_text(text):
    if not text:
        return ""

    # xóa @username
    text = re.sub(r'@\w+', '', text)

    # xóa link telegram
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r't\.me/\S+', '', text)

    # xóa khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()

    return text



# GỬI ALBUM

async def send_album(group_id, context):
    await asyncio.sleep(3)

    if group_id not in media_groups:
        return

    msgs = media_groups[group_id]

    media = []
    caption_used = False

    for m in msgs:
        cap = ""

        if not caption_used and m.caption:
            cap = clean_text(m.caption)
            caption_used = True

        if m.photo:
            media.append(
                InputMediaPhoto(
                    media=m.photo[-1].file_id,
                    caption=cap
                )
            )

        elif m.video:
            media.append(
                InputMediaVideo(
                    media=m.video.file_id,
                    caption=cap
                )
            )

    # Telegram chỉ cho tối đa 10 media
    media = media[:10]

    for channel_id in TARGET_CHANNELS:
        try:
            await context.bot.send_media_group(
                chat_id=channel_id,
                media=media
            )

            await asyncio.sleep(1)

        except Exception as e:
            print(f"Lỗi album {channel_id}: {e}")

    del media_groups[group_id]
    del media_tasks[group_id]



# XỬ LÝ TIN NHẮN

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # nhận cả bài đăng từ channel
    msg = update.message or update.channel_post

    if not msg:
        return

    print("CHAT ID:", msg.chat_id)

    # chỉ nhận từ kênh nguồn
    if msg.chat_id != SOURCE_CHAT_ID:
        return


    
    # ALBUM
    
    if msg.media_group_id:
        group_id = msg.media_group_id

        if group_id not in media_groups:
            media_groups[group_id] = []

        media_groups[group_id].append(msg)

        # reset timer nếu có media mới
        if group_id in media_tasks:
            media_tasks[group_id].cancel()

        media_tasks[group_id] = asyncio.create_task(
            send_album(group_id, context)
        )

        return

    
    # TIN THƯỜNG
    
    for channel_id in TARGET_CHANNELS:
        try:

            # TEXT
            if msg.text:
                await context.bot.send_message(
                    chat_id=channel_id,
                    text=clean_text(msg.text)
                )

            # PHOTO
            elif msg.photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=msg.photo[-1].file_id,
                    caption=clean_text(msg.caption)
                )

            # VIDEO
            elif msg.video:
                await context.bot.send_video(
                    chat_id=channel_id,
                    video=msg.video.file_id,
                    caption=clean_text(msg.caption)
                )

            # DOCUMENT
            elif msg.document:
                await context.bot.send_document(
                    chat_id=channel_id,
                    document=msg.document.file_id,
                    caption=clean_text(msg.caption)
                )

            await asyncio.sleep(1)

        except Exception as e:
            print(f"Lỗi gửi tới {channel_id}: {e}")



# CHẠY BOT

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(
    MessageHandler(filters.ALL, handle_message)
)

if __name__ == "__main__":
    print("Bot đang chạy...")
    app.run_polling()
