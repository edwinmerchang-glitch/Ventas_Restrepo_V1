"""Página: Ranking de ventas."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils import safe_dataframe, execute_query, periodo_a_fecha, DEPARTAMENTOS


def _medal(pos):
    if pos == 1: return "🥇"
    if pos == 2: return "🥈"
    if pos == 3: return "🥉"
    return f"#{pos}"


def page_ranking():
    st.title("🏆 Ranking de Ventas")

    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox("Período", ["Este mes", "Esta semana", "Este trimestre", "Este año", "Todo"], key="rank_periodo")
    with col2:
        depto = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS, key="rank_depto")

    fecha_inicio = periodo_a_fecha(periodo)

    query = """
        SELECT e.name, e.department, e.position, e.goal,
               COALESCE(SUM(s.autoliquidable+s.oferta+s.marca+s.adicional),0) as total,
               COALESCE(SUM(s.autoliquidable),0) as auto,
               COALESCE(SUM(s.oferta),0) as oferta,
               COALESCE(SUM(s.marca),0) as marca,
               COALESCE(SUM(s.adicional),0) as adicional,
               COUNT(DISTINCT s.date) as dias_activos
        FROM employees e
        LEFT JOIN sales s ON e.id = s.employee_id AND s.date >= ?
    """
    params = [fecha_inicio]
    if depto != "Todos":
        query += " WHERE e.department = ?"
        params.append(depto)
    query += " GROUP BY e.id ORDER BY total DESC"

    df = safe_dataframe(query, params)
    if df.empty:
        st.info("No hay datos para este período.")
        return

    df["Cumplimiento %"] = (df["total"] / df["goal"] * 100).round(1)

    # Cards del ranking
    st.subheader(f"📋 Ranking – {periodo}" + (f" – {depto}" if depto != "Todos" else ""))
    for i, row in df.iterrows():
        pos = i + 1
        pct = row["Cumplimiento %"]
        bar_color = "#16a34a" if pct >= 100 else "#d97706" if pct >= 70 else "#1a56db"
        bar_w = min(pct, 100)
        medal = _medal(pos)

        rank_class = f"rank-{min(pos,4) if pos <= 3 else 'n'}"
        st.markdown(
            f"""
            <div class="rank-card">
              <div class="rank-medal {rank_class}">{medal}</div>
              <div class="rank-info">
                <div class="rank-name">{row['name']}</div>
                <div class="rank-dept">{row['department']} · {row['position']} · {int(row['dias_activos'])} días activos</div>
                <div style="margin-top:6px">
                  <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--text-muted);margin-bottom:3px">
                    <span>Meta: {int(row['goal']):,}</span><span>{pct:.1f}%</span>
                  </div>
                  <div style="background:var(--border);border-radius:999px;height:6px;overflow:hidden">
                    <div style="width:{bar_w}%;height:100%;background:{bar_color};border-radius:999px"></div>
                  </div>
                </div>
              </div>
              <div style="text-align:right;flex-shrink:0">
                <div class="rank-score">{int(row['total']):,}</div>
                <div class="rank-score-label">unidades</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Gráfico
    st.divider()
    fig = px.bar(df.head(10), x="name", y="total", color="department",
                 title="Top 10 – Unidades vendidas",
                 labels={"name":"Empleado","total":"Unidades","department":"Depto"},
                 text="total")
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(xaxis_tickangle=-35, height=420)
    st.plotly_chart(fig, use_container_width=True)
