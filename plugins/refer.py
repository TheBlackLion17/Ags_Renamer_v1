from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import BOT_TOKEN # Assuming BOT_TOKEN can be used to construct bot username
import os # For getting bot username from env or client

@Client.on_message(filters.command("refer") & filters.private)
async def refer_command(client: Client, message: Message):
    """Generates a referral link for the user."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id) # Ensures user exists

    # Construct bot's username
    bot_username = (await client.get_me()).username
    if not bot_username:
        await message.reply_text("Could not get bot username. Referral link not available.")
        return

    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    referral_text = (
        f"**Invite your friends to use this bot and earn benefits!**\n\n"
        f"Share your unique referral link:\n`{referral_link}`\n\n"
        "*(Benefits for referring users are not yet implemented but will be added soon!)*"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Check%20out%20this%20awesome%20Telegram%20bot!")
            ],
            [
                InlineKeyboardButton("Home", callback_data="start_menu")
            ]
        ]
    )

    await message.reply_text(referral_text, reply_markup=keyboard, disable_web_page_preview=True)


@Client.on_message(filters.command("start") & filters.private)
async def handle_referral_start(client: Client, message: Message):
    """
    Intercepts /start commands to check for referral parameters.
    This needs to run *before* the main /start handler if possible,
    or be integrated carefully.
    """
    if message.text and len(message.text.split()) > 1:
        param = message.text.split(None, 1)[1]
        if param.startswith("ref_"):
            referred_by_id = int(param.split("_")[1])
            referrer_user_data = db.get_user(referred_by_id)
            
            if referrer_user_data and referred_by_id != message.from_user.id:
                # Store the referrer ID for the new user
                db.update_user_field(message.from_user.id, "referred_by", referred_by_id)
                await message.reply_text(f"You were referred by user `{referred_by_id}`! Welcome!")
                # Here, you'd add logic to give benefits to the referrer
                # e.g., db.increment_referrer_benefits(referred_by_id)
            else:
                await message.reply_text("Invalid referral link or you tried to refer yourself.")
    
    # Crucially, let the main /start handler (in handlers.py) continue its work
    # if this handler doesn't fully process the command or if there's no referral.
    # Pyrogram processes handlers based on filter order. If this is a plugin,
    # it needs to be loaded appropriately or you need to re-think how /start is handled.
    # For now, it's illustrative.
