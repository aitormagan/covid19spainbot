from enum import Enum
import os
from datetime import timedelta
from influxdb import InfluxDBClient


class Measurement(Enum):
    PCRS = "pcrs"
    DEATHS = "deaths"
    PCRS_LAST_24H = "pcrs_last_24h"


class Influx:
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            host = os.environ.get("INFLUX_HOST", "localhost")
            self._client = InfluxDBClient(host, 8086, None, None, "covid19")

        return self._client

    def insert_stats_in_influx(self, measurement: Measurement, date, data):
        influx_data = []
        for ccaa in data:
            influx_data.append({
                "measurement": measurement.value,
                "time": date.date().isoformat(),
                "tags": {
                    "ccaa": ccaa
                },
                "fields": {
                    "value": data[ccaa]
                }
            })

        self.client.write_points(influx_data)

    def get_week_report(self, measurement: Measurement, week_day):
        week_monday = week_day + timedelta(0 - week_day.weekday())
        week_sunday = week_day + timedelta(6 - week_day.weekday())
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time >='{week_monday.strftime(self.DATE_FORMAT)}' and " \
                f"time <='{week_sunday.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def get_day_stat(self, measurement: Measurement, day):
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time ='{day.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def get_day_accumulated_stat(self, measurement: Measurement, day):
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time <='{day.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def _get_report(self, query):
        query_result = self.client.query(query)
        ccaa_map = {}

        for item in query_result.items():
            for values in item[1]:
                ccaa_map[item[0][1]["ccaa"]] = values["sum"]

        return ccaa_map

    def get_all_stats_by_day(self, day):
        pcrs = self.get_day_stat(Measurement.PCRS, day)
        deaths = self.get_day_stat(Measurement.DEATHS, day)
        pcrs_last_24h = self.get_day_stat(Measurement.PCRS_LAST_24H, day)

        return pcrs, deaths, pcrs_last_24h

    def get_all_stats_accumulated_by_day(self, day):
        pcrs = self.get_day_accumulated_stat(Measurement.PCRS, day)
        deaths = self.get_day_accumulated_stat(Measurement.DEATHS, day)

        return pcrs, deaths
