"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de base de datos con soporte para PyTurso.
Maneja conexiones SQLite locales y sincronización con Turso.
"""

import sqlite3
import sys
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from config import DB_PATH


# ============================================================
# CONEXIÓN LOCAL (SQLite)
# ============================================================

def obtener_conexion():
    """Obtiene una conexión a la base de datos local SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ejecutar_consulta(query: str, params=None, commit: bool = False):
    """
    Ejecuta SQL en la base de datos local.
    Para SELECT: devuelve lista de diccionarios
    Para INSERT/UPDATE/DELETE: devuelve dict con 'filas_afectadas'
    """
    conn = obtener_conexion()
    cur = conn.cursor()
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            filas = cur.fetchall()
            resultado = [dict(fila) for fila in filas]
            conn.close()
            return resultado
        else:
            if commit:
                conn.commit()
            filas_afectadas = cur.rowcount
            conn.close()
            return {"filas_afectadas": filas_afectadas}
    except Exception as e:
        conn.close()
        raise e


def ejecutar_multiples(queries: List[Tuple[str, Optional[List[Any]]]], commit: bool = True):
    """
    Ejecuta múltiples consultas en una transacción local.
    """
    conn = obtener_conexion()
    cur = conn.cursor()
    try:
        for query, params in queries:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
        
        if commit:
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# FUNCIONES DE SINCRONIZACIÓN (TIMESTAMPS)
# ============================================================

def obtener_ultimo_timestamp_sync(tabla: str, direccion: str = "up") -> str:
    """
    Obtiene el último timestamp de sincronización para una tabla.
    """
    tabla_log = "sync_log" if direccion == "up" else "sync_log_reverse"
    filas = ejecutar_consulta(
        f"SELECT last_timestamp FROM {tabla_log} WHERE tabla = ?",
        (tabla,)
    )
    if filas and len(filas) > 0:
        return filas[0]["last_timestamp"]
    
    # Si no existe, insertar con valor por defecto
    ejecutar_consulta(
        f"INSERT OR IGNORE INTO {tabla_log} (tabla, last_timestamp) VALUES (?, ?)",
        (tabla, "1970-01-01T00:00:00"),
        commit=True
    )
    return "1970-01-01T00:00:00"


def actualizar_ultimo_timestamp_sync(tabla: str, timestamp: str, direccion: str = "up"):
    """
    Actualiza el último timestamp de sincronización para una tabla.
    """
    tabla_log = "sync_log" if direccion == "up" else "sync_log_reverse"
    ejecutar_consulta(
        f"UPDATE {tabla_log} SET last_timestamp = ? WHERE tabla = ?",
        (timestamp, tabla),
        commit=True
    )


def obtener_tablas_con_datos() -> List[str]:
    """
    Obtiene la lista de tablas que tienen datos en la base local.
    """
    resultado = ejecutar_consulta(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row['name'] for row in resultado]


def obtener_columnas_tabla(tabla: str) -> List[str]:
    """
    Obtiene los nombres de las columnas de una tabla local.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    rows = cursor.fetchall()
    conn.close()
    return [row[1] for row in rows if row[1] != 'rowid']


# ============================================================
# SINCRONIZACIÓN CON PYTURSO
# ============================================================

def sincronizar_fila(tabla: str, id_registro: str, direccion: str = "up"):
    """
    Sincroniza una fila específica inmediatamente usando PyTurso.
    """
    try:
        from turso_client import subir_tabla_pyturso, bajar_tabla_pyturso
        
        if direccion == "up":
            return subir_tabla_pyturso(tabla)
        else:
            return bajar_tabla_pyturso(tabla)
    except ImportError:
        print("⚠️ PyTurso no disponible, usando sincronización estándar")
        from sync import subir_tabla, bajar_tabla
        if direccion == "up":
            return subir_tabla(tabla)
        else:
            return bajar_tabla(tabla)


def sincronizar_tabla_completa(tabla: str, direccion: str = "up"):
    """
    Sincroniza una tabla completa.
    """
    try:
        from turso_client import subir_tabla_pyturso, bajar_tabla_pyturso
        
        if direccion == "up":
            return subir_tabla_pyturso(tabla)
        else:
            return bajar_tabla_pyturso(tabla)
    except ImportError:
        print("⚠️ PyTurso no disponible, usando sincronización estándar")
        from sync import subir_tabla, bajar_tabla
        if direccion == "up":
            return subir_tabla(tabla)
        else:
            return bajar_tabla(tabla)


# ============================================================
# MIGRACIONES DE BASE DE DATOS
# ============================================================

def aplicar_migraciones():
    """Aplica migraciones pendientes a la base de datos."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        
        # Verificar si la tabla nota_venta_detalle existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nota_venta_detalle'")
        if cur.fetchone():
            # Verificar columnas existentes
            cur.execute("PRAGMA table_info(nota_venta_detalle)")
            columnas = [row[1] for row in cur.fetchall()]
            
            # ✅ Migración: agregar codigo_producto si no existe
            if 'codigo_producto' not in columnas:
                conn.execute("ALTER TABLE nota_venta_detalle ADD COLUMN codigo_producto TEXT;")
                print("✅ Migración: columna codigo_producto agregada a nota_venta_detalle")
            
            conn.commit()
        else:
            print("⚠️ Tabla nota_venta_detalle no existe, se creará con el script")
        
        # ✅ Migración: verificar índices para sincronización
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_nota_detalle_codigo'")
        if not cur.fetchone():
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nota_detalle_codigo ON nota_venta_detalle(codigo_producto)")
            print("✅ Migración: índice idx_nota_detalle_codigo creado")
        
    except Exception as e:
        print(f"⚠️ Error en migración: {e}")
    finally:
        conn.close()


