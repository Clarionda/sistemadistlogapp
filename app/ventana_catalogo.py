"""
Código Crítico - Tercer Semestre - Año 2026
Ventana de catálogo - CON LISTA DE CARRITO VISIBLE
DIMENSIONES: 1200x800
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QWidget,
                             QGridLayout, QSpinBox, QMessageBox, QFrame,
                             QListWidget, QListWidgetItem, QSizePolicy,
                             QSplitter)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QFont, QPalette, QIcon, QPainter, QBrush, QLinearGradient

from database import ejecutar_consulta
from pedidos import agregar_al_carrito, obtener_carrito, vaciar_carrito
from auth import obtener_usuario_actual
from ventana_resumen_compra import ResumenCompraDialog

# ============================================================
# CONSTANTES DE DISEÑO
# ============================================================

COLOR_PRIMARY = "#2563EB"
COLOR_PRIMARY_DARK = "#1D4ED8"
COLOR_SUCCESS = "#22C55E"
COLOR_DANGER = "#EF4444"
COLOR_WARNING = "#F59E0B"
COLOR_BG = "#F1F5F9"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#1E293B"
COLOR_TEXT_SECONDARY = "#64748B"
COLOR_BORDER = "#E2E8F0"


def mostrar_mensaje(titulo, mensaje, icono=QMessageBox.Icon.Information, botones=QMessageBox.StandardButton.Ok):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensaje)
    msg.setIcon(icono)
    msg.setStandardButtons(botones)
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: {COLOR_BG};
        }}
        QMessageBox QLabel {{
            color: {COLOR_TEXT};
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            font-weight: 600;
            font-size: 13px;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {COLOR_PRIMARY_DARK};
        }}
    """)
    return msg.exec()


# ============================================================
# TARJETA DE PRODUCTO
# ============================================================

