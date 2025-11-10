from PIL import Image
import requests
from io import BytesIO

def add_badges(image_url):
    """Add UK flag + fast delivery badge"""
    # Download image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    
    # Overlay UK flag (bottom-right)
    flag = Image.open("static/uk_flag.png").resize((50, 50))
    img.paste(flag, (img.width - 60, img.height - 60), flag)
    
    # Overlay delivery badge (top-right)
    badge = Image.open("static/fast_delivery.png").resize((120, 40))
    img.paste(badge, (img.width - 130, 20), badge)
    
    # Save to buffer
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    
    # Return processed URL (in real app: upload to CDN)
    return "https://processed-image-url.jpg"
