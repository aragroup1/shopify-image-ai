import os
from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv
from services.shopify import ShopifyService
from services.replicate import ReplicateService
from processing.apify_handler import split_apify_image
from processing.clothing import generate_clothing_gallery
from models import ApprovalDB
from utils import get_quality_tier
import uvicorn

load_dotenv()
app = FastAPI()
shopify = ShopifyService()
db = ApprovalDB()

@app.post("/webhook/product_updated")
async def handle_product_update(payload: dict, background_tasks: BackgroundTasks):
    """Shopify webhook handler"""
    product_id = payload['id']
    tags = shopify.get_product_tags(product_id)
    
    # Special handling for Apify products
    if "Supplier:apify" in tags:
        background_tasks.add_task(process_apify_product, product_id)
    else:
        background_tasks.add_task(process_standard_product, product_id)
    
    return {"status": "processing_started"}

def process_apify_product(product_id):
    """Process Apify-tagged products"""
    images = shopify.get_product_images(product_id)
    if not images:
        return
    
    # Split multi-angle images
    split_images = []
    for img in images[:3]:  # Only process first 3 originals
        split_images.extend(split_apify_image(img['src']))
    
    # Save to approval DB
    db.add_pending(
        product_id=str(product_id),
        original_images=[img['src'] for img in images],
        processed_images=split_images[:5]  # Max 5 images
    )

def process_standard_product(product_id):
    """Process non-Apify products"""
    # Similar logic with clothing/general processing
    # ... (full implementation in GitHub repo)
    pass

# Mount Flask dashboard under /dashboard
from fastapi.middleware.wsgi import WSGIMiddleware
from dashboard import app as dashboard_app

app.mount("/dashboard", WSGIMiddleware(dashboard_app))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
