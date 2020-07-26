import requests
import codecs
import os
import tweepy
import sys
import logging
import tabula
import re
from collections import defaultdict
from datetime import datetime, timedelta
from shutil import copyfile
from urllib.error import HTTPError
from influxdb import InfluxDBClient
import math


FILES_FOLDER = "covid19_data"

CCAAS = {
    "AN": "Andalucía",
    "AR": "Aragón",
    "AS": "Asturias",
    "IB": "Baleares",
    "CN": "Canarias",
    "CB": "Cantabria",
    "CM": "Castilla La Mancha",
    "CL": "Castilla y León",
    "CT": "Cataluña",
    "CE": "Ceuta",
    "VC": "C. Valenciana",
    "EX": "Extremadura",
    "GA": "Galicia",
    "MD": "Madrid",
    "ML": "Melilla",
    "MC": "Murcia",
    "NC": "Navarra",
    "PV": "País Vasco",
    "RI": "La Rioja"
}

CCAA_POPULATION = {
    "AN": 8414240,
    "AR": 1319291,
    "AS": 1022800,
    "IB": 1149460,
    "CN": 2153389,
    "CB": 581078,
    "CM": 2032863,
    "CL": 2399548,
    "CT": 7675217,
    "CE": 84777,
    "VC": 5003769,
    "EX": 1067710,
    "GA": 2699499,
    "MD": 6663394,
    "ML": 86487,
    "MC": 1493898,
    "NC": 654214,
    "PV": 2207776,
    "RI": 316798
}

CCAA_REVERSE = {v: k for k, v in CCAAS.items()}
MS_PDF_FORMAT = "https://www.mscbs.gob.es/en/profesionales/saludPublica/ccayes/alertasActual/nCov-China/documentos/Actualizacion_{0}_COVID-19.pdf"
ISCIII_URL = "https://cnecovid.isciii.es/covid19/resources/agregados.csv"
DATE_FORMAT = "%d/%m/%Y"

def download_file(file_path):
    r = requests.get("https://cnecovid.isciii.es/covid19/resources/agregados.csv")
    open(file_path, "wb").write(r.content)
    return file_path


def get_path_for_date(date):
    return os.path.join(FILES_FOLDER, "{0}.csv".format(date.strftime("%Y%m%d")))


def process_file(today, yesterday, today_file, yesterday_file, day_before_yesterday_file):
    today_pcrs, today_deaths, today_antibodies = get_cases_later_day_in_file(today_file)
    yesterday_pcrs, yesterday_deaths, yesterday_antibodies = get_cases_later_day_in_file(yesterday_file)
    day_before_yesterday_pcrs, day_before_yesterday_deaths, day_before_yesterday_antibodies = get_cases_later_day_in_file(day_before_yesterday_file)
    today_cases = get_total_cases(today_pcrs, today_antibodies)
    yesterday_cases = get_total_cases(yesterday_pcrs, yesterday_antibodies)
    day_before_yesterday_cases = get_total_cases(day_before_yesterday_pcrs, day_before_yesterday_antibodies)

    # Antibodies information is not availble when the information has been collected from the PDFs...
    # At least, yesterday info is required to calculate the number of new cases today...
    antibodies_available = today_antibodies and yesterday_antibodies

    publish_tweets_for_stat("PCR+", today, today_pcrs, yesterday_pcrs, day_before_yesterday_pcrs)
    publish_tweets_for_stat("Muertes", today, today_deaths, yesterday_deaths, day_before_yesterday_deaths)
    # publish_tweets_for_stat("Ag+", yesterday, today_antibodies, yesterday_antibodies, day_before_yesterday_antibodies) if antibodies_available else None

    pcrs_summary = get_summary("PCR+", today_pcrs, yesterday_pcrs, day_before_yesterday_pcrs)
    deaths_summary = get_summary("Muertes", today_deaths, yesterday_deaths, day_before_yesterday_deaths)
    antibodies_summary = get_summary("Ag+", today_antibodies, yesterday_antibodies, day_before_yesterday_antibodies) if antibodies_available else None
    cases_summary = get_summary("Total Casos", today_cases, yesterday_cases, day_before_yesterday_cases) if antibodies_available else None

    publish_tweets([get_summary_tweet(today, pcrs_summary, antibodies_summary, cases_summary, deaths_summary)])

    logging.info("Tweets published correctly!")

    insert_stats_in_influx("pcrs", today), today_pcrs, yesterday_pcrs)
    insert_stats_in_influx("deaths", today), today_deaths, yesterday_deaths)


