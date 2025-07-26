from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from filter_plugins import force_sub

# This plugin provides commands related to custom captions.

@Client.on_message(filters.command("set_caption") & filters.private & force_sub)
async def set_caption_command(client: Client, message: Message):
    """Allows user to set a default custom caption."""
    user_id = message.from_user.id
    db.update_user_field(user_id, "active_file_operation.state", "waiting_for_global_caption") # Use a different state
    await message.reply_text(
        "Please send the **new default caption** you want to use for your uploads.\n\n"
        "You can use HTML tags (e.g., `<b>`, `<i>`, `<a href=...>`, `<code>`).\n"
        "Send /cancel_caption to cancel."
    )

@Client.on_message(filters.command("view_caption") & filters.private & force_sub)
async def view_caption_command(client: Client, message: Message):
    """Allows user to view their current default custom caption."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    current_caption = user_data.get("custom_caption")
    if current_caption:
        await message.reply_text(
            f"Your current default caption is:\n\n`{current_caption}`\n\n"
            "You can change it using /set_caption or clear it with /clear_caption."
        )
    else:
        await message.reply_text("You don't have a custom default caption set. Use /set_caption to set one.")

@Client.on_message(filters.command("clear_caption") & filters.private & force_sub)
async def clear_caption_command(client: Client, message: Message):
    """Allows user to clear their default custom caption."""
    user_id = message.from_user.id
    db.update_user_field(user_id, "custom_caption", None)
    await message.reply_text("Your default custom caption has been cleared.")

# Intercepting text messages for 'waiting_for_global_caption' state
@Client.on_message(filters.private & filters.text & filters.incoming & force_sub)
async def handle_caption_text_input(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    # Check if the user is in the state of setting a global caption
    if user_data.get("active_file_operation", {}).get("state") == "waiting_for_global_caption":
        if message.text == "/cancel_caption":
            db.update_user_field(user_id, "active_file_operation.state", None)
            await message.reply_text("Setting default caption cancelled.")
            return

        new_caption = message.text.strip()
        db.update_user_field(user_id, "custom_caption", new_caption)
        db.update_user_field(user_id, "active_file_operation.state", None) # Clear state
        await message.reply_text(f"Your new default caption has been set:\n\n`{new_caption}`")
    # This handler should be placed carefully or given a lower group/order
    # to avoid conflicting with the main handlers.py's text handler.
    # The `force_sub` filter should ensure it only processes valid users.
