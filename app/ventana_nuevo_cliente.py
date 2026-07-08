from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QLinearGradient, QColor, QBrush, QPalette
from database import ejecutar_consulta
from auth import obtener_usuario_actual
from geocoding import geocodificar_direccion


class GeocodingThread(QThread):
    finished = pyqtSignal(object, object)  # lat, lon
    progress = pyqtSignal(int)  # progreso
    
    def __init__(self, calle, numero, localidad, provincia):
        super().__init__()
        self.calle = calle
        self.numero = numero
        self.localidad = localidad
        self.provincia = provincia
    
    def run(self):
        self.progress.emit(25)
        lat, lon = geocodificar_direccion(self.calle, self.numero, self.localidad, self.provincia)
        self.progress.emit(100)
        self.finished.emit(lat, lon)


class NuevoClienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Cliente")
        self.setFixedSize(550, 750)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(52, 152, 219))
        gradient.setColorAt(1.0, QColor(41, 128, 185))
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        titulo = QLabel("Agregar Nuevo Cliente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-bottom: 15px;")
        layout.addWidget(titulo)
        
        line_edit_style = """
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                background-color: white;
                color: black;
                selection-background-color: #3498db;
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """
        
        self.razon_social = QLineEdit()
        self.razon_social.setPlaceholderText("Razón Social *")
        self.razon_social.setStyleSheet(line_edit_style)
        layout.addWidget(self.razon_social)
        
        self.cuit = QLineEdit()
        self.cuit.setPlaceholderText("CUIT")
        self.cuit.setStyleSheet(line_edit_style)
        layout.addWidget(self.cuit)
        
        direccion_layout = QHBoxLayout()
        self.calle = QLineEdit()
        self.calle.setPlaceholderText("Calle *")
        self.calle.setStyleSheet(line_edit_style)
        self.numero = QLineEdit()
        self.numero.setPlaceholderText("Número *")
        self.numero.setStyleSheet(line_edit_style)
        direccion_layout.addWidget(self.calle)
        direccion_layout.addWidget(self.numero)
        layout.addLayout(direccion_layout)
        
        self.domicilio = QLineEdit()
        self.domicilio.setPlaceholderText("Domicilio completo (opcional)")
        self.domicilio.setStyleSheet(line_edit_style)
        layout.addWidget(self.domicilio)
        
        loc_prov_layout = QHBoxLayout()
        self.localidad = QLineEdit()
        self.localidad.setPlaceholderText("Localidad *")
        self.localidad.setStyleSheet(line_edit_style)
        self.provincia = QLineEdit()
        self.provincia.setPlaceholderText("Provincia *")
        self.provincia.setStyleSheet(line_edit_style)
        loc_prov_layout.addWidget(self.localidad)
        loc_prov_layout.addWidget(self.provincia)
        layout.addLayout(loc_prov_layout)
        
        telefono_layout = QHBoxLayout()
        self.telefono = QLineEdit()
        self.telefono.setPlaceholderText("Teléfono")
        self.telefono.setStyleSheet(line_edit_style)
        self.whatsapp = QLineEdit()
        self.whatsapp.setPlaceholderText("WhatsApp (con código de área)")
        self.whatsapp.setStyleSheet(line_edit_style)
        telefono_layout.addWidget(self.telefono)
        telefono_layout.addWidget(self.whatsapp)
        layout.addLayout(telefono_layout)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.email.setStyleSheet(line_edit_style)
        layout.addWidget(self.email)
        
        coords_layout = QHBoxLayout()
        self.latitud = QLineEdit()
        self.latitud.setPlaceholderText("Latitud (automática)")
        self.latitud.setStyleSheet(line_edit_style)
        self.longitud = QLineEdit()
        self.longitud.setPlaceholderText("Longitud (automática)")
        self.longitud.setStyleSheet(line_edit_style)
        coords_layout.addWidget(self.latitud)
        coords_layout.addWidget(self.longitud)
        layout.addLayout(coords_layout)
        
        self.preventista_combo = QComboBox()
        self.preventista_combo.setVisible(False)
        self.preventista_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
        """)
        layout.addWidget(self.preventista_combo)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: white;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet("background-color: #2ecc71; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        usuario = obtener_usuario_actual()
        if usuario and usuario.get("rol") == "admin":
            self.preventista_combo.setVisible(True)
            self.cargar_preventistas()
            layout.insertWidget(11, QLabel("Asignar a preventista:"))
    
    def cargar_preventistas(self):
        preventistas = ejecutar_consulta("SELECT id, nombre, apellido FROM preventistas WHERE activo=1")
        for p in preventistas:
            self.preventista_combo.addItem(f"{p['nombre']} {p['apellido']}", p['id'])
    
    def guardar(self):
        razon = self.razon_social.text().strip()
        if not razon:
            QMessageBox.warning(self, "Error", "La Razón Social es obligatoria.")
            return
        
        calle = self.calle.text().strip()
        numero = self.numero.text().strip()
        localidad = self.localidad.text().strip()
        provincia = self.provincia.text().strip()
        
        if not calle or not numero or not localidad or not provincia:
            QMessageBox.warning(self, "Error", "Complete calle, número, localidad y provincia para geolocalizar.")
            return
        
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Geocodificando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.geo_thread = GeocodingThread(calle, numero, localidad, provincia)
        self.geo_thread.finished.connect(self.on_geocoding_finished)
        self.geo_thread.progress.connect(self.progress_bar.setValue)
        self.geo_thread.start()
    
    def on_geocoding_finished(self, lat, lon):
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText("Guardar")
        self.progress_bar.setVisible(False)
        
        if lat is None or lon is None:
            QMessageBox.warning(self, "Advertencia", "No se pudo obtener la ubicación automática. Puede ingresar coordenadas manualmente o revisar la dirección.")
            try:
                lat = float(self.latitud.text()) if self.latitud.text() else None
                lon = float(self.longitud.text()) if self.longitud.text() else None
            except:
                lat = lon = None
            if lat is None or lon is None:
                return
        
        calle = self.calle.text().strip()
        numero = self.numero.text().strip()
        localidad = self.localidad.text().strip()
        provincia = self.provincia.text().strip()
        domicilio_completo = f"{calle} {numero}, {localidad}, {provincia}"
        razon = self.razon_social.text().strip()
        cuit = self.cuit.text().strip() or None
        telefono = self.telefono.text().strip() or None
        whatsapp = self.whatsapp.text().strip() or None
        email = self.email.text().strip() or None
        
        usuario = obtener_usuario_actual()
        if usuario.get("rol") == "admin":
            preventista_id = self.preventista_combo.currentData() if self.preventista_combo.count() > 0 else None
        else:
            preventista_id = usuario.get("preventista_id")
        
        try:
            ejecutar_consulta("""
                INSERT INTO clientes (razon_social, cuit, domicilio, telefono, whatsapp, email, latitud, longitud, preventista_id, localidad, provincia, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (razon, cuit, domicilio_completo, telefono, whatsapp, email, lat, lon, preventista_id, localidad, provincia), commit=True)
            QMessageBox.information(self, "Éxito", "Cliente agregado correctamente.\nSe ha geolocalizado automáticamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")