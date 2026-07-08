"""
Código Crítico - Tercer Semestre - Año 2026
Ventana de login con diseño moderno y fondo blanco.
VERSIÓN PyQt6
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPalette
from auth import verificar_usuario, establecer_usuario_actual

class LoginDialog(QDialog):
    # Señal para avisar que se quiere salir de la app
    salir_app_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iniciar Sesión")
        self.setFixedSize(480, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Fondo blanco
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(QColor(255, 255, 255)))
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tarjeta central
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 25px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(45, 50, 45, 45)
        card_layout.setSpacing(22)

        # Título
        title = QLabel("Catálogo Virtual")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 34px;
            font-weight: bold;
            color: #2c3e50;
            letter-spacing: 1px;
        """)
        card_layout.addWidget(title)

        # Subtítulo
        subtitulo = QLabel("Ingrese sus credenciales")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 15px;
        """)
        card_layout.addWidget(subtitulo)

        # Usuario
        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px;")
        card_layout.addWidget(lbl_user)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese su usuario")
        self.username_input.setMinimumHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 1px solid #d0d0d0;
                border-radius: 12px;
                font-size: 15px;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #b0b0b0;
            }
        """)
        card_layout.addWidget(self.username_input)

        # Contraseña
        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px;")
        card_layout.addWidget(lbl_pass)

        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 1px solid #d0d0d0;
                border-radius: 12px;
                font-size: 15px;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #b0b0b0;
            }
        """)
        password_layout.addWidget(self.password_input)

        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setFixedSize(40, 45)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #7f8c8d;
            }
            QPushButton:hover { color: #3498db; }
        """)
        self.toggle_btn.clicked.connect(self.toggle_password)
        password_layout.addWidget(self.toggle_btn)
        card_layout.addLayout(password_layout)

        # Botón login
        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setMinimumHeight(52)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        login_btn.clicked.connect(self.verificar)
        card_layout.addWidget(login_btn)

        card.setLayout(card_layout)
        main_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

        self.usuario = None
        self.drag_pos = None
        self.drag_start = None

    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("👁️")

    def verificar(self):
        user = verificar_usuario(self.username_input.text(), self.password_input.text())
        if user:
            establecer_usuario_actual(user)
            self.usuario = user
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")

    def salir_aplicacion(self):
        respuesta = QMessageBox.question(
            self,
            "Salir",
            "¿Estás seguro que deseas salir de la aplicación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.salir_app_signal.emit()
            self.reject()

    def closeEvent(self, event):
        respuesta = QMessageBox.question(
            self,
            "Salir",
            "¿Estás seguro que deseas salir de la aplicación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.salir_app_signal.emit()
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self.drag_start = self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.drag_start + delta)