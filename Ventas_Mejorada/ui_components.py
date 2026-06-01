"""
Componentes UI modernos para Locatel AIS
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_kpi_card(title, value, icon, trend=None, trend_value=None, color="primary"):
    """
    Renderiza una tarjeta KPI moderna
    
    Args:
        title: Título del KPI
        value: Valor principal
        icon: Emoji o icono
        trend: 'up' o 'down'
        trend_value: Valor del trend
        color: 'primary', 'success', 'warning', 'danger'
    """
    colors = {
        "primary": {"bg": "linear-gradient(135deg, #4361ee, #3a56d4)", "text": "white"},
        "success": {"bg": "linear-gradient(135deg, #10b981, #059669)", "text": "white"},
        "warning": {"bg": "linear-gradient(135deg, #f59e0b, #d97706)", "text": "white"},
        "danger": {"bg": "linear-gradient(135deg, #ef4444, #dc2626)", "text": "white"},
        "info": {"bg": "linear-gradient(135deg, #06b6d4, #0891b2)", "text": "white"}
    }
    
    style = colors.get(color, colors["primary"])
    
    trend_html = ""
    if trend:
        trend_class = "trend-up" if trend == "up" else "trend-down"
        trend_icon = "📈" if trend == "up" else "📉"
        trend_html = f'<div class="kpi-trend {trend_class}">{trend_icon} {trend_value}</div>'
    
    st.markdown(f"""
    <div class="kpi-card" style="background: {style['bg']}; color: {style['text']};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="kpi-title" style="color: rgba(255,255,255,0.8);">{title}</div>
                <div class="kpi-value" style="color: white;">{value}</div>
                {trend_html}
            </div>
            <div style="font-size: 2rem;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_modern_card(title, content, icon=None, variant="default"):
    """
    Renderiza una tarjeta moderna
    
    Args:
        title: Título de la tarjeta
        content: Contenido HTML o texto
        icon: Emoji o icono
        variant: 'default', 'gradient', 'outline'
    """
    styles = {
        "default": "background: white; border: 1px solid var(--gray-100);",
        "gradient": "background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white;",
        "outline": "background: transparent; border: 2px solid var(--primary);"
    }
    
    style = styles.get(variant, styles["default"])
    
    header_style = "color: white;" if variant == "gradient" else "color: var(--gray-700);"
    
    st.markdown(f"""
    <div class="card" style="{style}">
        <div class="card-header" style="{header_style}">
            {icon + ' ' if icon else ''}{title}
        </div>
        <div style="{'color: white;' if variant == 'gradient' else ''}">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_empty_state(title, description, icon="📭"):
    """
    Renderiza un estado vacío moderno
    """
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def render_progress_card(title, current, total, icon="🎯"):
    """
    Renderiza una tarjeta de progreso moderna
    """
    percentage = (current / total * 100) if total > 0 else 0
    
    st.markdown(f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <div style="font-size: 0.75rem; color: var(--gray-500); text-transform: uppercase;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: var(--gray-800);">{current:,} / {total:,}</div>
            </div>
            <div style="font-size: 2rem;">{icon}</div>
        </div>
        <div class="progress">
            <div class="progress-bar" style="width: {min(percentage, 100)}%;"></div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--gray-600);">
            {percentage:.1f}% completado
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_modern_chart(df, x, y, title, chart_type="line", color=None):
    """
    Crea gráficos modernos con Plotly
    """
    colors = {
        "line": "#4361ee",
        "bar": "#10b981",
        "area": "#06b6d4"
    }
    
    color_used = color or colors.get(chart_type, "#4361ee")
    
    if chart_type == "line":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode='lines+markers',
            line=dict(color=color_used, width=3),
            marker=dict(size=8, color=color_used, symbol='circle'),
            fill='tozeroy',
            fillcolor=f'rgba({int(color_used[1:3], 16)}, {int(color_used[3:5], 16)}, {int(color_used[5:7], 16)}, 0.1)'
        ))
    elif chart_type == "bar":
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[y],
            marker=dict(color=color_used, line=dict(color='white', width=2)),
            text=df[y],
            textposition='outside'
        ))
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode='lines',
            fill='tonexty',
            line=dict(color=color_used, width=2),
            fillcolor=f'rgba({int(color_used[1:3], 16)}, {int(color_used[3:5], 16)}, {int(color_used[5:7], 16)}, 0.3)'
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, weight='bold'), x=0.05),
        xaxis=dict(
            title=dict(text=x, font=dict(size=12)),
            gridcolor='#e2e8f0',
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text=y, font=dict(size=12)),
            gridcolor='#e2e8f0',
            showgrid=True,
            gridwidth=1
        ),
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=50, r=30, t=80, b=50),
        font=dict(family="Inter, sans-serif")
    )
    
    return fig

def render_metric_grid(metrics):
    """
    Renderiza una cuadrícula de métricas
    
    Args:
        metrics: Lista de diccionarios con keys: title, value, icon, trend
    """
    cols = st.columns(len(metrics))
    
    for idx, (col, metric) in enumerate(zip(cols, metrics)):
        with col:
            trend_html = ""
            if metric.get('trend'):
                trend_class = "trend-up" if metric['trend'] == 'up' else "trend-down"
                trend_icon = "↑" if metric['trend'] == 'up' else "↓"
                trend_html = f'<div class="kpi-trend {trend_class}">{trend_icon} {metric.get("trend_value", "")}</div>'
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{metric['icon']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-label">{metric['title']}</div>
                {trend_html}
            </div>
            """, unsafe_allow_html=True)

def render_timeline(events):
    """
    Renderiza una línea de tiempo
    
    Args:
        events: Lista de diccionarios con keys: date, title, description
    """
    timeline_html = '<div class="timeline">'
    
    for event in events:
        timeline_html += f"""
        <div class="timeline-item">
            <div style="font-size: 0.75rem; color: var(--gray-500);">{event['date']}</div>
            <div style="font-weight: 600; margin: 0.25rem 0;">{event['title']}</div>
            <div style="font-size: 0.875rem; color: var(--gray-600);">{event.get('description', '')}</div>
        </div>
        """
    
    timeline_html += '</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)

def render_stats_table(df, title, columns_config=None):
    """
    Renderiza una tabla de estadísticas con formato moderno
    """
    st.markdown(f'<div class="section-title">📊 {title}</div>', unsafe_allow_html=True)
    
    if columns_config:
        styled_df = df.style
        for col, config in columns_config.items():
            if config.get('type') == 'currency':
                styled_df = styled_df.format({col: '${:,.0f}'})
            elif config.get('type') == 'percentage':
                styled_df = styled_df.format({col: '{:.1f}%'})
            elif config.get('type') == 'number':
                styled_df = styled_df.format({col: '{:,.0f}'})
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)