from helpers.spain_geography import get_impact_string


def get_report_by_ccaa(today_data, yesterday_data):
    sentences = []
    for ccaa in today_data:
        ccaa_today_total = today_data[ccaa]
        ccaa_yesterday_total = yesterday_data[ccaa]
        sentence = "{0}: {1:+} {2} {3}".format(ccaa, ccaa_today_total, get_impact_string(ccaa_today_total, ccaa),
                                               get_tendency_emoji(ccaa_today_total, ccaa_yesterday_total))
        sentences.append(' '.join(sentence.split()))

    return sentences


def get_human_summary(stat_type, today_data, yesterday_data, today_accumulated_data):
    today_total = sum(today_data.values())
    yesteday_total = sum(yesterday_data.values())
    sentence = "{0}: {1:+} {2} {3} (Totales: {4:,})".format(stat_type, today_total, get_impact_string(today_total),
                                                            get_tendency_emoji(today_total, yesteday_total),
                                                            sum(today_accumulated_data.values())).replace(",", ".")
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
