import unittest
from unittest.mock import patch
from helpers.vaccination_report import SpainVaccinationReport


class SpainVaccinationReportUnitTest(unittest.TestCase):

    @patch("helpers.vaccination_report.requests")
    @patch("helpers.vaccination_report.NamedTemporaryFile")
    @patch("helpers.vaccination_report.get_data")
    def test_given_ods_when_get_vaccination_by_ccaa_then_data_returned(self, get_data_mock,
                                                                       named_temporary_file_mock,
                                                                       requests_mock):

        get_data_mock.return_value = {'Hoja3': [
            ['', 'Dosis entregadas (1)', 'Dosis administradas (2)', '% sobre entregadas', 'Última actualización de datos'],
            ['Andalucía', 140295, 25809],
            ['Aragón', 23715, 2004],
            ['Asturias ', 23720, 9380],
            ['Baleares', 8940, 153],
            ['Canarias', 20835, 4846],
            ['Cantabria', 11850, 304],
            ['Castilla y Leon ', 51390, 10928,],
            ['Castilla La Mancha', 35550, 1983],
            ['Cataluña', 120545, 8150],
            ['C. Valenciana', 61225, 3252],
            ['Extremadura', 21725, 686],
            ['Galicia', 37555, 9124],
            ['La Rioja', 5915, 324],
            ['Madrid', 89040, 2883],
            ['Murcia ', 25685, 442],
            ['Navarra', 6975, 1583],
            ['País Vasco', 31605, 396],
            ['Ceuta', 1005, 380],
            ['Melilla', 1005, 207],
            ['Totales', 718575, 82834],
            []]
        }

        report = SpainVaccinationReport()
        result = report.get_vaccination_by_ccaa()
        self.assertEqual({'Andalucía': 25809,
                          'Aragón': 2004,
                          'Asturias': 9380,
                          'Baleares': 153,
                          'Canarias': 4846,
                          'Cantabria': 304,
                          'Castilla y León': 10928,
                          'Castilla La Mancha': 1983,
                          'Cataluña': 8150,
                          'C. Valenciana': 3252,
                          'Extremadura': 686,
                          'Galicia': 9124,
                          'La Rioja': 324,
                          'Madrid': 2883,
                          'Murcia': 442,
                          'Navarra': 1583,
                          'País Vasco': 396,
                          'Ceuta': 380,
                          'Melilla': 207},
                         result)

        requests_mock.get.assert_called_once_with(report._url)
        named_temporary_file_mock.assert_called_once_with(suffix=".ods")

        with named_temporary_file_mock.return_value as temp_file:
            temp_file.write.assert_called_once_with(requests_mock.get.return_value.content)
            temp_file.flush.assert_called_once_with()