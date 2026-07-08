"""
Código Crítico - Tercer Semestre - Año 2026
Punto de entrada principal de la aplicación.
Maneja el ciclo de vida: Login -> Principal -> Login -> Salir
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from database import inicializar_base_datos
from sync import iniciar_hilo_sincronizacion
from ventana_login import LoginDialog
from ventana_principal import VentanaPrincipal
from splash import SplashBienvenida

class Aplicacion:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ventana_principal = None
        self.login = None
        self.sync_iniciado = False
        
    def iniciar_sync(self):
        """Inicia el hilo de sincronización solo una vez."""
        if not self.sync_iniciado:
            iniciar_hilo_sincronizacion()
            self.sync_iniciado = True
            print("✅ Sincronización iniciada")
    
    def mostrar_login(self):
        """Muestra el diálogo de login."""
        if self.ventana_principal:
            self.ventana_principal.close()
            self.ventana_principal = None
        
        self.login = LoginDialog()
        self.login.accepted.connect(self.login_exitoso)
        self.login.rejected.connect(self.salir_aplicacion)
        self.login.salir_app_signal.connect(self.salir_aplicacion)
        
        self.login.show()
        print("🔐 Mostrando login")
    
    def login_exitoso(self):
        """Cuando el login es exitoso, mostrar ventana principal."""
        if self.login:
            self.login.close()
            self.login = None
        
        self.iniciar_sync()
        
        self.ventana_principal = VentanaPrincipal()
        self.ventana_principal.cerrar_sesion_signal.connect(self.mostrar_login)
        
        self.ventana_principal.show()
        print("🏠 Ventana principal mostrada")
    
    def salir_aplicacion(self):
        """Cierra toda la aplicación."""
        print("👋 Saliendo de la aplicación...")
        sys.exit(0)
    
    def ejecutar(self):
        """Inicia la aplicación con splash y login."""
        inicializar_base_datos()
        
        splash = SplashBienvenida()
        splash.terminado.connect(self.mostrar_login)
        splash.terminado.connect(self.iniciar_sync)
        
        sys.exit(self.app.exec())

def main():
    app = Aplicacion()
    app.ejecutar()

if __name__ == "__main__":
    main()