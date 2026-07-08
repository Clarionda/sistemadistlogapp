import requests
import time

def geocodificar_direccion(calle, numero, localidad, provincia, pais="Argentina"):
    """
    Convierte una dirección en coordenadas (lat, lon) usando Nominatim (OpenStreetMap).
    Retorna (latitud, longitud) o (None, None) si falla.
    """
    if not calle or not localidad or not provincia:
        return None, None
    
    direccion = f"{calle} {numero}, {localidad}, {provincia}, {pais}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": direccion,
        "format": "json",
        "limit": 1,
        "addressdetails": 0
    }
    headers = {
        "User-Agent": "DistribuidoraApp/1.0 (sistema de gestión de preventistas)"
    }
    try:
        time.sleep(1)  # Respetar límite de 1 solicitud por segundo
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon
    except Exception as e:
        print(f"Error de geocodificación: {e}")
    return None, None