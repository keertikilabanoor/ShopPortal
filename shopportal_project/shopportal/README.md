# 🛒 ShopPortal — Python Flask + SQLite Shopping Portal

## Tech Stack
- **Backend:** Python 3 + Flask
- **Database:** SQLite (built-in, zero installation)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Icons:** Font Awesome 6

---

## ✅ How to Run in VS Code

### Step 1 — Open Project in VS Code
```
File → Open Folder → Select the "shopportal" folder
```

### Step 2 — Open Terminal in VS Code
```
Terminal → New Terminal  (or press Ctrl + `)
```

### Step 3 — Create Virtual Environment
```bash
python -m venv venv
```

### Step 4 — Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 5 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 6 — Run the App
```bash
python app.py
```

### Step 7 — Open in Browser
```
http://127.0.0.1:5000
```

---

## 🔐 Login Credentials

| Role  | Email              | Password  |
|-------|--------------------|-----------|
| Admin | admin@shop.com     | admin123  |
| User  | Register yourself  | -         |

---

## 📁 Project Structure
```
shopportal/
├── app.py                  ← Entry point
├── requirements.txt        ← Dependencies
├── database/
│   ├── db.py               ← SQLite setup + sample data
│   └── shop.db             ← Auto-created on first run
├── routes/
│   ├── auth.py             ← Login, Register, Logout
│   ├── user.py             ← Shop, Cart, Wishlist, Orders
│   ├── admin.py            ← Admin panel
│   └── api.py              ← AJAX endpoints
├── templates/
│   ├── base.html           ← User base layout
│   ├── login.html
│   ├── register.html
│   ├── user/               ← All user pages
│   └── admin/              ← All admin pages
└── static/
    ├── css/
    │   ├── style.css       ← User styles
    │   └── admin.css       ← Admin styles
    ├── js/main.js
    └── images/uploads/     ← Uploaded product images
```

---

## 🌐 URLs

| URL                         | Description             |
|-----------------------------|-------------------------|
| http://127.0.0.1:5000       | Homepage                |
| http://127.0.0.1:5000/shop  | All Products            |
| http://127.0.0.1:5000/login | Login                   |
| http://127.0.0.1:5000/admin/dashboard | Admin Panel   |

---

## ❓ Notes
- SQLite database (`shop.db`) is created automatically on first run
- No MySQL, no XAMPP needed
- Sample data (brands, categories, products) is auto-loaded
- Upload product images from Admin Panel → Products → Add Product
