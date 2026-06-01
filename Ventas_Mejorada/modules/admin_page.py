"""Páginas de administración: Empleados, Usuarios, Reportes, Auditoría."""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import date
from utils import (execute_query, execute_insert, safe_dataframe,
                   CARGOS, DEPARTAMENTOS, get_badge_class)
from auth import create_user, get_all_users, hash_password, verify_password
from export_utils import barra_exportacion


# ══════════════════════════════════════════════════════════════════════
#  EMPLEADOS
# ══════════════════════════════════════════════════════════════════════
def page_empleados():
    st.title("🧑‍💼 Gestión de Empleados AIS")

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Registrar", "👤 Asignar usuario", "📋 Lista", "✏️ Editar / Eliminar"])

    with tab1:
        st.markdown('<div class="card" style="background:#e8f4fd"><h4>📌 Paso 1: Registrar empleado</h4><p>Luego asígnale un usuario en la pestaña siguiente.</p></div>', unsafe_allow_html=True)
        with st.form("reg_emp"):
            c1, c2 = st.columns(2)
            with c1:
                name       = st.text_input("Nombre completo*")
                position   = st.selectbox("Cargo*", CARGOS)
            with c2:
                department = st.selectbox("Departamento*", DEPARTAMENTOS)
                goal       = st.number_input("Meta mensual unidades", value=300, min_value=1, step=50)
                meta_afil  = st.number_input("Meta mensual afiliaciones", value=50, min_value=1, step=10)
            if st.form_submit_button("Registrar empleado", type="primary", use_container_width=True):
                if name and position and department:
                    if execute_query("SELECT id FROM employees WHERE name=?", (name,)):
                        st.warning(f"⚠️ Ya existe '{name}'")
                    else:
                        ok = execute_insert(
                            "INSERT INTO employees (name,position,department,goal,meta_afiliaciones,user_id) VALUES (?,?,?,?,?,NULL)",
                            (name, position, department, goal, meta_afil),
                            audit_action=f"Crear empleado {name}",
                        )
                        if ok:
                            st.success(f"✅ '{name}' registrado. Ahora crea su usuario.")
                            st.balloons(); time.sleep(1); st.rerun()
                else:
                    st.warning("⚠️ Completa todos los campos obligatorios (*)")

    with tab2:
        emp_sin = execute_query("SELECT id, name, position, department FROM employees WHERE user_id IS NULL ORDER BY name")
        if not emp_sin:
            st.success("✅ Todos los empleados tienen usuario asignado.")
        else:
            with st.form("asignar_user"):
                opts = {f"{e[1]} – {e[2]}": e[0] for e in emp_sin}
                emp_id = opts[st.selectbox("Empleado*", list(opts.keys()))]
                st.divider()
                username  = st.text_input("Nombre de usuario*")
                password  = st.text_input("Contraseña* (mín. 6 caracteres)", type="password")
                confirm   = st.text_input("Confirmar contraseña*", type="password")
                if st.form_submit_button("Crear usuario y asignar", type="primary", use_container_width=True):
                    if not username or not password:
                        st.warning("⚠️ Completa todos los campos.")
                    elif len(password) < 6:
                        st.warning("⚠️ Contraseña mínimo 8 caracteres.")
                    elif password != confirm:
                        st.warning("⚠️ Las contraseñas no coinciden.")
                    else:
                        try:
                            uid, *_ = create_user(username, password)
                            ok = execute_insert("UPDATE employees SET user_id=? WHERE id=?", (uid, emp_id),
                                               audit_action=f"Asignar usuario {username}")
                            if ok:
                                st.success(f"✅ Usuario '{username}' creado y asignado.")
                                st.balloons(); time.sleep(1); st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {e}")

    with tab3:
        df_emp = safe_dataframe("""
            SELECT e.id, e.name 'Nombre', e.position 'Cargo', e.department 'Departamento',
                   e.goal 'Meta', e.meta_afiliaciones 'Meta Afil.',
                   COALESCE(u.username,'⏳ Pendiente') 'Usuario',
                   CASE WHEN u.username IS NOT NULL THEN '✅ Asignado' ELSE '❌ Sin usuario' END 'Estado'
            FROM employees e LEFT JOIN users u ON e.user_id=u.id
            ORDER BY CASE WHEN u.username IS NULL THEN 0 ELSE 1 END, e.department, e.name
        """)
        if not df_emp.empty:
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
            c1,c2,c3 = st.columns(3)
            c1.metric("Total", len(df_emp))
            c2.metric("Con usuario", len(df_emp[df_emp["Estado"]=="✅ Asignado"]))
            c3.metric("Sin usuario", len(df_emp[df_emp["Estado"]=="❌ Sin usuario"]))
            barra_exportacion(df_emp, titulo="Lista de Empleados", nombre_archivo="empleados", key_prefix="emp_list")

    with tab4:
        todos = execute_query("""
            SELECT e.id, e.name, e.position, e.department, e.goal, e.meta_afiliaciones, u.username
            FROM employees e LEFT JOIN users u ON e.user_id=u.id ORDER BY e.name
        """)
        if not todos:
            st.info("No hay empleados.")
            return
        opts = {f"{e[1]} – {e[2]} ({e[6] or 'sin usuario'})": e[0] for e in todos}
        sel  = opts[st.selectbox("Seleccionar empleado", list(opts.keys()))]
        emp  = next(e for e in todos if e[0] == sel)

        c_edit, c_info = st.columns([3,1])
        with c_edit:
            with st.form("editar_emp"):
                new_name  = st.text_input("Nombre", value=emp[1])
                new_pos   = st.selectbox("Cargo", CARGOS, index=CARGOS.index(emp[2]) if emp[2] in CARGOS else 0)
                new_dept  = st.selectbox("Departamento", DEPARTAMENTOS, index=DEPARTAMENTOS.index(emp[3]) if emp[3] in DEPARTAMENTOS else 0)
                new_goal  = st.number_input("Meta unidades", value=emp[4], min_value=1, step=50)
                new_afil  = st.number_input("Meta afiliaciones", value=emp[5] or 50, min_value=1, step=10)
                col_a, col_b = st.columns(2)
                with col_a:
                    save = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
                with col_b:
                    delete = st.form_submit_button("🗑️ Eliminar", use_container_width=True)

                if save:
                    ok = execute_insert(
                        "UPDATE employees SET name=?,position=?,department=?,goal=?,meta_afiliaciones=? WHERE id=?",
                        (new_name,new_pos,new_dept,new_goal,new_afil,sel),
                        audit_action=f"Editar empleado {emp[1]}",
                    )
                    if ok: st.success("✅ Guardado."); time.sleep(1); st.rerun()

                if delete:
                    ventas = execute_query("SELECT COUNT(*) FROM sales WHERE employee_id=?", (sel,))
                    if ventas and ventas[0][0] > 0:
                        st.error("❌ No se puede eliminar: tiene ventas registradas.")
                    else:
                        st.session_state.confirmar_eliminar_emp = sel

            if st.session_state.get("confirmar_eliminar_emp") == sel:
                st.warning(f"¿Eliminar a {emp[1]}?")
                ca,cb = st.columns(2)
                with ca:
                    if st.button("✅ Sí", key="si_emp"):
                        execute_insert("DELETE FROM employees WHERE id=?", (sel,), audit_action=f"Eliminar empleado {emp[1]}")
                        del st.session_state.confirmar_eliminar_emp
                        st.rerun()
                with cb:
                    if st.button("❌ No", key="no_emp"):
                        del st.session_state.confirmar_eliminar_emp; st.rerun()

        with c_info:
            total_v = execute_query("SELECT COUNT(*) FROM sales WHERE employee_id=?", (sel,))
            st.markdown(f"**ID:** {emp[0]}\n\n**Usuario:** {emp[6] or '—'}\n\n**Ventas:** {total_v[0][0] if total_v else 0}")


