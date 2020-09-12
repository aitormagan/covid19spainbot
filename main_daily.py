import sys
import logging
from datetime import datetime, timedelta
from urllib.error import HTTPError
from helpers.twitter import Twitter
from helpers.db import Influx, Measurement
from helpers.ministry_report import SpainCovid19MinistryReport
from helpers.reports import get_report_by_ccaa, get_graph_url, get_global_report

twitter = Twitter()
influx = Influx()


def main():

    today = datetime.now()
    yesterday = subtract_days_ignoring_weekends(today, 1)

    data = influx.get_stat_group_by_day(Measurement.PCRS, today)

    if not data:
        try:
            update_database(today)
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
    influx.insert_stats(Measurement.PCRS_LAST_24H, today, today_pcrs_last_24h)

    return today_pcrs, today_deaths, today_pcrs_last_24h, today_admitted, today_uci


def update_stat(stat, accumulated_today, today):
    accumulated_yesterday = influx.get_stat_accumulated_until_day(stat, today)
    today_number = get_today_numbers(accumulated_today, accumulated_yesterday)
    influx.insert_stats(stat, today, today_number)

    return today_number


def get_today_numbers(today_accumulated, yesterday_accumulated):
    today_new = {}
    for ccaa in today_accumulated:
        today_new[ccaa] = today_accumulated[ccaa] - yesterday_accumulated.get(ccaa, 0)

    return today_new


def publish_report(today, yesterday):

    today_data = influx.get_all_stats_group_by_day(today)
    yesterday_data = influx.get_all_stats_group_by_day(yesterday)
    accumulated_data = influx.get_all_stats_accumulated_until_day(today)
    date_header = get_date_header(today)

    spain_report = get_global_report(date_header, today_data, yesterday_data, accumulated_data)
    graph_url = get_graph_url(today - timedelta(31), today)
    last_id = twitter.publish_tweet_with_media(spain_report, graph_url)

    tweets = get_report_by_ccaa(date_header, today_data, yesterday_data, accumulated_data)
    last_id = twitter.publish_tweets(tweets, last_id)
    twitter.publish_tweet(get_final_tweet(), last_id)

    logging.info("Tweets published correctly!")


def get_date_header(date):
    date_format = "%d/%m/%Y"
    if date.weekday() == 0:
        date_header = f"{(date - timedelta(3)).strftime(date_format)} al {(date - timedelta(1)).strftime(date_format)}"
    else:
        date_header = (date - timedelta(1)).strftime(date_format)

    return date_header


def get_final_tweet():
    items = ["¡Accede a los gráficos interactivos!",
             "",
             "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1",
             "Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1"]

    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
