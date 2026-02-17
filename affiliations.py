import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
from database import get_connection
import time

# Colores personalizados
COLORS = {
    'primary': '#4f7cff',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'purple': '#8b5cf6',
    'pink': '#ec4899'
}

def get_affiliation_types():
    """Obtener tipos de afiliación activos"""
    conn = get_connection()
    try:
        # Verificar si la tabla existe
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affiliation_types'")
        if not cur.fetchone():
            # Si no existe, crear DataFrame vacío
            return pd.DataFrame(columns=['id', 'name', 'description', 'points_value'])
        
        df = pd.read_sql("""
            SELECT id, name, description, points_value 
            FROM affiliation_types 
            WHERE is_active = 1 
            ORDER BY name
        """, conn)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['id', 'name', 'description', 'points_value'])
    finally:
        conn.close()

def get_employee_affiliation_goal(employee_id, year=None, month=None):
    """Obtener meta de afiliaciones para un empleado en un período específico"""
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month
    
    conn = get_connection()
    try:
        # Verificar si la tabla existe
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affiliation_goals'")
        tabla_existe = cur.fetchone()
        
        if tabla_existe:
            cur.execute("""
                SELECT monthly_goal 
                FROM affiliation_goals 
                WHERE employee_id = ? AND year = ? AND month = ?
            """, (employee_id, year, month))
            
            result = cur.fetchone()
            if result:
                return result[0]
        
        # Si no hay meta específica, usar la meta general del empleado
        cur.execute("SELECT affiliation_goal FROM employees WHERE id = ?", (employee_id,))
        general_goal = cur.fetchone()
        return general_goal[0] if general_goal else 0
    except Exception as e:
        return 0
    finally:
        conn.close()

def set_employee_affiliation_goal(employee_id, year, month, goal):
    """Establecer meta de afiliaciones para un empleado"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO affiliation_goals (employee_id, year, month, monthly_goal)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_id, year, month) 
            DO UPDATE SET monthly_goal = excluded.monthly_goal,
                         updated_at = CURRENT_TIMESTAMP
        """, (employee_id, year, month, goal))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al guardar meta: {e}")
        return False
    finally:
        conn.close()

def register_affiliation(employee_id, affiliation_type_id, quantity, registration_date, observations=""):
    """Registrar una nueva afiliación"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO affiliations 
            (employee_id, affiliation_type_id, quantity, registration_date, observations)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, affiliation_type_id, quantity, registration_date, observations))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al registrar afiliación: {e}")
        return False
    finally:
        conn.close()

def get_employee_affiliations(employee_id, start_date=None, end_date=None):
    """Obtener afiliaciones de un empleado en un rango de fechas"""
    conn = get_connection()
    try:
        # Verificar si las tablas existen
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affiliations'")
        if not cur.fetchone():
            return pd.DataFrame(columns=['Fecha', 'Tipo', 'Cantidad', 'Puntos', 'Observaciones'])
        
        query = """
            SELECT 
                a.id,
                a.registration_date as 'Fecha',
                at.name as 'Tipo',
                a.quantity as 'Cantidad',
                at.points_value as 'Valor punto',
                (a.quantity * at.points_value) as 'Puntos',
                a.observations as 'Observaciones'
            FROM affiliations a
            JOIN affiliation_types at ON a.affiliation_type_id = at.id
            WHERE a.employee_id = ?
        """
        params = [employee_id]
        
        if start_date:
            query += " AND a.registration_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.registration_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY a.registration_date DESC"
        
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['Fecha', 'Tipo', 'Cantidad', 'Puntos', 'Observaciones'])
    finally:
        conn.close()

def get_all_affiliations_summary(start_date=None, end_date=None):
    """Obtener resumen de afiliaciones para todos los empleados"""
    conn = get_connection()
    try:
        # Verificar si las tablas existen
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affiliations'")
        if not cur.fetchone():
            return pd.DataFrame(columns=['Empleado', 'Departamento', 'Cargo', 'Total afiliaciones', 'Total puntos'])
        
        query = """
            SELECT 
                e.id,
                e.name as 'Empleado',
                e.department as 'Departamento',
                e.position as 'Cargo',
                COUNT(a.id) as 'Total registros',
                COALESCE(SUM(a.quantity), 0) as 'Total afiliaciones',
                COALESCE(SUM(a.quantity * at.points_value), 0) as 'Total puntos',
                COALESCE(AVG(at.points_value), 0) as 'Promedio puntos'
            FROM employees e
            LEFT JOIN affiliations a ON e.id = a.employee_id
            LEFT JOIN affiliation_types at ON a.affiliation_type_id = at.id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND a.registration_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.registration_date <= ?"
            params.append(end_date)
            
        query += " GROUP BY e.id ORDER BY SUM(a.quantity) DESC NULLS LAST"
        
        df = pd.read_sql(query, conn, params=params)
        return df.fillna(0)
    except Exception as e:
        return pd.DataFrame(columns=['Empleado', 'Departamento', 'Cargo', 'Total afiliaciones', 'Total puntos'])
    finally:
        conn.close()