# ══════════════════════════════════════════════════════════════════════
#  USUARIOS
# ══════════════════════════════════════════════════════════════════════
def page_usuarios():
    st.title("👤 Gestión de Usuarios AIS")

    tab1, tab2, tab3 = st.tabs(["📋 Lista", "🔑 Contraseñas", "✏️ Editar / Eliminar"])

    with tab1:
        users = get_all_users()
        if users:
            df_u = pd.DataFrame(users, columns=["ID","Usuario","Rol","Empleado","Departamento"])
            df_u["Empleado"]    = df_u["Empleado"].fillna("—")
            df_u["Departamento"]= df_u["Departamento"].fillna("—")
            st.dataframe(df_u, use_container_width=True, hide_index=True)
            c1,c2,c3 = st.columns(3)
            c1.metric("Total", len(df_u))
            c2.metric("Admins", len(df_u[df_u["Rol"]=="admin"]))
            c3.metric("Empleados", len(df_u[df_u["Rol"]=="empleado"]))

    with tab2:
        users = get_all_users()
        if not users: st.info("No hay usuarios."); return
        opts = {f"{u[1]} ({u[3] or 'sin empleado'})": u[0] for u in users}
        uid  = opts[st.selectbox("Seleccionar usuario", list(opts.keys()), key="chpass_sel")]
        new_p = st.text_input("Nueva contraseña (mín. 6 car.)", type="password")
        conf  = st.text_input("Confirmar", type="password")
        if st.button("Cambiar contraseña", type="primary"):
            if len(new_p) < 6:
                st.warning("⚠️ Mínimo 8 caracteres.")
            elif new_p != conf:
                st.error("❌ No coinciden.")
            else:
                ok = execute_insert("UPDATE users SET password=? WHERE id=?",
                                    (hash_password(new_p), uid),
                                    audit_action="Admin cambió contraseña")
                if ok: st.success("✅ Contraseña actualizada."); st.balloons()

    with tab3:
        todos = execute_query("""
            SELECT u.id, u.username, u.role, e.name, e.id
            FROM users u LEFT JOIN employees e ON u.id=e.user_id ORDER BY u.username
        """)
        if not todos: st.info("No hay usuarios."); return
        opts2 = {f"{u[1]} – {u[2]} ({u[3] or 'sin emp.'})": u[0] for u in todos}
        uid2  = opts2[st.selectbox("Seleccionar usuario", list(opts2.keys()), key="edit_user_sel")]
        udat  = next(u for u in todos if u[0] == uid2)

        if udat[1] == "admin":
            st.warning("⚠️ El usuario 'admin' no se puede modificar desde aquí.")
            return

        with st.form("edit_user_form"):
            new_uname = st.text_input("Nombre de usuario", value=udat[1])
            new_role  = st.selectbox("Rol", ["empleado","admin"], index=0 if udat[2]=="empleado" else 1)
            ca, cb    = st.columns(2)
            with ca: save_u = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
            with cb: del_u  = st.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if save_u:
                dup = execute_query("SELECT id FROM users WHERE username=? AND id!=?", (new_uname, uid2))
                if dup: st.warning("⚠️ Ese nombre ya existe.")
                else:
                    ok = execute_insert("UPDATE users SET username=?,role=? WHERE id=?",
                                       (new_uname,new_role,uid2), audit_action="Editar usuario")
                    if ok: st.success("✅ Usuario actualizado."); time.sleep(1); st.rerun()

            if del_u:
                if udat[3]: st.error("❌ Tiene empleado asociado. Desasócialo primero.")
                else: st.session_state.confirm_del_user = uid2

        if st.session_state.get("confirm_del_user") == uid2:
            st.warning(f"¿Eliminar usuario '{udat[1]}'?")
            ca, cb = st.columns(2)
            with ca:
                if st.button("✅ Sí", key="si_user"):
                    execute_insert("DELETE FROM users WHERE id=?", (uid2,), audit_action=f"Eliminar usuario {udat[1]}")
                    del st.session_state.confirm_del_user; st.rerun()
            with cb:
                if st.button("❌ No", key="no_user"):
                    del st.session_state.confirm_del_user; st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════════════
