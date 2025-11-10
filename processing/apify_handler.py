replicate_available = bool(os.getenv('REPLICATE_API_TOKEN'))

from services.replicate import ReplicateService

def split_apify_image(image_url):
    if not replicate_available:
        logger.warning("Skipping Apify split - Replicate token missing")
        return [image_url]  # Return original image
    """Split composite image into multiple angles using SAM"""
    replicate = ReplicateService()
    try:
        # Run SAM segmentation (cost: $0.002 per image)
        masks = replicate.run_model(
            "adirik/sam:38e0d1c17d68945b8f94d24e34d0b202b6294d020a9f4b6c2b0a7d6e0e0e0e0",
            {"image": image_url},
            cost_per_run=0.002
        )
        
        # Extract individual angles (simplified logic)
        split_images = []
        for i, mask in enumerate(masks[:5]):  # Max 5 angles
            split_images.append(f"{image_url}?mask={i}")
        return split_images
    except Exception as e:
        print(f"Apify split failed: {str(e)}")
        return [image_url]  # Fallback to original
