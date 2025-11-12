import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session
from models import ApprovalDB
from dotenv import load_dotenv
import secrets

BASE_URL = os.getenv('BASE_URL', 'https://shopify-image-ai-production.up.railway.app')

@app.context_processor
def inject_base_url():
    return dict(BASE_URL=BASE_URL)
    
load_dotenv()
logger = logging.getLogger("dashboard")

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
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Looking for login.html at: {os.path.join(app.template_folder, 'login.html')}")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    pending = db.get_pending()
    return render_template('dashboard.html', pending_items=pending, os=os)

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

# NEW ENDPOINT FOR SIMULATION
@app.route('/simulate-webhook', methods=['POST'])
@login_required
def simulate_webhook():
    """Simulate Shopify webhook for testing"""
    logger.info("🔧 Simulating product update webhook")
    
    # Create mock product data
    mock_product = {
        'id': 9999999,
        'tags': ['Supplier:apify', 'test-product'],
        'images': [
            {'src': 'https://via.placeholder.com/300x300?text=Original+1'},
            {'src': 'https://via.placeholder.com/300x300?text=Original+2'}
        ]
    }
    
    # Add to approval queue
    db.add_pending(
        product_id=str(mock_product['id']),
        original_images=[img['src'] for img in mock_product['images']],
        processed_images=[
            'https://via.placeholder.com/300x300?text=Processed+1',
            'https://via.placeholder.com/300x300?text=Processed+2',
            'https://via.placeholder.com/300x300?text=Processed+3'
        ]
    )
    
    logger.info("✅ Simulated webhook processed successfully")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
