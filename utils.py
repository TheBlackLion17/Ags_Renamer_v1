import os
import asyncio
from PIL import Image
from pyrogram import Client
from pyrogram.types import Message, Document, Video, Photo
from config import DOWNLOAD_DIR, THUMBNAIL_DIR
from logger import logger # Import logger

async def get_or_generate_thumbnail(client: Client, message: Message, file_data: dict, downloaded_file_path: str):
    """
    Attempts to get a thumbnail from the file data, or generates one if needed.
    Prioritizes existing thumbnails, then generates from video/document, then uses default.
    """
    user_id = message.from_user.id
    thumbnail_path = None
    
    # Ensure directories exist
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    # 1. Check for custom thumbnail uploaded by user for this operation
    if file_data.get("custom_thumbnail_id"):
        logger.info(f"User {user_id}: Attempting to download custom thumbnail.")
        try:
            custom_thumb_path = await client.download_media(file_data["custom_thumbnail_id"], file_name=THUMBNAIL_DIR)
            logger.info(f"User {user_id}: Custom thumbnail downloaded: {custom_thumb_path}")
            return custom_thumb_path
        except Exception as e:
            logger.error(f"User {user_id}: Error downloading custom thumbnail: {e}", exc_info=True)
            # Fallback to other methods if custom thumbnail fails

    # 2. Try to get thumbnail from Pyrogram file object (if it's a video/document with a thumbnail)
    if file_data["file_type"] in ["video", "document"]:
        # Reconstruct Pyrogram object from dict to access attributes like thumbs
        # Note: This might not fully re-instantiate complex Pyrogram objects perfectly
        # A more robust way might be to pass the actual Pyrogram object initially.
        # For thumbs, it usually works as it's basic data.
        file_obj = None
        if file_data.get("pyrogram_file_obj") and isinstance(file_data["pyrogram_file_obj"], dict):
            if file_data["file_type"] == "video":
                file_obj = Video(**file_data["pyrogram_file_obj"])
            elif file_data["file_type"] == "document":
                file_obj = Document(**file_data["pyrogram_file_obj"])
            # Add other types if necessary
        
        if file_obj and getattr(file_obj, 'thumbs', None):
            logger.info(f"User {user_id}: Attempting to download existing thumbnail from file object.")
            try:
                # Get the largest available thumbnail
                thumbnail_id = sorted(file_obj.thumbs, key=lambda t: t.file_size or 0, reverse=True)[0].file_id
                thumbnail_path = await client.download_media(thumbnail_id, file_name=THUMBNAIL_DIR)
                logger.info(f"User {user_id}: Existing thumbnail downloaded: {thumbnail_path}")
                return thumbnail_path
            except Exception as e:
                logger.error(f"User {user_id}: Error downloading existing thumbnail from Pyrogram object: {e}", exc_info=True)

    # 3. Generate thumbnail from video file (requires ffmpeg)
    if file_data["file_type"] == "video" and downloaded_file_path and os.path.exists(downloaded_file_path):
        output_thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{user_id}_temp_thumb.jpg")
        logger.info(f"User {user_id}: Attempting to generate thumbnail from video using FFmpeg.")
        try:
            # Command to extract a frame from video using ffmpeg
            process = await asyncio.create_subprocess_shell(
                f"ffmpeg -i \"{downloaded_file_path}\" -ss 00:00:01 -vframes 1 \"{output_thumbnail_path}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                logger.info(f"User {user_id}: FFmpeg thumbnail generated for {downloaded_file_path}")
                # Resize and save as JPEG to ensure compatibility and small size
                try:
                    img = Image.open(output_thumbnail_path)
                    img.thumbnail((320, 320)) # Telegram thumbnail max size is 320x320
                    img.save(output_thumbnail_path, "jpeg")
                    logger.info(f"User {user_id}: FFmpeg generated thumbnail processed and saved.")
                    return output_thumbnail_path
                except Exception as e:
                    logger.error(f"User {user_id}: Error processing FFmpeg generated thumbnail: {e}", exc_info=True)
            else:
                logger.error(f"User {user_id}: FFmpeg failed for {downloaded_file_path}: {stderr.decode()}")
        except FileNotFoundError:
            logger.warning(f"User {user_id}: FFmpeg not found. Cannot generate video thumbnails.")
        except Exception as e:
            logger.error(f"User {user_id}: Error generating video thumbnail with FFmpeg: {e}", exc_info=True)

    # 4. Fallback: Use a default placeholder thumbnail
    default_thumbnail = os.path.join(THUMBNAIL_DIR, "default_thumbnail.jpg")
    logger.info(f"User {user_id}: Falling back to default thumbnail.")
    if not os.path.exists(default_thumbnail):
        # Create a simple placeholder if it doesn't exist
        try:
            img = Image.new('RGB', (320, 320), color = (73, 109, 137))
            img.save(default_thumbnail)
            logger.info(f"Created default thumbnail: {default_thumbnail}")
        except Exception as e:
            logger.error(f"User {user_id}: Could not create default thumbnail: {e}", exc_info=True)
            return None # Cannot even create default, return None

    return default_thumbnail
