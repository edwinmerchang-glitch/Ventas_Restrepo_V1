import sqlite3
import os
from datetime import datetime

DB_PATH = "ventas.db"

def get_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Crear todas las tablas necesarias"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Tabla de usuarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'empleado'
        )
    """)
    
    # Tabla de empleados
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT,
            department TEXT,
            goal INTEGER DEFAULT 300,
            meta_afiliaciones INTEGER DEFAULT 50,
            user_id INTEGER UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    """)
    
    # Tabla de ventas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            autoliquidable INTEGER DEFAULT 0,
            oferta INTEGER DEFAULT 0,
            marca INTEGER DEFAULT 0,
            adicional INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            UNIQUE(employee_id, date)
        )
    """)
    
    # Tabla de afiliaciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS afiliaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            UNIQUE(employee_id, fecha)
        )
    """)
    
    conn.commit()
    conn.close()

def migrate_database():
    """Agregar columnas nuevas si no existen"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Agregar columna meta_afiliaciones a employees si no existe
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN meta_afiliaciones INTEGER DEFAULT 50")
        print("Columna meta_afiliaciones agregada a employees")
    except sqlite3.OperationalError:
        # La columna ya existe
        pass
    
    conn.commit()
    conn.close()

def verify_database():
    """Verificar que la base de datos esté correctamente configurada"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Verificar tablas
    tables = ['users', 'employees', 'sales', 'afiliaciones']
    for table in tables:
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cur.fetchone() is None:
            print(f"Tabla {table} no encontrada, creando...")
            create_tables()
            break
    
    conn.close()
    print("✅ Base de datos verificada correctamente")

def init_database():
    """Inicializar la base de datos"""
    create_tables()
    migrate_database()
    verify_database()
    print("✅ Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_database()