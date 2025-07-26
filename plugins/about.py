from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ABOUT_TEXT, SUPPORT_GROUP_URL, UPDATE_CHANNEL_URL
from filter_plugins import force_sub
from logger import logger # Import logger

@Client.on_message(filters.command("about") & filters.private & force_sub)
async def about_command(client: Client, message: Message):
    """Handles the /about command."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent /about command.")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Update Channel", url=UPDATE_CHANNEL_URL),
                InlineKeyboardButton("Support Group", url=SUPPORT_GROUP_URL)
            ],
            [
                InlineKeyboardButton("Home", callback_data="start_menu")
            ]
        ]
    )
    await message.reply_text(ABOUT_TEXT, reply_markup=keyboard, disable_web_page_preview=True)
