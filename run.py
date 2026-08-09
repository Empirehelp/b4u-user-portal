from flask import Flask, redirect, url_for
from database import init_db
from auth import auth_bp
from dashboard import dash_bp
from admin_routes import admin_bp

app = Flask(__name__)
app.secret_key = 'b4u_network_super_secret_key_change_in_production'

app.register_blueprint(auth_bp)
app.register_blueprint(dash_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    return redirect(url_for('auth_bp.login'))

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
