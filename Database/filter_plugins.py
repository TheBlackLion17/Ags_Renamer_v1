from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNELS, FORCE_SUB_MESSAGE
import asyncio

async def force_subscribe_filter(_, client: Client, update: Message | CallbackQuery):
    """
    Custom filter to check if a user is subscribed to the required channels.
    Applies to both messages and callback queries.
    """
    if not FORCE_SUB_CHANNELS or not any(channel.strip() for channel in FORCE_SUB_CHANNELS):
        return True # No force subscribe required

    user_id = update.from_user.id

    # Check if the user is the bot's owner (admin) - admins bypass force sub
    from config import ADMINS
    if user_id in ADMINS:
        return True

    not_joined_channels = []

    for channel in FORCE_SUB_CHANNELS:
        if not channel: # Skip empty strings from split
            continue
        try:
            # Check if user is a member or admin
            status = await client.get_chat_member(channel.strip(), user_id)
            if status.status in ["member", "administrator", "creator"]:
                continue
            else:
                not_joined_channels.append(channel.strip())
        except UserNotParticipant:
            not_joined_channels.append(channel.strip())
        except Exception as e:
            print(f"Error checking channel membership for {channel}: {e}")
            not_joined_channels.append(channel.strip()) # Treat error as not joined for safety

    if not not_joined_channels:
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
        except Exception:
            channel_link = f"https://t.me/{channel_id_or_username}"
            channel_title = channel_id_or_username

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
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(
            response_text.format(channel_link=channel_link),
            reply_markup=InlineKeyboardMarkup([keyboard_buttons]),
            disable_web_page_preview=True
        )
        await update.answer(cache_time=60) # Answer callback query

    return False # User is not subscribed

# Instantiate the filter
force_sub = filters.create(force_subscribe_filter)
