import os
from flask import Flask, render_template, request, redirect, url_for
from models import ApprovalDB
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger("dashboard")

# FIX PATHS USING ABSOLUTE REFERENCES
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,  # Absolute path
    static_folder=STATIC_DIR      # Absolute path
)
db = ApprovalDB()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Default credentials if missing
    default_user = os.getenv('DASHBOARD_USER', 'admin')
    default_pass = os.getenv('DASHBOARD_PASS', 'default_password_change_me!')
    
    if request.method == 'POST':
        if (request.form['username'] == default_user and 
            request.form['password'] == default_pass):
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    # DEBUG: Log template paths on access
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Looking for login.html at: {os.path.join(app.template_folder, 'login.html')}")
    
    return render_template('login.html')
