"""
Código Crítico - Tercer Semestre - Año 2026
Cliente Turso usando HTTP (parser corregido)
"""

import threading
import requests
import json
from typing import List, Dict, Any, Optional

from config import TURSO_URL, TURSO_TOKEN
from database import ejecutar_consulta, obtener_conexion


def _escape(val):
    """Escapa valores para SQL"""
    if val is None:
        return "NULL"
    if isinstance(val, bytes):
        return "X'" + val.hex() + "'"
    if isinstance(val, memoryview):
        return "X'" + bytes(val).hex() + "'"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, dict):
        if 'value' in val:
            return _escape(val['value'])
        return "'" + str(val).replace("'", "''") + "'"
    return "'" + str(val).replace("'", "''") + "'"


def _pipeline_turso(requests_payload, timeout=60):
    """Ejecuta pipeline de requests en Turso via HTTP"""
    if not TURSO_TOKEN or not TURSO_URL:
        return {"error": "No hay configuración de Turso"}
    
    try:
        body = {"requests": requests_payload}
        response = requests.post(
            TURSO_URL,
            headers={
                "Authorization": f"Bearer {TURSO_TOKEN}",
                "Content-Type": "application/json"
            },
            json=body,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error HTTP: {e}")
        return {"error": str(e)}


def _parse_turso_value(val):
    """Parsea valores de Turso correctamente"""
    if val is None:
        return None
    if isinstance(val, dict):
        # Extraer el valor real del dict
        if 'value' in val:
            return _parse_turso_value(val['value'])
        if 'type' in val and 'value' in val:
            return _parse_turso_value(val['value'])
        return val
    return val


def consultar_turso(query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT en Turso via HTTP"""
    if not TURSO_TOKEN or not TURSO_URL:
        print("❌ Configuración de Turso incompleta")
        return []
    
    try:
        if params:
            parts = query.split("?")
            if len(parts) - 1 != len(params):
                return []
            full_query = parts[0]
            for i, val in enumerate(params):
                full_query += _escape(val) + parts[i + 1]
        else:
            full_query = query
        
        print(f"📤 Consultando Turso: {full_query[:80]}...")
        
        resultado = _pipeline_turso([
            {"type": "execute", "stmt": {"sql": full_query}},
            {"type": "close"}
        ])
        
        if not resultado or "error" in resultado:
            return []
        
        if "results" not in resultado:
            return []
        
        first = resultado["results"][0]
        if first.get("type") != "ok":
            return []
        
        response = first.get("response", {})
        if response.get("type") != "execute":
            return []
        
        result = response.get("result", {})
        if result.get("error"):
            return []
        
        cols = [c["name"] for c in result.get("cols", [])]
        rows = result.get("rows", [])
        
        if not cols:
            return []
        
        parsed_rows = []
        for row in rows:
            parsed_row = {}
            for i, col_name in enumerate(cols):
                if i < len(row):
                    val = row[i]
                    parsed_val = _parse_turso_value(val)
                    if isinstance(parsed_val, bytes):
                        parsed_val = '0x' + parsed_val.hex()
                    parsed_row[col_name] = parsed_val
                else:
                    parsed_row[col_name] = None
            parsed_rows.append(parsed_row)
        
        print(f"✅ Consulta exitosa: {len(parsed_rows)} filas")
        return parsed_rows
        
    except Exception as e:
        print(f"❌ Error en consultar_turso: {e}")
        import traceback
        traceback.print_exc()
        return []


def ejecutar_turso(query: str, params: Optional[List[Any]] = None) -> int:
    """Ejecuta una consulta de escritura en Turso via HTTP"""
    if not TURSO_TOKEN or not TURSO_URL:
        print("❌ Configuración de Turso incompleta")
        return 0
    
    try:
        if params:
            parts = query.split("?")
            if len(parts) - 1 != len(params):
                return 0
            full_query = parts[0]
            for i, val in enumerate(params):
                full_query += _escape(val) + parts[i + 1]
        else:
            full_query = query
        
        print(f"📤 Ejecutando en Turso: {full_query[:80]}...")
        
        resultado = _pipeline_turso([
            {"type": "execute", "stmt": {"sql": full_query}},
            {"type": "close"}
        ])
        
        if not resultado or "error" in resultado:
            return 0
        
        if "results" not in resultado:
            return 0
        
        first = resultado["results"][0]
        if first.get("type") != "ok":
            return 0
        
        response = first.get("response", {})
        result = response.get("result", {})
        
        row_count = result.get("affected_row_count", 0)
        print(f"✅ Escritura exitosa: {row_count} filas afectadas")
        return row_count
        
    except Exception as e:
        print(f"❌ Error en ejecutar_turso: {e}")
        return 0


def test_conexion_turso() -> bool:
    """Prueba la conexión con Turso via HTTP"""
    try:
        resultado = consultar_turso("SELECT 1 as test")
        if resultado:
            # Verificar si el valor es 1 (puede ser int o string)
            val = resultado[0].get('test')
            if val == 1 or val == '1':
                print("✅ Conexión con Turso exitosa")
                return True
            else:
                print(f"❌ Valor inesperado: {val} (tipo: {type(val)})")
                return False
        else:
            print("❌ Conexión con Turso falló: resultado vacío")
            return False
    except Exception as e:
        print(f"❌ Conexión con Turso falló: {e}")
        return False


def obtener_info_turso() -> Dict[str, Any]:
    """Obtiene información de la base de datos Turso"""
    info = {
        "connected": False,
        "tables": [],
        "table_counts": {}
    }
    
    try:
        tables = consultar_turso("SELECT name FROM sqlite_master WHERE type='table'")
        if tables:
            info["connected"] = True
            for t in tables:
                table_name = t.get('name')
                if table_name and not table_name.startswith('_'):
                    info["tables"].append(table_name)
                    count = consultar_turso(f"SELECT COUNT(*) as count FROM {table_name}")
                    if count:
                        info["table_counts"][table_name] = count[0].get('count', 0)
    except Exception as e:
        print(f"❌ Error obteniendo info de Turso: {e}")
    
    return info


def obtener_columnas_tabla(tabla: str) -> List[str]:
    """Obtiene los nombres de las columnas de una tabla local"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    rows = cursor.fetchall()
    conn.close()
    return [row[1] for row in rows if row[1] != 'rowid']


def subir_tabla_pyturso(tabla: str) -> int:
    """Sube datos locales a Turso via HTTP"""
    try:
        columnas = obtener_columnas_tabla(tabla)
        if not columnas:
            print(f"⚠️ Tabla {tabla} no existe localmente")
            return 0
        
        from database import obtener_ultimo_timestamp_sync
        last_ts = obtener_ultimo_timestamp_sync(tabla, "up")
        
        filas = ejecutar_consulta(
            f"SELECT * FROM {tabla} WHERE created_at > ? ORDER BY created_at ASC",
            (last_ts,)
        )
        
        if not filas:
            return 0
        
        print(f"📤 Subiendo {len(filas)} filas de {tabla} a Turso...")
        
        columnas_str = ", ".join(columnas)
        for fila in filas:
            valores_escapados = [_escape(fila.get(col)) for col in columnas]
            sql = f"INSERT OR REPLACE INTO {tabla} ({columnas_str}) VALUES ({', '.join(valores_escapados)})"
            _pipeline_turso([
                {"type": "execute", "stmt": {"sql": sql}},
                {"type": "close"}
            ])
        
        max_ts = max(f["created_at"] for f in filas if f.get("created_at"))
        if max_ts:
            from database import actualizar_ultimo_timestamp_sync
            actualizar_ultimo_timestamp_sync(tabla, max_ts, "up")
        
        print(f"✅ {tabla}: {len(filas)} filas subidas")
        return len(filas)
        
    except Exception as e:
        print(f"❌ Error en subir_tabla_pyturso: {e}")
        import traceback
        traceback.print_exc()
        return 0


def bajar_tabla_pyturso(tabla: str) -> int:
    """Baja datos desde Turso a local via HTTP"""
    try:
        columnas = obtener_columnas_tabla(tabla)
        if not columnas:
            print(f"⚠️ Tabla {tabla} no existe localmente")
            return 0
        
        from database import obtener_ultimo_timestamp_sync
        last_ts = obtener_ultimo_timestamp_sync(tabla, "down")
        
        print(f"📥 Bajando {tabla} desde Turso...")
        
        filas = consultar_turso(
            f"SELECT * FROM {tabla} WHERE created_at > ? ORDER BY created_at ASC",
            [last_ts]
        )
        
        if not filas:
            print(f"ℹ️ No hay datos nuevos en {tabla}")
            return 0
        
        print(f"📥 {len(filas)} filas nuevas en {tabla}")
        
        columnas_filtradas = [col for col in columnas if col in filas[0]]
        
        for fila in filas:
            valores = []
            for col in columnas_filtradas:
                val = fila.get(col)
                if isinstance(val, dict):
                    val = val.get('value', None)
                valores.append(val)
            
            placeholders = ", ".join(["?"] * len(columnas_filtradas))
            columnas_str = ", ".join(columnas_filtradas)
            
            sql = f"INSERT OR REPLACE INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
            ejecutar_consulta(sql, valores, commit=True)
        
        max_ts = None
        for r in filas:
            ts = r.get("created_at")
            if isinstance(ts, dict):
                ts = ts.get('value')
            if ts and (max_ts is None or str(ts) > str(max_ts)):
                max_ts = ts
        
        if max_ts:
            from database import actualizar_ultimo_timestamp_sync
            actualizar_ultimo_timestamp_sync(tabla, max_ts, "down")
        
        print(f"✅ {tabla}: {len(filas)} filas bajadas")
        return len(filas)
        
    except Exception as e:
        print(f"❌ Error en bajar_tabla_pyturso: {e}")
        import traceback
        traceback.print_exc()
        return 0


def sincronizacion_completa_pyturso():
    """Sincronización completa usando HTTP"""
    from config import TABLAS_SUBIDA, TABLAS_BAJADA
    from datetime import datetime
    
    print(f"\n🔄 [SYNC] Iniciando sincronización a las {datetime.now()}")
    
    print("\n📤 SUBIENDO DATOS:")
    for tabla in TABLAS_SUBIDA:
        try:
            subir_tabla_pyturso(tabla)
        except Exception as e:
            print(f"❌ Error subiendo {tabla}: {e}")
    
    print("\n📥 BAJANDO DATOS:")
    for tabla in TABLAS_BAJADA:
        try:
            bajar_tabla_pyturso(tabla)
        except Exception as e:
            print(f"❌ Error bajando {tabla}: {e}")
    
    print(f"✅ [SYNC] Sincronización completada a las {datetime.now()}\n")


def iniciar_hilo_sincronizacion_pyturso():
    """Inicia el hilo de sincronización usando HTTP"""
    import time
    from config import SUBIDA_CADA_SEGUNDOS
    
    def loop():
        while True:
            try:
                sincronizacion_completa_pyturso()
            except Exception as e:
                print(f"❌ Error en sincronización: {e}")
            time.sleep(SUBIDA_CADA_SEGUNDOS)
    
    threading.Thread(target=loop, daemon=True).start()
    print(f"🚀 Hilo de sincronización HTTP iniciado (cada {SUBIDA_CADA_SEGUNDOS}s)")

# Mostrar que estamos usando HTTP
print("✅ Usando HTTP (sin libsql-client)")