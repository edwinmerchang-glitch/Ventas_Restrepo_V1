import requests
import time
import threading
import streamlit as st
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self):
        self.last_ping = None
        self.ping_count = 0
        self.is_running = False
        # IMPORTANTE: Cambia esta URL por la TUYA
        self.app_url = "https://seguimiento-ventas-restrepo.streamlit.app/#ventas-equipo-locatel-restrepo"  # <--- CAMBIA ESTO
        
    def ping(self):
        """Hacer ping a la aplicación"""
        try:
            response = requests.get(
                self.app_url,
                timeout=10,
                headers={'User-Agent': 'KeepAliveBot/1.0'},
                params={'_t': str(self.ping_count)}
            )
            
            self.last_ping = datetime.now()
            self.ping_count += 1
            
            logger.info(f"✅ Ping #{self.ping_count} - {self.last_ping.strftime('%H:%M:%S')}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error en ping: {e}")
            return False
    
    def ping_loop(self):
        """Loop infinito de pings"""
        while self.is_running:
            self.ping()
            time.sleep(600)  # 10 minutos
    
    def start(self):
        """Iniciar el thread"""
        if not self.is_running:
            self.is_running = True
            thread = threading.Thread(target=self.ping_loop, daemon=True)
            thread.start()
            logger.info("🚀 Keep-alive iniciado")
            return True
        return False
    
    def get_status(self):
        """Obtener estado"""
        status = {
            'running': self.is_running,
            'ping_count': self.ping_count,
            'last_ping': self.last_ping.strftime('%H:%M:%S') if self.last_ping else None,
        }
        return status

# Instancia global
keep_alive = KeepAlive()

def init_keep_alive():
    """Inicializar keep-alive"""
    if 'keep_alive_initialized' not in st.session_state:
        keep_alive.start()
        st.session_state.keep_alive_initialized = True
        logger.info("📡 Keep-alive inicializado")

def render_keep_alive_status():
    """Mostrar estado en la UI"""
    if 'keep_alive_initialized' in st.session_state:
        status = keep_alive.get_status()
        if status['running']:
            st.caption(f"📡 Keep-alive: {status['ping_count']} pings")