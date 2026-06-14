from flask import Flask
from database.db import init_db
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp
import os

app = Flask(__name__)
app.secret_key = 'shopportal_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
