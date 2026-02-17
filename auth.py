import sqlite3
import hashlib
from database import get_connection

def hash_password(password):
    """Hashear contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    """Autenticar usuario"""
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(password)
    cur.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed)
    )
    user = cur.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "role": user[2]
        }
    return None

def create_user(username, password, role="empleado"):
    """Crear un nuevo usuario"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Verificar si el usuario ya existe
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        raise ValueError(f"El usuario '{username}' ya existe")
    
    # Crear usuario
    hashed = hash_password(password)
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed, role)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return (user_id, username, role)

def get_all_users():
    """Obtener todos los usuarios"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.role, e.name, e.department 
        FROM users u
        LEFT JOIN employees e ON u.id = e.user_id
        ORDER BY u.username
    """)
    users = cur.fetchall()
    conn.close()
    return users