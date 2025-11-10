from services.replicate import ReplicateService
from utils import combine_images

def generate_clothing_gallery(main_image, swatch_images):
    """Create lifestyle + swatch collage"""
    replicate = ReplicateService()
    
    # Generate swatch grid (SDXL - $0.005 per call)
    swatch_grid = replicate.run_model(
        "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        {
            "prompt": "Minimalist grid layout of clothing color swatches on white background",
            "image": main_image,
            "width": 500,
            "height": 500
        },
        cost_per_run=0.005
    )
    
    # Combine into final thumbnail
    return combine_images(main_image, swatch_grid)
