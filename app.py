import os
import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
from models import ApprovalDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

load_dotenv()
app = FastAPI()
db = ApprovalDB()

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
        "warnings": get_startup_warnings()
    }

def get_startup_warnings():
    """Collect configuration warnings without crashing"""
    warnings = []
    
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

@app.on_event("startup")
async def graceful_startup():
    """Start even with missing config - log warnings instead"""
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
from fastapi.middleware.wsgi import WSGIMiddleware
from dashboard import app as dashboard_app

app.mount("/dashboard", WSGIMiddleware(dashboard_app))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