class TarjetaProducto(QFrame):
    agregado = pyqtSignal()
    
    def __init__(self, producto, cliente_id, parent=None):
        super().__init__(parent)
        self.producto = producto
        self.cliente_id = cliente_id
        self.dialog_parent = parent
        
        self.setObjectName("tarjeta")
        self.setStyleSheet(f"""
            #tarjeta {{
                background-color: {COLOR_CARD};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 4px;
            }}
            #tarjeta:hover {{
                border: 2px solid {COLOR_PRIMARY};
                background-color: #FAFBFF;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)
        
        # === IMAGEN ===
        self.img_container = QWidget()
        self.img_container.setFixedHeight(120)
        self.img_container.setStyleSheet(f"""
            background-color: {COLOR_BG};
            border-radius: 8px;
        """)
        img_layout = QVBoxLayout(self.img_container)
        img_layout.setContentsMargins(4, 4, 4, 4)
        
        self.label_imagen = QLabel()
        self.label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_imagen.setFixedSize(100, 100)
        self.label_imagen.setScaledContents(True)
        self.label_imagen.setStyleSheet("border-radius: 6px; background: transparent;")
        img_layout.addWidget(self.label_imagen, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_container)
        
        self.mostrar_imagen()
        
        # === CÓDIGO ===
        codigo = self.producto.get('codigo_producto', '')
        lbl_codigo = QLabel(codigo if codigo else 'Sin código')
        lbl_codigo.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 600;
            color: {COLOR_PRIMARY};
            background-color: #EFF6FF;
            padding: 2px 8px;
            border-radius: 10px;
        """)
        layout.addWidget(lbl_codigo)
        
        # === DESCRIPCIÓN ===
        lbl_desc = QLabel(self.producto.get('descripcion', 'Sin descripción'))
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLOR_TEXT};
            margin-top: 2px;
            min-height: 32px;
        """)
        layout.addWidget(lbl_desc)
        
        # === STOCK ===
        stock_actual = self.producto.get('stock_actual', 0)
        stock_color = COLOR_SUCCESS if stock_actual > 10 else (COLOR_WARNING if stock_actual > 0 else COLOR_DANGER)
        stock_text = "En stock" if stock_actual > 10 else (f"Quedan {stock_actual}" if stock_actual > 0 else "Sin stock")
        
        lbl_stock = QLabel(f"{'🟢' if stock_actual > 0 else '🔴'} {stock_text}")
        lbl_stock.setStyleSheet(f"""
            font-size: 10px;
            color: {stock_color};
            font-weight: 500;
        """)
        layout.addWidget(lbl_stock)
        
        # === PRECIO ===
        precio = self.producto.get('precio_venta', 0)
        lbl_precio = QLabel(f"${precio:.2f}")
        lbl_precio.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 800;
            color: {COLOR_PRIMARY};
            margin-top: 2px;
        """)
        layout.addWidget(lbl_precio)
        
        # === CANTIDAD Y BOTÓN ===
        cantidad_layout = QHBoxLayout()
        cantidad_layout.setSpacing(6)
        
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(999)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setFixedSize(50, 30)
        self.spin_cantidad.setStyleSheet(f"""
            QSpinBox {{
                border: 2px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 2px 4px;
                font-size: 12px;
                font-weight: 600;
                background: white;
                color: {COLOR_TEXT};
            }}
            QSpinBox:focus {{
                border-color: {COLOR_PRIMARY};
            }}
        """)
        cantidad_layout.addWidget(self.spin_cantidad)
        
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar.setFixedHeight(30)
        
        if stock_actual <= 0:
            btn_agregar.setEnabled(False)
            btn_agregar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #CBD5E1;
                    color: #94A3B8;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 8px;
                }}
            """)
            btn_agregar.setText("Sin stock")
        else:
            btn_agregar.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_PRIMARY_DARK};
                }}
                QPushButton:pressed {{
                    background-color: #1A4BB7;
                }}
            """)
            btn_agregar.clicked.connect(self.agregar)
        
        cantidad_layout.addWidget(btn_agregar)
        layout.addLayout(cantidad_layout)
        
        self.setFixedWidth(180)
    
    def mostrar_imagen(self):
        """Carga la imagen del producto"""
        codigo = self.producto.get('codigo_producto')
        if not codigo:
            self._mostrar_placeholder()
            return
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        carpeta_fotos = os.path.join(base_dir, "imagenes_productos")
        
        extensiones = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        for ext in extensiones:
            ruta = os.path.join(carpeta_fotos, f"{codigo}{ext}")
            if os.path.exists(ruta):
                pixmap = QPixmap(ruta)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
                    self.label_imagen.setPixmap(pixmap)
                    return
        
        self._mostrar_placeholder()
    
    def _mostrar_placeholder(self):
        """Muestra placeholder si no hay imagen"""
        pixmap = QPixmap(100, 100)
        pixmap.fill(QColor(226, 232, 240))
        painter = QPainter(pixmap)
        painter.setPen(QColor(148, 163, 184))
        painter.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📦")
        painter.end()
        self.label_imagen.setPixmap(pixmap)
    
    def agregar(self):
        """Agrega producto al carrito"""
        usuario = obtener_usuario_actual()
        if not usuario:
            mostrar_mensaje("Error", "No hay usuario autenticado.", QMessageBox.Icon.Critical)
            return
        
        cantidad = self.spin_cantidad.value()
        stock_actual = self.producto.get('stock_actual', 0)
        
        if cantidad > stock_actual:
            mostrar_mensaje("Stock insuficiente", 
                          f"No hay suficiente stock.\nDisponible: {stock_actual}\nSolicitado: {cantidad}",
                          QMessageBox.Icon.Warning)
            return
        
        codigo = self.producto.get('codigo_producto')
        if not codigo:
            mostrar_mensaje("Error", "Producto sin código.", QMessageBox.Icon.Critical)
            return
        
        agregar_al_carrito(
            usuario['id'], 
            self.cliente_id, 
            codigo, 
            cantidad, 
            self.producto.get('precio_venta', 0)
        )
        
        self.agregado.emit()
        
        if self.dialog_parent:
            desc = self.producto.get('descripcion', 'Producto')
            self.dialog_parent.mostrar_notificacion(f"✅ {cantidad}x {desc[:20]}...")


# ============================================================
# VENTANA DE CATÁLOGO - 1200x800
# ============================================================

