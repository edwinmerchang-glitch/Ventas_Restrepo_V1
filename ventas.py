import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from database import create_tables, get_connection, migrate_database
from auth import authenticate, create_user
import sqlite3

# Configuración de página
st.set_page_config(
    "Ventas PRO", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Inicializar tablas y migrar BD
try:
    create_tables()
    migrate_database()  # Agregar nuevas columnas si no existen
except Exception as e:
    st.error(f"Error de inicialización: {e}")

def create_default_admin():
    """Crear admin por defecto si no hay usuarios"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        if total_users == 0:
            create_user("admin", "admin123", "admin")
            st.success("✅ Usuario admin creado por defecto (admin/admin123)")
        conn.close()
    except Exception as e:
        st.error(f"Error al crear admin por defecto: {e}")

# Crear admin por defecto
create_default_admin()

# ============= LISTAS PERSONALIZADAS =============
# Cargos específicos para tu empresa
CARGOS = [
    "Ais Droguería",
    "Ais Equipos Médicos", 
    "Ais Pasillos",
    "Ais Cajas"
]

# Departamentos específicos para tu empresa
DEPARTAMENTOS = [
    "Droguería",
    "Equipos Médicos",
    "Pasillos",
    "Cajas"
]

# NOTA: Ya no usamos el mapa automático, ahora será selección manual

def load_css():
    """Cargar estilos CSS"""
    try:
        with open("styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("""
        <style>
        .main { background: linear-gradient(120deg,#f4f6ff,#eef2ff); }
        .card { background: white; padding: 20px; border-radius: 18px; 
                box-shadow: 0px 4px 15px rgba(0,0,0,0.08); margin-bottom: 15px; }
        .metric { font-size: 28px; font-weight: 700; color: #3b5bfd; }
        .stButton > button { width: 100%; border-radius: 10px; 
                            background: linear-gradient(90deg,#4f7cff,#7aa2ff); 
                            color: white; font-weight: 600; border: none; }
        .stButton > button:hover { background: linear-gradient(90deg,#3b5bfd,#6b8aff); }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-cargo-drogueria { background: #e3f2fd; color: #1976d2; }
        .badge-cargo-equipos { background: #e8f5e8; color: #2e7d32; }
        .badge-cargo-pasillos { background: #fff3e0; color: #f57c00; }
        .badge-cargo-cajas { background: #fce4ec; color: #c2185b; }
        .badge-depto { background: #f3e5f5; color: #7b1fa2; }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Inicializar session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard" if st.session_state.user else "Login"
if "logout" not in st.session_state:
    st.session_state.logout = False

# ---------------- FUNCIONES DE UTILIDAD ---------------- #
def safe_dataframe(query, params=None):
    """Ejecutar query de forma segura y retornar DataFrame"""
    try:
        conn = get_connection()
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return pd.DataFrame()

def get_employee_info(user_id):
    """Obtener información del empleado por user_id"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, position, department, goal 
            FROM employees 
            WHERE user_id = ?
        """, (user_id,))
        emp = cur.fetchone()
        conn.close()
        return emp
    except Exception as e:
        st.error(f"Error al obtener información del empleado: {e}")
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

# ---------------- LOGIN ---------------- #
def show_login():
    """Mostrar pantalla de login"""
    st.title("📊 Sistema Profesional de Ventas - AIS")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🔐 Iniciar Sesión")
            
            u = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            p = st.text_input("Contraseña", type="password", placeholder="********")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Ingresar", use_container_width=True, type="primary"):
                    if u and p:
                        user = authenticate(u, p)
                        if user:
                            st.session_state.user = user
                            # Redirigir según rol
                            if user["role"] == "admin":
                                st.session_state.page = "Dashboard"
                            else:
                                # Verificar si el empleado tiene cargo y departamento
                                emp_info = get_employee_info(user["id"])
                                if emp_info and emp_info[2] and emp_info[3]:  # Si tiene cargo y depto
                                    st.session_state.page = "Registrar ventas"
                                else:
                                    st.warning("⚠️ Completa tu perfil de empleado antes de continuar")
                                    st.session_state.page = "Mi perfil"
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    else:
                        st.warning("⚠️ Completa todos los campos")
            
            with col_btn2:
                if st.button("Limpiar", use_container_width=True):
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.info("👤 Usuario por defecto: **admin** / **admin123**")

# ---------------- MENÚ MEJORADO CON BOTONES ---------------- #
def show_menu():
    """Mostrar menú con botones mejorados"""
    with st.sidebar:
        # Logo de la empresa
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #4f7cff; font-size: 32px; margin: 0;">AIS</h1>
            <p style="color: #666; font-size: 14px;">Sistema de Ventas</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Información del usuario
        emp_info = get_employee_info(st.session_state.user["id"])
        if emp_info:
            badge_class = get_badge_class(emp_info[2])
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: white; border-radius: 10px; margin-bottom: 15px;">
                <h4 style="margin: 5px 0;">{emp_info[1]}</h4>
                <p style="margin: 2px 0;">
                    <span class="badge {badge_class}">{emp_info[2] or 'Sin cargo'}</span>
                </p>
                <p style="margin: 2px 0;">
                    <span class="badge badge-depto">{emp_info[3] or 'Sin depto'}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.title(f"👋 Hola, {st.session_state.user['role'].title()}!")
        
        st.divider()
        
        # Definir opciones según rol
        if st.session_state.user["role"] == "admin":
            menu_options = {
                "📊 Dashboard": "Dashboard",
                "🏆 Ranking": "Ranking",
                "👥 Usuarios": "Usuarios",
                "🧑‍💼 Empleados": "Empleados",
                "📊 Reportes": "Reportes"
            }
        else:
            menu_options = {
                "📝 Registrar": "Registrar ventas",
                "📈 Mi Desempeño": "Mi desempeño",
                "👤 Mi perfil": "Mi perfil",
                "🏆 Ranking": "Ranking"
            }
        
        # Crear botones para cada opción
        for label, page in menu_options.items():
            if st.button(
                label, 
                key=f"menu_{page}",
                use_container_width=True,
                type="secondary" if st.session_state.page != page else "primary"
            ):
                st.session_state.page = page
                st.rerun()
        
        st.divider()
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            for key in ["user", "page", "logout"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # Mostrar información adicional
        st.divider()
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.caption("⚡ AIS Ventas v3.0")

# ---------------- PÁGINAS ---------------- #
def page_dashboard():
    st.title("📊 Dashboard Ejecutivo AIS")
    
    # Filtros por departamento
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())
    with col3:
        depto_filtro = st.multiselect("Departamento", DEPARTAMENTOS, default=DEPARTAMENTOS)
    
    # Construir query con filtros
    query = """
        SELECT s.*, e.name, e.position, e.department 
        FROM sales s
        JOIN employees e ON s.employee_id = e.id
        WHERE date BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    
    if depto_filtro:
        placeholders = ','.join(['?'] * len(depto_filtro))
        query += f" AND e.department IN ({placeholders})"
        params.extend(depto_filtro)
    
    query += " ORDER BY date DESC"
    
    with st.spinner("Cargando datos..."):
        df = safe_dataframe(query, params)
    
    if df.empty:
        st.info("ℹ️ No hay ventas en el período seleccionado")
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unidades", f"{int(df['total'].sum()):,}")
    with col2:
        st.metric("Autoliquidable", f"{int(df['autoliquidable'].sum()):,}")
    with col3:
        st.metric("Oferta Semana", f"{int(df['oferta'].sum()):,}")
    with col4:
        st.metric("Marca Propia", f"{int(df['marca'].sum()):,}")
    
    # Gráficos
    tab1, tab2, tab3 = st.tabs(["📈 Evolución", "📊 Distribución", "👥 Por empleado"])
    
    with tab1:
        fig = px.line(df, x="date", y="total", color="department",
                     title="📈 Evolución diaria de ventas por departamento",
                     template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        dist_df = df.groupby('department')[['autoliquidable','oferta','marca','adicional']].sum().reset_index()
        dist_df_melted = dist_df.melt(id_vars=['department'], var_name='Tipo', value_name='Cantidad')
        fig2 = px.bar(dist_df_melted, x='department', y='Cantidad', color='Tipo',
                     title="Distribución por departamento y tipo",
                     barmode='stack')
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        emp_df = df.groupby(['name', 'department']).agg({
            'total': 'sum'
        }).reset_index()
        
        fig3 = px.bar(emp_df, x='name', y='total', color='department',
                     title="Ventas por empleado",
                     barmode='group')
        st.plotly_chart(fig3, use_container_width=True)

def page_ranking():
    st.title("🏆 Ranking de Ventas AIS")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox("Período", ["Este mes", "Este trimestre", "Este año", "Todo"])
    with col2:
        depto_filtro = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS)
    
    # Construir filtro de fecha
    hoy = date.today()
    if periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        trimestre_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
        cond_fecha = f"AND date >= '{trimestre_inicio}'"
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    else:
        cond_fecha = ""
    
    # Construir query
    query = f"""
    SELECT 
        e.name as Empleado,
        e.position as Cargo,
        e.department as Departamento,
        COALESCE(SUM(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Total,
        COUNT(s.id) as Registros,
        COALESCE(AVG(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Promedio,
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
    
    # Calcular cumplimiento de meta
    df['Cumplimiento'] = (df['Total'] / df['Meta'] * 100).round(1)
    
    # Top por departamento
    st.subheader("🥇 Podio de Honor por Departamento")
    
    # Crear pestañas para cada departamento
    deptos_tab = st.tabs(DEPARTAMENTOS)
    
    for i, depto in enumerate(DEPARTAMENTOS):
        with deptos_tab[i]:
            df_depto = df[df['Departamento'] == depto].head(3)
            if not df_depto.empty:
                cols = st.columns(len(df_depto))
                for j, (idx, row) in enumerate(df_depto.iterrows()):
                    with cols[j]:
                        badge_class = get_badge_class(row['Cargo'])
                        st.markdown(f"""
                        <div class="card" style="text-align:center">
                            <h3>{'🥇' if j==0 else '🥈' if j==1 else '🥉'}</h3>
                            <h4>{row['Empleado']}</h4>
                            <p><span class="badge {badge_class}">{row['Cargo']}</span></p>
                            <p class="metric">{int(row['Total']):,}</p>
                            <p>unidades • {row['Cumplimiento']}% de meta</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info(f"Sin datos para {depto}")
    
    # Ranking general
    st.subheader("📋 Ranking General")
    df_display = df.copy()
    df_display["Posición"] = range(1, len(df) + 1)
    df_display["Total"] = df_display["Total"].apply(lambda x: f"{int(x):,}")
    df_display["Promedio"] = df_display["Promedio"].apply(lambda x: f"{int(x):,}")
    df_display["Cumplimiento"] = df_display["Cumplimiento"].apply(lambda x: f"{x}%")
    
    st.dataframe(
        df_display[["Posición", "Empleado", "Cargo", "Departamento", "Total", "Registros", "Cumplimiento"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico comparativo
    fig = px.bar(df, x="Empleado", y="Total", color="Departamento",
                 title="🔥 Ranking General por Departamento",
                 barmode="group")
    st.plotly_chart(fig, use_container_width=True)

def page_usuarios():
    st.title("👤 Gestión de Usuarios AIS")
    
    tab1, tab2 = st.tabs(["➕ Crear usuario", "📋 Lista de usuarios"])
    
    with tab1:
        with st.form("user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                u = st.text_input("Usuario", placeholder="Nuevo usuario")
            with col2:
                p = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            
            r = st.selectbox("Rol", ["empleado", "admin"])
            
            submitted = st.form_submit_button("Crear usuario", type="primary", use_container_width=True)
            
            if submitted:
                if u and p and len(p) >= 6:
                    try:
                        create_user(u, p, r)
                        st.success(f"✅ Usuario '{u}' creado exitosamente")
                        st.balloons()
                    except sqlite3.IntegrityError:
                        st.error("❌ El nombre de usuario ya existe")
                    except Exception as e:
                        st.error(f"❌ Error al crear usuario: {e}")
                else:
                    st.warning("⚠️ Completa todos los campos (contraseña mínimo 6 caracteres)")
    
    with tab2:
        df_users = safe_dataframe("""
            SELECT u.id, u.username, u.role, 
                   e.name as empleado, e.position, e.department
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            ORDER BY u.id
        """)
        if not df_users.empty:
            st.dataframe(df_users, use_container_width=True, hide_index=True)

def page_empleados():
    st.title("🧑‍💼 Gestión de Empleados AIS")
    
    tab1, tab2 = st.tabs(["➕ Registrar empleado", "📋 Lista de empleados"])
    
    with tab1:
        with st.form("employee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
                position = st.selectbox("Cargo", CARGOS)
            with col2:
                # ===== CAMBIO IMPORTANTE: Ahora es selección manual =====
                department = st.selectbox("Departamento", DEPARTAMENTOS)
                goal = st.number_input("Meta mensual", value=300, min_value=1, step=50)
            
            # Selector de usuario
            df_users = safe_dataframe("""
                SELECT id, username FROM users 
                WHERE role='empleado' AND id NOT IN (
                    SELECT user_id FROM employees WHERE user_id IS NOT NULL
                )
            """)
            
            if not df_users.empty:
                user_options = {row['username']: row['id'] for _, row in df_users.iterrows()}
                selected_user = st.selectbox("Usuario asociado", options=list(user_options.keys()))
                user_id = user_options[selected_user]
            else:
                st.warning("⚠️ No hay usuarios disponibles (todos ya tienen empleado asociado)")
                user_id = None
            
            submitted = st.form_submit_button("Registrar empleado", type="primary", use_container_width=True)
            
            if submitted and name and user_id:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO employees (name, position, department, goal, user_id) 
                        VALUES (?,?,?,?,?)
                    """, (name, position, department, goal, user_id))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Empleado '{name}' registrado exitosamente")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("❌ Este usuario ya tiene un empleado asociado")
                except Exception as e:
                    st.error(f"❌ Error al registrar: {e}")
    
    with tab2:
        df_emp = safe_dataframe("""
            SELECT e.id, e.name, e.position, e.department, e.goal, 
                   u.username, 
                   COUNT(s.id) as ventas_realizadas
            FROM employees e
            JOIN users u ON e.user_id = u.id
            LEFT JOIN sales s ON e.id = s.employee_id
            GROUP BY e.id
            ORDER BY e.department, e.name
        """)
        
        if not df_emp.empty:
            # Agrupar por departamento
            for depto in DEPARTAMENTOS:
                df_depto = df_emp[df_emp['department'] == depto]
                if not df_depto.empty:
                    with st.expander(f"📌 {depto} ({len(df_depto)} empleados)"):
                        for _, row in df_depto.iterrows():
                            badge_class = get_badge_class(row['position'])
                            col1, col2, col3, col4 = st.columns([3,2,2,1])
                            with col1:
                                st.markdown(f"**{row['name']}**")
                                st.markdown(f"<span class='badge {badge_class}'>{row['position']}</span>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"🎯 Meta: {row['goal']}")
                                st.markdown(f"📊 Ventas: {row['ventas_realizadas']}")
                            with col3:
                                st.markdown(f"👤 Usuario: {row['username']}")
                            with col4:
                                if st.button("✏️", key=f"edit_{row['id']}"):
                                    st.session_state.editing_employee = row['id']
                                    st.rerun()
                            st.divider()

def page_reportes():
    st.title("📊 Reportes Avanzados AIS")
    
    tipo_reporte = st.selectbox(
        "Tipo de reporte",
        ["Ventas por departamento", "Ventas por cargo", "Análisis de cumplimiento", "Tendencias"]
    )
    
    if tipo_reporte == "Ventas por departamento":
        df = safe_dataframe("""
            SELECT 
                e.department,
                SUM(s.autoliquidable + s.oferta + s.marca + s.adicional) as total,
                AVG(s.autoliquidable + s.oferta + s.marca + s.adicional) as promedio,
                COUNT(DISTINCT e.id) as empleados,
                COUNT(s.id) as transacciones
            FROM sales s
            JOIN employees e ON s.employee_id = e.id
            GROUP BY e.department
            ORDER BY total DESC
        """)
        
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(df, values='total', names='department', 
                           title="Distribución por departamento")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.bar(df, x='department', y='total',
                            title="Ventas por departamento",
                            color='department')
                st.plotly_chart(fig2, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
    
    elif tipo_reporte == "Ventas por cargo":
        df = safe_dataframe("""
            SELECT 
                e.position,
                e.department,
                SUM(s.autoliquidable + s.oferta + s.marca + s.adicional) as total,
                AVG(s.autoliquidable + s.oferta + s.marca + s.adicional) as promedio,
                COUNT(DISTINCT e.id) as empleados
            FROM sales s
            JOIN employees e ON s.employee_id = e.id
            GROUP BY e.position, e.department
            ORDER BY total DESC
        """)
        
        if not df.empty:
            fig = px.bar(df, x='position', y='total', color='department',
                        title="Ventas por cargo",
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True)

def page_registrar_ventas():
    st.title("📝 Registro Diario de Ventas - AIS")
    
    # Verificar si el usuario tiene empleado asociado
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado. Completa tu perfil primero.")
        if st.button("👤 Ir a Mi perfil"):
            st.session_state.page = "Mi perfil"
            st.rerun()
        return
    
    badge_class = get_badge_class(emp_info[2])
    
    # Mostrar información del empleado
    st.markdown(f"""
    <div class="card">
        <h4>Registrando para: {emp_info[1]}</h4>
        <p>
            <span class="badge {badge_class}">{emp_info[2]}</span>
            <span class="badge badge-depto">{emp_info[3]}</span>
            🎯 Meta mensual: {emp_info[4]} unidades
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar si ya registró hoy
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM sales 
        WHERE employee_id = ? AND date = ?
    """, (emp_info[0], str(date.today())))
    ya_registro_hoy = cur.fetchone()[0] > 0
    conn.close()
    
    if ya_registro_hoy:
        st.warning("⚠️ Ya has registrado ventas hoy. ¿Deseas agregar más?")
    
    # Formulario de ventas
    with st.form("ventas_form", clear_on_submit=True):
        st.subheader("Ingresa las ventas del día")
        
        col1, col2 = st.columns(2)
        with col1:
            aut = st.number_input("📦 Autoliquidable", min_value=0, step=1, value=0)
            ma = st.number_input("🏷 Marca Propia", min_value=0, step=1, value=0)
        
        with col2:
            of = st.number_input("🔥 Oferta Semana", min_value=0, step=1, value=0)
            ad = st.number_input("➕ Producto Adicional", min_value=0, step=1, value=0)
        
        # Resumen
        total = aut + of + ma + ad
        
        # Calcular progreso de meta
        mes_actual = date.today().strftime("%Y-%m")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(autoliquidable + oferta + marca + adicional)
            FROM sales 
            WHERE employee_id = ? AND date LIKE ?
        """, (emp_info[0], f"{mes_actual}%"))
        ventas_mes = cur.fetchone()[0] or 0
        conn.close()
        
        progreso = ((ventas_mes + total) / emp_info[4] * 100) if emp_info[4] > 0 else 0
        
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <p><strong>Total del día:</strong> {total} unidades</p>
            <p><strong>Progreso mensual:</strong> {ventas_mes + total} / {emp_info[4]} unidades ({progreso:.1f}%)</p>
            <div class="progress">
                <div class="progress-bar" style="width: {min(progreso, 100)}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("💾 Guardar ventas", type="primary", use_container_width=True)
        
        if submitted:
            if total > 0:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO sales (employee_id, date, autoliquidable, oferta, marca, adicional)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_info[0], str(date.today()), aut, of, ma, ad))
                    conn.commit()
                    conn.close()
                    st.success("✅ Venta registrada exitosamente!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
            else:
                st.warning("⚠️ Debes ingresar al menos una unidad")

def page_mi_desempeno():
    st.title("📊 Mi Desempeño Personal - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado")
        return
    
    badge_class = get_badge_class(emp_info[2])
    
    # Selector de período
    periodo = st.selectbox(
        "Período",
        ["Esta semana", "Este mes", "Este trimestre", "Este año", "Todo"],
        key="periodo_desempeno"
    )
    
    # Construir filtro de fecha
    hoy = date.today()
    if periodo == "Esta semana":
        fecha_inicio = hoy - pd.Timedelta(days=hoy.weekday())
    elif periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        trimestre_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
        fecha_inicio = trimestre_inicio
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
    else:
        fecha_inicio = date(2000, 1, 1)
    
    # Cargar datos
    df = safe_dataframe("""
        SELECT date, autoliquidable, oferta, marca, adicional
        FROM sales 
        WHERE employee_id = ? AND date >= ?
        ORDER BY date
    """, (emp_info[0], fecha_inicio))
    
    if df.empty:
        st.info(f"ℹ️ No hay registros en {periodo.lower()}")
        if st.button("📝 Ir a registrar ventas", type="primary"):
            st.session_state.page = "Registrar ventas"
            st.rerun()
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    # Métricas
    total_periodo = int(df["total"].sum())
    promedio = int(df["total"].mean())
    mejor_dia = int(df["total"].max())
    progreso_meta = (total_periodo / emp_info[4] * 100) if emp_info[4] > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total período", f"{total_periodo:,}")
    with col2:
        st.metric("Promedio diario", f"{promedio:,}")
    with col3:
        st.metric("Mejor día", f"{mejor_dia:,}")
    with col4:
        st.metric("Progreso meta", f"{progreso_meta:.1f}%")
    
    # Gráfico de evolución
    fig = px.line(df, x="date", y="total", 
                 title=f"📈 Evolución personal - {periodo}",
                 markers=True)
    fig.update_traces(line_color="#4f7cff", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    # Desglose por tipo
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Desglose por tipo")
        tipos = pd.DataFrame({
            'Tipo': ['Autoliquidable', 'Oferta', 'Marca', 'Adicional'],
            'Cantidad': [
                df['autoliquidable'].sum(),
                df['oferta'].sum(),
                df['marca'].sum(),
                df['adicional'].sum()
            ]
        })
        st.dataframe(tipos, use_container_width=True, hide_index=True)
    
    with col2:
        fig2 = px.pie(tipos, values='Cantidad', names='Tipo',
                     title="Distribución por tipo")
        st.plotly_chart(fig2, use_container_width=True)

def page_mi_perfil():
    st.title("👤 Mi Perfil - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.warning("⚠️ Completa tu perfil de empleado")
        
        with st.form("perfil_form"):
            name = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
            position = st.selectbox("Cargo", CARGOS)
            # ===== CAMBIO IMPORTANTE: Ahora es selección manual =====
            department = st.selectbox("Departamento", DEPARTAMENTOS)
            goal = st.number_input("Meta mensual", value=300, min_value=1, step=50)
            
            submitted = st.form_submit_button("Guardar perfil", type="primary", use_container_width=True)
            
            if submitted and name:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO employees (name, position, department, goal, user_id) 
                        VALUES (?,?,?,?,?)
                    """, (name, position, department, goal, st.session_state.user["id"]))
                    conn.commit()
                    conn.close()
                    st.success("✅ Perfil completado exitosamente!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
    else:
        badge_class = get_badge_class(emp_info[2])
        st.markdown(f"""
        <div class="card" style="text-align: center;">
            <h2>{emp_info[1]}</h2>
            <p>
                <span class="badge {badge_class}" style="font-size: 16px;">{emp_info[2]}</span>
                <span class="badge badge-depto" style="font-size: 16px;">{emp_info[3]}</span>
            </p>
            <p class="metric">🎯 Meta: {emp_info[4]} unidades/mes</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✏️ Editar perfil", use_container_width=True):
            st.session_state.editing_profile = True
        
        if st.session_state.get('editing_profile', False):
            with st.form("editar_perfil"):
                new_position = st.selectbox("Cargo", CARGOS, 
                                          index=CARGOS.index(emp_info[2]) if emp_info[2] in CARGOS else 0)
                # ===== CAMBIO IMPORTANTE: Ahora es selección manual =====
                new_department = st.selectbox("Departamento", DEPARTAMENTOS,
                                            index=DEPARTAMENTOS.index(emp_info[3]) if emp_info[3] in DEPARTAMENTOS else 0)
                new_goal = st.number_input("Meta mensual", value=emp_info[4], min_value=1, step=50)
                
                if st.form_submit_button("Actualizar perfil", type="primary"):
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE employees 
                            SET position = ?, department = ?, goal = ?
                            WHERE id = ?
                        """, (new_position, new_department, new_goal, emp_info[0]))
                        conn.commit()
                        conn.close()
                        st.success("✅ Perfil actualizado!")
                        st.session_state.editing_profile = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al actualizar: {e}")

# ---------------- CONTROL PRINCIPAL ---------------- #
def main():
    """Función principal de la aplicación"""
    if not st.session_state.user:
        show_login()
    else:
        show_menu()
        
        # Navegación de páginas
        pages = {
            "Dashboard": page_dashboard,
            "Ranking": page_ranking,
            "Usuarios": page_usuarios,
            "Empleados": page_empleados,
            "Reportes": page_reportes,
            "Registrar ventas": page_registrar_ventas,
            "Mi desempeño": page_mi_desempeno,
            "Mi perfil": page_mi_perfil
        }
        
        if st.session_state.page in pages:
            pages[st.session_state.page]()
        else:
            # Página por defecto
            if st.session_state.user["role"] == "admin":
                page_dashboard()
            else:
                page_registrar_ventas()

if __name__ == "__main__":
    main()