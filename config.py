import os
from dotenv import load_dotenv

load_dotenv()

# --- BOT CONFIGURATION ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- FORCE SUBSCRIBE CONFIGURATION ---
# ID of the channel(s) users must join. Use username (without @) or channel ID.
# Example: FORCE_SUB_CHANNELS = ["your_channel_username", "-1001234567890"]
FORCE_SUB_CHANNELS = os.getenv("FORCE_SUB_CHANNELS", "").split(',')
FORCE_SUB_MESSAGE = "You must join our [Update Channel]({channel_link}) to use this bot!"

# ADMINS - User IDs of bot administrators for broadcast etc.
ADMINS = list(map(int, os.getenv("ADMINS", "").split(','))) if os.getenv("ADMINS") else []


# --- DATABASE CONFIGURATION ---
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
DB_NAME = os.getenv("DB_NAME", "renamer_bot_db")

# Ensure all essential configurations are present
if not all([API_ID, API_HASH, BOT_TOKEN, MONGO_DB_URI]):
    raise ValueError(
        "Missing one or more required environment variables: API_ID, API_HASH, BOT_TOKEN, MONGO_DB_URI. "
        "Please set them in a .env file or your system's environment."
    )

# Convert API_ID to integer as required by Pyrogram
try:
    API_ID = int(API_ID)
except ValueError:
    raise ValueError("API_ID must be a valid integer.")

# Session name for your Pyrogram client
SESSION_NAME = "file_renamer_bot"

# --- OTHER SETTINGS ---
DOWNLOAD_DIR = "downloads/"
THUMBNAIL_DIR = "thumbnails/"

# Custom Start-up pic (URL or file path)
START_UP_PIC = os.getenv("START_UP_PIC", "https://telegra.ph/file/a0123456789abcdefg.jpg") # Replace with your image URL

# Default plan limits (can be pulled from DB in a real app, or hardcoded here)
DEFAULT_USER_PLAN = {
    "current_plan": "free",
    "daily_upload_limit_gb": 5, # 5GB for free plan
    "daily_uploaded_gb": 0,
    "last_upload_date": None, # Will be datetime object
    "parallel_processes": 1, # Free users can do 1 parallel process
    "plan_expiry_date": None, # Will be datetime object
    "active_file_operation": None, # For storing context of ongoing rename
    "uploaded_thumbnail_id": None, # Store user's last uploaded custom thumbnail ID
    "custom_caption": None # Store user's last custom caption
}

# Add premium plan tiers (example)
PREMIUM_PLANS = {
    "silver": {
        "daily_upload_limit_gb": 20,
        "parallel_processes": 3,
        "price": "5 USD/month"
    },
    "gold": {
        "daily_upload_limit_gb": 100,
        "parallel_processes": 5,
        "price": "15 USD/month"
    }
}

# --- BOT BUTTONS/TEXTS ---
UPDATE_CHANNEL_URL = os.getenv("UPDATE_CHANNEL_URL", "https://t.me/TBOT_UPDATE") # Replace with your channel link
SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL", "https://t.me/your_support_group") # Replace with your support group link
HELP_TEXT = "This bot helps you rename files, add custom thumbnails, and more!"
ABOUT_TEXT = "This is a powerful file renamer bot created by [Your Name/Team]."