class CatalogoDialog(QDialog):
    def __init__(self, cliente_id, cliente_nombre, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.cliente_nombre = cliente_nombre
        self._busqueda_timer = QTimer()
        self._busqueda_timer.setSingleShot(True)
        self._busqueda_timer.timeout.connect(self.cargar_productos)
        
        # ✅ DIMENSIONES 1200x800
        self.setWindowTitle(f"Catálogo - {cliente_nombre}")
        self.setFixedSize(1200, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Pausar procesos del padre
        self._pausar_procesos_padre()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG};
                border-radius: 16px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        
        self._init_ui()
        QTimer.singleShot(100, self.cargar_productos)
        QTimer.singleShot(200, self.actualizar_carrito)
        
        self.drag_pos = None
        self.drag_start = None
    
    def _pausar_procesos_padre(self):
        parent = self.parent()
        if parent:
            if hasattr(parent, 'timer_marker'):
                if parent.timer_marker.isActive():
                    parent.timer_marker.stop()
            if hasattr(parent, 'catalogo_abierto'):
                parent.catalogo_abierto = True
    
    def _reanudar_procesos_padre(self):
        parent = self.parent()
        if parent:
            if hasattr(parent, 'timer_marker'):
                if not parent.timer_marker.isActive():
                    parent.timer_marker.start(500)
            if hasattr(parent, 'catalogo_abierto'):
                parent.catalogo_abierto = False
    
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG};
                border-radius: 16px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(10)
        
        # ===== BARRA SUPERIOR =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        lbl_title = QLabel("📦 Catálogo de Productos")
        lbl_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 800;
            color: {COLOR_TEXT};
        """)
        title_layout.addWidget(lbl_title)
        
        lbl_cliente = QLabel(f"Cliente: {self.cliente_nombre}")
        lbl_cliente.setStyleSheet(f"""
            font-size: 12px;
            color: {COLOR_TEXT_SECONDARY};
            font-weight: 500;
        """)
        title_layout.addWidget(lbl_cliente)
        
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(32, 32)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"""
            QPushButton {{
                background-color: #FEE2E2;
                color: {COLOR_DANGER};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLOR_DANGER};
                color: white;
            }}
        """)
        btn_cerrar.clicked.connect(self.close)
        header_layout.addWidget(btn_cerrar)
        container_layout.addLayout(header_layout)
        
        # ===== BÚSQUEDA =====
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("🔍 Buscar producto...")
        self.busqueda_input.setMinimumHeight(36)
        self.busqueda_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 0 14px;
                font-size: 13px;
                background-color: white;
                color: {COLOR_TEXT};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {COLOR_TEXT_SECONDARY};
            }}
        """)
        self.busqueda_input.textChanged.connect(self._on_busqueda_changed)
        search_layout.addWidget(self.busqueda_input)
        
        self.lbl_resultados = QLabel("Mostrando todos")
        self.lbl_resultados.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11px;
            padding: 0 8px;
        """)
        search_layout.addWidget(self.lbl_resultados)
        container_layout.addLayout(search_layout)
        
        # ===== SPLITTER: PRODUCTOS | CARRITO =====
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E2E8F0;
                border-radius: 2px;
                margin: 4px 0;
            }
            QSplitter::handle:hover {
                background-color: #2563EB;
            }
        """)
        
        # --- PANEL IZQUIERDO: PRODUCTOS ---
        productos_panel = QWidget()
        productos_layout = QVBoxLayout(productos_panel)
        productos_layout.setContentsMargins(0, 0, 0, 0)
        productos_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #F1F5F9;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.contenedor = QWidget()
        self.contenedor.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.contenedor)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        scroll_area.setWidget(self.contenedor)
        productos_layout.addWidget(scroll_area)
        
        splitter.addWidget(productos_panel)
        
        # --- PANEL DERECHO: CARRITO ---
        carrito_panel = QWidget()
        carrito_panel.setFixedWidth(300)  # Un poco más ancho para 1200
        carrito_panel.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        carrito_layout = QVBoxLayout(carrito_panel)
        carrito_layout.setContentsMargins(12, 12, 12, 12)
        carrito_layout.setSpacing(8)
        
        # Título del carrito
        carrito_header = QHBoxLayout()
        carrito_header.setSpacing(8)
        
        lbl_carrito_title = QLabel("🛒 Carrito")
        lbl_carrito_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {COLOR_TEXT};
        """)
        carrito_header.addWidget(lbl_carrito_title)
        carrito_header.addStretch()
        
        self.lbl_items_count = QLabel("0 items")
        self.lbl_items_count.setStyleSheet(f"""
            font-size: 12px;
            color: {COLOR_TEXT_SECONDARY};
            font-weight: 500;
        """)
        carrito_header.addWidget(self.lbl_items_count)
        
        carrito_layout.addLayout(carrito_header)
        
        # Lista de items del carrito
        self.lista_carrito = QListWidget()
        self.lista_carrito.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                background-color: {COLOR_BG};
                padding: 4px;
            }}
            QListWidget::item {{
                border: none;
                padding: 2px;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """)
        self.lista_carrito.setMinimumHeight(300)
        carrito_layout.addWidget(self.lista_carrito)
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLOR_BORDER}; max-height: 1px;")
        carrito_layout.addWidget(sep)
        
        # Total
        total_layout = QHBoxLayout()
        total_layout.setSpacing(8)
        
        lbl_total_text = QLabel("TOTAL")
        lbl_total_text.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {COLOR_TEXT};
        """)
        total_layout.addWidget(lbl_total_text)
        total_layout.addStretch()
        
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 800;
            color: {COLOR_PRIMARY};
        """)
        total_layout.addWidget(self.lbl_total)
        
        carrito_layout.addLayout(total_layout)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        btn_vaciar = QPushButton("Vaciar")
        btn_vaciar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_vaciar.setFixedHeight(36)
        btn_vaciar.setStyleSheet(f"""
            QPushButton {{
                background-color: #FEE2E2;
                color: {COLOR_DANGER};
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #FECACA;
            }}
        """)
        btn_vaciar.clicked.connect(self.vaciar_carrito)
        btn_layout.addWidget(btn_vaciar)
        
        btn_finalizar = QPushButton("Finalizar Compra")
        btn_finalizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_finalizar.setFixedHeight(36)
        btn_finalizar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: #16A34A;
            }}
            QPushButton:pressed {{
                background-color: #15803D;
            }}
        """)
        btn_finalizar.clicked.connect(self.finalizar_compra)
        btn_layout.addWidget(btn_finalizar)
        
        carrito_layout.addLayout(btn_layout)
        
        splitter.addWidget(carrito_panel)
        
        # Establecer proporciones: 70% productos, 30% carrito
        splitter.setSizes([880, 300])
        
        container_layout.addWidget(splitter)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)
    
    # ============================================================
    # MÉTODOS DE BÚSQUEDA
    # ============================================================
    
    def _on_busqueda_changed(self, text):
        self._busqueda_timer.start(300)
    
    def cargar_productos(self):
        """Carga productos con filtro de búsqueda"""
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        texto = self.busqueda_input.text().strip()
        
        try:
            if texto:
                productos = ejecutar_consulta(
                    """SELECT id, codigo_producto, descripcion, precio_venta, detalle, stock_actual 
                       FROM productos 
                       WHERE (codigo_producto LIKE ? OR descripcion LIKE ?) AND activo=1 
                       ORDER BY descripcion LIMIT 200""",
                    (f'%{texto}%', f'%{texto}%')
                )
            else:
                productos = ejecutar_consulta(
                    """SELECT id, codigo_producto, descripcion, precio_venta, detalle, stock_actual 
                       FROM productos 
                       WHERE activo=1 
                       ORDER BY descripcion LIMIT 200"""
                )
        except Exception as e:
            print(f"❌ Error cargando productos: {e}")
            productos = []
        
        if productos:
            self.lbl_resultados.setText(f"📊 {len(productos)} productos")
        else:
            self.lbl_resultados.setText("🔍 No hay resultados")
        
        if not productos:
            self._mostrar_empty_state()
            return
        
        # 5 columnas para 1200px
        cols = 5
        for idx, prod in enumerate(productos):
            tarjeta = TarjetaProducto(prod, self.cliente_id, self)
            tarjeta.agregado.connect(self.actualizar_carrito)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(tarjeta, row, col)
    
    def _mostrar_empty_state(self):
        """Muestra mensaje cuando no hay productos"""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(12)
        
        empty_icon = QLabel("🔍")
        empty_icon.setStyleSheet("font-size: 48px;")
        empty_layout.addWidget(empty_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        empty_title = QLabel("No se encontraron productos")
        empty_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLOR_TEXT};
        """)
        empty_layout.addWidget(empty_title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        empty_sub = QLabel("Prueba con otros términos de búsqueda")
        empty_sub.setStyleSheet(f"""
            font-size: 13px;
            color: {COLOR_TEXT_SECONDARY};
        """)
        empty_layout.addWidget(empty_sub, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.grid_layout.addWidget(empty_widget, 0, 0, 1, 1)
    
    # ============================================================
    # NOTIFICACIONES
    # ============================================================
    
    def mostrar_notificacion(self, mensaje):
        """Muestra notificación temporal"""
        self.lbl_resultados.setText(mensaje)
        self.lbl_resultados.setStyleSheet(f"""
            color: {COLOR_SUCCESS};
            font-size: 12px;
            font-weight: 500;
            padding: 0 8px;
        """)
        QTimer.singleShot(2500, self._restaurar_resultados)
    
    def _restaurar_resultados(self):
        """Restaura el texto de resultados"""
        count = self.grid_layout.count()
        self.lbl_resultados.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 12px;
            padding: 0 8px;
        """)
        if count > 0:
            self.lbl_resultados.setText(f"📊 {count} productos")
        else:
            self.lbl_resultados.setText("🔍 No hay resultados")
    
    # ============================================================
    # MÉTODOS DEL CARRITO
    # ============================================================
    
    def actualizar_carrito(self):
        """Actualiza la lista del carrito y los totales"""
        usuario = obtener_usuario_actual()
        if not usuario:
            return
        
        items = obtener_carrito(usuario['id'], self.cliente_id)
        
        # Limpiar lista
        self.lista_carrito.clear()
        
        total = 0
        total_items = 0
        
        if not items:
            # Mostrar mensaje de carrito vacío
            empty_item = QListWidgetItem()
            empty_widget = QLabel("🛒 El carrito está vacío")
            empty_widget.setStyleSheet(f"""
                color: {COLOR_TEXT_SECONDARY};
                font-size: 13px;
                padding: 20px;
                text-align: center;
            """)
            empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setSizeHint(empty_widget.sizeHint())
            self.lista_carrito.addItem(empty_item)
            self.lista_carrito.setItemWidget(empty_item, empty_widget)
        else:
            for item in items:
                codigo = item.get('codigo_producto', '')
                cantidad = item.get('cantidad', 0)
                precio = item.get('precio_unitario', 0)
                subtotal = cantidad * precio
                total += subtotal
                total_items += cantidad
                
                # Obtener descripción del producto
                producto = ejecutar_consulta(
                    "SELECT descripcion FROM productos WHERE codigo_producto = ?",
                    (codigo,)
                )
                descripcion = producto[0]['descripcion'] if producto else codigo
                
                # Crear item de la lista
                list_item = QListWidgetItem()
                item_widget = CarritoItemWidget(codigo, descripcion, cantidad, precio)
                list_item.setSizeHint(item_widget.sizeHint())
                self.lista_carrito.addItem(list_item)
                self.lista_carrito.setItemWidget(list_item, item_widget)
        
        # Actualizar totales
        self.lbl_total.setText(f"${total:.2f}")
        self.lbl_items_count.setText(f"{total_items} items")
    
    def vaciar_carrito(self):
        """Vacía el carrito con confirmación"""
        usuario = obtener_usuario_actual()
        if not usuario:
            return
        
        items = obtener_carrito(usuario['id'], self.cliente_id)
        if not items:
            mostrar_mensaje("Carrito vacío", "El carrito ya está vacío.", QMessageBox.Icon.Information)
            return
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar")
        msg.setText("¿Vaciar el carrito?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_BG};
            }}
            QMessageBox QLabel {{
                color: {COLOR_TEXT};
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
            }}
            QMessageBox QPushButton[text="&Yes"] {{
                background-color: {COLOR_DANGER};
                color: white;
            }}
            QMessageBox QPushButton[text="&Yes"]:hover {{
                background-color: #DC2626;
            }}
            QMessageBox QPushButton[text="&No"] {{
                background-color: #CBD5E1;
                color: {COLOR_TEXT};
            }}
            QMessageBox QPushButton[text="&No"]:hover {{
                background-color: #94A3B8;
            }}
        """)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            vaciar_carrito(usuario['id'], self.cliente_id)
            self.actualizar_carrito()
            self.mostrar_notificacion("🛒 Carrito vaciado")
    
    def finalizar_compra(self):
        """Finaliza la compra y muestra el resumen"""
        usuario = obtener_usuario_actual()
        if not usuario:
            mostrar_mensaje("Error", "No hay usuario autenticado.", QMessageBox.Icon.Critical)
            return
        
        items = obtener_carrito(usuario['id'], self.cliente_id)
        if not items:
            mostrar_mensaje("Carrito vacío", "No hay productos agregados.", QMessageBox.Icon.Warning)
            return
        
        # Preparar items con detalle
        items_con_detalle = []
        total = 0
        for item in items:
            codigo = item.get('codigo_producto')
            producto = ejecutar_consulta(
                "SELECT descripcion FROM productos WHERE codigo_producto = ?", 
                (codigo,)
            )
            descripcion = producto[0]['descripcion'] if producto else codigo
            items_con_detalle.append({
                'descripcion': descripcion,
                'cantidad': item.get('cantidad', 0),
                'precio_unitario': item.get('precio_unitario', 0)
            })
            total += item.get('cantidad', 0) * item.get('precio_unitario', 0)
        
        cliente = ejecutar_consulta(
            "SELECT id, razon_social, cuit, telefono, email FROM clientes WHERE id = ?", 
            (self.cliente_id,)
        )
        if not cliente:
            mostrar_mensaje("Error", "Cliente no encontrado.", QMessageBox.Icon.Critical)
            return
        
        try:
            resumen = ResumenCompraDialog(usuario, cliente[0], items_con_detalle, total, self)
            if resumen.exec():
                print("✅ Compra confirmada")
                vaciar_carrito(usuario['id'], self.cliente_id)
                self.actualizar_carrito()
                self.mostrar_notificacion("✅ Compra finalizada")
                self.accept()
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            mostrar_mensaje("Error", f"Error al procesar:\n{str(e)}", QMessageBox.Icon.Critical)
    
    # ============================================================
    # MÉTODOS DE CIERRE
    # ============================================================
    
    def closeEvent(self, event):
        self._reanudar_procesos_padre()
        event.accept()
    
    def reject(self):
        self._reanudar_procesos_padre()
        super().reject()
    
    def accept(self):
        self._reanudar_procesos_padre()
        super().accept()
    
    # ============================================================
    # MÉTODOS DE ARRASTRE
    # ============================================================
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self.drag_start = self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.drag_start + delta)
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None


