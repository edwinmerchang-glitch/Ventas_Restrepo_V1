"""Punto de entrada principal – Locatel AIS Sistema de Ventas."""
import streamlit as st
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from database import create_tables, migrate_database, verify_database
from auth import authenticate, create_user
from utils import execute_query, execute_insert, get_employee_info
from keep_alive import init_keep_alive
from backup_manager import render_backup_page

# ── Importar páginas ──────────────────────────────────────────────────
from modules.dashboard_page      import page_dashboard
from modules.ranking_page        import page_ranking
from modules.ventas_page         import page_registrar_ventas
from modules.desempeno_page      import page_mi_desempeno, page_mi_perfil
from modules.afiliaciones_page   import (page_registrar_afiliaciones,
                                        page_mis_afiliaciones,
                                        page_admin_afiliaciones)
from modules.admin_page          import (page_empleados, page_usuarios,
                                        page_reportes, page_auditoria)

# Calendario en español
try:
    import locale
    locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
except Exception:
    pass

# ── Configuración de página ───────────────────────────────────────────
st.set_page_config(
    page_title="Ventas Equipo Locatel Restrepo",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "### Locatel AIS – Sistema de Gestión de Ventas v2.0\nEquipo Locatel Restrepo."
    },
)

# ── CSS ───────────────────────────────────────────────────────────────
def _load_css():
    css = r"""
/* ==================== LOCATEL AIS — DISEÑO PROFESIONAL v4.0 ==================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
    --primary:        #1a56db;
    --primary-dark:   #1341b3;
    --primary-light:  #eff6ff;
    --primary-glow:   rgba(26, 86, 219, 0.15);
    --accent:         #0ea5e9;
    --success:        #16a34a;
    --warning:        #d97706;
    --danger:         #dc2626;
    --bg:             #f0f4f8;
    --surface:        #ffffff;
    --surface-2:      #f8fafc;
    --border:         #e2e8f0;
    --border-strong:  #cbd5e1;
    --text-primary:   #0f172a;
    --text-secondary: #475569;
    --text-muted:     #94a3b8;
    --shadow-xs: 0 1px 2px rgba(0,0,0,.05);
    --shadow-sm: 0 2px 8px rgba(0,0,0,.07);
    --shadow-md: 0 4px 16px rgba(0,0,0,.09);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.12);
    --shadow-xl: 0 16px 48px rgba(0,0,0,.16);
    --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-xl: 20px; --r-full: 9999px;
    --font: 'Inter', 'Segoe UI', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

.stApp {{ background: var(--bg); font-family: var(--font); color: var(--text-primary); }}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: var(--r-full); }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

h1 {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-primary); margin-bottom: .25rem; }}
h2 {{ font-size: 1.35rem; font-weight: 600; letter-spacing: -0.02em; color: var(--text-primary); }}
h3 {{ font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }}

/* ── CARDS ── */
.card {{ background: var(--surface); border-radius: var(--r-lg); padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: var(--shadow-sm); border: 1px solid var(--border); transition: box-shadow .2s, transform .2s; }}
.card:hover {{ box-shadow: var(--shadow-md); transform: translateY(-1px); }}
.card-header {{ font-size: .8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--text-muted); margin-bottom: 1rem; display: flex; align-items: center; gap: .5rem; }}
.card-header::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}

/* ── KPI CARDS ── */
.kpi-card {{ background: var(--surface); border-radius: var(--r-lg); padding: 1.25rem 1.5rem; border: 1px solid var(--border); box-shadow: var(--shadow-sm); position: relative; overflow: hidden; transition: all .2s; }}
.kpi-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--primary), var(--accent)); }}
.kpi-card:hover {{ box-shadow: var(--shadow-md); transform: translateY(-2px); }}
.kpi-title {{ font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .07em; color: var(--text-muted); margin-bottom: .25rem; }}
.kpi-value {{ font-size: 2rem; font-weight: 800; color: var(--text-primary); line-height: 1; letter-spacing: -0.04em; }}
.kpi-sub {{ font-size: .75rem; color: var(--text-muted); margin-top: .4rem; }}
.kpi-trend-up {{ color: var(--success); font-weight: 600; }}
.kpi-trend-down {{ color: var(--danger); font-weight: 600; }}
.kpi-blue .kpi-value   {{ color: var(--primary); }}
.kpi-green .kpi-value  {{ color: var(--success); }}
.kpi-amber .kpi-value  {{ color: var(--warning); }}
.kpi-purple .kpi-value {{ color: #7c3aed; }}
.kpi-blue::before   {{ background: linear-gradient(90deg, #1a56db, #0ea5e9); }}
.kpi-green::before  {{ background: linear-gradient(90deg, #16a34a, #22c55e); }}
.kpi-amber::before  {{ background: linear-gradient(90deg, #d97706, #f59e0b); }}
.kpi-purple::before {{ background: linear-gradient(90deg, #7c3aed, #a855f7); }}

/* ── BADGES ── */
.badge {{ display: inline-flex; align-items: center; gap: .3rem; padding: .25rem .75rem; border-radius: var(--r-full); font-size: .72rem; font-weight: 600; letter-spacing: .02em; line-height: 1.4; }}
.badge-cargo-drogueria {{ background: #dbeafe; color: #1d4ed8; }}
.badge-cargo-equipos   {{ background: #dcfce7; color: #15803d; }}
.badge-cargo-pasillos  {{ background: #fef9c3; color: #92400e; }}
.badge-cargo-cajas     {{ background: #ede9fe; color: #6d28d9; }}
.badge-depto           {{ background: var(--surface-2); color: var(--text-secondary); border: 1px solid var(--border); }}
.badge-admin           {{ background: #fce7f3; color: #9d174d; }}
.badge-success         {{ background: #dcfce7; color: #15803d; }}
.badge-warning         {{ background: #fef3c7; color: #92400e; }}
.badge-danger          {{ background: #fee2e2; color: #b91c1c; }}

/* ── PROGRESS ── */
.progress {{ background: var(--border); border-radius: var(--r-full); height: 8px; overflow: hidden; margin: .5rem 0; }}
.progress-bar {{ height: 100%; border-radius: var(--r-full); background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width .6s cubic-bezier(.4,0,.2,1); }}
.progress-bar-success {{ background: linear-gradient(90deg, var(--success), #22c55e); }}
.progress-bar-warning {{ background: linear-gradient(90deg, var(--warning), #f59e0b); }}
.progress-bar-danger  {{ background: linear-gradient(90deg, var(--danger), #f87171); }}

/* ── RANKING ── */
.rank-card {{ background: var(--surface); border-radius: var(--r-lg); padding: 1rem 1.25rem; display: flex; align-items: center; gap: 1rem; border: 1px solid var(--border); box-shadow: var(--shadow-xs); margin-bottom: .75rem; transition: all .2s; }}
.rank-card:hover {{ box-shadow: var(--shadow-md); border-color: var(--border-strong); }}
.rank-medal {{ width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: 800; flex-shrink: 0; }}
.rank-1 {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); color: white; box-shadow: 0 4px 12px rgba(245,158,11,.4); }}
.rank-2 {{ background: linear-gradient(135deg, #94a3b8, #64748b); color: white; box-shadow: 0 4px 12px rgba(100,116,139,.4); }}
.rank-3 {{ background: linear-gradient(135deg, #f97316, #ea580c); color: white; box-shadow: 0 4px 12px rgba(249,115,22,.4); }}
.rank-n {{ background: var(--surface-2); color: var(--text-muted); border: 1px solid var(--border); font-size: .9rem; }}
.rank-info {{ flex: 1; min-width: 0; }}
.rank-name {{ font-weight: 600; font-size: .95rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.rank-dept {{ font-size: .75rem; color: var(--text-muted); margin-top: 2px; }}
.rank-score {{ font-size: 1.4rem; font-weight: 800; color: var(--primary); letter-spacing: -0.04em; }}
.rank-score-label {{ font-size: .65rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; }}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {{
    border-radius: var(--r-md) !important;
    border: 1.5px solid var(--border) !important;
    font-family: var(--font) !important;
    font-size: .9rem !important;
    color: var(--text-primary) !important;
    background: var(--surface) !important;
    padding: .6rem .9rem !important;
    transition: border .15s, box-shadow .15s !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-glow) !important;
    outline: none !important;
}}
.stSelectbox > div > div {{ border-radius: var(--r-md) !important; border: 1.5px solid var(--border) !important; }}
label {{ font-size: .8rem !important; font-weight: 600 !important; color: var(--text-secondary) !important; letter-spacing: .02em !important; }}

/* ── BUTTONS ── */
.stButton > button {{ border-radius: var(--r-md) !important; font-family: var(--font) !important; font-weight: 600 !important; font-size: .875rem !important; padding: .55rem 1.25rem !important; transition: all .15s ease !important; }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important; color: white !important; border: none !important; box-shadow: 0 2px 8px rgba(26,86,219,.3) !important; }}
.stButton > button[kind="primary"]:hover {{ box-shadow: 0 4px 16px rgba(26,86,219,.45) !important; transform: translateY(-1px) !important; }}
.stButton > button[kind="secondary"] {{ background: var(--surface) !important; border: 1.5px solid var(--border) !important; color: var(--text-secondary) !important; }}
.stButton > button[kind="secondary"]:hover {{ border-color: var(--primary) !important; color: var(--primary) !important; background: var(--primary-light) !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ gap: .35rem !important; background: var(--surface) !important; padding: .4rem !important; border-radius: var(--r-lg) !important; border: 1px solid var(--border) !important; box-shadow: var(--shadow-xs) !important; }}
.stTabs [data-baseweb="tab"] {{ border-radius: var(--r-md) !important; padding: .45rem 1rem !important; font-weight: 500 !important; font-size: .85rem !important; color: var(--text-secondary) !important; transition: all .15s !important; border: none !important; }}
.stTabs [data-baseweb="tab"]:hover {{ background: var(--surface-2) !important; color: var(--text-primary) !important; }}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{ background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important; color: white !important; box-shadow: 0 2px 8px rgba(26,86,219,.3) !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}

/* ── METRICS ── */
[data-testid="metric-container"] {{ background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; padding: 1.1rem 1.25rem !important; box-shadow: var(--shadow-xs) !important; }}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{ font-size: .75rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: .06em !important; color: var(--text-muted) !important; }}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{ font-size: 1.75rem !important; font-weight: 800 !important; color: var(--text-primary) !important; letter-spacing: -0.04em !important; }}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{ border-radius: var(--r-lg) !important; border: 1px solid var(--border) !important; overflow: hidden !important; box-shadow: var(--shadow-xs) !important; }}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{ background: var(--text-primary) !important; border-right: none !important; }}
[data-testid="stSidebar"] * {{ color: white !important; }}
[data-testid="stSidebar"] .stButton > button {{ background: rgba(255,255,255,.08) !important; border: 1px solid rgba(255,255,255,.12) !important; color: rgba(255,255,255,.9) !important; width: 100% !important; text-align: left !important; justify-content: flex-start !important; border-radius: var(--r-md) !important; }}
[data-testid="stSidebar"] .stButton > button:hover {{ background: rgba(255,255,255,.15) !important; border-color: rgba(255,255,255,.25) !important; color: white !important; }}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{ background: var(--primary) !important; border-color: var(--primary) !important; color: white !important; }}

/* ── USER CARD ── */
.user-card {{ background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.05)); border: 1px solid rgba(255,255,255,.12); border-radius: var(--r-lg); padding: 1.25rem 1rem; margin-bottom: 1.25rem; text-align: center; }}
.user-avatar {{ width: 52px; height: 52px; background: linear-gradient(135deg, var(--primary), var(--accent)); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; font-weight: 700; color: white; margin: 0 auto .75rem; box-shadow: 0 4px 12px rgba(26,86,219,.4); }}
.user-name {{ font-size: 1rem; font-weight: 700; color: white; margin-bottom: .3rem; }}
.user-badge {{ display: inline-block; background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.2); border-radius: var(--r-full); padding: .2rem .75rem; font-size: .72rem; font-weight: 600; color: rgba(255,255,255,.9); margin: .15rem; }}
.user-meta {{ display: flex; justify-content: center; gap: 1rem; margin-top: .75rem; background: rgba(255,255,255,.07); border-radius: var(--r-md); padding: .6rem; font-size: .75rem; color: rgba(255,255,255,.7); }}

/* ── NAV ── */
.nav-section {{ font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: rgba(255,255,255,.35) !important; padding: .75rem .5rem .3rem; margin-top: .5rem; }}
.nav-divider {{ height: 1px; background: rgba(255,255,255,.08); margin: .75rem 0; }}

/* ── EXPANDER ── */
.streamlit-expanderHeader {{ border-radius: var(--r-md) !important; background: var(--surface) !important; border: 1px solid var(--border) !important; font-weight: 600 !important; font-size: .875rem !important; }}
.streamlit-expanderHeader:hover {{ background: var(--surface-2) !important; }}

/* ── KEEP-ALIVE ── */
.keep-alive-card {{ background: linear-gradient(135deg, rgba(26,86,219,.8), rgba(14,165,233,.7)); border-radius: var(--r-md); padding: .9rem 1rem; margin: 1rem 0; border: 1px solid rgba(255,255,255,.15); }}
.keep-alive-header {{ display: flex; align-items: center; gap: .5rem; font-weight: 600; font-size: .8rem; margin-bottom: .5rem; }}
.pulse-dot {{ width: 8px; height: 8px; background: #4ade80; border-radius: 50%; animation: pulse 2s infinite; flex-shrink: 0; }}
@keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(74,222,128,.7); }} 70% {{ box-shadow: 0 0 0 8px rgba(74,222,128,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(74,222,128,0); }} }}
.keep-alive-stats {{ display: flex; justify-content: space-between; align-items: center; font-size: .75rem; background: rgba(255,255,255,.12); padding: .5rem .75rem; border-radius: var(--r-sm); }}
.ping-badge {{ background: rgba(255,255,255,.2); padding: 2px .6rem; border-radius: var(--r-full); font-weight: 600; font-size: .7rem; }}

/* ── PAGE HEADER ── */
.page-header {{ display: flex; align-items: center; gap: .75rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }}
.page-header-icon {{ width: 44px; height: 44px; background: var(--primary-light); border-radius: var(--r-md); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; border: 1px solid rgba(26,86,219,.15); }}
.page-header-title {{ font-size: 1.5rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.03em; }}
.page-header-sub {{ font-size: .8rem; color: var(--text-muted); margin-top: 1px; }}

/* ── HAMBURGER ── */
.hamburger-btn {{ background: var(--primary); color: white; border: none; border-radius: var(--r-md); width: 42px; height: 42px; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(26,86,219,.4); transition: all .2s; }}
.hamburger-btn:hover {{ background: var(--primary-dark); transform: scale(1.05); }}
.menu-overlay {{ position: fixed; inset: 0; background: rgba(15,23,42,.5); z-index: 998; backdrop-filter: blur(4px); }}
[data-testid="collapsedControl"] {{ display: none !important; }}

/* ── LOGIN ── */
.login-card {{ background: var(--surface); border-radius: var(--r-xl); padding: 2rem; box-shadow: var(--shadow-xl); border: 1px solid var(--border); }}

/* ── EMPTY STATE ── */
.empty-state {{ text-align: center; padding: 3.5rem 2rem; color: var(--text-muted); }}
.empty-state-icon {{ font-size: 3.5rem; margin-bottom: .75rem; opacity: .5; }}
.empty-state-title {{ font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); margin-bottom: .4rem; }}
.empty-state-desc {{ font-size: .85rem; }}

/* ── ANIMATIONS ── */
@keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.fade-in {{ animation: fadeInUp .3s ease-out; }}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {{ h1 {{ font-size: 1.35rem; }} .kpi-value {{ font-size: 1.5rem; }} .card {{ padding: 1rem; }} }}
"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🏥 Ventas Equipo Locatel Restrepo")
        st.caption("Sistema de Gestión de Ventas")
        st.divider()

        with st.form("login_form"):
            username  = st.text_input("👤 Usuario", placeholder="tu.usuario")
            password  = st.text_input("🔑 Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar sesión", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.warning("⚠️ Ingresa usuario y contraseña.")
                else:
                    user = authenticate(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "Dashboard" if user["role"] == "admin" else "Registrar ventas"
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas.")


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
              <h3 style="margin:.25rem 0 0;font-size:1rem">Locatel Restrepo</h3>
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
