import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from database import create_tables, get_connection
from auth import authenticate, create_user

def create_default_admin():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    if total_users == 0:
        create_user("admin", "admin123", "admin")

    conn.close()


st.set_page_config("Ventas PRO", layout="wide", page_icon="📊")
create_tables()
create_default_admin()


def css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css()

# ---------------- LOGIN ----------------

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("📊 Sistema Profesional de Ventas")

    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
            user = authenticate(u,p)
            if user:
                st.session_state.user = user
                st.experimental_rerun()
            else:
                st.error("Credenciales incorrectas")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------- MENÚ ----------------

if st.session_state.user["role"] == "admin":
    menu = st.sidebar.radio("📂 Menú",["Dashboard","Ranking","Usuarios","Empleados"])
else:
    menu = st.sidebar.radio("📂 Menú",["Registrar ventas","Mi desempeño","Ranking"])

# ---------------- DASHBOARD ADMIN ----------------

if menu == "Dashboard":
    st.title("📊 Dashboard Ejecutivo")

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sales", conn)

    if df.empty:
        st.info("No hay ventas registradas")
        st.stop()

    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Total Unidades", int(df["total"].sum()))
    col2.metric("Autoliquidable", int(df["autoliquidable"].sum()))
    col3.metric("Oferta Semana", int(df["oferta"].sum()))
    col4.metric("Marca Propia", int(df["marca"].sum()))

    fig = px.line(df, x="date", y="total", title="📈 Evolución diaria de ventas")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- RANKING ----------------

if menu == "Ranking":
    st.title("🏆 Ranking de Ventas")

    conn = get_connection()
    df = pd.read_sql("""
    SELECT e.name, SUM(s.autoliquidable+s.oferta+s.marca+s.adicional) as total
    FROM sales s
    JOIN employees e ON e.id=s.employee_id
    GROUP BY e.name
    ORDER BY total DESC
    """, conn)

    if df.empty:
        st.info("No hay datos aún")
        st.stop()

    df["Posición"] = range(1,len(df)+1)
    st.dataframe(df, use_container_width=True)

    fig = px.bar(df, x="name", y="total", title="🔥 Ranking General")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- USUARIOS ----------------

if menu == "Usuarios":
    st.title("👤 Crear usuarios")

    with st.form("user_form"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        r = st.selectbox("Rol",["admin","empleado"])
        b = st.form_submit_button("Crear usuario")

        if b:
            create_user(u,p,r)
            st.success("Usuario creado")

# ---------------- EMPLEADOS ----------------

if menu == "Empleados":
    st.title("🧑‍💼 Gestión de empleados")

    name = st.text_input("Nombre")
    user_id = st.number_input("ID usuario",step=1)
    goal = st.number_input("Meta mensual",value=300)

    if st.button("Registrar"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO employees VALUES (NULL,?,?,?)",(name,goal,user_id))
        conn.commit()
        conn.close()
        st.success("Empleado registrado")

# ---------------- REGISTRAR VENTAS ----------------

if menu == "Registrar ventas":
    st.title("📝 Registro Diario")

    with st.form("ventas"):
        col1,col2 = st.columns(2)
        aut = col1.number_input("📦 Autoliquidable",0)
        of = col2.number_input("🔥 Oferta Semana",0)
        ma = col1.number_input("🏷 Marca Propia",0)
        ad = col2.number_input("➕ Producto Adicional",0)

        if st.form_submit_button("Guardar"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM employees WHERE user_id=?",(st.session_state.user["id"],))
            emp = cur.fetchone()

            if emp:
                cur.execute("""
                    INSERT INTO sales VALUES (NULL,?,?,?,?,?,?)
                """,(emp[0],str(date.today()),aut,of,ma,ad))

                conn.commit()
                st.success("Venta registrada")
            else:
                st.error("Empleado no asociado")

# ---------------- DESEMPEÑO PERSONAL ----------------

if menu == "Mi desempeño":
    st.title("📊 Mi Desempeño")

    conn = get_connection()
    df = pd.read_sql(f"""
        SELECT * FROM sales WHERE employee_id=
        (SELECT id FROM employees WHERE user_id={st.session_state.user['id']})
    """,conn)

    if df.empty:
        st.info("Sin registros")
        st.stop()

    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)

    st.metric("Total acumulado", int(df["total"].sum()))

    fig = px.line(df, x="date", y="total", title="📈 Evolución personal")
    st.plotly_chart(fig, use_container_width=True)
