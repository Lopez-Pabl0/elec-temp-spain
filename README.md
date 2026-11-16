# Demanda eléctrica y temperatura en España
## Pregunta
¿Cuánto sube la demanda eléctrica por cada grado de frío o de calor, y en qué se diferencian Península, Baleares y Canarias?
## Datos
Demanda diaria de REData (2021-2025) y temperatura diaria de Open-Meteo, ambas sin registro.
## Modelo
Demanda ~ HDD + CDD + día de la semana + festivo + tendencia, uno por sistema.