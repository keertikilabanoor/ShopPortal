from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('user.home'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['full_name'] = user['full_name'] or user['username']
            flash('Welcome back, ' + (user['full_name'] or user['username']) + '!', 'success')
            if user['user_type'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.home'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email=? OR username=?", (email, username)).fetchone()
        if existing:
            flash('Email or username already exists.', 'error')
            db.close()
            return render_template('register.html')
        db.execute("""INSERT INTO users (username, email, password, full_name, phone)
                      VALUES (?,?,?,?,?)""",
                   (username, email, generate_password_hash(password), full_name, phone))
        db.commit()
        db.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
