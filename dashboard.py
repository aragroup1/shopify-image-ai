@app.route('/')
@login_required
def dashboard():
    """Main dashboard route with pagination"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Items per page
        
        # Get all pending items
        all_pending = db.get_pending()
        total_items = len(all_pending)
        
        # Calculate pagination
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        # Get items for current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        pending_items = all_pending[start_idx:end_idx]
        
        # Calculate display info
        start_item = start_idx + 1
        end_item = min(end_idx, total_items)
        
        return render_template('dashboard.html', 
                             pending_items=pending_items, 
                             os=os, 
                             BASE_URL=BASE_URL,
                             current_page=page,
                             total_pages=total_pages,
                             total_items=total_items,
                             start_item=start_item,
                             end_item=end_item)
    except Exception as e:
        logger.exception(f"🔥 Dashboard rendering failed: {str(e)}")
        return render_template('dashboard.html', 
                             pending_items=[], 
                             os=os, 
                             BASE_URL=BASE_URL,
                             current_page=1,
                             total_pages=1,
                             total_items=0,
                             start_item=0,
                             end_item=0)
