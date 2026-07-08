"""
Código Crítico - Tercer Semestre - Año 2026
Pantalla de Splash con sincronización real.
VERSIÓN PyQt6 - CORREGIDA
"""

import time

from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QRect, QPointF, QElapsedTimer
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, 
    QLinearGradient, QRadialGradient, QFont
)


class AnilloBordeExterno(QWidget):
    """Widget que dibuja 3 anillos giratorios en el BORDE EXTERNO del splash"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.angulo1 = 0
        self.angulo2 = 0
        self.angulo3 = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotar)
        self.timer.start(25)
    
    def rotar(self):
        self.angulo1 = (self.angulo1 + 4) % 360
        self.angulo2 = (self.angulo2 - 6) % 360
        self.angulo3 = (self.angulo3 + 8) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        centro_x = self.width() // 2
        centro_y = self.height() // 2
        radio_base = min(self.width(), self.height()) // 2 - 10
        
        radio1 = radio_base
        self._dibujar_anillo(painter, centro_x, centro_y, radio1, self.angulo1, QColor(255, 193, 7), 7)
        
        radio2 = radio_base - 35
        self._dibujar_anillo(painter, centro_x, centro_y, radio2, self.angulo2, QColor(51, 181, 229), 7)
        
        radio3 = radio_base - 70
        self._dibujar_anillo(painter, centro_x, centro_y, radio3, self.angulo3, QColor(76, 175, 80), 7)
    
    def _dibujar_anillo(self, painter, cx, cy, radio, angulo, color, grosor):
        pen_sombra = QPen(QColor(0, 0, 0, 60), grosor + 4)
        pen_sombra.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_sombra)
        
        start_angle = angulo * 16
        span_angle = 300 * 16
        
        rect = QRect(cx - radio, cy - radio, radio * 2, radio * 2)
        painter.drawArc(rect, start_angle, span_angle)
        
        pen = QPen(color, grosor)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, start_angle, span_angle)


class SplashBienvenida(QSplashScreen):
    """Splash con posicionamiento absoluto y sincronización real"""
    
    terminado = pyqtSignal()
    
    def __init__(self):
        size = 620
        self.tiempo_inicio = QElapsedTimer()
        self.tiempo_inicio.start()
        self.duracion_minima = 3000  # 3 segundos mínimo (se ajusta con la sincronización)
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        gradient = QRadialGradient(size//2, size//2, size//2)
        gradient.setColorAt(0.0, QColor(21, 101, 192))
        gradient.setColorAt(0.4, QColor(26, 35, 126))
        gradient.setColorAt(1.0, QColor(13, 71, 161))
        
        painter.fillRect(0, 0, size, size, gradient)
        painter.end()
        
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)
        
        self.anillos = AnilloBordeExterno(self)
        self.anillos.setGeometry(30, 30, 560, 560)
        
        self.contenedor = QWidget(self)
        self.contenedor.setGeometry(80, 240, 460, 340)
        self.contenedor.setStyleSheet("background: transparent;")
        
        contenedor_layout = QVBoxLayout(self.contenedor)
        contenedor_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contenedor_layout.setSpacing(12)
        contenedor_layout.setContentsMargins(10, 5, 10, 5)
        
        titulo = QLabel("Catálogo Virtual")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
            letter-spacing: 4px;
        """)
        contenedor_layout.addWidget(titulo)
        
        subtitulo = QLabel("Sistema de Gestión de Pedidos")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("""
            font-size: 16px;
            color: #B0C4DE;
            letter-spacing: 2px;
            font-weight: 300;
            margin-bottom: 10px;
        """)
        contenedor_layout.addWidget(subtitulo)
        
        self.label_estado = QLabel("🔄 Conectando con servidor...")
        self.label_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_estado.setWordWrap(True)
        self.label_estado.setStyleSheet("""
            font-size: 19px;
            font-weight: bold;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: rgba(0, 0, 0, 0.18);
            border-radius: 14px;
            padding: 10px 22px;
            border: 1px solid rgba(255,255,255,0.06);
            min-height: 50px;
        """)
        contenedor_layout.addWidget(self.label_estado)
        
        self.label_detalle = QLabel("Inicializando sincronización...")
        self.label_detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_detalle.setWordWrap(True)
        self.label_detalle.setStyleSheet("""
            font-size: 16px;
            color: #D4E0EC;
            font-weight: 500;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: rgba(0, 0, 0, 0.10);
            border-radius: 12px;
            padding: 8px 20px;
            min-height: 40px;
            max-width: 420px;
        """)
        contenedor_layout.addWidget(self.label_detalle)
        
        separador = QLabel("")
        separador.setFixedHeight(6)
        contenedor_layout.addWidget(separador)
        
        barra_container = QWidget()
        barra_container.setFixedHeight(20)
        barra_container.setStyleSheet("background: transparent;")
        
        barra_layout = QVBoxLayout(barra_container)
        barra_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QLabel()
        self.progress_bar.setFixedWidth(390)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.18);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.10);
            }
        """)
        barra_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        contenedor_layout.addWidget(barra_container)
        
        self.label_porcentaje = QLabel("0%")
        self.label_porcentaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_porcentaje.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: rgba(76, 175, 80, 0.72);
            border-radius: 28px;
            padding: 6px 28px;
            min-width: 90px;
            font-family: 'Segoe UI', Arial, sans-serif;
            border: 2px solid rgba(255, 255, 255, 0.20);
        """)
        contenedor_layout.addWidget(self.label_porcentaje, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.label_sync_status = QLabel("⚡ Sincronizando datos...")
        self.label_sync_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_sync_status.setStyleSheet("""
            font-size: 14px;
            color: #B8C8D8;
            font-weight: 400;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: rgba(0, 0, 0, 0.06);
            border-radius: 10px;
            padding: 4px 16px;
            min-height: 24px;
        """)
        contenedor_layout.addWidget(self.label_sync_status)
        
        self.center()
        self.show()
        
        self._sincronizacion_completa = False
        self._etapas = []
        self._etapa_actual = 0
        self._progreso_actual = 0
        self._sincronizacion_terminada = False
        self._tiempo_inicio_sync = None
        
        QTimer.singleShot(300, self.iniciar_sincronizacion_real)
    
    def center(self):
        pantalla = self.screen().availableGeometry()
        x = (pantalla.width() - self.width()) // 2
        y = (pantalla.height() - self.height()) // 2
        self.move(x, y)
    
    def actualizar_barra(self, porcentaje):
        self.label_porcentaje.setText(f"{int(porcentaje)}%")
        
        if porcentaje < 20:
            self.label_sync_status.setText("📡 Conectando con servidor...")
        elif porcentaje < 40:
            self.label_sync_status.setText("🔄 Descargando datos...")
        elif porcentaje < 60:
            self.label_sync_status.setText("📦 Procesando información...")
        elif porcentaje < 80:
            self.label_sync_status.setText("⚙️ Actualizando base de datos...")
        elif porcentaje < 100:
            self.label_sync_status.setText("✅ Finalizando sincronización...")
        else:
            self.label_sync_status.setText("🎉 ¡Sistema listo!")
        
        ancho = self.progress_bar.width()
        alto = self.progress_bar.height()
        
        if ancho <= 0 or alto <= 0:
            ancho = 390
            alto = 10
        
        pixmap = QPixmap(ancho, alto)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(255, 255, 255, 25))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRect(0, 0, ancho, alto)
        painter.drawRoundedRect(rect, 6, 6)
        
        ancho_progreso = int(ancho * (porcentaje / 100))
        if ancho_progreso > 0:
            gradiente = QLinearGradient(0, 0, ancho_progreso, 0)
            gradiente.setColorAt(0.0, QColor(255, 193, 7))
            gradiente.setColorAt(0.3, QColor(76, 175, 80))
            gradiente.setColorAt(0.7, QColor(33, 150, 243))
            gradiente.setColorAt(1.0, QColor(156, 39, 176))
            
            painter.setBrush(QColor(76, 175, 80, 20))
            glow_rect = QRect(2, -3, ancho_progreso - 4, alto + 6)
            painter.drawRoundedRect(glow_rect, 8, 8)
            
            painter.setBrush(gradiente)
            progress_rect = QRect(0, 0, ancho_progreso, alto)
            painter.drawRoundedRect(progress_rect, 6, 6)
            
            painter.setBrush(QColor(255, 255, 255, 50))
            highlight_rect = QRect(2, 1, ancho_progreso - 4, alto // 2 - 1)
            painter.drawRoundedRect(highlight_rect, 4, 4)
        
        painter.end()
        self.progress_bar.setPixmap(pixmap)
    
    def iniciar_sincronizacion_real(self):
        """Inicia la sincronización real de datos"""
        from sync import bajar_tabla
        
        self._tiempo_inicio_sync = time.time()
        
        # Etapas de sincronización - todas las tablas necesarias
        self._etapas = [
            {'tabla': 'usuarios', 'desc': 'Usuarios', 'icono': '👤'},
            {'tabla': 'preventistas', 'desc': 'Preventistas', 'icono': '👨‍💼'},
            {'tabla': 'clientes', 'desc': 'Clientes', 'icono': '🏢'},
            {'tabla': 'productos', 'desc': 'Productos (stock y precios)', 'icono': '📦'},
            {'tabla': 'categorias', 'desc': 'Categorías', 'icono': '📂'},
        ]
        
        self._etapa_actual = 0
        self._progreso_actual = 0
        self._sincronizar_siguiente_etapa()
    
    def _sincronizar_siguiente_etapa(self):
        """Sincroniza la siguiente etapa en la cola"""
        from sync import bajar_tabla
        
        if self._etapa_actual >= len(self._etapas):
            # Sincronización completada
            self._sincronizacion_terminada = True
            self.label_estado.setText("✅ ¡Sistema listo!")
            self.label_detalle.setText("Todos los datos sincronizados correctamente")
            self.label_sync_status.setText("🎉 ¡Listo para trabajar!")
            self.actualizar_barra(100)
            
            # Calcular tiempo real de sincronización
            tiempo_total = time.time() - self._tiempo_inicio_sync
            print(f"⏱️ Sincronización completada en {tiempo_total:.2f} segundos")
            
            # Cerrar después de un breve retraso para mostrar "completado"
            QTimer.singleShot(800, self.cerrar_splash)
            return
        
        etapa = self._etapas[self._etapa_actual]
        
        # Actualizar UI
        texto_estado = f"{etapa['icono']} {etapa['desc']}"
        texto_detalle = f"Sincronizando: {etapa['tabla'].upper()}..."
        
        self.label_estado.setText(texto_estado)
        self.label_detalle.setText(texto_detalle)
        
        # Ajustar tamaño de fuente para textos largos
        if len(texto_detalle) > 30:
            self.label_detalle.setStyleSheet("""
                font-size: 14px;
                color: #D4E0EC;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: rgba(0, 0, 0, 0.10);
                border-radius: 12px;
                padding: 8px 20px;
                min-height: 40px;
                max-width: 420px;
            """)
        else:
            self.label_detalle.setStyleSheet("""
                font-size: 16px;
                color: #D4E0EC;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: rgba(0, 0, 0, 0.10);
                border-radius: 12px;
                padding: 8px 20px;
                min-height: 40px;
                max-width: 420px;
            """)
        
        try:
            # Sincronizar tabla
            print(f"🔄 Sincronizando {etapa['tabla']}...")
            bajar_tabla(etapa['tabla'])
            print(f"✅ {etapa['tabla']} sincronizado correctamente")
            
            self._etapa_actual += 1
            progreso = int((self._etapa_actual / len(self._etapas)) * 100)
            self._progreso_actual = progreso
            self.actualizar_barra(progreso)
            
            # Continuar con la siguiente etapa (con un pequeño retraso para ver el progreso)
            QTimer.singleShot(200, self._sincronizar_siguiente_etapa)
            
        except Exception as e:
            print(f"⚠️ Error sincronizando {etapa['tabla']}: {e}")
            self.label_detalle.setText(f"⚠️ Error en {etapa['tabla']}, continuando...")
            
            self._etapa_actual += 1
            progreso = int((self._etapa_actual / len(self._etapas)) * 100)
            self._progreso_actual = progreso
            self.actualizar_barra(progreso)
            
            QTimer.singleShot(400, self._sincronizar_siguiente_etapa)
    
    def cerrar_splash(self):
        """Cierra el splash y emite la señal de terminado"""
        if hasattr(self, 'anillos') and hasattr(self.anillos, 'timer'):
            self.anillos.timer.stop()
        
        self.close()
        print("✅ Splash cerrado - Sistema listo")
        self.terminado.emit()
    
    def closeEvent(self, event):
        if hasattr(self, 'anillos') and hasattr(self.anillos, 'timer'):
            self.anillos.timer.stop()
        event.accept()