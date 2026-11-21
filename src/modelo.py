from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson

from features import CONFIG, cargar_sistema, crear_features

RESULTADOS = Path(__file__).resolve().parent.parent / "results"
MAXLAGS = 14

# variante -> ¿lleva dummies de mes?
VARIANTES = {"base": False, "mes": True}


def formula_sistema(sistema, con_mes=False):
    """Devuelve el string de la fórmula para cada sistema.

    Canarias va sin 'hdd': solo tiene ~42 días por debajo de T_base.
    con_mes=True añade dummies de mes (referencia: enero) para recoger
    la estacionalidad que no es temperatura: turismo, vacaciones, luz.
    """
    controles = "cdd + C(dia_semana) + festivo + C(anio)"
    if sistema != "canarias":
        controles = "hdd + " + controles
    if con_mes:
        controles += " + C(mes)"
    return "demanda_mwh ~ " + controles


def ajustar_modelo(df, formula, hac=True):
    """Ajusta OLS y devuelve el objeto de resultados.

    - hac=True  -> errores estándar Newey-West con MAXLAGS retardos
    - hac=False -> errores estándar clásicos (para comparar)
    """
    modelo = smf.ols(formula, data=df)
    if hac:
        return modelo.fit(cov_type="HAC", cov_kwds={"maxlags": MAXLAGS})
    return modelo.fit()


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


def residuos_por_mes(res):
    """Media de los residuos agrupada por mes (1..12), en MWh.

    Un mes con residuo medio claramente distinto de 0 indica algo que el
    modelo no recoge (p. ej. agosto en la península).
    """
    residuos = res.resid
    return residuos.groupby(residuos.index.month).mean().rename("residuo_medio")


if __name__ == "__main__":
    filas = []

    for sistema, cfg in CONFIG.items():
        # 1. datos
        df = cargar_sistema(sistema)
        df = crear_features(df, **cfg)
        df["mes"] = df.index.month
        demanda_media = df["demanda_mwh"].mean()

        for variante, con_mes in VARIANTES.items():
            # 2. fórmula del sistema
            formula = formula_sistema(sistema, con_mes)

            # 3. ajustar con HAC y sin HAC (mismos coeficientes, distintos SE)
            res_hac = ajustar_modelo(df, formula)
            res_ols = ajustar_modelo(df, formula, hac=False)

            # 4. summary, Durbin-Watson y comparación de SE
            dw = durbin_watson(res_hac.resid)
            print(f"=== {sistema} ({variante}) ===")
            print(res_hac.summary())
            print(f"\nDurbin-Watson: {dw:.2f}")
            print("\nErrores estándar clásico vs HAC:")
            print(comparar_errores(res_ols, res_hac).round(2))

            # 5-6. efectos en % de la demanda media -> una fila por sistema y variante
            fila = {"sistema": sistema, "variante": variante}
            fila.update(efectos_en_porcentaje(res_hac, demanda_media))
            fila["r2"] = res_hac.rsquared
            fila["durbin_watson"] = dw
            filas.append(fila)

            # 7. residuos por mes (solo en la base: con C(mes) salen 0 por construcción)
            if not con_mes:
                print("\nResiduo medio por mes (% de la demanda media):")
                print((residuos_por_mes(res_hac) / demanda_media * 100).round(2))
            print()

    # 8. tabla final
    tabla = pd.DataFrame(filas).set_index(["sistema", "variante"]).round(3)
    print("=== Resumen ===")
    print(tabla.to_string())

    # 9. guardar en results/
    RESULTADOS.mkdir(exist_ok=True)
    tabla.to_csv(RESULTADOS / "efectos_temperatura.csv")
    print(f"\nTabla guardada en {RESULTADOS / 'efectos_temperatura.csv'}")