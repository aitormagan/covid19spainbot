import logging
from datetime import datetime
from urllib.error import HTTPError
from helpers.twitter import Twitter
from helpers.db import Influx, Measurement
from helpers.ministry_report import VaccinesMinistryReport
from main_daily import update_stat, subtract_days_ignoring_weekends
from helpers.reports import get_vaccination_report

twitter = Twitter()
influx = Influx()


def main():

    today = datetime.now()
    yesterday = subtract_days_ignoring_weekends(today, 1)

    data = influx.get_stat_group_by_day(Measurement.VACCINATIONS, today)

    if not data:
        try:
            update_vaccinations(today)
            publish_report(today, yesterday)
        except HTTPError:
            logging.info("PDF is not available yet...")
        except Exception as e:
            logging.exception("Unhandled exception while trying to publish tweets")
            dm_text = f"There was an unhandled exception. Trace:\n\n{str(e)}"[0:280]
            twitter.send_dm(dm_text)


def update_vaccinations(today):
    vaccination_report = VaccinesMinistryReport(today, 3)
    accumulated_vaccinations = vaccination_report.get_column_data(5)
    accumulated_completed_vaccinations = vaccination_report.get_column_data(7)
    update_stat(Measurement.VACCINATIONS, accumulated_vaccinations, today)
    update_stat(Measurement.COMPLETED_VACCINATIONS, accumulated_completed_vaccinations, today)


def publish_report(today, yesterday):
    today_vaccinations = influx.get_stat_group_by_day(Measurement.VACCINATIONS, today)
    today_completed_vaccinations = influx.get_stat_group_by_day(Measurement.COMPLETED_VACCINATIONS, today)
    accumulated_vaccinations = influx.get_stat_accumulated_until_day(Measurement.VACCINATIONS, today)
    accumulated_completed_vaccinations = influx.get_stat_accumulated_until_day(Measurement.COMPLETED_VACCINATIONS,
                                                                               today)

    today_str = today.strftime("%d/%m/%Y")
    sentences_vaccination = get_vaccination_report(accumulated_vaccinations, today_vaccinations, False)
    last_tweet = twitter.publish_sentences_in_tweets(sentences_vaccination, f"💉 Total Dosis a {today_str}")

    sentences_completed_vaccination = get_vaccination_report(accumulated_completed_vaccinations,
                                                             today_completed_vaccinations, True)
    sentences_completed_vaccination.append("")
    sentences_completed_vaccination.append("* Porcentajes sobre población total de CCAA")
    twitter.publish_sentences_in_tweets(sentences_completed_vaccination, f"💉 Total Pautas Completas a {today_str}",
                                        last_tweet=last_tweet)


if __name__ == "__main__":
    main()
