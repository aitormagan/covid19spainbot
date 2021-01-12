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
    "Andalucía": 17112,
    "Aragón": 4206,
    "Asturias": 3492,
    "Baleares": 3353,
    "Canarias": 5349,
    "Cantabria": 1609,
    "Castilla La Mancha": 4817,
    "Castilla y León": 6703,
    "Cataluña": 24629,
    "Ceuta": 200,
    "C. Valenciana": 11644,
    "Extremadura": 3188,
    "Galicia": 8298,
    "Madrid": 15818,
    "Melilla": 179,
    "Murcia": 3952,
    "Navarra": 1881,
    "País Vasco": 4708,
    "La Rioja": 809,
}

CCAA_ICU_BEDS = {
    "Andalucía": 1688,
    "Aragón": 233,
    "Asturias": 322,
    "Baleares": 305,
    "Canarias": 442,
    "Cantabria": 122,
    "Castilla La Mancha": 377,
    "Castilla y León": 513,
    "Cataluña": 1358,
    "Ceuta": 17,
    "C. Valenciana": 1073,
    "Extremadura": 215,
    "Galicia": 729,
    "Madrid": 1132,
    "Melilla": 13,
    "Murcia": 465,
    "Navarra": 125,
    "País Vasco": 412,
    "La Rioja": 59,
}


def get_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa and ccaa in CCAA_POPULATION else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 100000 / divider
    return "{0:.2f}".format(ccaa_impact).replace(".", ",") + "/100.000 hab." if total_cases > 0 else ""
