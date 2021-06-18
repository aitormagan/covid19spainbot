import unittest
from datetime import datetime
from constants import VACCINE_IMAGE_PATH
from unittest.mock import patch, MagicMock, call, ANY
from main_vaccination import main, Measurement, HTTPError, update_vaccinations, publish_report, get_column_index


class MainVaccinationUnitTest(unittest.TestCase):

    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_data_when_main_then_update_and_publish_not_called(self, influx_mock, datetime_mock,
                                                                     publish_report_mock,
                                                                     update_vaccinations_mock):

        influx_mock.get_stat_group_by_day.return_value = {"Madrid": 1}

        main()

        update_vaccinations_mock.assert_not_called()
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_when_main_then_update_and_publish_called(self, influx_mock, datetime_mock,
                                                                    publish_report_mock,
                                                                    update_vaccinations_mock):

        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_called_once_with(datetime_mock.now.return_value)
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_http_error_when_main_then_no_exception_raised(self, influx_mock, datetime_mock,
                                                                             publish_report_mock,
                                                                             update_vaccinations_mock):

        update_vaccinations_mock.side_effect = HTTPError("http://google.com", 404, MagicMock(), MagicMock(), MagicMock())
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.twitter")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_another_error_when_main_then_twitter_dm_sent(self, influx_mock, datetime_mock,
                                                                            publish_report_mock,
                                                                            update_vaccinations_mock,
                                                                            twitter_mock):

        exception_text = "exception text"
        update_vaccinations_mock.side_effect = Exception(exception_text * 100)
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)
        twitter_mock.send_dm.assert_called_once_with(ANY)
        dm_text = twitter_mock.send_dm.call_args[0][0]
        self.assertEqual(280, len(dm_text))
        self.assertTrue(dm_text.startswith(f"There was an unhandled exception. Trace:\n\n{exception_text}"))

    @patch("main_vaccination.get_column_index")
    @patch("main_vaccination.VaccinesMinistryReport")
    @patch("main_vaccination.update_stat")
    def test_when_update_vaccinations_then_report_checked_and_database_updated(self, update_stat_mock,
                                                                               vaccines_ministry_report_mock,
                                                                               get_column_index_mock):

        today = MagicMock()
        vaccinations = MagicMock()
        first_dose = MagicMock()
        completed_vaccinations = MagicMock()
        vaccines_ministry_report_mock.return_value.get_column_data.side_effect = [vaccinations, first_dose,
                                                                                  completed_vaccinations]

        doses_column = MagicMock()
        first_dose_column = MagicMock()
        completed_column = MagicMock()

        get_column_index_mock.side_effect = [doses_column, first_dose_column, completed_column]

        update_vaccinations(today)

        vaccines_ministry_report_mock.assert_called_once_with(today, 1)
        vaccines_ministry_report_mock.return_value.get_column_data.assert_has_calls([call(doses_column, num_rows=21),
                                                                                     call(first_dose_column, num_rows=21),
                                                                                     call(completed_column, num_rows=21)])
        update_stat_mock.assert_has_calls([call(Measurement.VACCINATIONS,
                                                vaccinations,
                                                today),
                                           call(Measurement.COMPLETED_VACCINATIONS,
                                                completed_vaccinations,
                                                today),
                                           call(Measurement.FIRST_DOSE_VACCINATIONS,
                                                first_dose,
                                                today)])

    def test_given_column_in_columns_when_get_column_index_then_position_returned(self):
        df = MagicMock()
        df.columns = ['Dosis Administradas', 'Pautas Completadas', '1 dosis']

        self.assertEqual(get_column_index(df, "completadas"), 1)

    def test_given_column_not_in_columns_when_get_column_index_then_exception_risen(self):
        df = MagicMock()
        df.columns = ['Dosis Administradas', 'Pautas Completadas', '1 dosis']

        with self.assertRaises(ValueError):
            get_column_index(df, "test")

    @patch("main_vaccination.influx")
    @patch("main_vaccination.twitter")
    @patch("main_vaccination.get_vaccination_report")
    @patch("main_vaccination.get_graph_url")
    def test_when_publish_report_then_twitter_called(self, get_graph_url_mock, get_vaccination_report_mock,
                                                     twitter_mock, influx_mock):

        date_str = "04/05/2006"
        today = MagicMock()
        today.strftime.return_value = date_str
        vaccinations = MagicMock()
        completed_vaccinations = MagicMock()
        first_doses = MagicMock()
        accumulated_vaccinations = {"Madrid": 123, "Aragón": 456}
        accumulated_completed_vaccinations = MagicMock()
        accumulated_first_doses = MagicMock()
        influx_mock.get_stat_group_by_day.side_effect = [vaccinations, completed_vaccinations, first_doses]
        influx_mock.get_stat_accumulated_until_day.side_effect = [accumulated_vaccinations,
                                                                  accumulated_completed_vaccinations,
                                                                  accumulated_first_doses]
        spain_sentence = "spain_doses_and_completed"
        ccaa1_sentence = "ccaa1_sentence"
        ccaa2_sentence = "ccaa2_sentence"
        get_vaccination_report_mock.side_effect = [spain_sentence, ccaa1_sentence, ccaa2_sentence]
        last_tweet = MagicMock()
        first_tweet = MagicMock()
        twitter_mock.publish_sentences_in_tweets.return_value = last_tweet
        twitter_mock.publish_tweet_with_media.return_value = first_tweet

        publish_report(today)

        influx_mock.get_stat_group_by_day.assert_has_calls([call(Measurement.VACCINATIONS, today),
                                                            call(Measurement.COMPLETED_VACCINATIONS, today)])
        influx_mock.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.VACCINATIONS, today),
                                                                     call(Measurement.COMPLETED_VACCINATIONS, today)])
        twitter_mock.publish_tweets.assert_called_once_with([f"Aragón - Vacunación a {date_str}:\n\n{ccaa1_sentence}",
                                                             f"Madrid - Vacunación a {date_str}:\n\n{ccaa2_sentence}"],
                                                            twitter_mock.publish_tweet_with_media.return_value)
        get_graph_url_mock.assert_called_once_with(datetime(2021, 1, 1), today, graph_path=VACCINE_IMAGE_PATH)
        get_vaccination_report_mock.assert_has_calls([call("España", accumulated_vaccinations, vaccinations,
                                                           accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses),
                                                      call("Aragón", accumulated_vaccinations, vaccinations,
                                                           accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses),
                                                      call("Madrid", accumulated_vaccinations, vaccinations,
                                                           accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses)])
        twitter_mock.publish_tweet_with_media.assert_called_once_with(f"🇪🇸 España - Vacunación a {date_str}:"
                                                                      f"\n\n{spain_sentence}\n\n➡️ Gráfico "
                                                                      f"Interactivo: https://home.aitormagan.es/d/TeEplNgRk/covid-vacunas-espana?orgId=1",
                                                                      get_graph_url_mock.return_value)
        today.strftime.assert_called_once_with("%d/%m/%Y")
