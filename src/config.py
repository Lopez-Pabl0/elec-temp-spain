"""Rutas y periodo de estudio compartidos por todos los scripts."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS_RAW = RAIZ / "data" / "raw"
RESULTADOS = RAIZ / "results"
FIGURAS = RESULTADOS / "figuras"

ANIO_INICIO = 2021
ANIO_FIN = 2025
