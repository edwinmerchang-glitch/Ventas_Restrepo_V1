# backup_manager.py
import streamlit as st
import sqlite3
import os
import shutil
from datetime import datetime
import gzip
import io
from database import get_connection, DB_PATH
import time

def create_backup():
    """Crear un backup de la base de datos"""
    try:
        # Crear directorio de backups si no existe
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nombre del archivo backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Crear backup comprimido
        backup_gz_path = backup_path + '.gz'
        
        # Copiar la base de datos
        if os.path.exists(DB_PATH):
            # Crear una copia de seguridad
            shutil.copy2(DB_PATH, backup_path)
            
            # Comprimir el backup
            with open(backup_path, 'rb') as f_in:
                with gzip.open(backup_gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eliminar el archivo sin comprimir
            os.remove(backup_path)
            
            return True, backup_gz_path, f"✅ Backup creado: {backup_filename}.gz"
        else:
            return False, None, "❌ No se encontró la base de datos"
            
    except Exception as e:
        return False, None, f"❌ Error al crear backup: {str(e)}"

def restore_backup(uploaded_file):
    """Restaurar un backup desde archivo subido"""
    try:
        # Verificar que el archivo sea válido
        if uploaded_file is None:
            return False, "❌ No se seleccionó ningún archivo"
        
        # Validar extensión
        if not uploaded_file.name.endswith('.gz'):
            return False, "❌ El archivo debe tener extensión .gz"
        
        # Crear backup automático antes de restaurar
        st.info("📦 Creando backup de seguridad antes de restaurar...")
        backup_success, backup_path, backup_msg = create_backup()
        if backup_success:
            st.success(f"✅ Backup de seguridad creado: {os.path.basename(backup_path)}")
        
        # Leer el contenido del archivo subido
        file_content = uploaded_file.read()
        
        # Descomprimir en memoria
        try:
            with gzip.open(io.BytesIO(file_content), 'rb') as f:
                db_content = f.read()
        except Exception as e:
            return False, f"❌ El archivo no es un backup válido: {str(e)}"
        
        # Cerrar todas las conexiones a la base de datos
        try:
            # Forzar cierre de conexiones
            sqlite3.connect(DB_PATH).close()
        except:
            pass
        
        # Crear backup del archivo actual (por si algo sale mal)
        if os.path.exists(DB_PATH):
            temp_backup = DB_PATH + ".temp_backup"
            shutil.copy2(DB_PATH, temp_backup)
        
        try:
            # Escribir el nuevo contenido
            with open(DB_PATH, 'wb') as f:
                f.write(db_content)
            
            # Verificar que la base de datos restaurada sea válida
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("SELECT COUNT(*) FROM sqlite_master")
                conn.close()
                
                # Limpiar caché
                st.cache_data.clear()
                
                return True, f"✅ Backup restaurado exitosamente desde: {uploaded_file.name}"
                
            except sqlite3.Error as e:
                # Si hay error, restaurar el backup temporal
                if os.path.exists(temp_backup):
                    shutil.copy2(temp_backup, DB_PATH)
                return False, f"❌ El archivo no contiene una base de datos válida: {str(e)}"
                
        except Exception as e:
            # Restaurar backup temporal en caso de error
            if os.path.exists(temp_backup):
                shutil.copy2(temp_backup, DB_PATH)
            return False, f"❌ Error al restaurar backup: {str(e)}"
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
                
    except Exception as e:
        return False, f"❌ Error general: {str(e)}"

def list_backups():
    """Listar todos los backups disponibles"""
    backup_dir = "backups"
    backups = []
    
    if os.path.exists(backup_dir):
        files = os.listdir(backup_dir)
        for file in files:
            if file.startswith("backup_") and file.endswith(".gz"):
                file_path = os.path.join(backup_dir, file)
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                backups.append({
                    "name": file,
                    "size": size,
                    "modified": modified,
                    "path": file_path
                })
    
    # Ordenar por fecha descendente
    backups.sort(key=lambda x: x["modified"], reverse=True)
    return backups

def delete_backup(backup_name):
    """Eliminar un backup específico"""
    try:
        backup_path = os.path.join("backups", backup_name)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return True, f"✅ Backup {backup_name} eliminado"
        else:
            return False, "❌ El archivo no existe"
    except Exception as e:
        return False, f"❌ Error al eliminar: {str(e)}"

def format_size(size_bytes):
    """Formatear tamaño de archivo"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"

def render_backup_page():
    """Renderizar la página de gestión de backups"""
    st.title("💾 Gestión de Backups")
    
    tab1, tab2, tab3 = st.tabs([
        "📤 Crear Backup",
        "📥 Restaurar Backup",
        "📋 Lista de Backups"
    ])
    
    # ===== PESTAÑA 1: CREAR BACKUP =====
    with tab1:
        st.markdown("""
        <div class="card" style="background: #e8f4fd;">
            <h4>📤 Crear nuevo backup</h4>
            <p>Crea una copia de seguridad de la base de datos actual.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Crear Backup Ahora", type="primary", use_container_width=True):
                with st.spinner("Creando backup..."):
                    success, backup_path, message = create_backup()
                    
                if success:
                    st.success(message)
                    st.balloons()
                    
                    # Botón para descargar
                    with open(backup_path, 'rb') as f:
                        backup_data = f.read()
                    
                    st.download_button(
                        label="📥 Descargar Backup",
                        data=backup_data,
                        file_name=os.path.basename(backup_path),
                        mime="application/gzip",
                        use_container_width=True
                    )
                else:
                    st.error(message)
    
    # ===== PESTAÑA 2: RESTAURAR BACKUP =====
    with tab2:
        st.markdown("""
        <div class="card" style="background: #fff3cd;">
            <h4>⚠️ Importante - Restaurar Backup</h4>
            <p>Al restaurar un backup:</p>
            <ul>
                <li>Se creará automáticamente un backup de seguridad del estado actual</li>
                <li>Se reemplazará la base de datos actual con la del backup</li>
                <li>Todos los datos actuales se perderán si no se hace backup</li>
                <li>La aplicación se recargará automáticamente</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Opción 1: Subir archivo
        st.subheader("📂 Subir archivo de backup")
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo de backup (.gz)",
            type=['gz'],
            help="Archivos de backup generados por el sistema (formato .gz)"
        )
        
        if uploaded_file is not None:
            # Mostrar información del archivo
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📄 Archivo: {uploaded_file.name}")
            with col2:
                st.info(f"📦 Tamaño: {format_size(uploaded_file.size)}")
            
            # Botón de restauración
            if st.button("🔄 Restaurar este Backup", type="primary", use_container_width=True):
                with st.spinner("Restaurando backup... Esto puede tomar unos segundos"):
                    success, message = restore_backup(uploaded_file)
                
                if success:
                    st.success(message)
                    st.balloons()
                    st.warning("🔄 La aplicación se recargará en 3 segundos...")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(message)
        
        st.divider()
        
        # Opción 2: Seleccionar de backups existentes
        st.subheader("📋 O restaurar desde backups existentes")
        
        backups = list_backups()
        if backups:
            backup_options = {f"{b['name']} ({b['modified'].strftime('%Y-%m-%d %H:%M:%S')})": b['name'] for b in backups}
            selected_backup = st.selectbox(
                "Selecciona un backup existente",
                options=list(backup_options.keys())
            )
            
            if selected_backup:
                backup_name = backup_options[selected_backup]
                backup_info = next((b for b in backups if b['name'] == backup_name), None)
                
                if backup_info:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tamaño", format_size(backup_info['size']))
                    with col2:
                        st.metric("Fecha", backup_info['modified'].strftime('%Y-%m-%d'))
                    with col3:
                        st.metric("Hora", backup_info['modified'].strftime('%H:%M:%S'))
                    
                    if st.button("🔄 Restaurar este backup", key="restore_existing", use_container_width=True):
                        # Simular subida del archivo existente
                        with open(backup_info['path'], 'rb') as f:
                            file_content = f.read()
                        
                        class MockUploadedFile:
                            def __init__(self, name, content):
                                self.name = name
                                self.content = content
                                self.size = len(content)
                            
                            def read(self):
                                return self.content
                        
                        mock_file = MockUploadedFile(backup_info['name'], file_content)
                        
                        with st.spinner("Restaurando backup..."):
                            success, message = restore_backup(mock_file)
                        
                        if success:
                            st.success(message)
                            st.balloons()
                            st.warning("🔄 La aplicación se recargará en 3 segundos...")
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("📭 No hay backups disponibles para restaurar")
    
    # ===== PESTAÑA 3: LISTA DE BACKUPS =====
    with tab3:
        st.subheader("📋 Backups disponibles")
        
        backups = list_backups()
        
        if backups:
            # Crear DataFrame para mostrar
            backup_data = []
            for b in backups:
                backup_data.append({
                    "Nombre": b['name'],
                    "Fecha": b['modified'].strftime("%Y-%m-%d"),
                    "Hora": b['modified'].strftime("%H:%M:%S"),
                    "Tamaño": format_size(b['size']),
                    "Acciones": b['name']
                })
            
            for backup in backup_data:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{backup['Nombre']}**")
                    with col2:
                        st.write(backup['Fecha'])
                    with col3:
                        st.write(backup['Hora'])
                    with col4:
                        st.write(backup['Tamaño'])
                    with col5:
                        # Botón de descarga
                        backup_info = next((b for b in backups if b['name'] == backup['Nombre']), None)
                        if backup_info:
                            with open(backup_info['path'], 'rb') as f:
                                backup_data_file = f.read()
                            
                            st.download_button(
                                label="📥",
                                data=backup_data_file,
                                file_name=backup_info['name'],
                                mime="application/gzip",
                                key=f"download_{backup['Nombre']}",
                                help="Descargar backup"
                            )
                    
                    # Botón de eliminar en columna aparte
                    col_del1, col_del2, col_del3 = st.columns([1, 1, 8])
                    with col_del1:
                        if st.button("🗑️", key=f"del_{backup['Nombre']}", help="Eliminar backup"):
                            success, msg = delete_backup(backup['Nombre'])
                            if success:
                                st.success(msg)
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                    
                    st.divider()
            
            # Estadísticas de backups
            st.subheader("📊 Estadísticas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Backups", len(backups))
            with col2:
                total_size = sum(b['size'] for b in backups)
                st.metric("Espacio total", format_size(total_size))
            with col3:
                oldest = min(backups, key=lambda x: x['modified'])
                st.metric("Backup más antiguo", oldest['modified'].strftime('%Y-%m-%d'))
        
        else:
            st.info("📭 No hay backups disponibles. Crea tu primer backup en la pestaña 'Crear Backup'.")
            
            # Botón rápido para crear backup
            if st.button("🔄 Crear primer backup ahora", type="primary"):
                with st.spinner("Creando backup..."):
                    success, backup_path, message = create_backup()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)