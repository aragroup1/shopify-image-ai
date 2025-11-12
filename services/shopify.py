import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("shopify")

class ShopifyService:
    def __init__(self):
        self.api_key = os.getenv('SHOPIFY_API_KEY', '')
        self.password = os.getenv('SHOPIFY_PASSWORD', '')
        self.store_url = os.getenv('SHOPIFY_STORE_URL', '')
        
        # Critical fix: Admin API access token starts with shpat_
        if self.api_key.startswith('shpat_') and self.password.startswith('shppa_'):
            self.enabled = True
            logger.info("✅ Valid Shopify credentials detected")
        else:
            self.enabled = False
            logger.warning("⚠️ Invalid Shopify credentials format")
        
        self.base_url = f"https://{self.api_key}:{self.password}@{self.store_url}/admin/api/2023-10" if self.enabled else ""
    
    def get_product_images(self, product_id):
        """Fetch all images for a product"""
        if not self.enabled:
            logger.warning("🚫 Shopify service disabled - skipping image fetch")
            return []
        
        try:
            url = f"{self.base_url}/products/{product_id}/images.json"
            logger.debug(f"GET {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('images', [])
            else:
                logger.error(f"❌ Shopify API error ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            logger.exception(f"🔥 Shopify API exception: {str(e)}")
            return []
    
    def get_product_tags(self, product_id):
        """Get tags for product detection logic"""
        if not self.enabled:
            return []
        
        try:
            url = f"{self.base_url}/products/{product_id}.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()['product'].get('tags', [])
            return []
        except Exception as e:
            logger.exception(f"🔥 Shopify tags exception: {str(e)}")
            return []
