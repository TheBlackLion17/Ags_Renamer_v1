from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import PREMIUM_PLANS
from filter_plugins import force_sub
import datetime

@Client.on_message(filters.command("myplan") & filters.private & force_sub)
async def myplan_command(client: Client, message: Message):
    """Displays the user's current plan information."""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)

    plan_info_text = (
        f"**✨ Your Current Plan ✨**\n\n"
        f"**Plan Name:** `{user_data['current_plan'].upper()}`\n"
        f"**Daily Upload Limit:** `{user_data['daily_upload_limit_gb']} GB`\n"
        f"**Daily Uploaded:** `{user_data['daily_uploaded_gb']:.2f} GB`\n"
        f"**Parallel Processes:** `{user_data['parallel_processes']}`\n"
    )

    if user_data.get("plan_expiry_date"):
        plan_info_text += f"**Plan Expires:** `{user_data['plan_expiry_date'].strftime('%Y-%m-%d %H:%M:%S')}`\n"
    else:
        plan_info_text += "**Plan Expiry:** `N/A` (Free Plan)\n"
    
    # Calculate remaining daily limit
    remaining_limit = user_data['daily_upload_limit_gb'] - user_data['daily_uploaded_gb']
    plan_info_text += f"**Remaining Daily Limit:** `{remaining_limit:.2f} GB`\n"


    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Upgrade Plan", callback_data="upgrade_premium")
            ],
            [
                InlineKeyboardButton("Home", callback_data="start_menu")
            ]
        ]
    )

    await message.reply_text(plan_info_text, reply_markup=keyboard)
