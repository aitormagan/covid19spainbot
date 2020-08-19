from helpers.spain_geography import get_impact_string
from constants import GRAPH_IMAGE_URL, DATE_FORMAT
from datetime import timedelta


def get_report_by_ccaa(date, today_data, yesterday_data):
    tweets = []
    for ccaa in today_data:
        tweets.append(get_ccaa_report(ccaa, date, today_data[ccaa], yesterday_data[ccaa]))

    return tweets


def get_ccaa_report(ccaa, date, ccaa_today_data, ccaa_yesterday_data):
    date_in_report = date - timedelta(1)
    sentences = [f"{ccaa} el {date_in_report.strftime(DATE_FORMAT)}:", "\n"]

    sentences.append(generate_ccaa_sentence("💉 PCRs", ccaa, ccaa_today_data.get("pcrs"),
                                            ccaa_yesterday_data.get("pcrs"),
                                            ccaa_today_data.get("accumulated_pcrs")))

    sentences.append(generate_ccaa_sentence("💉 PCRs 24h", ccaa, ccaa_today_data.get("pcrs_last24h"),
                                            ccaa_yesterday_data.get("pcrs_last24h")))
    sentences.append(generate_ccaa_sentence("😢 Muertes", ccaa, ccaa_today_data.get("deaths"),
                                            ccaa_yesterday_data.get("deaths"),
                                            ccaa_today_data.get("accumulated_deaths")))

    sentences.append("\n")

    sentences.append(generate_ccaa_sentence("🚑 Hospitalizados", ccaa, ccaa_today_data.get("admitted"),
                                            ccaa_yesterday_data.get("admitted")))
    sentences.append(generate_ccaa_sentence("🏥 UCI", ccaa, ccaa_today_data.get("icu"),
                                            ccaa_yesterday_data.get("icu")))

    return "\n".join(sentences)


def generate_ccaa_sentence(stat, ccaa, today_total, yesterday_total, acumulated=None):
    total_sentence = "(Totales: {0:,})".format(acumulated) if acumulated else ""
    sentence = "{0}: {1:+} {2} {3} {4}".format(stat, today_total, get_impact_string(today_total, ccaa),
                                               get_tendency_emoji(today_total, yesterday_total),
                                               total_sentence).replace(",", ".").strip()

    return " ".join(sentence.split())


def get_human_summary(stat_type, today_data, yesterday_data, today_accumulated_data=None):
    today_total = sum(today_data.values())
    yesteday_total = sum(yesterday_data.values())
    total_sentence = "(Totales: {0:,})".format(sum(today_accumulated_data.values())) if today_accumulated_data else ""
    sentence = "{0}: {1:+} {2} {3} {4}".format(stat_type, today_total, get_impact_string(today_total),
                                               get_tendency_emoji(today_total, yesteday_total),
                                               total_sentence).replace(",", ".").strip()
    return " ".join(sentence.split())


def get_tendency_emoji(today_number, yesterday_number):
    if yesterday_number is None:
        return ""
    elif today_number > yesterday_number:
        return '🔺{0}'.format(today_number - yesterday_number)
    elif yesterday_number > today_number:
        return '🔻{0}'.format(yesterday_number - today_number)
    else:
        return '🔙'


def get_graph_url(start=None, end=None):
    start_str = f"&from={int(start.strftime('%s')) * 1000}" if start else ""
    end_str = f"&to={int(end.strftime('%s')) * 1000}" if end else ""

    return GRAPH_IMAGE_URL + start_str + end_str
