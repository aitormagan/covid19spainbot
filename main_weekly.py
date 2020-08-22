import logging
import sys
from datetime import timedelta, datetime
from helpers.db import Influx
from helpers.twitter import Twitter
from helpers.reports import get_report_by_ccaa, get_global_report, get_graph_url

influx = Influx()
twitter = Twitter()


def main():
    date = datetime.now()

    today_data = influx.get_all_stats_group_by_week(date)
    yesterday_data = influx.get_all_stats_group_by_week(date - timedelta(7))
    accumulated_data = influx.get_all_stats_accumulated_until_day(date)
    date_header = get_date_header(date)

    tweets = get_report_by_ccaa(date_header, today_data, yesterday_data, accumulated_data)
    last_id = twitter.publish_tweets(tweets)
    spain_report = get_global_report(date_header, today_data, yesterday_data, accumulated_data)
    graph_url = get_graph_url(date - timedelta(7), date - timedelta(2))
    last_id = twitter.publish_tweet_with_media(spain_report, graph_url, last_id)
    twitter.publish_tweet(get_final_tweet(), last_id)


def get_date_header(date):
    date_format = "%d/%m"
    monday = date + timedelta(0 - date.weekday())
    sunday = date + timedelta(6 - date.weekday())
    return "Sem. {0} al {1}".format(monday.strftime(date_format),
                                    sunday.strftime(date_format))


def get_final_tweet():
    items = ["¡Accede a los gráficos interactivos!",
             "",
             "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1&var-group_by=1w,4d",
             "",
             "* Los datos de nuevos hospitalizados e ingresados en UCI se basan en en la Tabla 2 del "
             "informe diario de Sanidad."
             ]
    return "\n".join(list(filter(lambda x: x is not None, items)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    main()
