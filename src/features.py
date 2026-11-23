"""Une demanda y temperatura de cada sistema y crea las variables del modelo.

Lo usan los tres notebooks y src/modelo.py:
  - cargar_sistema(sistema): demanda diaria y temperatura ponderada por población;
  - crear_features(df, **CONFIG[sistema]): añade las variables del modelo;
  - CONFIG: T_base y festivos autonómicos de cada sistema.

Necesita los CSV de data/raw/ que generan descarga_demanda.py y descarga_temperatura.py.
"""

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
    """Demanda diaria y temperatura ponderada por población de un sistema.

    Lee data/raw/demanda_{sistema}.csv y data/raw/temperatura_{sistema}.csv.
    Cada provincia pesa según su población; la temperatura del sistema es la
    media ponderada de las temperaturas de sus capitales.

    Devuelve un DataFrame con la fecha como índice y las columnas
    demanda_mwh (MWh/día) y temperatura (°C).
    """
    pesos = pd.Series(POBLACION[sistema])
    pesos = pesos / pesos.sum() # ponderación basada en la población

    temperatura = pd.read_csv(
        DATOS_RAW / f"temperatura_{sistema}.csv", parse_dates=["fecha"], index_col="fecha"
    )
    # Las ciudades se emparejan con su población por nombre: si alguna no casa, su
    # temperatura se perdería sin avisar al sumar, así que lo compruebo antes.
    if set(temperatura.columns) != set(pesos.index):
        raise ValueError(
            f"Las ciudades de temperatura_{sistema}.csv no coinciden con poblacion.py: "
            f"sobran {sorted(set(temperatura.columns) - set(pesos.index))}, "
            f"faltan {sorted(set(pesos.index) - set(temperatura.columns))}"
        )
    # multiplico la temperatura de las ciudades por sus pesos y las sumo, ahora tengo una solo columna "temperatura"
    temperatura = (temperatura * pesos).sum(axis=1).rename("temperatura") 

    demanda = pd.read_csv(
        DATOS_RAW / f"demanda_{sistema}.csv", parse_dates=["fecha"], index_col="fecha"
    )
    return pd.concat([demanda, temperatura], axis=1)


def crear_features(df, t_base, subdiv):
    """Añade las variables del modelo a la salida de cargar_sistema.

    - hdd, cdd: grados-día de frío y de calor, max(t_base − T, 0) y max(T − t_base, 0)
    - dia_semana: 0 = lunes ... 6 = domingo
    - festivo: 1 si es festivo y cae en laborable (en fin de semana ya lo recoge dia_semana);
      nacionales y, si subdiv no es None, también los de esa comunidad
    - anio, mes
    """
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
        # comprobaciones de que todo va bien
        print(f"=== {sistema} ===")
        print("shape:", df.shape)
        print("valores vacíos:", int(df.isna().sum().sum()))
        print("festivos por año:", df["festivo"].groupby(df["anio"]).sum().to_dict())
        print("días con HDD > 0:", (df["hdd"] > 0).sum())
        print("días con CDD > 0:", (df["cdd"] > 0).sum())
        print()
