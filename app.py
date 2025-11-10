import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
from services.shopify import ShopifyService
from models import ApprovalDB
import uvicorn

load_dotenv()
app = FastAPI()
shopify = ShopifyService()
db = ApprovalDB()

@app.get("/")
async def root():
    """Redirect root to dashboard login"""
    return RedirectResponse("/dashboard/login")

@app.get("/health")
async def health_check():
    """Railway health check endpoint"""
    return {"status": "ok", "db_status": "connected" if db.conn else "disconnected"}

@app.on_event("startup")
async def validate_config():
    """Critical startup checks"""
    required_vars = [
        'SHOPIFY_API_KEY', 
        'SHOPIFY_PASSWORD',
        'SHOPIFY_STORE_URL',
        'REPLICATE_API_TOKEN',
        'DASHBOARD_USER',
        'DASHBOARD_PASS'
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"MISSING ENV VARS: {', '.join(missing)} - Check Railway variables"
        )
    print("✅ All environment variables validated")

# Mount Flask dashboard under /dashboard
from fastapi.middleware.wsgi import WSGIMiddleware
from dashboard import app as dashboard_app

app.mount("/dashboard", WSGIMiddleware(dashboard_app))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
