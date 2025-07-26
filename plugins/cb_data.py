from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import UPDATE_CHANNEL_URL, SUPPORT_GROUP_URL, HELP_TEXT, ABOUT_TEXT, START_UP_PIC
from filter_plugins import force_sub
from logger import logger # Import logger
import os # For checking if START_UP_PIC is a local file

# This file will centralize the handling of common callback query data
# that might otherwise clutter handlers.py or be duplicated.

@Client.on_callback_query()
async def handle_general_callback_data(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    logger.info(f"User {user_id} clicked general callback: {data}")

    # Always check force subscribe first, unless it's the 'check_force_sub' itself
    if data != "check_force_sub" and not await force_sub(None, client, callback_query):
        logger.warning(f"User {user_id} failed force_sub check on general callback {data}.")
        return

    # Handle 'check_force_sub' specifically if it was the initial trigger
    if data == "check_force_sub":
        # The force_sub filter itself will handle the message edit/reply
        # We just need to answer the callback query here.
        await callback_query.answer("Checking subscription status...", show_alert=True)
        # Re-trigger start command to refresh state if subscription is now met
        # Note: This is a simplified way; a more robust solution might re-check without re-sending full start message
        from plugins.start import start_command_plugin # Import start_command_plugin from plugins.start
        await start_command_plugin(client, callback_query.message)
        logger.info(f"User {user_id}: Processed check_force_sub callback.")
        return

    # Handle common navigation callbacks
    if data == "help_command":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="start_menu")]]
        )
        await callback_query.message.edit_text(HELP_TEXT, reply_markup=keyboard, disable_web_page_preview=True)
        await callback_query.answer()
        logger.info(f"User {user_id}: Displayed help menu.")

    elif data == "about_command":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="start_menu")]]
        )
        await callback_query.message.edit_text(ABOUT_TEXT, reply_markup=keyboard, disable_web_page_preview=True)
        await callback_query.answer()
        logger.info(f"User {user_id}: Displayed about menu.")

    elif data == "upgrade_premium":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="start_menu")]]
        )
        await callback_query.message.edit_text(
            "Here you can see our premium plans: Free, Silver, Gold, Diamond. "
            "More details coming soon!",
            reply_markup=keyboard
        )
        await callback_query.answer()
        logger.info(f"User {user_id}: Displayed upgrade premium options.")

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
        
        caption_text = f"Hello {callback_query.from_user.first_name}! I am a powerful File Renamer Bot.\n\n" \
                       "I can rename files, change thumbnails, and support custom captions.\n\n" \
                       f"{plan_info}\n" \
                       "Send me a file (document, photo, video, audio) to rename it."

        try:
            # Try to edit an existing photo message, or send a new one
            if callback_query.message.photo and START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
                # If current message is a photo and START_UP_PIC is URL, try to edit caption/markup
                await callback_query.message.edit_caption(
                    caption=caption_text,
                    reply_markup=keyboard
                )
                logger.info(f"User {user_id}: Edited start menu photo caption.")
            else:
                # If current message is not a photo, or START_UP_PIC is not URL, delete and send new
                await callback_query.message.delete()
                if START_UP_PIC and START_UP_PIC.startswith(("http", "https")):
                    await client.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=START_UP_PIC,
                        caption=caption_text,
                        reply_markup=keyboard
                    )
                    logger.info(f"User {user_id}: Sent new start menu photo.")
                else:
                    await client.send_message( # Fallback to text if no photo or URL is invalid
                        chat_id=callback_query.message.chat.id,
                        text=caption_text,
                        reply_markup=keyboard
                    )
                    logger.info(f"User {user_id}: Sent new start menu text.")
        except Exception as e:
            logger.error(f"User {user_id}: Error handling start_menu callback: {e}", exc_info=True)
            # Fallback if editing/deleting fails (e.g., message too old)
            await callback_query.message.reply_text(caption_text, reply_markup=keyboard)
        
        await callback_query.answer()
        logger.info(f"User {user_id}: Returned to start menu.")

    # Other specific callback data handlers (like "rename_file", "add_thumbnail", "cancel_operation", "add_caption")
    # are in `handlers.py` and are more tightly coupled with the active file operation state.
    # Keep them there unless you decide to refactor states into this file as well.
