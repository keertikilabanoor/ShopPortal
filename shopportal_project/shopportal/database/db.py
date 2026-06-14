import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'shop.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            profile_pic TEXT DEFAULT 'default.png',
            user_type TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            logo TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            discount_price REAL,
            stock INTEGER DEFAULT 0,
            brand_id INTEGER,
            category_id INTEGER,
            subcategory_id INTEGER,
            image1 TEXT,
            image2 TEXT,
            image3 TEXT,
            is_active INTEGER DEFAULT 1,
            is_featured INTEGER DEFAULT 0,
            shipping_charge REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
        );

        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            user_id INTEGER,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            total_amount REAL,
            payment_method TEXT DEFAULT 'COD',
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            shipping_charge REAL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            rating INTEGER DEFAULT 5,
            comment TEXT,
            name TEXT,
            email TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    # Create default admin
    admin_exists = c.execute("SELECT id FROM users WHERE user_type='admin'").fetchone()
    if not admin_exists:
        c.execute("""INSERT INTO users (username, email, password, full_name, user_type)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('admin', 'admin@shop.com', generate_password_hash('admin123'), 'Administrator', 'admin'))

    # Insert sample data
    brand_count = c.execute("SELECT COUNT(*) FROM brands").fetchone()[0]
    if brand_count == 0:
        brands = [
            ('Samsung', None, 'Korean electronics giant'),
            ('Apple', None, 'Premium tech brand'),
            ('Dell', None, 'PC and laptop maker'),
            ('HP', None, 'Computers and printers'),
            ('Nike', None, 'Sports and lifestyle'),
            ('L\'Oreal', None, 'Beauty and cosmetics'),
        ]
        c.executemany("INSERT INTO brands (name, logo, description) VALUES (?,?,?)", brands)

        categories = [
            ('Mobiles', None, 'Smartphones and accessories'),
            ('Laptops', None, 'Laptops and notebooks'),
            ('Fashion', None, 'Clothing and accessories'),
            ('Beauty', None, 'Skincare and cosmetics'),
            ('Electronics', None, 'Gadgets and electronics'),
            ('Sports', None, 'Sports equipment'),
        ]
        c.executemany("INSERT INTO categories (name, image, description) VALUES (?,?,?)", categories)

        subcategories = [
            (1, 'Smartphones'), (1, 'Feature Phones'), (1, 'Tablets'),
            (2, 'Gaming Laptops'), (2, 'Ultrabooks'), (2, 'Business Laptops'),
            (3, "Men's Clothing"), (3, "Women's Clothing"), (3, 'Kids'),
            (4, 'Skincare'), (4, 'Haircare'), (4, 'Makeup'),
        ]
        c.executemany("INSERT INTO subcategories (category_id, name) VALUES (?,?)", subcategories)

        products = [
            ('Samsung Galaxy S24', 'Latest flagship smartphone with AI features', 79999, 74999, 50, 1, 1, 1, None, None, None, 1, 1, 99),
            ('iPhone 15 Pro', 'Apple flagship with titanium design', 134900, 129900, 30, 2, 1, 1, None, None, None, 1, 1, 0),
            ('Dell XPS 15', 'Premium laptop with OLED display', 149999, 139999, 20, 3, 2, 4, None, None, None, 1, 1, 199),
            ('HP Pavilion 15', 'Everyday laptop for work and study', 65999, 59999, 35, 4, 2, 6, None, None, None, 1, 1, 149),
            ('Nike Air Max', 'Comfortable sports shoes', 8999, 7499, 100, 5, 3, 7, None, None, None, 1, 1, 49),
            ('L\'Oreal Face Cream', 'Advanced moisturizing face cream', 899, 749, 200, 6, 4, 10, None, None, None, 1, 1, 29),
            ('Samsung 55" QLED TV', '4K QLED Smart TV', 89999, 79999, 15, 1, 5, None, None, None, None, 1, 1, 499),
            ('Apple AirPods Pro', 'Wireless earbuds with ANC', 24900, 22900, 60, 2, 5, None, None, None, None, 1, 1, 0),
            ('Dell Gaming Mouse', 'High precision gaming mouse', 3499, 2999, 80, 3, 5, None, None, None, None, 1, 0, 49),
            ('HP Ink Cartridge', 'Original HP ink cartridge', 1299, 1099, 150, 4, 5, None, None, None, None, 1, 0, 29),
            ('Nike Running Shorts', 'Breathable running shorts', 2499, 1999, 120, 5, 3, 7, None, None, None, 1, 0, 49),
            ('L\'Oreal Shampoo', 'Nourishing hair shampoo', 450, 399, 300, 6, 4, 11, None, None, None, 1, 0, 29),
        ]
        c.executemany("""INSERT INTO products
            (name, description, price, discount_price, stock, brand_id, category_id, subcategory_id,
             image1, image2, image3, is_active, is_featured, shipping_charge)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", products)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")
