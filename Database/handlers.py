import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, RPCError
import asyncio
import time # Import time for start_time
from utils import get_or_generate_thumbnail
from database import db
from config import (
    UPDATE_CHANNEL_URL, SUPPORT_GROUP_URL, HELP_TEXT, ABOUT_TEXT,
    START_UP_PIC, ADMINS
)
from filter_plugins import force_sub
from progress import progress_for_pyrogram

# --- States for Custom Thumbnail/Caption ---
# Using active_file_operation in DB for conversation state
# "waiting_for_thumbnail": True/False
# "waiting_for_caption": True/False

@Client.on_message(filters.command("start") & filters.private & force_sub)
async def start_command(client: Client, message: Message):
    """Handles the /start command and displays user plan info with inline keyboard."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id) # Get or create user

    plan_info = (
        f"**Current Plan:** `{user_data['current_plan'].upper()}`\n"
        f"**Daily Upload Limit:** `{user_data['daily_upload_limit_gb']} GB`\n"
        f"**Daily Uploaded:** `{user_data['daily_uploaded_gb']:.2f} GB`\n"
        f"**Parallel Processes:** `{user_data['parallel_processes']}`\n"
    )
    if user_data["plan_expiry_date"]:
        plan_info += f"**Plan Expires:** `{user_data['plan_expiry_date'].strftime('%Y-%m-%d')}`\n"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Update Channel", url=UPDATE_CHANNEL_URL),
                InlineKeyboardButton("Support Group", url=SUPPORT_GROUP_URL)
            ],
            [
                InlineKeyboardButton("Help", callback_data="help_command"),
                InlineKeyboardButton("About", callback_data="about_command")
            ],
            [
                InlineKeyboardButton("Upgrade To Premium", callback_data="upgrade_premium")
            ]
        ]
    )

    if START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
        await client.send_photo(
            chat_id=message.chat.id,
            photo=START_UP_PIC,
            caption=f"Hello {message.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
                    "I can rename files, change thumbnails, and support custom captions.\n\n"
                    f"{plan_info}\n"
                    "Send me a file (document, photo, video, audio) to rename it.",
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            f"Hello {message.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
            "I can rename files, change thumbnails, and support custom captions.\n\n"
            f"{plan_info}\n"
            "Send me a file (document, photo, video, audio) to rename it.",
            reply_markup=keyboard
        )


@Client.on_callback_query()
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    """Handles inline keyboard button presses."""
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "check_force_sub":
        await callback_query.answer("Checking subscription status...", show_alert=True)
        await start_command(client, callback_query.message)
        return

    if not await force_sub(None, client, callback_query):
        return

    active_op = db.get_active_operation(user_id)

    if data == "help_command":
        await callback_query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="start_menu")]]))
    elif data == "about_command":
        await callback_query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="start_menu")]]))
    elif data == "upgrade_premium":
        await callback_query.message.edit_text(
            "Here you can see our premium plans: Free, Silver, Gold, Diamond. "
            "More details coming soon!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="start_menu")]])
        )
    elif data == "start_menu":
        user_data = db.get_user(user_id)
        plan_info = (
            f"**Current Plan:** `{user_data['current_plan'].upper()}`\n"
            f"**Daily Upload Limit:** `{user_data['daily_upload_limit_gb']} GB`\n"
            f"**Daily Uploaded:** `{user_data['daily_uploaded_gb']:.2f} GB`\n"
            f"**Parallel Processes:** `{user_data['parallel_processes']}`\n"
        )
        if user_data["plan_expiry_date"]:
            plan_info += f"**Plan Expires:** `{user_data['plan_expiry_date'].strftime('%Y-%m-%d')}`\n"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Update Channel", url=UPDATE_CHANNEL_URL),
                    InlineKeyboardButton("Support Group", url=SUPPORT_GROUP_URL)
                ],
                [
                    InlineKeyboardButton("Help", callback_data="help_command"),
                    InlineKeyboardButton("About", callback_data="about_command")
                ],
                [
                    InlineKeyboardButton("Upgrade To Premium", callback_data="upgrade_premium")
                ]
            ]
        )
        if START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
            try:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=callback_query.message.chat.id,
                    photo=START_UP_PIC,
                    caption=f"Hello {callback_query.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
                            "I can rename files, change thumbnails, and support custom captions.\n\n"
                            f"{plan_info}\n"
                            "Send me a file (document, photo, video, audio) to rename it.",
                    reply_markup=keyboard
                )
            except RPCError as e:
                print(f"Failed to delete message for start_menu re-send: {e}")
                await callback_query.message.edit_text(
                    f"Hello {callback_query.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
                    "I can rename files, change thumbnails, and support custom captions.\n\n"
                    f"{plan_info}\n"
                    "Send me a file (document, photo, video, audio) to rename it.",
                    reply_markup=keyboard
                )
        else:
            await callback_query.message.edit_text(
                f"Hello {callback_query.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
                "I can rename files, change thumbnails, and support custom captions.\n\n"
                f"{plan_info}\n"
                "Send me a file (document, photo, video, audio) to rename it.",
                reply_markup=keyboard
            )

    elif data == "rename_file":
        if active_op:
            db.update_user_field(user_id, "active_file_operation.state", "waiting_for_new_name")
            original_name = active_op["original_name"]
            await callback_query.message.edit_text(
                f"Okay, you want to rename `{original_name}`.\n\n"
                "Please send me the **new name** for this file."
            )
        else:
            await callback_query.message.edit_text("No file found to rename. Please send a file first.")
    elif data == "cancel_operation":
        db.clear_active_operation(user_id)
        await callback_query.message.edit_text("Operation cancelled. Send a new file to start over.")
    elif data == "add_thumbnail":
        if active_op:
            db.update_user_field(user_id, "active_file_operation.state", "waiting_for_thumbnail")
            await callback_query.message.edit_text("Please send the **image** you want to use as a custom thumbnail for this file. Send /skip_thumbnail to use default.")
        else:
            await callback_query.message.edit_text("No active file operation to add thumbnail to. Please send a file first.")
    elif data == "add_caption":
        if active_op:
            db.update_user_field(user_id, "active_file_operation.state", "waiting_for_caption")
            await callback_query.message.edit_text("Please send the **custom caption** you want to use for this file. Send /skip_caption to use default.")
        else:
            await callback_query.message.edit_text("No active file operation to add caption to. Please send a file first.")

    await callback_query.answer()


@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo) & force_sub)
async def handle_file(client: Client, message: Message):
    """Handles incoming file messages and prompts for action with inline buttons."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)

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

        db.set_active_operation(user_id, {
            "file_id": file_info.file_id,
            "original_name": original_name,
            "file_type": file_type,
            "mime_type": mime_type,
            "pyrogram_file_obj": file_info.to_dict(),
            "file_size": file_info.file_size,
            "state": None,
            "custom_thumbnail_id": None,
            "custom_caption_text": None
        })

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Rename", callback_data="rename_file"),
                    InlineKeyboardButton("Add Thumbnail", callback_data="add_thumbnail")
                ],
                [
                    InlineKeyboardButton("Add Caption", callback_data="add_caption"),
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


@Client.on_message(filters.private & filters.text & force_sub)
async def handle_text_input(client: Client, message: Message):
    """Handles text messages based on the current state (new name or custom caption)."""
    user_id = message.from_user.id
    active_op = db.get_active_operation(user_id)
    text_input = message.text.strip()

    if not active_op:
        await message.reply_text("I'm not expecting text input right now. Please send a file or use /start.")
        return

    current_state = active_op.get("state")

    if current_state == "waiting_for_new_name":
        new_name = text_input

        db.update_user_field(user_id, "active_file_operation.state", None)

        sent_message = await message.reply_text("Starting operation...")

        download_path = None
        renamed_path = None
        thumbnail_path = None

        try:
            download_start_time = time.time()
            download_path = await client.download_media(
                active_op["file_id"],
                file_name=os.path.join("downloads", active_op["original_name"]),
                progress=progress_for_pyrogram,
                progress_args=(
                    active_op["pyrogram_file_obj"].get("file_size", 1),
                    "DOWNLOADING",
                    sent_message,
                    download_start_time
                )
            )
            await sent_message.edit_text(f"Downloaded `{active_op['original_name']}`. Renaming to `{new_name}`...")

            if active_op.get("custom_thumbnail_id"):
                thumbnail_path = await client.download_media(active_op["custom_thumbnail_id"])
            else:
                thumbnail_path = await get_or_generate_thumbnail(client, message, active_op, download_path)

            download_dir = os.path.dirname(download_path)
            renamed_path = os.path.join(download_dir, new_name)

            os.rename(download_path, renamed_path)

            upload_params = {
                "chat_id": message.chat.id,
                "caption": active_op.get("custom_caption_text", f"Here is your renamed file: `{new_name}`")
            }
            if thumbnail_path:
                upload_params["thumb"] = thumbnail_path

            upload_start_time = time.time()
            if active_op["file_type"] == "document":
                await client.send_document(
                    document=renamed_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        os.path.getsize(renamed_path),
                        "UPLOADING",
                        sent_message,
                        upload_start_time
                    ),
                    **upload_params
                )
            elif active_op["file_type"] == "video":
                duration = active_op["pyrogram_file_obj"].get('duration', 0)
                width = active_op["pyrogram_file_obj"].get('width', 0)
                height = active_op["pyrogram_file_obj"].get('height', 0)
                await client.send_video(
                    video=renamed_path,
                    duration=duration,
                    width=width,
                    height=height,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        os.path.getsize(renamed_path),
                        "UPLOADING",
                        sent_message,
                        upload_start_time
                    ),
                    **upload_params
                )
            elif active_op["file_type"] == "audio":
                duration = active_op["pyrogram_file_obj"].get('duration', 0)
                title = active_op["pyrogram_file_obj"].get('title', None)
                artist = active_op["pyrogram_file_obj"].get('artist', None)
                await client.send_audio(
                    audio=renamed_path,
                    duration=duration,
                    title=title,
                    artist=artist,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        os.path.getsize(renamed_path),
                        "UPLOADING",
                        sent_message,
                        upload_start_time
                    ),
                    **upload_params
                )
            elif active_op["file_type"] == "photo":
                await client.send_photo(
                    photo=renamed_path,
                    **upload_params
                )
                await sent_message.edit_text("Uploading photo... (progress not shown)")


            await sent_message.edit_text(f"File successfully renamed and sent! New name: `{new_name}`")
            db.increment_daily_upload(user_id, active_op["file_size"])

        except FloodWait as e:
            await sent_message.edit_text(f"Telegram is asking me to wait for {e.value} seconds. Please try again later.")
        except Exception as e:
            await sent_message.edit_text(f"An error occurred: `{e}`")
        finally:
            db.clear_active_operation(user_id)
            if download_path and os.path.exists(download_path):
                os.remove(download_path)
            if renamed_path and os.path.exists(renamed_path):
                os.remove(renamed_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

            os.makedirs("downloads", exist_ok=True)
            os.makedirs("thumbnails", exist_ok=True)

    elif current_state == "waiting_for_caption":
        if text_input == "/skip_caption":
            db.update_user_field(user_id, "active_file_operation.custom_caption_text", None)
            await message.reply_text("Skipped custom caption. Default caption will be used.")
        else:
            db.update_user_field(user_id, "active_file_operation.custom_caption_text", text_input)
            await message.reply_text("Custom caption saved!")

        db.update_user_field(user_id, "active_file_operation.state", None)
        active_op = db.get_active_operation(user_id)

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Rename File", callback_data="rename_file")]
            ]
        )
        await message.reply_text(
            f"Now you can proceed with renaming. Custom caption will be: `{active_op.get('custom_caption_text', 'Default')}`",
            reply_markup=keyboard
        )

    else:
        await message.reply_text("I'm not sure what you mean. Please use the buttons or send a file.")

