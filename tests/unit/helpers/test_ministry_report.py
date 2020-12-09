import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from pandas import DataFrame
from helpers.ministry_report import SpainCovid19MinistryReport
from helpers.spain_geography import CCAA_POPULATION


class SpainCovid19MinistryReportUnitTest(unittest.TestCase):

    def test_given_14_5_when_get_id_then_105_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 5, 14)), 105)

    def test_given_10_5_when_get_id_then_101_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 5, 10)), 101)

    def test_given_3_7_when_get_id_then_155_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 7, 3)), 155)

    def test_given_6_7_when_get_id_then_156_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 7, 6)), 156)

    def test_given_13_7_when_get_id_then_161_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 7, 13)), 161)

    @patch("helpers.ministry_report.DAYS_WITHOUT_REPORT", [date(2020, 12, 8)])
    def test_given_9_12_and_8_12_without_report_when_get_id_then_267_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 12, 9)), 267)

    @patch("helpers.ministry_report.DAYS_WITHOUT_REPORT", [date(2020, 12, 7), date(2020, 12, 8)])
    def test_given_9_12_and_7_12_and_8_12_without_report_when_get_id_then_266_returned(self):
        self.assertEqual(SpainCovid19MinistryReport.get_pdf_id_for_date(datetime(2020, 12, 9)), 266)

    @patch("helpers.ministry_report.tabula")
    @patch("helpers.ministry_report.SpainCovid19MinistryReport.get_pdf_id_for_date")
    def test_given_no_data_frame_acceded_when_access_then_tabula_used(self, get_pdf_for_id_mock, tabula_mock):
        date = datetime(2020, 5, 5)
        page = "1"
        area = MagicMock()
        report = SpainCovid19MinistryReport(date, page, area)
        valid_data = {"Col1*": ["value1", "value2*", "value3", "value4*"] + list(CCAA_POPULATION.keys())}
        d1 = DataFrame(data={"Col1": [1, 2, 3]})
        d2 = DataFrame(data=valid_data)
        tabula_mock.read_pdf.return_value = [d1, d2]

        returned_data_frame = report.data_frame

        tabula_mock.read_pdf.assert_called_once_with(SpainCovid19MinistryReport.PDF_URL_FORMAT.format(
            get_pdf_for_id_mock.return_value), pages=str(page), area=area)
        get_pdf_for_id_mock.assert_called_once_with(date)

        self.assertEqual(valid_data["Col1*"], list(returned_data_frame['Col1']))

    def test_given_dataframe_when_get_column_data_then_map_returned(self):

        with patch.object(SpainCovid19MinistryReport, 'data_frame'):
            report = SpainCovid19MinistryReport(None, None)
            headers = ["heade1", "header2", "header3"]
            ccaas = list(map(lambda x: x + "*", CCAA_POPULATION.keys()))
            data1 = list(map(lambda x: str(x), range(1, 20)))
            data2 = list(map(lambda x: str(x) + ".000", range(21, 40)))
            report.data_frame = DataFrame(data={"Unnamed: 0": headers + ccaas, "Column1": headers + data1,
                                                "Column2": headers + data2})

            result = report.get_column_data(2)

            self.assertEqual(list(CCAA_POPULATION.keys()), list(result.keys()))
            self.assertEqual(list(range(21000, 40000, 1000)), list(result.values()))
