from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from database.db import get_db
from functools import wraps
import uuid, io

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/home')
def home():
    db = get_db()
    featured = db.execute("""SELECT p.*, b.name as brand_name, c.name as cat_name
        FROM products p LEFT JOIN brands b ON p.brand_id=b.id
        LEFT JOIN categories c ON p.category_id=c.id
        WHERE p.is_active=1 AND p.is_featured=1 LIMIT 8""").fetchall()
    new_arrivals = db.execute("""SELECT p.*, b.name as brand_name
        FROM products p LEFT JOIN brands b ON p.brand_id=b.id
        WHERE p.is_active=1 ORDER BY p.created_at DESC LIMIT 8""").fetchall()
    categories = db.execute("SELECT * FROM categories WHERE is_active=1 LIMIT 6").fetchall()
    brands = db.execute("SELECT * FROM brands WHERE is_active=1 LIMIT 8").fetchall()
    db.close()
    return render_template('user/home.html', featured=featured, new_arrivals=new_arrivals,
                           categories=categories, brands=brands)

@user_bp.route('/shop')
def shop():
    db = get_db()
    q = request.args.get('q', '')
    cat_id = request.args.get('category', '')
    brand_id = request.args.get('brand', '')
    sort = request.args.get('sort', '')
    min_p = request.args.get('min_price', '')
    max_p = request.args.get('max_price', '')

    query = """SELECT p.*, b.name as brand_name, c.name as cat_name
               FROM products p LEFT JOIN brands b ON p.brand_id=b.id
               LEFT JOIN categories c ON p.category_id=c.id
               WHERE p.is_active=1"""
    params = []
    if q:
        query += " AND (p.name LIKE ? OR b.name LIKE ? OR p.description LIKE ?)"
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    if cat_id:
        query += " AND p.category_id=?"
        params.append(cat_id)
    if brand_id:
        query += " AND p.brand_id=?"
        params.append(brand_id)
    if min_p:
        query += " AND p.price>=?"
        params.append(min_p)
    if max_p:
        query += " AND p.price<=?"
        params.append(max_p)
    if sort == 'price_asc':
        query += " ORDER BY p.price ASC"
    elif sort == 'price_desc':
        query += " ORDER BY p.price DESC"
    elif sort == 'newest':
        query += " ORDER BY p.created_at DESC"
    else:
        query += " ORDER BY p.id DESC"

    products = db.execute(query, params).fetchall()
    categories = db.execute("SELECT * FROM categories WHERE is_active=1").fetchall()
    brands = db.execute("SELECT * FROM brands WHERE is_active=1").fetchall()
    db.close()
    return render_template('user/shop.html', products=products, categories=categories,
                           brands=brands, q=q, cat_id=cat_id, brand_id=brand_id, sort=sort)

@user_bp.route('/product/<int:pid>')
def product_detail(pid):
    db = get_db()
    product = db.execute("""SELECT p.*, b.name as brand_name, c.name as cat_name
        FROM products p LEFT JOIN brands b ON p.brand_id=b.id
        LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?""", (pid,)).fetchone()
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('user.shop'))
    reviews = db.execute("""SELECT r.*, u.username FROM reviews r
        LEFT JOIN users u ON r.user_id=u.id
        WHERE r.product_id=? AND r.status='approved'""", (pid,)).fetchall()
    related = db.execute("""SELECT * FROM products WHERE category_id=? AND id!=? AND is_active=1 LIMIT 4""",
                         (product['category_id'], pid)).fetchall()
    avg_rating = db.execute("SELECT AVG(rating) as avg FROM reviews WHERE product_id=? AND status='approved'", (pid,)).fetchone()
    db.close()
    return render_template('user/product_detail.html', product=product, reviews=reviews,
                           related=related, avg_rating=avg_rating['avg'] or 0)

