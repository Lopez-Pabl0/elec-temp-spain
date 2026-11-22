"""Une demanda y temperatura de cada sistema y crea las variables del modelo."""

import holidays
import pandas as pd

from config import DATOS_RAW
from poblacion import POBLACION

# t_base: temperatura de mínima demanda, leída en el 01_eda.ipynb (tramos de 1 °C, laborables).
# subdiv: comunidad para los festivos autonómicos; en la península solo nacionales.
CONFIG = {
    "peninsular": {"t_base": 17, "subdiv": None},
    "baleares": {"t_base": 16, "subdiv": "IB"},
    "canarias": {"t_base": 16, "subdiv": "CN"},
}


def cargar_sistema(sistema):
    """Quiero la Demanda diaria y temperatura ponderada por población de un sistema.
    Uso los datos descargados anteriormente en los CSV.

    Cada provincia pesa según su población; la temperatura del sistema es la
    media ponderada de las temperaturas de sus capitales.
    """
    pesos = pd.Series(POBLACION[sistema])
    pesos = pesos / pesos.sum() #ponderación basada en la población

    temperatura = pd.read_csv(
        DATOS_RAW / f"temperatura_{sistema}.csv", parse_dates=["fecha"], index_col="fecha"
    )
    #multiplico la temperatura de las ciudades por sus pesos y las sumo, ahora tengo una solo columna "temperatura"
    temperatura = (temperatura * pesos).sum(axis=1).rename("temperatura") 

    demanda = pd.read_csv(
        DATOS_RAW / f"demanda_{sistema}.csv", parse_dates=["fecha"], index_col="fecha"
    )
    return pd.concat([demanda, temperatura], axis=1)


def crear_features(df, t_base, subdiv):
    """Añade las nuevas variables del modelo: HDD, CDD, día de la semana, festivo, año y mes."""
    df = df.copy()
    df["hdd"] = (t_base - df["temperatura"]).clip(lower=0)
    df["cdd"] = (df["temperatura"] - t_base).clip(lower=0)
    df["dia_semana"] = df.index.day_of_week  # 0 = lunes ... 6 = domingo

    fest = holidays.Spain(years=df.index.year.unique(), subdiv=subdiv) # da los festivos por sistema
    fechas_festivas = pd.to_datetime(list(fest.keys()))
    # Solo cuenta si cae en laborable: el fin de semana ya lo recoge dia_semana
    df["festivo"] = (df.index.isin(fechas_festivas) & (df.index.day_of_week < 5)).astype(int)

    df["anio"] = df.index.year
    df["mes"] = df.index.month
    return df


if __name__ == "__main__":
    for sistema, cfg in CONFIG.items():
        df = crear_features(cargar_sistema(sistema), **cfg)
        #comprobaciones de que todo va bien
        print(f"=== {sistema} ===")
        print("shape:", df.shape)
        print("valores vacíos:", int(df.isna().sum().sum()))
        print("festivos por año:", df["festivo"].groupby(df["anio"]).sum().to_dict())
        print("días con HDD > 0:", (df["hdd"] > 0).sum())
        print("días con CDD > 0:", (df["cdd"] > 0).sum())
        print()