def get_cases_later_day_in_file(file_path):
    cases_by_ccaa_and_date = defaultdict(dict)
    deaths_by_ccaa_and_date = defaultdict(dict)
    antibodies_by_ccaa_and_date = defaultdict(dict)
    with codecs.open(file_path, "r", "iso-8859-1") as f:
        for line in f:

            line_parts = line.split(",")
            ccaa = line_parts[0]

            if len(ccaa) != 2:
                continue

            date = datetime.strptime(line_parts[1], DATE_FORMAT)
            cases = int(line_parts[3])
            antibodies = int(line_parts[4]) if line_parts[4] else None
            deaths = int(line_parts[7] if line_parts[7].strip() else "0")

            cases_by_ccaa_and_date[date][ccaa] = cases
            deaths_by_ccaa_and_date[date][ccaa] = deaths
            antibodies_by_ccaa_and_date[date][ccaa] = antibodies

    later_date = max(cases_by_ccaa_and_date.keys())
    antibodies_later_date = antibodies_by_ccaa_and_date[later_date]
    antibodies_later_date = {k: v for k, v in antibodies_later_date.items() if v is not None}
    return cases_by_ccaa_and_date[later_date], deaths_by_ccaa_and_date[later_date], antibodies_later_date


def get_total_cases(pcrs, antibodies):
    return {k: pcrs[k] + antibodies[k] for k in pcrs} if antibodies else None


def get_summary(stat_type, today_info, yesterday_info, day_before_yesterday_info):
    today_total = sum(today_info.values()) - sum(yesterday_info.values())
    yesteday_total = sum(yesterday_info.values()) - sum(day_before_yesterday_info.values()) if day_before_yesterday_info else None
    sentence = "{0}: {1:+} {2} {3} (Totales: {4:,})".format(stat_type, today_total, get_impact_string(today_total), get_tendency_emoji(today_total, yesteday_total), sum(today_info.values())).replace(",", ".")
    return " ".join(sentence.split())


def get_summary_tweet(date, pcrs_summary, antibodies_summary, cases_summary, deaths_summary):
    # items = ["Resumen España hasta el {0}:".format(date.strftime(DATE_FORMAT)), "", pcrs_summary, antibodies_summary, cases_summary, deaths_summary]
    items = ["Resumen España al finalizar el {0}:".format((date - timedelta(1)).strftime(DATE_FORMAT)), "", pcrs_summary, deaths_summary, "", "Evolución ➡️ https://home.aitormagan.es/d/HukfaHZgk/covid19?orgId=1", "Comparación ➡️ https://home.aitormagan.es/d/h6K39NRRk/covid19-comparison?orgId=1"]
    return "\n".join(list(filter(lambda x: x is not None, items)))


def publish_tweets_for_stat(stat_type, date, today_info, yesterday_info, day_before_yesterday_info):
    sentences = get_tweet_sentences(today_info, yesterday_info, day_before_yesterday_info)
    tweets = get_tweets(stat_type, date, sentences)
    publish_tweets(tweets)


