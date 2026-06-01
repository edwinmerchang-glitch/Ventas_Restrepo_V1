"""Página: Dashboard de ventas con comparativo mes anterior."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta
from utils import safe_dataframe, DEPARTAMENTOS, DEPT_COLORS
from export_utils import barra_exportacion


def _mes_anterior_range(fecha_inicio, fecha_fin):
    """Devuelve el mismo rango pero un mes atrás."""
    dias = (fecha_fin - fecha_inicio).days
    fin_ant = fecha_inicio - relativedelta(days=1)
    ini_ant = fin_ant - relativedelta(days=dias)
    return ini_ant, fin_ant


def page_dashboard():
    st.title("📊 Dashboard de Ventas")

    # ── Filtros ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())
    with col3:
        depto_filtro = st.multiselect("Departamento", DEPARTAMENTOS, default=DEPARTAMENTOS)

    if st.button("🔄 Recargar"):
        st.cache_data.clear()
        st.rerun()

    # ── Query principal ───────────────────────────────────────────────
    base_query = """
        SELECT s.*, e.name, e.position, e.department
        FROM sales s JOIN employees e ON s.employee_id = e.id
        WHERE date BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    if depto_filtro:
        ph = ",".join(["?"] * len(depto_filtro))
        base_query += f" AND e.department IN ({ph})"
        params.extend(depto_filtro)
    base_query += " ORDER BY date DESC"

    df = safe_dataframe(base_query, params)
    if df.empty:
        st.info("ℹ️ No hay ventas en el período seleccionado.")
        return

    df["total"] = df[["autoliquidable", "oferta", "marca", "adicional"]].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])

    # ── Comparativo período anterior ──────────────────────────────────
    ini_ant, fin_ant = _mes_anterior_range(fecha_inicio, fecha_fin)
    params_ant = [ini_ant, fin_ant]
    q_ant = base_query.replace("WHERE date BETWEEN ? AND ?", "WHERE date BETWEEN ? AND ?")
    if depto_filtro:
        ph = ",".join(["?"] * len(depto_filtro))
        params_ant_full = [ini_ant, fin_ant] + depto_filtro
    else:
        params_ant_full = [ini_ant, fin_ant]
    df_ant = safe_dataframe(base_query, params_ant_full)
    total_anterior = 0
    if not df_ant.empty:
        df_ant["total"] = df_ant[["autoliquidable", "oferta", "marca", "adicional"]].sum(axis=1)
        total_anterior = int(df_ant["total"].sum())

    # ── KPIs ──────────────────────────────────────────────────────────
    total_actual = int(df["total"].sum())
    delta_pct = ((total_actual - total_anterior) / total_anterior * 100) if total_anterior else None
    delta_str = f"{delta_pct:+.1f}% vs período anterior" if delta_pct is not None else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unidades", f"{total_actual:,}", delta=delta_str)
    with col2:
        st.metric("Autoliquidable", f"{int(df['autoliquidable'].sum()):,}")
    with col3:
        st.metric("Oferta Semana", f"{int(df['oferta'].sum()):,}")
    with col4:
        st.metric("Marca Propia", f"{int(df['marca'].sum()):,}")

    # ── Tabs ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Evolución", "📊 Distribución", "👥 Por empleado", "📅 Comparativo"])

    with tab1:
        vista = st.radio("Ver:", ["📊 Todas las áreas", "🔍 Por departamento"], horizontal=True)
        if vista == "📊 Todas las áreas":
            df_pivot = df.pivot_table(index="date", columns="department", values="total", aggfunc="sum", fill_value=0).reset_index()
            if len(df_pivot.columns) > 1:
                fig = px.area(df_pivot, x="date", y=df_pivot.columns[1:],
                              title="Evolución de ventas – todas las áreas",
                              labels={"value": "Unidades", "date": "Fecha", "variable": "Depto"},
                              color_discrete_map=DEPT_COLORS)
                fig.update_layout(hovermode="x unified", height=450)
                st.plotly_chart(fig, use_container_width=True)
        else:
            deptos = df["department"].unique()
            depto = st.selectbox("Departamento:", deptos)
            df_d = df[df["department"] == depto].groupby("date").agg(
                autoliquidable=("autoliquidable","sum"), oferta=("oferta","sum"),
                marca=("marca","sum"), adicional=("adicional","sum")
            ).reset_index()
            df_m = df_d.melt(id_vars=["date"], value_vars=["autoliquidable","oferta","marca","adicional"],
                             var_name="Categoría", value_name="Unidades")
            df_m["Categoría"] = df_m["Categoría"].map({
                "autoliquidable":"Autoliquidable","oferta":"Oferta","marca":"Marca Propia","adicional":"Adicional"})
            fig = px.line(df_m, x="date", y="Unidades", color="Categoría",
                          title=f"Evolución {depto}", markers=True)
            fig.update_layout(height=450, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        df_daily = df.groupby("date")["total"].sum().reset_index()
        c1, c2, c3 = st.columns(3)
        c1.metric("Promedio diario", f"{int(df_daily['total'].mean()):,}")
        mejor = df_daily.loc[df_daily["total"].idxmax()]
        c2.metric("Mejor día", f"{int(mejor['total']):,}", help=f"{mejor['date'].strftime('%d/%m/%Y')}")
        c3.metric("Total período", f"{int(df_daily['total'].sum()):,}")

    with tab2:
        dist = df.groupby("department")[["autoliquidable","oferta","marca","adicional"]].sum().reset_index()
        dist_m = dist.melt(id_vars=["department"], var_name="Tipo", value_name="Cantidad")
        dist_m["Tipo"] = dist_m["Tipo"].map({"autoliquidable":"Autoliquidable","oferta":"Oferta","marca":"Marca Propia","adicional":"Adicional"})
        fig2 = px.bar(dist_m, x="department", y="Cantidad", color="Tipo", barmode="stack",
                      title="Distribución por departamento", text="Cantidad")
        fig2.update_traces(texttemplate="%{text}", textposition="inside")
        st.plotly_chart(fig2, use_container_width=True)

        totales = df[["autoliquidable","oferta","marca","adicional"]].sum()
        pie_df = pd.DataFrame({
            "Tipo":["Autoliquidable","Oferta","Marca Propia","Adicional"],
            "Cantidad":[totales["autoliquidable"],totales["oferta"],totales["marca"],totales["adicional"]]
        })
        fig_pie = px.pie(pie_df, values="Cantidad", names="Tipo", title="Distribución porcentual total")
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        emp_res = df.groupby(["name","department"]).agg(
            autoliquidable=("autoliquidable","sum"), oferta=("oferta","sum"),
            marca=("marca","sum"), adicional=("adicional","sum"), total=("total","sum")
        ).reset_index().sort_values(["department","total"], ascending=[True,False])

        if not emp_res.empty:
            em = emp_res.melt(id_vars=["name","department"], value_vars=["autoliquidable","oferta","marca","adicional"],
                              var_name="Categoría", value_name="Cantidad")
            em["Categoría"] = em["Categoría"].map({"autoliquidable":"Auto","oferta":"Oferta","marca":"Marca","adicional":"Adicional"})
            fig_e = px.bar(em, x="name", y="Cantidad", color="Categoría", barmode="stack",
                           title="Ventas por empleado", text="Cantidad")
            fig_e.update_layout(xaxis_tickangle=-45, height=480)
            st.plotly_chart(fig_e, use_container_width=True)

            st.subheader("📋 Tabla de rendimiento")
            tabla = emp_res.copy()
            for c in ["autoliquidable","oferta","marca","adicional","total"]:
                tabla[c] = tabla[c].apply(lambda x: f"{int(x):,}")
            tabla.columns = ["Empleado","Departamento","Autoliquidable","Oferta","Marca","Adicional","Total"]
            st.dataframe(tabla, use_container_width=True, hide_index=True)
            barra_exportacion(emp_res, titulo="Ventas por Empleado", subtitulo=f"{fecha_inicio} → {fecha_fin}",
                              nombre_archivo="ventas_empleados", key_prefix="dash_emp")

    with tab4:
        st.subheader("📅 Comparativo con período anterior")
        if total_anterior == 0:
            st.info("No hay datos del período anterior para comparar.")
        else:
            comp_df = pd.DataFrame({
                "Período": [f"{fecha_inicio} – {fecha_fin}", f"{ini_ant} – {fin_ant}"],
                "Total": [total_actual, total_anterior]
            })
            fig_comp = px.bar(comp_df, x="Período", y="Total", color="Período",
                              title="Comparativo de períodos", text="Total", color_discrete_sequence=["#1a56db","#94a3b8"])
            fig_comp.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig_comp.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig_comp, use_container_width=True)

            variacion = total_actual - total_anterior
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Período actual", f"{total_actual:,}")
            col_b.metric("Período anterior", f"{total_anterior:,}")
            col_c.metric("Variación", f"{variacion:+,}", delta=f"{delta_pct:+.1f}%" if delta_pct else None)
