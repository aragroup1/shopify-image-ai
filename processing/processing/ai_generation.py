from services.replicate import ReplicateService

def generate_missing_images(product_type, base_image, count_needed):
    """Generate missing images ONLY after approval"""
    replicate = ReplicateService()
    new_images = []
    
    for i in range(count_needed):
        if "clothing" in product_type.lower():
            # Generate lifestyle image ($0.008 per image)
            img = replicate.run_model(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                {
                    "prompt": f"Professional lifestyle photo of model wearing {product_type}, studio lighting",
                    "image": base_image
                },
                cost_per_run=0.008
            )
        else:
            # Generate new angle ($0.004 per image)
            img = replicate.run_model(
                "lllyasviel/controlnet:1a0c51af1e8c3a8e5d6b3d7d6c9e8b7a6f5d4c3b2a1",
                {
                    "image": base_image,
                    "prompt": "product photo from new angle, white background"
                },
                cost_per_run=0.004
            )
        new_images.append(img)
    
    return new_images
