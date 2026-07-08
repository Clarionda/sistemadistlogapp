"""
Código Crítico - Tercer Semestre Año 2026
==================================================
VISTA DE MONITOR DE SINCRONIZACIÓN - VERIFICADOR TURSO EN VIVO
==================================================
📌 Muestra EXACTAMENTE lo que muestra verificar_turso.py pero EN VIVO:
    - Conexión a Turso
    - Tablas en Turso con cantidad de registros
    - Comparación Local vs Turso
    - Progreso en tiempo real
    - Estado de sincronización
"""

import sqlite3
import threading
import time
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFrame, QTextEdit,
                               QProgressBar, QWidget, QGroupBox, QGridLayout,
                               QTabWidget, QApplication, QScrollArea,
                               QSplitter, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont

from db.db_manager import _ruta_base_datos
from utilidades.turso_client import get_turso_client
from utilidades.sync_directo import get_turso_config


# ==================== CLASES DE ESTILO ====================

class LabelSeccionAzul(QLabel):
    def __init__(self, texto, parent=None):
        super().__init__(texto, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.setStyleSheet("""
            QLabel {
                background-color: #1A237E;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 10px;
            }
        """)


class VerificadorTursoThread(QThread):
    """Hilo que verifica Turso igual que verificar_turso.py"""
    
    actualizacion = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self._intervalo = 5  # segundos
    
    def stop(self):
        self._is_running = False
    
    def run(self):
        import sqlite3
        
        db_path = _ruta_base_datos()
        
        while self._is_running:
            try:
                datos = {
                    'tablas': {},
                    'conectado': False,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 1. Obtener conexión a Turso (como verificar_turso.py)
                url, token = get_turso_config()
                if not token:
                    self.actualizacion.emit(datos)
                    time.sleep(2)
                    continue
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                # 2. Verificar conexión (como verificar_turso.py)
                try:
                    payload_test = {
                        "requests": [
                            {"type": "execute", "stmt": {"sql": "SELECT 1 as test"}}
                        ]
                    }
                    response = requests.post(url, json=payload_test, headers=headers, timeout=5)
                    datos['conectado'] = response.status_code == 200
                except:
                    datos['conectado'] = False
                    self.actualizacion.emit(datos)
                    time.sleep(2)
                    continue
                
                # 3. Listar tablas en Turso (como verificar_turso.py)
                tablas_turso = []
                if datos['conectado']:
                    try:
                        payload = {
                            "requests": [
                                {
                                    "type": "execute",
                                    "stmt": {
                                        "sql": "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                                    }
                                }
                            ]
                        }
                        response = requests.post(url, json=payload, headers=headers, timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('results'):
                                result = data['results'][0]
                                if result.get('type') == 'ok':
                                    rows = result.get('response', {}).get('result', {}).get('rows', [])
                                    for row in rows:
                                        if row:
                                            # Extraer el nombre de la tabla (puede ser dict o string)
                                            if isinstance(row, dict):
                                                nombre = row.get('name', str(row))
                                            else:
                                                nombre = str(row)
                                            tablas_turso.append(nombre)
                    except Exception as e:
                        print(f"⚠️ Error listando tablas: {e}")
                
                # 4. Conectar a SQLite local
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # 5. Para cada tabla, contar registros (como verificar_turso.py)
                tablas_a_verificar = ['clientes', 'productos', 'preventistas', 'categorias', 'lotes', 'usuarios']
                
                for tabla in tablas_a_verificar:
                    # Contar local
                    try:
                        cur.execute(f"SELECT COUNT(*) as total FROM {tabla}")
                        row = cur.fetchone()
                        local = int(row['total']) if row and row['total'] is not None else 0
                    except:
                        local = 0
                    
                    # Contar en Turso
                    turso = 0
                    if datos['conectado'] and tabla in tablas_turso:
                        try:
                            payload = {
                                "requests": [
                                    {
                                        "type": "execute",
                                        "stmt": {
                                            "sql": f"SELECT COUNT(*) as total FROM {tabla}"
                                        }
                                    }
                                ]
                            }
                            response = requests.post(url, json=payload, headers=headers, timeout=5)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('results'):
                                    result = data['results'][0]
                                    if result.get('type') == 'ok':
                                        rows = result.get('response', {}).get('result', {}).get('rows', [])
                                        if rows:
                                            turso = int(rows[0][0]) if rows[0] else 0
                        except:
                            turso = 0
                    
                    # Calcular diferencia
                    diferencia = local - turso
                    
                    # Determinar estado (como verificar_turso.py)
                    if local == 0 and turso == 0:
                        estado = "sin_datos"
                        icono = "ℹ️"
                        mensaje = "Tabla vacía"
                    elif local > 0 and turso == 0:
                        estado = "sin_sincronizar"
                        icono = "⚠️"
                        mensaje = f"{diferencia} faltan"
                    elif local == turso and local > 0:
                        estado = "sincronizado"
                        icono = "✅"
                        mensaje = "Sincronizado"
                    elif local > turso:
                        estado = "parcial"
                        icono = "📤"
                        mensaje = f"{diferencia} faltan"
                    else:
                        estado = "desconocido"
                        icono = "❓"
                        mensaje = "Desconocido"
                    
                    datos['tablas'][tabla] = {
                        'local': local,
                        'turso': turso,
                        'diferencia': diferencia,
                        'estado': estado,
                        'icono': icono,
                        'mensaje': mensaje,
                        'en_turso': tabla in tablas_turso
                    }
                
                conn.close()
                
                # 6. Totales (como verificar_turso.py)
                total_local = sum(t['local'] for t in datos['tablas'].values())
                total_turso = sum(t['turso'] for t in datos['tablas'].values())
                total_diferencia = total_local - total_turso
                
                datos['total_local'] = total_local
                datos['total_turso'] = total_turso
                datos['total_diferencia'] = total_diferencia
                datos['tablas_turso'] = tablas_turso
                datos['timestamp'] = datetime.now().isoformat()
                
                self.actualizacion.emit(datos)
                
            except Exception as e:
                datos = {'error': str(e)}
                self.actualizacion.emit(datos)
            
            # Esperar intervalo
            for _ in range(self._intervalo):
                if not self._is_running:
                    break
                time.sleep(1)


class VistaMonitorSincronizacion(QDialog):
    """Ventana que muestra EXACTAMENTE lo que verificar_turso.py"""
    
    def __init__(self, db: sqlite3.Connection, parent=None):
        super().__init__(parent)
        self.db = db
        self.db_path = _ruta_base_datos()
        self._monitor_thread = None
        self._datos_actuales = {}
        
        self.setWindowTitle("📡 Monitor de Sincronización - Verificador Turso")
        self.setFixedSize(950, 720)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F2F5;
            }
            QPushButton {
                background-color: #1565C0;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QFrame {
                background-color: #E0E0E0;
                border-radius: 8px;
                border: 1px solid #D0D0D0;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #B0BEC5;
                border-radius: 5px;
                font-size: 9px;
                gridline-color: #A0A0A0;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                background-color: transparent;
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #1565C0;
                color: white;
            }
            QHeaderView::section {
                background-color: #1565C0;
                color: white;
                padding: 5px;
                font-weight: 600;
                border: none;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #B0BEC5;
                border-radius: 5px;
                font-family: monospace;
                font-size: 9px;
            }
            QProgressBar {
                border: 1px solid #B0BEC5;
                border-radius: 5px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background-color: #1565C0;
            }
        """)
        
        self._setup_ui()
        self._iniciar_monitoreo()
    
    def _setup_ui(self):
        """Configura la interfaz igual que verificar_turso.py"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        tarjeta = QFrame()
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(10, 10, 10, 10)
        tarjeta_layout.setSpacing(8)
        
        # ============================================================
        # TÍTULO (como verificar_turso.py)
        # ============================================================
        tarjeta_layout.addWidget(LabelSeccionAzul("🔍 VERIFICANDO SINCRONIZACIÓN CON TURSO"))
        
        # ============================================================
        # ESTADO DE CONEXIÓN (como verificar_turso.py)
        # ============================================================
        frame_conexion = QFrame()
        frame_conexion.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #D0D0D0; }")
        conexion_layout = QHBoxLayout(frame_conexion)
        conexion_layout.setContentsMargins(10, 8, 10, 8)
        conexion_layout.setSpacing(15)
        
        self.lbl_estado = QLabel("🔴 Desconectado")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 12px;")
        conexion_layout.addWidget(self.lbl_estado)
        
        self.lbl_consultas = QLabel("📊 Consultas: 0")
        self.lbl_consultas.setStyleSheet("font-size: 11px; color: #666;")
        conexion_layout.addWidget(self.lbl_consultas)
        
        self.lbl_ultima = QLabel("🕐 -")
        self.lbl_ultima.setStyleSheet("font-size: 10px; color: #999;")
        conexion_layout.addWidget(self.lbl_ultima)
        
        conexion_layout.addStretch()
        
        tarjeta_layout.addWidget(frame_conexion)
        
        # ============================================================
        # TABLA DE TABLAS EN TURSO (como verificar_turso.py)
        # ============================================================
        frame_tablas = QFrame()
        frame_tablas.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #D0D0D0; }")
        tablas_layout = QVBoxLayout(frame_tablas)
        tablas_layout.setContentsMargins(5, 5, 5, 5)
        
        tablas_layout.addWidget(LabelSeccionAzul("📋 TABLAS EN TURSO"))
        
        self.tabla_tablas = QTableWidget()
        self.tabla_tablas.setColumnCount(3)
        self.tabla_tablas.setHorizontalHeaderLabels(["Tabla", "Registros", "Estado"])
        self.tabla_tablas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_tablas.setColumnWidth(1, 150)
        self.tabla_tablas.setColumnWidth(2, 200)
        self.tabla_tablas.setShowGrid(True)
        self.tabla_tablas.setGridStyle(Qt.PenStyle.SolidLine)
        self.tabla_tablas.setAlternatingRowColors(True)
        self.tabla_tablas.setMinimumHeight(200)
        tablas_layout.addWidget(self.tabla_tablas)
        
        tarjeta_layout.addWidget(frame_tablas)
        
        # ============================================================
        # COMPARACIÓN LOCAL VS TURSO (como verificar_turso.py)
        # ============================================================
        frame_comparacion = QFrame()
        frame_comparacion.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #D0D0D0; }")
        comparacion_layout = QVBoxLayout(frame_comparacion)
        comparacion_layout.setContentsMargins(5, 5, 5, 5)
        
        comparacion_layout.addWidget(LabelSeccionAzul("📊 COMPARACIÓN LOCAL VS TURSO"))
        
        self.tabla_comparacion = QTableWidget()
        self.tabla_comparacion.setColumnCount(5)
        self.tabla_comparacion.setHorizontalHeaderLabels(["Tabla", "Local", "Turso", "Diferencia", "Estado"])
        self.tabla_comparacion.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_comparacion.setColumnWidth(1, 100)
        self.tabla_comparacion.setColumnWidth(2, 100)
        self.tabla_comparacion.setColumnWidth(3, 100)
        self.tabla_comparacion.setColumnWidth(4, 150)
        self.tabla_comparacion.setShowGrid(True)
        self.tabla_comparacion.setGridStyle(Qt.PenStyle.SolidLine)
        self.tabla_comparacion.setAlternatingRowColors(True)
        self.tabla_comparacion.setMinimumHeight(200)
        comparacion_layout.addWidget(self.tabla_comparacion)
        
        tarjeta_layout.addWidget(frame_comparacion)
        
        # ============================================================
        # BOTONES
        # ============================================================
        frame_botones = QFrame()
        frame_botones.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #D0D0D0; }")
        botones_layout = QHBoxLayout(frame_botones)
        botones_layout.setContentsMargins(10, 8, 10, 8)
        botones_layout.setSpacing(10)
        
        btn_refrescar = QPushButton("🔄 Refrescar")
        btn_refrescar.setStyleSheet("background-color: #1565C0;")
        btn_refrescar.clicked.connect(self._forzar_actualizacion)
        botones_layout.addWidget(btn_refrescar)
        
        btn_sincronizar = QPushButton("🔄 Sincronizar Ahora")
        btn_sincronizar.setStyleSheet("background-color: #4CAF50;")
        btn_sincronizar.clicked.connect(self._ejecutar_sincronizacion)
        botones_layout.addWidget(btn_sincronizar)
        
        botones_layout.addStretch()
        
        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.setStyleSheet("background-color: #D32F2F;")
        btn_cerrar.clicked.connect(self.close)
        botones_layout.addWidget(btn_cerrar)
        
        tarjeta_layout.addWidget(frame_botones)
        
        layout.addWidget(tarjeta)
    
    def _iniciar_monitoreo(self):
        """Inicia el monitoreo automático"""
        self._monitor_thread = VerificadorTursoThread()
        self._monitor_thread.actualizacion.connect(self._on_actualizacion)
        self._monitor_thread.start()
        
        self._actualizar_estado("🔄", "Iniciando monitoreo...")
    
    def _on_actualizacion(self, datos):
        """Recibe actualización del verificador"""
        if 'error' in datos:
            self._actualizar_estado("❌", f"Error: {datos['error']}")
            return
        
        self._datos_actuales = datos
        
        # Actualizar conexión
        if datos.get('conectado', False):
            self._actualizar_estado("✅", "Conectado a Turso")
            self.lbl_estado.setText("🟢 Conectado a Turso")
            self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 12px; color: #4CAF50;")
        else:
            self._actualizar_estado("⚠️", "Sin conexión a Turso")
            self.lbl_estado.setText("🔴 Desconectado")
            self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 12px; color: #D32F2F;")
        
        # Actualizar consultas
        self.lbl_consultas.setText(f"📊 Consultas: {len(datos.get('tablas', {}))}")
        
        # Actualizar timestamp
        if datos.get('timestamp'):
            ts = datetime.fromisoformat(datos['timestamp']).strftime("%H:%M:%S")
            self.lbl_ultima.setText(f"🕐 {ts}")
        
        # ============================================================
        # ACTUALIZAR TABLA DE TABLAS EN TURSO (como verificar_turso.py)
        # ============================================================
        tablas_turso = datos.get('tablas_turso', [])
        tablas_info = datos.get('tablas', {})
        
        self.tabla_tablas.setRowCount(len(tablas_turso))
        for i, tabla in enumerate(tablas_turso):
            # ✅ CORREGIDO: Extraer el nombre de la tabla si es un diccionario
            if isinstance(tabla, dict):
                nombre_tabla = tabla.get('name', str(tabla))
            else:
                nombre_tabla = str(tabla)
            
            self.tabla_tablas.setItem(i, 0, QTableWidgetItem(nombre_tabla))
            
            # Registros
            info = tablas_info.get(nombre_tabla, {})
            turso = info.get('turso', 0)
            item_reg = QTableWidgetItem(str(turso))
            item_reg.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if turso > 0:
                item_reg.setForeground(QColor(40, 167, 69))
            else:
                item_reg.setForeground(QColor(255, 165, 0))
            self.tabla_tablas.setItem(i, 1, item_reg)
            
            # Estado
            estado = info.get('estado', 'desconocido')
            icono = info.get('icono', '❓')
            mensaje = info.get('mensaje', '')
            
            item_estado = QTableWidgetItem(f"{icono} {mensaje}")
            if estado == 'sincronizado':
                item_estado.setForeground(QColor(40, 167, 69))
            elif estado in ['sin_sincronizar', 'parcial']:
                item_estado.setForeground(QColor(255, 165, 0))
            else:
                item_estado.setForeground(QColor(108, 117, 125))
            self.tabla_tablas.setItem(i, 2, item_estado)
        
        # ============================================================
        # ACTUALIZAR COMPARACIÓN LOCAL VS TURSO
        # ============================================================
        tablas = ['clientes', 'productos', 'preventistas', 'categorias', 'lotes', 'usuarios']
        
        self.tabla_comparacion.setRowCount(len(tablas))
        for i, tabla in enumerate(tablas):
            info = tablas_info.get(tabla, {})
            local = info.get('local', 0)
            turso = info.get('turso', 0)
            diferencia = info.get('diferencia', 0)
            icono = info.get('icono', '❓')
            mensaje = info.get('mensaje', '')
            
            # Nombre
            self.tabla_comparacion.setItem(i, 0, QTableWidgetItem(tabla))
            
            # Local
            item_local = QTableWidgetItem(str(local))
            item_local.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.tabla_comparacion.setItem(i, 1, item_local)
            
            # Turso
            item_turso = QTableWidgetItem(str(turso))
            item_turso.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if turso > 0:
                item_turso.setForeground(QColor(40, 167, 69))
            self.tabla_comparacion.setItem(i, 2, item_turso)
            
            # Diferencia
            item_diff = QTableWidgetItem(str(diferencia))
            item_diff.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if diferencia > 0:
                item_diff.setForeground(QColor(255, 165, 0))
            elif diferencia == 0 and local > 0:
                item_diff.setForeground(QColor(40, 167, 69))
            self.tabla_comparacion.setItem(i, 3, item_diff)
            
            # Estado
            item_estado = QTableWidgetItem(f"{icono} {mensaje}")
            if diferencia == 0 and local > 0:
                item_estado.setForeground(QColor(40, 167, 69))
            elif diferencia > 0:
                item_estado.setForeground(QColor(255, 165, 0))
            else:
                item_estado.setForeground(QColor(108, 117, 125))
            self.tabla_comparacion.setItem(i, 4, item_estado)
        
        # ============================================================
        # RESALTAR FILAS CON DIFERENCIAS
        # ============================================================
        for i in range(self.tabla_comparacion.rowCount()):
            item_diff = self.tabla_comparacion.item(i, 3)
            if item_diff and int(item_diff.text()) > 0:
                for col in range(5):
                    item = self.tabla_comparacion.item(i, col)
                    if item:
                        item.setBackground(QColor(255, 248, 225))
            elif item_diff and int(item_diff.text()) == 0:
                for col in range(5):
                    item = self.tabla_comparacion.item(i, col)
                    if item:
                        item.setBackground(QColor(232, 245, 233))
    
    def _actualizar_estado(self, icono, mensaje):
        """Actualiza el estado en la barra"""
        pass
    
    def _forzar_actualizacion(self):
        """Fuerza una actualización inmediata"""
        if self._monitor_thread:
            self._monitor_thread.stop()
            self._monitor_thread.wait(1000)
            self._monitor_thread = VerificadorTursoThread()
            self._monitor_thread.actualizacion.connect(self._on_actualizacion)
            self._monitor_thread.start()
    
    def _ejecutar_sincronizacion(self):
        """Ejecuta sincronización manual"""
        from utilidades.central_sync import sincronizar_ahora
        from db.db_manager import obtener_conexion
        
        try:
            db = obtener_conexion()
            resultado = sincronizar_ahora(db)
            
            QMessageBox.information(self, "Sincronización", "✅ Sincronización completada")
            self._forzar_actualizacion()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en sincronización: {e}")
    
    def closeEvent(self, event):
        """Cierra el monitor"""
        if self._monitor_thread:
            self._monitor_thread.stop()
            self._monitor_thread.wait(2000)
        event.accept()


def abrir_monitor_sincronizacion(db, parent=None):
    """Abre el monitor de sincronización"""
    dialog = VistaMonitorSincronizacion(db, parent)
    dialog.exec()