@Client.on_message(filters.command("skip_thumbnail") & filters.private & force_sub)
async def skip_thumbnail_command(client: Client, message: Message):
    user_id = message.from_user.id
    active_op = db.get_active_operation(user_id)
    if active_op and active_op.get("state") == "waiting_for_thumbnail":
        db.update_user_field(user_id, "active_file_operation.custom_thumbnail_id", None)
        db.update_user_field(user_id, "active_file_operation.state", None)
        await message.reply_text("Skipped custom thumbnail. Default thumbnail will be used. Now send the **new name** for the file.")
    else:
        await message.reply_text("No active thumbnail request to skip.")

@Client.on_message(filters.command("skip_caption") & filters.private & force_sub)
async def skip_caption_command(client: Client, message: Message):
    user_id = message.from_user.id
    active_op = db.get_active_operation(user_id)
    if active_op and active_op.get("state") == "waiting_for_caption":
        db.update_user_field(user_id, "active_file_operation.custom_caption_text", None)
        db.update_user_field(user_id, "active_file_operation.state", None)
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Rename File", callback_data="rename_file")]
            ]
        )
        await message.reply_text("Skipped custom caption. Default caption will be used. Now you can proceed with renaming.", reply_markup=keyboard)
    else:
        await message.reply_text("No active caption request to skip.")
