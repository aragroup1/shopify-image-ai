from services.replicate import ReplicateService
from PIL import Image
import requests
from io import BytesIO
import numpy as np

def generate_clothing_gallery(main_image, swatch_images):
    """Create lifestyle + swatch collage for clothing products"""
    replicate = ReplicateService()
    
    try:
        # Generate lifestyle image using original image as reference
        lifestyle_image = replicate.run_model(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            {
                "prompt": "Professional lifestyle photo of model wearing this clothing item, studio lighting, high quality, commercial product photography",
                "image": main_image
            },
            cost_per_run=0.008
        )
        
        # Generate swatch grid
        swatch_grid = replicate.run_model(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            {
                "prompt": "Minimalist grid layout of clothing color swatches on white background, professional product photography",
                "image": main_image
            },
            cost_per_run=0.005
        )
        
        # Create final collage (simplified - real implementation would use PIL to combine)
        logger.info("✅ Generated lifestyle image and swatch grid")
        return [lifestyle_image, swatch_grid]
        
    except Exception as e:
        logger.exception(f"🔥 Clothing gallery generation failed: {str(e)}")
        # Fallback to original images
        return [main_image] + swatch_images[:4]
