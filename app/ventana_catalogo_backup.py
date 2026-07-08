"""
Código Crítico - Tercer Semestre - Año 2026
Ventana principal de la aplicación (preventista).
"""

import sys
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QStatusBar, QMessageBox, QHBoxLayout, QLabel, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QKeyEvent
from database import ejecutar_consulta
from sync import sincronizacion_completa
from auth import obtener_usuario_actual, cerrar_sesion
from ventana_catalogo import CatalogoDialog

try:
    from ubicacion import RastreadorUbicacion, registrar_visita_cliente
    GPS_DISPONIBLE = True
except ImportError:
    GPS_DISPONIBLE = False
    def registrar_visita_cliente(cliente_id):
        pass
    class RastreadorUbicacion:
        def __init__(self):
            print("GPS no disponible")
        def obtener_ultima_posicion(self):
            return None, None


class VentanaPrincipal(QMainWindow):
    cerrar_sesion_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Distribuidora - Preventista")
        
        self.showFullScreen()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.usuario = obtener_usuario_actual()
        if not self.usuario:
            self.close()
            return

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        top = QHBoxLayout()
        top.setSpacing(20)
        
        self.lbl_usuario = QLabel(f"Usuario: {self.usuario['username']} ({self.usuario['rol']})")
        self.lbl_usuario.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        
        btn_sync = QPushButton("🔄 Sincronizar ahora")
        btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sync.setMinimumHeight(45)
        btn_sync.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_sync.clicked.connect(self.sincronizar_manual)
        
        btn_nuevo_cliente = QPushButton("➕ Nuevo Cliente")
        btn_nuevo_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo_cliente.setMinimumHeight(45)
        btn_nuevo_cliente.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_nuevo_cliente.clicked.connect(self.agregar_cliente)
        
        btn_logout = QPushButton("🚪 Cerrar sesión")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setMinimumHeight(45)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        btn_logout.clicked.connect(self.volver_al_login)
        
        top.addWidget(self.lbl_usuario)
        top.addStretch()
        top.addWidget(btn_sync)
        top.addWidget(btn_nuevo_cliente)
        top.addWidget(btn_logout)
        layout.addLayout(top)

        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

        self.statusBar().showMessage("Listo")
        
        # ✅ CONFIGURAR JAVA SCRIPT BRIDGE
        self.webview.page().javaScriptWindowObjectCleared.connect(self._inject_js_bridge)
        
        self.actualizar_mapa()

        self.timer_marker = QTimer()
        self.timer_marker.timeout.connect(self.verificar_marker_click)
        self.timer_marker.start(500)

        if GPS_DISPONIBLE:
            self.rastreador = RastreadorUbicacion()
            registrar_visita_cliente.rastreador = self.rastreador
        else:
            self.rastreador = None
    
    def _inject_js_bridge(self):
        """Inyecta el puente JavaScript para comunicación"""
        # ✅ EXPONER OBJETO PYTHON A JAVASCRIPT
        self.webview.page().addJavaScriptApiObject("pywebview", self)
        
        js_code = """
        // Función que será llamada desde el botón
        window.abrirCatalogo = function(cliente_id) {
            console.log('📦 Abriendo catálogo para cliente:', cliente_id);
            try {
                // Llamar al método Python expuesto
                if (window.pywebview) {
                    window.pywebview.abrirCatalogo(cliente_id);
                } else {
                    // Fallback: guardar en variable global
                    window.clienteSeleccionado = cliente_id;
                }
            } catch(e) {
                console.error('Error:', e);
            }
        };
        console.log('✅ Bridge JavaScript inicializado');
        """
        self.webview.page().runJavaScript(js_code)
    
    # ✅ MÉTODO EXPUESTO A JAVASCRIPT
    def abrirCatalogo(self, cliente_id):
        """Método llamado desde JavaScript para abrir el catálogo"""
        print(f"🔍 JavaScript llamó a abrirCatalogo con ID: {cliente_id}")
        # Convertir a entero si es string
        try:
            cliente_id = int(cliente_id)
        except:
            pass
        self.procesar_cliente_seleccionado(cliente_id)

    def actualizar_mapa(self):
        """Actualiza el mapa con los clientes que tienen coordenadas."""
        usuario = self.usuario
        
        if usuario.get('rol') == 'admin':
            clientes = ejecutar_consulta("SELECT id, razon_social, latitud, longitud FROM clientes WHERE latitud IS NOT NULL AND longitud IS NOT NULL")
        else:
            preventista_id = usuario.get('preventista_id')
            if not preventista_id:
                self.statusBar().showMessage("Usuario no tiene preventista asignado")
                return
            clientes = ejecutar_consulta(
                "SELECT id, razon_social, latitud, longitud FROM clientes WHERE preventista_id = ? AND latitud IS NOT NULL AND longitud IS NOT NULL",
                (preventista_id,)
            )

        print(f"📍 Mostrando {len(clientes)} clientes en el mapa")

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
            <title>Mapa de Clientes</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map { height: 100%; width: 100%; position: absolute; top: 0; left: 0; }
                body { margin: 0; padding: 0; }
                .leaflet-popup-content { 
                    font-size: 16px; 
                    min-width: 150px;
                }
                .btn-catalogo { 
                    font-size: 16px; 
                    padding: 8px 16px; 
                    background-color: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 8px; 
                    cursor: pointer; 
                    width: 100%;
                    margin-top: 8px;
                    font-weight: bold;
                }
                .btn-catalogo:hover { 
                    background-color: #2980b9; 
                }
                .btn-catalogo:active {
                    background-color: #1a6ea0;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Esperar a que el bridge esté listo
                console.log('🗺️ Inicializando mapa...');
                
                var map = L.map('map').setView([-38.4161, -63.6167], 5);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                }).addTo(map);
                
                console.log('✅ Mapa inicializado');
        """
        
        for c in clientes:
            html += f"""
                // Cliente ID: {c['id']} - {c['razon_social']}
                var marker = L.marker([{c['latitud']}, {c['longitud']}]).addTo(map);
                
                // Crear contenido del popup
                var popupContent = document.createElement('div');
                popupContent.innerHTML = `
                    <b>{c['razon_social']}</b><br>
                    <button class="btn-catalogo" id="btn_{c['id']}">📦 Ver catálogo</button>
                `;
                
                // Agregar evento al botón cuando se abre el popup
                marker.on('popupopen', function() {{
                    var btn = document.getElementById('btn_{c['id']}');
                    if (btn) {{
                        btn.addEventListener('click', function(e) {{
                            e.stopPropagation();
                            console.log('🔘 Click en botón para cliente {c['id']}');
                            // Llamar a la función global
                            if (typeof window.abrirCatalogo === 'function') {{
                                window.abrirCatalogo({c['id']});
                            }} else {{
                                console.error('❌ window.abrirCatalogo no está definido');
                                // Fallback: usar variable global
                                window.clienteSeleccionado = {c['id']};
                            }}
                        }});
                    }}
                }});
                
                marker.bindPopup(popupContent);
            """
        
        html += """
                // También permitir clics en la variable global (fallback)
                window.clienteSeleccionado = null;
                
                // Monitorear variable global
                setInterval(function() {
                    if (window.clienteSeleccionado !== null && window.clienteSeleccionado !== undefined) {
                        console.log('🔍 Variable global detectada:', window.clienteSeleccionado);
                        var id = window.clienteSeleccionado;
                        window.clienteSeleccionado = null;
                        if (typeof window.abrirCatalogo === 'function') {
                            window.abrirCatalogo(id);
                        }
                    }
                }, 1000);
            </script>
        </body>
        </html>
        """
        self.webview.setHtml(html)
        
        # ✅ Inyectar bridge después de cargar
        QTimer.singleShot(500, self._inject_js_bridge)

    def verificar_marker_click(self):
        """Verifica si se hizo clic en un marcador (método de respaldo)"""
        self.webview.page().runJavaScript("window.clienteSeleccionado", self._procesar_cliente_desde_js)

    def _procesar_cliente_desde_js(self, cliente_id):
        """Procesa cliente desde variable global JS"""
        if cliente_id and int(cliente_id) > 0:
            print(f"🔍 JS variable global: {cliente_id}")
            self.webview.page().runJavaScript("window.clienteSeleccionado = null;")
            self.procesar_cliente_seleccionado(cliente_id)

    def procesar_cliente_seleccionado(self, cliente_id):
        """Procesa el cliente seleccionado y abre el catálogo"""
        print(f"🔍 Procesando cliente ID: {cliente_id} (tipo: {type(cliente_id)})")
        
        try:
            cliente_id_int = int(cliente_id)
        except (ValueError, TypeError):
            print(f"❌ ID inválido: {cliente_id}")
            return
        
        if cliente_id_int > 0:
            cliente = ejecutar_consulta("SELECT razon_social FROM clientes WHERE id = ?", (cliente_id_int,))
            print(f"📋 Cliente encontrado: {cliente}")
            
            if cliente:
                print(f"🚀 Abriendo catálogo para: {cliente[0]['razon_social']}")
                try:
                    dialog = CatalogoDialog(cliente_id_int, cliente[0]['razon_social'], self)
                    dialog.exec()
                    print("✅ Catálogo cerrado correctamente")
                except Exception as e:
                    print(f"❌ Error al abrir catálogo: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "Error", f"No se pudo abrir el catálogo:\n{str(e)}")
            else:
                print(f"❌ Cliente no encontrado con ID: {cliente_id}")
                QMessageBox.warning(self, "Error", f"Cliente ID {cliente_id} no encontrado")
        else:
            print(f"❌ ID inválido: {cliente_id}")

    def sincronizar_manual(self):
        self.statusBar().showMessage("Sincronizando...")
        try:
            sincronizacion_completa()
            self.statusBar().showMessage("Sincronización completada", 3000)
            self.actualizar_mapa()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en sincronización: {e}")
            self.statusBar().showMessage("Error en sincronización")

    def agregar_cliente(self):
        from ventana_nuevo_cliente import NuevoClienteDialog
        dialog = NuevoClienteDialog(self)
        if dialog.exec():
            self.actualizar_mapa()
            self.statusBar().showMessage("Cliente agregado. Se sincronizará automáticamente.", 3000)

    def volver_al_login(self):
        cerrar_sesion()
        print("🔒 Sesión cerrada - Volviendo al login")
        self.cerrar_sesion_signal.emit()
        self.close()
    
    def closeEvent(self, event):
        respuesta = QMessageBox.question(
            self,
            "Cerrar sesión",
            "¿Estás seguro que deseas cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            cerrar_sesion()
            print("🔒 Sesión cerrada - Volviendo al login")
            self.cerrar_sesion_signal.emit()
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Q:
            respuesta = QMessageBox.question(
                self,
                "Salir",
                "¿Estás seguro que deseas salir de la aplicación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.Yes:
                cerrar_sesion()
                self.cerrar_sesion_signal.emit()
                self.close()
        super().keyPressEvent(event)