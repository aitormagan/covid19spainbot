CCAA_POPULATION = {
    "Andalucía": 8414240,
    "Aragón": 1319291,
    "Asturias": 1022800,
    "Baleares": 1149460,
    "Canarias": 2153389,
    "Cantabria": 581078,
    "Castilla La Mancha": 2032863,
    "Castilla y León": 2399548,
    "Cataluña": 7675217,
    "Ceuta": 84777,
    "C. Valenciana": 5003769,
    "Extremadura": 1067710,
    "Galicia": 2699499,
    "Madrid": 6663394,
    "Melilla": 86487,
    "Murcia": 1493898,
    "Navarra": 654214,
    "País Vasco": 2207776,
    "La Rioja": 316798
}


def get_accumulated_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa and ccaa in CCAA_POPULATION else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 100000 / divider
    return "{0:.2f}".format(ccaa_impact).replace(".", ",") + "/100.000 hab." if total_cases > 0 else ""