def inicializar_base_datos():
    """Inicializa la base de datos con el esquema completo."""
    # ✅ Si la base de datos existe, la eliminamos para crear una nueva con el esquema corregido
    if Path(DB_PATH).exists():
        print("🗑️ Eliminando base de datos anterior para recrearla con el esquema corregido...")
        try:
            os.remove(DB_PATH)
            print("✅ Base de datos anterior eliminada")
        except Exception as e:
            print(f"⚠️ Error al eliminar base de datos: {e}")
    
    # Crear nueva base de datos
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    script_path = Path(base_dir) / "script_creacion.sql"
    if not script_path.exists():
        raise FileNotFoundError(f"No se encuentra script_creacion.sql en {script_path}")
    
    with open(script_path, "r", encoding="utf-8") as f:
        sql = f.read()
    
    conn = obtener_conexion()
    try:
        conn.executescript(sql)
        conn.commit()
        print("✅ Base de datos inicializada correctamente con el nuevo esquema.")
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        raise
    finally:
        conn.close()
    
    # Aplicar migraciones adicionales
    aplicar_migraciones()
    
    # ✅ Crear tabla de logs de sincronización si no existe
    crear_tablas_sync_si_no_existen()


def crear_tablas_sync_si_no_existen():
    """Crea las tablas de sincronización si no existen."""
    conn = obtener_conexion()
    try:
        # Sync log para subida
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                tabla TEXT PRIMARY KEY,
                last_timestamp TEXT DEFAULT '1970-01-01T00:00:00'
            )
        """)
        
        # Sync log para bajada
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log_reverse (
                tabla TEXT PRIMARY KEY,
                last_timestamp TEXT DEFAULT '1970-01-01T00:00:00'
            )
        """)
        
        # Inicializar tablas de sincronización
        tablas = [
            'clientes', 'productos', 'preventistas', 'categorias', 
            'lotes', 'notas_venta', 'nota_venta_detalle',
            'facturas', 'factura_detalle', 'cuenta_corriente_movimientos',
            'cobros', 'cheques', 'usuarios', 'posiciones_preventistas',
            'visitas_clientes'
        ]
        
        for tabla in tablas:
            conn.execute(
                "INSERT OR IGNORE INTO sync_log (tabla, last_timestamp) VALUES (?, ?)",
                (tabla, "1970-01-01T00:00:00")
            )
            conn.execute(
                "INSERT OR IGNORE INTO sync_log_reverse (tabla, last_timestamp) VALUES (?, ?)",
                (tabla, "1970-01-01T00:00:00")
            )
        
        conn.commit()
        print("✅ Tablas de sincronización inicializadas")
    except Exception as e:
        print(f"⚠️ Error creando tablas de sincronización: {e}")
    finally:
        conn.close()


# ============================================================
# UTILIDADES DE SINCRONIZACIÓN
# ============================================================

def obtener_estado_sincronizacion() -> Dict[str, Any]:
    """
    Obtiene el estado actual de la sincronización.
    """
    estado = {
        "up": {},
        "down": {}
    }
    
    # Obtener timestamps de subida
    up_logs = ejecutar_consulta("SELECT tabla, last_timestamp FROM sync_log")
    for log in up_logs:
        estado["up"][log["tabla"]] = log["last_timestamp"]
    
    # Obtener timestamps de bajada
    down_logs = ejecutar_consulta("SELECT tabla, last_timestamp FROM sync_log_reverse")
    for log in down_logs:
        estado["down"][log["tabla"]] = log["last_timestamp"]
    
    return estado


def verificar_integridad_local() -> Dict[str, Any]:
    """
    Verifica la integridad de la base de datos local.
    """
    resultado = {
        "ok": True,
        "errores": [],
        "tablas": {}
    }
    
    try:
        # Verificar integridad de la base de datos
        integrity = ejecutar_consulta("PRAGMA integrity_check")
        if integrity and integrity[0].get('integrity_check') != 'ok':
            resultado["ok"] = False
            resultado["errores"].append(f"Integridad: {integrity[0].get('integrity_check')}")
        
        # Verificar cada tabla
        tablas = obtener_tablas_con_datos()
        for tabla in tablas:
            if tabla.startswith('sync_'):
                continue
            try:
                count = ejecutar_consulta(f"SELECT COUNT(*) as count FROM {tabla}")
                resultado["tablas"][tabla] = count[0]['count'] if count else 0
            except Exception as e:
                resultado["ok"] = False
                resultado["errores"].append(f"Tabla {tabla}: {e}")
        
    except Exception as e:
        resultado["ok"] = False
        resultado["errores"].append(f"Error general: {e}")
    
    return resultado