# Agregar esta función a database.py

def create_afiliaciones_table():
    """Crear tabla de afiliaciones si no existe"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Crear tabla de afiliaciones
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
    
    # Agregar columna de meta_afiliaciones a employees si no existe
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN meta_afiliaciones INTEGER DEFAULT 50")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    
    conn.commit()
    conn.close()

# Modificar la función create_tables() para incluir la nueva tabla
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