def get_affiliation_stats_by_period(period='month'):
    """Obtener estadísticas de afiliaciones por período"""
    conn = get_connection()
    try:
        # Verificar si las tablas existen
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affiliations'")
        if not cur.fetchone():
            return pd.DataFrame(columns=['periodo', 'total_afiliaciones'])
        
        if period == 'month':
            group_by = "strftime('%Y-%m', registration_date) as periodo"
        elif period == 'week':
            group_by = "strftime('%Y-%W', registration_date) as periodo"
        else:  # day
            group_by = "registration_date as periodo"
            
        query = f"""
            SELECT 
                {group_by},
                COUNT(DISTINCT employee_id) as empleados_activos,
                SUM(quantity) as total_afiliaciones,
                SUM(quantity * at.points_value) as total_puntos,
                AVG(quantity) as promedio_por_registro
            FROM affiliations a
            JOIN affiliation_types at ON a.affiliation_type_id = at.id
            GROUP BY periodo
            ORDER BY periodo DESC
            LIMIT 12
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['periodo', 'total_afiliaciones'])
    finally:
        conn.close()

def render_affiliations_page(employee_id=None, employee_name=None):
    """Renderizar página de afiliaciones"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h3 style="color: #4f7cff;">📋 Registro de Afiliaciones</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📝 Registrar Afiliación", 
        "📊 Mi Progreso", 
        "🎯 Metas"
    ])
    
    # Obtener datos necesarios
    affiliation_types = get_affiliation_types()
    
    # ===== TAB 1: REGISTRAR AFILIACIÓN =====
    with tab1:
        with st.form("affiliation_form"):
            # Seleccionar tipo de afiliación
            if not affiliation_types.empty:
                tipo_options = dict(zip(affiliation_types['name'], affiliation_types['id']))
                selected_type = st.selectbox(
                    "Tipo de afiliación*",
                    options=list(tipo_options.keys())
                )
                tipo_id = tipo_options[selected_type]
                puntos_tipo = affiliation_types[affiliation_types['id'] == tipo_id]['points_value'].iloc[0]
                
                st.info(f"💡 Valor por unidad: **{puntos_tipo} puntos**")
            else:
                st.warning("No hay tipos de afiliación configurados")
                selected_type = None
                tipo_id = None
                puntos_tipo = 1
            
            # Cantidad
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                cantidad = st.number_input("Cantidad*", min_value=1, value=1, step=1)
            with col_q2:
                total_puntos = cantidad * puntos_tipo if puntos_tipo else 0
                st.metric("Puntos totales", f"{total_puntos:.1f}")
            
            # Fecha
            fecha = st.date_input("Fecha de registro*", value=date.today())
            
            # Observaciones
            observaciones = st.text_area("Observaciones", placeholder="Notas adicionales...")
            
            submitted = st.form_submit_button("💾 Registrar Afiliación", type="primary", use_container_width=True)
            
            if submitted:
                if selected_type and cantidad > 0 and employee_id:
                    success = register_affiliation(
                        employee_id, 
                        tipo_id, 
                        cantidad, 
                        fecha.strftime("%Y-%m-%d"),
                        observaciones
                    )
                    if success:
                        st.success("✅ Afiliación registrada exitosamente!")
                        st.balloons()
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("⚠️ Completa todos los campos obligatorios")
    
    # ===== TAB 2: MI PROGRESO =====
    with tab2:
        if employee_id:
            # Selector de período
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                year = st.selectbox("Año", [date.today().year, date.today().year - 1, date.today().year - 2])
            with col_p2:
                month = st.selectbox("Mes", range(1, 13), index=date.today().month - 1)
            
            # Obtener meta del mes
            monthly_goal = get_employee_affiliation_goal(employee_id, year, month)
            
            # Obtener afiliaciones del período
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            df_aff = get_employee_affiliations(employee_id, start_date, end_date)
            
            if not df_aff.empty:
                # Métricas principales
                total_afiliaciones = df_aff['Cantidad'].sum()
                total_puntos = df_aff['Puntos'].sum()
                cumplimiento = (total_afiliaciones / monthly_goal * 100) if monthly_goal > 0 else 0
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Total afiliaciones", f"{int(total_afiliaciones)}")
                with col_m2:
                    st.metric("Total puntos", f"{int(total_puntos)}")
                with col_m3:
                    st.metric("Meta mensual", f"{monthly_goal}")
                with col_m4:
                    st.metric("Cumplimiento", f"{cumplimiento:.1f}%")
                
                # Barra de progreso
                progress_color = COLORS['success'] if cumplimiento >= 100 else COLORS['primary']
                st.markdown(f"""
                <div style="margin: 20px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Progreso mensual</span>
                        <span><strong>{int(total_afiliaciones)}/{monthly_goal}</strong></span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: {min(cumplimiento, 100)}%; background: {progress_color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Gráfico
                if not df_aff.empty:
                    df_daily = df_aff.groupby('Fecha').agg({'Cantidad': 'sum'}).reset_index()
                    fig = px.bar(
                        df_daily,
                        x='Fecha',
                        y='Cantidad',
                        title="Afiliaciones por día",
                        color_discrete_sequence=[COLORS['primary']]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                with st.expander("📋 Ver detalle de afiliaciones"):
                    st.dataframe(
                        df_aff[['Fecha', 'Tipo', 'Cantidad', 'Puntos', 'Observaciones']],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info(f"📭 No hay afiliaciones registradas en {start_date.strftime('%B %Y')}")
        else:
            st.warning("⚠️ No hay información de empleado disponible")
    
    # ===== TAB 3: METAS =====
    with tab3:
        if employee_id:
            st.markdown("### 🎯 Configuración de metas mensuales")
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                meta_year = st.number_input("Año", min_value=2024, value=date.today().year, key="goal_year")
            with col_g2:
                meta_month = st.number_input("Mes", min_value=1, max_value=12, value=date.today().month, key="goal_month")
            
            # Obtener meta actual
            current_goal = get_employee_affiliation_goal(employee_id, meta_year, meta_month)
            
            with st.form("goal_form"):
                new_goal = st.number_input(
                    "Meta mensual de afiliaciones",
                    min_value=0,
                    value=current_goal,
                    step=5
                )
                
                submitted_goal = st.form_submit_button("💾 Guardar meta", type="primary", use_container_width=True)
                
                if submitted_goal:
                    success = set_employee_affiliation_goal(employee_id, meta_year, meta_month, new_goal)
                    if success:
                        st.success("✅ Meta guardada exitosamente!")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
        else:
            st.warning("⚠️ No hay información de empleado disponible")