@user_bp.route('/product/<int:pid>/review', methods=['POST'])
@login_required
def add_review(pid):
    rating = request.form.get('rating', 5)
    comment = request.form.get('comment', '').strip()
    if comment:
        db = get_db()
        db.execute("""INSERT INTO reviews (product_id, user_id, rating, comment, name, email, status)
                      VALUES (?,?,?,?,?,?,'pending')""",
                   (pid, session['user_id'], rating, comment, session['full_name'], ''))
        db.commit()
        db.close()
        flash('Review submitted! Pending approval.', 'success')
    return redirect(url_for('user.product_detail', pid=pid))

@user_bp.route('/cart')
@login_required
def cart():
    db = get_db()
    items = db.execute("""SELECT c.id, c.quantity, p.name, p.price, p.discount_price,
        p.image1, p.shipping_charge, p.id as product_id
        FROM cart c JOIN products p ON c.product_id=p.id
        WHERE c.user_id=?""", (session['user_id'],)).fetchall()
    db.close()
    total = sum((i['discount_price'] or i['price']) * i['quantity'] for i in items)
    shipping = sum(i['shipping_charge'] for i in items if i['quantity'] > 0)
    return render_template('user/cart.html', items=items, total=total, shipping=shipping)

@user_bp.route('/cart/add/<int:pid>', methods=['POST'])
@login_required
def add_to_cart(pid):
    db = get_db()
    existing = db.execute("SELECT id, quantity FROM cart WHERE user_id=? AND product_id=?",
                          (session['user_id'], pid)).fetchone()
    if existing:
        db.execute("UPDATE cart SET quantity=quantity+1 WHERE id=?", (existing['id'],))
    else:
        db.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,1)",
                   (session['user_id'], pid))
    db.commit()
    db.close()
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('user.shop'))

@user_bp.route('/cart/remove/<int:cid>')
@login_required
def remove_from_cart(cid):
    db = get_db()
    db.execute("DELETE FROM cart WHERE id=? AND user_id=?", (cid, session['user_id']))
    db.commit()
    db.close()
    return redirect(url_for('user.cart'))

@user_bp.route('/cart/update/<int:cid>', methods=['POST'])
@login_required
def update_cart(cid):
    qty = int(request.form.get('quantity', 1))
    db = get_db()
    if qty > 0:
        db.execute("UPDATE cart SET quantity=? WHERE id=? AND user_id=?", (qty, cid, session['user_id']))
    else:
        db.execute("DELETE FROM cart WHERE id=? AND user_id=?", (cid, session['user_id']))
    db.commit()
    db.close()
    return redirect(url_for('user.cart'))

@user_bp.route('/wishlist')
@login_required
def wishlist():
    db = get_db()
    items = db.execute("""SELECT w.id, p.id as product_id, p.name, p.price, p.discount_price, p.image1
        FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.user_id=?""",
                       (session['user_id'],)).fetchall()
    db.close()
    return render_template('user/wishlist.html', items=items)

@user_bp.route('/wishlist/add/<int:pid>')
@login_required
def add_to_wishlist(pid):
    db = get_db()
    existing = db.execute("SELECT id FROM wishlist WHERE user_id=? AND product_id=?",
                          (session['user_id'], pid)).fetchone()
    if not existing:
        db.execute("INSERT INTO wishlist (user_id, product_id) VALUES (?,?)", (session['user_id'], pid))
        db.commit()
        flash('Added to wishlist!', 'success')
    else:
        flash('Already in wishlist.', 'info')
    db.close()
    return redirect(request.referrer or url_for('user.shop'))

@user_bp.route('/wishlist/remove/<int:wid>')
@login_required
def remove_from_wishlist(wid):
    db = get_db()
    db.execute("DELETE FROM wishlist WHERE id=? AND user_id=?", (wid, session['user_id']))
    db.commit()
    db.close()
    return redirect(url_for('user.wishlist'))

