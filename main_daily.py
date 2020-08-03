import sys
import logging
from datetime import datetime, timedelta
from urllib.error import HTTPError
from helpers.twitter import Twitter
from helpers.influx import Influx, Measurement
from helpers.ministry_report import SpainCovid19MinistryReport
from helpers.reports import get_report_by_ccaa, get_human_summary
from constants import DATE_FORMAT


twitter = Twitter()
influx = Influx()


def main():

    today = datetime.now()
    yesterday = subtract_days_ignoring_weekends(today, 1)

    data = influx.get_stat_group_by_day(Measurement.PCRS, today)

    if not data:
        try:
            update_database(today, yesterday)
            publish_report(today, yesterday)

        except HTTPError:
            logging.info("PDF is not availble yet...")
        except Exception:
            logging.exception("Unhandled exception while trying to publish tweets")
            twitter.send_dm_error()


def subtract_days_ignoring_weekends(initial_date, days_to_substract):
    result = initial_date

    while days_to_substract > 0:
        result = result - timedelta(days=1)

        if result.weekday() < 5:
            days_to_substract -= 1

    return result


def update_database(today, yesterday):
    pcrs_report = SpainCovid19MinistryReport(today, 1, (239, 56, 239 + 283, 56 + 756))
    deaths_report = SpainCovid19MinistryReport(today, 2)

    accumulated_pcrs_today = pcrs_report.get_column_data(1)
    accumulated_deaths_today = deaths_report.get_column_data(3)

    accumulated_pcrs_yesterday = influx.get_stat_accumulated_until_day(Measurement.PCRS, yesterday)
    accumulated_deaths_yesterday = influx.get_stat_accumulated_until_day(Measurement.DEATHS, yesterday)

    today_pcrs = get_today_numbers(accumulated_pcrs_today, accumulated_pcrs_yesterday)
    today_deaths = get_today_numbers(accumulated_deaths_today, accumulated_deaths_yesterday)
    today_pcrs_last_24h = pcrs_report.get_column_data(2)

    influx.insert_stats_in_influx(Measurement.PCRS, today, today_pcrs)
    influx.insert_stats_in_influx(Measurement.DEATHS, today, today_deaths)
    influx.insert_stats_in_influx(Measurement.PCRS_LAST_24H, today, today_pcrs_last_24h)

    return today_pcrs, today_deaths, today_pcrs_last_24h


def get_today_numbers(today_accumulated, yesterday_accumulated):
    today_new = {}
    for ccaa in today_accumulated:
        today_new[ccaa] = today_accumulated[ccaa] - yesterday_accumulated.get(ccaa, 0)

    return today_new


def publish_report(today, yesterday):
    today_pcrs, today_deaths, _ = influx.get_all_stats_group_by_day(today)
    yesterday_pcrs, yesterday_deaths, _ = influx.get_all_stats_group_by_day(yesterday)

    pcrs_report = get_report_by_ccaa(today_pcrs, yesterday_pcrs)
    deaths_report = get_report_by_ccaa(today_deaths, yesterday_deaths)

    twitter.publish_tweets(pcrs_report, get_header("PCR+", today))
    twitter.publish_tweets(deaths_report, get_header("Muertes", today))

    today_pcrs_accumulated, today_deaths_accumulated = influx.get_all_stats_accumulated_until_day(today)
    pcrs_summary = get_human_summary("PCR+", today_pcrs, yesterday_pcrs, today_pcrs_accumulated)
    deaths_summary = get_human_summary("Muertes", today_deaths, yesterday_deaths, today_deaths_accumulated)
    twitter.publish_tweets([get_summary_tweet(today, pcrs_summary, deaths_summary)])

    logging.info("Tweets published correctly!")


def get_header(stat_type, date):
    return "{0} reportadas el{1}{2}".format(stat_type, " fin de semana del " if date.weekday() == 0 else " ",
                                            (date - timedelta(1)).strftime(DATE_FORMAT))


def get_summary_tweet(date, pcrs_summary, deaths_summary):
    items = ["Resumen España al finalizar el {0}:".format((date - timedelta(1)).strftime(DATE_FORMAT)), "",
             pcrs_summary, deaths_summary, "", "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1",
             "Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1"]

    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
