import sqlite3
import json
import os
import zipfile
from datetime import datetime
import shutil
from pathlib import Path
import streamlit as st
import pandas as pd
from database import get_connection, DB_PATH

class BackupManager:
    def __init__(self):
        self.backup_dir = Path(__file__).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, include_files=True):
        """
        Crear backup completo de la base de datos y archivos
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_locatel_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Crear directorio temporal para el backup
            temp_dir = backup_path
            temp_dir.mkdir(exist_ok=True)
            
            # 1. Backup de la base de datos SQLite
            db_backup_path = temp_dir / "database.db"
            self._backup_database(db_backup_path)
            
            # 2. Exportar datos a JSON (formato legible)
            json_backup_path = temp_dir / "data_export.json"
            self._export_to_json(json_backup_path)
            
            # 3. Exportar a CSV (para fácil importación en Excel)
            csv_dir = temp_dir / "csv_exports"
            csv_dir.mkdir(exist_ok=True)
            self._export_to_csv(csv_dir)
            
            # 4. Crear archivo de metadatos
            metadata = {
                "fecha_backup": datetime.now().isoformat(),
                "version_app": "2.0.0",
                "tablas_incluidas": ["users", "employees", "sales"],
                "incluye_archivos": include_files
            }
            
            with open(temp_dir / "metadata.json", "w", encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 5. Comprimir todo en un ZIP
            zip_path = self.backup_dir / f"{backup_name}.zip"
            self._create_zip(temp_dir, zip_path)
            
            # 6. Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            return {
                "success": True,
                "path": zip_path,
                "name": f"{backup_name}.zip",
                "size": self._get_file_size(zip_path),
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _backup_database(self, dest_path):
        """Hacer backup de la base de datos SQLite"""
        try:
            # Hacer backup usando el módulo de sqlite3
            source = sqlite3.connect(str(DB_PATH))
            dest = sqlite3.connect(str(dest_path))
            source.backup(dest)
            source.close()
            dest.close()
        except Exception as e:
            raise Exception(f"Error en backup de base de datos: {e}")
    
    def _export_to_json(self, json_path):
        """Exportar todos los datos a JSON"""
        data = {}
        conn = get_connection()
        
        try:
            # Exportar usuarios
            users_df = pd.read_sql("SELECT * FROM users", conn)
            data['users'] = json.loads(users_df.to_json(orient='records', date_format='iso', force_ascii=False))
            
            # Exportar empleados
            employees_df = pd.read_sql("SELECT * FROM employees", conn)
            data['employees'] = json.loads(employees_df.to_json(orient='records', date_format='iso', force_ascii=False))
            
            # Exportar ventas
            sales_df = pd.read_sql("SELECT * FROM sales", conn)
            data['sales'] = json.loads(sales_df.to_json(orient='records', date_format='iso', force_ascii=False))
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        finally:
            conn.close()
    
    def _export_to_csv(self, csv_dir):
        """Exportar datos a CSV"""
        conn = get_connection()
        
        try:
            # Exportar cada tabla a CSV
            tables = ['users', 'employees', 'sales']
            for table in tables:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                csv_path = csv_dir / f"{table}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8')
                
        finally:
            conn.close()
    
    def _create_zip(self, source_dir, zip_path):
        """Comprimir directorio en ZIP"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    
    def _get_file_size(self, file_path):
        """Obtener tamaño del archivo en formato legible"""
        size_bytes = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def list_backups(self):
        """Listar todos los backups disponibles"""
        backups = []
        for file in sorted(self.backup_dir.glob("*.zip"), reverse=True):
            stats = file.stat()
            backups.append({
                "name": file.name,
                "size": self._get_file_size(file),
                "date": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "path": file
            })
        return backups
    
    def restore_backup(self, zip_path, restore_type="database"):
        """
        Restaurar desde backup
        restore_type: "database" (solo BD), "full" (todo)
        """
        try:
            # Extraer ZIP
            extract_dir = self.backup_dir / "temp_restore"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir()
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            if restore_type == "database":
                # Restaurar solo la base de datos
                db_file = extract_dir / "database.db"
                if db_file.exists():
                    # Hacer backup automático antes de restaurar
                    pre_restore_backup = self.create_backup()
                    
                    # Reemplazar base de datos actual
                    shutil.copy2(db_file, DB_PATH)
                    
                    shutil.rmtree(extract_dir)
                    return {
                        "success": True,
                        "message": "Base de datos restaurada exitosamente",
                        "pre_restore_backup": pre_restore_backup.get("name")
                    }
                else:
                    return {"success": False, "error": "No se encontró archivo de base de datos"}
            
            elif restore_type == "full":
                # Restaurar todo (futura implementación)
                pass
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
    
    def delete_backup(self, backup_name):
        """Eliminar un backup"""
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
    
    def get_backup_stats(self):
        """Obtener estadísticas de backups"""
        backups = self.list_backups()
        total_size = sum([b['path'].stat().st_size for b in backups])
        
        return {
            "total_backups": len(backups),
            "total_size": self._get_file_size(total_size),
            "latest_backup": backups[0] if backups else None,
            "backup_dir": str(self.backup_dir)
        }