def get_tweet_sentences(today_info, yesterday_info, day_before_yesterday_info):
    today_total = sum(today_info.values()) - sum(yesterday_info.values())
    yesterday_total = sum(yesterday_info.values()) - sum(day_before_yesterday_info.values())
    sentences = []
    for ccaa in today_info:
        ccaa_today_total = today_info[ccaa] - yesterday_info.get(ccaa, 0)
        ccaa_yesterday_total = yesterday_info[ccaa] - day_before_yesterday_info[ccaa] if ccaa in yesterday_info and ccaa in day_before_yesterday_info else None
        sentence = "{0}: {1:+} {2} {3}".format(CCAAS[ccaa], ccaa_today_total, get_impact_string(ccaa_today_total, ccaa), get_tendency_emoji(ccaa_today_total, ccaa_yesterday_total))
        sentences.append(' '.join(sentence.split()))

    return sentences


def get_tendency_emoji(today_number, yesterday_number):
    if yesterday_number is None:
        return ""
    elif today_number > yesterday_number:
        return '🔺{0}'.format(today_number - yesterday_number)
    elif yesterday_number > today_number:
        return '🔻{0}'.format(yesterday_number - today_number)
    else:
        return '🔙'


def get_impact_string(total_cases, ccaa=None):
    divider = CCAA_POPULATION[ccaa] if ccaa else sum(CCAA_POPULATION.values())
    ccaa_impact = total_cases * 1000000 / divider
    return "({0:.2f}/millón)".format(ccaa_impact).replace(".", ",") if total_cases > 0 else ""


def get_tweets(stat_type, date, sentences):
    tweets = []
    
    if date.weekday() in [5, 6]:
        monday = date + timedelta(0 - date.weekday())
        sunday = date + timedelta(6 - date.weekday())
        header_format = "{0} reportadas la semana del {1} al {2}".format(stat_type, monday.strftime(DATE_FORMAT), sunday.strftime(DATE_FORMAT))
    else:
        header_format = "{0} reportadas el{1}{2} ".format(stat_type, " fin de semana del " if date.weekday() == 0 else " ", (date - timedelta(1)).strftime(DATE_FORMAT))
    
    header_format += " ({0}/{1}):\n\n"
    # We assume that the total amount of tweets will be 9 or less...
    header_length = tweet_length(header_format.format(stat_type, (date - timedelta(1)).strftime(DATE_FORMAT), 0, 0))

    current_tweet = ""
    for sentence in sentences:
        # Twitter counts emoji as double characters...
        if tweet_length(current_tweet) + tweet_length(sentence) + header_length > 280:
            tweets.append(current_tweet.strip("\n"))
            current_tweet = ""

        current_tweet += sentence + "\n"

    tweets.append(current_tweet.strip("\n"))

    return list(map(lambda x: header_format.format(x + 1, len(tweets)) + tweets[x], range(0, len(tweets))))


def tweet_length(sentence):
    emoji_regex = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
    return len(sentence) + len(emoji_regex.findall(sentence))


def publish_tweets(tweets):

    api = get_twitter_api()

    last_tweet = None
    for tweet in tweets:
        last_tweet = api.update_status(tweet, last_tweet).id


def send_dm_error():
    api = get_twitter_api()
    api.send_direct_message(api.get_user("aitormagan").id, "There was an error, please, check!")


def get_twitter_api():
    auth = tweepy.OAuthHandler(os.environ.get("API_SECRET", ""),
                               os.environ.get("API_SECRET_KEY", ""))
    auth.set_access_token(os.environ.get("ACCESS_TOKEN", ""),
                          os.environ.get("ACCESS_TOKEN_SECRET", ""))
    return tweepy.API(auth)


def create_custom_file(today, yesterday, today_file):
    try:
        create_custom_file1(today, yesterday, today_file)
    except HTTPError as e:
        raise e
    except:
        logging.exception("Impossible to obtain info. using the default read_pdf function. Trying with specific area...")
        create_custom_file2(today, yesterday, today_file)


