"""Utilidades compartidas: acceso a BD, helpers de UI y constantes."""
import streamlit as st
import pandas as pd
from datetime import date
from database import get_connection, log_audit

# ── Listas de dominio ────────────────────────────────────────────────
CARGOS = [
    "Ais Droguería",
    "Ais Equipos Médicos",
    "Ais Pasillos",
    "Ais Cajas",
]

DEPARTAMENTOS = [
    "Droguería",
    "Equipos Médicos",
    "Pasillos",
    "Cajas",
]

DEPT_COLORS = {
    "Droguería":       "#FF6B6B",
    "Equipos Médicos": "#4ECDC4",
    "Pasillos":        "#45B7D1",
    "Cajas":           "#96CEB4",
}

# ── Acceso BD ─────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def safe_dataframe(query: str, params=None) -> pd.DataFrame:
    """Ejecuta SELECT y devuelve DataFrame (cacheado 60 s)."""
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=list(params) if params else None)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()


def execute_query(query: str, params=None):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or [])
        return cur.fetchall()
    except Exception as e:
        st.error(f"Error en consulta: {e}")
        return []
    finally:
        if conn:
            conn.close()


def execute_insert(query: str, params=None, audit_action=None) -> bool:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or [])
        conn.commit()
        st.cache_data.clear()

        # Auditoría opcional
        if audit_action and "user" in st.session_state and st.session_state.user:
            u = st.session_state.user
            log_audit(u["id"], u["username"], audit_action)

        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


# ── Empleado helper ───────────────────────────────────────────────────
def get_employee_info(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT id, name, position, department, goal, meta_afiliaciones
               FROM employees WHERE user_id = ?""",
            (user_id,),
        )
        emp = cur.fetchone()
        conn.close()
        return emp
    except Exception:
        return None


def get_badge_class(position: str) -> str:
    if "Droguería" in position:
        return "badge-cargo-drogueria"
    elif "Equipos" in position:
        return "badge-cargo-equipos"
    elif "Pasillos" in position:
        return "badge-cargo-pasillos"
    elif "Cajas" in position:
        return "badge-cargo-cajas"
    return "badge-cargo-drogueria"


# ── Período helper ────────────────────────────────────────────────────
def periodo_a_fecha(periodo: str) -> date:
    """Convierte nombre de período a fecha de inicio."""
    hoy = date.today()
    if periodo == "Esta semana":
        return hoy - pd.Timedelta(days=hoy.weekday())
    elif periodo == "Este mes":
        return hoy.replace(day=1)
    elif periodo == "Este trimestre":
        m = hoy.month
        return hoy.replace(month=((m - 1) // 3) * 3 + 1, day=1)
    elif periodo == "Este año":
        return hoy.replace(month=1, day=1)
    return date(2000, 1, 1)


# ── Barra de meta con color dinámico ─────────────────────────────────
def render_progress(actual: int, meta: int, label: str = "Progreso"):
    pct = min((actual / meta * 100) if meta > 0 else 0, 100)
    if pct >= 100:
        bar_class = "progress-bar progress-bar-success"
    elif pct >= 70:
        bar_class = "progress-bar progress-bar-warning"
    else:
        bar_class = "progress-bar"

    st.markdown(
        f"""
        <div style="margin:12px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:.8rem;color:var(--text-muted)">{label}</span>
            <span style="font-size:.8rem;font-weight:600">{actual:,} / {meta:,} ({pct:.1f}%)</span>
          </div>
          <div class="progress">
            <div class="{bar_class}" style="width:{pct}%"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Notificación de meta alcanzada ───────────────────────────────────
def check_meta_celebration(actual: int, meta: int):
    if meta > 0 and actual >= meta:
        st.balloons()
        st.success(f"🏆 ¡Felicitaciones! Superaste tu meta de {meta:,} unidades con {actual:,}!")
