"""Páginas de afiliaciones (empleado y admin)."""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import date
from utils import (execute_query, execute_insert, safe_dataframe,
                   get_employee_info, get_badge_class, periodo_a_fecha,
                   render_progress, check_meta_celebration, DEPARTAMENTOS)
from export_utils import barra_exportacion


def page_registrar_afiliaciones():
    st.title("📱 Registro de Afiliaciones - AIS")

    emp_info = get_employee_info(st.session_state.user["id"])
    if not emp_info:
        st.error("❌ No tienes un empleado asociado."); return

    badge_class = get_badge_class(emp_info[2])
    meta_afil   = emp_info[5] if len(emp_info) > 5 and emp_info[5] else 50

    st.markdown(
        f"""<div class="card">
            <h4>Registrando para: {emp_info[1]}</h4>
            <p><span class="badge {badge_class}">{emp_info[2]}</span>
               <span class="badge badge-depto">{emp_info[3]}</span>
               🎯 Meta mensual afiliaciones: <strong>{meta_afil}</strong></p>
        </div>""",
        unsafe_allow_html=True,
    )

    col_f, _ = st.columns([2,2])
    with col_f:
        fecha = st.date_input("📅 Fecha del registro", value=date.today(), max_value=date.today())

    existe = execute_query(
        "SELECT id, cantidad FROM afiliaciones WHERE employee_id=? AND fecha=?",
        (emp_info[0], str(fecha)),
    )
    ya_reg = bool(existe)
    cant_existente = existe[0][1] if ya_reg else 0

    if ya_reg:
        st.info(f"ℹ️ Ya tienes {cant_existente} afiliación(es) para el {fecha.strftime('%d/%m/%Y')}. Editando.")

    with st.form("afil_form"):
        st.subheader(f"Afiliaciones del {fecha.strftime('%d/%m/%Y')}")
        cantidad = st.number_input("Cantidad de afiliaciones", min_value=0, step=1,
                                   value=cant_existente if ya_reg else 1)

        mes  = fecha.strftime("%Y-%m")
        res  = execute_query("SELECT SUM(cantidad) FROM afiliaciones WHERE employee_id=? AND fecha LIKE ?",
                             (emp_info[0], f"{mes}%"))
        afil_mes = res[0][0] or 0 if res else 0
        afil_mes_adj = (afil_mes - cant_existente + cantidad) if ya_reg else (afil_mes + cantidad)

        render_progress(afil_mes_adj, meta_afil, "Progreso mensual de afiliaciones")

        _, col_b, _ = st.columns([1,2,1])
        with col_b:
            submitted = st.form_submit_button("💾 Registrar afiliaciones", use_container_width=True, type="primary")

        if submitted:
            if cantidad == 0:
                st.warning("⚠️ Ingresa al menos una afiliación.")
            else:
                if ya_reg:
                    ok = execute_insert(
                        "UPDATE afiliaciones SET cantidad=? WHERE employee_id=? AND fecha=?",
                        (cantidad, emp_info[0], str(fecha)),
                        audit_action=f"Editar afiliaciones {fecha}",
                    )
                else:
                    ok = execute_insert(
                        "INSERT INTO afiliaciones (employee_id,fecha,cantidad) VALUES (?,?,?)",
                        (emp_info[0], str(fecha), cantidad),
                        audit_action=f"Registrar afiliaciones {fecha}",
                    )
                if ok:
                    st.success(f"✅ {cantidad} afiliación(es) guardadas para el {fecha.strftime('%d/%m/%Y')}.")
                    check_meta_celebration(afil_mes_adj, meta_afil)
                    time.sleep(1); st.rerun()

    st.divider()
    st.subheader("📋 Historial reciente")
    df_h = safe_dataframe(
        "SELECT fecha Fecha, cantidad Afiliaciones FROM afiliaciones WHERE employee_id=? ORDER BY fecha DESC LIMIT 15",
        (emp_info[0],),
    )
    if not df_h.empty:
        df_h["Fecha"] = pd.to_datetime(df_h["Fecha"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        barra_exportacion(df_h, "Historial Afiliaciones", nombre_archivo="afil_historial", key_prefix="afil_h")
    else:
        st.info("No hay afiliaciones registradas aún.")


def page_mis_afiliaciones():
    st.title("📊 Mis Afiliaciones - AIS")

    emp_info = get_employee_info(st.session_state.user["id"])
    if not emp_info: st.error("❌ No tienes empleado asociado."); return

    meta_afil = emp_info[5] if len(emp_info) > 5 else 50

    col_p, col_b = st.columns([3,1])
    with col_p: periodo = st.selectbox("Período", ["Esta semana","Este mes","Este trimestre","Este año","Todo"])
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar"): st.cache_data.clear(); st.rerun()

    fi = periodo_a_fecha(periodo)
    df = safe_dataframe(
        "SELECT fecha, cantidad FROM afiliaciones WHERE employee_id=? AND fecha>=? ORDER BY fecha DESC",
        (emp_info[0], fi),
    )

    if df.empty:
        st.info(f"No hay afiliaciones en {periodo.lower()}."); return

    df["fecha"] = pd.to_datetime(df["fecha"])
    total = int(df["cantidad"].sum())

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Total período", f"{total:,}")
    col2.metric("Promedio diario", f"{int(df['cantidad'].mean()):,}")
    col3.metric("Mejor día", f"{int(df['cantidad'].max()):,}")
    col4.metric("Progreso meta", f"{(total/meta_afil*100):.1f}%" if meta_afil else "—")

    render_progress(total, meta_afil, f"Meta mensual afiliaciones ({meta_afil})")

    fig = px.bar(df, x="fecha", y="cantidad", title=f"Afiliaciones – {periodo}",
                 labels={"fecha":"Fecha","cantidad":"Afiliaciones"})
    st.plotly_chart(fig, use_container_width=True)

    df_d = df.copy(); df_d["fecha"] = df_d["fecha"].dt.strftime("%d/%m/%Y")
    df_d.columns = ["Fecha","Afiliaciones"]
    st.dataframe(df_d, use_container_width=True, hide_index=True)
    barra_exportacion(df_d, "Mis Afiliaciones", nombre_archivo="mis_afiliaciones", key_prefix="mis_afil")


def page_admin_afiliaciones():
    st.title("⚙️ Administración de Afiliaciones")

    tab1, tab2, tab3 = st.tabs(["🎯 Metas", "🏆 Ranking", "📈 Reporte"])

    with tab1:
        emps = execute_query("SELECT id, name, department, position, meta_afiliaciones FROM employees ORDER BY department, name")
        if not emps: st.info("No hay empleados."); return
        for emp in emps:
            with st.expander(f"{emp[1]} – {emp[2]} ({emp[3]})"):
                c1, c2 = st.columns([3,1])
                with c1:
                    nueva = st.number_input("Meta mensual afiliaciones", min_value=1, value=emp[4] or 50,
                                            step=10, key=f"meta_{emp[0]}")
                with c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Guardar", key=f"g_{emp[0]}"):
                        ok = execute_insert("UPDATE employees SET meta_afiliaciones=? WHERE id=?",
                                           (nueva, emp[0]), audit_action=f"Actualizar meta afil. {emp[1]}")
                        if ok: st.success("✅ Meta actualizada."); st.rerun()

    with tab2:
        col_p, col_d = st.columns(2)
        with col_p: periodo = st.selectbox("Período", ["Este mes","Esta semana","Este trimestre","Todo"], key="r_periodo")
        with col_d: depto   = st.selectbox("Departamento", ["Todos"]+DEPARTAMENTOS, key="r_depto")

        fi = periodo_a_fecha(periodo)
        q = """
            SELECT e.name Empleado, e.department Departamento, e.meta_afiliaciones Meta,
                   COALESCE(SUM(a.cantidad),0) Total,
                   COUNT(DISTINCT a.fecha) Dias,
                   ROUND(COALESCE(SUM(a.cantidad),0)*100.0/e.meta_afiliaciones,1) Pct
            FROM employees e LEFT JOIN afiliaciones a ON e.id=a.employee_id AND a.fecha>=?
        """
        params = [fi]
        if depto != "Todos": q += " WHERE e.department=?"; params.append(depto)
        q += " GROUP BY e.id ORDER BY Total DESC"
        df = safe_dataframe(q, params)

        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            fig = px.bar(df, x="Empleado", y="Total", color="Departamento",
                         title="Afiliaciones por empleado", text="Total")
            fig.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)
            barra_exportacion(df, "Ranking Afiliaciones", nombre_archivo="ranking_afil", key_prefix="r_afil")

    with tab3:
        c1, c2 = st.columns(2)
        with c1: fi = st.date_input("Desde", value=date.today().replace(day=1), key="rep_fi")
        with c2: ff = st.date_input("Hasta", value=date.today(), key="rep_ff")
        df = safe_dataframe("""
            SELECT a.fecha, e.department, e.name empleado, a.cantidad
            FROM afiliaciones a JOIN employees e ON a.employee_id=e.id
            WHERE a.fecha BETWEEN ? AND ? ORDER BY a.fecha DESC
        """, (fi, ff))
        if df.empty: st.info("Sin registros en el período.")
        else:
            c1,c2,c3 = st.columns(3)
            c1.metric("Total", f"{int(df['cantidad'].sum()):,}")
            c2.metric("Prom. diario", f"{int(df.groupby('fecha')['cantidad'].sum().mean()):,}")
            c3.metric("Días con reg.", len(df["fecha"].unique()))

            depto_df = df.groupby("department")["cantidad"].sum().reset_index()
            fig_p = px.pie(depto_df, values="cantidad", names="department", title="Por departamento")
            st.plotly_chart(fig_p, use_container_width=True)

            daily_df = df.groupby("fecha")["cantidad"].sum().reset_index()
            fig_l = px.line(daily_df, x="fecha", y="cantidad", title="Evolución diaria", markers=True)
            st.plotly_chart(fig_l, use_container_width=True)

            st.dataframe(df, use_container_width=True, hide_index=True)
            barra_exportacion(df, "Reporte Afiliaciones", nombre_archivo="rep_afil", key_prefix="rep_a")
