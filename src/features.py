from pathlib import Path

import holidays
import pandas as pd

from poblacion import POBLACION

DATOS = Path(__file__).resolve().parent.parent / "data" / "raw"

CONFIG = {
    "peninsular": {"t_base": 17, "subdiv": None},
    "baleares": {"t_base": 16, "subdiv": "IB"},
    "canarias": {"t_base": 16, "subdiv": "CN"},
}


def cargar_sistema(sistema):
    pesos = pd.Series(POBLACION[sistema])
    pesos = pesos / pesos.sum()

    temperatura = pd.read_csv(DATOS / f"temperatura_{sistema}.csv", parse_dates=["fecha"], index_col="fecha")
    temperatura = (temperatura * pesos).sum(axis=1).rename("temperatura")

    demanda = pd.read_csv(DATOS / f"demanda_{sistema}.csv", parse_dates=["fecha"], index_col="fecha")
    df = pd.concat([demanda, temperatura], axis=1)
    return df


def crear_features(df, t_base, subdiv):
    df = df.copy()
    df["hdd"] = (t_base - df["temperatura"]).clip(lower=0)
    df["cdd"] = (df["temperatura"] - t_base).clip(lower=0)
    df["dia_semana"] = df.index.day_of_week

    fest = holidays.Spain(years=df.index.year.unique(), subdiv=subdiv)
    fechas_festivas = pd.to_datetime(list(fest.keys()))
    df["festivo"] = ( (df.index.isin(fechas_festivas)) & (df.index.day_of_week<5)).astype(int) # festivo solo si cae en laborable (en finde ya lo recoge dia_semana)
    df["anio"] = df.index.year
    return df


if __name__ == "__main__":
    for sistema, cfg in CONFIG.items():
        df = cargar_sistema(sistema)
        df = crear_features(df, **cfg)

        print(f"=== {sistema} ===")
        print("shape:", df.shape)
        print("valores vacíos:", int(df.isna().sum().sum()))
        print("festivos por año:", df["festivo"].groupby(df["anio"]).sum().to_dict())
        print("días con HDD > 0:", (df["hdd"] > 0).sum())
        print("días con CDD > 0:", (df["cdd"] > 0).sum())
        print()
