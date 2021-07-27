CCAA_POPULATION = {
    "Andalucía": 8464423,
    "Aragón": 1329389,
    "Asturias": 1018786,
    "Baleares": 1171543,
    "Canarias": 2175970,
    "Cantabria": 582907,
    "Castilla La Mancha": 2045203,
    "Castilla y León": 2394912,
    "Cataluña": 7780445,
    "Ceuta": 84201,
    "C. Valenciana": 5057380,
    "Extremadura": 1063978,
    "Galicia": 2701807,
    "Madrid": 6779868,
    "Melilla": 87076,
    "Murcia": 1511239,
    "Navarra": 661194,
    "País Vasco": 2220500,
    "La Rioja": 319913
}

CCAA_ADMITTED_BEDS = {
    "Andalucía": 17852,
    "Aragón": 3993,
    "Asturias": 3345,
    "Baleares": 3255,
    "Canarias": 5517,
    "Cantabria": 1361,
    "Castilla La Mancha": 4800,
    "Castilla y León": 6363,
    "Cataluña": 24361,
    "Ceuta": 200,
    "C. Valenciana": 11129,
    "Extremadura": 2881,
    "Galicia": 8163,
    "Madrid": 15258,
    "Melilla": 182,
    "Murcia": 4032,
    "Navarra": 1765,
    "País Vasco": 4467,
    "La Rioja": 703
}

CCAA_ICU_BEDS = {
    "Andalucía": 1861,
    "Aragón": 217,
    "Asturias": 297,
    "Baleares": 277,
    "Canarias": 481,
    "Cantabria": 118,
    "Castilla La Mancha": 360,
    "Castilla y León": 431,
    "Cataluña": 1317,
    "Ceuta": 17,
    "C. Valenciana": 833,
    "Extremadura": 187,
    "Galicia": 744,
    "Madrid": 1060,
    "Melilla": 16,
    "Murcia": 462,
    "Navarra": 116,
    "País Vasco": 387,
    "La Rioja": 53
}


def get_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa and ccaa in CCAA_POPULATION else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 100000 / divider
    return "{0:.2f}".format(ccaa_impact).replace(".", ",") + "/100.000 hab." if total_cases > 0 else ""
