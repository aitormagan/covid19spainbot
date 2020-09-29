import os
import locale
from collections import defaultdict
from helpers.db import Measurement
from constants import GRAPH_IMAGE_PATH

locale.setlocale(locale.LC_ALL, 'es_ES')


def get_report_by_ccaa(date_in_header, ccaas_today, ccaas_yesterday, ccaas_accumulated_today):
    tweets = []
    for ccaa in sorted(ccaas_today.keys()):
        tweets.append(get_territorial_unit_report(ccaa, date_in_header, ccaas_today[ccaa],
                                                  ccaas_yesterday[ccaa], ccaas_accumulated_today[ccaa]))

    return tweets


def get_global_report(date_in_header, ccaas_today, ccaas_yesterday, ccaas_accumulated_today):
    global_today_data = get_global_data(ccaas_today)
    global_yesterday_data = get_global_data(ccaas_yesterday)
    global_accumulated_data = get_global_data(ccaas_accumulated_today)

    return get_territorial_unit_report("🇪🇸 España", date_in_header, global_today_data, global_yesterday_data,
                                       global_accumulated_data)


def get_global_data(dict_to_unpack):
    keys = set([key for ccaa in dict_to_unpack for key in dict_to_unpack[ccaa].keys()])

    result = defaultdict(lambda: 0)
    for key in keys:
        for ccaa in dict_to_unpack:
            result[key] += dict_to_unpack[ccaa][key] if dict_to_unpack[ccaa][key] else 0

    return result


def get_territorial_unit_report(territorial_unit, header_date, today_data, yesterday_data, accumulated_today):

    sentences = list()
    sentences.append(f"{territorial_unit} - {header_date}:")
    sentences.append("")
    sentences.append(get_report_sentence("💉 PCRs", today_data.get(Measurement.PCRS),
                                         yesterday_data.get(Measurement.PCRS),
                                         accumulated_today.get(Measurement.PCRS)))

    if Measurement.PCRS_LAST_24H in today_data:
        sentences.append(get_report_sentence("💉 PCRs 24h", today_data.get(Measurement.PCRS_LAST_24H),
                                             yesterday_data.get(Measurement.PCRS_LAST_24H)))

    sentences.append(get_accumulated_impact_sentence("💥 IA 14 días",
                                                     today_data.get(Measurement.ACCUMULATED_INCIDENCE),
                                                     yesterday_data.get(Measurement.ACCUMULATED_INCIDENCE)))
    sentences.append("")
    sentences.append(get_report_sentence("😢 Muertes", today_data.get(Measurement.DEATHS),
                                         yesterday_data.get(Measurement.DEATHS),
                                         accumulated_today.get(Measurement.DEATHS)))
    sentences.append("")
    sentences.append(get_report_sentence("🚑 Hospitalizados", today_data.get(Measurement.ADMITTED_PEOPLE),
                                         yesterday_data.get(Measurement.ADMITTED_PEOPLE)))
    sentences.append(get_report_sentence("🏥 UCI", today_data.get(Measurement.ICU_PEOPLE),
                                         yesterday_data.get(Measurement.ICU_PEOPLE)))

    return "\n".join(sentences)


def get_accumulated_impact_sentence(stat, today_total, yesterday_total):
    formatted_number = locale.format_string('%.2f', today_total, grouping=True, monetary=True)
    return "{0}: {1}/100.000 hab. {2}".format(stat, formatted_number, get_tendency_emoji(today_total, yesterday_total))


def get_report_sentence(stat, today_total, yesterday_total, accumulated=None):
    total_sentence = "(Totales: {0:,})".format(accumulated).replace(",", ".") if accumulated else ""
    sentence = "{0}: {1} {2} {3}".format(stat, "{0:+,}".format(today_total).replace(",", "."),
                                         get_tendency_emoji(today_total, yesterday_total),
                                         total_sentence).strip()

    return " ".join(sentence.split())


def get_tendency_emoji(today_number, yesterday_number):

    def formatter(x):
        return locale.format_string("%.6g", round(x, 2), grouping=True, monetary=True)

    if yesterday_number is None:
        result = ""
    elif today_number > yesterday_number:
        result = f'🔺{formatter(today_number - yesterday_number)}'
    elif yesterday_number > today_number:
        result = f'🔻{formatter(yesterday_number - today_number)}'
    else:
        result = '🔙'

    return result


def get_graph_url(start=None, end=None, additional_vars=None):
    vars_str = "&" + "&".join([f"var-{k}={v}" for k, v in additional_vars.items()]) if additional_vars else ""
    start_str = f"&from={int(start.strftime('%s')) * 1000}" if start else ""
    end_str = f"&to={int(end.strftime('%s')) * 1000}" if end else ""
    grafana_server = os.environ.get("GRAFANA_SERVER", "http://localhost:3000")

    return os.path.join(grafana_server, GRAPH_IMAGE_PATH) + start_str + end_str + vars_str

