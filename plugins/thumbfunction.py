from pyrogram import Client, filters
from pyrogram.types import Message
from database import db
from config import THUMBNAIL_DIR
from filter_plugins import force_sub
import os

# This plugin handles setting and clearing a user's *default* custom thumbnail.

@Client.on_message(filters.command("set_thumb") & filters.private & force_sub)
async def set_default_thumbnail(client: Client, message: Message):
    """Prompts the user to send a photo for their default thumbnail."""
    user_id = message.from_user.id
    
    # Set a state in DB to indicate bot is waiting for a thumbnail image
    db.update_user_field(user_id, "active_file_operation", {"state": "waiting_for_default_thumbnail"})
    
    await message.reply_text(
        "Please send the **image** you want to set as your **default thumbnail** for all future uploads. "
        "It will be applied automatically unless you specify a different one for a specific file.\n\n"
        "Send /cancel_thumb to cancel."
    )

@Client.on_message(filters.command("clear_thumb") & filters.private & force_sub)
async def clear_default_thumbnail(client: Client, message: Message):
    """Clears the user's default custom thumbnail."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    current_thumbnail_id = user_data.get("uploaded_thumbnail_id")
    if current_thumbnail_id:
        db.update_user_field(user_id, "uploaded_thumbnail_id", None)
        await message.reply_text("Your default custom thumbnail has been cleared.")
    else:
        await message.reply_text("You don't have a default custom thumbnail set.")

@Client.on_message(filters.command("view_thumb") & filters.private & force_sub)
async def view_default_thumbnail(client: Client, message: Message):
    """Displays the user's current default custom thumbnail."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    current_thumbnail_id = user_data.get("uploaded_thumbnail_id")
    if current_thumbnail_id:
        try:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=current_thumbnail_id,
                caption="This is your current default thumbnail."
            )
        except Exception as e:
            await message.reply_text(f"Could not retrieve your thumbnail. It might have expired or been deleted from Telegram servers. Error: {e}")
            db.update_user_field(user_id, "uploaded_thumbnail_id", None) # Clear invalid ID
    else:
        await message.reply_text("You don't have a default custom thumbnail set. Use /set_thumb to set one.")


# Handler to actually receive the thumbnail image
@Client.on_message(filters.private & filters.photo & filters.incoming & force_sub)
async def handle_default_thumbnail_upload(client: Client, message: Message):
    """Processes the incoming photo when the bot is waiting for a default thumbnail."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)

    # Check if the user is in the state of setting a default thumbnail
    if user_data.get("active_file_operation", {}).get("state") == "waiting_for_default_thumbnail":
        thumbnail_file_id = message.photo.file_id
        db.update_user_field(user_id, "uploaded_thumbnail_id", thumbnail_file_id)
        db.update_user_field(user_id, "active_file_operation.state", None) # Clear state
        db.clear_active_operation(user_id) # Clear the temporary active_file_operation entirely
        await message.reply_text("Default thumbnail saved successfully! It will now be used for your uploads.")
    # This handler needs to be placed carefully in plugin loading order
    # to avoid conflicting with the main handlers.py's file handler,
    # specifically when the "waiting_for_thumbnail" state is active for a *specific* file.
    # The `active_file_operation` in the DB helps distinguish between a specific file's thumbnail
    # and a user's global default thumbnail.


@Client.on_message(filters.command("cancel_thumb") & filters.private & force_sub)
async def cancel_thumb_command(client: Client, message: Message):
    """Cancels the default thumbnail setting process."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if user_data.get("active_file_operation", {}).get("state") == "waiting_for_default_thumbnail":
        db.update_user_field(user_id, "active_file_operation.state", None)
        db.clear_active_operation(user_id) # Clear the temporary active_file_operation entirely
        await message.reply_text("Setting default thumbnail cancelled.")
    else:
        await message.reply_text("No active default thumbnail setting process to cancel.")
