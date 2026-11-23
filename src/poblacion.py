"""Población de cada provincia (o isla), para ponderar la temperatura de cada sistema.

Población a 1 de enero de 2023. Fuente: INE, Cifras oficiales de población
(Revisión del Padrón Municipal), tablas "<Provincia>: Población por municipios y sexo".
Baleares por isla = suma de sus municipios; Formentera va con Ibiza.

Las claves tienen que ser las mismas que las de CIUDADES en descarga_temperatura.py,
porque features.py empareja cada temperatura con su población por nombre.
"""

POBLACION = {
    "peninsular": {
        # Andalucía
        "almeria":     753_920,
        "cadiz":       1_250_539,
        "cordoba":     773_997,
        "granada":     930_181,
        "huelva":      530_824,
        "jaen":        620_242,
        "malaga":      1_751_600,
        "sevilla":     1_957_210,
        # Aragón
        "huesca":      227_077,
        "teruel":      135_237,
        "zaragoza":    977_413,
        # Asturias
        "asturias":    1_005_283,
        # Cantabria
        "cantabria":   588_419,
        # Castilla-La Mancha
        "albacete":    387_174,
        "ciudad_real": 491_127,
        "cuenca":      197_139,
        "guadalajara": 274_598,
        "toledo":      728_496,
        # Castilla y León
        "avila":       158_407,
        "burgos":      357_180,
        "leon":        447_463,
        "palencia":    157_752,
        "salamanca":   327_170,
        "segovia":     155_258,
        "soria":       89_482,
        "valladolid":  521_071,
        "zamora":      166_366,
        # Cataluña
        "barcelona":   5_805_500,
        "girona":      809_266,
        "lleida":      446_793,
        "tarragona":   847_566,
        # Comunidad Valenciana
        "alicante":    1_950_357,
        "castellon":   603_952,
        "valencia":    2_656_291,
        # Extremadura
        "badajoz":     665_089,
        "caceres":     387_434,
        # Galicia
        "a_coruna":    1_123_426,
        "lugo":        323_956,
        "ourense":     304_550,
        "pontevedra":  944_245,
        # Madrid
        "madrid":      6_859_914,
        # Murcia
        "murcia":      1_552_457,
        # Navarra
        "navarra":     671_746,
        # País Vasco
        "araba":       336_686,
        "bizkaia":     1_154_306,
        "gipuzkoa":    728_027,
        # La Rioja
        "la_rioja":    322_490,
    },
    "baleares": {
        "palma": 929_950,   # Mallorca
        "ibiza": 168_976,   # Ibiza 157 805 + Formentera 11 171
        "mahon": 98_335,    # Menorca
    },
    "canarias": {
        "las_palmas":          1_140_258,
        "santa_cruz_tenerife": 1_061_790,
    },
}
