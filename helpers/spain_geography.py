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


def get_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa and ccaa in CCAA_POPULATION else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 100000 / divider
    return "{0:.2f}".format(ccaa_impact).replace(".", ",") + "/100.000 hab." if total_cases > 0 else ""
