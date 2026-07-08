"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de sincronización con Turso usando API HTTP.
"""

import threading
import time
import requests
from datetime import datetime
from config import TURSO_URL, TURSO_TOKEN, TABLAS_SUBIDA, TABLAS_BAJADA, SUBIDA_CADA_SEGUNDOS
from database import ejecutar_consulta, obtener_ultimo_timestamp_sync, actualizar_ultimo_timestamp_sync, obtener_conexion

def _escape(val):
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
    if not TURSO_TOKEN or not TURSO_URL:
        return {"error": "No hay configuración de Turso"}
    try:
        body = {"requests": requests_payload}
        response = requests.post(
            TURSO_URL,
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
            json=body,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al contactar Turso: {e}")
        return {"error": str(e)}

# ✅ FUNCIÓN EXPORTADA para que pedidos.py pueda usarla
def _consultar_turso(query, args=None):
    """Función pública para consultar Turso desde otros módulos"""
    if not TURSO_TOKEN or not TURSO_URL:
        return []
    try:
        if args:
            parts = query.split("?")
            if len(parts) - 1 != len(args):
                return []
            full_query = parts[0]
            for i, val in enumerate(args):
                full_query += _escape(val) + parts[i + 1]
        else:
            full_query = query
        
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
                    if isinstance(val, dict) and 'value' in val:
                        val = val['value']
                    if isinstance(val, str) and val.startswith('0x'):
                        try:
                            val = bytes.fromhex(val[2:])
                        except ValueError:
                            pass
                    parsed_row[col_name] = val
                else:
                    parsed_row[col_name] = None
            parsed_rows.append(parsed_row)
        
        return parsed_rows
    except Exception as e:
        print(f"Error en consultar_turso: {e}")
        return []

def obtener_columnas_tabla(tabla):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    rows = cursor.fetchall()
    conn.close()
    return [row[1] for row in rows if row[1] != 'rowid']

def subir_tabla(tabla):
    try:
        columnas = obtener_columnas_tabla(tabla)
        if not columnas:
            print(f"[INFO] Tabla {tabla} no existe localmente")
            return
        
        if tabla == 'nota_venta_detalle' and 'codigo_producto' not in columnas:
            columnas.append('codigo_producto')
        
        last_ts = obtener_ultimo_timestamp_sync(tabla, "up")
        filas = ejecutar_consulta(f"SELECT * FROM {tabla} WHERE created_at > ? ORDER BY created_at ASC", (last_ts,))
        if not filas:
            return
        
        if tabla == 'nota_venta_detalle' and 'codigo_producto' in columnas:
            print(f"[INFO] Subiendo {tabla} con codigo_producto")
        
        columnas_str = ", ".join(columnas)
        for fila in filas:
            if tabla == 'nota_venta_detalle' and 'codigo_producto' not in fila:
                detalle_id = fila.get('id')
                if detalle_id:
                    extra = ejecutar_consulta("SELECT codigo_producto FROM nota_venta_detalle WHERE id = ?", (detalle_id,))
                    if extra and extra[0].get('codigo_producto'):
                        fila['codigo_producto'] = extra[0]['codigo_producto']
            
            valores_escapados = [_escape(fila.get(col)) for col in columnas]
            sql = f"INSERT OR REPLACE INTO {tabla} ({columnas_str}) VALUES ({', '.join(valores_escapados)})"
            _pipeline_turso([
                {"type": "execute", "stmt": {"sql": sql}},
                {"type": "close"}
            ])
        
        max_ts = max(f["created_at"] for f in filas if f.get("created_at"))
        if max_ts:
            actualizar_ultimo_timestamp_sync(tabla, max_ts, "up")
            print(f"[SUBIDA] {tabla}: {len(filas)} filas enviadas. Último TS: {max_ts}")
        else:
            print(f"[SUBIDA] {tabla}: {len(filas)} filas enviadas")
    except Exception as e:
        print(f"[ERROR] Subiendo {tabla}: {e}")

def bajar_tabla(tabla):
    try:
        last_ts = obtener_ultimo_timestamp_sync(tabla, "down")
        rows = _consultar_turso(f"SELECT * FROM {tabla} WHERE created_at > ? ORDER BY created_at ASC", [last_ts])
        if not rows:
            return
        
        columnas = obtener_columnas_tabla(tabla)
        if not columnas:
            print(f"[ERROR] No se encontraron columnas para {tabla}")
            return
        
        if not rows or not isinstance(rows[0], dict):
            print(f"[ERROR] Formato de filas inesperado para {tabla}")
            return
        
        columnas_filtradas = [col for col in columnas if col in rows[0]]
        
        for fila in rows:
            valores = []
            for col in columnas_filtradas:
                val = fila.get(col)
                if isinstance(val, dict):
                    val = val.get('value', None)
                if isinstance(val, str) and val.startswith('0x'):
                    try:
                        val = bytes.fromhex(val[2:])
                    except ValueError:
                        pass
                valores.append(val)
            
            placeholders = ", ".join(["?" for _ in columnas_filtradas])
            columnas_str = ", ".join(columnas_filtradas)
            update_cols = ", ".join([f"{col}=excluded.{col}" for col in columnas_filtradas if col not in ("id", "created_at")])
            
            ejecutar_consulta(f"""
                INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {update_cols}
            """, valores, commit=True)
        
        max_ts = None
        for r in rows:
            ts = r.get("created_at")
            if isinstance(ts, dict):
                ts = ts.get('value')
            if ts and (max_ts is None or str(ts) > str(max_ts)):
                max_ts = ts
        
        if max_ts:
            actualizar_ultimo_timestamp_sync(tabla, max_ts, "down")
            print(f"[BAJADA] {tabla}: {len(rows)} filas actualizadas. Último TS: {max_ts}")
        else:
            print(f"[BAJADA] {tabla}: {len(rows)} filas actualizadas")
    except Exception as e:
        print(f"[ERROR] Bajando {tabla}: {e}")

def sincronizacion_completa():
    print(f"[SYNC] Iniciando sincronización a las {datetime.now()}")
    for tabla in TABLAS_SUBIDA:
        subir_tabla(tabla)
    for tabla in TABLAS_BAJADA:
        bajar_tabla(tabla)

def iniciar_hilo_sincronizacion():
    def loop():
        while True:
            try:
                sincronizacion_completa()
            except Exception as e:
                print(f"[ERROR] Sincronización general: {e}")
            time.sleep(SUBIDA_CADA_SEGUNDOS)
    threading.Thread(target=loop, daemon=True).start()
    print(f"Hilo de sincronización iniciado (cada {SUBIDA_CADA_SEGUNDOS} segundos)")
