"""Punto de entrada principal – Locatel AIS Sistema de Ventas."""
import streamlit as st
from database import create_tables, migrate_database, verify_database
from auth import authenticate, create_user
from utils import execute_query, execute_insert, get_employee_info
from keep_alive import init_keep_alive
from backup_manager import render_backup_page

# ── Importar páginas ──────────────────────────────────────────────────
from pages.dashboard_page      import page_dashboard
from pages.ranking_page        import page_ranking
from pages.ventas_page         import page_registrar_ventas
from pages.desempeno_page      import page_mi_desempeno, page_mi_perfil
from pages.afiliaciones_page   import (page_registrar_afiliaciones,
                                        page_mis_afiliaciones,
                                        page_admin_afiliaciones)
from pages.admin_page          import (page_empleados, page_usuarios,
                                        page_reportes, page_auditoria)

# ── Configuración de página ───────────────────────────────────────────
st.set_page_config(
    page_title="Locatel AIS – Ventas",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "### Locatel AIS – Sistema de Gestión de Ventas v2.0\nEquipo Locatel Restrepo."
    },
)

# ── CSS ───────────────────────────────────────────────────────────────
def _load_css():
    try:
        with open("styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

_load_css()

# ── Inicialización BD ─────────────────────────────────────────────────
with st.spinner("🔄 Inicializando sistema…"):
    try:
        create_tables()
        migrate_database()
        verify_database()
    except Exception as e:
        st.error(f"❌ Error inicializando base de datos: {e}")
        st.stop()


def _crear_admin_defecto():
    try:
        total = execute_query("SELECT COUNT(*) FROM users")[0][0]
        if total == 0:
            create_user("admin", "admin123", "admin")
    except Exception:
        pass


_crear_admin_defecto()

# ── Session state ─────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False
if "page" not in st.session_state:
    st.session_state.page = "Login"


# ══════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown(
        """
        <div style="max-width:420px;margin:60px auto 0">
          <div class="card" style="padding:2.5rem">
            <div style="text-align:center;margin-bottom:1.5rem">
              <span style="font-size:2.8rem">🏥</span>
              <h2 style="margin:.5rem 0 .25rem">Locatel AIS</h2>
              <p style="color:var(--text-muted);font-size:.85rem">Sistema de Gestión de Ventas</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("👤 Usuario", placeholder="tu.usuario")
        password = st.text_input("🔑 Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.warning("⚠️ Ingresa usuario y contraseña.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    # Verificar si debe cambiar contraseña
                    res = execute_query("SELECT must_change_password FROM users WHERE id=?", (user["id"],))
                    if res and res[0][0]:
                        st.session_state.page = "Cambiar contraseña"
                    else:
                        st.session_state.page = "Dashboard" if user["role"] == "admin" else "Registrar ventas"
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")

    st.markdown("</div></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  CAMBIO DE CONTRASEÑA OBLIGATORIO (primer login admin)
# ══════════════════════════════════════════════════════════════════════
def show_force_password_change():
    st.title("🔑 Cambia tu contraseña")
    st.warning("Por seguridad debes establecer una contraseña nueva antes de continuar.")

    with st.form("force_pass"):
        nueva  = st.text_input("Nueva contraseña (mín. 8 caracteres)", type="password")
        conf   = st.text_input("Confirmar contraseña", type="password")
        submit = st.form_submit_button("Guardar y continuar", type="primary", use_container_width=True)

        if submit:
            if len(nueva) < 8:
                st.warning("⚠️ Mínimo 8 caracteres.")
            elif nueva != conf:
                st.error("❌ Las contraseñas no coinciden.")
            else:
                from auth import hash_password
                ok = execute_insert(
                    "UPDATE users SET password=?, must_change_password=0 WHERE id=?",
                    (hash_password(nueva), st.session_state.user["id"]),
                )
                if ok:
                    st.success("✅ Contraseña actualizada. Bienvenido/a.")
                    st.session_state.page = "Dashboard" if st.session_state.user["role"] == "admin" else "Registrar ventas"
                    import time; time.sleep(1); st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  MENÚ LATERAL
# ══════════════════════════════════════════════════════════════════════
def show_menu():
    user  = st.session_state.user
    role  = user["role"]
    empinfo = get_employee_info(user["id"])

    # ── Sidebar ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center;padding:1rem 0 .5rem">
              <span style="font-size:2rem">🏥</span>
              <h3 style="margin:.25rem 0 0;font-size:1rem">Locatel AIS</h3>
            </div>
            <div style="background:var(--surface-2);border-radius:var(--r-md);padding:.75rem 1rem;margin-bottom:1rem;border:1px solid var(--border)">
              <div style="font-weight:600;font-size:.9rem">{user['username']}</div>
              <div style="font-size:.75rem;color:var(--text-muted)">{empinfo[1] if empinfo else ''}</div>
              <span class="badge {'badge-admin' if role=='admin' else 'badge-success'}" style="margin-top:.35rem">
                {'👑 Admin' if role == 'admin' else '👤 Empleado'}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Menú según rol
        if role == "admin":
            _seccion("📊 Análisis", [
                ("Dashboard",          "📊"),
                ("Ranking",            "🏆"),
                ("Reportes",           "📈"),
                ("Auditoría",          "🔍"),
            ])
            _seccion("👥 Gestión", [
                ("Empleados",          "🧑‍💼"),
                ("Usuarios",           "👤"),
                ("Admin Afiliaciones", "⚙️"),
                ("Backups",            "💾"),
            ])
            _seccion("📝 Mis Registros", [
                ("Registrar ventas",       "📝"),
                ("Registrar afiliaciones", "📱"),
                ("Mi desempeño",           "📊"),
                ("Mis afiliaciones",       "📋"),
                ("Mi perfil",              "👤"),
            ])
        else:
            _seccion("📝 Mis Registros", [
                ("Registrar ventas",       "📝"),
                ("Registrar afiliaciones", "📱"),
                ("Mi desempeño",           "📊"),
                ("Mis afiliaciones",       "📋"),
                ("Mi perfil",              "👤"),
            ])
            _seccion("📊 Ver", [
                ("Ranking",  "🏆"),
            ])

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def _seccion(titulo, items):
    st.markdown(f"<div style='font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin:.75rem 0 .35rem .25rem'>{titulo}</div>", unsafe_allow_html=True)
    for label, icon in items:
        active = st.session_state.page == label
        btn_type = "primary" if active else "secondary"
        if st.button(f"{icon} {label}", key=f"nav_{label}", use_container_width=True, type=btn_type):
            st.session_state.page = label
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  MAPA DE PÁGINAS
# ══════════════════════════════════════════════════════════════════════
PAGES = {
    "Dashboard":             page_dashboard,
    "Ranking":               page_ranking,
    "Reportes":              page_reportes,
    "Auditoría":             page_auditoria,
    "Empleados":             page_empleados,
    "Usuarios":              page_usuarios,
    "Admin Afiliaciones":    page_admin_afiliaciones,
    "Backups":               render_backup_page,
    "Registrar ventas":      page_registrar_ventas,
    "Registrar afiliaciones":page_registrar_afiliaciones,
    "Mi desempeño":          page_mi_desempeno,
    "Mis afiliaciones":      page_mis_afiliaciones,
    "Mi perfil":             page_mi_perfil,
}

ADMIN_ONLY = {"Empleados","Usuarios","Admin Afiliaciones","Backups","Reportes","Auditoría"}


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    init_keep_alive()

    if not st.session_state.user:
        show_login()
        return

    show_menu()

    # Guard: empleados no acceden a páginas de admin
    if st.session_state.page in ADMIN_ONLY and st.session_state.user["role"] != "admin":
        st.error("🚫 No tienes permiso para acceder a esta sección.")
        return

    page_fn = PAGES.get(st.session_state.page)
    if page_fn:
        page_fn()
    else:
        if st.session_state.user["role"] == "admin":
            page_dashboard()
        else:
            page_registrar_ventas()


if __name__ == "__main__":
    main()
