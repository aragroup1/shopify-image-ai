import os
import logging
from flask import Flask, render_template, request, redirect, url_for
from models import ApprovalDB
from dotenv import load_dotenv

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
db = ApprovalDB()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Default credentials if missing
    default_user = os.getenv('DASHBOARD_USER', 'admin')
    default_pass = os.getenv('DASHBOARD_PASS', 'default_password_change_me!')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == default_user and password == default_pass:
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Looking for login.html at: {os.path.join(app.template_folder, 'login.html')}")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    pending = db.get_pending()
    return render_template('dashboard.html', pending_items=pending, os=os)

@app.route('/approve/<int:approval_id>')
def approve(approval_id):
    db.approve(approval_id)
    return redirect(url_for('dashboard'))

@app.route('/reject/<int:approval_id>', methods=['POST'])
def reject(approval_id):
    reason = request.form.get('reason', 'No reason provided')
    db.reject(approval_id, reason)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
