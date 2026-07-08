"""
Código Crítico - Tercer Semestre - Año 2026
Módulo de ubicación y GPS con sincronización PyTurso
"""

import uuid
import threading
from PyQt6.QtCore import QObject, QTimer
from database import ejecutar_consulta, sincronizar_tabla_completa
from auth import obtener_preventista_id

# Importación condicional de QtPositioning
try:
    from PyQt6.QtPositioning import QGeoPositionInfoSource
    GPS_DISPONIBLE = True
except ImportError:
    GPS_DISPONIBLE = False
    print("Advertencia: QtPositioning no disponible. El GPS no funcionará.")


class RastreadorUbicacion(QObject):
    """Rastrea la ubicación GPS y la sincroniza con Turso"""
    
    def __init__(self):
        super().__init__()
        self.source = None
        self.ultima_posicion = (None, None)
        self._sync_pendiente = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.obtener_y_guardar_posicion)
        self.timer.start(30000)  # Cada 30 segundos
        
        if GPS_DISPONIBLE:
            self.iniciar_gps()
        else:
            print("GPS desactivado (módulo QtPositioning no encontrado)")

    def iniciar_gps(self):
        """Inicia el GPS"""
        self.source = QGeoPositionInfoSource.createDefaultSource(self)
        if self.source:
            self.source.positionUpdated.connect(self.guardar_posicion)
            self.source.startUpdates()
            print("✅ GPS iniciado")
        else:
            print("⚠️ No se pudo iniciar GPS (sin hardware o permisos)")

    def guardar_posicion(self, info):
        """Guarda la posición GPS obtenida"""
        if not GPS_DISPONIBLE:
            return
        coord = info.coordinate()
        if coord.isValid():
            lat = coord.latitude()
            lon = coord.longitude()
            self.ultima_posicion = (lat, lon)
            
            preventista_id = obtener_preventista_id()
            if preventista_id:
                id_pos = str(uuid.uuid4())
                ejecutar_consulta("""
                    INSERT INTO posiciones_preventistas (id, preventista_id, latitud, longitud, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (id_pos, preventista_id, lat, lon), commit=True)
                print(f"📍 Posición guardada: {lat}, {lon}")
                
                # ✅ Sincronizar inmediatamente con PyTurso
                self._sincronizar_posicion()

    def _sincronizar_posicion(self):
        """Sincroniza la posición con Turso usando PyTurso"""
        if self._sync_pendiente:
            return
        
        self._sync_pendiente = True
        
        def _sync():
            try:
                from turso_client import subir_tabla_pyturso
                subir_tabla_pyturso('posiciones_preventistas')
                print("✅ Posición sincronizada con Turso")
            except ImportError:
                # Fallback
                from sync import subir_tabla
                subir_tabla('posiciones_preventistas')
                print("✅ Posición sincronizada (fallback HTTP)")
            except Exception as e:
                print(f"⚠️ Error sincronizando posición: {e}")
            finally:
                self._sync_pendiente = False
        
        threading.Thread(target=_sync, daemon=True).start()

    def obtener_y_guardar_posicion(self):
        """Solicita una actualización de posición"""
        if GPS_DISPONIBLE and self.source:
            self.source.requestUpdate()

    def obtener_ultima_posicion(self):
        """Obtiene la última posición conocida"""
        if self.ultima_posicion != (None, None):
            return self.ultima_posicion
        
        # Buscar en la base de datos
        filas = ejecutar_consulta(
            "SELECT latitud, longitud FROM posiciones_preventistas ORDER BY created_at DESC LIMIT 1"
        )
        if filas:
            lat = filas[0]["latitud"]
            lon = filas[0]["longitud"]
            self.ultima_posicion = (lat, lon)
            return lat, lon
        return None, None


def registrar_visita_cliente(cliente_id):
    """Registra una visita a un cliente y la sincroniza con Turso"""
    from auth import obtener_usuario_actual
    usuario = obtener_usuario_actual()
    if not usuario:
        return
    
    preventista_id = usuario.get("preventista_id")
    if not preventista_id:
        return
    
    id_visita = str(uuid.uuid4())
    lat, lon = None, None
    
    # Obtener última posición del rastreador
    if hasattr(registrar_visita_cliente, "rastreador"):
        lat, lon = registrar_visita_cliente.rastreador.obtener_ultima_posicion()
    
    # Guardar visita
    ejecutar_consulta("""
        INSERT INTO visitas_clientes (id, preventista_id, cliente_id, fecha_hora, latitud, longitud, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
    """, (id_visita, preventista_id, cliente_id, lat, lon), commit=True)
    
    print(f"📍 Visita registrada: cliente {cliente_id} por preventista {preventista_id}")
    
    # ✅ Sincronizar visita con Turso
    def _sync_visita():
        try:
            from turso_client import subir_tabla_pyturso
            subir_tabla_pyturso('visitas_clientes')
            print("✅ Visita sincronizada con Turso")
        except ImportError:
            from sync import subir_tabla
            subir_tabla('visitas_clientes')
        except Exception as e:
            print(f"⚠️ Error sincronizando visita: {e}")
    
    threading.Thread(target=_sync_visita, daemon=True).start()