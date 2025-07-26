from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
import asyncio
from config import ADMINS
from database import db # Assuming db instance is accessible here or passed from main
from logger import logger # Import logger

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Admin-only command to broadcast a message to all users."""
    user_id = message.from_user.id
    logger.info(f"Admin {user_id} initiated broadcast.")

    if not message.reply_to_message:
        await message.reply_text("Reply to the message you want to broadcast.")
        logger.warning(f"Admin {user_id}: Broadcast failed - no replied message.")
        return

    all_users_cursor = db.users_collection.find({}) # Get all users from DB
    success_count = 0
    fail_count = 0
    
    # Count documents asynchronously. PyMongo's count_documents is synchronous,
    # so we need to run it in a thread or use aiohttp with motor/asyncio driver if available.
    # For simplicity here, we'll fetch and count, or assume a synchronous call.
    # A more robust solution for large DBs would be motor.
    try:
        total_users = await asyncio.to_thread(db.users_collection.count_documents, {})
    except Exception as e:
        logger.error(f"Error counting total users for broadcast: {e}", exc_info=True)
        total_users = "unknown" # Fallback


    status_message = await message.reply_text(f"Starting broadcast to {total_users} users...")
    logger.info(f"Admin {user_id}: Broadcast started for {total_users} users.")

    # Convert cursor to list in a thread for non-blocking iteration
    users_list = await asyncio.to_thread(list, all_users_cursor)

    for user_doc in users_list:
        user_id_to_send = user_doc["_id"]
        if user_id_to_send == message.from_user.id: # Don't send to self
            continue
        try:
            await message.reply_to_message.copy(user_id_to_send)
            success_count += 1
            await asyncio.sleep(0.1) # Small delay to avoid hitting Telegram's flood limits
        except FloodWait as e:
            logger.warning(f"FloodWait on broadcast to {user_id_to_send}: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            try:
                await message.reply_to_message.copy(user_id_to_send) # Try again after floodwait
                success_count += 1
            except Exception as retry_e:
                logger.error(f"Failed to send broadcast to {user_id_to_send} after FloodWait retry: {retry_e}")
                fail_count += 1
        except RPCError as e:
            logger.error(f"RPCError sending broadcast to user {user_id_to_send}: {e}")
            fail_count += 1
        except Exception as e:
            logger.error(f"Unexpected error broadcasting to user {user_id_to_send}: {e}", exc_info=True)
            fail_count += 1
    
    await status_message.edit_text(
        f"Broadcast completed!\n\n"
        f"✅ Sent to: {success_count} users\n"
        f"❌ Failed for: {fail_count} users"
    )
    logger.info(f"Admin {user_id}: Broadcast finished. Success: {success_count}, Failed: {fail_count}.")
