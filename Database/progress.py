import time
from pyrogram.types import Message
import math
from logger import logger # Import logger

async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message: Message,
    start_time
):
    """
    Callback function to update a message with download/upload progress.
    Args:
        current (int): Bytes transferred so far.
        total (int): Total bytes of the file.
        ud_type (str): Type of operation (e.g., "Downloading", "Uploading").
        message (Message): The Pyrogram message object to update.
        start_time (float): Time when the operation started (time.time()).
    """
    now = time.time()
    diff = now - start_time
    # Update every 5 seconds or when complete, to avoid flooding Telegram API
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        
        if diff > 0: # Avoid division by zero
            speed = current / diff
        else:
            speed = 0 # No speed yet if no time elapsed

        elapsed_time = round(diff)
        
        # Calculate time to completion, handle cases where speed is 0
        if speed > 0:
            time_to_completion = round((total - current) / speed)
        else:
            time_to_completion = 0 # Cannot estimate if no speed

        # Calculate human-readable sizes
        converted_current = humanbytes(current)
        converted_total = humanbytes(total)

        # Calculate human-readable speed
        converted_speed = humanbytes(speed)

        # Create progress bar
        progress_bar_length = 10
        filled_blocks = math.floor(percentage / 100 * progress_bar_length)
        empty_blocks = progress_bar_length - filled_blocks
        
        progress_bar = "".join(['█' for _ in range(filled_blocks)])
        empty_bar = "".join([' ' for _ in range(empty_blocks)])
        
        progress_string = (
            f"**{ud_type}**\n\n"
            f"**Progress**: `{progress_bar}{empty_bar}` `{percentage:.2f}%`\n"
            f"**Size**: `{converted_current}` / `{converted_total}`\n"
            f"**Speed**: `{converted_speed}/s`\n"
            f"**ETA**: `{TimeFormatter(time_to_completion)}`\n"
            f"**Elapsed**: `{TimeFormatter(elapsed_time)}`"
        )
        
        try:
            await message.edit_text(
                text=progress_string
            )
        except Exception as e:
            # Suppress frequent errors if message doesn't need modification
            # or if Telegram API limits are hit, but log for debugging
            logger.debug(f"Error updating progress message: {e}") 

def humanbytes(size):
    """Converts bytes to human-readable format."""
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(seconds):
    """Converts seconds to human-readable time format."""
    if seconds <= 0:
        return "0s"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp.rstrip(', ')
