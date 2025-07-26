from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import PREMIUM_PLANS, SUPPORT_GROUP_URL # Ensure SUPPORT_GROUP_URL is imported for "Contact Support"
from filter_plugins import force_sub
from logger import logger # Import logger

@Client.on_message(filters.command("upgrade") & filters.private & force_sub)
async def upgrade_command(client: Client, message: Message):
    """Displays premium upgrade options to the user."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent /upgrade.")

    upgrade_text = "**💎 Upgrade Your Plan! 💎**\n\n" \
                   "Unlock more features and higher limits by upgrading to a premium plan.\n\n" \
                   "Here are our available plans:\n\n"

    for plan_name, details in PREMIUM_PLANS.items():
        upgrade_text += f"**✨ {plan_name.upper()} Plan:**\n" \
                        f"  - Daily Upload Limit: `{details['daily_upload_limit_gb']} GB`\n" \
                        f"  - Parallel Processes: `{details['parallel_processes']}`\n" \
                        f"  - Price: `{details['price']}`\n\n"
    
    upgrade_text += f"Contact our [support]({SUPPORT_GROUP_URL}) to subscribe!" # Link to a payment gateway/support

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Contact Support", url=SUPPORT_GROUP_URL) 
            ],
            [
                InlineKeyboardButton("My Current Plan", callback_data="myplan_command"), # Link to myplan
                InlineKeyboardButton("Home", callback_data="start_menu")
            ]
        ]
    )

    await message.reply_text(upgrade_text, reply_markup=keyboard, disable_web_page_preview=True)
    logger.info(f"User {user_id}: Displayed upgrade options.")
