from enum import Enum
import os
from datetime import timedelta
from collections import defaultdict
from influxdb import InfluxDBClient


class Measurement(Enum):
    PCRS = "pcrs"
    DEATHS = "deaths"
    PCRS_LAST_24H = "pcrs_last_24h"
    ICU_PEOPLE = "icu_people"
    ADMITTED_PEOPLE = "admitted_people"
    ACCUMULATED_INCIDENCE = "accumulated_incidence"
    PERCENTAGE_ADMITTED = "percentage_admitted"
    PERCENTAGE_ICU = "percentage_icu"
    VACCINATIONS = "vaccinations"
    COMPLETED_VACCINATIONS = "completed_vaccinations"
    FIRST_DOSE_VACCINATIONS = "first_dose_vaccinations"
    EXTRA_DOSE_VACCINATIONS = "extra_dose_vaccinations"
    PERCENTAGE_FIRST_DOSE = "percentage_first_dose"
    PERCENTAGE_COMPLETED_VACCINATION = "percentage_completed_vaccination"
    PERCENTAGE_EXTRA_DOSE = "percentage_extra_dose"


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

    def insert_stats(self, measurement: Measurement, date, data):
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

    def get_stat_group_by_week(self, measurement: Measurement, week_day):
        week_monday = week_day + timedelta(0 - week_day.weekday())
        week_sunday = week_day + timedelta(6 - week_day.weekday())
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time >= '{week_monday.strftime(self.DATE_FORMAT)}' and " \
                f"time <= '{week_sunday.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def get_stat_group_by_day(self, measurement: Measurement, day):
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time = '{day.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def get_stat_accumulated_until_day(self, measurement: Measurement, day):
        query = f"SELECT sum(value) FROM {measurement.value} where " \
                f"time <= '{day.strftime(self.DATE_FORMAT)}' group by ccaa;"
        return self._get_report(query)

    def get_last_value_from_week(self, mesaurement: Measurement, day):
        monday = day + timedelta(0 - day.weekday())
        sunday = day + timedelta(6 - day.weekday())

        query = f"SELECT * FROM {mesaurement.value} where " \
                f"time >= '{monday.strftime(self.DATE_FORMAT)} 00:00:00' and " \
                f"time <= '{sunday.strftime(self.DATE_FORMAT)} 23:59:59' " \
                f"group by ccaa order by desc limit 1"

        return self._get_report(query, "value")

    def _get_report(self, query, key="sum"):
        query_result = self.client.query(query)
        ccaa_map = {}

        for item in query_result.items():
            for values in item[1]:
                ccaa_map[item[0][1]["ccaa"]] = values[key]

        return ccaa_map

    def get_all_stats_group_by_week(self, day):
        pcrs = self.get_stat_group_by_week(Measurement.PCRS, day)
        deaths = self.get_stat_group_by_week(Measurement.DEATHS, day)
        pcrs_last_24h = self.get_stat_group_by_week(Measurement.PCRS_LAST_24H, day)
        admitted = self.get_stat_group_by_week(Measurement.ADMITTED_PEOPLE, day)
        icu = self.get_stat_group_by_week(Measurement.ICU_PEOPLE, day)
        accumulated_incidence = self.get_last_value_from_week(Measurement.ACCUMULATED_INCIDENCE, day)
        percentage_admitted = self.get_last_value_from_week(Measurement.PERCENTAGE_ADMITTED, day)
        percentage_icu = self.get_last_value_from_week(Measurement.PERCENTAGE_ICU, day)
        vaccinations = self.get_stat_group_by_week(Measurement.VACCINATIONS, day)
        completed_vaccinations = self.get_stat_group_by_week(Measurement.COMPLETED_VACCINATIONS, day)

        return self._pack_elements(**{
            Measurement.PCRS.value: pcrs,
            Measurement.DEATHS.value: deaths,
            Measurement.PCRS_LAST_24H.value: pcrs_last_24h,
            Measurement.ADMITTED_PEOPLE.value: admitted,
            Measurement.ICU_PEOPLE.value: icu,
            Measurement.ACCUMULATED_INCIDENCE.value: accumulated_incidence,
            Measurement.PERCENTAGE_ICU.value: percentage_icu,
            Measurement.PERCENTAGE_ADMITTED.value: percentage_admitted,
            Measurement.VACCINATIONS.value: vaccinations,
            Measurement.COMPLETED_VACCINATIONS.value: completed_vaccinations
        })

    def get_all_stats_group_by_day(self, day):
        pcrs = self.get_stat_group_by_day(Measurement.PCRS, day)
        deaths = self.get_stat_group_by_day(Measurement.DEATHS, day)
        pcrs_last_24h = self.get_stat_group_by_day(Measurement.PCRS_LAST_24H, day)
        admitted = self.get_stat_group_by_day(Measurement.ADMITTED_PEOPLE, day)
        icu = self.get_stat_group_by_day(Measurement.ICU_PEOPLE, day)
        accumulated_incidence = self.get_stat_group_by_day(Measurement.ACCUMULATED_INCIDENCE, day)
        percentage_admitted = self.get_stat_group_by_day(Measurement.PERCENTAGE_ADMITTED, day)
        percentage_icu = self.get_stat_group_by_day(Measurement.PERCENTAGE_ICU, day)
        vaccinations = self.get_stat_group_by_day(Measurement.VACCINATIONS, day)
        completed_vaccinations = self.get_stat_group_by_day(Measurement.COMPLETED_VACCINATIONS, day)

        return self._pack_elements(**{
            Measurement.PCRS.value: pcrs,
            Measurement.DEATHS.value: deaths,
            Measurement.PCRS_LAST_24H.value: pcrs_last_24h,
            Measurement.ADMITTED_PEOPLE.value: admitted,
            Measurement.ICU_PEOPLE.value: icu,
            Measurement.ACCUMULATED_INCIDENCE.value: accumulated_incidence,
            Measurement.PERCENTAGE_ADMITTED.value: percentage_admitted,
            Measurement.PERCENTAGE_ICU.value: percentage_icu,
            Measurement.VACCINATIONS.value: vaccinations,
            Measurement.COMPLETED_VACCINATIONS.value: completed_vaccinations
        })

    def get_all_stats_accumulated_until_day(self, day):
        pcrs = self.get_stat_accumulated_until_day(Measurement.PCRS, day)
        deaths = self.get_stat_accumulated_until_day(Measurement.DEATHS, day)
        vaccinations = self.get_stat_accumulated_until_day(Measurement.VACCINATIONS, day)
        completed_vaccinations = self.get_stat_accumulated_until_day(Measurement.COMPLETED_VACCINATIONS, day)

        return self._pack_elements(**{
            Measurement.PCRS.value: pcrs,
            Measurement.DEATHS.value: deaths,
            Measurement.VACCINATIONS.value: vaccinations,
            Measurement.COMPLETED_VACCINATIONS.value: completed_vaccinations
        })

    @staticmethod
    def _pack_elements(*_, **kwargs):

        keys = set([key for arg in kwargs for key in kwargs[arg].keys()])

        result = defaultdict(lambda: dict())
        for key in keys:
            for measurement in kwargs:
                result[key][Measurement(measurement)] = kwargs[measurement].get(key, None)

        return result
