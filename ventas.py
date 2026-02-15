import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from database import create_tables, get_connection, migrate_database, verify_database, DB_PATH
from auth import authenticate, create_user, get_all_users
import sqlite3
import time

# Configuración de página
st.set_page_config(
    "AIS Ventas PRO", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Verificar y crear base de datos al inicio
with st.spinner("🔄 Inicializando sistema..."):
    try:
        create_tables()
        migrate_database()
        verify_database()
        st.success(f"✅ Base de datos lista: {DB_PATH}")
    except Exception as e:
        st.error(f"❌ Error inicializando base de datos: {e}")
        st.stop()

def create_default_admin():
    """Crear admin por defecto si no hay usuarios"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        conn.close()
        
        if total_users == 0:
            create_user("admin", "admin123", "admin")
            st.success("✅ Usuario admin creado por defecto (admin/admin123)")
    except Exception as e:
        st.error(f"Error al crear admin por defecto: {e}")

# Crear admin por defecto si es necesario
create_default_admin()

# ============= LISTAS PERSONALIZADAS =============
CARGOS = [
    "Ais Droguería",
    "Ais Equipos Médicos", 
    "Ais Pasillos",
    "Ais Cajas"
]

DEPARTAMENTOS = [
    "Droguería",
    "Equipos Médicos",
    "Pasillos",
    "Cajas"
]

def load_css():
    """Cargar estilos CSS"""
    try:
        with open("styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# Inicializar session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard" if st.session_state.user else "Login"

# ---------------- FUNCIONES DE UTILIDAD ---------------- #
@st.cache_data(ttl=60)
def safe_dataframe(query, params=None):
    """Ejecutar query de forma segura y retornar DataFrame con cache"""
    try:
        conn = get_connection()
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()

def execute_query(query, params=None):
    """Ejecutar query SELECT y retornar resultados"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        results = cur.fetchall()
        return results
    except Exception as e:
        st.error(f"Error en consulta: {e}")
        return []
    finally:
        if conn:
            conn.close()

def execute_insert(query, params=None):
    """Ejecutar query INSERT/UPDATE/DELETE con commit"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_employee_info(user_id):
    """Obtener información del empleado por user_id"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, position, department, goal 
            FROM employees 
            WHERE user_id = ?
        """, (user_id,))
        emp = cur.fetchone()
        conn.close()
        return emp
    except Exception as e:
        return None

def get_badge_class(position):
    """Obtener la clase CSS para el badge según el cargo"""
    if "Droguería" in position:
        return "badge-cargo-drogueria"
    elif "Equipos" in position:
        return "badge-cargo-equipos"
    elif "Pasillos" in position:
        return "badge-cargo-pasillos"
    elif "Cajas" in position:
        return "badge-cargo-cajas"
    else:
        return "badge-cargo-drogueria"

# ---------------- LOGIN ---------------- #
def show_login():
    """Mostrar pantalla de login"""
    st.title("📊 AIS - Sistema Profesional de Ventas")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🔐 Iniciar Sesión")
            
            u = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            p = st.text_input("Contraseña", type="password", placeholder="********")
            
            if st.button("Ingresar", use_container_width=True, type="primary"):
                if u and p:
                    user = authenticate(u, p)
                    if user:
                        st.session_state.user = user
                        if user["role"] == "admin":
                            st.session_state.page = "Dashboard"
                        else:
                            emp_info = get_employee_info(user["id"])
                            if emp_info:
                                st.session_state.page = "Registrar ventas"
                            else:
                                st.warning("⚠️ Completa tu perfil de empleado antes de continuar")
                                st.session_state.page = "Mi perfil"
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                else:
                    st.warning("⚠️ Completa todos los campos")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- MENÚ ---------------- #
def show_menu():
    """Mostrar menú con botones"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #4f7cff; font-size: 32px; margin: 0;">AIS</h1>
            <p style="color: #666; font-size: 14px;">Sistema de Ventas</p>
        </div>
        """, unsafe_allow_html=True)
        
        emp_info = get_employee_info(st.session_state.user["id"])
        if emp_info:
            badge_class = get_badge_class(emp_info[2])
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: white; border-radius: 10px; margin-bottom: 15px;">
                <h4 style="margin: 5px 0;">{emp_info[1]}</h4>
                <p style="margin: 2px 0;">
                    <span class="badge {badge_class}">{emp_info[2] or 'Sin cargo'}</span>
                </p>
                <p style="margin: 2px 0;">
                    <span class="badge badge-depto">{emp_info[3] or 'Sin depto'}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        if st.session_state.user["role"] == "admin":
            menu_options = {
                "📊 Dashboard": "Dashboard",
                "🏆 Ranking": "Ranking",
                "🧑‍💼 Empleados": "Empleados",
                "👥 Usuarios": "Usuarios",
                "📊 Reportes": "Reportes"
            }
        else:
            menu_options = {
                "📝 Registrar": "Registrar ventas",
                "📈 Mi Desempeño": "Mi desempeño",
                "👤 Mi perfil": "Mi perfil",
                "🏆 Ranking": "Ranking"
            }
        
        for label, page in menu_options.items():
            if st.button(
                label, 
                key=f"menu_{page}",
                use_container_width=True,
                type="secondary" if st.session_state.page != page else "primary"
            ):
                st.session_state.page = page
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        #st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============= NUEVA PÁGINA DE EMPLEADOS (primero empleado) =============
# ... (todo el código anterior se mantiene igual hasta la página de empleados)

def page_empleados():
    st.title("🧑‍💼 Gestión de Empleados AIS")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Registrar empleado", 
        "👤 Asignar usuario", 
        "📋 Lista de empleados",
        "✏️ Editar/Eliminar"
    ])
    
    # ===== PESTAÑA 1: REGISTRAR EMPLEADO =====
    with tab1:
        st.markdown("""
        <div class="card" style="background: #e8f4fd;">
            <h4>📌 Paso 1: Registrar empleado</h4>
            <p>Primero registra los datos del empleado. Luego podrás asignarle un usuario.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("registrar_empleado_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nombre completo*", placeholder="Ej: Juan Pérez")
                position = st.selectbox("Cargo*", CARGOS)
            with col2:
                department = st.selectbox("Departamento*", DEPARTAMENTOS)
                goal = st.number_input("Meta mensual", value=300, min_value=1, step=50)
            
            submitted = st.form_submit_button("Registrar empleado", type="primary", use_container_width=True)
            
            if submitted:
                if name and position and department:
                    # Verificar si ya existe un empleado con ese nombre
                    check_query = "SELECT id FROM employees WHERE name = ?"
                    existing = execute_query(check_query, (name,))
                    
                    if existing:
                        st.warning(f"⚠️ Ya existe un empleado con el nombre '{name}'")
                    else:
                        insert_query = """
                            INSERT INTO employees (name, position, department, goal, user_id) 
                            VALUES (?,?,?,?, NULL)
                        """
                        success = execute_insert(insert_query, (name, position, department, goal))
                        
                        if success:
                            st.success(f"✅ Empleado '{name}' registrado exitosamente!")
                            st.info("👉 Ahora ve a la pestaña 'Asignar usuario' para crear su usuario.")
                            st.balloons()
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                else:
                    st.warning("⚠️ Completa todos los campos obligatorios (*)")
    
    # ===== PESTAÑA 2: ASIGNAR USUARIO =====
    with tab2:
        st.markdown("""
        <div class="card" style="background: #fff3cd;">
            <h4>📌 Paso 2: Asignar usuario a empleado</h4>
            <p>Crea un usuario y asígnalo a un empleado existente.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obtener empleados sin usuario asignado
        empleados_sin_usuario = execute_query("""
            SELECT id, name, position, department 
            FROM employees 
            WHERE user_id IS NULL
            ORDER BY name
        """)
        
        if not empleados_sin_usuario:
            st.info("✅ Todos los empleados ya tienen usuario asignado.")
            if st.button("➕ Registrar nuevo empleado", key="btn_nuevo_emp"):
                st.session_state.page = "Empleados"
                st.rerun()
        else:
            with st.form("asignar_usuario_form"):
                # Selector de empleado
                empleado_options = {f"{emp[1]} - {emp[2]}": emp[0] for emp in empleados_sin_usuario}
                selected_empleado = st.selectbox(
                    "Seleccionar empleado*", 
                    options=list(empleado_options.keys())
                )
                empleado_id = empleado_options[selected_empleado]
                
                st.divider()
                
                # Datos del usuario
                st.subheader("Datos del usuario")
                username = st.text_input("Nombre de usuario*", placeholder="ej: juan.perez")
                password = st.text_input("Contraseña*", type="password", placeholder="Mínimo 6 caracteres")
                confirm_password = st.text_input("Confirmar contraseña*", type="password")
                
                submitted = st.form_submit_button("Crear usuario y asignar", type="primary", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.warning("⚠️ Completa todos los campos obligatorios")
                    elif len(password) < 6:
                        st.warning("⚠️ La contraseña debe tener al menos 6 caracteres")
                    elif password != confirm_password:
                        st.warning("⚠️ Las contraseñas no coinciden")
                    else:
                        try:
                            # Crear usuario
                            user_result = create_user(username, password, "empleado")
                            
                            if user_result:
                                # Obtener el ID del usuario creado
                                user_id = user_result[0]
                                
                                # Asignar usuario al empleado
                                update_query = "UPDATE employees SET user_id = ? WHERE id = ?"
                                update_success = execute_insert(update_query, (user_id, empleado_id))
                                
                                if update_success:
                                    st.success(f"✅ Usuario '{username}' creado y asignado exitosamente!")
                                    st.balloons()
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")
                        except Exception as e:
                            st.error(f"❌ Error al crear usuario: {e}")
    
    # ===== PESTAÑA 3: LISTA DE EMPLEADOS =====
    with tab3:
        st.subheader("📋 Lista completa de empleados")
        
        df_emp = safe_dataframe("""
            SELECT 
                e.id,
                e.name as 'Nombre',
                e.position as 'Cargo',
                e.department as 'Departamento',
                e.goal as 'Meta',
                CASE 
                    WHEN u.username IS NOT NULL THEN u.username 
                    ELSE '⏳ Pendiente' 
                END as 'Usuario',
                CASE 
                    WHEN u.username IS NOT NULL THEN '✅ Asignado'
                    ELSE '❌ Sin usuario'
                END as 'Estado'
            FROM employees e
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY 
                CASE WHEN u.username IS NULL THEN 0 ELSE 1 END,
                e.department, 
                e.name
        """)
        
        if not df_emp.empty:
            # Colorear filas según estado
            def color_estado(val):
                if '✅' in val:
                    return 'background-color: #d4edda'
                elif '❌' in val:
                    return 'background-color: #f8d7da'
                return ''
            
            styled_df = df_emp.style.applymap(color_estado, subset=['Estado'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total empleados", len(df_emp))
            with col2:
                con_usuario = len(df_emp[df_emp['Estado'] == '✅ Asignado'])
                st.metric("Con usuario", con_usuario)
            with col3:
                sin_usuario = len(df_emp[df_emp['Estado'] == '❌ Sin usuario'])
                st.metric("Sin usuario", sin_usuario)
            
            # Resumen por departamento
            st.subheader("📊 Resumen por departamento")
            depto_resumen = df_emp.groupby('Departamento').agg({
                'Nombre': 'count'
            }).rename(columns={'Nombre': 'Empleados'}).reset_index()
            st.dataframe(depto_resumen, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No hay empleados registrados")
    
    # ===== PESTAÑA 4: EDITAR/ELIMINAR EMPLEADOS =====
    with tab4:
        st.subheader("✏️ Editar o Eliminar Empleados")
        
        # Obtener todos los empleados
        todos_empleados = execute_query("""
            SELECT 
                e.id, 
                e.name, 
                e.position, 
                e.department, 
                e.goal,
                u.username
            FROM employees e
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.name
        """)
        
        if not todos_empleados:
            st.info("📭 No hay empleados para editar")
        else:
            # Crear opciones para el selector
            empleado_options = {}
            for emp in todos_empleados:
                usuario_info = f" (Usuario: {emp[5]})" if emp[5] else " (Sin usuario)"
                display_text = f"{emp[1]} - {emp[2]} - {emp[3]}{usuario_info}"
                empleado_options[display_text] = emp[0]
            
            selected_display = st.selectbox(
                "Seleccionar empleado",
                options=list(empleado_options.keys()),
                key="select_empleado_editar"
            )
            empleado_id = empleado_options[selected_display]
            
            # Obtener datos del empleado seleccionado
            empleado_data = next((emp for emp in todos_empleados if emp[0] == empleado_id), None)
            
            if empleado_data:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### 📝 Editar información")
                    with st.form("editar_empleado_form"):
                        new_name = st.text_input("Nombre", value=empleado_data[1])
                        new_position = st.selectbox("Cargo", CARGOS, 
                                                   index=CARGOS.index(empleado_data[2]) if empleado_data[2] in CARGOS else 0)
                        new_department = st.selectbox("Departamento", DEPARTAMENTOS,
                                                     index=DEPARTAMENTOS.index(empleado_data[3]) if empleado_data[3] in DEPARTAMENTOS else 0)
                        new_goal = st.number_input("Meta mensual", value=empleado_data[4], min_value=1, step=50)
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            submitted_edit = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
                        with col_edit2:
                            submitted_delete = st.form_submit_button("🗑️ Eliminar empleado", type="secondary", use_container_width=True)
                        
                        if submitted_edit:
                            if new_name and new_position and new_department:
                                update_query = """
                                    UPDATE employees 
                                    SET name = ?, position = ?, department = ?, goal = ?
                                    WHERE id = ?
                                """
                                success = execute_insert(update_query, (new_name, new_position, new_department, new_goal, empleado_id))
                                
                                if success:
                                    st.success("✅ Empleado actualizado exitosamente!")
                                    st.balloons()
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.warning("⚠️ Completa todos los campos")
                        
                        if submitted_delete:
                            # Verificar si tiene ventas antes de eliminar
                            ventas = execute_query("SELECT COUNT(*) FROM sales WHERE employee_id = ?", (empleado_id,))
                            tiene_ventas = ventas[0][0] > 0 if ventas else False
                            
                            if tiene_ventas:
                                st.error("❌ No se puede eliminar: el empleado tiene ventas registradas")
                            else:
                                # Confirmar eliminación
                                st.session_state.confirmar_eliminar = empleado_id
                    
                    # Mostrar confirmación fuera del formulario
                    if 'confirmar_eliminar' in st.session_state and st.session_state.confirmar_eliminar == empleado_id:
                        st.warning("⚠️ ¿Estás seguro de eliminar este empleado?")
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button("✅ Sí, eliminar", key="confirm_si"):
                                delete_query = "DELETE FROM employees WHERE id = ?"
                                success = execute_insert(delete_query, (empleado_id,))
                                
                                if success:
                                    st.success("✅ Empleado eliminado exitosamente!")
                                    del st.session_state.confirmar_eliminar
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                        with col_confirm2:
                            if st.button("❌ No, cancelar", key="confirm_no"):
                                del st.session_state.confirmar_eliminar
                                st.rerun()
                
                with col2:
                    st.markdown("### ℹ️ Información")
                    
                    # Obtener conteo de ventas
                    ventas_count = execute_query("SELECT COUNT(*) FROM sales WHERE employee_id = ?", (empleado_id,))
                    total_ventas = ventas_count[0][0] if ventas_count else 0
                    
                    st.markdown(f"""
                    **ID:** {empleado_data[0]}
                    
                    **Usuario:** {empleado_data[5] or 'No asignado'}
                    
                    **Ventas:** {total_ventas}
                    """)
                    
                    if empleado_data[5]:
                        st.info("🔒 El usuario asociado no se puede modificar aquí")
                    else:
                        st.info("👤 Este empleado no tiene usuario asignado")

# ============= PÁGINA DE USUARIOS (simplificada) =============
def page_usuarios():
    st.title("👤 Gestión de Usuarios AIS")
    
    tab1, tab2, tab3 = st.tabs([
        "📋 Lista de usuarios", 
        "🔑 Cambiar contraseña",
        "✏️ Editar/Eliminar usuarios"
    ])
    
    with tab1:
        users = get_all_users()
        if users:
            df_users = pd.DataFrame(users, columns=["ID", "Usuario", "Rol", "Empleado", "Departamento"])
            df_users['Empleado'] = df_users['Empleado'].fillna('—')
            df_users['Departamento'] = df_users['Departamento'].fillna('—')
            
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total usuarios", len(df_users))
            with col2:
                st.metric("Administradores", len(df_users[df_users['Rol'] == 'admin']))
            with col3:
                st.metric("Empleados", len(df_users[df_users['Rol'] == 'empleado']))
        else:
            st.info("No hay usuarios registrados")
    
    with tab2:
        st.subheader("Cambiar contraseña de usuario")
        
        users = get_all_users()
        if users:
            user_options = {f"{u[1]} ({u[3] or 'Sin empleado'})": u[0] for u in users}
            selected_user = st.selectbox("Seleccionar usuario", options=list(user_options.keys()), key="cambiar_pass_select")
            user_id = user_options[selected_user]
            
            new_pass = st.text_input("Nueva contraseña", type="password", placeholder="Mínimo 6 caracteres")
            confirm_pass = st.text_input("Confirmar contraseña", type="password")
            
            if st.button("Cambiar contraseña", type="primary"):
                if new_pass and len(new_pass) >= 6:
                    if new_pass == confirm_pass:
                        from auth import hash_password
                        success = execute_insert(
                            "UPDATE users SET password = ? WHERE id = ?",
                            (hash_password(new_pass), user_id)
                        )
                        if success:
                            st.success("✅ Contraseña actualizada!")
                            st.balloons()
                    else:
                        st.error("❌ Las contraseñas no coinciden")
                else:
                    st.warning("⚠️ La contraseña debe tener al menos 6 caracteres")
        else:
            st.info("No hay usuarios para modificar")
    
    # ===== NUEVA PESTAÑA: EDITAR/ELIMINAR USUARIOS =====
    with tab3:
        st.subheader("✏️ Editar o Eliminar Usuarios")
        
        st.markdown("""
        <div class="card" style="background: #fff3cd;">
            <h4>⚠️ Importante</h4>
            <p>Los usuarios que tienen un empleado asociado no se pueden eliminar directamente.</p>
            <p>Primero debes desasociar el empleado o eliminarlo.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obtener todos los usuarios
        todos_usuarios = execute_query("""
            SELECT 
                u.id, 
                u.username, 
                u.role,
                e.name as empleado_nombre,
                e.id as empleado_id
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            ORDER BY u.username
        """)
        
        if not todos_usuarios:
            st.info("📭 No hay usuarios para editar")
        else:
            # Crear opciones para el selector
            usuario_options = {}
            for user in todos_usuarios:
                empleado_info = f" (Empleado: {user[3]})" if user[3] else " (Sin empleado)"
                display_text = f"{user[1]} - {user[2]}{empleado_info}"
                usuario_options[display_text] = user[0]
            
            selected_display = st.selectbox(
                "Seleccionar usuario",
                options=list(usuario_options.keys()),
                key="select_usuario_editar"
            )
            usuario_id = usuario_options[selected_display]
            
            # Obtener datos del usuario seleccionado
            usuario_data = next((user for user in todos_usuarios if user[0] == usuario_id), None)
            
            if usuario_data:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### 📝 Editar información")
                    
                    # No permitir editar admin por defecto
                    if usuario_data[1] == "admin":
                        st.warning("⚠️ El usuario 'admin' no se puede modificar")
                    else:
                        with st.form("editar_usuario_form"):
                            new_username = st.text_input("Nombre de usuario", value=usuario_data[1])
                            new_role = st.selectbox("Rol", ["empleado", "admin"], 
                                                  index=0 if usuario_data[2] == "empleado" else 1)
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                submitted_edit = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
                            with col_edit2:
                                submitted_delete = st.form_submit_button("🗑️ Eliminar usuario", type="secondary", use_container_width=True)
                            
                            if submitted_edit:
                                if new_username:
                                    # Verificar si el nuevo username ya existe (y no es el mismo usuario)
                                    check_query = "SELECT id FROM users WHERE username = ? AND id != ?"
                                    check_result = execute_query(check_query, (new_username, usuario_id))
                                    
                                    if check_result:
                                        st.warning(f"⚠️ El nombre de usuario '{new_username}' ya existe")
                                    else:
                                        update_query = "UPDATE users SET username = ?, role = ? WHERE id = ?"
                                        success = execute_insert(update_query, (new_username, new_role, usuario_id))
                                        
                                        if success:
                                            st.success("✅ Usuario actualizado exitosamente!")
                                            st.balloons()
                                            st.cache_data.clear()
                                            time.sleep(1)
                                            st.rerun()
                                else:
                                    st.warning("⚠️ El nombre de usuario no puede estar vacío")
                            
                            if submitted_delete:
                                # Verificar si el usuario tiene empleado asociado
                                if usuario_data[3]:  # Tiene empleado
                                    st.error("❌ No se puede eliminar: el usuario tiene un empleado asociado")
                                else:
                                    # Confirmar eliminación
                                    st.session_state.confirmar_eliminar_usuario = usuario_id
                        
                        # Mostrar confirmación fuera del formulario
                        if 'confirmar_eliminar_usuario' in st.session_state and st.session_state.confirmar_eliminar_usuario == usuario_id:
                            st.warning(f"⚠️ ¿Estás seguro de eliminar el usuario '{usuario_data[1]}'?")
                            col_confirm1, col_confirm2 = st.columns(2)
                            with col_confirm1:
                                if st.button("✅ Sí, eliminar", key="confirm_si_usuario"):
                                    delete_query = "DELETE FROM users WHERE id = ?"
                                    success = execute_insert(delete_query, (usuario_id,))
                                    
                                    if success:
                                        st.success("✅ Usuario eliminado exitosamente!")
                                        del st.session_state.confirmar_eliminar_usuario
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
                            with col_confirm2:
                                if st.button("❌ No, cancelar", key="confirm_no_usuario"):
                                    del st.session_state.confirmar_eliminar_usuario
                                    st.rerun()
                
                with col2:
                    st.markdown("### ℹ️ Información")
                    
                    st.markdown(f"""
                    **ID:** {usuario_data[0]}
                    
                    **Rol:** {usuario_data[2]}
                    
                    **Empleado:** {usuario_data[3] or 'No asociado'}
                    """)
                    
                    if usuario_data[3]:
                        st.info("🔒 Este usuario tiene un empleado asociado")
                    else:
                        st.info("👤 Usuario sin empleado")

# Las demás páginas se mantienen igual...
def page_dashboard():
    st.title("📊 Dashboard Ejecutivo AIS")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())
    with col3:
        depto_filtro = st.multiselect("Departamento", DEPARTAMENTOS, default=DEPARTAMENTOS)
    
    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()
    
    query = """
        SELECT s.*, e.name, e.position, e.department 
        FROM sales s
        JOIN employees e ON s.employee_id = e.id
        WHERE date BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    
    if depto_filtro:
        placeholders = ','.join(['?'] * len(depto_filtro))
        query += f" AND e.department IN ({placeholders})"
        params.extend(depto_filtro)
    
    query += " ORDER BY date DESC"
    
    with st.spinner("Cargando datos..."):
        df = safe_dataframe(query, params)
    
    if df.empty:
        st.info("ℹ️ No hay ventas en el período seleccionado")
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unidades", f"{int(df['total'].sum()):,}")
    with col2:
        st.metric("Autoliquidable", f"{int(df['autoliquidable'].sum()):,}")
    with col3:
        st.metric("Oferta Semana", f"{int(df['oferta'].sum()):,}")
    with col4:
        st.metric("Marca Propia", f"{int(df['marca'].sum()):,}")
    
    tab1, tab2, tab3 = st.tabs(["📈 Evolución", "📊 Distribución", "👥 Por empleado"])
    
    with tab1:
        fig = px.line(df, x="date", y="total", color="department",
                     title="📈 Evolución diaria de ventas por departamento")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        dist_df = df.groupby('department')[['autoliquidable','oferta','marca','adicional']].sum().reset_index()
        dist_df_melted = dist_df.melt(id_vars=['department'], var_name='Tipo', value_name='Cantidad')
        fig2 = px.bar(dist_df_melted, x='department', y='Cantidad', color='Tipo',
                     title="Distribución por departamento y tipo",
                     barmode='stack')
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        emp_df = df.groupby(['name', 'department']).agg({
            'total': 'sum'
        }).reset_index()
        
        fig3 = px.bar(emp_df, x='name', y='total', color='department',
                     title="Ventas por empleado",
                     barmode='group')
        st.plotly_chart(fig3, use_container_width=True)

def page_ranking():
    st.title("🏆 Ranking de Ventas AIS")
    
    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox("Período", ["Este mes", "Este trimestre", "Este año", "Todo"])
    with col2:
        depto_filtro = st.selectbox("Departamento", ["Todos"] + DEPARTAMENTOS)
    
    if st.button("🔄 Actualizar ranking"):
        st.cache_data.clear()
        st.rerun()
    
    hoy = date.today()
    if periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        trimestre_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
        cond_fecha = f"AND date >= '{trimestre_inicio}'"
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
        cond_fecha = f"AND date >= '{fecha_inicio}'"
    else:
        cond_fecha = ""
    
    query = f"""
    SELECT 
        e.name as Empleado,
        e.position as Cargo,
        e.department as Departamento,
        COALESCE(SUM(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Total,
        COUNT(s.id) as Registros,
        COALESCE(AVG(s.autoliquidable + s.oferta + s.marca + s.adicional), 0) as Promedio,
        e.goal as Meta
    FROM employees e
    LEFT JOIN sales s ON e.id = s.employee_id {cond_fecha}
    """
    
    if depto_filtro != "Todos":
        query += f" WHERE e.department = '{depto_filtro}'"
    
    query += " GROUP BY e.id ORDER BY Total DESC"
    
    df = safe_dataframe(query)
    
    if df.empty:
        st.info("ℹ️ No hay datos aún")
        return
    
    df['Cumplimiento'] = (df['Total'] / df['Meta'] * 100).round(1)
    
    st.subheader("📋 Ranking General")
    df_display = df.copy()
    df_display["Posición"] = range(1, len(df) + 1)
    df_display["Total"] = df_display["Total"].apply(lambda x: f"{int(x):,}")
    df_display["Promedio"] = df_display["Promedio"].apply(lambda x: f"{int(x):,}")
    df_display["Cumplimiento"] = df_display["Cumplimiento"].apply(lambda x: f"{x}%")
    
    st.dataframe(
        df_display[["Posición", "Empleado", "Cargo", "Departamento", "Total", "Registros", "Cumplimiento"]],
        use_container_width=True,
        hide_index=True
    )

def page_registrar_ventas():
    st.title("📝 Registro Diario de Ventas - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado. Contacta al administrador.")
        return
    
    badge_class = get_badge_class(emp_info[2])
    
    st.markdown(f"""
    <div class="card">
        <h4>Registrando para: {emp_info[1]}</h4>
        <p>
            <span class="badge {badge_class}">{emp_info[2]}</span>
            <span class="badge badge-depto">{emp_info[3]}</span>
            🎯 Meta mensual: {emp_info[4]} unidades
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar registro hoy
    result = execute_query(
        "SELECT COUNT(*) FROM sales WHERE employee_id = ? AND date = ?",
        (emp_info[0], str(date.today()))
    )
    ya_registro_hoy = result[0][0] > 0 if result else False
    
    if ya_registro_hoy:
        st.warning("⚠️ Ya has registrado ventas hoy. ¿Deseas agregar más?")
    
    with st.form("ventas_form"):
        st.subheader("Ingresa las ventas del día")
        
        col1, col2 = st.columns(2)
        with col1:
            aut = st.number_input("📦 Autoliquidable", min_value=0, step=1, value=0)
            ma = st.number_input("🏷 Marca Propia", min_value=0, step=1, value=0)
        
        with col2:
            of = st.number_input("🔥 Oferta Semana", min_value=0, step=1, value=0)
            ad = st.number_input("➕ Producto Adicional", min_value=0, step=1, value=0)
        
        total = aut + of + ma + ad
        
        # Progreso mensual
        mes_actual = date.today().strftime("%Y-%m")
        result = execute_query(
            "SELECT SUM(autoliquidable + oferta + marca + adicional) FROM sales WHERE employee_id = ? AND date LIKE ?",
            (emp_info[0], f"{mes_actual}%")
        )
        ventas_mes = result[0][0] or 0 if result else 0
        
        progreso = ((ventas_mes + total) / emp_info[4] * 100) if emp_info[4] > 0 else 0
        
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <p><strong>Total del día:</strong> {total} unidades</p>
            <p><strong>Progreso mensual:</strong> {ventas_mes + total} / {emp_info[4]} unidades ({progreso:.1f}%)</p>
            <div class="progress">
                <div class="progress-bar" style="width: {min(progreso, 100)}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("💾 Guardar ventas", use_container_width=True)
        
        if submitted:
            if total > 0:
                success = execute_insert("""
                    INSERT INTO sales (employee_id, date, autoliquidable, oferta, marca, adicional)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (emp_info[0], str(date.today()), aut, of, ma, ad))
                
                if success:
                    st.success("✅ Venta registrada exitosamente!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("⚠️ Debes ingresar al menos una unidad")

def page_mi_desempeno():
    st.title("📊 Mi Desempeño Personal - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if not emp_info:
        st.error("❌ No tienes un empleado asociado")
        return
    
    periodo = st.selectbox(
        "Período",
        ["Esta semana", "Este mes", "Este trimestre", "Este año", "Todo"]
    )
    
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
    
    hoy = date.today()
    if periodo == "Esta semana":
        fecha_inicio = hoy - pd.Timedelta(days=hoy.weekday())
    elif periodo == "Este mes":
        fecha_inicio = hoy.replace(day=1)
    elif periodo == "Este trimestre":
        mes_actual = hoy.month
        trimestre_inicio = hoy.replace(month=((mes_actual-1)//3)*3+1, day=1)
        fecha_inicio = trimestre_inicio
    elif periodo == "Este año":
        fecha_inicio = hoy.replace(month=1, day=1)
    else:
        fecha_inicio = date(2000, 1, 1)
    
    df = safe_dataframe("""
        SELECT date, autoliquidable, oferta, marca, adicional
        FROM sales 
        WHERE employee_id = ? AND date >= ?
        ORDER BY date
    """, (emp_info[0], fecha_inicio))
    
    if df.empty:
        st.info(f"ℹ️ No hay registros en {periodo.lower()}")
        return
    
    df["total"] = df[['autoliquidable','oferta','marca','adicional']].sum(axis=1)
    df["date"] = pd.to_datetime(df["date"])
    
    total_periodo = int(df["total"].sum())
    promedio = int(df["total"].mean())
    mejor_dia = int(df["total"].max())
    progreso_meta = (total_periodo / emp_info[4] * 100) if emp_info[4] > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total período", f"{total_periodo:,}")
    with col2:
        st.metric("Promedio diario", f"{promedio:,}")
    with col3:
        st.metric("Mejor día", f"{mejor_dia:,}")
    with col4:
        st.metric("Progreso meta", f"{progreso_meta:.1f}%")
    
    fig = px.line(df, x="date", y="total", 
                 title=f"📈 Evolución personal - {periodo}",
                 markers=True)
    st.plotly_chart(fig, use_container_width=True)

def page_mi_perfil():
    st.title("👤 Mi Perfil - AIS")
    
    emp_info = get_employee_info(st.session_state.user["id"])
    
    if emp_info:
        badge_class = get_badge_class(emp_info[2])
        st.markdown(f"""
        <div class="card" style="text-align: center;">
            <h2>{emp_info[1]}</h2>
            <p>
                <span class="badge {badge_class}" style="font-size: 16px;">{emp_info[2]}</span>
                <span class="badge badge-depto" style="font-size: 16px;">{emp_info[3]}</span>
            </p>
            <p class="metric">🎯 Meta: {emp_info[4]} unidades/mes</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No tienes un perfil de empleado configurado. Contacta al administrador.")

def page_reportes():
    st.title("📊 Reportes Avanzados AIS")
    
    tipo_reporte = st.selectbox(
        "Tipo de reporte",
        ["Ventas por departamento", "Ventas por cargo"]
    )
    
    if st.button("🔄 Generar reporte"):
        st.cache_data.clear()
        st.rerun()
    
    if tipo_reporte == "Ventas por departamento":
        df = safe_dataframe("""
            SELECT 
                e.department,
                SUM(s.autoliquidable + s.oferta + s.marca + s.adicional) as total,
                AVG(s.autoliquidable + s.oferta + s.marca + s.adicional) as promedio,
                COUNT(DISTINCT e.id) as empleados,
                COUNT(s.id) as transacciones
            FROM sales s
            JOIN employees e ON s.employee_id = e.id
            GROUP BY e.department
            ORDER BY total DESC
        """)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            fig = px.bar(df, x='department', y='total',
                        title="Ventas por departamento",
                        color='department')
            st.plotly_chart(fig, use_container_width=True)

# ---------------- CONTROL PRINCIPAL ---------------- #
def main():
    if not st.session_state.user:
        show_login()
    else:
        show_menu()
        
        pages = {
            "Dashboard": page_dashboard,
            "Ranking": page_ranking,
            "Empleados": page_empleados,
            "Usuarios": page_usuarios,
            "Reportes": page_reportes,
            "Registrar ventas": page_registrar_ventas,
            "Mi desempeño": page_mi_desempeno,
            "Mi perfil": page_mi_perfil
        }
        
        if st.session_state.page in pages:
            pages[st.session_state.page]()
        else:
            page_dashboard() if st.session_state.user["role"] == "admin" else page_registrar_ventas()

if __name__ == "__main__":
    main()