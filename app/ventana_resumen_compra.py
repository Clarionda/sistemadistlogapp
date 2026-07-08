"""
Código Crítico - Tercer Semestre - Año 2026
Ventana de resumen de compra - PyQt6
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFrame, QWidget,
                             QSizePolicy, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from pedidos import crear_nota_venta


def mostrar_mensaje(titulo, mensaje, icono=QMessageBox.Icon.Information):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensaje)
    msg.setIcon(icono)
    msg.exec()


class ResumenCompraDialog(QDialog):
    def __init__(self, usuario, cliente, items, total, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.cliente = cliente
        self.items = items
        self.total = total
        self.setWindowTitle("Confirmar Compra")
        self.setFixedSize(900, 750)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.Dialog)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 25, 30, 25)
        
        # TÍTULO
        titulo = QLabel("📋 Resumen de la Compra")
        titulo.setStyleSheet("""
            font-size: 26px;
            font-weight: 800;
            color: #1a2634;
            padding: 10px 0;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)
        
        # INFO CLIENTE
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setSpacing(30)
        
        # Cliente
        cliente_widget = QWidget()
        cliente_layout = QVBoxLayout(cliente_widget)
        cliente_layout.setSpacing(4)
        
        lbl_cliente_title = QLabel("👤 CLIENTE")
        lbl_cliente_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #4a90d9; letter-spacing: 1px;")
        cliente_layout.addWidget(lbl_cliente_title)
        
        lbl_cliente_nombre = QLabel(f"<b>{cliente['razon_social']}</b>")
        lbl_cliente_nombre.setStyleSheet("font-size: 15px; color: #1a2634;")
        cliente_layout.addWidget(lbl_cliente_nombre)
        
        cuit_text = cliente.get('cuit', 'N/A')
        lbl_cuit = QLabel(f"CUIT: {cuit_text}")
        lbl_cuit.setStyleSheet("font-size: 13px; color: #64748b;")
        cliente_layout.addWidget(lbl_cuit)
        
        telefono_text = cliente.get('telefono', 'N/A')
        lbl_telefono = QLabel(f"Teléfono: {telefono_text}")
        lbl_telefono.setStyleSheet("font-size: 13px; color: #64748b;")
        cliente_layout.addWidget(lbl_telefono)
        
        info_layout.addWidget(cliente_widget, 1)
        
        # Preventista
        preventista_widget = QWidget()
        preventista_layout = QVBoxLayout(preventista_widget)
        preventista_layout.setSpacing(4)
        
        lbl_prev_title = QLabel("👨‍💼 PREVENTISTA")
        lbl_prev_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #27ae60; letter-spacing: 1px;")
        preventista_layout.addWidget(lbl_prev_title)
        
        lbl_usuario = QLabel(f"Usuario: {usuario['username']}")
        lbl_usuario.setStyleSheet("font-size: 14px; color: #1a2634;")
        preventista_layout.addWidget(lbl_usuario)
        
        prev_id_text = usuario.get('preventista_id', 'N/A')
        lbl_prev_id = QLabel(f"ID: {prev_id_text}")
        lbl_prev_id.setStyleSheet("font-size: 13px; color: #64748b;")
        preventista_layout.addWidget(lbl_prev_id)
        
        info_layout.addWidget(preventista_widget, 1)
        main_layout.addWidget(info_frame)
        
        # TABLA DE PRODUCTOS
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setSpacing(5)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_items_title = QLabel(f"📦 Productos ({len(self.items)} items)")
        lbl_items_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1a2634;")
        header_layout.addWidget(lbl_items_title)
        header_layout.addStretch()
        table_layout.addWidget(header_widget)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Cant.", "Precio", "Subtotal"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setMinimumHeight(250)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: none;
                gridline-color: #e8eaed;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 8px;
                color: #1a2634;
            }
            QTableWidget::item:selected {
                background-color: #e8edf5;
                color: #1a2634;
            }
            QTableWidget::item:alternate {
                background-color: #f7f8fa;
            }
            QHeaderView::section {
                background-color: #1a2634;
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 8px;
                border: none;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
            }
        """)
        table_layout.addWidget(self.tabla)
        main_layout.addWidget(table_frame)
        
        # Cargar productos
        self.tabla.setRowCount(len(self.items))
        for i, item in enumerate(self.items):
            item_prod = QTableWidgetItem(item['descripcion'])
            item_prod.setForeground(QColor(26, 38, 52))
            self.tabla.setItem(i, 0, item_prod)
            
            item_cant = QTableWidgetItem(str(item['cantidad']))
            item_cant.setForeground(QColor(26, 38, 52))
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 1, item_cant)
            
            item_precio = QTableWidgetItem(f"${item['precio_unitario']:.2f}")
            item_precio.setForeground(QColor(26, 38, 52))
            item_precio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 2, item_precio)
            
            subtotal = item['cantidad'] * item['precio_unitario']
            item_subtotal = QTableWidgetItem(f"${subtotal:.2f}")
            item_subtotal.setForeground(QColor(26, 38, 52))
            item_subtotal.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            font_sub = item_subtotal.font()
            font_sub.setWeight(QFont.Weight.DemiBold)
            item_subtotal.setFont(font_sub)
            self.tabla.setItem(i, 3, item_subtotal)
        
        for i in range(self.tabla.rowCount()):
            self.tabla.setRowHeight(i, 38)
        
        # TOTAL
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                background-color: #f7f8fa;
                border-radius: 12px;
                border: 2px solid #e2e8f0;
            }
        """)
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(20, 12, 20, 12)
        
        lbl_total_text = QLabel("💰 TOTAL")
        lbl_total_text.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1a2634;
            letter-spacing: 1px;
        """)
        total_layout.addWidget(lbl_total_text)
        total_layout.addStretch()
        
        self.total_label = QLabel(f"${self.total:.2f}")
        self.total_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
            color: #d4761a;
        """)
        total_layout.addWidget(self.total_label)
        main_layout.addWidget(total_frame)
        
        # BOTONES
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("✕ Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setFixedSize(140, 45)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_confirmar = QPushButton("✅ Confirmar Compra")
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.setFixedSize(180, 45)
        btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_confirmar.clicked.connect(self.confirmar)
        btn_layout.addWidget(btn_confirmar)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def confirmar(self):
        """Confirma la compra y crea la nota de venta"""
        print("🔄 Creando nota de venta...")
        
        nota_id = crear_nota_venta(
            self.usuario['id'], 
            self.usuario.get('preventista_id'), 
            self.cliente['id']
        )
        
        if nota_id:
            # ✅ Cerrar el diálogo y luego mostrar el mensaje
            self.accept()
            # ✅ Mostrar mensaje después de cerrar (usando QTimer)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: mostrar_mensaje(
                "✅ Compra Confirmada", 
                f"¡Compra realizada con éxito!\n\nNota de venta creada correctamente.\nSe sincronizará automáticamente.",
                QMessageBox.Icon.Information
            ))
        else:
            mostrar_mensaje(
                "❌ Error", 
                "No se pudo crear la nota de venta.\nEl carrito puede estar vacío o ha ocurrido un error inesperado.",
                QMessageBox.Icon.Critical
            )