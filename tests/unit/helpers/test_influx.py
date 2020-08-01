from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock, call
from helpers.influx import Influx, Measurement


class InfluxUnitTest(unittest.TestCase):

    @patch("helpers.influx.InfluxDBClient")
    @patch("helpers.influx.os")
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

            self._influx.insert_stats_in_influx(stats, date, data)

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
        influx.get_stat_group_by_day = MagicMock()
        date = MagicMock()

        result = influx.get_all_stats_group_by_day(date)

        get_stat_group_by_day_result = influx.get_stat_group_by_day.return_value
        self.assertEqual((get_stat_group_by_day_result, get_stat_group_by_day_result,
                          get_stat_group_by_day_result), result)

        influx.get_stat_group_by_day.assert_has_calls([call(Measurement.PCRS, date), call(Measurement.DEATHS, date),
                                                       call(Measurement.PCRS_LAST_24H, date)])

    def test_when_get_all_stats_accumulated_until_day_then_two_value_returned(self):
        influx = Influx()
        influx.get_stat_accumulated_until_day = MagicMock()
        date = MagicMock()

        result = influx.get_all_stats_accumulated_until_day(date)

        get_stat_accumulated_until_day_result = influx.get_stat_accumulated_until_day.return_value
        self.assertEqual((get_stat_accumulated_until_day_result, get_stat_accumulated_until_day_result), result)

        influx.get_stat_accumulated_until_day.assert_has_calls([call(Measurement.PCRS, date),
                                                                call(Measurement.DEATHS, date)])
