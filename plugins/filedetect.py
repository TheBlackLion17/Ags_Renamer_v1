from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import DOWNLOAD_DIR, THUMBNAIL_DIR
from filter_plugins import force_sub
import os

# This plugin specifically focuses on detecting incoming files and initiating the process.

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo) & force_sub)
async def detect_file_and_prompt(client: Client, message: Message):
    """Detects an incoming file and prompts the user for action."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)

    # Check if a thumbnail is being sent as part of a previous operation
    # This check is crucial to avoid re-triggering the file detection flow
    # when a user is in the "waiting_for_thumbnail" state.
    active_op = db.get_active_operation(user_id)
    if active_op and active_op.get("state") == "waiting_for_thumbnail":
        if message.photo:
            db.update_user_field(user_id, "active_file_operation.custom_thumbnail_id", message.photo.file_id)
            db.update_user_field(user_id, "active_file_operation.state", None) # Clear state
            await message.reply_text("Custom thumbnail received! Now send the **new name** for the file.")
            return
        else:
            await message.reply_text("That's not an image. Please send an **image** for the thumbnail, or /skip_thumbnail.")
            return


    file_type = None
    file_info = None

    if message.document:
        file_info = message.document
        file_type = "document"
    elif message.video:
        file_info = message.video
        file_type = "video"
    elif message.audio:
        file_info = message.audio
        file_type = "audio"
    elif message.photo:
        file_info = sorted(message.photo, key=lambda p: p.file_size or 0, reverse=True)[0]
        file_type = "photo"

    if file_info:
        file_size_gb = (file_info.file_size or 0) / (1024**3)
        if (user_data["daily_uploaded_gb"] + file_size_gb) > user_data["daily_upload_limit_gb"]:
            await message.reply_text(
                f"Your daily upload limit of `{user_data['daily_upload_limit_gb']} GB` has been reached. "
                "Please upgrade your plan or try again tomorrow."
            )
            return

        original_name = getattr(file_info, "file_name", f"untitled_{file_type}")
        mime_type = getattr(file_info, "mime_type", "application/octet-stream")

        # Store file data in the database for the active operation
        db.set_active_operation(user_id, {
            "file_id": file_info.file_id,
            "original_name": original_name,
            "file_type": file_type,
            "mime_type": mime_type,
            "pyrogram_file_obj": file_info.to_dict(), # Store full Pyrogram object data
            "file_size": file_info.file_size,
            "state": None, # No specific state yet, just stored file info
            "custom_thumbnail_id": None,
            "custom_caption_text": user_data.get("custom_caption") # Use user's default caption if set
        })

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Rename", callback_data="rename_file"),
                    InlineKeyboardButton("Add Thumbnail", callback_data="add_thumbnail")
                ],
                [
                    InlineKeyboardButton("Add Caption", callback_data="add_caption"), # To override default/set specific
                    InlineKeyboardButton("Cancel", callback_data="cancel_operation")
                ]
            ]
        )
        
        await message.reply_text(
            f"What do you want me to do with this file?\n\n"
            f"File Name :- `{original_name}`\n"
            f"File Size :- `{file_info.file_size / (1024 * 1024):.2f} MB`\n"
            f"Dc ID :- `{file_info.dc_id}`",
            reply_markup=keyboard
        )
    else:
        await message.reply_text("I can only process documents, videos, audio, and photos.")
