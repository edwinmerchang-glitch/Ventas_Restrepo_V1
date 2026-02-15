import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from database import create_tables, get_connection
from auth import authenticate, create_user
import sqlite3

def create_default_admin():
    """Crear admin por defecto si no hay usuarios"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        if total_users == 0:
            create_user("admin", "admin123", "admin")
            st.success("Usuario admin creado por defecto (admin/admin123)")
        conn.close()
    except Exception as e:
        st.error(f"Error al crear admin por defecto: {e}")

# Configuración de página
st.set_page_config(
    "Ventas PRO", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Inicializar tablas y admin
try:
    create_tables()
    create_default_admin()
except Exception as e:
    st.error(f"Error de inicialización: {e}")

def load_css():
    """Cargar estilos CSS"""
    try:
        with open("styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # CSS por defecto si no existe el archivo
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

# ---------------- LOGIN ---------------- #
def show_login():
    """Mostrar pantalla de login"""
    st.title("📊 Sistema Profesional de Ventas")
    
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
                            st.session_state.page = "Dashboard" if user["role"] == "admin" else "Registrar ventas"
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    else:
                        st.warning("⚠️ Completa todos los campos")
            
            with col_btn2:
                if st.button("Limpiar", use_container_width=True):
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Info de acceso por defecto
            st.info("👤 Usuario por defecto: admin / admin123")

# ---------------- MENÚ MEJORADO CON BOTONES ---------------- #
def show_menu():
    """Mostrar menú con botones mejorados"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000.png", width=80)
        st.title(f"👋 Hola, {st.session_state.user['role'].title()}!")
        
        st.divider()
        
        # Definir opciones según rol
        if st.session_state.user["role"] == "admin":
            menu_options = {
                "📊 Dashboard": "Dashboard",
                "🏆 Ranking": "Ranking",
                "👥 Usuarios": "Usuarios",
                "🧑‍💼 Empleados": "Empleados"
            }
        else:
            menu_options = {
                "📝 Registrar": "Registrar ventas",
                "📈 Mi Desempeño": "Mi desempeño",
                "🏆 Ranking": "Ranking"
            }
        
        # Crear botones para cada opción
        cols = st.columns(2)
        col_list = list(cols) * len(menu_options)
        
        for i, (label, page) in enumerate(menu_options.items()):
            if st.button(
                label, 
                key=f"menu_{i}",
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
        st.caption(f"📅 {date.today().strftime('%d/%m/%Y')}")
        st.caption("⚡ Versión 2.0")

# ---------------- FUNCIONES DE PÁGINA CON MANEJO DE ERRORES ---------------- #
def safe_dataframe(query):
    """Ejecutar query de forma segura y retornar DataFrame"""
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return pd.DataFrame()

def page_dashboard():
    st.title("📊 Dashboard Ejecutivo")
    
    with st.spinner("Cargando datos..."):
        df = safe_dataframe("SELECT * FROM sales")
    
    if df.empty:
        st.info("ℹ️ No hay ventas registradas")
        st.balloons()
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    # Métricas con diseño mejorado
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unidades", f"{int(df['total'].sum()):,}", 
                 delta=f"+{int(df['total'].tail(7).sum()):,} últimos 7 días")
    with col2:
        st.metric("Autoliquidable", f"{int(df['autoliquidable'].sum()):,}")
    with col3:
        st.metric("Oferta Semana", f"{int(df['oferta'].sum()):,}")
    with col4:
        st.metric("Marca Propia", f"{int(df['marca'].sum()):,}")
    
    # Gráficos
    tab1, tab2 = st.tabs(["📈 Evolución", "📊 Distribución"])
    
    with tab1:
        fig = px.line(df, x="date", y="total", 
                     title="📈 Evolución diaria de ventas",
                     template="plotly_white")
        fig.update_traces(line_color="#4f7cff", line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        dist_df = df[['autoliquidable','oferta','marca','adicional']].sum().reset_index()
        dist_df.columns = ['Tipo', 'Cantidad']
        fig2 = px.pie(dist_df, values='Cantidad', names='Tipo',
                     title="🥧 Distribución por tipo",
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig2, use_container_width=True)

def page_ranking():
    st.title("🏆 Ranking de Ventas")
    
    query = """
    SELECT 
        e.name as Empleado,
        COALESCE(SUM(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Total,
        COUNT(s.id) as Registros,
        COALESCE(AVG(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Promedio
    FROM employees e
    LEFT JOIN sales s ON e.id = s.employee_id
    GROUP BY e.name
    ORDER BY Total DESC
    """
    
    df = safe_dataframe(query)
    
    if df.empty:
        st.info("ℹ️ No hay datos aún")
        return
    
    # Top 3 destacado
    st.subheader("🥇 Podio de Honor")
    cols = st.columns(3)
    for i, col in enumerate(cols[:min(3, len(df))]):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center">
                <h3>{'🥇' if i==0 else '🥈' if i==1 else '🥉'}</h3>
                <h4>{df.iloc[i]['Empleado']}</h4>
                <p class="metric">{int(df.iloc[i]['Total']):,}</p>
                <p>unidades</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Tabla completa
    st.subheader("📋 Tabla completa")
    df["Posición"] = range(1, len(df) + 1)
    df["Total"] = df["Total"].apply(lambda x: f"{int(x):,}")
    df["Promedio"] = df["Promedio"].apply(lambda x: f"{int(x):,}")
    st.dataframe(
        df[["Posición", "Empleado", "Total", "Registros", "Promedio"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico de barras
    fig = px.bar(
        df, 
        x="Empleado", 
        y="Total",
        title="🔥 Ranking General",
        color="Total",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig, use_container_width=True)

def page_usuarios():
    st.title("👤 Gestión de Usuarios")
    
    with st.form("user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            u = st.text_input("Usuario", placeholder="Nuevo usuario")
        with col2:
            p = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
        
        r = st.selectbox("Rol", ["empleado", "admin"])
        
        submitted = st.form_submit_button("➕ Crear usuario", type="primary", use_container_width=True)
        
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
    
    # Mostrar usuarios existentes
    st.subheader("📋 Usuarios registrados")
    df_users = safe_dataframe("SELECT id, username, role FROM users")
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True, hide_index=True)

def page_empleados():
    st.title("🧑‍💼 Gestión de Empleados")
    
    # Formulario en dos columnas
    with st.form("employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
        with col2:
            goal = st.number_input("Meta mensual", value=300, min_value=1, step=50)
        
        # Selector de usuario
        df_users = safe_dataframe("SELECT id, username FROM users WHERE role='empleado'")
        if not df_users.empty:
            user_options = {row['username']: row['id'] for _, row in df_users.iterrows()}
            selected_user = st.selectbox("Usuario asociado", options=list(user_options.keys()))
            user_id = user_options[selected_user]
        else:
            st.warning("⚠️ No hay usuarios con rol 'empleado' disponibles")
            user_id = None
        
        submitted = st.form_submit_button("➕ Registrar empleado", type="primary", use_container_width=True)
        
        if submitted and name and user_id:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO employees (name, goal, user_id) VALUES (?,?,?)",
                           (name, goal, user_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Empleado '{name}' registrado exitosamente")
            except sqlite3.IntegrityError:
                st.error("❌ Este usuario ya tiene un empleado asociado")
            except Exception as e:
                st.error(f"❌ Error al registrar: {e}")
    
    # Lista de empleados
    st.subheader("📋 Empleados activos")
    df_emp = safe_dataframe("""
        SELECT e.id, e.name, e.goal, u.username 
        FROM employees e
        JOIN users u ON e.user_id = u.id
    """)
    if not df_emp.empty:
        st.dataframe(df_emp, use_container_width=True, hide_index=True)

def page_registrar_ventas():
    st.title("📝 Registro Diario de Ventas")
    
    # Verificar si el usuario tiene empleado asociado
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM employees WHERE user_id=?", 
               (st.session_state.user["id"],))
    emp = cur.fetchone()
    conn.close()
    
    if not emp:
        st.error("❌ No tienes un empleado asociado. Contacta al administrador.")
        return
    
    st.success(f"👤 Registrando para: **{emp[1]}**")
    
    # Formulario con validaciones
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
        st.metric("Total del día", f"{total} unidades")
        
        submitted = st.form_submit_button("💾 Guardar ventas", type="primary", use_container_width=True)
        
        if submitted:
            if total > 0:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO sales (employee_id, date, autoliquidable, oferta, marca, adicional)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp[0], str(date.today()), aut, of, ma, ad))
                    conn.commit()
                    conn.close()
                    st.success("✅ Venta registrada exitosamente!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
            else:
                st.warning("⚠️ Debes ingresar al menos una unidad")

def page_mi_desempeno():
    st.title("📊 Mi Desempeño Personal")
    
    # Obtener ID del empleado
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM employees WHERE user_id=?", 
               (st.session_state.user["id"],))
    emp = cur.fetchone()
    
    if not emp:
        st.error("❌ No tienes un empleado asociado")
        return
    
    # Cargar datos
    df = safe_dataframe(f"""
        SELECT date, autoliquidable, oferta, marca, adicional
        FROM sales 
        WHERE employee_id = {emp[0]}
        ORDER BY date
    """)
    
    if df.empty:
        st.info("ℹ️ Aún no has registrado ventas")
        # Botón para ir a registrar
        if st.button("📝 Ir a registrar ventas", type="primary"):
            st.session_state.page = "Registrar ventas"
            st.rerun()
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    total = int(df["total"].sum())
    promedio = int(df["total"].mean())
    mejor_dia = int(df["total"].max())
    
    with col1:
        st.metric("Total acumulado", f"{total:,}")
    with col2:
        st.metric("Promedio diario", f"{promedio:,}")
    with col3:
        st.metric("Mejor día", f"{mejor_dia:,}")
    
    # Gráfico de evolución
    fig = px.line(df, x="date", y="total", 
                 title="📈 Evolución personal de ventas",
                 markers=True)
    fig.update_traces(line_color="#4f7cff", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    # Desglose por tipo
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(tipos, use_container_width=True, hide_index=True)
    with col2:
        fig2 = px.pie(tipos, values='Cantidad', names='Tipo')
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- CONTROL PRINCIPAL ---------------- #
def main():
    """Función principal de la aplicación"""
    if not st.session_state.user:
        show_login()
    else:
        show_menu()
        
        # Navegación de páginas
        if st.session_state.page == "Dashboard":
            page_dashboard()
        elif st.session_state.page == "Ranking":
            page_ranking()
        elif st.session_state.page == "Usuarios":
            page_usuarios()
        elif st.session_state.page == "Empleados":
            page_empleados()
        elif st.session_state.page == "Registrar ventas":
            page_registrar_ventas()
        elif st.session_state.page == "Mi desempeño":
            page_mi_desempeno()

if __name__ == "__main__":
    main()