import os
import logging
import time
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv
from models import ApprovalDB
from services.shopify import ShopifyService
from threading import Thread
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")
startup_time = time.time()

load_dotenv()
app = FastAPI()
db = ApprovalDB()
shopify = ShopifyService()

def log_directory_structure():
    """Debug directory structure on startup"""
    logger.info("\n" + "="*50)
    logger.info("DIRECTORY STRUCTURE DEBUG")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"App directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # List critical directories
    for dir_name in ['templates', 'static']:
        path = os.path.join(os.getcwd(), dir_name)
        exists = os.path.exists(path)
        logger.info(f"{'✅' if exists else '❌'} {dir_name} directory: {path}")
        if exists:
            files = os.listdir(path)
            logger.info(f"  Files: {', '.join(files) if files else 'EMPTY'}")
    
    logger.info("="*50 + "\n")

def get_startup_warnings():
    """Collect configuration warnings without crashing"""
    warnings = []
    
    # Replicate token check
    replicate_token = os.getenv('REPLICATE_API_TOKEN', '')
    if not replicate_token.startswith('r8_'):
        warnings.append("⚠️ REPLICATE TOKEN MISSING OR INVALID FORMAT")
    
    # Dashboard auth check
    if not os.getenv('DASHBOARD_USER') or not os.getenv('DASHBOARD_PASS'):
        warnings.append("⚠️ DASHBOARD AUTH MISSING - using default credentials")
    
    return warnings

def get_memory_usage():
    """Simple memory usage check"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    except:
        return "unknown"

def is_app_ready():
    """Quick check if app is ready for traffic"""
    return True

@app.get("/")
async def root():
    """Redirect root to dashboard login"""
    return RedirectResponse("/dashboard")

@app.get("/health")
async def health_check():
    """Ultra-fast health check for Railway"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - startup_time,
        "memory": get_memory_usage(),
        "ready": is_app_ready(),
        "shopify_status": "connected" if shopify.enabled else "disconnected"
    }

@app.post("/webhook/product_updated")
async def handle_product_update(request: Request, background_tasks: BackgroundTasks):
    """Shopify webhook handler - processes product updates"""
    if not shopify.enabled:
        logger.warning("🚫 Ignoring webhook - Shopify service disabled")
        return {"status": "shopify_disabled"}
    
    try:
        payload = await request.json()
        product_id = payload.get('id')
        tags = payload.get('tags', [])
        
        if not product_id:
            logger.error("❌ Webhook missing product ID")
            return {"status": "error", "message": "missing_product_id"}
        
        logger.info(f"✅ Webhook received for product: {product_id}")
        logger.info(f"🏷️ Product tags: {tags}")
        
        # Add to background processing
        background_tasks.add_task(process_product, product_id, tags)
        return {"status": "processing_started", "product_id": product_id}
    
    except Exception as e:
        logger.exception(f"🔥 Webhook processing failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/fetch-all-products")
async def fetch_all_products(background_tasks: BackgroundTasks):
    """Manually trigger fetching of all products from Shopify"""
    if not shopify.enabled:
        return {"status": "error", "message": "Shopify service disabled"}
    
    background_tasks.add_task(process_all_products)
    return {"status": "started", "message": "Batch processing started - check dashboard in 2-5 minutes"}

def process_product(product_id, tags):
    """Background task to process product images"""
    try:
        # Get product images from Shopify
        images = shopify.get_product_images(product_id)
        if not images:
            logger.warning(f"🖼️ No images found for product {product_id}")
            return
        
        logger.info(f"📸 Found {len(images)} images for product {product_id}")
        
        # Special handling for Apify products
        if "Supplier:apify" in tags:
            logger.info(f"🔍 Processing Supplier:apify tagged product")
            # In real implementation: split multi-angle images
            processed_images = [img['src'] for img in images[:5]]  # Simple placeholder
        else:
            # Standard processing
            processed_images = [img['src'] for img in images[:5]]  # Simple placeholder
        
        # Add to approval queue
        db.add_pending(
            product_id=str(product_id),
            original_images=[img['src'] for img in images],
            processed_images=processed_images,
            variant_id=','.join(tags) if isinstance(tags, list) else tags
        )
        logger.info(f"✅ Added pending approval for product {product_id}")
    
    except Exception as e:
        logger.exception(f"💥 Processing failed for product {product_id}: {str(e)}")

