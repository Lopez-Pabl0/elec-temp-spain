"""Gráficas y utilidades de dibujo compartidas por los notebooks."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import FIGURAS

# Mismo nombre y mismo color para cada sistema en todos los notebooks
NOMBRES_SISTEMA = {"peninsular": "Península", "baleares": "Baleares", "canarias": "Canarias"}
COLORES = {"peninsular": "tab:blue", "baleares": "tab:orange", "canarias": "tab:green"}
NOMBRES_MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def predecir_v(res, t_base, temp, dias=range(5), festivo=0, anios=None):
    """La V que predice el modelo para una rejilla de temperaturas.

    Promedia la predicción de los días de la semana indicados (por defecto un
    laborable medio, de lunes a viernes) y, si se pasan, de los años indicados.
    Los modelos sin C(anio) (como el modelo B) se usan con anios=None.
    """
    rejilla = pd.DataFrame({"hdd": np.maximum(t_base - temp, 0), "cdd": np.maximum(temp - t_base, 0)})
    combinaciones = [{"dia_semana": dia, "festivo": festivo} for dia in dias]
    if anios is not None:
        combinaciones = [{**c, "anio": anio} for c in combinaciones for anio in anios]
    return np.mean([res.predict(rejilla.assign(**c)) for c in combinaciones], axis=0)


def plot_v_sistemas(datos, modelos, t_bases, archivo=None):
    """La V de cada sistema sobre sus datos, en % de la demanda media para poder comparar pendientes."""
    fig, axes = plt.subplots(1, len(datos), figsize=(18, 5.5), sharey=True)
    for ax, (sistema, df) in zip(axes, datos.items()):
        res, t_base = modelos[sistema], t_bases[sistema]
        media = df["demanda_mwh"].mean()
        anios = sorted(df["anio"].unique())
        temp = np.linspace(df["temperatura"].min(), df["temperatura"].max(), 200)

        no_laborable = (df["dia_semana"] >= 5) | (df["festivo"] == 1)
        pct = df["demanda_mwh"] / media * 100
        ax.scatter(df.loc[~no_laborable, "temperatura"], pct[~no_laborable], s=4, alpha=0.3, label="Laborable")
        ax.scatter(df.loc[no_laborable, "temperatura"], pct[no_laborable], s=4, alpha=0.3,
                   label="Fin de semana / festivo")
        ax.plot(temp, predecir_v(res, t_base, temp, anios=anios) / media * 100, color="tab:red", linewidth=2,
                label="Predicción: laborable medio")
        ax.plot(temp, predecir_v(res, t_base, temp, dias=[6], anios=anios) / media * 100, color="darkred",
                linewidth=2, linestyle="--", label="Predicción: domingo")
        ax.axvline(t_base, color="black", linestyle=":", linewidth=1)
        ax.axhline(100, color="gray", linewidth=0.8)
        ax.set_title(f"{NOMBRES_SISTEMA.get(sistema, sistema)} (T_base = {t_base} °C)")
        ax.set_xlabel("Temperatura media ponderada (°C)")
    axes[0].set_ylabel("Demanda (% de la media del sistema)")
    fig.suptitle("La V del modelo sobre los datos de cada sistema")
    plt.tight_layout()
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(0.5, -0.07),
               ncol=4, frameon=False)
    if archivo:
        fig.savefig(FIGURAS / archivo, dpi=120, bbox_inches="tight")
    plt.show()


def plot_serie_real_prediccion(datos, modelos, anio, archivo=None, con_error=False):
    """Demanda real y predicción del modelo día a día durante un año, una fila por sistema.

    Todo en % de la demanda media de cada sistema, para poder comparar sistemas.
    Con con_error=True añade debajo de cada serie el error de cada día.
    Devuelve {sistema: error diario en %} para poder sacar cifras en el notebook.
    """
    filas = len(datos) * (2 if con_error else 1)
    alturas = [3, 1] * len(datos) if con_error else [1] * len(datos)
    fig, axes = plt.subplots(filas, 1, figsize=(14, 3.7 * len(datos) + (1.5 if con_error else 0)), sharex=True,
                             gridspec_kw={"height_ratios": alturas}, squeeze=False)
    axes = axes[:, 0]

    errores = {}
    for k, (sistema, df) in enumerate(datos.items()):
        media = df["demanda_mwh"].mean()
        real = df.loc[str(anio), "demanda_mwh"] / media * 100
        prediccion = modelos[sistema].fittedvalues.loc[str(anio)] / media * 100
        errores[sistema] = real - prediccion

        ax = axes[2 * k] if con_error else axes[k]
        ax.plot(real.index, real, color=COLORES.get(sistema, "tab:blue"), linewidth=1, label="Demanda real")
        ax.plot(prediccion.index, prediccion, color="black", linewidth=0.8, alpha=0.7,
                label="Predicción del modelo")
        ax.axhline(100, color="gray", linewidth=0.8)
        ax.set_title(f"{NOMBRES_SISTEMA.get(sistema, sistema)}   "
                     f"error absoluto medio = {errores[sistema].abs().mean():.1f} %")
        ax.set_ylabel("% de la demanda media")
        ax.legend(loc="upper left")

        if con_error:
            ax_error = axes[2 * k + 1]
            ax_error.bar(errores[sistema].index, errores[sistema], width=1, color="gray")
            ax_error.axhline(0, color="black", linewidth=1)
            ax_error.set_ylabel("Error (%)")

    if not con_error:
        ymin = min(ax.get_ylim()[0] for ax in axes)
        ymax = max(ax.get_ylim()[1] for ax in axes)
        for ax in axes:
            ax.set_ylim(ymin, ymax)   # misma escala en todos los sistemas
    fig.suptitle(f"Demanda real y predicción del modelo, {anio}")
    plt.tight_layout()
    if archivo:
        fig.savefig(FIGURAS / archivo, dpi=120, bbox_inches="tight")
    plt.show()
    return errores
