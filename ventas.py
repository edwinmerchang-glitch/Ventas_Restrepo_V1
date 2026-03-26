import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from database import create_tables, get_connection, migrate_database, verify_database, DB_PATH
from auth import authenticate, create_user, get_all_users
import sqlite3
import time
from keep_alive import init_keep_alive, render_keep_alive_status
from backup_manager import render_backup_page

# Configuración de página
st.set_page_config(
    "Ventas Equipo Locatel Restrepo", 
    layout="wide", 
    page_icon="🏥",
    initial_sidebar_state="collapsed"
)

# ============= INICIALIZACIÓN DE BASE DE DATOS =============
with st.spinner("🔄 Inicializando sistema..."):
    try:
        create_tables()
        migrate_database()
        verify_database()
    except Exception as e:
        st.error(f"❌ Error inicializando base de datos: {e}")
        st.stop()

def create_default_admin():
    """Crear admin por defecto si no hay usuarios"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        conn.close()
        
        if total_users == 0:
            create_user("admin", "admin123", "admin")
            st.success("✅ Usuario admin creado por defecto (admin/admin123)")
    except Exception as e:
        st.error(f"Error al crear admin por defecto: {e}")

create_default_admin()

# ============= LISTAS PERSONALIZADAS =============
CARGOS = [
    "Ais Droguería",
    "Ais Equipos Médicos", 
    "Ais Pasillos",
    "Ais Cajas"
]

DEPARTAMENTOS = [
    "Droguería",
    "Equipos Médicos",
    "Pasillos",
    "Cajas"
]

# ============= ESTILOS CSS MODERNOS =============
def load_css():
    """Cargar estilos CSS modernos"""
    st.markdown("""
    <style>
    /* Importar fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset y estilos base */
    .stApp {
        background: #f5f7fa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Ocultar el header de Streamlit */
    header[data-testid="stHeader"] {
        background: transparent;
        box-shadow: none;
    }
    
    /* Estilo para el contenido principal */
    .main-content {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Tarjetas modernas */
    .modern-card {
        background: white;
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
    }
    
    .modern-card:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* Header principal */
    .app-header {
        background: white;
        padding: 1rem 2rem;
        border-bottom: 1px solid #e9ecef;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .logo-icon {
        font-size: 32px;
    }
    
    .logo-text {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a2e;
        letter-spacing: -0.5px;
    }
    
    .logo-subtitle {
        font-size: 14px;
        color: #6c757d;
        margin-top: 2px;
    }
    
    /* Campos de formulario modernos */
    .modern-input {
        width: 100%;
        padding: 12px 16px;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        font-size: 14px;
        transition: all 0.3s ease;
        background: white;
    }
    
    .modern-input:focus {
        outline: none;
        border-color: #4f7cff;
        box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.1);
    }
    
    /* Botones modernos */
    .modern-btn {
        background: #4f7cff;
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 12px;
        font-weight: 500;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .modern-btn:hover {
        background: #3a5fd0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 124, 255, 0.3);
    }
    
    .modern-btn-secondary {
        background: white;
        color: #4f7cff;
        border: 1px solid #e9ecef;
    }
    
    .modern-btn-secondary:hover {
        background: #f8f9fa;
        border-color: #4f7cff;
    }
    
    /* Grid de búsqueda */
    .search-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .search-field {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .search-label {
        font-size: 14px;
        font-weight: 500;
        color: #495057;
    }
    
    /* Badges y etiquetas */
    .badge-modern {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-success {
        background: #d4edda;
        color: #155724;
    }
    
    .badge-warning {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge-info {
        background: #e7f1ff;
        color: #004085;
    }
    
    /* Footer moderno */
    .modern-footer {
        background: white;
        border-top: 1px solid #e9ecef;
        padding: 1rem 2rem;
        margin-top: 3rem;
        text-align: center;
        font-size: 13px;
        color: #6c757d;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .search-grid {
            grid-template-columns: 1fr;
        }
        
        .app-header {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ============= COMPONENTES MODERNOS =============
def create_modern_header():
    """Crear header moderno"""
    st.markdown("""
    <div class="app-header">
        <div class="logo-container">
            <span class="logo-icon">🏥</span>
            <div>
                <div class="logo-text">Restrepo</div>
                <div class="logo-subtitle">Sistema de Gestión de Ventas</div>
            </div>
        </div>
        <div class="logo-container">
            <span class="badge-modern badge-info">AIS</span>
            <span class="badge-modern badge-success">En línea</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_modern_search_card():
    """Crear tarjeta de búsqueda moderna"""
    st.markdown("""
    <div class="modern-card">
        <h3 style="margin-bottom: 1.5rem; font-weight: 600; color: #1a1a2e;">🔍 Consultar Productos</h3>
        <div class="search-grid">
            <div class="search-field">
                <label class="search-label">Código EAN o Código Material</label>
                <input type="text" class="modern-input" placeholder="Ingresa el código del producto" id="codigo_producto">
            </div>
            <div class="search-field">
                <label class="search-label">Nombre del producto</label>
                <input type="text" class="modern-input" placeholder="Nombre del producto" id="nombre_producto">
            </div>
            <div class="search-field">
                <label class="search-label">Tienda Física</label>
                <select class="modern-input" id="tienda_fisica">
                    <option value="">Seleccionar tienda</option>
                    <option value="Restrepo">Restrepo</option>
                    <option value="Centro">Centro</option>
                    <option value="Norte">Norte</option>
                </select>
            </div>
            <div style="display: flex; gap: 1rem; align-items: flex-end;">
                <button class="modern-btn" onclick="alert('Funcionalidad en desarrollo')">
                    🔍 Consultar
                </button>
                <button class="modern-btn modern-btn-secondary" onclick="document.getElementById('codigo_producto').value=''; document.getElementById('nombre_producto').value='';">
                    🧹 Limpiar
                </button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_modern_login():
    """Pantalla de login moderna"""
    st.markdown("""
    <style>
    .login-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .login-card {
        background: white;
        border-radius: 32px;
        padding: 2.5rem;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-icon {
        font-size: 48px;
        margin-bottom: 1rem;
    }
    .login-title {
        font-size: 28px;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .login-subtitle {
        color: #6c757d;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("""
            <div class="login-card">
                <div class="login-header">
                    <div class="login-icon">🏥</div>
                    <div class="login-title">Bienvenido</div>
                    <div class="login-subtitle">Sistema de Ventas - Restrepo</div>
                </div>
            """, unsafe_allow_html=True)
            
            u = st.text_input("Usuario", placeholder="Ingresa tu usuario", key="login_user")
            p = st.text_input("Contraseña", type="password", placeholder="********", key="login_pass")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("Ingresar", use_container_width=True, type="primary"):
                    if u and p:
                        user = authenticate(u, p)
                        if user:
                            st.session_state.user = user
                            if user["role"] == "admin":
                                st.session_state.page = "Dashboard"
                            else:
                                emp_info = get_employee_info(user["id"])
                                if emp_info:
                                    st.session_state.page = "Registrar ventas"
                                else:
                                    st.session_state.page = "Mi perfil"
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    else:
                        st.warning("⚠️ Completa todos los campos")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_modern_menu():
    """Menú moderno simplificado"""
    if 'sidebar_open' not in st.session_state:
        st.session_state.sidebar_open = False
    
    # Botón hamburguesa
    col1, col2, col3 = st.columns([1, 10, 1])
    with col1:
        if st.button("☰", key="hamburger_btn", help="Abrir menú"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()
    
    if st.session_state.sidebar_open:
        with st.sidebar:
            # Cerrar menú
            col_close1, col_close2 = st.columns([6, 1])
            with col_close2:
                if st.button("✕", key="close_sidebar", help="Cerrar menú"):
                    st.session_state.sidebar_open = False
                    st.rerun()
            
            st.markdown("---")
            
            # Información del usuario
            emp_info = get_employee_info(st.session_state.user["id"])
            if emp_info:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 48px; margin-bottom: 0.5rem;">👤</div>
                    <div style="font-weight: 600; font-size: 16px;">{emp_info[1]}</div>
                    <div style="font-size: 12px; color: #6c757d;">{emp_info[2]}</div>
                    <div style="font-size: 12px; color: #6c757d;">🎯 Meta: {emp_info[4]} uni</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Menú items
            if st.session_state.user["role"] == "admin":
                menu_items = [
                    ("📊 Dashboard", "Dashboard"),
                    ("🏆 Ranking", "Ranking"),
                    ("🧑‍💼 Empleados", "Empleados"),
                    ("👥 Usuarios", "Usuarios"),
                    ("📊 Reportes", "Reportes"),
                    ("📱 Afiliaciones", "Admin Afiliaciones"),
                    ("💾 Backups", "Backups")
                ]
            else:
                menu_items = [
                    ("📝 Registrar ventas", "Registrar ventas"),
                    ("📱 Registrar afiliaciones", "Registrar afiliaciones"),
                    ("📊 Mis afiliaciones", "Mis afiliaciones"),
                    ("📈 Mi Desempeño", "Mi desempeño"),
                    ("👤 Mi perfil", "Mi perfil"),
                    ("🏆 Ranking", "Ranking")
                ]
            
            for label, page in menu_items:
                if st.button(
                    label,
                    key=f"nav_{page}",
                    use_container_width=True,
                    type="primary" if st.session_state.page == page else "secondary"
                ):
                    st.session_state.page = page
                    st.session_state.sidebar_open = False
                    st.rerun()
            
            st.markdown("---")
            
            # Botón cerrar sesión
            if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
                st.session_state.clear()
                st.cache_data.clear()
                st.rerun()

def show_modern_footer():
    """Footer moderno"""
    try:
        ahora_utc = datetime.utcnow()
        hora_colombia = ahora_utc - timedelta(hours=5)
        fecha_hora = hora_colombia.strftime('%d/%m/%Y %H:%M')
    except:
        fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    st.markdown(f"""
    <div class="modern-footer">
        <div>🏥 Locatel Restrepo | AIS | v2.0.0</div>
        <div style="margin-top: 5px;">⏱️ {fecha_hora} (Colombia)</div>
        <div style="margin-top: 5px;">Creado por Edwin Merchan</div>
    </div>
    """, unsafe_allow_html=True)

# ============= FUNCIONES DE UTILIDAD =============
@st.cache_data(ttl=60)
def safe_dataframe(query, params=None):
    """Ejecutar query de forma segura y retornar DataFrame con cache"""
    try:
        conn = get_connection()
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()

def execute_query(query, params=None):
    """Ejecutar query SELECT y retornar resultados"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        results = cur.fetchall()
        return results
    except Exception as e:
        st.error(f"Error en consulta: {e}")
        return []
    finally:
        if conn:
            conn.close()

def execute_insert(query, params=None):
    """Ejecutar query INSERT/UPDATE/DELETE con commit"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_employee_info(user_id):
    """Obtener información del empleado por user_id"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, position, department, goal, meta_afiliaciones 
            FROM employees 
            WHERE user_id = ?
        """, (user_id,))
        emp = cur.fetchone()
        conn.close()
        return emp
    except Exception as e:
        return None

def get_badge_class(position):
    """Obtener la clase CSS para el badge según el cargo"""
    if "Droguería" in position:
        return "badge-cargo-drogueria"
    elif "Equipos" in position:
        return "badge-cargo-equipos"
    elif "Pasillos" in position:
        return "badge-cargo-pasillos"
    elif "Cajas" in position:
        return "badge-cargo-cajas"
    else:
        return "badge-cargo-drogueria"

# ============= FUNCIONES DE AFILIACIONES =============
def get_afiliaciones_info(employee_id, fecha=None):
    """Obtener información de afiliaciones para un empleado"""
    if fecha is None:
        fecha = date.today()
    
    result = execute_query(
        "SELECT cantidad FROM afiliaciones WHERE employee_id = ? AND fecha = ?",
        (employee_id, str(fecha))
    )
    afiliaciones_hoy = result[0][0] if result else 0
    
    mes_actual = fecha.strftime("%Y-%m")
    result_mes = execute_query(
        "SELECT SUM(cantidad) FROM afiliaciones WHERE employee_id = ? AND fecha LIKE ?",
        (employee_id, f"{mes_actual}%")
    )
    afiliaciones_mes = result_mes[0][0] or 0 if result_mes else 0
    
    return afiliaciones_hoy, afiliaciones_mes

# ============= PÁGINAS DE AFILIACIONES =============
def page_registrar_afiliaciones():
    """Página para que los empleados registren sus afiliaciones"""
    st.title("📱 Registro de Afiliaciones - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado. Contacta al administrador.")
        return
    
    badge_class = get_badge_class(emp_info[2])
    meta_afiliaciones = emp_info[5] if len(emp_info) > 5 and emp_info[5] else 50
    
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
        <h4>Registrando para: {emp_info[1]}</h4>
        <p>
            <span style="background: #e7f1ff; padding: 4px 12px; border-radius: 20px;">{emp_info[2]}</span>
            <span style="background: #e7f1ff; padding: 4px 12px; border-radius: 20px; margin-left: 8px;">{emp_info[3]}</span>
            🎯 Meta mensual de afiliaciones: {meta_afiliaciones}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_fecha1, col_fecha2 = st.columns([2, 2])
    with col_fecha1:
        fecha_registro = st.date_input(
            "📅 Fecha del registro",
            value=date.today(),
            max_value=date.today()
        )
    
    result = execute_query(
        "SELECT COUNT(*) FROM afiliaciones WHERE employee_id = ? AND fecha = ?",
        (emp_info[0], str(fecha_registro))
    )
    ya_registro = result[0][0] > 0 if result else False
    
    if ya_registro:
        st.warning(f"⚠️ Ya hay afiliaciones registradas para el {fecha_registro.strftime('%d/%m/%Y')}. Puedes agregar más.")
    
    with st.form("afiliaciones_form"):
        cantidad = st.number_input("Cantidad de afiliaciones realizadas", min_value=0, step=1, value=1)
        
        submitted = st.form_submit_button("💾 Registrar afiliaciones", use_container_width=True, type="primary")
        
        if submitted:
            if cantidad > 0:
                if ya_registro:
                    success = execute_insert(
                        "UPDATE afiliaciones SET cantidad = ? WHERE employee_id = ? AND fecha = ?",
                        (cantidad, emp_info[0], str(fecha_registro))
                    )
                else:
                    success = execute_insert(
                        "INSERT INTO afiliaciones (employee_id, fecha, cantidad) VALUES (?, ?, ?)",
                        (emp_info[0], str(fecha_registro), cantidad)
                    )
                
                if success:
                    st.success(f"✅ {cantidad} afiliación(es) registrada(s) exitosamente!")
                    st.balloons()
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ Debes ingresar al menos una afiliación")

def page_mis_afiliaciones():
    """Página para que los empleados vean su historial de afiliaciones"""
    st.title("📊 Mis Afiliaciones - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado")
        return
    
    periodo = st.selectbox("Período", ["Este mes", "Este trimestre", "Este año", "Todo"])
    
    hoy = date.today()
    if periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        fecha_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
    else:
        fecha_inicio = date(2000, 1, 1)
    
    df = safe_dataframe("""
        SELECT fecha, cantidad
        FROM afiliaciones 
        WHERE employee_id = ? AND fecha >= ?
        ORDER BY fecha DESC
    """, (emp_info[0], fecha_inicio))
    
    if df.empty:
        st.info(f"ℹ️ No hay registros de afiliaciones en {periodo.lower()}")
        return
    
    df["fecha"] = pd.to_datetime(df["fecha"])
    
    total_periodo = int(df["cantidad"].sum())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total período", f"{total_periodo:,}")
    with col2:
        st.metric("Promedio diario", f"{int(df['cantidad'].mean()):,}")
    with col3:
        st.metric("Mejor día", f"{int(df['cantidad'].max()):,}")
    
    fig = px.line(df, x="fecha", y="cantidad", title=f"📈 Evolución de afiliaciones - {periodo}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

def page_admin_afiliaciones():
    """Página para que el admin gestione las metas de afiliaciones"""
    st.title("⚙️ Configuración de Afiliaciones")
    
    tab1, tab2 = st.tabs(["🎯 Metas por empleado", "📊 Ranking de afiliaciones"])
    
    with tab1:
        empleados = execute_query("""
            SELECT id, name, department, position, meta_afiliaciones
            FROM employees
            ORDER BY department, name
        """)
        
        if not empleados:
            st.info("No hay empleados registrados")
        else:
            for emp in empleados:
                with st.expander(f"{emp[1]} - {emp[2]} ({emp[3]})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        nueva_meta = st.number_input(
                            "Meta mensual de afiliaciones",
                            min_value=1,
                            value=emp[4] or 50,
                            step=10,
                            key=f"meta_{emp[0]}"
                        )
                    with col2:
                        if st.button("💾 Guardar", key=f"guardar_{emp[0]}"):
                            success = execute_insert(
                                "UPDATE employees SET meta_afiliaciones = ? WHERE id = ?",
                                (nueva_meta, emp[0])
                            )
                            if success:
                                st.success("✅ Meta actualizada!")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
    
    with tab2:
        df = safe_dataframe("""
            SELECT 
                e.name as Empleado,
                e.department as Departamento,
                COALESCE(SUM(a.cantidad), 0) as Total,
                e.meta_afiliaciones as Meta
            FROM employees e
            LEFT JOIN afiliaciones a ON e.id = a.employee_id
            GROUP BY e.id
            ORDER BY Total DESC
        """)
        
        if not df.empty:
            df['Cumplimiento'] = (df['Total'] / df['Meta'] * 100).round(1)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ============= PÁGINAS DE VENTAS =============
def page_dashboard():
    st.title("📊 Dashboard de ventas")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())
    
    query = """
        SELECT s.*, e.name, e.position, e.department 
        FROM sales s
        JOIN employees e ON s.employee_id = e.id
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC
    """
    
    with st.spinner("Cargando datos..."):
        df = safe_dataframe(query, (fecha_inicio, fecha_fin))
    
    if df.empty:
        st.info("ℹ️ No hay ventas en el período seleccionado")
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unidades", f"{int(df['total'].sum()):,}")
    with col2:
        st.metric("Autoliquidable", f"{int(df['autoliquidable'].sum()):,}")
    with col3:
        st.metric("Oferta Semana", f"{int(df['oferta'].sum()):,}")
    with col4:
        st.metric("Marca Propia", f"{int(df['marca'].sum()):,}")
    
    fig = px.bar(df, x="date", y="total", color="department", title="Ventas diarias por departamento")
    st.plotly_chart(fig, use_container_width=True)

def page_ranking():
    st.title("🏆 Ranking de Ventas")
    
    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox("Período", ["Este mes", "Este trimestre", "Este año", "Todo"])
    with col2:
        depto_filtro = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS)
    
    hoy = date.today()
    if periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        fecha_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    else:
        cond_fecha = ""
    
    query = f"""
    SELECT 
        e.name as Empleado,
        e.position as Cargo,
        e.department as Departamento,
        COALESCE(SUM(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Total,
        e.goal as Meta
    FROM employees e
    LEFT JOIN sales s ON e.id = s.employee_id {cond_fecha}
    """
    
    if depto_filtro != "Todos":
        query += f" WHERE e.department = '{depto_filtro}'"
    
    query += " GROUP BY e.id ORDER BY Total DESC"
    
    df = safe_dataframe(query)
    
    if df.empty:
        st.info("ℹ️ No hay datos aún")
        return
    
    df['Cumplimiento'] = (df['Total'] / df['Meta'] * 100).round(1)
    df["Posición"] = range(1, len(df) + 1)
    
    st.dataframe(df[["Posición", "Empleado", "Cargo", "Departamento", "Total", "Cumplimiento"]], use_container_width=True, hide_index=True)

def page_empleados():
    st.title("🧑‍💼 Gestión de Empleados AIS")
    
    tab1, tab2 = st.tabs(["➕ Registrar empleado", "📋 Lista de empleados"])
    
    with tab1:
        with st.form("registrar_empleado_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nombre completo*", placeholder="Ej: Juan Pérez")
                position = st.selectbox("Cargo*", CARGOS)
            with col2:
                department = st.selectbox("Departamento*", DEPARTAMENTOS)
                goal = st.number_input("Meta mensual", value=300, min_value=1, step=50)
            
            submitted = st.form_submit_button("Registrar empleado", type="primary", use_container_width=True)
            
            if submitted:
                if name and position and department:
                    check_query = "SELECT id FROM employees WHERE name = ?"
                    existing = execute_query(check_query, (name,))
                    
                    if existing:
                        st.warning(f"⚠️ Ya existe un empleado con el nombre '{name}'")
                    else:
                        insert_query = """
                            INSERT INTO employees (name, position, department, goal, user_id) 
                            VALUES (?,?,?,?, NULL)
                        """
                        success = execute_insert(insert_query, (name, position, department, goal))
                        
                        if success:
                            st.success(f"✅ Empleado '{name}' registrado exitosamente!")
                            st.balloons()
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                else:
                    st.warning("⚠️ Completa todos los campos obligatorios (*)")
    
    with tab2:
        df_emp = safe_dataframe("""
            SELECT 
                e.name as 'Nombre',
                e.position as 'Cargo',
                e.department as 'Departamento',
                e.goal as 'Meta',
                CASE 
                    WHEN u.username IS NOT NULL THEN '✅ Asignado'
                    ELSE '❌ Sin usuario'
                END as 'Estado'
            FROM employees e
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.department, e.name
        """)
        
        if not df_emp.empty:
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No hay empleados registrados")

def page_usuarios():
    st.title("👤 Gestión de Usuarios AIS")
    
    users = get_all_users()
    if users:
        df_users = pd.DataFrame(users, columns=["ID", "Usuario", "Rol", "Empleado", "Departamento"])
        df_users['Empleado'] = df_users['Empleado'].fillna('—')
        df_users['Departamento'] = df_users['Departamento'].fillna('—')
        
        st.dataframe(df_users, use_container_width=True, hide_index=True)

def page_registrar_ventas():
    st.title("📝 Registro Diario de Ventas - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado. Contacta al administrador.")
        return
    
    st.markdown(f"""
    <div style="background: white; border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
        <h4>Registrando para: {emp_info[1]}</h4>
        <p>🎯 Meta mensual: {emp_info[4]} unidades</p>
    </div>
    """, unsafe_allow_html=True)
    
    fecha_registro = st.date_input("📅 Fecha del registro", value=date.today(), max_value=date.today())
    
    with st.form("ventas_form"):
        col1, col2 = st.columns(2)
        with col1:
            aut = st.number_input("📦 Autoliquidable", min_value=0, step=1, value=0)
            ma = st.number_input("🏷 Marca Propia", min_value=0, step=1, value=0)
        
        with col2:
            of = st.number_input("🔥 Oferta Semana", min_value=0, step=1, value=0)
            ad = st.number_input("➕ Producto Adicional", min_value=0, step=1, value=0)
        
        submitted = st.form_submit_button("💾 Guardar ventas", use_container_width=True, type="primary")
        
        if submitted:
            total = aut + of + ma + ad
            if total > 0:
                success = execute_insert("""
                    INSERT INTO sales (employee_id, date, autoliquidable, oferta, marca, adicional)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (emp_info[0], str(fecha_registro), aut, of, ma, ad))
                
                if success:
                    st.success(f"✅ Ventas registradas exitosamente!")
                    st.balloons()
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ Debes ingresar al menos una unidad")

def page_mi_desempeno():
    st.title("📊 Mi Desempeño Personal - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado")
        return
    
    periodo = st.selectbox("Período", ["Este mes", "Este trimestre", "Este año", "Todo"])
    
    hoy = date.today()
    if periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        fecha_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
    else:
        fecha_inicio = date(2000, 1, 1)
    
    df = safe_dataframe("""
        SELECT date, autoliquidable, oferta, marca, adicional
        FROM sales 
        WHERE employee_id = ? AND date >= ?
        ORDER BY date
    """, (emp_info[0], fecha_inicio))
    
    if df.empty:
        st.info(f"ℹ️ No hay registros en {periodo.lower()}")
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    total_periodo = int(df["total"].sum())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total período", f"{total_periodo:,}")
    with col2:
        st.metric("Promedio diario", f"{int(df['total'].mean()):,}")
    with col3:
        st.metric("Mejor día", f"{int(df['total'].max()):,}")
    
    fig = px.line(df, x="date", y="total", title=f"📈 Evolución personal - {periodo}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

def page_mi_perfil():
    st.title("👤 Mi Perfil - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if emp_info:
        st.markdown(f"""
        <div style="background: white; border-radius: 16px; padding: 2rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <h2>{emp_info[1]}</h2>
            <p>
                <span style="background: #e7f1ff; padding: 4px 12px; border-radius: 20px;">{emp_info[2]}</span>
                <span style="background: #e7f1ff; padding: 4px 12px; border-radius: 20px; margin-left: 8px;">{emp_info[3]}</span>
            </p>
            <p class="metric">🎯 Meta: {emp_info[4]} unidades/mes</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No tienes un perfil de empleado configurado. Contacta al administrador.")

def page_reportes():
    st.title("📊 Reportes Avanzados")
    
    df = safe_dataframe("""
        SELECT 
            e.department,
            SUM(s.autoliquidable + s.oferta + s.marca + s.adicional) as total,
            COUNT(DISTINCT e.id) as empleados
        FROM sales s
        JOIN employees e ON s.employee_id = e.id
        GROUP BY e.department
        ORDER BY total DESC
    """)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        fig = px.bar(df, x='department', y='total', title="Ventas por departamento", color='department')
        st.plotly_chart(fig, use_container_width=True)

# ============= FUNCIÓN PRINCIPAL =============
def main():
    # Inicializar keep-alive
    init_keep_alive()
    
    # Inicializar session state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "Login"
    if 'sidebar_open' not in st.session_state:
        st.session_state.sidebar_open = False
    
    # Cargar CSS moderno
    load_css()
    
    if not st.session_state.user:
        show_modern_login()
    else:
        # Mostrar header moderno
        create_modern_header()
        
        # Mostrar menú
        show_modern_menu()
        
        # Contenido principal
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Mostrar tarjeta de búsqueda en páginas específicas
        if st.session_state.page in ["Dashboard", "Registrar ventas"]:
            create_modern_search_card()
        
        # Diccionario de páginas
        pages = {
            "Dashboard": page_dashboard,
            "Ranking": page_ranking,
            "Empleados": page_empleados,
            "Usuarios": page_usuarios,
            "Reportes": page_reportes,
            "Backups": render_backup_page,
            "Admin Afiliaciones": page_admin_afiliaciones,
            "Registrar ventas": page_registrar_ventas,
            "Registrar afiliaciones": page_registrar_afiliaciones,
            "Mis afiliaciones": page_mis_afiliaciones,
            "Mi desempeño": page_mi_desempeno,
            "Mi perfil": page_mi_perfil
        }
        
        if st.session_state.page in pages:
            pages[st.session_state.page]()
        else:
            page_dashboard() if st.session_state.user["role"] == "admin" else page_registrar_ventas()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer moderno
        show_modern_footer()

if __name__ == "__main__":
    main()