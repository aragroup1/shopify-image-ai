import requests
from dotenv import load_dotenv
import os

load_dotenv()

class ShopifyService:
# REPLACE __init__ WITH THIS:
def __init__(self):
    self.api_key = os.getenv('SHOPIFY_API_KEY', '')
    self.password = os.getenv('SHOPIFY_PASSWORD', '')
    self.store_url = os.getenv('SHOPIFY_STORE_URL', '')
    
    # Disable service if credentials missing
    self.enabled = all([self.api_key, self.password, self.store_url])
    if not self.enabled:
        logger.warning("🚫 Shopify service disabled - missing credentials")
    
    self.base_url = f"https://{self.api_key}:{self.password}@{self.store_url}/admin/api/2023-10" if self.enabled else ""

# ADD SAFETY CHECKS TO ALL METHODS:
def get_product_images(self, product_id):
    if not self.enabled:
        logger.warning("Attempted Shopify operation while disabled")
        return []
    # ... rest of existing code
    
    def update_product_images(self, product_id, new_images):
        """Replace all images for a product"""
        url = f"{self.base_url}/products/{product_id}/images.json"
        payload = {"images": [{"src": img} for img in new_images]}
        return requests.put(url, json=payload)
    
    def get_product_tags(self, product_id):
        """Get tags for product detection logic"""
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.get(url)
        return response.json()['product']['tags'] if response.status_code == 200 else []
