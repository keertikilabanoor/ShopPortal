from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.db import get_db
from functools import wraps
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def save_image(file, folder='products'):
    if file and allowed_file(file.filename):
        from flask import current_app
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return filename
    return None

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    stats = {
        'brands': db.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
        'categories': db.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
        'subcategories': db.execute("SELECT COUNT(*) FROM subcategories").fetchone()[0],
        'products': db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'users': db.execute("SELECT COUNT(*) FROM users WHERE user_type='user'").fetchone()[0],
        'new_orders': db.execute("SELECT COUNT(*) FROM orders WHERE status='New'").fetchone()[0],
        'processing': db.execute("SELECT COUNT(*) FROM orders WHERE status='Processing'").fetchone()[0],
        'dispatched': db.execute("SELECT COUNT(*) FROM orders WHERE status='Dispatched'").fetchone()[0],
        'delivered': db.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'").fetchone()[0],
        'cancelled': db.execute("SELECT COUNT(*) FROM orders WHERE status='Cancelled'").fetchone()[0],
        'pending_reviews': db.execute("SELECT COUNT(*) FROM reviews WHERE status='pending'").fetchone()[0],
        'approved_reviews': db.execute("SELECT COUNT(*) FROM reviews WHERE status='approved'").fetchone()[0],
    }
    recent_orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 5").fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

