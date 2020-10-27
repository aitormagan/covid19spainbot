CCAA_POPULATION = {
    "Andalucía": 8414192,
    "Aragón": 1319281,
    "Asturias": 1022840,
    "Baleares": 1149490,
    "Canarias": 2153472,
    "Cantabria": 581081,
    "Castilla La Mancha": 2032851,
    "Castilla y León": 2399575,
    "Cataluña": 7675124,
    "Ceuta": 84778,
    "C. Valenciana": 5003797,
    "Extremadura": 1067705,
    "Galicia": 2699404,
    "Madrid": 6663356,
    "Melilla": 86486,
    "Murcia": 1493912,
    "Navarra": 654216,
    "País Vasco": 2207797,
    "La Rioja": 316795
}

CCAA_ADMITTED_BEDS = {
    'Andalucía': 15479,
    'Aragón': 4146,
    'Asturias': 3251,
    'Baleares': 3033,
    'Canarias': 4900,
    'Cantabria': 1554,
    'Castilla La Mancha': 4783,
    'Castilla y León': 6701,
    'Cataluña': 25221,
    'Ceuta': 185,
    'C. Valenciana': 11413,
    'Extremadura': 3143,
    'Galicia': 8255,
    'Madrid': 16006,
    'Melilla': 178,
    'Murcia': 3703,
    'Navarra': 2147,
    'País Vasco': 4928,
    'La Rioja': 859,
}

CCAA_ICU_BEDS = {
    'Andalucía': 1437,
    'Aragón': 208,
    'Asturias': 260,
    'Baleares': 283,
    'Canarias': 417,
    'Cantabria': 115,
    'Castilla La Mancha': 387,
    'Castilla y León': 464,
    'Cataluña': 1274,
    'Ceuta': 16,
    'C. Valenciana': 1033,
    'Extremadura': 222,
    'Galicia': 715,
    'Madrid': 1265,
    'Melilla': 13,
    'Murcia': 525,
    'Navarra': 133,
    'País Vasco': 314,
    'La Rioja': 59,
}


def get_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa and ccaa in CCAA_POPULATION else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 100000 / divider
    return "{0:.2f}".format(ccaa_impact).replace(".", ",") + "/100.000 hab." if total_cases > 0 else ""
