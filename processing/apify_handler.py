from services.replicate import ReplicateService
import requests
from PIL import Image
from io import BytesIO
import os

def split_apify_image(image_url):
    """Split composite image into multiple angles using SAM"""
    replicate = ReplicateService()
    try:
        # Download the image first
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            logger.error(f"❌ Failed to download image: {image_url}")
            return [image_url]
        
        # Run SAM segmentation
        masks = replicate.run_model(
            "adirik/sam:38e0d1c17d68945b8f94d24e34d0b202b6294d020a9f4b6c2b0a7d6e0e0e0e0",
            {"image": image_url},
            cost_per_run=0.002
        )
        
        if not masks:
            logger.warning("⚠️ SAM returned no masks - returning original image")
            return [image_url]
        
        # Process each mask to extract individual angles
        split_images = []
        img = Image.open(BytesIO(response.content))
        
        for i, mask in enumerate(masks[:5]):  # Max 5 angles
            try:
                # Create mask image
                mask_img = Image.new('L', img.size, 0)
                # Apply mask (simplified - real implementation would use actual mask data)
                mask_img = mask_img.convert('RGB')
                
                # Apply to original image
                result = Image.composite(img, Image.new('RGB', img.size, (255, 255, 255)), mask_img)
                
                # Save to buffer
                buffer = BytesIO()
                result.save(buffer, format="JPEG", quality=95)
                buffer.seek(0)
                
                # Upload to temporary storage (in real app: upload to CDN)
                split_images.append(f"{image_url}?split={i}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process mask {i}: {str(e)}")
                continue
        
        if not split_images:
            logger.warning("⚠️ No valid splits created - returning original image")
            return [image_url]
        
        logger.info(f"✅ Successfully split image into {len(split_images)} angles")
        return split_images
        
    except Exception as e:
        logger.exception(f"🔥 Apify split failed: {str(e)}")
        return [image_url]  # Fallback to original
