from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from database import db
import asyncio

@Client.on_message(filters.command("stats") & filters.user(ADMINS) & filters.private)
async def stats_command(client: Client, message: Message):
    """Admin-only command to show bot statistics."""
    total_users = await db.users_collection.count_documents({})
    
    # You can add more stats here, e.g., active users, premium users, etc.
    # For now, just total users.

    stats_text = f"**📊 Bot Statistics 📊**\n\n" \
                 f"**Total Users:** `{total_users}`\n" \
                 f"**Active Operations:** (Not implemented yet)" # You'd need to track this in your DB

    await message.reply_text(stats_text)


@Client.on_message(filters.command("ping") & filters.user(ADMINS) & filters.private)
async def ping_command(client: Client, message: Message):
    """Admin-only command to check bot's responsiveness."""
    start_time = asyncio.get_event_loop().time()
    sent_message = await message.reply_text("Pinging...")
    end_time = asyncio.get_event_loop().time()
    ping_time = round((end_time - start_time) * 1000, 2) # in ms
    await sent_message.edit_text(f"Pong! 🏓 `{ping_time}ms`")

# You can add more admin commands here as needed
# For example, commands to manage user plans, broadcast messages (already in broadcast.py),
# ban/unban users, etc.
