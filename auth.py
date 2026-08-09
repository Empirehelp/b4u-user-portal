from flask import Blueprint, request, redirect, render_template_string, session, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

auth_bp = Blueprint('auth_bp', __name__)

def hash_pwd(password):
    return generate_password_hash(password)

def verify_pwd(pwhash, password):
    return check_password_hash(pwhash, password)

def generate_uid():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LOGIN - B4U NETWORK</title>
    <style>
        body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: rgba(35, 13, 56, 0.8); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 14px; padding: 35px; width: 360px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        h2 { color: #fdb913; text-align: center; margin-bottom: 25px; font-size: 20px; }
        input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 15px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #fdb913; }
        .btn { width: 100%; padding: 12px; background: #fdb913; border: none; border-radius: 8px; color: #130620; font-weight: bold; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #e0a30f; }
        p { text-align: center; font-size: 13px; color: #a78bfa; margin-top: 20px; }
        a { color: #fdb913; text-decoration: none; }
        .msg { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 10px; border-radius: 6px; font-size: 12px; text-align: center; margin-bottom: 15px; border: 1px solid rgba(239, 68, 68, 0.4); }
    </style>
</head>
<body>
    <div class="card">
        <h2>B4U NETWORK LOGIN</h2>
        {% if msg %}
        <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Email or UID (e.g. B4U1000)" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn">LOGIN</button>
        </form>
        <p style="font-size:11px; color:#10b981; margin-top:10px;">Default Admin: admin@b4u.com / admin123</p>
        <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
</body>
</html>
"""

REGISTER_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>REGISTER - B4U NETWORK</title>
    <style>
        body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: rgba(35, 13, 56, 0.8); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 14px; padding: 35px; width: 380px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        h2 { color: #fdb913; text-align: center; margin-bottom: 25px; font-size: 20px; }
        input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 12px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #fdb913; }
        .btn { width: 100%; padding: 12px; background: #10b981; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #059669; }
        p { text-align: center; font-size: 13px; color: #a78bfa; margin-top: 15px; }
        a { color: #fdb913; text-decoration: none; }
        .msg { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 10px; border-radius: 6px; font-size: 12px; text-align: center; margin-bottom: 15px; border: 1px solid rgba(239, 68, 68, 0.4); }
    </style>
</head>
<body>
    <div class="card">
        <h2>CREATE ACCOUNT</h2>
        {% if msg %}
        <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email Address" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="text" name="sponsor_uid" value="{{ sponsor_ref }}" placeholder="Sponsor UID (Optional)">
            <button type="submit" class="btn">REGISTER NOW</button>
        </form>
        <p>Already have an account? <a href="/login">Login here</a></p>
    </div>
</body>
</html>
"""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s OR uid = %s", (username, username))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and verify_pwd(user['password'], password):
                session['uid'] = user['uid']
                session['name'] = user['name']
                if user['email'] == 'admin@b4u.com' or user['rank'] == 'Admin':
                    return redirect('/admin')
                return redirect('/dashboard')
            else:
                msg = "Invalid email/UID or password!"
        except Exception as e:
            msg = f"System Error: {str(e)}"
            
    return render_template_string(LOGIN_HTML, msg=msg)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    msg = None
    sponsor_ref = request.args.get('ref', '')
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = hash_pwd(request.form.get('password'))
        sponsor_uid = request.form.get('sponsor_uid') or 'None'
        uid = generate_uid()
        
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (uid, name, email, password, sponsor_uid) VALUES (%s, %s, %s, %s, %s)",
                        (uid, name, email, password, sponsor_uid))
            conn.commit()
            cur.close()
            conn.close()
            return redirect('/login')
        except Exception as e:
            msg = f"Registration error: {str(e)}"
            
    return render_template_string(REGISTER_HTML, msg=msg, sponsor_ref=sponsor_ref)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
