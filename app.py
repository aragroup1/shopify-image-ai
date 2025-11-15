import os
import logging
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv
from models import ApprovalDB
from services.shopify import ShopifyService
from threading import Thread
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

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

@app.post("/fetch-all-products")
async def fetch_all_products(background_tasks: BackgroundTasks):
    """Manually trigger fetching of all products from Shopify"""
    if not shopify.enabled:
        return {"status": "error", "message": "Shopify service disabled"}
    
    background_tasks.add_task(process_all_products)
    return {"status": "started", "message": "Batch processing started - check dashboard in 2-5 minutes"}

@app.get("/")
async def root():
    """Redirect root to dashboard login"""
    return RedirectResponse("/dashboard/login")

@app.get("/health")
async def health_check():
    """Railway health check - ultra fast"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0",
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
            processed_images=processed_images
        )
        logger.info(f"✅ Added pending approval for product {product_id}")
    
    except Exception as e:
        logger.exception(f"💥 Processing failed for product {product_id}: {str(e)}")

@app.on_event("startup")
async def graceful_startup():
    """Non-blocking startup - verify connections in background"""
    log_directory_structure()
    logger.info("✅ Application started (background verification in progress)")
    
    # Start Shopify verification in background thread
    Thread(target=async_shopify_verification, daemon=True).start()

def async_shopify_verification():
    """Non-blocking Shopify verification"""
    time.sleep(2)  # Let server start first
    
    if shopify.enabled:
        if shopify.verify_connection():
            logger.info("✅ Shopify connection verified in background")
        else:
            logger.warning("⚠️ Shopify connection failed in background verification")
    else:
        logger.warning("⚠️ Shopify service disabled")

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
