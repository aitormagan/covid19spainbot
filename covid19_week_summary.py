from datetime import timedelta, datetime
from influxdb import InfluxDBClient
from covid19_cases_reporter import CCAA_REVERSE, publish_tweets_for_stat, get_summary, DATE_FORMAT, publish_tweets
import os

client = InfluxDBClient(os.environ.get("INFLUX_HOST", "localhost"), 8086, None, None, 'covid19')


def get_week_report(measurement, week_day):
    week_sunday = week_day + timedelta(6 - week_day.weekday())
    DATE_FORMAT = "%Y-%m-%d"

    query_result = client.query(f"SELECT sum(value) FROM {measurement} where time <='{week_sunday.strftime(DATE_FORMAT)}' group by ccaa;")
    ccaa_map = {}

    for item in query_result.items():
        for values in item[1]:
            ccaa_map[CCAA_REVERSE[item[0][1]['ccaa']]] = values["sum"]

    return ccaa_map


def get_week_summary_tweet(date, pcrs_summary, deaths_summary):
    monday = date + timedelta(0 - date.weekday())
    sunday = date + timedelta(6 - date.weekday())
    items = ["Resumen España la semana del {0} al {1}:".format(monday.strftime(DATE_FORMAT), sunday.strftime(DATE_FORMAT)), "", pcrs_summary, deaths_summary, "", "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1&var-group_by=1w,4d"]
    return "\n".join(list(filter(lambda x: x is not None, items)))


def main():
    pcrs_current_week = get_week_report("pcrs", datetime.today())
    pcrs_previous_week = get_week_report("pcrs", datetime.today() - timedelta(7))
    pcrs_two_weeks_ago = get_week_report("pcrs", datetime.today() - timedelta(14))
    deaths_current_week = get_week_report("deaths", datetime.today())
    deaths_previous_week = get_week_report("deaths", datetime.today() - timedelta(7))
    deaths_two_weeks_ago = get_week_report("deaths", datetime.today() - timedelta(14))

    publish_tweets_for_stat("PCR+", datetime.today(), pcrs_current_week, pcrs_previous_week, pcrs_two_weeks_ago)
    publish_tweets_for_stat("Muertes", datetime.today(), deaths_current_week, deaths_previous_week, deaths_two_weeks_ago)

    pcrs_summary = get_summary("PCR+", pcrs_current_week, pcrs_previous_week, pcrs_two_weeks_ago)
    deaths_summary = get_summary("Muertes", deaths_current_week, deaths_previous_week, deaths_two_weeks_ago)

    publish_tweets([get_week_summary_tweet(datetime.today(), pcrs_summary, deaths_summary)])


if __name__ == '__main__':
    main()