# keep_alive.py - Agrega esta función

import streamlit as st
import threading
import time
from datetime import datetime

# Variable global para contar pings
_ping_count = 0
_last_ping = None
_keep_alive_thread = None
_keep_alive_running = False

def ping():
    """Función que se ejecuta periódicamente para mantener la app activa"""
    global _ping_count, _last_ping
    while _keep_alive_running:
        _ping_count += 1
        _last_ping = datetime.now()
        time.sleep(60)  # Ping cada minuto

def init_keep_alive():
    """Inicializar el thread de keep-alive"""
    global _keep_alive_thread, _keep_alive_running
    if _keep_alive_thread is None or not _keep_alive_thread.is_alive():
        _keep_alive_running = True
        _keep_alive_thread = threading.Thread(target=ping, daemon=True)
        _keep_alive_thread.start()

def get_ping_count():
    """Obtener el número de pings realizados"""
    global _ping_count
    return _ping_count

def get_last_ping():
    """Obtener la hora del último ping"""
    global _last_ping
    return _last_ping

def render_keep_alive_status():
    """Renderizar el estado del keep-alive en Streamlit"""
    global _ping_count, _last_ping
    
    if _last_ping:
        last_ping_str = _last_ping.strftime("%H:%M:%S")
        st.caption(f"🔄 Keep-alive: {_ping_count} pings | Último: {last_ping_str}")
    else:
        st.caption("🔄 Keep-alive: Iniciando...")