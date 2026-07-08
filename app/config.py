"""
Código Crítico - Tercer Semestre - Año 2026
Archivo de configuración central para la aplicación.
Define rutas, tablas de sincronización, intervalos y parámetros globales.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

# Ruta de la base de datos local (SQLite)
DB_PATH = os.environ.get("DB_PATH", "catalogo.db")

# ============================================================
# CONFIGURACIÓN DE TURSO
# ============================================================

# ✅ URL de Turso (convertida a HTTP)
TURSO_URL = os.environ.get(
    "TURSO_URL",
    "https://nube-clarionda.aws-us-east-1.turso.io/v2/pipeline"
)

# ✅ Token de Turso
TURSO_TOKEN = os.environ.get(
    "TURSO_TOKEN",
    "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODI1MTQyMTEsImlkIjoiMDE5ZjA2MjAtM2YwMS03NzgwLWI0ZDgtNDU3YWY3OWYyNzY1IiwicmlkIjoiOWU1YzkyZDktMmI3MC00MTJjLThkNmYtZjgzMzY5NjM4ODViIn0.H_PKJrBCAvNH5WPaCYUJOgHDVDPQHw7Y4qir1zFlx6MSih-vjUZnojZdp5AmMwAz9151gNCjX-rC3oGuj_ETAw"
)

# ============================================================
# INTERVALOS DE SINCRONIZACIÓN
# ============================================================

SUBIDA_CADA_SEGUNDOS = int(os.environ.get("SUBIDA_CADA_SEGUNDOS", 3))
BAJADA_CADA_SEGUNDOS = int(os.environ.get("BAJADA_CADA_SEGUNDOS", 3))

# ============================================================
# TABLAS PARTICIPANTES EN SINCRONIZACIÓN
# ============================================================

# Tablas que SUBEN a Turso (local -> Turso)
TABLAS_SUBIDA = [
    "clientes",
    "preventistas",
    "categorias",
    "notas_venta",
    "nota_venta_detalle",
    "cobros",
    "cuenta_corriente_movimientos",
    "posiciones_preventistas",
    "visitas_clientes"
]

# Tablas que BAJAN desde Turso (Turso -> local)
TABLAS_BAJADA = [
    "clientes",
    "preventistas",
    "categorias"
]

# ============================================================
# OPCIONES ADICIONALES
# ============================================================

CACHE_IMAGENES_DIR = os.path.join(os.path.dirname(__file__), "cache_imagenes")

# ============================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================

if not TURSO_TOKEN:
    print("⚠️ ADVERTENCIA: TURSO_TOKEN no está configurado.")
    print("   Crea un archivo .env con TURSO_TOKEN=tu_token")
else:
    print(f"✅ Configuración de Turso cargada correctamente.")
    print(f"   URL: {TURSO_URL}")
    print(f"   Token: {TURSO_TOKEN[:20]}...")
    print(f"   Subida cada: {SUBIDA_CADA_SEGUNDOS}s")
    print(f"   Bajada cada: {BAJADA_CADA_SEGUNDOS}s")