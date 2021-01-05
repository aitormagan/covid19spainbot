import sys
import logging
from datetime import datetime, timedelta, date
from urllib.error import HTTPError
from helpers.twitter import Twitter
from helpers.db import Influx, Measurement
from helpers.ministry_report import SpainCovid19MinistryReport
from helpers.vaccination_report import SpainVaccinationReport
from helpers.reports import get_report_by_ccaa, get_graph_url, get_global_report
from constants import DAYS_WITHOUT_REPORT

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

        if result.weekday() < 5 and result.date() not in DAYS_WITHOUT_REPORT:
            days_to_substract -= 1

    return result


def update_database(today):
    pcrs_report = SpainCovid19MinistryReport(today, 1)
    deaths_report = SpainCovid19MinistryReport(today, 5, (142, 539, 142+343, 539+265))
    hospital_report = _get_hospitals_report(today)
    vaccination_report = SpainVaccinationReport()

    try:
        accumulated_pcrs_today = pcrs_report.get_column_data(1)
    except Exception:
        # With some PDFs, tabula-pdf auto table detection fails.
        # We need to specify a custom area.
        pcrs_report = SpainCovid19MinistryReport(today, 1, (239, 56, 239 + 283, 56 + 756))
        accumulated_pcrs_today = pcrs_report.get_column_data(1)

    accumulated_admitted_today = hospital_report.get_column_data(1)
    accumulated_icu_today = hospital_report.get_column_data(3)
    accumulated_deaths_today = deaths_report.get_column_data(1)
    today_percentage_admitted = hospital_report.get_column_data(7, cast=float)
    today_percentage_icu = hospital_report.get_column_data(9, cast=float)
    today_pcrs_last_24h = pcrs_report.get_column_data(2)
    accumulated_incidence = pcrs_report.get_column_data(3, 1, float)
    accumulated_vaccinations = vaccination_report.get_vaccination_by_ccaa()

    update_stat(Measurement.PCRS, accumulated_pcrs_today, today)
    update_stat(Measurement.DEATHS, accumulated_deaths_today, today)
    update_stat(Measurement.ADMITTED_PEOPLE, accumulated_admitted_today, today)
    update_stat(Measurement.ICU_PEOPLE, accumulated_icu_today, today)
    update_stat(Measurement.VACCINATIONS, accumulated_vaccinations, today)

    influx.insert_stats(Measurement.PCRS_LAST_24H, today, today_pcrs_last_24h)
    influx.insert_stats(Measurement.ACCUMULATED_INCIDENCE, today, accumulated_incidence)
    influx.insert_stats(Measurement.PERCENTAGE_ADMITTED, today, today_percentage_admitted)
    influx.insert_stats(Measurement.PERCENTAGE_ICU, today, today_percentage_icu)


def _get_hospitals_report(date):
    try:
        hospital_report = SpainCovid19MinistryReport(date, 3, (160, 33, 160 + 250, 33 + 790))
        hospital_report.get_column_data(1)
    except:
        hospital_report = SpainCovid19MinistryReport(date, 3, (150, 33, 150 + 250, 33 + 790))

    return hospital_report


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
    accumulated_today = influx.get_all_stats_accumulated_until_day(today)
    date_header = get_date_header(today, yesterday)

    spain_report = get_global_report(date_header, today_data, yesterday_data, accumulated_today)
    graph_url = get_graph_url(today - timedelta(31), today)
    last_id = twitter.publish_tweet_with_media(spain_report, graph_url)

    tweets = get_report_by_ccaa(date_header, today_data, yesterday_data, accumulated_today)
    last_id = twitter.publish_tweets(tweets, last_id)
    twitter.publish_tweet(get_final_tweet(), last_id)

    logging.info("Tweets published correctly!")


def get_date_header(today, yesterday):
    date_format = "%d/%m/%Y"

    today = today.date()
    yesterday = yesterday.date()

    if today - timedelta(days=1) == yesterday:
        date_header = (today - timedelta(1)).strftime(date_format)
    else:
        date_header = f"{yesterday.strftime(date_format)} al {(today - timedelta(1)).strftime(date_format)}"

    return date_header


def get_final_tweet():
    items = ["¡Accede a los gráficos interactivos!",
             "",
             "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1",
             "Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1"
             "",
             "* Porcentaje vacunados sobre población total"]

    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
