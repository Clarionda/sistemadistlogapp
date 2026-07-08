"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de autenticación de usuarios.
Autentica contra la tabla preventistas usando el legajo como usuario.
"""

import hashlib
from database import ejecutar_consulta

_usuario_actual = None

def hash_password(password):
    """Genera el hash SHA256 de una contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(username, password):
    """
    Autentica usando la tabla preventistas.
    El username es el legajo del preventista.
    La contraseña por defecto es '1234'.
    """
    # Buscar preventista por legajo
    preventistas = ejecutar_consulta(
        "SELECT id, nombre, apellido, legajo, zona, activo FROM preventistas WHERE legajo = ? AND activo = 1",
        (username,)
    )
    
    if not preventistas:
        return None
    
    preventista = preventistas[0]
    
    # Verificar contraseña (por defecto '1234')
    password_hash_esperado = hash_password('1234')
    
    if password_hash_esperado != hash_password(password):
        return None
    
    # Devolver el preventista como usuario (manteniendo compatibilidad)
    return {
        'id': preventista['id'],
        'username': preventista['legajo'],
        'nombre': preventista['nombre'],
        'apellido': preventista['apellido'],
        'rol': 'preventista',
        'preventista_id': preventista['id'],
        'cliente_id': None
    }

def establecer_usuario_actual(usuario):
    """Establece el usuario actual en sesión."""
    global _usuario_actual
    _usuario_actual = usuario
    if usuario:
        print(f"👤 Usuario establecido: {usuario.get('username')}")

def obtener_usuario_actual():
    """Devuelve el usuario actual."""
    return _usuario_actual

def cerrar_sesion():
    """Cierra la sesión actual."""
    global _usuario_actual
    if _usuario_actual:
        print(f"🔒 Cerrando sesión de: {_usuario_actual.get('username')}")
    _usuario_actual = None

def es_admin():
    """Verifica si el usuario actual es administrador."""
    return _usuario_actual and _usuario_actual.get("rol") == "admin"

def es_preventista():
    """Verifica si el usuario actual es preventista."""
    return _usuario_actual and _usuario_actual.get("rol") == "preventista"

def obtener_preventista_id():
    """Devuelve el ID del preventista actual."""
    return _usuario_actual.get("preventista_id") if _usuario_actual else None