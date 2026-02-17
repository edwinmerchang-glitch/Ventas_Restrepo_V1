import sqlite3
import os
from pathlib import Path

# Usar una ruta absoluta para la base de datos
DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "app.db"

def get_connection():
    """Obtener conexión a la base de datos con persistencia garantizada"""
    try:
        # Crear el directorio data si no existe
        DB_DIR.mkdir(exist_ok=True)
        
        # Conectar a la base de datos con timeout para evitar bloqueos
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        
        # Habilitar foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def create_tables():
    """Crear tablas si no existen"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Tabla de usuarios
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
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
            goal INTEGER DEFAULT 100,
            user_id INTEGER UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Tabla de ventas
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            autoliquidable INTEGER DEFAULT 0,
            oferta INTEGER DEFAULT 0,
            marca INTEGER DEFAULT 0,
            adicional INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
        """)

        # Crear índices para mejorar el rendimiento
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_employee ON sales(employee_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_employees_user ON employees(user_id)")
        
        conn.commit()
        print("✅ Tablas creadas/verificadas correctamente")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
# Agregar después de create_tables() o dentro de migrate_database()

def create_affiliations_tables():
    """Crear tablas para el sistema de afiliaciones"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Tabla de metas de afiliación por empleado
        cur.execute("""
        CREATE TABLE IF NOT EXISTS affiliation_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            monthly_goal INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, year, month)
        )
        """)

        # Tabla de tipos de afiliación
        cur.execute("""
        CREATE TABLE IF NOT EXISTS affiliation_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            points_value REAL DEFAULT 1.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabla de registro de afiliaciones
        cur.execute("""
        CREATE TABLE IF NOT EXISTS affiliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            affiliation_type_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            registration_date TEXT NOT NULL,
            observations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            FOREIGN KEY (affiliation_type_id) REFERENCES affiliation_types(id) ON DELETE CASCADE
        )
        """)

        # Insertar tipos de afiliación por defecto
        default_types = [
            ("Afiliación Tradicional", "Afiliación regular al POS", 1.0),
            ("Afiliación Especial", "Afiliación con beneficios adicionales", 1.5),
            ("Reactivación", "Reactivación de afiliación vencida", 0.8),
            ("Portabilidad", "Portabilidad desde otra EPS", 1.2),
            ("Beneficiario", "Afiliación de beneficiario", 0.5)
        ]
        
        for type_name, desc, points in default_types:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO affiliation_types (name, description, points_value)
                    VALUES (?, ?, ?)
                """, (type_name, desc, points))
            except:
                pass

        conn.commit()
        print("✅ Tablas de afiliaciones creadas/verificadas correctamente")
        
    except Exception as e:
        print(f"❌ Error creando tablas de afiliaciones: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Modificar la función migrate_database para incluir las nuevas tablas
def migrate_database():
    """Migrar base de datos existente si es necesario"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verificar y agregar columnas faltantes en employees
        cur.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'position' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN position TEXT DEFAULT 'Sin cargo'")
            print("✅ Columna 'position' agregada a employees")
        
        if 'department' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN department TEXT DEFAULT 'Sin departamento'")
            print("✅ Columna 'department' agregada a employees")
        
        if 'created_at' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'created_at' agregada a employees")
            
        # Agregar columna de meta de afiliaciones si no existe
        if 'affiliation_goal' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN affiliation_goal INTEGER DEFAULT 0")
            print("✅ Columna 'affiliation_goal' agregada a employees")
        
        # Verificar y agregar columnas en sales
        cur.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'created_at' not in columns:
            cur.execute("ALTER TABLE sales ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'created_at' agregada a sales")
        
        conn.commit()
        
        # Crear tablas de afiliaciones
        create_affiliations_tables()
        
        print("✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def migrate_database():
    """Migrar base de datos existente si es necesario"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verificar y agregar columnas faltantes en employees
        cur.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'position' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN position TEXT DEFAULT 'Sin cargo'")
            print("✅ Columna 'position' agregada a employees")
        
        if 'department' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN department TEXT DEFAULT 'Sin departamento'")
            print("✅ Columna 'department' agregada a employees")
        
        if 'created_at' not in columns:
            cur.execute("ALTER TABLE employees ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'created_at' agregada a employees")
        
        # Verificar y agregar columnas en sales
        cur.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'created_at' not in columns:
            cur.execute("ALTER TABLE sales ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'created_at' agregada a sales")
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def verify_database():
    """Verificar que la base de datos está funcionando correctamente"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verificar tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"📊 Tablas encontradas: {[t[0] for t in tables]}")
        
        # Verificar datos existentes
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"👥 Usuarios en BD: {user_count}")
        
        cur.execute("SELECT COUNT(*) FROM employees")
        emp_count = cur.fetchone()[0]
        print(f"🧑‍💼 Empleados en BD: {emp_count}")
        
        cur.execute("SELECT COUNT(*) FROM sales")
        sales_count = cur.fetchone()[0]
        print(f"📝 Ventas en BD: {sales_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False
    finally:
        if conn:
            conn.close()