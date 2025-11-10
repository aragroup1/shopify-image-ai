from flask import Flask, render_template, request, redirect, url_for
from models import ApprovalDB
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(
    __name__,
    static_folder='../static',  # Critical path fix
    template_folder='../templates'
)
db = ApprovalDB()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if (request.form['username'] == os.getenv('DASHBOARD_USER') and 
            request.form['password'] == os.getenv('DASHBOARD_PASS')):
            return redirect(url_for('dashboard'))
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