# ─── BRANDS ───
@admin_bp.route('/brands')
@admin_required
def brands():
    db = get_db()
    brands = db.execute("SELECT * FROM brands ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/brands.html', brands=brands)

@admin_bp.route('/brands/add', methods=['GET', 'POST'])
@admin_required
def add_brand():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        desc = request.form.get('description', '').strip()
        logo = save_image(request.files.get('logo'))
        db = get_db()
        db.execute("INSERT INTO brands (name, description, logo) VALUES (?,?,?)", (name, desc, logo))
        db.commit()
        db.close()
        flash('Brand added!', 'success')
        return redirect(url_for('admin.brands'))
    return render_template('admin/brand_form.html', brand=None)

@admin_bp.route('/brands/edit/<int:bid>', methods=['GET', 'POST'])
@admin_required
def edit_brand(bid):
    db = get_db()
    brand = db.execute("SELECT * FROM brands WHERE id=?", (bid,)).fetchone()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        desc = request.form.get('description', '').strip()
        logo = save_image(request.files.get('logo')) or brand['logo']
        db.execute("UPDATE brands SET name=?, description=?, logo=? WHERE id=?", (name, desc, logo, bid))
        db.commit()
        flash('Brand updated!', 'success')
        db.close()
        return redirect(url_for('admin.brands'))
    db.close()
    return render_template('admin/brand_form.html', brand=brand)

@admin_bp.route('/brands/delete/<int:bid>')
@admin_required
def delete_brand(bid):
    db = get_db()
    db.execute("DELETE FROM brands WHERE id=?", (bid,))
    db.commit()
    db.close()
    flash('Brand deleted!', 'success')
    return redirect(url_for('admin.brands'))

# ─── CATEGORIES ───
@admin_bp.route('/categories')
@admin_required
def categories():
    db = get_db()
    cats = db.execute("SELECT * FROM categories ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        desc = request.form.get('description', '').strip()
        db = get_db()
        db.execute("INSERT INTO categories (name, description) VALUES (?,?)", (name, desc))
        db.commit()
        db.close()
        flash('Category added!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)

@admin_bp.route('/categories/edit/<int:cid>', methods=['GET', 'POST'])
@admin_required
def edit_category(cid):
    db = get_db()
    cat = db.execute("SELECT * FROM categories WHERE id=?", (cid,)).fetchone()
    if request.method == 'POST':
        db.execute("UPDATE categories SET name=?, description=? WHERE id=?",
                   (request.form.get('name'), request.form.get('description'), cid))
        db.commit()
        flash('Category updated!', 'success')
        db.close()
        return redirect(url_for('admin.categories'))
    db.close()
    return render_template('admin/category_form.html', category=cat)

@admin_bp.route('/categories/delete/<int:cid>')
@admin_required
def delete_category(cid):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id=?", (cid,))
    db.commit()
    db.close()
    flash('Category deleted!', 'success')
    return redirect(url_for('admin.categories'))

# ─── SUBCATEGORIES ───
@admin_bp.route('/subcategories')
@admin_required
def subcategories():
    db = get_db()
    subs = db.execute("""SELECT s.*, c.name as cat_name FROM subcategories s
        JOIN categories c ON s.category_id=c.id ORDER BY s.created_at DESC""").fetchall()
    db.close()
    return render_template('admin/subcategories.html', subcategories=subs)

@admin_bp.route('/subcategories/add', methods=['GET', 'POST'])
@admin_required
def add_subcategory():
    db = get_db()
    cats = db.execute("SELECT * FROM categories WHERE is_active=1").fetchall()
    if request.method == 'POST':
        db.execute("INSERT INTO subcategories (category_id, name) VALUES (?,?)",
                   (request.form.get('category_id'), request.form.get('name')))
        db.commit()
        db.close()
        flash('Subcategory added!', 'success')
        return redirect(url_for('admin.subcategories'))
    db.close()
    return render_template('admin/subcategory_form.html', sub=None, categories=cats)

@admin_bp.route('/subcategories/delete/<int:sid>')
@admin_required
def delete_subcategory(sid):
    db = get_db()
    db.execute("DELETE FROM subcategories WHERE id=?", (sid,))
    db.commit()
    db.close()
    flash('Subcategory deleted!', 'success')
    return redirect(url_for('admin.subcategories'))

# ─── PRODUCTS ───
@admin_bp.route('/products')
@admin_required
def products():
    db = get_db()
    prods = db.execute("""SELECT p.*, b.name as brand_name, c.name as cat_name
        FROM products p LEFT JOIN brands b ON p.brand_id=b.id
        LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.created_at DESC""").fetchall()
    db.close()
    return render_template('admin/products.html', products=prods)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    db = get_db()
    brands = db.execute("SELECT * FROM brands WHERE is_active=1").fetchall()
    cats = db.execute("SELECT * FROM categories WHERE is_active=1").fetchall()
    subs = db.execute("SELECT * FROM subcategories WHERE is_active=1").fetchall()
    if request.method == 'POST':
        img1 = save_image(request.files.get('image1'))
        img2 = save_image(request.files.get('image2'))
        img3 = save_image(request.files.get('image3'))
        db.execute("""INSERT INTO products (name, description, price, discount_price, stock,
            brand_id, category_id, subcategory_id, image1, image2, image3, shipping_charge, is_featured)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (request.form.get('name'), request.form.get('description'),
                    request.form.get('price'), request.form.get('discount_price') or None,
                    request.form.get('stock', 0), request.form.get('brand_id') or None,
                    request.form.get('category_id') or None, request.form.get('subcategory_id') or None,
                    img1, img2, img3, request.form.get('shipping_charge', 0),
                    1 if request.form.get('is_featured') else 0))
        db.commit()
        db.close()
        flash('Product added!', 'success')
        return redirect(url_for('admin.products'))
    db.close()
    return render_template('admin/product_form.html', product=None, brands=brands, categories=cats, subcategories=subs)

@admin_bp.route('/products/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def edit_product(pid):
    db = get_db()
    prod = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    brands = db.execute("SELECT * FROM brands WHERE is_active=1").fetchall()
    cats = db.execute("SELECT * FROM categories WHERE is_active=1").fetchall()
    subs = db.execute("SELECT * FROM subcategories WHERE is_active=1").fetchall()
    if request.method == 'POST':
        img1 = save_image(request.files.get('image1')) or prod['image1']
        img2 = save_image(request.files.get('image2')) or prod['image2']
        img3 = save_image(request.files.get('image3')) or prod['image3']
        db.execute("""UPDATE products SET name=?, description=?, price=?, discount_price=?,
            stock=?, brand_id=?, category_id=?, subcategory_id=?, image1=?, image2=?, image3=?,
            shipping_charge=?, is_featured=? WHERE id=?""",
                   (request.form.get('name'), request.form.get('description'),
                    request.form.get('price'), request.form.get('discount_price') or None,
                    request.form.get('stock', 0), request.form.get('brand_id') or None,
                    request.form.get('category_id') or None, request.form.get('subcategory_id') or None,
                    img1, img2, img3, request.form.get('shipping_charge', 0),
                    1 if request.form.get('is_featured') else 0, pid))
        db.commit()
        db.close()
        flash('Product updated!', 'success')
        return redirect(url_for('admin.products'))
    db.close()
    return render_template('admin/product_form.html', product=prod, brands=brands, categories=cats, subcategories=subs)

@admin_bp.route('/products/delete/<int:pid>')
@admin_required
def delete_product(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    db.close()
    flash('Product deleted!', 'success')
    return redirect(url_for('admin.products'))

# ─── ORDERS ───
@admin_bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', '')
    db = get_db()
    if status:
        ords = db.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        ords = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/orders.html', orders=ords, status=status)

@admin_bp.route('/orders/<int:oid>')
@admin_required
def order_detail(oid):
    db = get_db()
    order = db.execute("SELECT o.*, u.email as user_email FROM orders o LEFT JOIN users u ON o.user_id=u.id WHERE o.id=?", (oid,)).fetchone()
    items = db.execute("""SELECT oi.*, p.name, p.image1 FROM order_items oi
        JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""", (oid,)).fetchall()
    db.close()
    return render_template('admin/order_detail.html', order=order, items=items)

@admin_bp.route('/orders/<int:oid>/status', methods=['POST'])
@admin_required
def update_order_status(oid):
    status = request.form.get('status')
    db = get_db()
    db.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    db.commit()
    db.close()
    flash(f'Order status updated to {status}.', 'success')
    return redirect(url_for('admin.order_detail', oid=oid))

@admin_bp.route('/orders/search', methods=['GET', 'POST'])
@admin_required
def search_order():
    order = None
    if request.method == 'POST':
        num = request.form.get('order_number', '').strip()
        db = get_db()
        order = db.execute("SELECT * FROM orders WHERE order_number=?", (num,)).fetchone()
        db.close()
        if not order:
            flash('Order not found.', 'error')
    return render_template('admin/search_order.html', order=order)

# ─── REVIEWS ───
@admin_bp.route('/reviews')
@admin_required
def reviews():
    db = get_db()
    revs = db.execute("""SELECT r.*, p.name as product_name FROM reviews r
        JOIN products p ON r.product_id=p.id ORDER BY r.created_at DESC""").fetchall()
    db.close()
    return render_template('admin/reviews.html', reviews=revs)

@admin_bp.route('/reviews/<int:rid>/approve')
@admin_required
def approve_review(rid):
    db = get_db()
    db.execute("UPDATE reviews SET status='approved' WHERE id=?", (rid,))
    db.commit()
    db.close()
    flash('Review approved!', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/<int:rid>/reject')
@admin_required
def reject_review(rid):
    db = get_db()
    db.execute("UPDATE reviews SET status='rejected' WHERE id=?", (rid,))
    db.commit()
    db.close()
    flash('Review rejected.', 'success')
    return redirect(url_for('admin.reviews'))

# ─── USERS ───
@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    users = db.execute("SELECT * FROM users WHERE user_type='user' ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/users.html', users=users)

# ─── REPORTS ───
@admin_bp.route('/reports')
@admin_required
def reports():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    db = get_db()
    if from_date and to_date:
        orders = db.execute("""SELECT * FROM orders WHERE date(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC""", (from_date, to_date)).fetchall()
    else:
        orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    total_sales = sum(o['total_amount'] for o in orders)
    db.close()
    return render_template('admin/reports.html', orders=orders, total_sales=total_sales,
                           from_date=from_date, to_date=to_date)
