import requests
import codecs
import os
import tweepy
import sys
import logging
from collections import defaultdict
from datetime import datetime, timedelta

FILES_FOLDER = "covid19_data"

CCAAS = {
    "AN": "Andalucía",
    "AR": "Aragón",
    "AS": "Asturias",
    "IB": "Islas Baleares",
    "CN": "Canarias",
    "CB": "Cantabria",
    "CM": "Castilla-La Mancha",
    "CL": "Castilla y León",
    "CT": "Cataluña",
    "CE": "Ceuta",
    "VC": "Comunidad Valenciana",
    "EX": "Extremadura",
    "GA": "Galicia",
    "MD": "Madrid",
    "ML": "Melilla",
    "MC": "Murcia",
    "NC": "Navarra",
    "PV": "País Vasco",
    "RI": "La Rioja"
}


def download_file(file_path):
    r = requests.get("https://cnecovid.isciii.es/covid19/resources/agregados.csv")
    open(file_path, "wb").write(r.content)
    return file_path


def get_path_for_date(date):
    return os.path.join(FILES_FOLDER, "{0}.csv".format(date.strftime("%Y%m%d")))


def get_cases_later_day_in_file(file_path):

    cases_by_ccaa_and_date = defaultdict(dict)
    deaths_by_ccaa_and_date = defaultdict(dict)
    with codecs.open(file_path, "r", "iso-8859-1") as f:
        for line in f:
            
            line_parts = line.split(",")
            ccaa = line_parts[0]

            if len(ccaa) > 2:
                continue
            
            date = datetime.strptime(line_parts[1], "%d/%m/%Y")
            cases = int(line_parts[3])
            deaths = int(line_parts[7] if line_parts[7] else "0")

            cases_by_ccaa_and_date[date][ccaa] = cases
            deaths_by_ccaa_and_date[date][ccaa] = deaths

    later_date = max(cases_by_ccaa_and_date.keys())
    return cases_by_ccaa_and_date[later_date], deaths_by_ccaa_and_date[later_date]


def get_tweet_sentences(stat_type, date, today_cases, yesterday_cases, day_before_yesterday_cases):
    total_new_cases = sum(today_cases.values()) - sum(yesterday_cases.values())
    yesterday_new_cases = sum(yesterday_cases.values()) - sum(day_before_yesterday_cases.values())
    sentences = ["{0} reportadas hasta el {1} (+{2} {3}):".format(stat_type, date.strftime("%d/%m/%Y"), total_new_cases, get_tendency_emoji(total_new_cases, yesterday_new_cases)), ""]
    for ccaa in today_cases:
        ccaa_yesterday_cases = yesterday_cases[ccaa] - day_before_yesterday_cases[ccaa]
        ccaa_new_cases = today_cases[ccaa] - yesterday_cases[ccaa]
        ccaa_percentage = 100 * ccaa_new_cases / total_new_cases
        sentences.append("{0}: +{1} ({2:.2f} %) {3}".format(CCAAS[ccaa], ccaa_new_cases, ccaa_percentage, get_tendency_emoji(ccaa_new_cases, ccaa_yesterday_cases)))
    
    return sentences


def get_tendency_emoji(today_number, yesterday_number):
    if today_number > yesterday_number:
        return '🔺'
    elif yesterday_number > today_number:
        return '🔻'
    else:
        return '🔙'


def get_tweets(sentences):
    tweets = []
    current_tweet = ""
    for sentence in sentences:
        sentence += "\n"
        if len(current_tweet) + len(sentence) < 280:
            current_tweet += sentence
        else:
            tweets.append(current_tweet)
            current_tweet = sentence

    tweets.append(current_tweet)

    return tweets


def publish_tweets(tweets):

    auth = tweepy.OAuthHandler("API_SECRET", 
                               "API_SECRET_KEY")
    auth.set_access_token("ACCESS_TOKEN", 
                          "ACCESS_TOKEN_SECRET")

    last_tweet = None
    for tweet in tweets:
        api = tweepy.API(auth)
        last_tweet = api.update_status(tweet, last_tweet).id

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)
    os.chdir(os.path.dirname(__file__))
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    today_file = get_path_for_date(today)
    yesterday_file = get_path_for_date(yesterday)
    day_before_yesterday_file = get_path_for_date(day_before_yesterday)

    if not os.path.exists(today_file):
        download_file(today_file)

        if os.path.getsize(today_file) == os.path.getsize(yesterday_file):
            logging.info("File has not been updated yet...")
            os.remove(today_file)
        else:
            today_cases, today_deaths = get_cases_later_day_in_file(today_file)
            yesterday_cases, yesterday_deaths = get_cases_later_day_in_file(yesterday_file)
            day_before_yesrday_cases, day_before_yesterday_deaths = get_cases_later_day_in_file(day_before_yesterday_file)
            
            cases_sentences = get_tweet_sentences("PCR+", today, today_cases, yesterday_cases, day_before_yesrday_cases)
            cases_tweets = get_tweets(cases_sentences)
            publish_tweets(cases_tweets)


            deaths_sentences = get_tweet_sentences("Muertes", today, today_deaths, yesterday_deaths, day_before_yesterday_deaths)
            deaths_tweets = get_tweets(deaths_sentences)
            publish_tweets(deaths_tweets)

            logging.info("Tweets published correctly!")
    else:
        logging.info("File already exists...")
