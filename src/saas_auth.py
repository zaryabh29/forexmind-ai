import hashlib
from database.db import get_db_connection

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username: str, email: str, password: str, tier: str = "Pro"):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure user table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        tier TEXT DEFAULT 'Pro',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    pwd_hash = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash, tier) VALUES (?, ?, ?, ?)",
                       (username, email, pwd_hash, tier))
        conn.commit()
        conn.close()
        return {"status": "SUCCESS", "message": f"User {username} registered successfully on {tier} tier."}
    except Exception as e:
        conn.close()
        return {"status": "FAILED", "message": "Username or email already registered."}

def authenticate_user(username: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"authenticated": False, "message": "Invalid username or password."}

    pwd_hash = hash_password(password)
    if row['password_hash'] == pwd_hash:
        return {
            "authenticated": True,
            "username": row['username'],
            "email": row['email'],
            "tier": row['tier'],
            "token": f"token_{row['username']}_active"
        }
    
    return {"authenticated": False, "message": "Invalid username or password."}
