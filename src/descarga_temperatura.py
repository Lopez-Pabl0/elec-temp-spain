import time
from pathlib import Path

import pandas as pd
import requests

SALIDA = Path(__file__).resolve().parent.parent / "data" / "raw"
URL="https://archive-api.open-meteo.com/v1/archive"
CIUDADES = {
    "peninsular": {
        # Andalucía
        "almeria":     (36.84, -2.46),
        "cadiz":       (36.53, -6.29),
        "cordoba":     (37.89, -4.78),
        "granada":     (37.18, -3.60),
        "huelva":      (37.26, -6.95),
        "jaen":        (37.77, -3.79),
        "malaga":      (36.72, -4.42),
        "sevilla":     (37.39, -5.98),
        # Aragón
        "huesca":      (42.14, -0.41),
        "teruel":      (40.34, -1.11),
        "zaragoza":    (41.65, -0.88),
        # Asturias (Oviedo)
        "asturias":    (43.36, -5.85),
        # Cantabria (Santander)
        "cantabria":   (43.46, -3.81),
        # Castilla-La Mancha
        "albacete":    (38.99, -1.86),
        "ciudad_real": (38.99, -3.93),
        "cuenca":      (40.07, -2.14),
        "guadalajara": (40.63, -3.16),
        "toledo":      (39.86, -4.03),
        # Castilla y León
        "avila":       (40.66, -4.70),
        "burgos":      (42.34, -3.70),
        "leon":        (42.60, -5.57),
        "palencia":    (42.01, -4.53),
        "salamanca":   (40.97, -5.66),
        "segovia":     (40.95, -4.12),
        "soria":       (41.76, -2.46),
        "valladolid":  (41.65, -4.72),
        "zamora":      (41.50, -5.75),
        # Cataluña
        "barcelona":   (41.39,  2.17),
        "girona":      (41.98,  2.82),
        "lleida":      (41.62,  0.62),
        "tarragona":   (41.12,  1.25),
        # Comunidad Valenciana
        "alicante":    (38.35, -0.48),
        "castellon":   (39.99, -0.05),
        "valencia":    (39.47, -0.38),
        # Extremadura
        "badajoz":     (38.88, -6.97),
        "caceres":     (39.47, -6.37),
        # Galicia
        "a_coruna":    (43.36, -8.41),
        "lugo":        (43.01, -7.56),
        "ourense":     (42.34, -7.86),
        "pontevedra":  (42.43, -8.64),
        # Madrid
        "madrid":      (40.42, -3.70),
        # Murcia
        "murcia":      (37.98, -1.13),
        # Navarra (Pamplona)
        "navarra":     (42.81, -1.64),
        # País Vasco
        "araba":       (42.85, -2.67),   # Vitoria-Gasteiz
        "bizkaia":     (43.26, -2.93),   # Bilbao
        "gipuzkoa":    (43.32, -1.98),   # Donostia-San Sebastián
        # La Rioja (Logroño)
        "la_rioja":    (42.47, -2.45),
    },
    "baleares": {
        "palma": (39.57, 2.65),
        "ibiza": (38.91, 1.43),
        "mahon": (39.89, 4.27),
    },
    "canarias": {
        "las_palmas":          (28.10, -15.42),
        "santa_cruz_tenerife": (28.47, -16.25),
    },
}

def descargar(lat, lon):
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": "2021-01-01",
        "end_date":   "2025-12-31",
        "daily":      "temperature_2m_mean",
        "timezone":   "Europe/Madrid",
    }
    resp = requests.get(URL, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Lat={lat}, Long={lon}")
        print("Error", resp.status_code)
        print(resp.text[:300])
        raise SystemExit
    datos = resp.json()
    
    df = pd.DataFrame(datos["daily"])
    df["time"]=pd.to_datetime(df["time"])
    df=df.rename(columns={"time": "fecha", "temperature_2m_mean": "temperatura" })
    df = df[["fecha", "temperatura"]]
    return df

# Lo que se ejecuta al lanzar el script
if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    for sistema, ciudades in CIUDADES.items():
        columnas = {}
        for ciudad, (lat, lon) in ciudades.items():
            time.sleep(1)
            df_ciudad = descargar(lat, lon)
            columnas[ciudad]=df_ciudad.set_index("fecha")["temperatura"]  
        df = pd.concat(columnas, axis=1)
        df.to_csv(SALIDA / f"temperatura_{sistema}.csv")
