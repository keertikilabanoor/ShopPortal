from flask import Blueprint, jsonify, session
from database.db import get_db

api_bp = Blueprint('api', __name__)

@api_bp.route('/cart/count')
def cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    db = get_db()
    count = db.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?", (session['user_id'],)).fetchone()[0]
    db.close()
    return jsonify({'count': count or 0})

@api_bp.route('/wishlist/count')
def wishlist_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM wishlist WHERE user_id=?", (session['user_id'],)).fetchone()[0]
    db.close()
    return jsonify({'count': count or 0})

@api_bp.route('/subcategories/<int:cat_id>')
def subcategories_by_cat(cat_id):
    db = get_db()
    subs = db.execute("SELECT id, name FROM subcategories WHERE category_id=? AND is_active=1", (cat_id,)).fetchall()
    db.close()
    return jsonify([dict(s) for s in subs])
