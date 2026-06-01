import sqlite3
import os
from datetime import datetime

DB_PATH = "ventas.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # mejor concurrencia
    conn.execute("PRAGMA foreign_keys=ON")     # integridad referencial
    return conn


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'empleado'
        );

        CREATE TABLE IF NOT EXISTS employees (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            name               TEXT    NOT NULL,
            position           TEXT,
            department         TEXT,
            goal               INTEGER DEFAULT 300,
            meta_afiliaciones  INTEGER DEFAULT 50,
            user_id            INTEGER UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id    INTEGER NOT NULL,
            date           DATE    NOT NULL,
            autoliquidable INTEGER DEFAULT 0,
            oferta         INTEGER DEFAULT 0,
            marca          INTEGER DEFAULT 0,
            adicional      INTEGER DEFAULT 0,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            UNIQUE(employee_id, date)
        );

        CREATE TABLE IF NOT EXISTS afiliaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            fecha       DATE    NOT NULL,
            cantidad    INTEGER NOT NULL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            UNIQUE(employee_id, fecha)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            action      TEXT NOT NULL,
            table_name  TEXT,
            record_id   INTEGER,
            detail      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def migrate_database():
    conn = get_connection()
    cur = conn.cursor()

    migrations = [
        ("employees", "meta_afiliaciones", "INTEGER DEFAULT 50"),
        ("sales",     "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]

    for table, column, definition in migrations:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass  # ya existe

    # Crear audit_log si no existe (puede que sea una BD antigua)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def verify_database():
    conn = get_connection()
    cur = conn.cursor()
    tables = ['users', 'employees', 'sales', 'afiliaciones', 'audit_log']
    for table in tables:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        if cur.fetchone() is None:
            conn.close()
            create_tables()
            return
    conn.close()


def log_audit(user_id, username, action, table_name=None, record_id=None, detail=None):
    """Registra una acción en el log de auditoría."""
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO audit_log (user_id, username, action, table_name, record_id, detail)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, action, table_name, record_id, detail),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # log nunca debe romper el flujo principal


def init_database():
    create_tables()
    migrate_database()
    verify_database()
