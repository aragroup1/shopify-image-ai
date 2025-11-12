import requests
import os
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()
logger = logging.getLogger("shopify")

class ShopifyService:
    def __init__(self):
        # Get credentials with stripping
        self.api_key = os.getenv('SHOPIFY_API_KEY', '').strip()
        self.password = os.getenv('SHOPIFY_PASSWORD', '').strip()  # Should be shpat_ token
        self.store_url = os.getenv('SHOPIFY_STORE_URL', '').strip()
        
        # Validate credentials format
        self.enabled = False
        missing = []
        
        if not self.api_key:
            missing.append("SHOPIFY_API_KEY")
        if not self.password:
            missing.append("SHOPIFY_PASSWORD")
        if not self.store_url:
            missing.append("SHOPIFY_STORE_URL")
        
        if missing:
            logger.warning(f"⚠️ MISSING CREDENTIALS: {', '.join(missing)}")
        elif not self.password.startswith('shpat_'):
            logger.warning(f"⚠️ INVALID PASSWORD FORMAT - should start with 'shpat_' but got: {self.password[:10]}...")
        else:
            # Clean store URL (remove http/https prefixes)
            if self.store_url.startswith(('http://', 'https://')):
                self.store_url = urlparse(self.store_url).netloc
            
            # Final validation
            if all([self.api_key, self.password, self.store_url]):
                self.enabled = True
                logger.info("✅ CORRECT Shopify credentials format detected")
                logger.info(f"Store URL: {self.store_url}")
        
        self.base_url = f"https://{self.api_key}:{self.password}@{self.store_url}/admin/api/2023-10" if self.enabled else ""
    
    def get_product_images(self, product_id):
        """Fetch all images for a product"""
        if not self.enabled:
            logger.warning("🚫 Shopify service disabled - skipping image fetch")
            return []
        
        try:
            url = f"{self.base_url}/products/{product_id}/images.json"
            logger.info(f"📡 Fetching images from: {url.split('@')[1]}")  # Hide credentials
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                images = response.json().get('images', [])
                logger.info(f"✅ Retrieved {len(images)} images for product {product_id}")
                return images
            else:
                logger.error(f"❌ Shopify API error ({response.status_code}): {response.text[:200]}")
                return []
        except Exception as e:
            logger.exception(f"🔥 Shopify API exception: {str(e)}")
            return []
    
    def verify_connection(self):
        """Test Shopify connection at startup"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/shop.json"
            logger.info(f"🔍 Testing connection to: {url.split('@')[1]}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                shop_data = response.json()['shop']
                logger.info(f"🎉 Successfully connected to Shopify store: {shop_data['name']} (ID: {shop_data['id']})")
                return True
            else:
                logger.error(f"❌ Connection failed (Status {response.status_code})")
                logger.error(f"Response: {response.text[:500]}")
                return False
        except Exception as e:
            logger.exception(f"🔥 Connection test failed: {str(e)}")
            return False
