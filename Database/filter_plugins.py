from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNELS, FORCE_SUB_MESSAGE, ADMINS
import asyncio
from logger import logger # Import logger

async def force_subscribe_filter(_, client: Client, update: Message | CallbackQuery):
    """
    Custom filter to check if a user is subscribed to the required channels.
    Applies to both messages and callback queries.
    """
    if not FORCE_SUB_CHANNELS or not any(channel.strip() for channel in FORCE_SUB_CHANNELS):
        logger.debug("No force subscribe channels configured. Skipping check.")
        return True # No force subscribe required

    user_id = update.from_user.id
    
    # Check if the user is the bot's owner (admin) - admins bypass force sub
    if user_id in ADMINS:
        logger.debug(f"User {user_id} is an admin, bypassing force subscribe.")
        return True

    not_joined_channels = []
    
    for channel in FORCE_SUB_CHANNELS:
        channel = channel.strip()
        if not channel: # Skip empty strings from split
            continue
        try:
            # Check if user is a member or admin
            status = await client.get_chat_member(channel, user_id)
            if status.status in ["member", "administrator", "creator"]:
                logger.debug(f"User {user_id} is a member of {channel}.")
                continue
            else:
                not_joined_channels.append(channel)
                logger.info(f"User {user_id} is NOT a member of {channel}.")
        except UserNotParticipant:
            not_joined_channels.append(channel)
            logger.info(f"User {user_id} is NOT a member of {channel} (UserNotParticipant).")
        except Exception as e:
            logger.error(f"Error checking channel membership for {channel} for user {user_id}: {e}", exc_info=True)
            not_joined_channels.append(channel) # Treat error as not joined for safety

    if not not_joined_channels:
        logger.debug(f"User {user_id} is subscribed to all required channels.")
        return True # User is subscribed to all required channels

    # If not subscribed, send force subscribe message with join buttons
    keyboard_buttons = []
    response_text = FORCE_SUB_MESSAGE + "\n\n"
    for channel_id_or_username in not_joined_channels:
        # Try to fetch chat info to get a proper link if it's an ID
        try:
            chat = await client.get_chat(channel_id_or_username)
            if chat.invite_link:
                channel_link = chat.invite_link
                channel_title = chat.title
            else:
                # Fallback for private channels without invite link or if fetching fails
                channel_link = f"https://t.me/{channel_id_or_username}"
                channel_title = channel_id_or_username
            logger.debug(f"Resolved channel {channel_id_or_username} to link: {channel_link}")
        except Exception as e:
            logger.warning(f"Could not get chat info for {channel_id_or_username}: {e}. Using raw link.")
            channel_link = f"https://t.me/{channel_id_or_username}"
            channel_title = channel_id_or_username # Use raw name as title

        keyboard_buttons.append(
            InlineKeyboardButton(f"Join {channel_title}", url=channel_link)
        )
    
    # Add a "Try Again" button to re-check subscription
    keyboard_buttons.append(InlineKeyboardButton("✅ I've Joined", callback_data="check_force_sub"))

    if isinstance(update, Message):
        await update.reply_text(
            response_text.format(channel_link=channel_link),
            reply_markup=InlineKeyboardMarkup([keyboard_buttons]),
            disable_web_page_preview=True
        )
        logger.info(f"User {user_id} was prompted for force subscribe (message).")
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(
            response_text.format(channel_link=channel_link),
            reply_markup=InlineKeyboardMarkup([keyboard_buttons]),
            disable_web_page_preview=True
        )
        await update.answer(cache_time=60) # Answer callback query
        logger.info(f"User {user_id} was prompted for force subscribe (callback).")

    return False # User is not subscribed

# Instantiate the filter
force_sub = filters.create(force_subscribe_filter)
