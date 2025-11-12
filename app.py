import os
import logging
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv
from models import ApprovalDB
from services.shopify import ShopifyService
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

load_dotenv()
app = FastAPI()
db = ApprovalDB()
shopify = ShopifyService()

# REPLACE get_startup_warnings FUNCTION WITH THIS:
def get_startup_warnings():
    """Collect configuration warnings without crashing"""
    warnings = []
    
    # Verify Shopify connection at startup
    if shopify.enabled:
        if shopify.verify_connection():
            logger.info("✅ Shopify connection verified")
        else:
            warnings.append("⚠️ SHOPIFY CONNECTION FAILED - check credentials")
            shopify.enabled = False
    else:
        warnings.append("⚠️ SHOPIFY CREDENTIALS MISSING OR INVALID FORMAT")
    
    # Replicate token check
    replicate_token = os.getenv('REPLICATE_API_TOKEN', '')
    if not replicate_token.startswith('r8_'):
        warnings.append("⚠️ REPLICATE TOKEN MISSING OR INVALID FORMAT")
    
    # Dashboard auth check
    if not os.getenv('DASHBOARD_USER') or not os.getenv('DASHBOARD_PASS'):
        warnings.append("⚠️ DASHBOARD AUTH MISSING - using default credentials")
        os.environ['DASHBOARD_USER'] = 'admin'
        os.environ['DASHBOARD_PASS'] = 'default_password_change_me!'
    
    return warnings

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
    
    # Verify Shopify connection at startup
    if shopify.enabled:
        try:
            shop_url = f"https://{shopify.store_url}/admin/api/2023-10/shop.json"
            response = requests.get(
                shop_url,
                auth=(shopify.api_key, shopify.password),
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Shopify connection verified")
            else:
                warnings.append(f"⚠️ SHOPIFY CONNECTION FAILED (Status: {response.status_code})")
                shopify.enabled = False
        except Exception as e:
            warnings.append(f"⚠️ SHOPIFY ERROR: {str(e)}")
            shopify.enabled = False
    
    # Critical but non-fatal checks
    if not os.getenv('SHOPIFY_API_KEY') or not os.getenv('SHOPIFY_PASSWORD'):
        warnings.append("⚠️ SHOPIFY CREDENTIALS MISSING - webhook processing disabled")
    
    if not os.getenv('REPLICATE_API_TOKEN'):
        warnings.append("⚠️ REPLICATE TOKEN MISSING - AI processing disabled")
    
    if not os.getenv('DASHBOARD_USER') or not os.getenv('DASHBOARD_PASS'):
        warnings.append("⚠️ DASHBOARD AUTH MISSING - using default credentials")
        # Set safe defaults
        os.environ['DASHBOARD_USER'] = 'admin'
        os.environ['DASHBOARD_PASS'] = 'default_password_change_me!'
    
    # Required for Railway but provide fallback
    os.environ['PORT'] = os.getenv('PORT', '8000')
    
    return warnings

@app.get("/")
async def root():
    """Redirect root to dashboard login"""
    return RedirectResponse("/dashboard/login")

@app.get("/health")
async def health_check():
    """Railway health check - always passes"""
    return {
        "status": "ok",
        "db_status": "connected" if db.conn else "disconnected",
        "shopify_status": "enabled" if shopify.enabled else "disabled",
        "warnings": get_startup_warnings()
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
    log_directory_structure()
    warnings = get_startup_warnings()
    
    if warnings:
        logger.warning("\n" + "="*50)
        logger.warning("CONFIGURATION WARNINGS - APP WILL RUN IN DEGRADED MODE")
        for warning in warnings:
            logger.warning(warning)
        logger.warning("="*50 + "\n")
    else:
        logger.info("✅ All systems operational")

# Mount Flask dashboard under /dashboard
from dashboard import app as dashboard_app
app.mount("/dashboard", WSGIMiddleware(dashboard_app))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
