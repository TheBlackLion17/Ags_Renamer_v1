from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import UPDATE_CHANNEL_URL, SUPPORT_GROUP_URL, HELP_TEXT, ABOUT_TEXT, START_UP_PIC
from database import db
from filter_plugins import force_sub

# This plugin specifically handles the /start command.
# Note: There's a start_command in handlers.py. You should decide where the primary
# /start logic resides. For modularity, it's better to move it here fully and
# remove it from handlers.py. I'll put the full logic here.

@Client.on_message(filters.command("start") & filters.private & force_sub)
async def start_command_plugin(client: Client, message: Message):
    """Handles the /start command and displays user plan info with inline keyboard."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id) # Get or create user (handled by lazyusers.py as well)

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

    # Check for referral parameter
    referred_by_message = ""
    if message.text and len(message.text.split()) > 1:
        param = message.text.split(None, 1)[1]
        if param.startswith("ref_"):
            referred_by_id = int(param.split("_")[1])
            # Ensure the referrer is not the user themselves
            if referred_by_id != user_id:
                # You might want to prevent setting 'referred_by' if already set
                current_referred_by = user_data.get("referred_by")
                if not current_referred_by:
                    db.update_user_field(user_id, "referred_by", referred_by_id)
                    referred_by_message = f"You were referred by user `{referred_by_id}`!\n"
                    # Add logic here to give benefits to the referrer if desired
                elif current_referred_by == referred_by_id:
                    referred_by_message = f"You are already referred by user `{referred_by_id}`.\n"
                else:
                    referred_by_message = f"You were referred by user `{current_referred_by}` already.\n"


    caption_text = (
        f"Hello {message.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
        f"{referred_by_message}" # Add referral message
        "I can rename files, change thumbnails, and support custom captions.\n\n"
        f"{plan_info}\n"
        "Send me a file (document, photo, video, audio) to rename it."
    )

    if START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
        await client.send_photo(
            chat_id=message.chat.id,
            photo=START_UP_PIC,
            caption=caption_text,
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            caption_text,
            reply_markup=keyboard
        )
