from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
import asyncio
from config import ADMINS
from database import db # Assuming db instance is accessible here or passed from main

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Admin-only command to broadcast a message to all users."""
    if not message.reply_to_message:
        await message.reply_text("Reply to the message you want to broadcast.")
        return

    all_users_cursor = db.users_collection.find({}) # Get all users from DB
    success_count = 0
    fail_count = 0
    total_users = await db.users_collection.count_documents({}) # Asynchronous count

    status_message = await message.reply_text(f"Starting broadcast to {total_users} users...")

    for user_doc in await asyncio.to_thread(list, all_users_cursor): # Convert cursor to list in a thread for non-blocking
        user_id = user_doc["_id"]
        if user_id == message.from_user.id: # Don't send to self
            continue
        try:
            await message.reply_to_message.copy(user_id)
            success_count += 1
            await asyncio.sleep(0.1) # Small delay to avoid hitting Telegram's flood limits
        except FloodWait as e:
            print(f"FloodWait on broadcast: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user_id) # Try again after floodwait
            success_count += 1
        except RPCError as e:
            print(f"Error sending broadcast to user {user_id}: {e}")
            fail_count += 1
        except Exception as e:
            print(f"Unexpected error broadcasting to user {user_id}: {e}")
            fail_count += 1

    await status_message.edit_text(
        f"Broadcast completed!\n\n"
        f"✅ Sent to: {success_count} users\n"
        f"❌ Failed for: {fail_count} users"
    )
