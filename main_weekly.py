import logging
import sys
from datetime import timedelta, datetime
from helpers.influx import Influx, Measurement
from helpers.twitter import Twitter
from helpers.reports import get_report_by_ccaa, get_human_summary, get_graph_url
from constants import DATE_FORMAT

influx = Influx()
twitter = Twitter()


def main():
    date = datetime.now()

    pcrs_current_week = influx.get_stat_group_by_week(Measurement.PCRS, date)
    pcrs_previous_week = influx.get_stat_group_by_week(Measurement.PCRS, date - timedelta(7))
    deaths_current_week = influx.get_stat_group_by_week(Measurement.DEATHS, date)
    deaths_previous_week = influx.get_stat_group_by_week(Measurement.DEATHS, date - timedelta(7))

    pcrs_report = get_report_by_ccaa(pcrs_current_week, pcrs_previous_week)
    deaths_report = get_report_by_ccaa(deaths_current_week, deaths_previous_week)

    twitter.publish_tweets(pcrs_report, get_header("PCR+", date))
    twitter.publish_tweets(deaths_report, get_header("Muertes", date))

    today_pcrs_accumulated, today_deaths_accumulated = influx.get_all_stats_accumulated_until_day(date)
    pcrs_summary = get_human_summary("PCR+", pcrs_current_week, pcrs_previous_week, today_pcrs_accumulated)
    deaths_summary = get_human_summary("Muertes", deaths_current_week, deaths_previous_week, today_deaths_accumulated)

    graph_url = get_graph_url(date - timedelta(7), date)
    twitter.publish_tweet_with_media(get_week_summary_tweet(date, pcrs_summary, deaths_summary), graph_url)


def get_header(stat_type, date):
    monday = date + timedelta(0 - date.weekday())
    sunday = date + timedelta(6 - date.weekday())
    return "{0} reportadas la semana del {1} al {2}".format(stat_type, monday.strftime(DATE_FORMAT),
                                                            sunday.strftime(DATE_FORMAT))


def get_week_summary_tweet(date, pcrs_summary, deaths_summary):
    monday = date + timedelta(0 - date.weekday())
    sunday = date + timedelta(6 - date.weekday())
    items = ["Resumen España la semana del {0} al {1}:".format(monday.strftime(DATE_FORMAT),
                                                               sunday.strftime(DATE_FORMAT)),
             "", pcrs_summary, deaths_summary, "",
             "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1&var-group_by=1w,4d"]
    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
