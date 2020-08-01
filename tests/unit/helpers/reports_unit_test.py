import unittest
from unittest.mock import patch, call
from helpers.reports import get_tendency_emoji, get_human_summary, get_report_by_ccaa


class ReportsUnitTest(unittest.TestCase):

    @patch("helpers.reports.get_tendency_emoji", return_value="^ 1")
    @patch("helpers.reports.get_impact_string", return_value="(0.21/millón)")
    def test_given_data_when_get_report_by_ccaa_then_report_returned(self, get_impact_mock, get_tendency_emoji_mock):
        today_data = {"Madrid": 7, "Cataluña": 3}
        yesterday_data = {"Madrid": 2, "Cataluña": 9}

        result = get_report_by_ccaa(today_data, yesterday_data)

        self.assertEqual(["Madrid: +7 {0} {1}".format(get_impact_mock.return_value,
                                                      get_tendency_emoji_mock.return_value),
                          "Cataluña: +3 {0} {1}".format(get_impact_mock.return_value,
                                                        get_tendency_emoji_mock.return_value)], result)

        get_impact_mock.assert_has_calls([call(7, "Madrid"), call(3, "Cataluña")])
        get_tendency_emoji_mock.assert_has_calls([call(7, 2), call(3, 9)])

    @patch("helpers.reports.get_tendency_emoji", return_value="^ 1")
    @patch("helpers.reports.get_impact_string", return_value="(0.21/millón)")
    def test_given_data_when_get_human_summary_then_report_returned(self, get_impact_mock, get_tendency_emoji_mock):
        today_data = {"Madrid": 7, "Cataluña": 3}
        yesterday_data = {"Madrid": 2, "Cataluña": 9}
        today_accumulated = {"Madrid": 9000, "Cataluña": 11123}

        result = get_human_summary("PCR+", today_data, yesterday_data, today_accumulated)

        self.assertEqual("PCR+: +10 {0} {1} (Totales: 20.123)".format(get_impact_mock.return_value,
                                                                      get_tendency_emoji_mock.return_value), result)

        get_impact_mock.assert_called_once_with(10)
        get_tendency_emoji_mock.assert_called_once_with(10, 11)

    def test_given_today_higher_than_yesterday_when_get_tendency_icon_then_upwards_triangle_returned(self):
        emoji = get_tendency_emoji(20, 15)

        self.assertEqual("🔺5", emoji)

    def test_given_today_lower_than_yesterday_when_get_tendency_icon_then_downwards_triangle_returned(self):
        emoji = get_tendency_emoji(15, 20)

        self.assertEqual("🔻5", emoji)

    def test_given_today_equals_than_yesterday_when_get_tendency_icon_then_back_arrow_returned(self):
        emoji = get_tendency_emoji(20, 20)

        self.assertEqual("🔙", emoji)
