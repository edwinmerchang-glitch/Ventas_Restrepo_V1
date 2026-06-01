"""Página: Registro diario de ventas."""
import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
from utils import execute_query, execute_insert, get_employee_info, get_badge_class, render_progress, check_meta_celebration
from export_utils import barra_exportacion


def page_registrar_ventas():
    st.title("📝 Registro Diario de Ventas - AIS")

    emp_info = get_employee_info(st.session_state.user["id"])
    if not emp_info:
        st.error("❌ No tienes un empleado asociado. Contacta al administrador.")
        return

    badge_class = get_badge_class(emp_info[2])
    st.markdown(
        f"""
        <div class="card">
            <h4>Registrando para: {emp_info[1]}</h4>
            <p>
                <span class="badge {badge_class}">{emp_info[2]}</span>
                <span class="badge badge-depto">{emp_info[3]}</span>
                🎯 Meta mensual: <strong>{emp_info[4]:,}</strong> unidades
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_fecha, _ = st.columns([2, 2])
    with col_fecha:
        fecha_registro = st.date_input(
            "📅 Fecha del registro",
            value=date.today(),
            max_value=date.today(),
            help="No puede ser futura",
        )

    # Revisar si ya existe registro
    result = execute_query(
        "SELECT autoliquidable, oferta, marca, adicional FROM sales WHERE employee_id = ? AND date = ?",
        (emp_info[0], str(fecha_registro)),
    )
    ya_registro = bool(result)
    vals_existentes = result[0] if ya_registro else (0, 0, 0, 0)

    if ya_registro:
        st.info(f"ℹ️ Ya tienes ventas para el {fecha_registro.strftime('%d/%m/%Y')}. Editando registro existente.")

    with st.form("ventas_form"):
        st.subheader(f"Ventas del {fecha_registro.strftime('%d/%m/%Y')}")
        col1, col2 = st.columns(2)
        with col1:
            aut = st.number_input("📦 Autoliquidable", min_value=0, step=1, value=int(vals_existentes[0]))
            ma  = st.number_input("🏷 Marca Propia",    min_value=0, step=1, value=int(vals_existentes[2]))
        with col2:
            of  = st.number_input("🔥 Oferta Semana",      min_value=0, step=1, value=int(vals_existentes[1]))
            ad  = st.number_input("➕ Producto Adicional", min_value=0, step=1, value=int(vals_existentes[3]))

        total = aut + of + ma + ad

        # Progreso mensual en tiempo real
        mes_actual = fecha_registro.strftime("%Y-%m")
        res_mes = execute_query(
            "SELECT SUM(autoliquidable + oferta + marca + adicional) FROM sales WHERE employee_id = ? AND date LIKE ?",
            (emp_info[0], f"{mes_actual}%"),
        )
        ventas_mes = res_mes[0][0] or 0 if res_mes else 0
        ventas_mes_ajustadas = ventas_mes - sum(vals_existentes) + total if ya_registro else ventas_mes + total

        render_progress(ventas_mes_ajustadas, emp_info[4], "Progreso mensual con este registro")

        col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
        with col_b2:
            submitted = st.form_submit_button(
                "💾 Guardar ventas", use_container_width=True, type="primary"
            )

        if submitted:
            if total == 0:
                st.warning("⚠️ Debes ingresar al menos una unidad.")
            else:
                if ya_registro:
                    ok = execute_insert(
                        """UPDATE sales SET autoliquidable=?, oferta=?, marca=?, adicional=?, updated_at=CURRENT_TIMESTAMP
                           WHERE employee_id=? AND date=?""",
                        (aut, of, ma, ad, emp_info[0], str(fecha_registro)),
                        audit_action=f"Editar ventas {fecha_registro}",
                    )
                    msg = f"✅ Ventas actualizadas para el {fecha_registro.strftime('%d/%m/%Y')}."
                else:
                    ok = execute_insert(
                        "INSERT INTO sales (employee_id, date, autoliquidable, oferta, marca, adicional) VALUES (?,?,?,?,?,?)",
                        (emp_info[0], str(fecha_registro), aut, of, ma, ad),
                        audit_action=f"Registrar ventas {fecha_registro}",
                    )
                    msg = f"✅ Ventas registradas para el {fecha_registro.strftime('%d/%m/%Y')}."

                if ok:
                    st.success(msg)
                    check_meta_celebration(ventas_mes_ajustadas, emp_info[4])
                    time.sleep(1)
                    st.rerun()

    # Historial reciente
    st.divider()
    st.subheader("📋 Historial reciente (últimos 15 días)")
    from utils import safe_dataframe
    df_hist = safe_dataframe(
        """SELECT date as Fecha, autoliquidable as Auto, oferta as Oferta,
                  marca as Marca, adicional as Adicional,
                  (autoliquidable+oferta+marca+adicional) as Total
           FROM sales WHERE employee_id=? ORDER BY date DESC LIMIT 15""",
        (emp_info[0],),
    )
    if not df_hist.empty:
        df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        barra_exportacion(df_hist, titulo="Historial de Ventas", nombre_archivo="ventas_historial", key_prefix="hist_v")
    else:
        st.info("No hay ventas registradas aún.")
