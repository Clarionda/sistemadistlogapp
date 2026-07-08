"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de mapas con NiceGUI - Sincronización mejorada con PyTurso
"""

from nicegui import ui, app
from database import ejecutar_consulta, sincronizar_tabla_completa
from auth import obtener_preventista_id, obtener_usuario_actual
from pedidos import agregar_al_carrito, obtener_carrito, crear_nota_venta, sincronizar_nota_inmediata


def mostrar_mapa():
    """Crea un mapa Leaflet con marcadores de clientes asignados al preventista."""
    usuario = obtener_usuario_actual()
    if not usuario:
        ui.notify("Debe iniciar sesión", type="warning")
        return
    
    preventista_id = usuario.get("preventista_id")
    if not preventista_id and not usuario.get("rol") == "admin":
        ui.notify("Usuario no asociado a un preventista", type="warning")
        return
    
    # ✅ Sincronizar clientes antes de mostrar
    try:
        from turso_client import bajar_tabla_pyturso
        bajar_tabla_pyturso('clientes')
    except ImportError:
        from sync import bajar_tabla
        bajar_tabla('clientes')
    except Exception as e:
        print(f"⚠️ Error sincronizando clientes: {e}")
    
    # Obtener clientes
    if usuario["rol"] == "admin":
        clientes = ejecutar_consulta(
            "SELECT id, razon_social, latitud, longitud FROM clientes WHERE latitud IS NOT NULL AND longitud IS NOT NULL"
        )
    else:
        clientes = ejecutar_consulta(
            "SELECT id, razon_social, latitud, longitud FROM clientes WHERE preventista_id = ? AND latitud IS NOT NULL AND longitud IS NOT NULL",
            (preventista_id,)
        )
    
    if not clientes:
        ui.label("No hay clientes con coordenadas cargadas.").classes("text-grey")
        return
    
    # ✅ Mostrar contador de clientes
    ui.label(f"📍 {len(clientes)} clientes en el mapa").classes("text-sm text-grey")
    
    # Generar HTML/JavaScript para el mapa
    markers_js = []
    for c in clientes:
        markers_js.append(f"""
            L.marker([{c['latitud']}, {c['longitud']}]).addTo(map)
            .bindPopup(`
                <b>{c['razon_social']}</b><br>
                <button onclick="window.dispatchEvent(new CustomEvent('abrir_catalogo', {{detail: {{cliente_id: {c['id']}}}}})">Ver catálogo</button>
            `);
        """)
    
    js_code = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="height: 500px;"></div>
    <script>
        var map = L.map('map').setView([-38.4161, -63.6167], 5);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap'
        }}).addTo(map);
        {chr(10).join(markers_js)}
        window.addEventListener('abrir_catalogo', (e) => {{
            const cliente_id = e.detail.cliente_id;
            fetch('/_nicegui/open_client_catalog?cliente_id=' + cliente_id);
        }});
    </script>
    """
    ui.html(js_code)
    
    # ✅ Botón para sincronizar clientes
    with ui.row():
        ui.button("🔄 Sincronizar clientes", on_click=lambda: _sincronizar_clientes())
        ui.button("📍 Refrescar mapa", on_click=lambda: _refrescar_mapa())


def _sincronizar_clientes():
    """Sincroniza clientes con PyTurso"""
    try:
        from turso_client import bajar_tabla_pyturso
        filas = bajar_tabla_pyturso('clientes')
        ui.notify(f"✅ Clientes sincronizados: {filas} filas", type="positive")
    except ImportError:
        from sync import bajar_tabla
        bajar_tabla('clientes')
        ui.notify("✅ Clientes sincronizados (HTTP)", type="positive")
    except Exception as e:
        ui.notify(f"❌ Error: {e}", type="negative")


def _refrescar_mapa():
    """Refresca el mapa"""
    ui.navigate.to('/mapa')


# Endpoint para abrir el catálogo desde el mapa
@ui.page('/abrir_catalogo/{cliente_id}')
async def abrir_catalogo(cliente_id: int):
    from nicegui import ui
    usuario = obtener_usuario_actual()
    if not usuario:
        ui.label("No autorizado")
        return
    
    cliente = ejecutar_consulta("SELECT id, razon_social FROM clientes WHERE id = ?", (cliente_id,))
    if not cliente:
        ui.label("Cliente no encontrado")
        return
    
    cliente = cliente[0]
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Catálogo para {cliente['razon_social']}").classes("text-h6")
        
        busqueda = ui.input("Buscar producto")
        productos_container = ui.column()
        
        def mostrar_productos():
            productos_container.clear()
            texto = busqueda.value
            if texto:
                prods = ejecutar_consulta(
                    "SELECT id, codigo, descripcion, precio_venta, stock_actual FROM productos WHERE descripcion LIKE ? AND activo=1 LIMIT 30",
                    (f"%{texto}%",)
                )
            else:
                prods = ejecutar_consulta(
                    "SELECT id, codigo, descripcion, precio_venta, stock_actual FROM productos WHERE activo=1 LIMIT 30"
                )
            
            for p in prods:
                with productos_container:
                    with ui.row().classes("items-center w-full justify-between"):
                        ui.label(f"{p['codigo']} - {p['descripcion']}").classes("text-sm")
                        stock_text = f"Stock: {p['stock_actual']}" if p['stock_actual'] > 0 else "⚠️ Sin stock"
                        ui.label(stock_text).classes("text-xs text-grey")
                        cantidad = ui.number(value=1, min=0.01, step=0.5).classes("w-20")
                        btn = ui.button("Agregar", on_click=lambda pid=p['id'], cant=cantidad: _agregar_producto(pid, cant.value))
                        if p['stock_actual'] <= 0:
                            btn.disable()
        
        busqueda.on_change(mostrar_productos)
        mostrar_productos()
        
        ui.separator()
        with ui.row():
            ui.button("Finalizar pedido", on_click=lambda: _finalizar_pedido(dialog, cliente_id), color="primary")
            ui.button("Cancelar", on_click=dialog.close)


def _agregar_producto(producto_id, cantidad):
    """Agrega producto al carrito desde NiceGUI"""
    from pedidos import agregar_al_carrito
    usuario = obtener_usuario_actual()
    if not usuario:
        ui.notify("No autorizado", type="negative")
        return
    
    producto = ejecutar_consulta("SELECT codigo, precio_venta FROM productos WHERE id = ?", (producto_id,))
    if not producto:
        ui.notify("Producto no encontrado", type="negative")
        return
    
    # ✅ Usar codigo_producto, no ID
    agregar_al_carrito(usuario["id"], None, producto[0]['codigo'], cantidad, producto[0]['precio_venta'])
    ui.notify(f"✅ Agregado {cantidad} unidades", type="positive")


def _finalizar_pedido(dialog, cliente_id):
    """Finaliza pedido con sincronización PyTurso"""
    from pedidos import crear_nota_venta
    usuario = obtener_usuario_actual()
    if not usuario:
        ui.notify("No autorizado", type="negative")
        return
    
    nota_id = crear_nota_venta(usuario["id"], usuario.get("preventista_id"), cliente_id)
    if nota_id:
        ui.notify(f"✅ Nota de venta creada y sincronizada", type="positive")
        dialog.close()
    else:
        ui.notify("❌ Error al crear nota de venta", type="negative")