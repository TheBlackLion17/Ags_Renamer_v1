from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from logger import logger # Import logger
# BOT_TOKEN is not directly used for client.get_me(), client object handles it.

@Client.on_message(filters.command("refer") & filters.private)
async def refer_command(client: Client, message: Message):
    """Generates a referral link for the user."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent /refer.")
    user_data = db.get_user(user_id) # Ensures user exists

    # Construct bot's username
    try:
        bot_username = (await client.get_me()).username
    except Exception as e:
        logger.error(f"Error getting bot username for referral link: {e}", exc_info=True)
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
    logger.info(f"User {user_id}: Sent referral link.")


@Client.on_message(filters.command("start") & filters.private)
async def handle_referral_start(client: Client, message: Message):
    """
    Intercepts /start commands to check for referral parameters.
    This handler needs to execute *before* the main /start handler in plugins/start.py
    for the referral logic to apply. Pyrogram executes filters in order of plugin loading.
    """
    user_id = message.from_user.id
    
    if message.text and len(message.text.split()) > 1:
        param = message.text.split(None, 1)[1]
        if param.startswith("ref_"):
            try:
                referred_by_id = int(param.split("_")[1])
                logger.info(f"User {user_id} started with referral from {referred_by_id}.")

                # Prevent self-referral
                if referred_by_id == user_id:
                    await message.reply_text("You cannot refer yourself!")
                    logger.warning(f"User {user_id}: Attempted self-referral.")
                    return # Do not proceed with referral logic, but let /start handler continue
                
                referrer_user_data = db.get_user(referred_by_id) # Get referrer data
                
                if referrer_user_data:
                    current_user_data = db.get_user(user_id) # Ensure current user is in DB
                    
                    if not current_user_data.get("referred_by"): # Only set if not already referred
                        db.update_user_field(user_id, "referred_by", referred_by_id)
                        await message.reply_text(f"You were referred by user `{referred_by_id}`! Welcome!")
                        logger.info(f"User {user_id} successfully referred by {referred_by_id}.")
                        # Here, you'd add logic to give benefits to the referrer
                        # e.g., db.increment_referrer_benefits(referred_by_id, amount=1)
                    else:
                        await message.reply_text(f"You have already been referred by user `{current_user_data['referred_by']}`.")
                        logger.info(f"User {user_id} already referred by {current_user_data['referred_by']}.")
                else:
                    await message.reply_text("Invalid referral link or referrer not found.")
                    logger.warning(f"User {user_id}: Invalid referral link/referrer {referred_by_id} not found.")

            except ValueError:
                await message.reply_text("Invalid referral link format.")
                logger.warning(f"User {user_id}: Invalid referral link format: {param}.")
            except Exception as e:
                logger.error(f"Error handling referral for user {user_id} with param {param}: {e}", exc_info=True)
                await message.reply_text("An error occurred while processing your referral. Please try /start again.")
    
    # This handler finishes and implicitly allows other handlers with the same filter
    # (like the main /start in plugins.start) to execute after it.
