import sqlite3
from datetime import datetime

class ApprovalDB:
# REPLACE __init__ METHOD WITH THIS:
def __init__(self, db_path='/tmp/approvals.db'):  # Use tmp dir for Railway
    """Use ephemeral storage compatible with Railway"""
    self.conn = sqlite3.connect(db_path, check_same_thread=False)
    self._init_db()
    
    def _init_db(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS pending_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    variant_id TEXT,
                    original_images TEXT,
                    processed_images TEXT,
                    status TEXT CHECK(status IN ('pending', 'approved', 'rejected')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    reject_reason TEXT
                )
            ''')
    
    def add_pending(self, product_id, original_images, processed_images, variant_id=None):
        with self.conn:
            self.conn.execute(
                'INSERT INTO pending_images (product_id, variant_id, original_images, processed_images, status) VALUES (?, ?, ?, ?, ?)',
                (product_id, variant_id, ','.join(original_images), ','.join(processed_images), 'pending')
            )
    
    def get_pending(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM pending_images WHERE status='pending' ORDER BY created_at DESC")
        return cur.fetchall()
    
    def approve(self, approval_id):
        with self.conn:
            self.conn.execute(
                'UPDATE pending_images SET status="approved", approved_at=? WHERE id=?',
                (datetime.now(), approval_id)
            )
    
    def reject(self, approval_id, reason):
        with self.conn:
            self.conn.execute(
                'UPDATE pending_images SET status="rejected", reject_reason=? WHERE id=?',
                (reason, approval_id)
            )
