# logger.py
import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from config import LOG_CHANNEL_ID # Assuming LOG_CHANNEL_ID is defined in config

# Basic console logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO # Default logging level for console
)

# Get the root logger
logger = logging.getLogger(__name__)

# Custom handler for Pyrogram to send logs to a Telegram channel
class TelegramLogHandler(logging.Handler):
    def __init__(self, client: Client, chat_id: int):
        super().__init__()
        self.client = client
        self.chat_id = chat_id
        # Get the current event loop. This handler will typically be setup
        # while the bot is initializing, before the loop starts running.
        # So we store the loop reference to run async tasks on it.
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()
            
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s')) # Simple format for Telegram

    def emit(self, record):
        log_entry = self.format(record)
        # We need to run this in the event loop as Pyrogram operations are async
        if self.client and self.chat_id != 0: # Check if client is initialized and chat_id is valid
            # Wrap send_message in an async task and submit to the event loop
            try:
                # Use call_soon_threadsafe if emit might be called from a different thread
                # For Pyrogram handlers, it's usually the same thread, but good practice.
                self.loop.call_soon_threadsafe(
                    asyncio.create_task, # Create a task for the coroutine
                    self.send_log_message(log_entry)
                )
            except Exception as e:
                # Fallback if cannot submit to loop (e.g., loop not running yet)
                print(f"Failed to submit log to event loop: {e} - Log: {log_entry}")

    async def send_log_message(self, log_message):
        try:
            if self.chat_id != 0: # Double check chat_id
                await self.client.send_message(self.chat_id, f"```json\n{log_message}\n```", parse_mode="MarkdownV2")
        except FloodWait as e:
            # If floodwaited, try again after the specified time
            logger.warning(f"TelegramLogHandler: FloodWait encountered ({e.value}s). Retrying log message.")
            await asyncio.sleep(e.value)
            await self.client.send_message(self.chat_id, f"```json\n{log_message}\n```", parse_mode="MarkdownV2")
        except RPCError as e:
            print(f"Failed to send log to Telegram channel (RPCError): {e}")
        except Exception as e:
            print(f"Failed to send log to Telegram channel: {e}")

# This part needs to be called after the Pyrogram client is initialized
def setup_telegram_logging(app_client: Client):
    """
    Sets up the Telegram log handler and adds it to the root logger.
    Call this function in your main.py after your Pyrogram Client is initialized.
    """
    if LOG_CHANNEL_ID != 0:
        telegram_handler = TelegramLogHandler(app_client, LOG_CHANNEL_ID)
        telegram_handler.setLevel(logging.WARNING) # Only send WARNING and above to Telegram channel
        
        # Add the handler to the root logger
        logging.getLogger().addHandler(telegram_handler) 
        
        logger.info("Telegram logging handler added.")
    else:
        logger.info("LOG_CHANNEL_ID not set in config, skipping Telegram logging.")
