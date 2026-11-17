import time
from pathlib import Path

import pandas as pd
import requests

SALIDA = Path(__file__).resolve().parent.parent / "data" / "raw"
URL="https://archive-api.open-meteo.com/v1/archive"
CIUDADES = {
    "peninsular": {
        "madrid":     (40.42, -3.70),
        "barcelona":  (41.39,  2.17),
        "valencia":   (39.47, -0.38),
        "sevilla":    (37.39, -5.98),
        "malaga":     (36.72, -4.42),
        "alicante":   (38.35, -0.48),
        "murcia":     (37.98, -1.13),
        "bilbao":     (43.26, -2.93),
        "zaragoza":   (41.65, -0.88),
        "a_coruna":   (43.36, -8.41),
        "oviedo":     (43.36, -5.85),
        "valladolid": (41.65, -4.72),
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