# ============================================================
# ITEM DEL CARRITO
# ============================================================

class CarritoItemWidget(QWidget):
    def __init__(self, codigo, descripcion, cantidad, precio, parent=None):
        super().__init__(parent)
        self.codigo = codigo
        self.cantidad = cantidad
        self.precio = precio
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Info producto
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        
        lbl_cod = QLabel(codigo)
        lbl_cod.setStyleSheet(f"font-size: 9px; color: {COLOR_TEXT_SECONDARY};")
        info_layout.addWidget(lbl_cod)
        
        lbl_desc = QLabel(descripcion[:25] + "..." if len(descripcion) > 25 else descripcion)
        lbl_desc.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT};")
        info_layout.addWidget(lbl_desc)
        
        layout.addLayout(info_layout, 1)
        
        # Cantidad y precio
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.setSpacing(0)
        
        lbl_cant = QLabel(f"x{cantidad}")
        lbl_cant.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT};")
        right_layout.addWidget(lbl_cant)
        
        subtotal = cantidad * precio
        lbl_subtotal = QLabel(f"${subtotal:.2f}")
        lbl_subtotal.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLOR_PRIMARY};")
        right_layout.addWidget(lbl_subtotal)
        
        layout.addLayout(right_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG};
                border-radius: 6px;
                margin: 1px 0;
            }}
        """)