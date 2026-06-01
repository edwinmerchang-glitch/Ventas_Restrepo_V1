# Locatel AIS – Sistema de Ventas v2.0

## Cambios respecto a la versión anterior

### 🔒 Seguridad
- Contraseñas hasheadas con **PBKDF2-HMAC-SHA256 + salt** (antes: SHA-256 plano sin sal)
- Migración automática: usuarios existentes se migran al nuevo hash en el próximo login
- Admin por defecto usa contraseña `Admin2024!` y debe cambiarla obligatoriamente en el primer login
- Contraseña mínima de 8 caracteres en todos los formularios
- Guard de permisos: empleados no pueden acceder a rutas de administrador

### 🏗 Arquitectura
- `ventas.py` reducido de 2.494 a ~180 líneas (punto de entrada únicamente)
- Código organizado en módulos independientes dentro de `pages/`:
  - `dashboard_page.py` — Dashboard con comparativo
  - `ventas_page.py` — Registro de ventas
  - `ranking_page.py` — Ranking
  - `desempeno_page.py` — Mi desempeño y Mi perfil
  - `afiliaciones_page.py` — Afiliaciones
  - `admin_page.py` — Empleados, Usuarios, Reportes, Auditoría
- `utils.py` — helpers compartidos (BD, progreso, periodo_a_fecha)
- `database.py` — WAL mode, FK enforcement, tabla audit_log

### ✨ Funcionalidades nuevas
- **Comparativo mes anterior** en el Dashboard (tab "Comparativo")
- **Log de auditoría** con filtro de búsqueda (página Auditoría)
- **Reporte de cumplimiento de metas** con gráfico de colores semáforo
- **Reporte de días sin registro** para detectar ausencias
- **Cambio de contraseña propio** desde Mi Perfil
- **Valores pre-cargados** al editar ventas de un día anterior
- **Progress bar con colores** verde/amarillo/rojo según cumplimiento
- **Celebración de meta** con confeti al superar la meta mensual
- **Meta de afiliaciones editable** al crear empleados
- **Gráfico de distribución personal** por categoría en Mi desempeño

### 🔧 Mejoras técnicas
- `PRAGMA journal_mode=WAL` para mejor concurrencia en SQLite
- `PRAGMA foreign_keys=ON` activo en todas las conexiones
- Un único patrón de acceso a BD (eliminada duplicación `safe_dataframe` vs `execute_query`)
- Menú lateral con secciones colapsadas y botón activo resaltado
- Footer eliminado (reducción de ruido visual)

## Estructura de archivos
```
ventas.py              ← Punto de entrada
utils.py               ← Helpers compartidos
auth.py                ← Autenticación segura
database.py            ← BD con auditoría
pages/
  dashboard_page.py
  ventas_page.py
  ranking_page.py
  desempeno_page.py
  afiliaciones_page.py
  admin_page.py
export_utils.py        ← Sin cambios
backup_manager.py      ← Sin cambios
keep_alive.py          ← Sin cambios
styles.css             ← Sin cambios
```
