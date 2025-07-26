from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_NAME
from database import db

def main():
    """Initializes and runs the Telegram bot."""
    print("Initializing Pyrogram client...")
    # Ensure MongoDB connection is attempted at startup
    if not db.client:
        print("MongoDB connection failed at startup. Exiting.")
        return # Or implement retry logic

    app = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=dict(root="plugins")
    )

    print("Bot is starting...")
    app.run()
    print("Bot has stopped.")
    db.close() # Close DB connection when bot stops

if __name__ == "__main__":
    main()