def page_reportes():
    st.title("📊 Reportes Avanzados")

    tipo = st.selectbox("Tipo de reporte", [
        "Ventas por departamento",
        "Ventas por cargo",
        "Días sin registro (empleados ausentes)",
        "Cumplimiento de metas",
    ])

    col_f1, col_f2 = st.columns(2)
    with col_f1: fi = st.date_input("Desde", value=date.today().replace(day=1), format="DD/MM/YYYY")
    with col_f2: ff = st.date_input("Hasta", value=date.today(), format="DD/MM/YYYY")

    if st.button("🔄 Generar reporte"):
        st.cache_data.clear()
        st.rerun()

    if tipo == "Ventas por departamento":
        df = safe_dataframe("""
            SELECT e.department, SUM(s.autoliquidable+s.oferta+s.marca+s.adicional) total,
                   AVG(s.autoliquidable+s.oferta+s.marca+s.adicional) promedio,
                   COUNT(DISTINCT e.id) empleados, COUNT(s.id) dias_reg
            FROM sales s JOIN employees e ON s.employee_id=e.id
            WHERE s.date BETWEEN ? AND ? GROUP BY e.department ORDER BY total DESC
        """, (fi, ff))
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            fig = px.bar(df, x="department", y="total", color="department",
                         title="Ventas por departamento", text="total")
            fig.update_traces(texttemplate="%{text:,}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
            barra_exportacion(df, "Reporte Dept.", nombre_archivo="reporte_depto", key_prefix="rep_d")

    elif tipo == "Ventas por cargo":
        df = safe_dataframe("""
            SELECT e.position, SUM(s.autoliquidable+s.oferta+s.marca+s.adicional) total,
                   COUNT(DISTINCT e.id) empleados
            FROM sales s JOIN employees e ON s.employee_id=e.id
            WHERE s.date BETWEEN ? AND ? GROUP BY e.position ORDER BY total DESC
        """, (fi, ff))
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            fig = px.pie(df, values="total", names="position", title="Distribución por cargo")
            st.plotly_chart(fig, use_container_width=True)

    elif tipo == "Días sin registro (empleados ausentes)":
        df = safe_dataframe("""
            SELECT e.name, e.department,
                   MAX(s.date) ultimo_registro,
                   CAST(julianday('now') - julianday(MAX(s.date)) AS INTEGER) dias_sin_reg
            FROM employees e LEFT JOIN sales s ON e.id=s.employee_id
            GROUP BY e.id HAVING dias_sin_reg > 0 OR MAX(s.date) IS NULL
            ORDER BY dias_sin_reg DESC
        """)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info("💡 Empleados sin registros recientes pueden necesitar seguimiento.")

    elif tipo == "Cumplimiento de metas":
        df = safe_dataframe("""
            SELECT e.name, e.department, e.goal meta,
                   COALESCE(SUM(s.autoliquidable+s.oferta+s.marca+s.adicional),0) actual,
                   ROUND(COALESCE(SUM(s.autoliquidable+s.oferta+s.marca+s.adicional),0)*100.0/e.goal,1) pct
            FROM employees e LEFT JOIN sales s ON e.id=s.employee_id AND s.date BETWEEN ? AND ?
            GROUP BY e.id ORDER BY pct DESC
        """, (fi, ff))
        if not df.empty:
            fig = px.bar(df, x="name", y="pct", color="pct",
                         color_continuous_scale=["#dc2626","#d97706","#16a34a"],
                         range_color=[0,120], title="Cumplimiento de metas (%)",
                         text="pct", labels={"pct":"%","name":"Empleado"})
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.add_hline(y=100, line_dash="dash", line_color="#1a56db", annotation_text="100%")
            fig.update_layout(xaxis_tickangle=-35, height=450)
            st.plotly_chart(fig, use_container_width=True)
            barra_exportacion(df, "Cumplimiento Metas", nombre_archivo="cumplimiento", key_prefix="rep_c")


# ══════════════════════════════════════════════════════════════════════
#  LOG DE AUDITORÍA
# ══════════════════════════════════════════════════════════════════════
def page_auditoria():
    st.title("🔍 Log de Auditoría")
    st.caption("Registro de acciones realizadas por usuarios en el sistema.")

    df = safe_dataframe("""
        SELECT username, action, table_name, detail,
               datetime(created_at,'localtime') as fecha
        FROM audit_log ORDER BY created_at DESC LIMIT 200
    """)

    if df.empty:
        st.info("No hay registros de auditoría aún.")
        return

    col_f, col_u = st.columns(2)
    with col_f:
        buscar = st.text_input("🔎 Buscar acción o usuario")
    with col_u:
        if st.button("🔄 Actualizar"):
            st.cache_data.clear(); st.rerun()

    if buscar:
        mask = df.apply(lambda r: buscar.lower() in str(r).lower(), axis=1)
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)
    barra_exportacion(df, "Auditoría", nombre_archivo="auditoria", key_prefix="aud")
