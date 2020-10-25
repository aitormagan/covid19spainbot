import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call, ANY
from main_daily import subtract_days_ignoring_weekends, main, Measurement, HTTPError, get_today_numbers, \
    publish_report, update_database, update_stat, get_date_header, get_final_tweet


class MainDailyUnitTest(unittest.TestCase):

    @patch("main_daily.subtract_days_ignoring_weekends")
    @patch("main_daily.update_database")
    @patch("main_daily.publish_report")
    @patch("main_daily.datetime")
    @patch("main_daily.influx")
    def test_given_data_when_main_then_update_and_publish_not_called(self, influx_mock, datetime_mock,
                                                                     publish_report_mock,
                                                                     update_database_mock,
                                                                     subtract_days_ignoring_weekends_mock):

        influx_mock.get_stat_group_by_day.return_value = {"Madrid": 1}

        main()

        update_database_mock.assert_not_called()
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.PCRS, datetime_mock.now.return_value)

    @patch("main_daily.subtract_days_ignoring_weekends")
    @patch("main_daily.update_database")
    @patch("main_daily.publish_report")
    @patch("main_daily.datetime")
    @patch("main_daily.influx")
    def test_given_no_data_when_main_then_update_and_publish_called(self, influx_mock, datetime_mock,
                                                                    publish_report_mock,
                                                                    update_database_mock,
                                                                    subtract_days_ignoring_weekends_mock):

        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_called_once_with(datetime_mock.now.return_value,
                                                    subtract_days_ignoring_weekends_mock.return_value)
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.PCRS, datetime_mock.now.return_value)

    @patch("main_daily.subtract_days_ignoring_weekends")
    @patch("main_daily.update_database")
    @patch("main_daily.publish_report")
    @patch("main_daily.datetime")
    @patch("main_daily.influx")
    def test_given_no_data_and_http_error_when_main_then_no_exception_raised(self, influx_mock, datetime_mock,
                                                                             publish_report_mock, update_database_mock,
                                                                             subtract_days_ignoring_weekends_mock):

        update_database_mock.side_effect = HTTPError("http://google.com", 404, MagicMock(), MagicMock(), MagicMock())
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.PCRS, datetime_mock.now.return_value)

    @patch("main_daily.twitter")
    @patch("main_daily.subtract_days_ignoring_weekends")
    @patch("main_daily.update_database")
    @patch("main_daily.publish_report")
    @patch("main_daily.datetime")
    @patch("main_daily.influx")
    def test_given_no_data_and_another_error_when_main_then_twitter_dm_sent(self, influx_mock, datetime_mock,
                                                                            publish_report_mock, update_database_mock,
                                                                            subtract_days_ignoring_weekends_mock,
                                                                            twitter_mock):

        exception_text = "exception text"
        update_database_mock.side_effect = Exception(exception_text * 100)
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.PCRS, datetime_mock.now.return_value)
        twitter_mock.send_dm.assert_called_once_with(ANY)
        dm_text = twitter_mock.send_dm.call_args[0][0]
        self.assertEqual(280, len(dm_text))
        self.assertTrue(dm_text.startswith(f"There was an unhandled exception. Trace:\n\n{exception_text}"))

    def test_given_no_weekends_when_subtract_days_ignoring_weekends_then_no_gaps(self):
        date = datetime(2020, 7, 29)
        self.assertEqual(datetime(2020, 7, 27), subtract_days_ignoring_weekends(date, 2))

    def test_given_29_july_and_three_day_when_subtract_days_ignoring_weekends_then_friday(self):
        date = datetime(2020, 7, 29)
        self.assertEqual(datetime(2020, 7, 24), subtract_days_ignoring_weekends(date, 3))

    def test_given_29_july_and_four_day_when_subtract_days_ignoring_weekends_then_thursday(self):
        date = datetime(2020, 7, 29)
        self.assertEqual(datetime(2020, 7, 23), subtract_days_ignoring_weekends(date, 4))

    @patch("main_daily.SpainCovid19MinistryReport")
    @patch("main_daily.influx")
    @patch("main_daily.update_stat")
    def test_given_pdf_requires_area_when_update_database_then_info_calculated_and_inserted(self,
                                                                                            update_stat_mock,
                                                                                            influx_mock,
                                                                                            ministry_report_mock):

        today = MagicMock()

        pcrs_pdf = MagicMock()
        accumulated_pcrs = MagicMock()
        last_24h_pcrs = MagicMock()
        accumulated_incidence = MagicMock()
        pcrs_pdf.get_column_data.side_effect = [Exception(), accumulated_pcrs, last_24h_pcrs, accumulated_incidence]
        deaths_pdf = MagicMock()
        accumulated_admitted = MagicMock()
        accumulated_icu = MagicMock()
        accumulated_deaths = MagicMock()
        hospitals_pdf = MagicMock()
        deaths_pdf.get_column_data.side_effect = [accumulated_deaths]
        hospitals_pdf.get_column_data.side_effect = [accumulated_admitted, accumulated_icu]
        ministry_report_mock.side_effect = [pcrs_pdf, deaths_pdf, hospitals_pdf, pcrs_pdf]

        yesterday_pcrs_accumulated = MagicMock()
        yesterday_deaths_accumulated = MagicMock()
        influx_mock.get_stat_accumulated_until_day.side_effect = [yesterday_pcrs_accumulated,
                                                                  yesterday_deaths_accumulated]

        today_pcrs = MagicMock()
        today_deaths = MagicMock()
        today_admitted = MagicMock()
        today_icu = MagicMock()
        update_stat_mock.side_effect = [today_pcrs, today_deaths, today_admitted, today_icu]

        update_database(today)

        ministry_report_mock.assert_has_calls([call(today, 1),
                                               call(today, 5, (142, 539, 142+343, 539+265)),
                                               call(today, 3),
                                               call(today, 1, (239, 56, 239 + 283, 56 + 756))])
        pcrs_pdf.get_column_data.assert_has_calls([call(1), call(2), call(3, 1, float)])
        deaths_pdf.get_column_data.assert_has_calls([call(1)])
        hospitals_pdf.get_column_data.assert_has_calls([call(1), call(2)])

        update_stat_mock.assert_has_calls([call(Measurement.PCRS, accumulated_pcrs, today),
                                          call(Measurement.DEATHS, accumulated_deaths, today),
                                          call(Measurement.ADMITTED_PEOPLE, accumulated_admitted, today),
                                          call(Measurement.ICU_PEOPLE, accumulated_icu, today)])

        influx_mock.insert_stats.assert_has_calls([call(Measurement.PCRS_LAST_24H, today, last_24h_pcrs),
                                                   call(Measurement.ACCUMULATED_INCIDENCE, today,
                                                        accumulated_incidence)])

    @patch("main_daily.SpainCovid19MinistryReport")
    @patch("main_daily.influx")
    @patch("main_daily.update_stat")
    def test_when_update_database_then_info_calculated_and_inserted(self, update_stat_mock,
                                                                    influx_mock, ministry_report_mock):

        today = MagicMock()

        pcrs_pdf = MagicMock()
        accumulated_pcrs = MagicMock()
        last_24h_pcrs = MagicMock()
        accumulated_incidence = MagicMock()
        pcrs_pdf.get_column_data.side_effect = [accumulated_pcrs, last_24h_pcrs, accumulated_incidence]
        deaths_pdf = MagicMock()
        accumulated_admitted = MagicMock()
        accumulated_icu = MagicMock()
        accumulated_deaths = MagicMock()
        hospitals_pdf = MagicMock()
        deaths_pdf.get_column_data.side_effect = [accumulated_deaths]
        hospitals_pdf.get_column_data.side_effect = [accumulated_admitted, accumulated_icu]
        ministry_report_mock.side_effect = [pcrs_pdf, deaths_pdf, hospitals_pdf]

        yesterday_pcrs_accumulated = MagicMock()
        yesterday_deaths_accumulated = MagicMock()
        influx_mock.get_stat_accumulated_until_day.side_effect = [yesterday_pcrs_accumulated,
                                                                  yesterday_deaths_accumulated]

        today_pcrs = MagicMock()
        today_deaths = MagicMock()
        today_admitted = MagicMock()
        today_icu = MagicMock()
        update_stat_mock.side_effect = [today_pcrs, today_deaths, today_admitted, today_icu]

        update_database(today)

        ministry_report_mock.assert_has_calls([call(today, 1),
                                               call(today, 5, (142, 539, 142+343, 539+265)),
                                               call(today, 3)])
        pcrs_pdf.get_column_data.assert_has_calls([call(1), call(2), call(3, 1, float)])
        deaths_pdf.get_column_data.assert_has_calls([call(1)])
        hospitals_pdf.get_column_data.assert_has_calls([call(1), call(2)])

        update_stat_mock.assert_has_calls([call(Measurement.PCRS, accumulated_pcrs, today),
                                          call(Measurement.DEATHS, accumulated_deaths, today),
                                          call(Measurement.ADMITTED_PEOPLE, accumulated_admitted, today),
                                          call(Measurement.ICU_PEOPLE, accumulated_icu, today)])

        influx_mock.insert_stats.assert_has_calls([call(Measurement.PCRS_LAST_24H, today, last_24h_pcrs),
                                                   call(Measurement.ACCUMULATED_INCIDENCE, today,
                                                        accumulated_incidence)])

    @patch("main_daily.influx")
    @patch("main_daily.get_today_numbers")
    def test_given_data_and_date_when_update_stat_then_info_calculated_stored_and_returned(self, get_today_numbers_mock,
                                                                                           influx_mock):
        stat = MagicMock()
        date = MagicMock()
        accumulated_today = MagicMock()

        result = update_stat(stat, accumulated_today, date)

        self.assertEqual(result, get_today_numbers_mock.return_value)
        get_today_numbers_mock.assert_called_once_with(accumulated_today,
                                                       influx_mock.get_stat_accumulated_until_day.return_value)
        influx_mock.get_stat_accumulated_until_day.assert_called_once_with(stat, date)
        influx_mock.insert_stats.assert_called_once_with(stat, date, get_today_numbers_mock.return_value)

    def test_given_today_and_yesterday_data_when_get_today_numbers_then_subtraction_returned(self):
        today = {"Madrid": 100, "Cataluña": 90}
        yesterday = {"Madrid": 95, "Cataluña": 80}

        self.assertEqual({"Madrid": 5, "Cataluña": 10}, get_today_numbers(today, yesterday))

    def test_given_only_today_data_when_get_today_numbers_then_today_data_returned(self):
        today = {"Madrid": 100, "Cataluña": 90}
        yesterday = {}

        self.assertEqual({"Madrid": 100, "Cataluña": 90}, get_today_numbers(today, yesterday))

    @patch("main_daily.get_graph_url")
    @patch("main_daily.influx")
    @patch("main_daily.get_report_by_ccaa")
    @patch("main_daily.twitter")
    @patch("main_daily.get_global_report")
    @patch("main_daily.get_final_tweet")
    @patch("main_daily.get_date_header")
    def test_when_publish_report_then_info_calculated_and_published(self, get_date_header_mock, get_final_tweet_mock,
                                                                    get_global_report_mock, twitter_mock,
                                                                    get_report_by_ccaa_mock, influx_mock,
                                                                    get_graph_url_mock):
        today = datetime(2020, 8, 6)
        yesterday = datetime(2020, 8, 5)

        today_data = MagicMock()
        yesterday_data = MagicMock()
        accumulated_today = MagicMock()

        influx_mock.get_all_stats_group_by_day.side_effect = [today_data, yesterday_data]

        influx_mock.get_all_stats_accumulated_until_day.return_value = accumulated_today

        publish_report(today, yesterday)

        influx_mock.get_all_stats_group_by_day.assert_has_calls([call(today), call(yesterday)])
        get_report_by_ccaa_mock.assert_called_once_with(get_date_header_mock.return_value, today_data, yesterday_data,
                                                        accumulated_today)
        get_date_header_mock.assert_called_once_with(today)

        influx_mock.get_all_stats_accumulated_until_day.assert_called_once_with(today)
        get_global_report_mock.assert_called_once_with(get_date_header_mock.return_value, today_data, yesterday_data,
                                                       accumulated_today)

        twitter_mock.publish_tweet_with_media.assert_called_once_with(get_global_report_mock.return_value,
                                                                      get_graph_url_mock.return_value)
        twitter_mock.publish_tweets.assert_called_once_with(get_report_by_ccaa_mock.return_value,
                                                            twitter_mock.publish_tweet_with_media.return_value)
        twitter_mock.publish_tweet.assert_called_once_with(get_final_tweet_mock.return_value,
                                                           twitter_mock.publish_tweets.return_value)
        get_graph_url_mock.assert_called_once_with(today - timedelta(31), today)

    def test_given_monday_when_get_date_header_then_weekend_text_included(self):
        date = datetime(2020, 7, 27)

        header = get_date_header(date)

        self.assertEqual("24/07/2020 al 26/07/2020", header)

    def test_given_tuesday_when_get_date_header_then_weekend_text_not_included(self):
        date = datetime(2020, 7, 28)

        header = get_date_header(date)

        self.assertEqual("27/07/2020", header)

    def test_when_get_summary_tweet_then_date_is_correct(self):

        summary = get_final_tweet()

        self.assertTrue("Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1" in summary)
        self.assertTrue("Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1" in summary)
