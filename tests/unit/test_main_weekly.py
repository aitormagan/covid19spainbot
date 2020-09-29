import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from main_weekly import get_date_header, get_final_tweet, main, delete_pcrs24h, Measurement


class MainWeeklyUnitTest(unittest.TestCase):

    @patch("main_weekly.get_graph_url")
    @patch("main_weekly.datetime")
    @patch("main_weekly.influx")
    @patch("main_weekly.get_report_by_ccaa")
    @patch("main_weekly.twitter")
    @patch("main_weekly.get_global_report")
    @patch("main_weekly.get_final_tweet")
    @patch("main_weekly.get_date_header")
    @patch("main_weekly.delete_pcrs24h")
    def test_when_main_then_reports_published(self, delete_pcrs_24h_mock, get_date_header_mock, get_final_tweet_mock,
                                              get_global_report_mock, twitter_mock, get_report_by_ccaa_mock,
                                              influx_mock, datetime_mock, get_graph_url_mock):

        delete_pcrs_24h_mock.side_effect = lambda x: x
        today = datetime(2020, 8, 1)
        datetime_mock.now.return_value = today
        previous_week = today - timedelta(7)

        today_data = MagicMock()
        previous_week_data = MagicMock()
        accumulated_today = MagicMock()
        accumulated_two_weeks_ago = MagicMock()

        influx_mock.get_all_stats_group_by_week.side_effect = [today_data, previous_week_data]
        influx_mock.get_all_stats_accumulated_until_day.side_effect = [accumulated_today, accumulated_two_weeks_ago]

        main()

        influx_mock.get_all_stats_group_by_week.assert_has_calls([call(today), call(previous_week)])
        get_report_by_ccaa_mock.assert_called_once_with(get_date_header_mock.return_value, today_data,
                                                        previous_week_data, accumulated_today,
                                                        accumulated_two_weeks_ago)
        get_date_header_mock.assert_called_once_with(today)

        influx_mock.get_all_stats_accumulated_until_day.assert_has_calls([call(today), call(today - timedelta(14))])
        get_global_report_mock.assert_called_once_with(get_date_header_mock.return_value, today_data,
                                                       previous_week_data, accumulated_today, accumulated_two_weeks_ago)

        twitter_mock.publish_tweet_with_media.assert_called_once_with(get_global_report_mock.return_value,
                                                                      get_graph_url_mock.return_value)
        twitter_mock.publish_tweets.assert_called_once_with(get_report_by_ccaa_mock.return_value,
                                                            twitter_mock.publish_tweet_with_media.return_value)
        twitter_mock.publish_tweet.assert_called_once_with(get_final_tweet_mock.return_value,
                                                           twitter_mock.publish_tweets.return_value)
        get_graph_url_mock.assert_called_once_with(additional_vars={"group_by": "1w,4d"})

    def test_given_element_with_pcrs24h_when_delete_pcrs24h_then_removed_from_all_elements(self):

        pcrs = 1
        deaths = 2
        icu = 3
        admitted = 4

        element = {
            "Madrid": {
                Measurement.PCRS: pcrs,
                Measurement.PCRS_LAST_24H: 2,
                Measurement.DEATHS: deaths,
                Measurement.ICU_PEOPLE: icu,
                Measurement.ADMITTED_PEOPLE: admitted
            },
            "CLM": {
                Measurement.PCRS: pcrs,
                Measurement.PCRS_LAST_24H: 2
            }
        }

        self.assertEqual(delete_pcrs24h(element), {
            "Madrid": {
                Measurement.PCRS: pcrs,
                Measurement.DEATHS: deaths,
                Measurement.ICU_PEOPLE: icu,
                Measurement.ADMITTED_PEOPLE: admitted
            },
            "CLM": {
                Measurement.PCRS: pcrs
            }
        })

    def test_given_element_without_pcrs24h_when_delete_pcrs24h_then_same_element_returned(self):

        element = {
            "Madrid": {
                Measurement.PCRS: 1,
                Measurement.DEATHS: 2,
                Measurement.ICU_PEOPLE: 3,
                Measurement.ADMITTED_PEOPLE: 4
            },
            "CLM": {
                Measurement.PCRS: 5,
            }
        }

        expected_element = dict(element)

        self.assertEqual(delete_pcrs24h(element), expected_element)

    def test_when_get_header_then_monday_and_sunday_included(self):
        date = datetime(2020, 7, 27)

        header = get_date_header(date)

        self.assertEqual("Sem. 27/07 al 02/08", header)

    def test_when_get_final_tweet_then_monday_and_sunday_included_is_correct(self):
        summary = get_final_tweet()

        self.assertTrue("Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1&var-group_by=1w,4d"
                        in summary)
