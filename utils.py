import os
import asyncio
from PIL import Image
from pyrogram import Client
from pyrogram.types import Message, Document, Video, Photo
from config import DOWNLOAD_DIR, THUMBNAIL_DIR

async def get_or_generate_thumbnail(client: Client, message: Message, file_data: dict, downloaded_file_path: str):
    """
    Attempts to get a thumbnail from the file data, or generates one if needed.
    Prioritizes existing thumbnails, then generates from video/document, then uses default.
    """
    user_id = message.from_user.id
    thumbnail_path = None

    # 1. Check for custom thumbnail uploaded by user for this operation
    if file_data.get("custom_thumbnail_id"):
        try:
            custom_thumb_path = await client.download_media(file_data["custom_thumbnail_id"], file_name=THUMBNAIL_DIR)
            return custom_thumb_path
        except Exception as e:
            print(f"Error downloading custom thumbnail: {e}")
            # Fallback to other methods if custom thumbnail fails

    # 2. Try to get thumbnail from Pyrogram file object (if it's a video/document with a thumbnail)
    if file_data["file_type"] in ["video", "document"]:
        file_obj = client.parse_download_media(file_data["pyrogram_file_obj"]) # Reconstruct Pyrogram object
        if file_obj and getattr(file_obj, 'thumbs', None):
            try:
                # Get the largest available thumbnail
                thumbnail_id = sorted(file_obj.thumbs, key=lambda t: t.file_size or 0, reverse=True)[0].file_id
                thumbnail_path = await client.download_media(thumbnail_id, file_name=THUMBNAIL_DIR)
                return thumbnail_path
            except Exception as e:
                print(f"Error downloading existing thumbnail from Pyrogram object: {e}")

    # 3. Generate thumbnail from video file (requires ffmpeg)
    if file_data["file_type"] == "video" and downloaded_file_path:
        output_thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{user_id}_temp_thumb.jpg")
        try:
            # Command to extract a frame from video using ffmpeg
            process = await asyncio.create_subprocess_shell(
                f"ffmpeg -i \"{downloaded_file_path}\" -ss 00:00:01 -vframes 1 \"{output_thumbnail_path}\"",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                print(f"FFmpeg thumbnail generated for {downloaded_file_path}")
                # Resize and save as JPEG to ensure compatibility and small size
                try:
                    img = Image.open(output_thumbnail_path)
                    img.thumbnail((320, 320)) # Telegram thumbnail max size is 320x320
                    img.save(output_thumbnail_path, "jpeg")
                    return output_thumbnail_path
                except Exception as e:
                    print(f"Error processing FFmpeg generated thumbnail: {e}")
            else:
                print(f"FFmpeg failed: {stderr.decode()}")
        except FileNotFoundError:
            print("FFmpeg not found. Cannot generate video thumbnails.")
        except Exception as e:
            print(f"Error generating video thumbnail with FFmpeg: {e}")

    # 4. Fallback: Use a default placeholder thumbnail
    default_thumbnail = os.path.join(THUMBNAIL_DIR, "default_thumbnail.jpg")
    if not os.path.exists(default_thumbnail):
        # Create a simple placeholder if it doesn't exist
        try:
            img = Image.new('RGB', (320, 320), color = (73, 109, 137))
            img.save(default_thumbnail)
            print(f"Created default thumbnail: {default_thumbnail}")
        except Exception as e:
            print(f"Could not create default thumbnail: {e}")
            return None # Cannot even create default, return None

    return default_thumbnail
