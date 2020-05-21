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


def process_file(today, today_file, yesterday_file, day_before_yesterday_file):
    today_pcrs, today_deaths, today_antibodies = get_cases_later_day_in_file(today_file)
    yesterday_pcrs, yesterday_deaths, yesterday_antibodies = get_cases_later_day_in_file(yesterday_file)
    day_before_yesterday_pcrs, day_before_yesterday_deaths, day_before_yesterday_antibodies = get_cases_later_day_in_file(day_before_yesterday_file)
    today_cases = get_total_cases(today_pcrs, yesterday_antibodies)
    yesterday_cases = get_total_cases(yesterday_pcrs, yesterday_antibodies)
    day_before_yesterday_cases = get_total_cases(day_before_yesterday_pcrs, day_before_yesterday_antibodies)

    # Antibodies information is not availble when the information has been collected from the PDFs...
    # At least, yesterday info is required to calculate the number of new cases today...
    antibodies_available = today_antibodies and yesterday_antibodies

    publish_tweets_for_stat("PCR+", today, today_pcrs, yesterday_pcrs, day_before_yesterday_pcrs)
    publish_tweets_for_stat("Muertes", today, today_deaths, yesterday_deaths, day_before_yesterday_deaths)
    publish_tweets_for_stat("Ag+", today, today_antibodies, yesterday_antibodies, day_before_yesterday_antibodies) if antibodies_available else None

    pcrs_summary = get_summary("PCR+", today_pcrs, yesterday_pcrs, day_before_yesterday_pcrs)
    deaths_summary = get_summary("Muertes", today_deaths, yesterday_deaths, day_before_yesterday_deaths)
    antibodies_summary = get_summary("Ag+", today_antibodies, yesterday_antibodies, day_before_yesterday_antibodies) if antibodies_available else None
    cases_summary = get_summary("Total Casos", today_cases, yesterday_cases, day_before_yesterday_cases) if antibodies_available else None

    publish_tweets([get_summary_tweet(today, pcrs_summary, antibodies_summary, cases_summary, deaths_summary)])

    logging.info("Tweets published correctly!")


def get_cases_later_day_in_file(file_path):

    cases_by_ccaa_and_date = defaultdict(dict)
    deaths_by_ccaa_and_date = defaultdict(dict)
    antibodies_by_ccaa_and_date = defaultdict(dict)
    with codecs.open(file_path, "r", "iso-8859-1") as f:
        for line in f:
            
            line_parts = line.split(",")
            ccaa = line_parts[0]

            if len(ccaa) > 2:
                continue
            
            date = datetime.strptime(line_parts[1], DATE_FORMAT)
            cases = int(line_parts[3])
            antibodies = int(line_parts[4]) if line_parts[4] else None
            deaths = int(line_parts[7] if line_parts[7] else "0")

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
    print(today_info, yesterday_info)
    today_total = sum(today_info.values()) - sum(yesterday_info.values())
    yesteday_total = sum(yesterday_info.values()) - sum(day_before_yesterday_info.values()) if day_before_yesterday_info else None
    sentence = "{0}: {1:+} {2} {3} (Totales: {4:,})".format(stat_type, today_total, get_impact_string(today_total), get_tendency_emoji(today_total, yesteday_total), sum(today_info.values())).replace(",", ".")
    return " ".join(sentence.split())


def get_summary_tweet(date, pcrs_summary, antibodies_summary, cases_summary, deaths_summary):
    items = ["Resumen España a fecha {0}:".format(date.strftime(DATE_FORMAT)), "", pcrs_summary, antibodies_summary, cases_summary, deaths_summary]
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
    current_tweet = ""
    header_format = "{0} reportadas hasta el {1} ({2}/{3}):\n\n"
    # We assume that the total amount of tweets will be 9 or less...
    header_length = tweet_length(header_format.format(stat_type, date.strftime(DATE_FORMAT), 0, 0))

    for sentence in sentences:
        # Twitter counts emoji as double characters...
        if tweet_length(current_tweet) + tweet_length(sentence) + header_length > 280:
            tweets.append(current_tweet.strip("\n"))
            current_tweet = ""
        
        current_tweet += sentence + "\n"

    tweets.append(current_tweet.strip("\n"))

    return list(map(lambda x: header_format.format(stat_type, date.strftime(DATE_FORMAT), x + 1, len(tweets)) + tweets[x], range(0, len(tweets))))


def tweet_length(sentence):
    emoji_regex = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
    return len(sentence) + len(emoji_regex.findall(sentence))


def publish_tweets(tweets):

    api = get_twitter_api()

    last_tweet = None
    for tweet in tweets:
        # last_tweet = api.update_status(tweet, last_tweet).id
        print(tweet)


def send_dm_error():
    api = get_twitter_api()
    api.send_direct_message(api.get_user("aitormagan").id, "There was an error, please, check!")


def get_twitter_api():
    auth = tweepy.OAuthHandler(os.environ.get("API_SECRET", ""),
                               os.environ.get("API_SECRET_KEY", ""))
    auth.set_access_token(os.environ.get("ACCESS_TOKEN", ""),
                          os.environ.get("ACCESS_TOKEN_SECRET", ""))
    return tweepy.API(auth)


def create_custom_file(today, yesterday, today_file, yesterday_file):
    cases = {}
    deaths = {}
    df = tabula.read_pdf(MS_PDF_FORMAT.format(get_pdf_id_for_date(today)), pages='1,2')
    
    for i in range(2, 21):
        cases[CCAA_REVERSE[df[-2]['Unnamed: 0'][i].replace('*', '')]] = int(df[-2]['Unnamed: 1'][i].replace('.', '').replace('-', '0'))
        deaths[CCAA_REVERSE[df[-1]['Unnamed: 0'][i].replace('*', '')]] = int(df[-1]['Fallecidos'][i].split(" ")[0].replace('.', '').replace('-','0'))
    
    copyfile(yesterday_file, today_file)

    rows = []
    for ccaa in cases:
        rows.append('{0},{1},,{2},,,,{3},'.format(ccaa, yesterday.strftime(DATE_FORMAT), cases[ccaa], deaths[ccaa]))
    
    with open(today_file, 'a') as f:
        f.write("\n".join(rows))

def get_pdf_id_for_date(date):
    # 14/5/2020 -> id: 105
    reference_date = datetime(2020, 5, 14)
    return 105 + (date - reference_date).days

def main():
        
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    today_file = get_path_for_date(today)
    yesterday_file = get_path_for_date(yesterday)
    day_before_yesterday_file = get_path_for_date(day_before_yesterday)

    if os.path.exists(today_file):
        try:
            # download_file(today_file)

            if os.path.getsize(today_file) <= os.path.getsize(yesterday_file):
                logging.info("File has not been updated yet...")
                os.remove(today_file)
                if today.hour >= 20:
                    logging.info("Trying to get information using the PDFs...")
                    create_custom_file(today, yesterday, today_file, yesterday_file)
                    process_file(today, today_file, yesterday_file, day_before_yesterday_file)
            else:
                process_file(today, today_file, yesterday_file, day_before_yesterday_file)
        except Exception as e:
            logging.exception("Unhandled exception while trying to publish tweets. Today file will be removed...")
            if os.path.exists(today_file):
                pass
                # os.remove(today_file)
            send_dm_error()
    else:
        logging.info("File already exists...")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)
    os.chdir(os.path.dirname(__file__))

    main()
