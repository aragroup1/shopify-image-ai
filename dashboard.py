import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, g
from models import ApprovalDB
from dotenv import load_dotenv
import secrets
import requests
import time

load_dotenv()
logger = logging.getLogger("dashboard")

def create_dashboard_app():
    """Factory function to create Flask app - prevents circular imports"""
    # Get base URL from environment or default
    BASE_URL = os.getenv('BASE_URL', 'https://shopify-image-ai-production.up.railway.app')
    logger.info(f"Creating dashboard app with Base URL: {BASE_URL}")

    # Absolute paths for templates and static files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR
    )
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
    db = ApprovalDB()

    @app.context_processor
    def inject_base_url():
        """Make BASE_URL available to all templates"""
        return dict(BASE_URL=BASE_URL)

    def login_required(f):
        """Decorator to protect routes"""
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Default credentials if missing
        default_user = os.getenv('DASHBOARD_USER', 'admin')
        default_pass = os.getenv('DASHBOARD_PASS', 'default_password_change_me!')
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if username == default_user and password == default_pass:
                session['logged_in'] = True
                next_url = request.args.get('next') or url_for('dashboard')
                # Fix double /dashboard issue
                if '/dashboard/dashboard' in next_url:
                    next_url = next_url.replace('/dashboard/dashboard', '/dashboard')
                return redirect(next_url)
            else:
                return render_template('login.html', error="Invalid username or password")
        
        logger.info(f"Template folder: {app.template_folder}")
        logger.info(f"Looking for login.html at: {os.path.join(app.template_folder, 'login.html')}")
        return render_template('login.html')

    @app.route('/')
    @login_required
    def dashboard():
        """Main dashboard route - fixed to root of Flask app"""
        pending = db.get_pending()
        return render_template('dashboard.html', pending_items=pending, os=os, BASE_URL=BASE_URL)

    @app.route('/approve/<int:approval_id>')
    @login_required
    def approve(approval_id):
        db.approve(approval_id)
        return redirect(url_for('dashboard'))

    @app.route('/reject/<int:approval_id>', methods=['POST'])
    @login_required
    def reject(approval_id):
        reason = request.form.get('reason', 'No reason provided')
        db.reject(approval_id, reason)
        return redirect(url_for('dashboard'))

    @app.route('/simulate-webhook', methods=['POST'])
    @login_required
    def simulate_webhook():
        """Simulate Shopify webhook for testing"""
        logger.info("🔧 Simulating product update webhook")
        
        # Create mock product data
        mock_product = {
            'id': 9999999,
            'tags': 'Supplier:apify,clothing,test-product',
            'images': [
                {'src': 'https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?auto=format&fit=crop&w=300&q=80'},
                {'src': 'https://images.unsplash.com/photo-1591047139829-d91485f5e0e9?auto=format&fit=crop&w=300&q=80'}
            ]
        }
        
        # Add to approval queue
        db.add_pending(
            product_id=str(mock_product['id']),
            original_images=[img['src'] for img in mock_product['images']],
            processed_images=[
                'https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?auto=format&fit=crop&w=300&q=80&blend=6366f1&blend-mode=normal&sat=-100',
                'https://images.unsplash.com/photo-1591047139829-d91485f5e0e9?auto=format&fit=crop&w=300&q=80&blend=6366f1&blend-mode=normal&sat=-100',
                'https://images.unsplash.com/photo-1541099649105-f69ad2cb1727?auto=format&fit=crop&w=300&q=80&blend=6366f1&blend-mode=normal&sat=-100'
            ],
            variant_id=mock_product['tags']
        )
        
        logger.info("✅ Simulated webhook processed successfully")
        return redirect(url_for('dashboard'))

    @app.route('/fetch-all-products', methods=['POST'])
    @login_required
    def manual_fetch():
        """Manual trigger for batch product fetching"""
        logger.info(">manual Manual batch fetch triggered by user")
        
        # Trigger the FastAPI endpoint
        try:
            BASE_URL = os.getenv('BASE_URL', 'https://shopify-image-ai-production.up.railway.app')
            response = requests.post(f"{BASE_URL}/fetch-all-products")
            logger.info(f"📡 Batch fetch API response: {response.status_code} - {response.text}")
        except Exception as e:
            logger.exception(f"🔥 Failed to trigger batch fetch: {str(e)}")
        
        return redirect(url_for('dashboard'))

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        return redirect(url_for('login'))

    return app
