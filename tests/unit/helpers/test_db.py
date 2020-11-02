from datetime import datetime
from collections import defaultdict
import unittest
from unittest.mock import patch, MagicMock, call
from helpers.db import Influx, Measurement


class InfluxUnitTest(unittest.TestCase):

    @patch("helpers.db.InfluxDBClient")
    @patch("helpers.db.os")
    def test_given_no_client_defined_when_access_client_then_client_is_built(self, os_mock, influxdbclient_mock):
        influx = Influx()

        client = influx.client

        self.assertEqual(influxdbclient_mock.return_value, client)
        influxdbclient_mock.assert_called_once_with(os_mock.environ.get.return_value, 8086, None, None, "covid19")
        os_mock.environ.get.assert_called_once_with("INFLUX_HOST", "localhost")

    def test_given_ccaas_when_insert_stats_in_influx_then_points_written(self):
        stats = Measurement.PCRS
        data = {'Madrid': 2, 'Cataluña': 3}
        date = datetime(2020, 8, 1)

        expected_calls = list(map(lambda x: {
                "measurement": stats.value,
                "time": date.date().isoformat(),
                "tags": {
                    "ccaa": x
                },
                "fields": {
                    "value": data[x]
                }
            }, data.keys()))

        with patch.object(Influx, 'client'):
            self._influx = Influx()
            self._influx.client = MagicMock()

            self._influx.insert_stats(stats, date, data)

            self._influx.client.write_points.assert_called_once_with(expected_calls)

    def test_given_day_when_get_stat_group_by_week_then_get_report_called(self):
        influx = Influx()
        influx._get_report = MagicMock()
        date = datetime(2020, 8, 1)
        stat = Measurement.PCRS

        result = influx.get_stat_group_by_week(stat, date)

        self.assertEqual(result, influx._get_report.return_value)
        influx._get_report.assert_called_once_with(
            f"SELECT sum(value) FROM pcrs where time >= '2020-07-27' and time <= '2020-08-02' group by ccaa;")

    def test_given_day_when_get_stat_group_by_day_then_get_report_called(self):
        influx = Influx()
        influx._get_report = MagicMock()
        date = datetime(2020, 8, 1)
        stat = Measurement.PCRS

        result = influx.get_stat_group_by_day(stat, date)

        self.assertEqual(result, influx._get_report.return_value)
        influx._get_report.assert_called_once_with(
            f"SELECT sum(value) FROM pcrs where time = '2020-08-01' group by ccaa;")

    def test_given_day_when_get_stat_accumulated_until_day_then_get_report_called(self):
        influx = Influx()
        influx._get_report = MagicMock()
        date = datetime(2020, 8, 1)
        stat = Measurement.PCRS

        result = influx.get_stat_accumulated_until_day(stat, date)

        self.assertEqual(result, influx._get_report.return_value)
        influx._get_report.assert_called_once_with(
            f"SELECT sum(value) FROM pcrs where time <= '2020-08-01' group by ccaa;")

    def test_given_database_info_when_get_report_then_map_returned(self):
        with patch.object(Influx, 'client'):
            self._influx = Influx()
            self._influx.client = MagicMock()
            query = MagicMock()
            self._influx.client.query.return_value.items.return_value = [(('pcrs', {'ccaa': 'Madrid'}), [{'sum': 7}]),
                                                                         (('pcrs', {'ccaa': 'Cataluña'}), [{'sum': 9}])]

            result = self._influx._get_report(query)

            self.assertEqual(result, {"Madrid": 7, "Cataluña": 9})
            self._influx.client.query.assert_called_once_with(query)

    def test_when_get_all_stats_group_by_day_then_three_value_returned(self):
        influx = Influx()
        influx._pack_elements = MagicMock()
        influx.get_stat_group_by_day = MagicMock()
        date = MagicMock()

        result = influx.get_all_stats_group_by_day(date)

        self.assertEqual(influx._pack_elements.return_value, result)

        influx.get_stat_group_by_day.assert_has_calls([call(Measurement.PCRS, date),
                                                       call(Measurement.DEATHS, date),
                                                       call(Measurement.PCRS_LAST_24H, date),
                                                       call(Measurement.ADMITTED_PEOPLE, date),
                                                       call(Measurement.ICU_PEOPLE, date),
                                                       call(Measurement.ACCUMULATED_INCIDENCE, date)])

    def test_when_get_all_stats_group_by_week_then_three_value_returned(self):
        influx = Influx()
        influx._pack_elements = MagicMock()
        influx.get_stat_group_by_week = MagicMock()
        influx.get_stat_group_by_day = MagicMock()
        date = datetime(2020, 10, 11)

        result = influx.get_all_stats_group_by_week(date)

        self.assertEqual(influx._pack_elements.return_value, result)

        influx.get_stat_group_by_week.assert_has_calls([call(Measurement.PCRS, date),
                                                        call(Measurement.DEATHS, date),
                                                        call(Measurement.PCRS_LAST_24H, date),
                                                        call(Measurement.ADMITTED_PEOPLE, date),
                                                        call(Measurement.ICU_PEOPLE, date)])
        influx.get_stat_group_by_day.assert_has_calls([call(Measurement.ACCUMULATED_INCIDENCE, datetime(2020, 10, 9)),
                                                       call(Measurement.PERCENTAGE_ADMITTED, datetime(2020, 10, 9)),
                                                       call(Measurement.PERCENTAGE_ICU, datetime(2020, 10, 9))])

    def test_when_get_all_stats_accumulated_until_day_then_two_value_returned(self):
        influx = Influx()
        influx._pack_elements = MagicMock()
        influx.get_stat_accumulated_until_day = MagicMock()
        date = MagicMock()

        result = influx.get_all_stats_accumulated_until_day(date)

        self.assertEqual(influx._pack_elements.return_value, result)

        influx.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.PCRS, date),
                                                                call(Measurement.DEATHS, date)])

    def test_given_no_args_when_pack_elements_then_empty_dict_returned(self):

        self.assertEqual(defaultdict(), Influx._pack_elements(**{}))

    def test_given_one_arg_when_pack_elements_then_dict_reversed(self):

        ccaa1 = 'Andalucia'
        ccaa2 = 'Castilla-La Mancha'
        ccaa1_value = 1
        ccaa2_value = 2

        arguments = {
            Measurement.PCRS.value: {ccaa1: ccaa1_value, ccaa2: ccaa2_value}
        }

        expected_result = {
            ccaa1: {
                Measurement.PCRS: ccaa1_value
            },
            ccaa2: {
                Measurement.PCRS: ccaa2_value
            }
        }

        self.assertEqual(expected_result, Influx._pack_elements(**arguments))

    def test_given_two_arg_when_pack_elements_then_dict_packed(self):

        ccaa1 = 'Andalucia'
        ccaa2 = 'Castilla-La Mancha'
        ccaa1_value = 1
        ccaa2_value = 2
        ccaa1_value_deaths = 4
        ccaa2_value_deaths = 3

        arguments = {
            Measurement.PCRS.value: {ccaa1: ccaa1_value, ccaa2: ccaa2_value},
            Measurement.DEATHS.value: {ccaa1: ccaa1_value_deaths, ccaa2: ccaa2_value_deaths}
        }

        expected_result = {
            ccaa1: {
                Measurement.PCRS: ccaa1_value,
                Measurement.DEATHS: ccaa1_value_deaths
            },
            ccaa2: {
                Measurement.PCRS: ccaa2_value,
                Measurement.DEATHS: ccaa2_value_deaths
            }
        }

        self.assertEqual(expected_result, Influx._pack_elements(**arguments))
