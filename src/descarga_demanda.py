"""Descarga la demanda eléctrica diaria de REData (Red Eléctrica) por sistema.

Genera data/raw/demanda_{sistema}.csv con las columnas fecha y demanda_mwh.
La API de REData es pública y no pide token (a diferencia de ESIOS).
Solo admite un año por petición con time_trunc=day, así que se pide año a año.
"""

import time

import pandas as pd
import requests

from config import ANIO_FIN, ANIO_INICIO, DATOS_RAW

URL = "https://apidatos.ree.es/es/datos/demanda/evolucion"
ZONAS = {
    "peninsular": 8741,
    "canarias": 8742,
    "baleares": 8743,
}


def descargar(sistema, geo_id, anio):
    """Demanda diaria de un sistema durante un año, en MWh."""
    params = {
        "start_date": f"{anio}-01-01T00:00",
        "end_date": f"{anio}-12-31T23:59",
        "time_trunc": "day",
        "geo_trunc": "electric_system",
        "geo_limit": sistema,
        "geo_ids": geo_id,
    }
    resp = requests.get(URL, params=params, timeout=30)
    resp.raise_for_status()

    # Los valores diarios de la demanda están en included[0].attributes.values
    valores = resp.json()["included"][0]["attributes"]["values"]
    df = pd.DataFrame(valores)
    df["fecha"] = pd.to_datetime(df["datetime"].str[:10])  # transformo en formato fecha de pandas y me quedo con YY-MM-DD
    df = df.rename(columns={"value": "demanda_mwh"})
    return df[["fecha", "demanda_mwh"]]


if __name__ == "__main__":
    DATOS_RAW.mkdir(parents=True, exist_ok=True)
    for sistema, geo_id in ZONAS.items():
        trozos = []
        for anio in range(ANIO_INICIO, ANIO_FIN + 1):
            time.sleep(1)  # no saturar la API
            trozos.append(descargar(sistema, geo_id, anio))
        df = pd.concat(trozos, ignore_index=True)
        df.to_csv(DATOS_RAW / f"demanda_{sistema}.csv", index=False)
        print(f"{sistema}: {len(df)} días")
