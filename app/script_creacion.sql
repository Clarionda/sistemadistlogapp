-- ============================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS - VERSIÓN UUID
-- ============================================================
-- 
-- 📌 TODAS LAS TABLAS USAN UUID (TEXT) COMO CLAVE PRIMARIA
-- 📌 COMPATIBLE CON: Central (Escritorio) | App (Tablet) | Turso
-- 📌 FLUJO DE SINCRONIZACIÓN:
--    - Central → Turso: clientes, productos, preventistas, categorias, lotes, facturas
--    - Turso → Central: notas_venta, nota_venta_detalle, visitas_clientes
--    - App → Turso: notas_venta (con codigo_producto, NO producto_id)
--    - Turso → App: clientes, productos, preventistas, categorias, lotes
-- ============================================================

-- ============================================================
-- 1. PARÁMETROS GENERALES (SOLO Central / App)
-- ============================================================
-- Esta tabla es la ÚNICA que NO usa UUID porque es un singleton (id=1)
-- Contiene configuración de la empresa, facturación y geolocalización

CREATE TABLE IF NOT EXISTS parametros (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    moneda TEXT NOT NULL DEFAULT 'ARS',
    nombre_distribuidora TEXT,
    direccion TEXT,
    telefono1 TEXT,
    telefono2 TEXT,
    whatsapp TEXT,
    email TEXT,
    logo BLOB,
    encabezado_factura TEXT,
    encabezado_reporte TEXT,
    tasa_municipal_porcentaje REAL DEFAULT 0.0,
    punto_venta TEXT DEFAULT '0001',
    ultimo_numero_factura INTEGER DEFAULT 1,
    calle TEXT,
    numero TEXT,
    localidad TEXT,
    provincia TEXT,
    pais TEXT DEFAULT 'Argentina',
    latitud REAL,
    longitud REAL,
    escala_visual REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. CATEGORÍAS - UUID
-- ============================================================
-- Clasificación de productos (ej: Bebidas, Almacén, Limpieza)
-- Se sincroniza: Central → Turso → App

CREATE TABLE IF NOT EXISTS categorias (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_categorias_nombre ON categorias(nombre);
CREATE INDEX IF NOT EXISTS idx_categorias_activo ON categorias(activo);

-- ============================================================
-- 3. PRODUCTOS - UUID
-- ============================================================
-- Productos con stock, precios e imágenes
-- codigo_producto: identificador único GLOBAL (usado por la App)
-- Se sincroniza: Central → Turso → App (SIN fotos para ahorrar ancho de banda)

CREATE TABLE IF NOT EXISTS productos (
    id TEXT PRIMARY KEY,
    codigo_producto TEXT UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    precio_costo REAL DEFAULT 0,
    precio_venta REAL DEFAULT 0,
    stock_actual REAL DEFAULT 0,
    stock_critico REAL DEFAULT 0,
    unidad_medida TEXT DEFAULT 'unidad',
    categoria_id TEXT REFERENCES categorias(id),
    foto BLOB,
    url_foto TEXT,
    detalle TEXT,
    precio_oferta REAL,
    destacado INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para productos
CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo_producto);
CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(descripcion);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);

-- ============================================================
-- 4. LOTES - UUID
-- ============================================================
-- Trazabilidad de stock por lotes (FIFO - First In, First Out)
-- Se sincroniza: Central → Turso → App

CREATE TABLE IF NOT EXISTS lotes (
    id TEXT PRIMARY KEY,
    producto_id TEXT NOT NULL REFERENCES productos(id),
    codigo_producto TEXT,
    numero_lote TEXT,
    fecha_vencimiento DATE NOT NULL,
    cantidad_inicial REAL NOT NULL,
    cantidad_actual REAL NOT NULL,
    fecha_ingreso DATE DEFAULT (date('now')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para lotes
CREATE INDEX IF NOT EXISTS idx_lotes_producto ON lotes(producto_id);
CREATE INDEX IF NOT EXISTS idx_lotes_codigo ON lotes(codigo_producto);
CREATE INDEX IF NOT EXISTS idx_lotes_vencimiento ON lotes(fecha_vencimiento);

-- ============================================================
-- 5. CLIENTES - UUID
-- ============================================================
-- Clientes de la distribuidora con cuenta corriente
-- Se sincroniza: Central → Turso → App
-- La App SOLO LEE clientes (no los crea)

CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY,
    razon_social TEXT NOT NULL,
    cuit TEXT UNIQUE,
    condicion_iva TEXT CHECK(condicion_iva IN ('RI','M','EX','CF','MT')) DEFAULT 'RI',
    domicilio TEXT,
    telefono TEXT,
    whatsapp TEXT,
    email TEXT,
    aplica_tasa_municipal BOOLEAN DEFAULT 0,
    limite_credito REAL DEFAULT 0,
    saldo_cuenta_corriente REAL DEFAULT 0,
    fecha_alta DATE DEFAULT (date('now')),
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    latitud REAL,
    longitud REAL,
    preventista_id TEXT,
    localidad TEXT,
    provincia TEXT,
    calle TEXT,
    numero TEXT
);

-- Índices para clientes
CREATE INDEX IF NOT EXISTS idx_clientes_cuit ON clientes(cuit);
CREATE INDEX IF NOT EXISTS idx_clientes_razon_social ON clientes(razon_social);
CREATE INDEX IF NOT EXISTS idx_clientes_preventista ON clientes(preventista_id);

-- ============================================================
-- 6. PREVENTISTAS - UUID
-- ============================================================
-- Vendedores/representantes que toman pedidos
-- Se sincroniza: Central → Turso → App

CREATE TABLE IF NOT EXISTS preventistas (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    legajo TEXT UNIQUE,
    telefono TEXT,
    email TEXT,
    zona TEXT,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- ============================================================
-- 7. USUARIOS - UUID
-- ============================================================
-- Usuarios del sistema con autenticación
-- Se sincroniza: Central → Turso → App
-- La App USA los usuarios para login

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('preventista','admin','cliente')) DEFAULT 'preventista',
    preventista_id TEXT REFERENCES preventistas(id),
    cliente_id TEXT REFERENCES clientes(id),
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);

-- ============================================================
-- 8. NOTAS DE VENTA - UUID
-- ============================================================
-- Pedidos tomados por los preventistas en la App
-- Se sincroniza: App → Turso → Central
-- La App CREA notas, la Central las PROCESA (facturación)

CREATE TABLE IF NOT EXISTS notas_venta (
    id TEXT PRIMARY KEY,
    preventista_id TEXT NOT NULL REFERENCES preventistas(id),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    fecha DATE DEFAULT (date('now')),
    numero_nota TEXT UNIQUE,
    total REAL DEFAULT 0,
    observaciones TEXT,
    estado TEXT DEFAULT 'PENDIENTE',
    procesado_central BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para notas de venta
CREATE INDEX IF NOT EXISTS idx_notas_venta_estado ON notas_venta(estado);
CREATE INDEX IF NOT EXISTS idx_notas_venta_fecha ON notas_venta(fecha);
CREATE INDEX IF NOT EXISTS idx_notas_venta_cliente ON notas_venta(cliente_id);
CREATE INDEX IF NOT EXISTS idx_notas_venta_procesado ON notas_venta(procesado_central);

-- ============================================================
-- 9. NOTA VENTA DETALLE - UUID
-- ============================================================
-- Detalle de los productos en las notas
-- 🔑 IMPORTANTE: Usa codigo_producto (NO producto_id) para evitar conflictos
-- La App envía codigo_producto, Central lo convierte a producto_id

CREATE TABLE IF NOT EXISTS nota_venta_detalle (
    id TEXT PRIMARY KEY,
    nota_venta_id TEXT NOT NULL REFERENCES notas_venta(id),
    producto_id TEXT,
    codigo_producto TEXT NOT NULL,
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para detalle de notas
CREATE INDEX IF NOT EXISTS idx_nota_detalle_nota ON nota_venta_detalle(nota_venta_id);
CREATE INDEX IF NOT EXISTS idx_nota_detalle_producto ON nota_venta_detalle(producto_id);
CREATE INDEX IF NOT EXISTS idx_nota_detalle_codigo ON nota_venta_detalle(codigo_producto);

-- ============================================================
-- 10. FACTURAS - UUID (SOLO Central)
-- ============================================================
-- Facturas emitidas desde la Central
-- Se sincroniza: Central → Turso (para consulta desde App)

CREATE TABLE IF NOT EXISTS facturas (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    preventista_id TEXT REFERENCES preventistas(id),
    tipo_comprobante TEXT CHECK(tipo_comprobante IN ('A','B','C','X')) DEFAULT 'B',
    numero_factura TEXT NOT NULL UNIQUE,
    fecha DATE DEFAULT (date('now')),
    subtotal REAL DEFAULT 0,
    iva REAL DEFAULT 0,
    tasa_municipal REAL DEFAULT 0,
    total REAL DEFAULT 0,
    observaciones TEXT,
    nota_venta_id TEXT REFERENCES notas_venta(id),
    estado TEXT DEFAULT 'EMITIDA',
    saldo_anterior_cliente REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para facturas
CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha);
CREATE INDEX IF NOT EXISTS idx_facturas_estado ON facturas(estado);
CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura);

-- ============================================================
-- 11. FACTURA DETALLE - UUID (SOLO Central)
-- ============================================================
-- Detalle de productos facturados

CREATE TABLE IF NOT EXISTS factura_detalle (
    id TEXT PRIMARY KEY,
    factura_id TEXT NOT NULL REFERENCES facturas(id),
    producto_id TEXT NOT NULL REFERENCES productos(id),
    codigo_producto TEXT NOT NULL,
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para factura detalle
CREATE INDEX IF NOT EXISTS idx_factura_detalle_factura ON factura_detalle(factura_id);
CREATE INDEX IF NOT EXISTS idx_factura_detalle_producto ON factura_detalle(producto_id);
CREATE INDEX IF NOT EXISTS idx_factura_detalle_codigo ON factura_detalle(codigo_producto);

-- ============================================================
-- 12. CUENTA CORRIENTE - UUID (SOLO Central)
-- ============================================================
-- Movimientos de cuenta corriente de los clientes

CREATE TABLE IF NOT EXISTS cuenta_corriente_movimientos (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    fecha DATE DEFAULT (date('now')),
    tipo_movimiento TEXT CHECK(tipo_movimiento IN ('FACTURA','COBRO','NOTA_CREDITO','AJUSTE','ANULACION','REVERSO_COBRO')),
    referencia_id TEXT,
    importe REAL NOT NULL,
    saldo_resultante REAL NOT NULL,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Índices para cuenta corriente
CREATE INDEX IF NOT EXISTS idx_movimientos_cliente ON cuenta_corriente_movimientos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON cuenta_corriente_movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_movimientos_referencia ON cuenta_corriente_movimientos(referencia_id);

-- ============================================================
-- 13. COBROS - UUID (SOLO Central)
-- ============================================================
-- Cobros registrados en la Central

CREATE TABLE IF NOT EXISTS cobros (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    fecha DATE DEFAULT (date('now')),
    importe REAL NOT NULL,
    medio_pago TEXT,
    tipo_pago TEXT DEFAULT 'EFECTIVO',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- ============================================================
-- 14. CHEQUES - UUID (SOLO Central)
-- ============================================================
-- Cheques recibidos de clientes

CREATE TABLE IF NOT EXISTS cheques (
    id TEXT PRIMARY KEY,
    cobro_id TEXT NOT NULL REFERENCES cobros(id),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    banco TEXT NOT NULL,
    numero_cheque TEXT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    importe REAL NOT NULL,
    estado TEXT DEFAULT 'EN_CARTERA',
    fecha_acreditacion DATE,
    vendido_a TEXT,
    factura_ids TEXT,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- ============================================================
-- 15. POSICIONES GPS - UUID (SOLO App)
-- ============================================================
-- Ubicación de los preventistas en tiempo real
-- Se sincroniza: App → Turso → Central

CREATE TABLE IF NOT EXISTS posiciones_preventistas (
    id TEXT PRIMARY KEY,
    preventista_id TEXT NOT NULL REFERENCES preventistas(id),
    latitud REAL NOT NULL,
    longitud REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para posiciones
CREATE INDEX IF NOT EXISTS idx_posiciones_preventista ON posiciones_preventistas(preventista_id);
CREATE INDEX IF NOT EXISTS idx_posiciones_timestamp ON posiciones_preventistas(timestamp);

-- ============================================================
-- 16. VISITAS A CLIENTES - UUID (SOLO App)
-- ============================================================
-- Registro de visitas realizadas por preventistas
-- Se sincroniza: App → Turso → Central

CREATE TABLE IF NOT EXISTS visitas_clientes (
    id TEXT PRIMARY KEY,
    preventista_id TEXT NOT NULL REFERENCES preventistas(id),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitud REAL,
    longitud REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para visitas
CREATE INDEX IF NOT EXISTS idx_visitas_preventista ON visitas_clientes(preventista_id);
CREATE INDEX IF NOT EXISTS idx_visitas_cliente ON visitas_clientes(cliente_id);

-- ============================================================
-- 17. SINCRONIZACIÓN
-- ============================================================
-- Tablas para control de sincronización con Turso

-- Control de última sincronización (para saber qué datos nuevos hay)
CREATE TABLE IF NOT EXISTS sync_log (
    tabla TEXT PRIMARY KEY,
    last_timestamp TEXT DEFAULT '1970-01-01T00:00:00'
);

-- Control de última sincronización inversa
CREATE TABLE IF NOT EXISTS sync_log_reverse (
    tabla TEXT PRIMARY KEY,
    last_timestamp TEXT DEFAULT '1970-01-01T00:00:00'
);

-- Cola de operaciones pendientes para sincronizar
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    args TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retries INTEGER DEFAULT 0,
    last_error TEXT,
    next_retry TIMESTAMP
);

-- Índice para la cola
CREATE INDEX IF NOT EXISTS idx_sync_queue_next_retry ON sync_queue(next_retry);

-- Historial de sincronización
CREATE TABLE IF NOT EXISTS sync_log_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT,
    args TEXT,
    success BOOLEAN,
    error TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Registro de conflictos de sincronización
CREATE TABLE IF NOT EXISTS sync_conflictos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla TEXT NOT NULL,
    registro_id TEXT NOT NULL,
    version_local INTEGER,
    version_remota INTEGER,
    resolucion TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para conflictos
CREATE INDEX IF NOT EXISTS idx_sync_conflictos_tabla ON sync_conflictos(tabla);
CREATE INDEX IF NOT EXISTS idx_sync_conflictos_timestamp ON sync_conflictos(timestamp);

-- ============================================================
-- 18. PEDIDOS PARA ARMAR (Central)
-- ============================================================
-- Historial de pedidos procesados (armados)
-- Se sincroniza: Central → Turso (solo para registro)

CREATE TABLE IF NOT EXISTS pedidos_procesados (
    id TEXT PRIMARY KEY,
    factura_id TEXT NOT NULL UNIQUE REFERENCES facturas(id),
    fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    procesado_por TEXT,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para pedidos procesados
CREATE INDEX IF NOT EXISTS idx_pedidos_procesados_factura ON pedidos_procesados(factura_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_procesados_fecha ON pedidos_procesados(fecha_procesado);

-- ============================================================
-- 19. TRIGGERS DE ACTUALIZACIÓN (updated_at)
-- ============================================================
-- Actualizan automáticamente updated_at en cada modificación

CREATE TRIGGER IF NOT EXISTS update_parametros_updated_at AFTER UPDATE ON parametros
BEGIN UPDATE parametros SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_categorias_updated_at AFTER UPDATE ON categorias
BEGIN UPDATE categorias SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_productos_updated_at AFTER UPDATE ON productos
BEGIN UPDATE productos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_lotes_updated_at AFTER UPDATE ON lotes
BEGIN UPDATE lotes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_clientes_updated_at AFTER UPDATE ON clientes
BEGIN UPDATE clientes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_preventistas_updated_at AFTER UPDATE ON preventistas
BEGIN UPDATE preventistas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_usuarios_updated_at AFTER UPDATE ON usuarios
BEGIN UPDATE usuarios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_notas_venta_updated_at AFTER UPDATE ON notas_venta
BEGIN UPDATE notas_venta SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_nota_venta_detalle_updated_at AFTER UPDATE ON nota_venta_detalle
BEGIN UPDATE nota_venta_detalle SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_facturas_updated_at AFTER UPDATE ON facturas
BEGIN UPDATE facturas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_factura_detalle_updated_at AFTER UPDATE ON factura_detalle
BEGIN UPDATE factura_detalle SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_cuenta_corriente_movimientos_updated_at AFTER UPDATE ON cuenta_corriente_movimientos
BEGIN UPDATE cuenta_corriente_movimientos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_cobros_updated_at AFTER UPDATE ON cobros
BEGIN UPDATE cobros SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_cheques_updated_at AFTER UPDATE ON cheques
BEGIN UPDATE cheques SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- ============================================================
-- 20. DATOS INICIALES MÍNIMOS
-- ============================================================
-- 🔑 Usuario admin con UUID fijo
-- 🔑 Parámetros por defecto
-- 🔑 Control de sincronización

-- 20.1 USUARIO ADMIN
-- Contraseña: admin (hash SHA256)
INSERT OR IGNORE INTO usuarios (id, username, password_hash, rol) 
VALUES ('00000000-0000-0000-0000-000000000001', 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin');

-- 20.2 PARÁMETROS GENERALES
INSERT OR IGNORE INTO parametros (
    id, moneda, nombre_distribuidora, punto_venta, ultimo_numero_factura, escala_visual
) VALUES (
    1, 'ARS', 'Mi Distribuidora', '0001', 1, 1.0
);

-- 20.3 CONTROL DE SINCRONIZACIÓN - SUBIDA (Central → Turso)
INSERT OR IGNORE INTO sync_log (tabla) VALUES 
('clientes'),
('productos'),
('preventistas'),
('categorias'),
('lotes'),
('usuarios'),
('facturas'),
('factura_detalle'),
('cobros'),
('cheques'),
('cuenta_corriente_movimientos'),
('pedidos_procesados');

-- 20.4 CONTROL DE SINCRONIZACIÓN - BAJADA (Turso → Central)
INSERT OR IGNORE INTO sync_log_reverse (tabla) VALUES 
('notas_venta'),
('nota_venta_detalle'),
('visitas_clientes'),
('posiciones_preventistas');

-- ============================================================
-- FIN DEL SCRIPT
-- ============================================================
-- BASE DE DATOS LIMPIA:
--   ✅ Todas las tablas con UUID
--   ✅ Usuario admin con UUID fijo
--   ✅ Parámetros mínimos configurados
--   ✅ Control de sincronización inicializado
--   ❌ SIN datos de muestra (clientes, productos, etc.)
-- ============================================================