import bcrypt
from database import get_connection
import sqlite3

def hash_password(password):
    """Hashear contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verificar contraseña"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_user(username, password, role):
    """Crear nuevo usuario con persistencia garantizada"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verificar si el usuario ya existe
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            raise ValueError(f"El usuario '{username}' ya existe")
        
        # Insertar nuevo usuario
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?,?,?)",
            (username, hash_password(password), role)
        )
        conn.commit()
        
        # Verificar que se guardó
        cur.execute("SELECT id, username, role FROM users WHERE username = ?", (username,))
        new_user = cur.fetchone()
        print(f"✅ Usuario '{username}' creado con ID: {new_user[0]}")
        
        return new_user
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Error de integridad: {e}")
        if conn:
            conn.rollback()
        raise ValueError(f"El usuario '{username}' ya existe")
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def authenticate(username, password):
    """Autenticar usuario"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id, password, role FROM users WHERE username = ?", 
            (username,)
        )
        row = cur.fetchone()
        
        if row and verify_password(password, row[1]):
            user_data = {"id": row[0], "role": row[2]}
            print(f"✅ Usuario autenticado: {username} - Rol: {row[2]}")
            return user_data
        
        print(f"❌ Autenticación fallida para: {username}")
        return None
        
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_users():
    """Obtener todos los usuarios (para administración)"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.id, u.username, u.role, 
                   e.name as employee_name, e.department
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            ORDER BY u.id
        """)
        
        return cur.fetchall()
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_users_with_employees():
    """Obtener todos los usuarios con información de empleados"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.id, u.username, u.role, 
                   e.name as employee_name,
                   e.id as employee_id
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            ORDER BY u.username
        """)
        
        return cur.fetchall()
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return []
    finally:
        if conn:
            conn.close()