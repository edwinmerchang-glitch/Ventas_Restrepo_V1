import sqlite3
import os

DB_PATH = "data/app.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password BLOB,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        position TEXT,
        department TEXT,
        goal INTEGER DEFAULT 100,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date TEXT,
        autoliquidable INTEGER,
        oferta INTEGER,
        marca INTEGER,
        adicional INTEGER,
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    )
    """)

    conn.commit()
    conn.close()

def migrate_database():
    """Función para migrar base de datos existente (agregar nuevas columnas)"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verificar si las columnas existen y agregarlas si no
        cur.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'position' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN position TEXT DEFAULT 'Sin cargo'")
        
        if 'department' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN department TEXT DEFAULT 'Sin departamento'")
        
        conn.commit()
        conn.close()
        print("Migración de base de datos completada exitosamente")
    except Exception as e:
        print(f"Error en migración: {e}")