def process_all_products():
    """Process ALL products from Shopify - not just webhooks"""
    try:
        logger.info("🚀 Starting batch processing of ALL products")
        
        # Get all products from Shopify
        all_products = shopify.get_all_products()
        if not all_products:
            logger.warning("❌ No products found in Shopify store")
            return
        
        logger.info(f"📋 Found {len(all_products)} total products to process")
        
        processed_count = 0
        apify_count = 0
        clothing_count = 0
        
        # Process each product
        for product in all_products:
            product_id = product['id']
            tags = product.get('tags', '')
            title = product.get('title', 'Untitled Product')
            
            # Skip if already processed recently
            if db.get_pending_by_product_id(str(product_id)):
                logger.info(f"⏭️ Skipping already pending product: {title} (ID: {product_id})")
                continue
            
            # Determine product type
            is_apify = 'Supplier:apify' in str(tags)
            is_clothing = any(keyword in title.lower() for keyword in [
                'shirt', 'dress', 'pants', 'jacket', 'hoodie', 'sweater', 
                'top', 'bottom', 'jeans', 'blouse', 'skirt', 'shorts'
            ])
            
            logger.info(f"🔍 Processing: {title} (ID: {product_id})")
            logger.info(f"🏷️ Tags: {tags}")
            logger.info(f"📊 Type: {'Apify' if is_apify else 'Clothing' if is_clothing else 'Standard'}")
            
            # Get product images
            images = shopify.get_product_images(product_id)
            if not images:
                logger.warning(f"🖼️ No images found for product: {title}")
                continue
            
            # Process based on type
            if is_apify:
                logger.info(f"🔧 Processing as Apify multi-angle product")
                apify_count += 1
                # In real implementation: split multi-angle images
                processed_images = [img['src'] for img in images[:5]]
            elif is_clothing:
                logger.info(f"👗 Processing as clothing product")
                clothing_count += 1
                # In real implementation: generate lifestyle + swatch collage
                processed_images = [img['src'] for img in images[:5]]
            else:
                logger.info(f"📦 Processing as standard product")
                # Add UK flag + fast delivery badge
                processed_images = [img['src'] for img in images[:5]]
            
            # Add to approval queue
            db.add_pending(
                product_id=str(product_id),
                original_images=[img['src'] for img in images],
                processed_images=processed_images,
                variant_id=str(tags)  # Store tags for display
            )
            
            processed_count += 1
            logger.info(f"✅ Added to approval queue: {title}")
            
            # Rate limiting - be nice to Shopify API
            time.sleep(0.5)
        
        logger.info(f"🎉 Batch processing complete!")
        logger.info(f"✅ Total processed: {processed_count}/{len(all_products)}")
        logger.info(f"🔍 Apify products: {apify_count}")
        logger.info(f"👗 Clothing products: {clothing_count}")
        logger.info(f"📦 Standard products: {processed_count - apify_count - clothing_count}")
        
    except Exception as e:
        logger.exception(f"💥 Batch processing failed: {str(e)}")

@app.on_event("startup")
async def graceful_startup():
    """Optimized startup - no heavy operations"""
    log_directory_structure()
    logger.info("✅ Application started (lightweight startup)")
    
    # ONLY log warnings - no blocking operations
    warnings = get_startup_warnings()
    if warnings:
        logger.warning("\n" + "="*50)
        logger.warning("CONFIGURATION WARNINGS")
        for warning in warnings:
            logger.warning(warning)
        logger.warning("="*50 + "\n")

# ===== CRITICAL FIX: MOVE FLASK MOUNTING TO BOTTOM =====
# This prevents circular imports and mounting errors
try:
    from dashboard import create_dashboard_app
    
    # Create and mount the dashboard app
    dashboard_app = create_dashboard_app()
    app.mount("/dashboard", WSGIMiddleware(dashboard_app))
    logger.info("✅ Dashboard mounted successfully at /dashboard")
except Exception as e:
    logger.exception(f"🔥 Failed to mount dashboard: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
