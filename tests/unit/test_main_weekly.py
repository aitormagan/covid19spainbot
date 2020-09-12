import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from main_weekly import get_date_header, get_final_tweet, main


class MainWeeklyUnitTest(unittest.TestCase):

    @patch("main_weekly.get_graph_url")
    @patch("main_weekly.datetime")
    @patch("main_weekly.influx")
    @patch("main_weekly.get_report_by_ccaa")
    @patch("main_weekly.twitter")
    @patch("main_weekly.get_global_report")
    @patch("main_weekly.get_final_tweet")
    @patch("main_weekly.get_date_header")
    def test_when_main_then_reports_published(self, get_date_header_mock, get_final_tweet_mock,
                                              get_global_report_mock, twitter_mock, get_report_by_ccaa_mock,
                                              influx_mock, datetime_mock, get_graph_url_mock):

        today = datetime(2020, 8, 1)
        datetime_mock.now.return_value = today
        previous_week = today - timedelta(7)

        today_data = MagicMock()
        previous_week_data = MagicMock()
        accumulated_data = MagicMock()

        influx_mock.get_all_stats_group_by_week.side_effect = [today_data, previous_week_data]
        influx_mock.get_all_stats_accumulated_until_day.return_value = accumulated_data

        main()

        influx_mock.get_all_stats_group_by_week.assert_has_calls([call(today), call(previous_week)])
        get_report_by_ccaa_mock.assert_called_once_with(get_date_header_mock.return_value, today_data,
                                                        previous_week_data, accumulated_data)
        get_date_header_mock.assert_called_once_with(today)

        influx_mock.get_all_stats_accumulated_until_day.assert_called_once_with(today)
        get_global_report_mock.assert_called_once_with(get_date_header_mock.return_value, today_data,
                                                       previous_week_data, accumulated_data)

        twitter_mock.publish_tweet_with_media.assert_called_once_with(get_global_report_mock.return_value,
                                                                      get_graph_url_mock.return_value)
        twitter_mock.publish_tweets.assert_called_once_with(get_report_by_ccaa_mock.return_value,
                                                            twitter_mock.publish_tweet_with_media.return_value)
        twitter_mock.publish_tweet.assert_called_once_with(get_final_tweet_mock.return_value,
                                                           twitter_mock.publish_tweets.return_value)
        get_graph_url_mock.assert_called_once_with(additional_vars={"group_by": "1w,4d"})

    def test_when_get_header_then_monday_and_sunday_included(self):
        date = datetime(2020, 7, 27)

        header = get_date_header(date)

        self.assertEqual("Sem. 27/07 al 02/08", header)

    def test_when_get_final_tweet_then_monday_and_sunday_included_is_correct(self):
        summary = get_final_tweet()

        self.assertTrue("Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1&var-group_by=1w,4d"
                        in summary)