def create_custom_file1(today, yesterday, today_file):
    cases = {}
    deaths = {}
    df = tabula.read_pdf(MS_PDF_FORMAT.format(get_pdf_id_for_date(today)), pages='1,2')
    df = list(filter(lambda x: len(x) >= 22, df))

    for table in df:
        for column in table:
            table[column.replace('*', '').strip()] = table.pop(column)

    for i in range(len(df[0]) - 19 - 1, len(df[0]) - 1):
        cases[CCAA_REVERSE[df[0]['Unnamed: 0'][i].replace('*', '')]] = int(df[0]['Unnamed: 1'][i].replace('.', '').replace('-', '0'))

    for i in range(len(df[1]) - 19 - 1, len(df[1]) - 1):
        deaths[CCAA_REVERSE[df[1]['Unnamed: 0'][i].replace('*', '')]] = int(df[1]['Unnamed: 1'][i].split(" ")[0].replace('.', '').replace('-','0'))

    rows = []
    for ccaa in cases:
        rows.append('{0},{1},,{2},,,,{3},'.format(ccaa, yesterday.strftime(DATE_FORMAT), cases[ccaa], deaths[ccaa]))

    with open(today_file, 'w+') as f:
        f.write("\n".join(rows) + "\n")

def create_custom_file2(today, yesterday, today_file):
    cases = {}
    df = tabula.read_pdf(MS_PDF_FORMAT.format(get_pdf_id_for_date(today)), pages='1', area=(233, 65, 233+301, 65+767))
    df = list(filter(lambda x: len(x) >= 22, df))

    for table in df:
        for column in table:
            table[column.replace('*', '').strip()] = table.pop(column)

    for i in range(5, 24):
        cases[CCAA_REVERSE[df[0]['Unnamed: 0'][i].replace('*', '')]] = int(df[0]['Unnamed: 1'][i].replace('.', '').replace('-', '0'))

    rows = []
    for ccaa in cases:
        rows.append('{0},{1},,{2},,,,0,'.format(ccaa, yesterday.strftime(DATE_FORMAT), cases[ccaa]))

    with open(today_file, 'w+') as f:
        f.write("\n".join(rows) + "\n")


def get_pdf_id_for_date(date):
    # 14/5/2020 -> id: 105
    # Weekends starting on 4/7/2020 no reports are published
    reference_date = datetime(2020, 5, 14)
    intial_weekend_without_report = datetime(2020, 7, 4)
    weekends = math.ceil((date - intial_weekend_without_report).days / 7)
    return 105 + (date - reference_date).days - weekends * 2


def insert_stats_in_influx(measurement, date, today_pcrs, yesterday_pcrs):
    cases_by_day = {}
    for ccaa in today_pcrs:
        diff = today_pcrs[ccaa] - yesterday_pcrs[ccaa]
        cases_by_day[ccaa] = diff

    influx_data = []
    for ccaa in cases_by_day:
        influx_data.append({
            "measurement": measurement,
            "time": date.date().isoformat(),
            "tags": {
                "ccaa": CCAAS[ccaa]
            },
            "fields": {
                "value": cases_by_day[ccaa]
            }
        })

    client = InfluxDBClient(os.environ.get("INFLUX_HOST", "localhost"), 8086, None, None, 'covid19')
    client.write_points(influx_data)


def substract_days_ignoring_weekends(initial_date, days_to_substract):
    result = initial_date

    while days_to_substract > 0:
        result = result - timedelta(days=1)

        if result.weekday() < 5:
            days_to_substract -= 1

    return result


def main():

    today = datetime.now()
    yesterday = substract_days_ignoring_weekends(today, 1)
    day_before_yesterday = substract_days_ignoring_weekends(today, 2)

    today_file = get_path_for_date(today)
    yesterday_file = get_path_for_date(yesterday)
    day_before_yesterday_file = get_path_for_date(day_before_yesterday)

    if not os.path.exists(today_file):
        try:
            create_custom_file(today, yesterday, today_file)
            process_file(today, yesterday, today_file, yesterday_file, day_before_yesterday_file)
        except HTTPError as e:
            logging.info("PDF is not availble yet...")
        except Exception as e:
            logging.exception("Unhandled exception while trying to publish tweets")
            send_dm_error()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)
    os.chdir(os.path.dirname(__file__))

    main()
