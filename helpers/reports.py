from collections import defaultdict
from helpers.spain_geography import get_impact_string
from helpers.db import Measurement
from constants import GRAPH_IMAGE_URL


def get_report_by_ccaa(date_in_header, ccaas_today_data, ccaas_yesterday_data, ccaas_accumulated_data):
    tweets = []
    for ccaa in sorted(ccaas_today_data.keys()):
        tweets.append(get_territorial_unit_report(ccaa, date_in_header, ccaas_today_data[ccaa],
                                                  ccaas_yesterday_data[ccaa], ccaas_accumulated_data[ccaa]))

    return tweets


def get_global_report(date_in_header, ccaas_today_data, ccaas_yesterday_data, ccaas_accumulated_data):
    global_today_data = get_global_data(ccaas_today_data)
    global_yesterday_data = get_global_data(ccaas_yesterday_data)
    global_accumulated_data = get_global_data(ccaas_accumulated_data)

    return get_territorial_unit_report("🇪🇸 España", date_in_header, global_today_data, global_yesterday_data,
                                       global_accumulated_data)


def get_global_data(dict_to_unpack):
    keys = set([key for ccaa in dict_to_unpack for key in dict_to_unpack[ccaa].keys()])

    result = defaultdict(lambda: 0)
    for key in keys:
        for ccaa in dict_to_unpack:
            result[key] += dict_to_unpack[ccaa][key]

    return result


def get_territorial_unit_report(territorial_unit, date_in_header, today_data, yesterday_data, accumulated_data):
    sentences = [f"{territorial_unit} - {date_in_header}:\n",
                 get_report_sentence("💉 PCRs", territorial_unit, today_data.get(Measurement.PCRS),
                                     yesterday_data.get(Measurement.PCRS), accumulated_data.get(Measurement.PCRS)),
                 get_report_sentence("💉 PCRs 24h", territorial_unit, today_data.get(Measurement.PCRS_LAST_24H),
                                     yesterday_data.get(Measurement.PCRS_LAST_24H)),
                 get_report_sentence("😢 Muertes", territorial_unit, today_data.get(Measurement.DEATHS),
                                     yesterday_data.get(Measurement.DEATHS), accumulated_data.get(Measurement.DEATHS))
                 + "\n",
                 # FIXME!! Be aware! Data seems to be inconsistent
                 get_report_sentence("🚑 Hospitalizados", territorial_unit, today_data.get(Measurement.ADMITTED_PEOPLE),
                                     yesterday_data.get(Measurement.ADMITTED_PEOPLE)),
                 get_report_sentence("🏥 UCI", territorial_unit, today_data.get(Measurement.ICU_PEOPLE),
                                     yesterday_data.get(Measurement.ICU_PEOPLE))
                 ]

    return "\n".join(sentences)


def get_report_sentence(stat, territorial_unit, today_total, yesterday_total, accumulated=None):
    total_sentence = "(Totales: {0:,})".format(accumulated) if accumulated else ""
    sentence = "{0}: {1:+,} {2} {3} {4}".format(stat, today_total,
                                                get_impact_string(today_total, territorial_unit),
                                                get_tendency_emoji(today_total, yesterday_total),
                                                total_sentence).replace(",", ".").strip()

    return " ".join(sentence.split())


def get_tendency_emoji(today_number, yesterday_number):
    if yesterday_number is None:
        return ""
    elif today_number > yesterday_number:
        return '🔺{0:,}'.format(today_number - yesterday_number)
    elif yesterday_number > today_number:
        return '🔻{0:,}'.format(yesterday_number - today_number)
    else:
        return '🔙'


def get_graph_url(start=None, end=None):
    start_str = f"&from={int(start.strftime('%s')) * 1000}" if start else ""
    end_str = f"&to={int(end.strftime('%s')) * 1000}" if end else ""

    return GRAPH_IMAGE_URL + start_str + end_str