@user_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    db = get_db()
    items = db.execute("""SELECT c.id, c.quantity, p.name, p.price, p.discount_price,
        p.image1, p.shipping_charge, p.id as product_id, p.stock
        FROM cart c JOIN products p ON c.product_id=p.id
        WHERE c.user_id=?""", (session['user_id'],)).fetchall()
    if not items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('user.cart'))
    total = sum((i['discount_price'] or i['price']) * i['quantity'] for i in items)
    shipping = sum(i['shipping_charge'] for i in items)
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        order_num = 'ORD' + uuid.uuid4().hex[:8].upper()
        db.execute("""INSERT INTO orders (order_number, user_id, full_name, email, phone,
            address, city, state, pincode, total_amount, payment_method, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,'New')""",
                   (order_num, session['user_id'],
                    request.form.get('full_name'), request.form.get('email'),
                    request.form.get('phone'), request.form.get('address'),
                    request.form.get('city'), request.form.get('state'),
                    request.form.get('pincode'), total + shipping,
                    request.form.get('payment_method', 'COD')))
        order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        for item in items:
            db.execute("""INSERT INTO order_items (order_id, product_id, quantity, price, shipping_charge)
                VALUES (?,?,?,?,?)""",
                       (order_id, item['product_id'], item['quantity'],
                        item['discount_price'] or item['price'], item['shipping_charge']))
            db.execute("UPDATE products SET stock=stock-? WHERE id=?", (item['quantity'], item['product_id']))
        db.execute("DELETE FROM cart WHERE user_id=?", (session['user_id'],))
        db.commit()
        db.close()
        flash(f'Order placed! Order #: {order_num}', 'success')
        return redirect(url_for('user.order_detail', oid=order_id))
    db.close()
    return render_template('user/checkout.html', items=items, total=total,
                           shipping=shipping, user=user)

@user_bp.route('/orders')
@login_required
def orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",
                        (session['user_id'],)).fetchall()
    db.close()
    return render_template('user/orders.html', orders=orders)

@user_bp.route('/order/<int:oid>')
@login_required
def order_detail(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('user.orders'))
    items = db.execute("""SELECT oi.*, p.name, p.image1 FROM order_items oi
        JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""", (oid,)).fetchall()
    db.close()
    return render_template('user/order_detail.html', order=order, items=items)

@user_bp.route('/order/<int:oid>/cancel')
@login_required
def cancel_order(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    if order and order['status'] in ('New', 'Processing'):
        db.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (oid,))
        db.commit()
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Cannot cancel this order.', 'error')
    db.close()
    return redirect(url_for('user.order_detail', oid=oid))

@user_bp.route('/order/<int:oid>/invoice')
@login_required
def invoice(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    items = db.execute("""SELECT oi.*, p.name FROM order_items oi
        JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""", (oid,)).fetchall()
    db.close()
    lines = ["="*50, "     SHOPPING PORTAL - INVOICE", "="*50,
             f"Order #: {order['order_number']}", f"Date   : {order['created_at']}",
             f"Status : {order['status']}", "-"*50,
             f"Name   : {order['full_name']}", f"Phone  : {order['phone']}",
             f"Address: {order['address']}, {order['city']}, {order['state']} - {order['pincode']}",
             "-"*50, "ITEMS:"]
    for i in items:
        lines.append(f"  {i['name']} x{i['quantity']} @ ₹{i['price']} = ₹{i['price']*i['quantity']}")
    lines += ["-"*50, f"TOTAL: ₹{order['total_amount']}", f"Payment: {order['payment_method']}",
              "="*50, "Thank you for shopping with us!"]
    response = make_response("\n".join(lines))
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order["order_number"]}.txt'
    return response

@user_bp.route('/track', methods=['GET', 'POST'])
def track_order():
    order = None
    if request.method == 'POST':
        order_num = request.form.get('order_number', '').strip()
        db = get_db()
        order = db.execute("SELECT * FROM orders WHERE order_number=?", (order_num,)).fetchone()
        db.close()
        if not order:
            flash('No order found with this number.', 'error')
    return render_template('user/track_order.html', order=order)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        db.execute("""UPDATE users SET full_name=?, phone=?, address=?, city=?, state=?, pincode=?
                      WHERE id=?""",
                   (request.form.get('full_name'), request.form.get('phone'),
                    request.form.get('address'), request.form.get('city'),
                    request.form.get('state'), request.form.get('pincode'),
                    session['user_id']))
        db.commit()
        session['full_name'] = request.form.get('full_name')
        flash('Profile updated!', 'success')
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    db.close()
    return render_template('user/profile.html', user=user)
