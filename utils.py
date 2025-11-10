import json
import os
from datetime import date

def track_cost(amount):
    """Persistent daily cost tracking"""
    today = str(date.today())
    cost_file = "daily_costs.json"
    
    costs = {}
    if os.path.exists(cost_file):
        with open(cost_file) as f:
            costs = json.load(f)
    
    costs[today] = costs.get(today, 0) + amount
    
    with open(cost_file, 'w') as f:
        json.dump(costs, f)

def combine_images(main_img, swatch_grid):
    """Create clothing collage (simplified)"""
    # In production: use PIL to combine images
    return f"{main_img}?collage=true"  # Placeholder for real processing

def get_quality_tier(product_metafields):
    """Determine quality tier from Shopify metafields"""
    tier = os.getenv('DEFAULT_QUALITY_TIER', 'basic')
    if 'quality_tier' in product_metafields:
        tier = product_metafields['quality_tier']
    return tier
