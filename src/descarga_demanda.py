import time
from pathlib import Path

import pandas as pd
import requests

SALIDA = Path(__file__).resolve().parent.parent / "data" / "raw"
URL="https://apidatos.ree.es/es/datos/demanda/evolucion"
ZONAS={"peninsular": 8741,
       "canarias": 8742,
       "baleares": 8743}
AÑOS=range(2021,2026)

def descargar(sistema, geo_id, año):
    params = {
        "start_date": f"{año}-01-01T00:00",
        "end_date":   f"{año}-12-31T23:59",
        "time_trunc": "day",
        "geo_trunc":  "electric_system",
        "geo_limit":  sistema,
        "geo_ids":    geo_id,
    }
    resp = requests.get(URL, params=params, timeout=30)
    if resp.status_code != 200:
        print(sistema,año)
        print("Error", resp.status_code)
        print(resp.text[:300])
        raise SystemExit
    datos = resp.json()
    
    df=pd.DataFrame(datos["included"][0]["attributes"]["values"])
    df["fecha"]=pd.to_datetime(df["datetime"].str[:10])
    df=df.rename(columns={"value": "demanda_mwh"})
    df = df[["fecha", "demanda_mwh"]]
    return df

# Lo que se ejecuta al lanzar el script
if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    for sistema, geo_id in ZONAS.items():
        trozos=[]
        for año in AÑOS:
            time.sleep(1)
            df_año=descargar(sistema,geo_id,año)
            trozos.append(df_año)
        df=pd.concat(trozos, ignore_index=True)
        df.to_csv(SALIDA / f"demanda_{sistema}.csv", index=False)
        
