import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, call, ANY
from main_daily import subtract_days_ignoring_weekends, main, Measurement, HTTPError, get_today_numbers, get_header, \
    get_summary_tweet, publish_report, update_database


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

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value,
                                                     subtract_days_ignoring_weekends_mock.return_value)
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

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value,
                                                     subtract_days_ignoring_weekends_mock.return_value)
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

        update_database_mock.assert_called_once_with(datetime_mock.now.return_value,
                                                     subtract_days_ignoring_weekends_mock.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.PCRS, datetime_mock.now.return_value)
        twitter_mock.send_dm.assert_called_once_with(ANY)
        dm_text = twitter_mock.send_dm.call_args[0][0]
        self.assertEqual(280, len(dm_text))
        self.assertTrue(dm_text.startswith(f"There was un unhandled exception. Trace:\n\n{exception_text}"))


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
    @patch("main_daily.get_today_numbers")
    def test_given_pdf_requires_area_when_update_database_then_info_calculated_and_inserted(self,
                                                                                            get_today_numbers_mock,
                                                                                            influx_mock,
                                                                                            ministry_report_mock):

        today = MagicMock()
        yesterday = MagicMock()

        pcrs_pdf = MagicMock()
        accumulated_pcrs = MagicMock()
        last_24h_pcrs = MagicMock()
        pcrs_pdf.get_column_data.side_effect = [Exception(), accumulated_pcrs, last_24h_pcrs]
        deaths_pdf = MagicMock()
        ministry_report_mock.side_effect = [pcrs_pdf, deaths_pdf, pcrs_pdf]

        yesterday_pcrs_accumulated = MagicMock()
        yesterday_deaths_accumulated = MagicMock()
        influx_mock.get_stat_accumulated_until_day.side_effect = [yesterday_pcrs_accumulated,
                                                                  yesterday_deaths_accumulated]

        today_pcrs = MagicMock()
        today_deaths = MagicMock()
        get_today_numbers_mock.side_effect = [today_pcrs, today_deaths]

        update_database(today, yesterday)

        ministry_report_mock.assert_has_calls([call(today, 1), call(today, 2),
                                               call(today, 1,  (239, 56, 239 + 283, 56 + 756))])
        pcrs_pdf.get_column_data.assert_has_calls([call(1), call(1), call(2)])
        deaths_pdf.get_column_data.assert_called_once_with(3)

        influx_mock.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.PCRS, yesterday),
                                                                     call(Measurement.DEATHS, yesterday)])

        get_today_numbers_mock.assert_has_calls([call(accumulated_pcrs,
                                                      yesterday_pcrs_accumulated),
                                                 call(deaths_pdf.get_column_data.return_value,
                                                      yesterday_deaths_accumulated)])

        influx_mock.insert_stats_in_influx.assert_has_calls([call(Measurement.PCRS, today, today_pcrs),
                                                             call(Measurement.DEATHS, today, today_deaths),
                                                             call(Measurement.PCRS_LAST_24H, today,
                                                                  last_24h_pcrs)])

    @patch("main_daily.SpainCovid19MinistryReport")
    @patch("main_daily.influx")
    @patch("main_daily.get_today_numbers")
    def test_when_update_database_then_info_calculated_and_inserted(self, get_today_numbers_mock,
                                                                    influx_mock, ministry_report_mock):

        today = MagicMock()
        yesterday = MagicMock()

        pcrs_pdf = MagicMock()
        accumulated_pcrs = MagicMock()
        last_24h_pcrs = MagicMock()
        pcrs_pdf.get_column_data.side_effect = [accumulated_pcrs, last_24h_pcrs]
        deaths_pdf = MagicMock()
        ministry_report_mock.side_effect = [pcrs_pdf, deaths_pdf]

        yesterday_pcrs_accumulated = MagicMock()
        yesterday_deaths_accumulated = MagicMock()
        influx_mock.get_stat_accumulated_until_day.side_effect = [yesterday_pcrs_accumulated,
                                                                  yesterday_deaths_accumulated]

        today_pcrs = MagicMock()
        today_deaths = MagicMock()
        get_today_numbers_mock.side_effect = [today_pcrs, today_deaths]

        update_database(today, yesterday)

        ministry_report_mock.assert_has_calls([call(today, 1), call(today, 2)])
        pcrs_pdf.get_column_data.assert_has_calls([call(1), call(2)])
        deaths_pdf.get_column_data.assert_called_once_with(3)

        influx_mock.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.PCRS, yesterday),
                                                                     call(Measurement.DEATHS, yesterday)])

        get_today_numbers_mock.assert_has_calls([call(accumulated_pcrs,
                                                      yesterday_pcrs_accumulated),
                                                 call(deaths_pdf.get_column_data.return_value,
                                                      yesterday_deaths_accumulated)])

        influx_mock.insert_stats_in_influx.assert_has_calls([call(Measurement.PCRS, today, today_pcrs),
                                                             call(Measurement.DEATHS, today, today_deaths),
                                                             call(Measurement.PCRS_LAST_24H, today,
                                                                  last_24h_pcrs)])

    def test_given_today_and_yesterday_data_when_get_today_numbers_then_subtraction_returned(self):
        today = {"Madrid": 100, "Cataluña": 90}
        yesterday = {"Madrid": 95, "Cataluña": 80}

        self.assertEqual({"Madrid": 5, "Cataluña": 10}, get_today_numbers(today, yesterday))

    def test_given_only_today_data_when_get_today_numbers_then_today_data_returned(self):
        today = {"Madrid": 100, "Cataluña": 90}
        yesterday = {}

        self.assertEqual({"Madrid": 100, "Cataluña": 90}, get_today_numbers(today, yesterday))

    @patch("main_daily.influx")
    @patch("main_daily.get_report_by_ccaa")
    @patch("main_daily.twitter")
    @patch("main_daily.get_human_summary")
    @patch("main_daily.get_summary_tweet")
    @patch("main_daily.get_header")
    def test_when_publish_report_then_info_calculated_and_published(self, get_header_mock, get_summary_tweet_mock,
                                                                    get_human_summary_mock, twitter_mock,
                                                                    get_report_by_ccaa_mock, influx_mock):
        today = MagicMock()
        yesterday = MagicMock()

        today_pcrs_report = MagicMock()
        today_deaths_report = MagicMock()
        yesterday_pcrs_report = MagicMock()
        yesterday_deaths_report = MagicMock()
        today_pcrs_accumulated_report = MagicMock()
        today_deaths_accumulated_report = MagicMock()

        influx_mock.get_all_stats_group_by_day.side_effect = [(today_pcrs_report, today_deaths_report, MagicMock()),
                                                              (yesterday_pcrs_report, yesterday_deaths_report,
                                                               MagicMock())]

        influx_mock.get_all_stats_accumulated_until_day.return_value = (today_pcrs_accumulated_report,
                                                                        today_deaths_accumulated_report)

        publish_report(today, yesterday)

        influx_mock.get_all_stats_group_by_day.assert_has_calls([call(today), call(yesterday)])
        get_report_by_ccaa_mock.assert_has_calls([call(today_pcrs_report, yesterday_pcrs_report),
                                                  call(today_deaths_report, yesterday_deaths_report)])
        get_header_mock.assert_has_calls([call("PCR+", today), call("Muertes", today)])

        influx_mock.get_all_stats_accumulated_until_day.assert_called_once_with(today)
        get_human_summary_mock.assert_has_calls([call("PCR+", today_pcrs_report, yesterday_pcrs_report,
                                                      today_pcrs_accumulated_report),
                                                 call("Muertes", today_deaths_report, yesterday_deaths_report,
                                                      today_deaths_accumulated_report)])

        get_summary_tweet_mock.assert_called_once_with(today, get_human_summary_mock.return_value,
                                                       get_human_summary_mock.return_value)

        publish_tweet_call = call(get_report_by_ccaa_mock.return_value, get_header_mock.return_value)
        twitter_mock.publish_tweets.assert_has_calls([publish_tweet_call, publish_tweet_call,
                                                      call([get_summary_tweet_mock.return_value])])

    def test_given_monday_when_get_header_then_weekend_text_included(self):
        date = datetime(2020, 7, 27)
        stat = "PCR+"

        header = get_header(stat, date)

        self.assertEqual("PCR+ reportadas el fin de semana del 26/07/2020", header)

    def test_given_tuesday_when_get_header_then_weekend_text_not_included(self):
        date = datetime(2020, 7, 28)
        stat = "PCR+"

        header = get_header(stat, date)

        self.assertEqual("PCR+ reportadas el 27/07/2020", header)

    def test_when_get_summary_tweet_then_date_is_correct(self):
        date = datetime(2020, 7, 27)
        pcrs_summary = "pcrs_summary"
        deaths_summary = "deaths_summary"

        summary = get_summary_tweet(date, pcrs_summary, deaths_summary)

        self.assertTrue(summary.startswith("Resumen España al finalizar el 26/07/2020:\n\n{0}\n{1}".format(
            pcrs_summary, deaths_summary)))
