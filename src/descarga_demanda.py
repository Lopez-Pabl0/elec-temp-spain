from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent   # src/ → raíz del proyecto
salida = RAIZ / "data" / "raw"
salida.mkdir(parents=True, exist_ok=True)       # crea la carpeta si no existe


# 1) Creo primero la url básica
url="https://apidatos.ree.es/es/datos/demanda/evolucion"

# 2) Los parámetros van en un diccionario: requests los añade tras el "?"
# vamos primero con la peninsula, luego lo automatizo

params = {
    "start_date": "2021-01-01T00:00",
    "end_date": "2021-12-31T23:59",
    "time_trunc": "day",
    "geo_trunc": "electric_system",
    "geo_limit": "peninsular",
    "geo_ids": "8741"
}

# 3) Hacemos la petición GET
resp = requests.get(url, params=params, timeout=30)
if resp.status_code != 200:
    print("Error", resp.status_code)
    print(resp.text[:300])
    raise SystemExit
# 4) Pasamos los datos a un JSON-> DataFrame-> CSV
datos = resp.json()
df=pd.DataFrame(datos["included"][0]["attributes"]["values"]) # tabla de 365 filas × 3 columnas con cada fila un dict de value-percentage-datetime
#limpio estos datos
df["fecha"]=pd.to_datetime(df["datetime"].str[:10])
df=df.rename(columns={"value": "demanda_mwh"})
df = df[["fecha", "demanda_mwh"]]
df.to_csv(salida / "demanda_peninsular_2021.csv", index=False)