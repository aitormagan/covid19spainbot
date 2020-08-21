import os
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

    def publish_tweets(self, tweets):
        last_tweet = None
        for tweet in tweets:
            last_tweet = self.publish_tweet(tweet, last_tweet)

        return last_tweet

    def publish_tweet(self, tweet, in_response_to=None):
        return self.client.update_status(tweet, in_response_to).id

    def send_dm(self, dm):
        self.client.send_direct_message(self.client.get_user("aitormagan").id, dm)

    def publish_tweet_with_media(self, tweet, media_url, in_response_to=None):
        with NamedTemporaryFile(suffix=".png") as temp_file:
            self._download_file(media_url, temp_file)
            return self.client.update_with_media(temp_file.name, tweet, in_reply_to_status_id=in_response_to).id

    @staticmethod
    def _download_file(media_url, file):
        get_request = requests.get(media_url)

        if get_request.status_code == 200:
            for chunk in get_request:
                file.write(chunk)

            file.flush()
        else:
            raise Exception("File could not be downloaded")
