import sys
import logging
from datetime import datetime, timedelta
from urllib.error import HTTPError
from helpers.twitter import Twitter
from helpers.influx import Influx, Measurement
from helpers.ministry_report import SpainCovid19MinistryReport
from helpers.reports import get_report_by_ccaa, get_graph_url, get_ccaa_report
from constants import DATE_FORMAT

twitter = Twitter()
influx = Influx()


def main():

    today = datetime.now()
    yesterday = subtract_days_ignoring_weekends(today, 1)

    data = influx.get_stat_group_by_day(Measurement.PCRS, today)

    if data:
        try:
            # update_database(today)
            publish_report(today, yesterday)

        except HTTPError:
            logging.info("PDF is not availble yet...")
        except Exception as e:
            logging.exception("Unhandled exception while trying to publish tweets")
            dm_text = f"There was an unhandled exception. Trace:\n\n{str(e)}"[0:280]
            twitter.send_dm(dm_text)


def subtract_days_ignoring_weekends(initial_date, days_to_substract):
    result = initial_date

    while days_to_substract > 0:
        result = result - timedelta(days=1)

        if result.weekday() < 5:
            days_to_substract -= 1

    return result


def update_database(today):
    pcrs_report = SpainCovid19MinistryReport(today, 1)
    deaths_report = SpainCovid19MinistryReport(today, 2)

    try:
        accumulated_pcrs_today = pcrs_report.get_column_data(1)
    except Exception:
        # With some PDFs, tabula-pdf auto table detection fails.
        # We need to specify a custom area.
        pcrs_report = SpainCovid19MinistryReport(today, 1, (239, 56, 239 + 283, 56 + 756))
        accumulated_pcrs_today = pcrs_report.get_column_data(1)

    accumulated_admitted_today = deaths_report.get_column_data(1)
    accumulated_icu_today = deaths_report.get_column_data(2)
    accumulated_deaths_today = deaths_report.get_column_data(3)

    today_pcrs = update_stat(Measurement.PCRS, accumulated_pcrs_today, today)
    today_deaths = update_stat(Measurement.DEATHS, accumulated_deaths_today, today)
    today_admitted = update_stat(Measurement.ADMITTED_PEOPLE, accumulated_admitted_today, today)
    today_uci = update_stat(Measurement.ICU_PEOPLE, accumulated_icu_today, today)

    today_pcrs_last_24h = pcrs_report.get_column_data(2)
    influx.insert_stats_in_influx(Measurement.PCRS_LAST_24H, today, today_pcrs_last_24h)

    return today_pcrs, today_deaths, today_pcrs_last_24h, today_admitted, today_uci


def update_stat(stat, accumulated_today, today):
    accumulated_yesterday = influx.get_stat_accumulated_until_day(stat, today)
    today_number = get_today_numbers(accumulated_today, accumulated_yesterday)
    influx.insert_stats_in_influx(stat, today, today_number)

    return today_number


def get_today_numbers(today_accumulated, yesterday_accumulated):
    today_new = {}
    for ccaa in today_accumulated:
        today_new[ccaa] = today_accumulated[ccaa] - yesterday_accumulated.get(ccaa, 0)

    return today_new


def publish_report(today, yesterday):
    today_pcrs, today_deaths, today_pcrs24h, today_admitted, today_icu = influx.get_all_stats_group_by_day(today)
    yesterday_pcrs, yesterday_deaths, yesterday_pcrs24h, yesterday_admitted, yesterday_icu = influx.get_all_stats_group_by_day(yesterday)

    accumulated_pcrs, accumulated_deaths = influx.get_all_stats_accumulated_until_day(today)

    today_data = {}
    yesterday_data = {}

    for ccaa in today_pcrs:
        today_data[ccaa] = {}
        yesterday_data[ccaa] = {}

        today_data[ccaa]["pcrs"] = today_pcrs[ccaa]
        today_data[ccaa]["pcrs_last24h"] = today_pcrs24h[ccaa]
        today_data[ccaa]["deaths"] = today_deaths[ccaa]
        today_data[ccaa]["admitted"] = today_admitted[ccaa]
        today_data[ccaa]["icu"] = today_icu[ccaa]
        today_data[ccaa]["accumulated_pcrs"] = accumulated_pcrs[ccaa]
        today_data[ccaa]["accumulated_deaths"] = accumulated_deaths[ccaa]

        yesterday_data[ccaa]["pcrs"] = yesterday_pcrs[ccaa]
        yesterday_data[ccaa]["pcrs_last24h"] = yesterday_pcrs24h[ccaa]
        yesterday_data[ccaa]["deaths"] = yesterday_deaths[ccaa]
        yesterday_data[ccaa]["admitted"] = yesterday_admitted[ccaa]
        yesterday_data[ccaa]["icu"] = yesterday_icu[ccaa]

    tweets = get_report_by_ccaa(today, today_data, yesterday_data)

    last_id = twitter.publish_tweets(tweets)

    spain_today_data = {
        "pcrs": sum(today_pcrs.values()),
        "pcrs_last24h": sum(today_pcrs24h.values()),
        "deaths": sum(today_deaths.values()),
        "admitted": sum(today_admitted.values()),
        "icu": sum(today_icu.values()),
        "accumulated_pcrs": sum(accumulated_pcrs.values()),
        "accumulated_deaths": sum(accumulated_deaths.values())
    }

    spain_yesterday_data = {
        "pcrs": sum(yesterday_pcrs.values()),
        "pcrs_last24h": sum(yesterday_pcrs24h.values()),
        "deaths": sum(yesterday_deaths.values()),
        "admitted": sum(yesterday_admitted.values()),
        "icu": sum(yesterday_icu.values())
    }

    spain_report = get_ccaa_report("España", today, spain_today_data, spain_yesterday_data)
    graph_url = get_graph_url(today - timedelta(31), today)
    twitter.publish_tweet_with_media(spain_report, graph_url, last_id)

    logging.info("Tweets published correctly!")


def get_header(stat_type, date):
    return "{0} reportadas el{1}{2}".format(stat_type, " fin de semana del " if date.weekday() == 0 else " ",
                                            (date - timedelta(1)).strftime(DATE_FORMAT))


def get_summary_tweet(date, pcrs_summary, pcrs24h_summary, deaths_summary):
    items = ["Resumen España al finalizar el {0}:".format((date - timedelta(1)).strftime(DATE_FORMAT)), "",
             pcrs_summary, pcrs24h_summary, deaths_summary, "",
             "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1",
             "Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1"]

    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
