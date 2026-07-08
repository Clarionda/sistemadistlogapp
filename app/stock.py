from database import ejecutar_consulta

def descontar_stock(producto_id, cantidad):
    ejecutar_consulta(
        "UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ? AND activo = 1",
        (cantidad, producto_id),
        commit=True
    )

def obtener_stock(producto_id):
    filas = ejecutar_consulta("SELECT stock_actual FROM productos WHERE id = ?", (producto_id,))
    return filas[0]["stock_actual"] if filas else 0

def obtener_stock_por_codigo(codigo_producto):
    filas = ejecutar_consulta("SELECT stock_actual FROM productos WHERE codigo_producto = ? AND activo = 1", (codigo_producto,))
    return filas[0]["stock_actual"] if filas else 0
