import bcrypt
from database import get_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def create_user(username, password, role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                (username, hash_password(password), role))
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,password,role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and verify_password(password, row[1]):
        return {"id": row[0], "role": row[2]}
    return None