def render_backup_page():
    """Renderizar página de backups en Streamlit"""
    st.title("💾 Gestión de Backups")
    
    # Inicializar manager
    if 'backup_manager' not in st.session_state:
        st.session_state.backup_manager = BackupManager()
    
    manager = st.session_state.backup_manager
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs([
        "📀 Crear Backup",
        "📋 Listar Backups",
        "⚙️ Configuración"
    ])
    
    # ===== TAB 1: CREAR BACKUP =====
    with tab1:
        st.markdown("""
        <div class="card">
            <h4>Crear nuevo backup</h4>
            <p>Genera una copia de seguridad completa de todos los datos del sistema.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📦 Incluir en el backup:")
            include_files = st.checkbox("Incluir archivos adjuntos", value=True, 
                                      help="Incluye imágenes y documentos adicionales")
            include_csv = st.checkbox("Incluir exportación CSV", value=True,
                                     help="Exporta también a formato CSV para Excel")
        
        with col2:
            st.markdown("### ℹ️ Información:")
            st.info("""
            **El backup incluirá:**
            - Base de datos completa
            - Usuarios y empleados
            - Historial de ventas
            - Metadatos del sistema
            """)
        
        if st.button("🚀 Crear Backup Ahora", type="primary", use_container_width=True):
            with st.spinner("🔄 Creando backup... Esto puede tomar unos segundos"):
                result = manager.create_backup(include_files=include_files)
                
                if result["success"]:
                    st.success(f"✅ Backup creado exitosamente!")
                    st.balloons()
                    
                    # Mostrar detalles
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Nombre", result["name"])
                    with col2:
                        st.metric("Tamaño", result["size"])
                    with col3:
                        st.metric("Fecha", datetime.now().strftime("%H:%M:%S"))
                    
                    # Botón para descargar
                    with open(result["path"], "rb") as fp:
                        st.download_button(
                            label="📥 Descargar Backup",
                            data=fp,
                            file_name=result["name"],
                            mime="application/zip",
                            use_container_width=True
                        )
                else:
                    st.error(f"❌ Error creando backup: {result['error']}")
    
    # ===== TAB 2: LISTAR BACKUPS =====
    with tab2:
        st.markdown("### 📋 Backups disponibles")
        
        backups = manager.list_backups()
        
        if not backups:
            st.info("📭 No hay backups disponibles. Crea uno en la pestaña anterior.")
        else:
            # Estadísticas
            stats = manager.get_backup_stats()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Backups", stats["total_backups"])
            with col2:
                st.metric("Espacio total", stats["total_size"])
            with col3:
                if stats["latest_backup"]:
                    st.metric("Último backup", stats["latest_backup"]["date"])
            
            st.divider()
            
            # Tabla de backups
            for backup in backups:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{backup['name']}**")
                    with col2:
                        st.markdown(f"`{backup['size']}`")
                    with col3:
                        st.markdown(f"📅 {backup['date']}")
                    with col4:
                        # Botón de restaurar
                        if st.button("🔄 Restaurar", key=f"restore_{backup['name']}"):
                            st.session_state.confirm_restore = backup['name']
                    
                    with col5:
                        # Botón de eliminar
                        if st.button("🗑️ Eliminar", key=f"delete_{backup['name']}"):
                            st.session_state.confirm_delete = backup['name']
                    
                    # Botón de descargar
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 1, 1])
                    with col4:
                        with open(backup['path'], "rb") as fp:
                            st.download_button(
                                label="📥",
                                data=fp,
                                file_name=backup['name'],
                                mime="application/zip",
                                key=f"download_{backup['name']}"
                            )
                    
                    st.divider()
            
            # Confirmación de restauración
            if 'confirm_restore' in st.session_state:
                backup_name = st.session_state.confirm_restore
                st.warning(f"⚠️ ¿Estás seguro de restaurar el backup '{backup_name}'?")
                st.error("⚠️ Esta acción sobreescribirá TODOS los datos actuales!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Sí, restaurar", key="confirm_restore_yes"):
                        backup_path = manager.backup_dir / backup_name
                        result = manager.restore_backup(backup_path, "database")
                        
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                            if result.get("pre_restore_backup"):
                                st.info(f"💾 Backup automático creado: {result['pre_restore_backup']}")
                            del st.session_state.confirm_restore
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result['error']}")
                
                with col2:
                    if st.button("❌ No, cancelar", key="confirm_restore_no"):
                        del st.session_state.confirm_restore
                        st.rerun()
            
            # Confirmación de eliminación
            if 'confirm_delete' in st.session_state:
                backup_name = st.session_state.confirm_delete
                st.warning(f"⚠️ ¿Estás seguro de eliminar el backup '{backup_name}'?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Sí, eliminar", key="confirm_delete_yes"):
                        if manager.delete_backup(backup_name):
                            st.success("✅ Backup eliminado!")
                            del st.session_state.confirm_delete
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar")
                
                with col2:
                    if st.button("❌ No, cancelar", key="confirm_delete_no"):
                        del st.session_state.confirm_delete
                        st.rerun()
    
    # ===== TAB 3: CONFIGURACIÓN =====
    with tab3:
        st.markdown("### ⚙️ Configuración de Backups")
        
        stats = manager.get_backup_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📁 Directorio de backups")
            st.code(stats['backup_dir'])
            
            if st.button("📂 Abrir carpeta de backups"):
                # Abrir carpeta en el explorador de archivos
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(str(manager.backup_dir))
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(manager.backup_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(manager.backup_dir)])
        
        with col2:
            st.markdown("#### 🔧 Opciones avanzadas")
            
            # Backup automático
            auto_backup = st.checkbox("Activar backups automáticos", value=False,
                                     help="Crear backups automáticos cada cierto tiempo")
            
            if auto_backup:
                frecuencia = st.selectbox("Frecuencia", ["Diario", "Semanal", "Mensual"])
                mantener = st.number_input("Mantener últimos N backups", min_value=1, value=10)
                
                if st.button("💾 Guardar configuración"):
                    st.success("✅ Configuración guardada!")
            
            # Limpiar backups antiguos
            st.divider()
            st.markdown("#### 🧹 Limpiar backups antiguos")
            
            dias = st.number_input("Eliminar backups más antiguos de (días)", min_value=1, value=30)
            
            if st.button("🗑️ Limpiar backups antiguos", type="secondary"):
                # Implementar limpieza
                st.warning(f"¿Eliminar backups anteriores a {dias} días?")