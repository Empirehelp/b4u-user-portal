import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/b4u_db")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                uid VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                sponsor_uid VARCHAR(50) DEFAULT 'None',
                inv NUMERIC(12, 2) DEFAULT 0.00,
                profit_wallet NUMERIC(12, 2) DEFAULT 0.00,
                rank VARCHAR(50) DEFAULT 'Member',
                status VARCHAR(20) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id SERIAL PRIMARY KEY,
                uid VARCHAR(50) NOT NULL,
                method VARCHAR(50) NOT NULL,
                amount NUMERIC(12, 2) NOT NULL,
                address TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                uid VARCHAR(50) NOT NULL,
                method VARCHAR(50) NOT NULL,
                amount NUMERIC(12, 2) NOT NULL,
                address TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert Default Admin if not exists
        cur.execute("SELECT * FROM users WHERE email = 'admin@b4u.com'")
        if not cur.fetchone():
            admin_pwd = generate_password_hash('admin123')
            cur.execute("""
                INSERT INTO users (uid, name, email, password, rank, status) 
                VALUES ('B4U1000', 'Admin', 'admin@b4u.com', %s, 'Admin', 'Active')
            """, (admin_pwd,))
            
        conn.commit()
        print("[INFO] Database initialized & Admin created successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Database init error: {e}")
    finally:
        cur.close()
        conn.close()
