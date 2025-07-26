from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import UPDATE_CHANNEL_URL, SUPPORT_GROUP_URL, HELP_TEXT, ABOUT_TEXT, START_UP_PIC
from database import db
from filter_plugins import force_sub
from logger import logger # Import logger

# This plugin specifically handles the /start command.
# Ensure this handler runs after plugins/refer.py if you want referral logic to apply first.

@Client.on_message(filters.command("start") & filters.private & force_sub)
async def start_command_plugin(client: Client, message: Message):
    """Handles the /start command and displays user plan info with inline keyboard."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent /start command (plugin).")
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

    # Check for referral parameter - this part will only execute if plugins/refer.py's
    # handler didn't consume the /start update. For robust referral, ensure refer.py
    # processes it first. This is just for display.
    referred_by_message = ""
    if user_data.get("referred_by"):
        referred_by_message = f"You were referred by user `{user_data['referred_by']}`!\n"


    caption_text = (
        f"Hello {message.from_user.first_name}! I am a powerful File Renamer Bot.\n\n"
        f"{referred_by_message}" # Add referral message
        "I can rename files, change thumbnails, and support custom captions.\n\n"
        f"{plan_info}\n"
        "Send me a file (document, photo, video, audio) to rename it."
    )

    if START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
        try:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=START_UP_PIC,
                caption=caption_text,
                reply_markup=keyboard
            )
            logger.info(f"User {user_id}: Sent start photo from plugin.")
        except Exception as e:
            logger.error(f"User {user_id}: Failed to send start photo from plugin: {e}", exc_info=True)
            await message.reply_text(caption_text, reply_markup=keyboard) # Fallback to text
    else:
        await message.reply_text(
            caption_text,
            reply_markup=keyboard
        )
        logger.info(f"User {user_id}: Sent start text from plugin.")
