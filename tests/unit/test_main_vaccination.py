import unittest
from datetime import datetime
from constants import VACCINE_IMAGE_PATH
from unittest.mock import patch, MagicMock, call, ANY
from main_vaccination import main, Measurement, HTTPError, update_vaccinations, publish_report, get_column_index, \
    update_percentage
from helpers.spain_geography import CCAA_POPULATION


class MainVaccinationUnitTest(unittest.TestCase):

    @patch("main_vaccination.update_percentage")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_data_when_main_then_update_and_publish_not_called(self, influx_mock, datetime_mock,
                                                                     publish_report_mock,
                                                                     update_vaccinations_mock,
                                                                     update_percentage_mock):

        influx_mock.get_stat_group_by_day.return_value = {"Madrid": 1}

        main()

        update_vaccinations_mock.assert_not_called()
        publish_report_mock.assert_not_called()
        update_percentage_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.update_percentage")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_when_main_then_update_and_publish_called(self, influx_mock, datetime_mock,
                                                                    publish_report_mock,
                                                                    update_vaccinations_mock,
                                                                    update_percentage_mock):

        influx_mock.get_stat_group_by_day.return_value = {}
        today = datetime_mock.now.return_value

        main()

        update_vaccinations_mock.assert_called_once_with(today)
        publish_report_mock.assert_called_once_with(today)
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  today)
        update_percentage_mock.assert_has_calls([call(today, Measurement.COMPLETED_VACCINATIONS,
                                                      Measurement.PERCENTAGE_COMPLETED_VACCINATION),
                                                 call(today, Measurement.FIRST_DOSE_VACCINATIONS,
                                                      Measurement.PERCENTAGE_FIRST_DOSE),
                                                 call(today, Measurement.EXTRA_DOSE_VACCINATIONS,
                                                      Measurement.PERCENTAGE_EXTRA_DOSE)])

    @patch("main_vaccination.update_percentage")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_http_error_when_main_then_no_exception_raised(self, influx_mock, datetime_mock,
                                                                             publish_report_mock,
                                                                             update_vaccinations_mock,
                                                                             update_percentage_mock):

        update_vaccinations_mock.side_effect = HTTPError("http://google.com", 404, MagicMock(), MagicMock(), MagicMock())
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        update_percentage_mock.assert_not_called()
        datetime_mock.now.assert_called_once_with()
        influx_mock.get_stat_group_by_day.assert_called_once_with(Measurement.VACCINATIONS,
                                                                  datetime_mock.now.return_value)

    @patch("main_vaccination.update_percentage")
    @patch("main_vaccination.twitter")
    @patch("main_vaccination.update_vaccinations")
    @patch("main_vaccination.publish_report")
    @patch("main_vaccination.datetime")
    @patch("main_vaccination.influx")
    def test_given_no_data_and_another_error_when_main_then_twitter_dm_sent(self, influx_mock, datetime_mock,
                                                                            publish_report_mock,
                                                                            update_vaccinations_mock,
                                                                            twitter_mock, update_percentage_mock):

        exception_text = "exception text"
        update_vaccinations_mock.side_effect = Exception(exception_text * 100)
        influx_mock.get_stat_group_by_day.return_value = {}

        main()

        update_vaccinations_mock.assert_called_once_with(datetime_mock.now.return_value)
        publish_report_mock.assert_not_called()
        update_percentage_mock.assert_not_called()
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
        extra_dose = MagicMock()
        vaccines_ministry_report_mock.return_value.get_column_data.side_effect = [vaccinations, first_dose,
                                                                                  completed_vaccinations, extra_dose]

        doses_column = MagicMock()
        first_dose_column = MagicMock()
        completed_column = MagicMock()
        extra_column = MagicMock()

        get_column_index_mock.side_effect = [doses_column, first_dose_column, completed_column, extra_column]

        update_vaccinations(today)

        vaccines_ministry_report_mock.assert_called_once_with(today, 1)
        vaccines_ministry_report_mock.return_value.get_column_data.assert_has_calls([call(doses_column, num_rows=21),
                                                                                     call(first_dose_column, num_rows=21),
                                                                                     call(completed_column, num_rows=21),
                                                                                     call(extra_column, num_rows=21)])
        update_stat_mock.assert_has_calls([call(Measurement.VACCINATIONS,
                                                vaccinations,
                                                today),
                                           call(Measurement.COMPLETED_VACCINATIONS,
                                                completed_vaccinations,
                                                today),
                                           call(Measurement.FIRST_DOSE_VACCINATIONS,
                                                first_dose,
                                                today),
                                           call(Measurement.EXTRA_DOSE_VACCINATIONS,
                                                extra_dose,
                                                today)
                                           ])

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
        extra_doses = MagicMock()
        completed_vaccinations = MagicMock()
        first_doses = MagicMock()
        accumulated_extra_doses = MagicMock()
        accumulated_completed_vaccinations = MagicMock()
        accumulated_first_doses = {"Madrid": 123, "Aragón": 456}
        influx_mock.get_stat_group_by_day.side_effect = [completed_vaccinations, first_doses, extra_doses]
        influx_mock.get_stat_accumulated_until_day.side_effect = [accumulated_completed_vaccinations,
                                                                  accumulated_first_doses,
                                                                  accumulated_extra_doses]
        spain_sentence = "spain_doses_and_completed"
        ccaa1_sentence = "ccaa1_sentence"
        ccaa2_sentence = "ccaa2_sentence"
        get_vaccination_report_mock.side_effect = [spain_sentence, ccaa1_sentence, ccaa2_sentence]
        last_tweet = MagicMock()
        first_tweet = MagicMock()
        twitter_mock.publish_sentences_in_tweets.return_value = last_tweet
        twitter_mock.publish_tweet_with_media.return_value = first_tweet

        publish_report(today)

        influx_mock.get_stat_group_by_day.assert_has_calls([call(Measurement.COMPLETED_VACCINATIONS, today),
                                                            call(Measurement.FIRST_DOSE_VACCINATIONS, today),
                                                            call(Measurement.EXTRA_DOSE_VACCINATIONS, today)])
        influx_mock.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.COMPLETED_VACCINATIONS, today),
                                                                     call(Measurement.FIRST_DOSE_VACCINATIONS, today),
                                                                     call(Measurement.EXTRA_DOSE_VACCINATIONS, today)])
        twitter_mock.publish_tweets.assert_called_once_with([f"Aragón - Vacunación a {date_str}:\n\n{ccaa1_sentence}",
                                                             f"Madrid - Vacunación a {date_str}:\n\n{ccaa2_sentence}"],
                                                            twitter_mock.publish_tweet_with_media.return_value)
        get_graph_url_mock.assert_called_once_with(datetime(2021, 1, 1), today, graph_path=VACCINE_IMAGE_PATH)
        get_vaccination_report_mock.assert_has_calls([call("España", accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses, accumulated_extra_doses, extra_doses),
                                                      call("Aragón", accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses, accumulated_extra_doses, extra_doses),
                                                      call("Madrid", accumulated_completed_vaccinations,
                                                           completed_vaccinations, accumulated_first_doses,
                                                           first_doses, accumulated_extra_doses, extra_doses)])
        twitter_mock.publish_tweet_with_media.assert_called_once_with(f"🇪🇸 España - Vacunación a {date_str}:"
                                                                      f"\n\n{spain_sentence}\n\n➡️ Gráfico "
                                                                      f"Interactivo: https://home.aitormagan.es/d/TeEplNgRk/covid-vacunas-espana?orgId=1",
                                                                      get_graph_url_mock.return_value)
        today.strftime.assert_called_once_with("%d/%m/%Y")

    @patch("main_vaccination.influx")
    def test_given_no_info_when_update_percentage_then_influx_called_with_empty_dict(self, influx_mock):
        influx_mock.get_stat_accumulated_until_day.return_value = {}
        date = MagicMock()
        base_table = MagicMock()
        final_table = MagicMock()

        update_percentage(date, base_table, final_table)

        influx_mock.get_stat_accumulated_until_day.assert_called_once_with(base_table, date)
        influx_mock.insert_stats.assert_called_once_with(final_table, date, {})

    @patch("main_vaccination.influx")
    def test_given_info_when_update_percentage_then_influx_called_with_returned_regions(self, influx_mock):
        region = "Castilla La Mancha"
        region_population = CCAA_POPULATION[region]
        half_population = int(region_population / 2)
        expected_percentage = 100 * half_population / region_population
        influx_mock.get_stat_accumulated_until_day.return_value = {region: half_population}
        date = MagicMock()
        base_table = MagicMock()
        final_table = MagicMock()

        update_percentage(date, base_table, final_table)

        influx_mock.get_stat_accumulated_until_day.assert_called_once_with(base_table, date)
        influx_mock.insert_stats.assert_called_once_with(final_table, date, {region: expected_percentage})

    @patch("main_vaccination.influx")
    def test_given_spain_info_when_update_percentage_then_influx_called_with_sum_spain_population(self, influx_mock):
        spain_population = sum(CCAA_POPULATION.values())
        half_population = int(spain_population / 2)
        expected_percentage = 100 * half_population / spain_population
        influx_mock.get_stat_accumulated_until_day.return_value = {"España": half_population}
        date = MagicMock()
        base_table = MagicMock()
        final_table = MagicMock()

        update_percentage(date, base_table, final_table)

        influx_mock.get_stat_accumulated_until_day.assert_called_once_with(base_table, date)
        influx_mock.insert_stats.assert_called_once_with(final_table, date, {"España": expected_percentage})
