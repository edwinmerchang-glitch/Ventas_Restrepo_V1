"""Página: Mi desempeño y Mi perfil."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils import safe_dataframe, execute_query, execute_insert, get_employee_info, get_badge_class, periodo_a_fecha, render_progress
from auth import hash_password
from export_utils import barra_exportacion


def page_mi_desempeno():
    st.title("📊 Mi Desempeño Personal - AIS")

    emp_info = get_employee_info(st.session_state.user["id"])
    if not emp_info:
        st.error("❌ No tienes un empleado asociado.")
        return

    col_p, col_btn = st.columns([3, 1])
    with col_p:
        periodo = st.selectbox("Período", ["Esta semana", "Este mes", "Este trimestre", "Este año", "Todo"])
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar"):
            st.cache_data.clear()
            st.rerun()

    fecha_inicio = periodo_a_fecha(periodo)

    df = safe_dataframe(
        """SELECT date, autoliquidable, oferta, marca, adicional
           FROM sales WHERE employee_id=? AND date>=? ORDER BY date""",
        (emp_info[0], fecha_inicio),
    )

    if df.empty:
        st.info(f"ℹ️ No hay registros en {periodo.lower()}.")
        return

    df["total"] = df[["autoliquidable", "oferta", "marca", "adicional"]].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])

    total_p = int(df["total"].sum())
    promedio = int(df["total"].mean())
    mejor = int(df["total"].max())
    dias_reg = len(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total período", f"{total_p:,}")
    col2.metric("Promedio diario", f"{promedio:,}")
    col3.metric("Mejor día", f"{mejor:,}")
    col4.metric("Días registrados", dias_reg)

    render_progress(total_p, emp_info[4], "Progreso vs meta mensual")

    # Gráfico combinado: barras por categoría + línea total
    tab1, tab2 = st.tabs(["📈 Evolución", "🥧 Por categoría"])

    with tab1:
        fig = px.line(df, x="date", y="total", title=f"Evolución – {periodo}", markers=True,
                      labels={"date":"Fecha","total":"Unidades"})
        fig.update_traces(line_color="#1a56db", line_width=2.5)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        cat_totales = {
            "Autoliquidable": int(df["autoliquidable"].sum()),
            "Oferta":         int(df["oferta"].sum()),
            "Marca Propia":   int(df["marca"].sum()),
            "Adicional":      int(df["adicional"].sum()),
        }
        pie_df = pd.DataFrame({"Categoría": list(cat_totales.keys()), "Unidades": list(cat_totales.values())})
        fig_pie = px.pie(pie_df, values="Unidades", names="Categoría", title="Distribución personal")
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    barra_exportacion(df, titulo="Mi Desempeño", nombre_archivo="mi_desempeno", key_prefix="desemp")


def page_mi_perfil():
    st.title("👤 Mi Perfil - AIS")

    emp_info = get_employee_info(st.session_state.user["id"])
    user = st.session_state.user

    if emp_info:
        badge_class = get_badge_class(emp_info[2])
        # Ventas del mes actual
        from datetime import date as d
        mes = d.today().strftime("%Y-%m")
        from utils import execute_query as eq
        res = eq(
            "SELECT SUM(autoliquidable+oferta+marca+adicional) FROM sales WHERE employee_id=? AND date LIKE ?",
            (emp_info[0], f"{mes}%"),
        )
        ventas_mes = res[0][0] or 0 if res else 0

        st.markdown(
            f"""
            <div class="card" style="text-align:center">
                <h2>{emp_info[1]}</h2>
                <p>
                    <span class="badge {badge_class}" style="font-size:15px">{emp_info[2]}</span>
                    <span class="badge badge-depto" style="font-size:15px">{emp_info[3]}</span>
                </p>
                <p class="metric">🎯 Meta: <strong>{emp_info[4]:,}</strong> unidades/mes</p>
                <p class="metric">📦 Este mes: <strong>{ventas_mes:,}</strong> unidades</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_progress(ventas_mes, emp_info[4], "Progreso mes actual")
    else:
        st.warning("⚠️ No tienes perfil de empleado configurado. Contacta al administrador.")

    # Cambio de contraseña propio
    st.divider()
    st.subheader("🔑 Cambiar mi contraseña")
    with st.form("cambiar_pass_propio"):
        pass_actual = st.text_input("Contraseña actual", type="password")
        pass_nueva  = st.text_input("Nueva contraseña (mín. 6 caracteres)", type="password")
        pass_conf   = st.text_input("Confirmar nueva contraseña", type="password")
        submitted   = st.form_submit_button("Actualizar contraseña", type="primary")

        if submitted:
            if not pass_actual or not pass_nueva:
                st.warning("⚠️ Completa todos los campos.")
            elif len(pass_nueva) < 6:
                st.warning("⚠️ La contraseña debe tener al menos 6 caracteres.")
            elif pass_nueva != pass_conf:
                st.error("❌ Las contraseñas nuevas no coinciden.")
            else:
                from database import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT password FROM users WHERE id=?", (user["id"],))
                row = cur.fetchone()
                conn.close()
                if row and hash_password(pass_actual) == row[0]:
                    from utils import execute_insert as ei
                    ok = ei(
                        "UPDATE users SET password=? WHERE id=?",
                        (hash_password(pass_nueva), user["id"]),
                        audit_action="Cambio de contraseña propio",
                    )
                    if ok:
                        st.success("✅ Contraseña actualizada exitosamente.")
                else:
                    st.error("❌ La contraseña actual es incorrecta.")
