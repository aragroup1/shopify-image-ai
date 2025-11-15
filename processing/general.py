from PIL import Image
import requests
from io import BytesIO
import os

def add_badges(image_url):
    """Add UK flag + fast delivery badge to standard products"""
    try:
        # Download image
        response = requests.get(image_url, timeout=15)
        if response.status_code != 200:
            logger.error(f"❌ Failed to download image: {image_url}")
            return image_url
        
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Add UK flag (bottom-right)
        try:
            flag_path = os.path.join(os.path.dirname(__file__), '../static/uk_flag.png')
            flag = Image.open(flag_path).convert("RGBA")
            flag = flag.resize((50, 50))
            
            # Position: bottom-right with 10px padding
            position = (img.width - flag.width - 10, img.height - flag.height - 10)
            img.paste(flag, position, flag)
        except Exception as e:
            logger.warning(f"⚠️ Failed to add UK flag: {str(e)}")
        
        # Add delivery badge (top-right)
        try:
            badge_path = os.path.join(os.path.dirname(__file__), '../static/fast_delivery.png')
            badge = Image.open(badge_path).convert("RGBA")
            badge = badge.resize((120, 40))
            
            # Position: top-right with 10px padding
            position = (img.width - badge.width - 10, 10)
            img.paste(badge, position, badge)
        except Exception as e:
            logger.warning(f"⚠️ Failed to add delivery badge: {str(e)}")
        
        # Save to buffer
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        
        # In real app: upload to CDN and return URL
        logger.info("✅ Added UK flag and delivery badge")
        return f"{image_url}?processed=true"
        
    except Exception as e:
        logger.exception(f"🔥 Badge addition failed: {str(e)}")
        return image_url  # Return original on failure
