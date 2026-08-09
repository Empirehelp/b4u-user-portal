from flask import Blueprint, request, redirect, render_template_string, session, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

auth_bp = Blueprint('auth_bp', __name__)

def hash_pwd(password):
    return generate_password_hash(password)

def verify_pwd(pwhash, password):
    if not pwhash:
        return False
    if pwhash == password:
        return True
    try:
        return check_password_hash(pwhash, password)
    except:
        return False

def generate_uid():
    return 'B4U' + ''.join(random.choices(string.digits, k=5))

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>LOGIN - B4U EMPIRE</title><style>body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }.card { background: rgba(35, 13, 56, 0.8); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 14px; padding: 35px; width: 360px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }h2 { color: #fdb913; text-align: center; margin-bottom: 25px; font-size: 20px; }input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 15px; box-sizing: border-box; outline: none; }input:focus { border-color: #fdb913; }.btn { width: 100%; padding: 12px; background: #fdb913; border: none; border-radius: 8px; color: #130620; font-weight: bold; cursor: pointer; font-size: 14px; }.btn:hover { background: #e0a30f; }p { text-align: center; font-size: 13px; color: #a78bfa; margin-top: 20px; }a { color: #fdb913; text-decoration: none; }.msg { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 10px; border-radius: 6px; font-size: 12px; text-align: center; margin-bottom: 15px; border: 1px solid rgba(239, 68, 68, 0.4); }</style></head><body><div class="card"><h2>B4U EMPIRE LOGIN</h2>{% if msg %}<div class="msg">{{ msg }}</div>{% endif %}<form method="POST"><input type="text" name="username" placeholder="Email or UID (e.g. B4U10001)" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="btn">LOGIN</button></form><p>Don't have an account? <a href="/register">Register here</a></p></div></body></html>"""

REGISTER_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>REGISTER - B4U EMPIRE</title><style>body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }.card { background: rgba(35, 13, 56, 0.8); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 14px; padding: 35px; width: 380px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }h2 { color: #fdb913; text-align: center; margin-bottom: 25px; font-size: 20px; }input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 12px; box-sizing: border-box; outline: none; }input:focus { border-color: #fdb913; }.btn { width: 100%; padding: 12px; background: #10b981; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; font-size: 14px; }.btn:hover { background: #059669; }p { text-align: center; font-size: 13px; color: #a78bfa; margin-top: 15px; }a { color: #fdb913; text-decoration: none; }.msg { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 10px; border-radius: 6px; font-size: 12px; text-align: center; margin-bottom: 15px; border: 1px solid rgba(239, 68, 68, 0.4); }</style></head><body><div class="card"><h2>CREATE ACCOUNT</h2>{% if msg %}<div class="msg">{{ msg }}</div>{% endif %}<form method="POST"><input type="text" name="name" placeholder="Full Name" required><input type="email" name="email" placeholder="Email Address" required><input type="password" name="password" placeholder="Password" required><input type="text" name="sponsor_uid" value="{{ sponsor_ref }}" placeholder="Sponsor UID (Optional)"><button type="submit" class="btn">REGISTER NOW</button></form><p>Already have an account? <a href="/login">Login here</a></p></div></body></html>"""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
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
                return redirect('/dashboard')
            else:
                msg = "Invalid email/UID or password!"
        except Exception as e:
            msg = f"Login Error: {str(e)}"
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
            cur.execute("""
                INSERT INTO users (uid, name, email, password, sponsor_uid, wheel_spun)
                VALUES (%s, %s, %s, %s, %s, FALSE)
            """, (uid, name, email, password, sponsor_uid))
            conn.commit()
            cur.close()
            conn.close()

            session['uid'] = uid
            session['name'] = name
            return redirect('/spin_wheel')
        except Exception as e:
            msg = f"Registration error: {str(e)}"
    return render_template_string(REGISTER_HTML, msg=msg, sponsor_ref=sponsor_ref)

@auth_bp.route('/spin_wheel', methods=['GET', 'POST'])
def spin_wheel():
    if 'uid' not in session:
        return redirect('/login')
    uid = session['uid']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT wheel_spun FROM users WHERE uid = %s", (uid,))
    user = cur.fetchone()
    if user and user['wheel_spun']:
        cur.close()
        conn.close()
        return redirect('/dashboard?msg=You have already claimed your signup wheel bonus!')
    
    msg = None
    if request.method == 'POST':
        rewards = [1.00, 5.00, 10.00, 25.00, 50.00]
        won_amount = random.choice(rewards)
        try:
            cur.execute("""
                UPDATE users
                SET profit_wallet = profit_wallet + %s,
                    wheel_spun = TRUE,
                    wheel_bonus = %s
                WHERE uid = %s
            """, (won_amount, won_amount, uid))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(f'/dashboard?msg=Congratulations! You won ${won_amount} from the Signup Wheel Bonus!')
        except Exception as e:
            conn.rollback()
            msg = f"Error: {str(e)}"
    
    cur.close()
    conn.close()
    return """<!DOCTYPE html><html><head><title>Lucky Wheel Bonus - B4U EMPIRE</title><style>body { background: #0f0518; color: #fff; font-family: sans-serif; text-align: center; padding-top: 100px; }.card { background: rgba(35, 13, 56, 0.9); border: 1px solid #4a256d; display: inline-block; padding: 40px; border-radius: 15px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); width: 380px; }h2 { color: #fdb913; }.btn { background: #fdb913; color: #130620; border: none; padding: 15px 30px; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 20px; width: 100%; }.btn:hover { background: #e0a30f; }</style></head><body><div class="card"><h2>🎁 Signup Lucky Wheel</h2><p>Spin the wheel to win instant bonus cash directly into your profit wallet!</p><form method="POST"><button type="submit" class="btn">SPIN NOW</button></form></div></body></html>"""

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
