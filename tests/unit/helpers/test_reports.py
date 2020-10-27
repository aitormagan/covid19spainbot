from datetime import datetime
import unittest
from unittest.mock import patch, call, MagicMock
from helpers.reports import get_tendency_emoji, get_report_sentence, get_report_by_ccaa, get_graph_url, \
    get_global_report, get_global_data, get_territorial_unit_report, get_report_sentence_with_unit, \
    calculate_global_incidence
from helpers.db import Measurement
from helpers.spain_geography import CCAA_POPULATION
from constants import GRAPH_IMAGE_PATH

DEFAULT_GRAPH_IMAGE_URL = "http://localhost:3000/" + GRAPH_IMAGE_PATH


class ReportsUnitTest(unittest.TestCase):

    @patch("helpers.reports.get_territorial_unit_report")
    def test_given_data_when_get_report_by_ccaa_then_report_returned(self, get_territorial_unit_report_mock):
        ccaa1 = "Melilla"
        ccaa2 = "Andalucia"
        data_header = "data_header"
        today_data = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }
        yesterday_data = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }
        accumulated_data = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }

        result = get_report_by_ccaa(data_header, today_data, yesterday_data, accumulated_data)

        self.assertEqual([get_territorial_unit_report_mock.return_value,
                          get_territorial_unit_report_mock.return_value], result)

        # Note: info is published in alphabetical order
        get_territorial_unit_report_mock.assert_has_calls([
            call(ccaa2, data_header, today_data[ccaa2], yesterday_data[ccaa2], accumulated_data[ccaa2]),
            call(ccaa1, data_header, today_data[ccaa1], yesterday_data[ccaa1], accumulated_data[ccaa1])
        ])

    @patch("helpers.reports.get_territorial_unit_report")
    @patch("helpers.reports.get_global_data")
    def test_given_data_when_get_global_report_then_report_returned(self, get_global_data_mock,
                                                                    get_territorial_unit_report_mock):
        ccaa1 = "Melilla"
        ccaa2 = "Andalucia"
        data_header = "data_header"
        today_data = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }
        yesterday_data = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }
        accumulated_today = {
            ccaa1: MagicMock(),
            ccaa2: MagicMock()
        }

        global_today_data = MagicMock()
        global_yesterday_data = MagicMock()
        global_accumulated_data = MagicMock()
        get_global_data_mock.side_effect = [global_today_data, global_yesterday_data, global_accumulated_data]

        result = get_global_report(data_header, today_data, yesterday_data, accumulated_today)

        self.assertEqual(get_territorial_unit_report_mock.return_value, result)

        get_territorial_unit_report_mock.assert_called_once_with("🇪🇸 España", data_header, global_today_data,
                                                                 global_yesterday_data, global_accumulated_data)
        get_global_data_mock.assert_has_calls([call(today_data),
                                               call(yesterday_data),
                                               call(accumulated_today)])

    def test_given_no_data_when_global_data_then_empty_dict_returned(self):
        self.assertEqual({}, get_global_data({}))

    @patch("helpers.reports.calculate_global_incidence")
    def test_given_data_for_one_ccaa_when_global_data_then_ccaa_data_returned(self, calculate_global_incidence_mock):
        ccaa = "Melilla"
        pcrs = 100
        deaths = 4
        data = {
            ccaa: {
                Measurement.PCRS: pcrs,
                Measurement.DEATHS: deaths
            }
        }

        self.assertEqual({
            Measurement.PCRS: pcrs,
            Measurement.DEATHS: deaths
        }, get_global_data(data))

        calculate_global_incidence_mock.assert_not_called()

    @patch("helpers.reports.calculate_global_incidence")
    def test_given_data_for_two_ccaa_when_global_data_then_sum_values_returned(self, calculate_global_incidence_mock):
        ccaa1 = "Melilla"
        pcrs1 = 100
        deaths1 = 4
        ccaa2 = "Andalucia"
        pcrs2 = 400
        deaths2 = 7
        data = {
            ccaa1: {
                Measurement.PCRS: pcrs1,
                Measurement.DEATHS: deaths1
            },
            ccaa2: {
                Measurement.PCRS: pcrs2,
                Measurement.DEATHS: deaths2
            }
        }

        self.assertEqual({
            Measurement.PCRS: pcrs1 + pcrs2,
            Measurement.DEATHS: deaths1 + deaths2
        }, get_global_data(data))

        calculate_global_incidence_mock.assert_not_called()

    @patch("helpers.reports.calculate_global_incidence")
    def test_given_accumulated_incidence_when_global_data_then_calculate_global_incidence_returned(self,
                                                                                                   calculate_global_incidence_mock):
        ccaa1 = "Melilla"
        pcrs1 = 100
        deaths1 = 4
        ccaa2 = "Andalucia"
        pcrs2 = 400
        deaths2 = 7
        ia1 = 1.1
        ia2 = 2.2
        percentage_icu1 = 3.3
        percentage_icu2 = 4.4
        percentage_admitted1 = 5.5
        percentage_admitted2 = 6.6
        data = {
            ccaa1: {
                Measurement.PCRS: pcrs1,
                Measurement.DEATHS: deaths1,
                Measurement.ACCUMULATED_INCIDENCE: ia1,
                Measurement.PERCENTAGE_ICU: percentage_icu1,
                Measurement.PERCENTAGE_ADMITTED: percentage_admitted1
            },
            ccaa2: {
                Measurement.PCRS: pcrs2,
                Measurement.DEATHS: deaths2,
                Measurement.ACCUMULATED_INCIDENCE: ia2,
                Measurement.PERCENTAGE_ICU: percentage_icu2,
                Measurement.PERCENTAGE_ADMITTED: percentage_admitted2
            }
        }

        self.assertEqual({
            Measurement.PCRS: pcrs1 + pcrs2,
            Measurement.DEATHS: deaths1 + deaths2,
            Measurement.ACCUMULATED_INCIDENCE: calculate_global_incidence_mock.return_value,
            Measurement.PERCENTAGE_ADMITTED: calculate_global_incidence_mock.return_value,
            Measurement.PERCENTAGE_ICU: calculate_global_incidence_mock.return_value
        }, get_global_data(data))

        calculate_global_incidence_mock.assert_has_calls([call(data, Measurement.ACCUMULATED_INCIDENCE),
                                                          call(data, Measurement.PERCENTAGE_ADMITTED),
                                                          call(data, Measurement.PERCENTAGE_ICU)])

    def test_given_no_data_when_calculate_global_incidence_then_zero_returned(self):
        self.assertEqual(0, calculate_global_incidence({}, Measurement.ACCUMULATED_INCIDENCE))

    def test_given_only_one_ccaa_when_calculate_global_incidence_then_same_value_returned(self):
        ia = 7

        result = calculate_global_incidence({
            "Castilla y León": {
                Measurement.ACCUMULATED_INCIDENCE: ia
            }
        }, Measurement.ACCUMULATED_INCIDENCE)

        # Round because the operation is returning 6.999999
        self.assertEqual(ia, round(result, 0))

    def test_given_two_ccaas_when_calculate_global_incidence_then_same_value_returned(self):
        ia1 = 7
        ia2 = 6
        ccaa1 = "Castilla y León"
        ccaa2 = "Castilla La Mancha"

        result = calculate_global_incidence({
            ccaa1: {
                Measurement.ACCUMULATED_INCIDENCE: ia1
            },
            ccaa2: {
                Measurement.ACCUMULATED_INCIDENCE: ia2
            }
        }, Measurement.ACCUMULATED_INCIDENCE)


        population_ccaa1 = CCAA_POPULATION[ccaa1]
        population_ccaa2 = CCAA_POPULATION[ccaa2]
        total_cases = ia1 * population_ccaa1 / 100000 + ia2 * population_ccaa2 / 100000
        total_population = population_ccaa1 + population_ccaa2
        expected_result = total_cases / total_population * 100000

        self.assertEqual(expected_result, result)

    @patch("helpers.reports.get_report_sentence")
    @patch("helpers.reports.get_report_sentence_with_unit")
    def test_given_pcrs_24_data_when_get_territorial_unit_report_then_tweet_with_pcrs24h_returned(self,
                                                                                                  get_report_sentence_with_unit_mock,
                                                                                                  get_report_sentence_mock):

        territorial_unit = MagicMock()
        date_header = MagicMock()
        today_data = {
            Measurement.PCRS: MagicMock(),
            Measurement.PCRS_LAST_24H: MagicMock(),
            Measurement.DEATHS: MagicMock(),
            Measurement.PERCENTAGE_ADMITTED: MagicMock(),
            Measurement.PERCENTAGE_ICU: MagicMock()
        }
        yesterday_data = MagicMock()
        accumulated_today = MagicMock()
        pcrs = "pcrs"
        pcrs24h = "pcrs24h"
        deaths = "deaths"
        admitted = "admitted"
        uci = "uci"
        get_report_sentence_mock.side_effect = [pcrs, pcrs24h, deaths]
        accumulated_string = "0,21"
        get_report_sentence_with_unit_mock.side_effect = [accumulated_string, admitted, uci]

        expected_tweet = f"{territorial_unit} - {date_header}:\n\n{pcrs}\n{pcrs24h}\n{accumulated_string}" \
                         f"\n\n{deaths}\n\n{admitted}\n{uci}"

        self.assertEqual(expected_tweet, get_territorial_unit_report(territorial_unit, date_header, today_data,
                                                                     yesterday_data, accumulated_today))

        get_report_sentence_with_unit_mock.assert_has_calls([call("💥 IA 14 días",
                                                                   today_data.get(Measurement.ACCUMULATED_INCIDENCE),
                                                                   yesterday_data.get(Measurement.ACCUMULATED_INCIDENCE),
                                                                   "/100.000 hab."),
                                                             call("🚑 Hospitalizados",
                                                                  today_data.get(Measurement.PERCENTAGE_ADMITTED),
                                                                  yesterday_data.get(Measurement.PERCENTAGE_ADMITTED), "%"),
                                                             call("🏥 UCI", today_data.get(Measurement.PERCENTAGE_ICU),
                                                                  yesterday_data.get(Measurement.PERCENTAGE_ICU), "%")])

        get_report_sentence_mock.assert_has_calls([
            call("💉 PCRs", today_data.get(Measurement.PCRS),
                 yesterday_data.get(Measurement.PCRS),
                 accumulated_today.get(Measurement.PCRS)),
            call("💉 PCRs 24h", today_data.get(Measurement.PCRS_LAST_24H),
                 yesterday_data.get(Measurement.PCRS_LAST_24H)),
            call("😢 Muertes", today_data.get(Measurement.DEATHS),
                 yesterday_data.get(Measurement.DEATHS),
                 accumulated_today.get(Measurement.DEATHS))
        ])

    @patch("helpers.reports.get_report_sentence")
    @patch("helpers.reports.get_report_sentence_with_unit")
    def test_given_no_pcrs_24_data_when_get_territorial_unit_report_then_tweet_without_pcrs24h_returned(self,
                                                                                                        get_report_sentence_with_unit_mock,
                                                                                                        get_report_sentence_mock):

        territorial_unit = MagicMock()
        date_header = MagicMock()
        today_data = {
            Measurement.PCRS: MagicMock(),
            Measurement.DEATHS: MagicMock(),
            Measurement.ADMITTED_PEOPLE: MagicMock(),
            Measurement.PERCENTAGE_ICU: MagicMock(),
            Measurement.PERCENTAGE_ADMITTED: MagicMock()
        }
        yesterday_data = MagicMock()
        accumulated_today = MagicMock()
        pcrs = "pcrs"
        deaths = "deaths"
        admitted = "admitted"
        uci = "uci"
        get_report_sentence_mock.side_effect = [pcrs, deaths]
        accumulated_string = "0,21"
        get_report_sentence_with_unit_mock.side_effect = [accumulated_string, admitted, uci]

        expected_tweet = f"{territorial_unit} - {date_header}:\n\n{pcrs}\n{accumulated_string}" \
                         f"\n\n{deaths}\n\n{admitted}\n{uci}"

        self.assertEqual(expected_tweet, get_territorial_unit_report(territorial_unit, date_header, today_data,
                                                                     yesterday_data, accumulated_today))

        get_report_sentence_with_unit_mock.assert_has_calls([call("💥 IA 14 días",
                                                                   today_data.get(Measurement.ACCUMULATED_INCIDENCE),
                                                                   yesterday_data.get(Measurement.ACCUMULATED_INCIDENCE),
                                                                   "/100.000 hab."),
                                                             call("🚑 Hospitalizados",
                                                                  today_data.get(Measurement.PERCENTAGE_ADMITTED),
                                                                  yesterday_data.get(Measurement.PERCENTAGE_ADMITTED), "%"),
                                                             call("🏥 UCI", today_data.get(Measurement.PERCENTAGE_ICU),
                                                                  yesterday_data.get(Measurement.PERCENTAGE_ICU), "%")])

        get_report_sentence_mock.assert_has_calls([
            call("💉 PCRs", today_data.get(Measurement.PCRS),
                 yesterday_data.get(Measurement.PCRS),
                 accumulated_today.get(Measurement.PCRS)),
            call("😢 Muertes", today_data.get(Measurement.DEATHS),
                 yesterday_data.get(Measurement.DEATHS),
                 accumulated_today.get(Measurement.DEATHS))
        ])

    @patch("helpers.reports.get_tendency_emoji", return_value="^ 1")
    def test_given_data_when_get_report_sentence_with_unit_then_impact_returned(self, get_tendency_emoji_mock):
        stat = "IA 14 days"
        today_total = 1100.18
        yesterday_total = 80.10

        self.assertEqual("{0}: {1}%100.000 hab. {2}".format(stat, "1.100,18", get_tendency_emoji_mock.return_value),
                         get_report_sentence_with_unit(stat, today_total, yesterday_total, "%100.000 hab."))

        get_tendency_emoji_mock.assert_called_once_with(today_total, yesterday_total)

    @patch("helpers.reports.get_tendency_emoji", return_value="^ 1")
    def test_given_accumulated_when_get_report_sentence_then_report_includes_accumulated(self, get_tendency_emoji_mock):
        stat = "PCRS"
        today_value = 1000
        yesterday_value = 500
        today_accumulated = 8000
        result = get_report_sentence(stat, today_value, yesterday_value, today_accumulated)

        self.assertEqual("{0}: +1.000 {1} (Totales: 8.000)".format(stat, get_tendency_emoji_mock.return_value), result)

        get_tendency_emoji_mock.assert_called_once_with(today_value, yesterday_value)

    @patch("helpers.reports.get_tendency_emoji", return_value="^ 1")
    def test_given_no_accumulated_when_get_report_sentence_then_report_no_include_accumulated(self,
                                                                                              get_tendency_emoji_mock):

        stat = "PCRS"
        today_value = 1000
        yesterday_value = 500
        result = get_report_sentence(stat, today_value, yesterday_value)

        self.assertEqual("{0}: +1.000 {1}".format(stat, get_tendency_emoji_mock.return_value), result)

        get_tendency_emoji_mock.assert_called_once_with(today_value, yesterday_value)

    def test_given_no_yesterday_when_get_tendency_icon_then_empty_returned(self):
        emoji = get_tendency_emoji(20, None)

        self.assertEqual("", emoji)

    def test_given_today_higher_than_yesterday_when_get_tendency_icon_then_upwards_triangle_returned(self):
        emoji = get_tendency_emoji(2000, 15)

        self.assertEqual("🔺1.985", emoji)

    def test_given_today_lower_than_yesterday_when_get_tendency_icon_then_downwards_triangle_returned(self):
        emoji = get_tendency_emoji(15, 2000)

        self.assertEqual("🔻1.985", emoji)

    def test_given_today_lower_than_yesterday_with_decimals_when_get_tendency_icon_then_downwards_triangle_returned(self):
        emoji = get_tendency_emoji(14.99, 1500.01)

        self.assertEqual("🔻1.485,02", emoji)

    def test_given_today_equals_than_yesterday_when_get_tendency_icon_then_back_arrow_returned(self):
        emoji = get_tendency_emoji(20, 20)

        self.assertEqual("🔙", emoji)

    def test_given_no_dates_when_get_graph_url_then_base_url_returned(self):
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL, get_graph_url())

    def test_graph_image_path_does_not_start_with_slash(self):
        self.assertFalse(GRAPH_IMAGE_PATH.startswith("/"))

    @patch("helpers.reports.os.environ", {"GRAFANA_SERVER": "http://grafana-server.com/"})
    def test_given_custom_grafana_server_when_get_graph_url_then_custom_server_used_returned(self):
        self.assertEqual("http://grafana-server.com/" + GRAPH_IMAGE_PATH, get_graph_url())

    @patch("helpers.reports.os.environ", {"GRAFANA_SERVER": "http://grafana-server.com"})
    def test_given_custom_grafana_server_without_final_slash_when_get_graph_url_then_separator_slash_included(self):
        self.assertEqual("http://grafana-server.com/" + GRAPH_IMAGE_PATH, get_graph_url())

    def test_given_start_when_get_graph_url_then_from_included_url_returned(self):
        date = datetime(2020, 8, 6)
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL + "&from=" + str(int(date.strftime("%s")) * 1000),
                         get_graph_url(date))

    def test_given_end_when_get_graph_url_then_to_included_url_returned(self):
        date = datetime(2020, 8, 6)
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL + "&to=" + str(int(date.strftime("%s")) * 1000),
                         get_graph_url(end=date))

    def test_given_start_and_end_when_get_graph_url_then_from_and_to_included_url_returned(self):
        date1 = datetime(2020, 8, 6)
        date2 = datetime(2020, 8, 12)
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL + "&from=" + str(int(date1.strftime("%s")) * 1000) +
                         "&to=" + str(int(date2.strftime("%s")) * 1000), get_graph_url(date1, date2))

    def test_given_start_end_and_var_when_get_graph_url_then_from_to_and_var_included_url_returned(self):
        date1 = datetime(2020, 8, 6)
        date2 = datetime(2020, 8, 12)
        var_name = "group_by"
        var_value = "1w,4d"
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL + "&from=" + str(int(date1.strftime("%s")) * 1000) +
                         "&to=" + str(int(date2.strftime("%s")) * 1000) + f"&var-{var_name}={var_value}",
                         get_graph_url(date1, date2, {var_name: var_value}))

    def test_given_start_end_and_vars_when_get_graph_url_then_from_to_and_vars_included_url_returned(self):
        date1 = datetime(2020, 8, 6)
        date2 = datetime(2020, 8, 12)
        var1_name = "group_by"
        var1_value = "1w,4d"
        var2_name = "ccaa"
        var2_value = "Madrid"
        self.assertEqual(DEFAULT_GRAPH_IMAGE_URL + "&from=" + str(int(date1.strftime("%s")) * 1000) +
                         "&to=" + str(int(date2.strftime("%s")) * 1000) +
                         f"&var-{var1_name}={var1_value}&var-{var2_name}={var2_value}",
                         get_graph_url(date1, date2, {var1_name: var1_value, var2_name: var2_value}))
