import os
import re
from tempfile import NamedTemporaryFile
import tweepy
import requests


class Twitter:

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            auth = tweepy.OAuthHandler(os.environ.get("API_SECRET", ""),
                                       os.environ.get("API_SECRET_KEY", ""))
            auth.set_access_token(os.environ.get("ACCESS_TOKEN", ""),
                                  os.environ.get("ACCESS_TOKEN_SECRET", ""))
            self._client = tweepy.API(auth)

        return self._client

    def publish_tweets(self, sentences, header=None):
        tweets = self._split_tweets(sentences, header)
        self._publish_tweets(tweets)

    def _split_tweets(self, sentences, header=None):
        tweets = []

        header_format = header + " ({0}/{1}):\n\n" if header else ""
        # We assume that the total amount of tweets will be 9 or less...
        header_length = self._get_tweet_length(header_format.format(0, 0))

        current_tweet = ""
        for sentence in sentences:
            # Twitter counts emoji as double characters...
            if self._get_tweet_length(current_tweet) + self._get_tweet_length(sentence) + header_length > 280:
                tweets.append(current_tweet.strip("\n"))
                current_tweet = ""

            current_tweet += sentence + "\n"

        tweets.append(current_tweet.strip("\n"))
        tweets = list(filter(lambda x: x, tweets))

        return list(map(lambda x: header_format.format(x + 1, len(tweets)) + tweets[x], range(0, len(tweets))))

    @staticmethod
    def _get_tweet_length(sentence):
        emoji_regex = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
        return len(sentence) + len(emoji_regex.findall(sentence))

    def _publish_tweets(self, tweets):
        last_tweet = None
        for tweet in tweets:
            last_tweet = self.client.update_status(tweet, last_tweet).id

    def send_dm(self, dm):
        self.client.send_direct_message(self.client.get_user("aitormagan").id, dm)

    def publish_tweet_with_media(self, tweet, media_url):
        with NamedTemporaryFile(suffix=".png") as temp_file:
            self._download_file(media_url, temp_file)
            self.client.update_with_media(temp_file.name, tweet)

    @staticmethod
    def _download_file(media_url, file):
        get_request = requests.get(media_url)

        if get_request.status_code == 200:
            for chunk in get_request:
                file.write(chunk)

            file.flush()
        else:
            raise Exception("File could not be downloaded")
