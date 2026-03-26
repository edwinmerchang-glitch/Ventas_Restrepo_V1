"""
Configuración de la aplicación
"""
import streamlit as st

# Configuración de página
def setup_page_config():
    st.set_page_config(
        page_title="Locatel AIS - Sistema de Ventas",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': 'https://www.locatel.com.co/soporte',
            'Report a bug': 'mailto:soporte@locatel.co',
            'About': """
            ### Locatel AIS - Sistema de Gestión de Ventas
            **Versión:** 3.0.0
            
            Sistema integral para el registro y seguimiento de ventas y afiliaciones.
            
            Desarrollado para el equipo Locatel Restrepo.
            """
        }
    )

# Paleta de colores
COLORS = {
    'primary': '#4361ee',
    'primary_dark': '#3a56d4',
    'secondary': '#06b6d4',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#8b5cf6',
    'dark': '#1e293b',
    'light': '#f8fafc'
}

# Temas para gráficos
CHART_THEMES = {
    'light': {
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'font_color': '#1e293b',
        'grid_color': '#e2e8f0'
    },
    'dark': {
        'plot_bgcolor': '#1e293b',
        'paper_bgcolor': '#1e293b',
        'font_color': '#f8fafc',
        'grid_color': '#334155'
    }
}