import unittest
from unittest.mock import patch, MagicMock, call, ANY
from main_vaccination import main, Measurement, HTTPError, update_vaccinations, publish_report


class MainDailyUnitTest(unittest.TestCase):

    @patch("main_vaccination.subtract_days_ignoring_weekends")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_data_when_main_then_update_and_publish_not_called(self, influx_mock, datetime_mock,
                                                                     publish_report_mock,
                                                                     update_vaccinations_mock,
                                                                     subtract_days_ignoring_weekends_mock):

        influx_mock.get_stat_group_by_day.return_value = {"Madrid": 1}

        main()

        update_vaccinations_mock.assert_not_called()
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.subtract_days_ignoring_weekends")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_when_main_then_update_and_publish_called(self, influx_mock, datetime_mock,
                                                                    publish_report_mock,
                                                                    update_vaccinations_mock,
                                                                    subtract_days_ignoring_weekends_mock):

        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_called_once_with(datetime_mock.now.return_value,
                                                    subtract_days_ignoring_weekends_mock.return_value)
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.subtract_days_ignoring_weekends")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_http_error_when_main_then_no_exception_raised(self, influx_mock, datetime_mock,
                                                                             publish_report_mock,
                                                                             update_vaccinations_mock,
                                                                             subtract_days_ignoring_weekends_mock):

        update_vaccinations_mock.side_effect = HTTPError("http://google.com", 404, MagicMock(), MagicMock(), MagicMock())
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.twitter")
    @patch("main_vaccination.subtract_days_ignoring_weekends")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_another_error_when_main_then_twitter_dm_sent(self, influx_mock, datetime_mock,
                                                                            publish_report_mock,
                                                                            update_vaccinations_mock,
                                                                            subtract_days_ignoring_weekends_mock,
                                                                            twitter_mock):

        exception_text = "exception text"
        update_vaccinations_mock.side_effect = Exception(exception_text * 100)
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        subtract_days_ignoring_weekends_mock.assert_called_once_with(datetime_mock.now.return_value, 1)
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)
        twitter_mock.send_dm.assert_called_once_with(ANY)
        dm_text = twitter_mock.send_dm.call_args[0][0]
        self.assertEqual(280, len(dm_text))
        self.assertTrue(dm_text.startswith(f"There was an unhandled exception. Trace:\n\n{exception_text}"))

    @patch("main_vaccination.VaccinesMinistryReport")
    @patch("main_vaccination.update_stat")
    def test_when_update_vaccinations_then_report_checked_and_database_updated(self, update_stat_mock,
                                                                               vaccines_ministry_report_mock):

        today = MagicMock()

        update_vaccinations(today)

        vaccines_ministry_report_mock.assert_called_once_with(today, 3)
        vaccines_ministry_report_mock.return_value.get_column_data.assert_called_once_with(4)
        update_stat_mock.assert_called_once_with(Measurement.VACCINATIONS,
                                                 vaccines_ministry_report_mock.return_value.get_column_data.return_value,
                                                 today)

    @patch("main_vaccination.influx")
    @patch("main_vaccination.twitter")
    @patch("main_vaccination.get_vaccination_report")
    def test_when_publish_report_then_twitter_called(self, get_vaccination_report_mock,
                                                     twitter_mock, influx_mock):

        date_str = "04/05/2006"
        today = MagicMock()
        today.strftime.return_value = date_str

        publish_report(today, MagicMock())

        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS, today)
        influx_mock.get_stat_accumulated_until_day.assert_called_once_with(Measurement.VACCINATIONS, today)
        get_vaccination_report_mock.assert_called_once_with(influx_mock.get_stat_accumulated_until_day.return_value,
                                                            influx_mock.get_stat_group_by_day.return_value)
        twitter_mock.publish_sentences_in_tweets.assert_called_once_with(get_vaccination_report_mock.return_value,
                                                                         f"💉 Total Vacunados a {date_str}")
        today.strftime.assert_called_once_with("%d/%m/%Y")
