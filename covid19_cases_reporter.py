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

    cases_by_day_and_date = defaultdict(dict)
    with codecs.open(file_path, "r", "iso-8859-1") as f:
        for line in f:
            
            line_parts = line.split(",")
            ccaa = line_parts[0]

            if len(ccaa) > 2:
                continue
            
            date = datetime.strptime(line_parts[1], "%d/%m/%Y")
            cases = int(line_parts[3])

            cases_by_day_and_date[date][ccaa] = cases

    later_date = max(cases_by_day_and_date.keys())
    return cases_by_day_and_date[later_date]


def get_tweet_sentences(date, cases_later_date, cases_day_before_later_date):
    total_new_cases = sum(cases_later_date.values()) - sum(cases_day_before_later_date.values())
    sentences = ["Casos reportados hasta el {0} (+{1}):".format(date.strftime("%d/%m/%Y"), total_new_cases), ""]
    for ccaa in cases_later_date:
        ccaa_new_cases = cases_later_date[ccaa] - cases_day_before_later_date[ccaa]
        ccaa_percentage = 100 * ccaa_new_cases / total_new_cases
        sentences.append("{0}: +{1} ({2:.2f} %)".format(CCAAS[ccaa], ccaa_new_cases, ccaa_percentage))
    
    return sentences

def get_tweets(sentences):
    tweets = []
    current_tweet = ""
    for sentence in sentences:
        sentence += "\n"
        if len(current_tweet) + len(sentence) < 240:
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

    today_file = get_path_for_date(today)
    yesterday_file = get_path_for_date(yesterday)

    if not os.path.exists(today_file):
        download_file(today_file)

        if os.path.getsize(today_file) == os.path.getsize(yesterday_file):
            logging.info("File has not been updated yet...")
            os.remove(today_file)
        else:
            cases_later_date = get_cases_later_day_in_file(today_file)
            cases_day_before_later_date = get_cases_later_day_in_file(yesterday_file)
            sentences = get_tweet_sentences(today, cases_later_date, cases_day_before_later_date)
            tweets = get_tweets(sentences)
            publish_tweets(tweets)
            logging.info("Tweets published correctly!")
    else:
        logging.info("File already exists...")
