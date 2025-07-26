import time
from pyrogram.types import Message
import math

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
    if round(diff % 10.00) == 0 or current == total: # Update every 10 seconds or when complete
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff)
        time_to_completion = round((total - current) / speed)

        # Calculate human-readable sizes
        converted_current = humanbytes(current)
        converted_total = humanbytes(total)

        # Calculate human-readable speed
        converted_speed = humanbytes(speed)

        # Create progress bar
        progress_bar = "".join([
            '█' for i in range(math.floor(percentage / 10))
        ])
        empty_bar = "".join([
            ' ' for i in range(10 - math.floor(percentage / 10))
        ])

        progress_string = (
            f"{ud_type}\n\n"
            f"**{progress_bar}{empty_bar}** `{percentage:.2f}%`\n\n"
            f"**Progress**: `{converted_current}` of `{converted_total}`\n"
            f"**Speed**: `{converted_speed}/s`\n"
            f"**ETA**: `{TimeFormatter(time_to_completion)}`\n"
            f"**Elapsed**: `{TimeFormatter(elapsed_time)}`"
        )

        try:
            await message.edit_text(
                text=progress_string
            )
        except Exception as e:
            pass # Suppress frequent errors if message doesn't need modification

def humanbytes(size):
    """Converts bytes to human-readable format."""
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(seconds):
    """Converts seconds to human-readable time format."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp.rstrip(', ')
