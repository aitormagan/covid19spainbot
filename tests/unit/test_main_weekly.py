import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from main_weekly import get_header, get_week_summary_tweet, main, Measurement, GRAPH_IMAGE_URL


class MainWeeklyUnitTest(unittest.TestCase):

    @patch("main_weekly.datetime")
    @patch("main_weekly.influx")
    @patch("main_weekly.get_report_by_ccaa")
    @patch("main_weekly.twitter")
    @patch("main_weekly.get_human_summary")
    @patch("main_weekly.get_week_summary_tweet")
    @patch("main_weekly.get_header")
    def test_when_main_then_reports_published(self, get_header_mock, get_week_summary_tweet_mock,
                                              get_human_summary_mock, twitter_mock, get_report_by_ccaa_mock,
                                              influx_mock, datetime_mock):

        today = datetime(2020, 8, 1)
        datetime_mock.now.return_value = today
        previous_week = today - timedelta(7)

        pcrs_current_week = MagicMock()
        pcrs_previous_week = MagicMock()
        deaths_current_week = MagicMock()
        deaths_previous_week = MagicMock()
        today_pcrs_accumulated_report = MagicMock()
        today_deaths_accumulated_report = MagicMock()

        influx_mock.get_stat_group_by_week.side_effect = [pcrs_current_week, pcrs_previous_week,
                                                          deaths_current_week, deaths_previous_week]

        influx_mock.get_all_stats_accumulated_until_day.return_value = (today_pcrs_accumulated_report,
                                                                        today_deaths_accumulated_report)

        main()

        influx_mock.get_stat_group_by_week.assert_has_calls([call(Measurement.PCRS, today),
                                                             call(Measurement.PCRS, previous_week),
                                                             call(Measurement.DEATHS, today),
                                                             call(Measurement.DEATHS, previous_week)])
        get_report_by_ccaa_mock.assert_has_calls([call(pcrs_current_week, pcrs_previous_week),
                                                  call(deaths_current_week, deaths_previous_week)])
        get_header_mock.assert_has_calls([call("PCR+", today), call("Muertes", today)])

        influx_mock.get_all_stats_accumulated_until_day.assert_called_once_with(today)
        get_human_summary_mock.assert_has_calls([call("PCR+", pcrs_current_week, pcrs_previous_week,
                                                      today_pcrs_accumulated_report),
                                                 call("Muertes", deaths_current_week, deaths_previous_week,
                                                      today_deaths_accumulated_report)])

        get_week_summary_tweet_mock.assert_called_once_with(today, get_human_summary_mock.return_value,
                                                            get_human_summary_mock.return_value)

        publish_tweet_call = call(get_report_by_ccaa_mock.return_value, get_header_mock.return_value)
        twitter_mock.publish_tweets.assert_has_calls([publish_tweet_call, publish_tweet_call])
        twitter_mock.publish_tweet_with_media.assert_called_once_with(get_week_summary_tweet_mock.return_value,
                                                                      GRAPH_IMAGE_URL)

    def test_when_get_header_then_monday_and_sunday_included(self):
        date = datetime(2020, 7, 27)
        stat = "PCR+"

        header = get_header(stat, date)

        self.assertEqual("PCR+ reportadas la semana del 27/07/2020 al 02/08/2020", header)

    def test_when_get_summary_tweet_then_monday_and_sunday_included_is_correct(self):
        date = datetime(2020, 7, 27)
        pcrs_summary = "pcrs_summary"
        deaths_summary = "deaths_summary"

        summary = get_week_summary_tweet(date, pcrs_summary, deaths_summary)

        self.assertTrue(summary.startswith("Resumen España la semana del 27/07/2020 al 02/08/2020:\n\n{0}\n{1}".format(
            pcrs_summary, deaths_summary)))
