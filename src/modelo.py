"""Modelo final de sensibilidad de la demanda a la temperatura, para los tres sistemas.

Es la versión "todo de una vez" de lo que se construye y se explora en los notebooks:
el modelo se construye paso a paso en 02_modelo.ipynb y se compara entre sistemas en
03_comparacion_sistemas.ipynb. Recomiendo leer primero los notebooks.

Modelo (modelo C de 02_modelo.ipynb), uno por sistema:

    demanda_mwh ~ hdd + cdd + C(dia_semana) + festivo + C(anio)     (Canarias sin hdd)

con errores estándar HAC (Newey-West) y maxlags elegido con la ACF de los residuos.

Al ejecutarlo (python src/modelo.py):
  - imprime, para cada sistema, el resumen del ajuste y el diagnóstico de autocorrelación;
  - guarda results/efectos_temperatura.csv, una fila por sistema, con las mismas cifras
    que la sección 5 (Resultados) de 03_comparacion_sistemas.ipynb:
      hdd_%, cdd_%                 efecto por grado-día, en % de la demanda media
      hdd_ic_inf/sup, cdd_ic_...   intervalo de confianza al 95 % (HAC)
      hdd_medio_dia, cdd_medio_dia grados-día medios de un día del periodo
      peso_frio_%, peso_calor_%,   parte de la demanda media que se debe al frío,
      peso_temperatura_%           al calor y a la temperatura en total
      r2, durbin_watson, maxlags   calidad del ajuste y diagnóstico de autocorrelación
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf

from config import RESULTADOS
from features import CONFIG, cargar_sistema, crear_features

# maxlags de HAC = primer retardo en el que la ACF de los residuos baja de UMBRAL_ACF.
# En la Península sale 14 (dos semanas); en las islas la autocorrelación dura mucho más.
UMBRAL_ACF = 0.1
MAX_RETARDOS = 365


def formula_sistema(sistema):
    """Devuelve el string de la fórmula para cada sistema.

    Canarias va sin 'hdd': solo tiene ~42 días por debajo de T_base.
    """
    controles = "cdd + C(dia_semana) + festivo + C(anio)"
    if sistema != "canarias":
        controles = "hdd + " + controles
    return "demanda_mwh ~ " + controles


def elegir_maxlags(residuos, umbral=UMBRAL_ACF):
    """Primer retardo en el que la autocorrelación de los residuos cae por debajo del umbral."""
    autocorrelacion = acf(residuos, nlags=MAX_RETARDOS)
    por_debajo = np.flatnonzero(autocorrelacion[1:] < umbral)
    return int(por_debajo[0] + 1) if len(por_debajo) else MAX_RETARDOS


def ajustar_modelo(df, formula, hac=True):
    """Ajusta OLS y devuelve el objeto de resultados.

    - hac=True  -> errores estándar Newey-West; maxlags se elige con la ACF de
                   los residuos (queda guardado en res.cov_kwds["maxlags"])
    - hac=False -> errores estándar clásicos (para comparar)
    """
    modelo = smf.ols(formula, data=df)
    res_ols = modelo.fit()
    if not hac:
        return res_ols
    maxlags = elegir_maxlags(res_ols.resid)
    return modelo.fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})


def cargar_datos():
    """Datos de los tres sistemas, con todas las variables del modelo: {sistema: DataFrame}."""
    return {sistema: crear_features(cargar_sistema(sistema), **cfg) for sistema, cfg in CONFIG.items()}


def ajustar_sistemas(datos):
    """Modelo final (con errores HAC) de cada sistema: {sistema: resultados}."""
    return {sistema: ajustar_modelo(df, formula_sistema(sistema)) for sistema, df in datos.items()}


def efectos_en_porcentaje(res, demanda_media):
    """Devuelve un dict con el efecto en % y su IC 95 % para hdd y cdd.

    Si la variable no está en el modelo, sus tres valores son NaN.
    """
    ic = res.conf_int()
    efectos = {}
    for var in ("hdd", "cdd"):
        if var in res.params.index:
            coef = res.params[var]
            inf, sup = ic.loc[var]
        else:
            coef = inf = sup = float("nan")
        efectos[f"{var}_%"] = coef / demanda_media * 100
        efectos[f"{var}_ic_inf"] = inf / demanda_media * 100
        efectos[f"{var}_ic_sup"] = sup / demanda_media * 100
    return efectos


def peso_temperatura(res, df):
    """Parte de la demanda media que se debe a la temperatura, en %.

    Es el HDD (o CDD) medio de un día del periodo multiplicado por su efecto por grado-día.
    """
    media = df["demanda_mwh"].mean()
    peso = {
        "hdd_medio_dia": df["hdd"].mean(),
        "cdd_medio_dia": df["cdd"].mean(),
        "peso_frio_%": df["hdd"].mean() * res.params.get("hdd", 0) / media * 100,
        "peso_calor_%": df["cdd"].mean() * res.params["cdd"] / media * 100,
    }
    peso["peso_temperatura_%"] = peso["peso_frio_%"] + peso["peso_calor_%"]
    return peso


def tabla_resultados(datos, modelos):
    """Tabla de resultados, una fila por sistema: la que guarda este script y la que muestra el 03."""
    filas = {}
    for sistema, res in modelos.items():
        df = datos[sistema]
        filas[sistema] = {
            **efectos_en_porcentaje(res, df["demanda_mwh"].mean()),
            **peso_temperatura(res, df),
            "r2": res.rsquared,
            "durbin_watson": durbin_watson(res.resid),
            "maxlags": res.cov_kwds["maxlags"],
        }
    tabla = pd.DataFrame(filas).T
    tabla["maxlags"] = tabla["maxlags"].astype(int)
    tabla.index.name = "sistema"
    return tabla


def comparar_errores(res_ols, res_hac, variables=("hdd", "cdd")):
    """Tabla con el SE clásico, el SE HAC y su cociente para cada variable.

    Las variables que no están en el modelo (hdd en canarias) se saltan.
    """
    variables = [v for v in variables if v in res_hac.params.index]
    tabla = pd.DataFrame({
        "se_ols": res_ols.bse[variables],
        "se_hac": res_hac.bse[variables],
    })
    tabla["ratio"] = tabla["se_hac"] / tabla["se_ols"]
    return tabla


def residuos_por_mes(res):
    """Media de los residuos agrupada por mes (1..12), en MWh.

    Un mes con residuo medio claramente distinto de 0 indica algo que el
    modelo no recoge (p. ej. agosto en la península).
    """
    residuos = res.resid
    return residuos.groupby(residuos.index.month).mean().rename("residuo_medio")


if __name__ == "__main__":
    datos = cargar_datos()
    modelos = ajustar_sistemas(datos)

    for sistema, res_hac in modelos.items():
        df = datos[sistema]
        res_ols = ajustar_modelo(df, formula_sistema(sistema), hac=False)   # mismos β, SE clásicos

        print(f"=== {sistema} ===")
        print(res_hac.summary())
        print(f"\nDurbin-Watson: {durbin_watson(res_hac.resid):.2f}   maxlags HAC: {res_hac.cov_kwds['maxlags']}")
        print("\nErrores estándar clásico vs HAC:")
        print(comparar_errores(res_ols, res_hac).round(2))
        print("\nResiduo medio por mes (% de la demanda media):")
        print((residuos_por_mes(res_hac) / df["demanda_mwh"].mean() * 100).round(2))
        print()

    tabla = tabla_resultados(datos, modelos).round(3)
    print("=== Resumen ===")
    print(tabla.to_string())

    RESULTADOS.mkdir(exist_ok=True)
    tabla.to_csv(RESULTADOS / "efectos_temperatura.csv")
    print(f"\nTabla guardada en {RESULTADOS / 'efectos_temperatura.csv'}")
