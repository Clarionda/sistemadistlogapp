"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de gestión de pedidos (carrito y notas de venta)
Mantiene el carrito de compras en memoria y genera notas de venta en la base local.
NOTA: Usa codigo_producto (TEXT) para Turso, NO producto_id.
"""

import uuid
import threading
from datetime import datetime
from database import ejecutar_consulta
from stock import descontar_stock

carritos = {}

def obtener_carrito(usuario_id, cliente_id):
    if usuario_id not in carritos:
        carritos[usuario_id] = {}
    return carritos[usuario_id].setdefault(cliente_id, [])

def vaciar_carrito(usuario_id, cliente_id):
    if usuario_id in carritos and cliente_id in carritos[usuario_id]:
        carritos[usuario_id][cliente_id] = []

def agregar_al_carrito(usuario_id, cliente_id, codigo_producto, cantidad, precio_unitario):
    """
    Agrega un producto al carrito usando CODIGO de producto (no ID).
    """
    carro = obtener_carrito(usuario_id, cliente_id)
    for item in carro:
        if item["codigo_producto"] == codigo_producto:
            item["cantidad"] += cantidad
            return
    carro.append({
        "codigo_producto": codigo_producto,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario
    })

def generar_numero_nota():
    """
    Genera un número de nota ÚNICO.
    """
    fecha_actual = datetime.now()
    prefijo = f"NOTA-{fecha_actual.strftime('%Y%m')}"
    
    local = ejecutar_consulta(
        "SELECT numero_nota FROM notas_venta WHERE numero_nota LIKE ? ORDER BY created_at DESC LIMIT 1",
        (f"{prefijo}%",)
    )
    
    try:
        from sync import _consultar_turso
        remoto = _consultar_turso(
            "SELECT numero_nota FROM notas_venta WHERE numero_nota LIKE ? ORDER BY created_at DESC LIMIT 1",
            [f"{prefijo}%"]
        )
    except Exception as e:
        print(f"⚠️ Error consultando Turso: {e}")
        remoto = []
    
    ultimo_num = 0
    
    if local and local[0].get("numero_nota"):
        try:
            num_str = local[0]["numero_nota"].split("-")[-1]
            ultimo_num = max(ultimo_num, int(num_str))
        except:
            pass
    
    if remoto and remoto[0].get("numero_nota"):
        try:
            num_str = remoto[0]["numero_nota"].split("-")[-1]
            ultimo_num = max(ultimo_num, int(num_str))
        except:
            pass
    
    nuevo_num = ultimo_num + 1
    return f"{prefijo}-{str(nuevo_num).zfill(4)}"

def subir_nota_inmediata(nota_id):
    def _subir():
        try:
            from sync import subir_tabla
            print(f"🔄 Subiendo nota de venta a Turso...")
            subir_tabla('notas_venta')
            subir_tabla('nota_venta_detalle')
            print(f"✅ Nota de venta enviada a Turso correctamente")
        except Exception as e:
            print(f"❌ Error al subir nota: {e}")
    threading.Thread(target=_subir, daemon=True).start()

def crear_nota_venta(usuario_id, preventista_id, cliente_id):
    carro = obtener_carrito(usuario_id, cliente_id)
    if not carro:
        print("❌ Carrito vacío")
        return None
    
    total = sum(item["cantidad"] * item["precio_unitario"] for item in carro)
    nota_id = str(uuid.uuid4())
    numero_nota = generar_numero_nota()
    
    if preventista_id is None:
        from auth import obtener_usuario_actual
        usuario = obtener_usuario_actual()
        if usuario:
            preventista_id = usuario.get('preventista_id', 1)
        else:
            preventista_id = 1
    
    check = ejecutar_consulta("SELECT id FROM preventistas WHERE id = ?", (preventista_id,))
    if not check:
        preventista_id = 1
    
    # ✅ CORREGIDO: usar codigo_producto
    productos_validos = []
    for item in carro:
        producto = ejecutar_consulta(
            "SELECT id FROM productos WHERE codigo_producto = ? AND activo = 1",
            (item["codigo_producto"],)
        )
        if producto:
            productos_validos.append({
                'codigo': item["codigo_producto"],
                'producto_id': producto[0]["id"],
                'cantidad': item["cantidad"],
                'precio_unitario': item["precio_unitario"]
            })
        else:
            print(f"⚠️ Producto con código {item['codigo_producto']} no encontrado")
    
    if not productos_validos:
        print("❌ No hay productos válidos en el carrito")
        return None
    
    # Insertar nota de venta
    ejecutar_consulta("""
        INSERT INTO notas_venta (id, preventista_id, cliente_id, fecha, numero_nota, total, estado, created_at)
        VALUES (?, ?, ?, date('now'), ?, ?, 'PENDIENTE', CURRENT_TIMESTAMP)
    """, (nota_id, preventista_id, cliente_id, numero_nota, total), commit=True)
    
    # Insertar detalles con codigo_producto
    for item in productos_validos:
        detalle_id = str(uuid.uuid4())
        
        ejecutar_consulta("""
            INSERT INTO nota_venta_detalle (id, nota_venta_id, producto_id, codigo_producto, cantidad, precio_unitario, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (detalle_id, nota_id, item['producto_id'], item['codigo'], item['cantidad'], item['precio_unitario']), commit=True)
        
        descontar_stock(item['producto_id'], item['cantidad'])
    
    vaciar_carrito(usuario_id, cliente_id)
    
    # FORZAR sincronización inmediata
    print(f"📤 Subiendo nota {numero_nota} a Turso...")
    from sync import subir_tabla
    subir_tabla('notas_venta')
    subir_tabla('nota_venta_detalle')
    print(f"✅ Nota {numero_nota} creada y sincronizada")
    
    return nota_id
