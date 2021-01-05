from tempfile import NamedTemporaryFile
import requests
from pyexcel_ods import get_data


class SpainVaccinationReport:

    def __init__(self):
        self.__url = "https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/Informe_Comunicacion.ods"

    def get_vaccination_by_ccaa(self):
        res = requests.get(self.__url)
        result = {}

        with NamedTemporaryFile(suffix=".ods") as temp_file:
            temp_file.write(res.content)
            temp_file.flush()
            vaccinations = get_data(temp_file)
            page = list(vaccinations.keys())[0]

            for item in vaccinations[page][1:20]:
                result[item[0].strip().replace("Leon", "León")] = item[2]

        return result
