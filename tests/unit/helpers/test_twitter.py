import unittest
from unittest.mock import patch, call, MagicMock
from helpers.twitter import Twitter


class TwitterUnitTest(unittest.TestCase):

    @patch("helpers.twitter.tweepy")
    @patch("helpers.twitter.os")
    def test_given_no_client_when_get_client_then_client_is_built(self, os_mock, tweepy_mock):
        twitter = Twitter()

        client = twitter.client

        self.assertEqual(client, tweepy_mock.API.return_value)
        tweepy_mock.API.assert_called_once_with(tweepy_mock.OAuthHandler.return_value)
        tweepy_mock.OAuthHandler.assert_called_once_with(os_mock.environ.get.return_value,
                                                         os_mock.environ.get.return_value)
        tweepy_mock.OAuthHandler.return_value.set_access_token.assert_called_once_with(os_mock.environ.get.return_value,
                                                                                       os_mock.environ.get.return_value)
        os_mock.environ.get.assert_has_calls([call("API_SECRET", ""),
                                              call("API_SECRET_KEY", ""),
                                              call("ACCESS_TOKEN", ""),
                                              call("ACCESS_TOKEN_SECRET", "")])

    def test_when_publish_tweets_then_split_and_publish(self):
        twitter = Twitter()
        tweet1_id = 123
        tweet2_id = 456
        tweet1 = "test1"
        tweet2 = "test2"
        twitter.publish_tweet = MagicMock(side_effect=[tweet1_id, tweet2_id])
        tweets = [tweet1, tweet2]

        last_tweet_id = twitter.publish_tweets(tweets)

        self.assertEqual(tweet2_id, last_tweet_id)
        twitter.publish_tweet.assert_has_calls([call(tweet1, None),
                                                call(tweet2, tweet1_id)])

    def test_given_tweet_when_publish_tweet_then_client_called(self):
        with patch.object(Twitter, 'client'):
            twitter = Twitter()
            twitter.client = MagicMock()
            tweet = MagicMock()
            in_response_to = MagicMock()

            tweet_id = twitter.publish_tweet(tweet, in_response_to)

            self.assertEqual(twitter.client.update_status.return_value.id, tweet_id)
            twitter.client.update_status.assert_called_once_with(tweet, in_response_to)

    def test_when_send_dm_error_then_send_dm_called(self):
        with patch.object(Twitter, 'client'):
            twitter = Twitter()
            twitter.client = MagicMock()
            dm = "example"

            twitter.send_dm(dm)

            twitter.client.get_user.assert_called_once_with("aitormagan")
            twitter.client.send_direct_message(twitter.client.get_user.return_value.id, dm)

    @patch("helpers.twitter.NamedTemporaryFile")
    def test_given_url_and_text_when_publish_with_media_then_file_downloaded_and_tweet_published(self, temp_file_mock):
        with patch.object(Twitter, 'client'):
            twitter = Twitter()
            twitter.client = MagicMock()
            twitter._download_file = MagicMock()
            url = "http://example.com/file.jpg"
            text = "this is an example"
            in_response_to = MagicMock()

            tweet_id = twitter.publish_tweet_with_media(text, url, in_response_to)

            self.assertEqual(twitter.client.update_with_media.return_value.id, tweet_id)
            temp_file_mock.assert_called_once_with(suffix=".png")

            with temp_file_mock.return_value as temp_file:
                twitter._download_file.assert_called_once_with(url, temp_file)
                twitter.client.update_with_media.assert_called_once_with(temp_file.name, text,
                                                                         in_reply_to_status_id=in_response_to)

    @patch("helpers.twitter.requests")
    def test_given_file_cannot_be_downloaded_when_download_file_then_exception_risen(self, requests_mock):
        requests_mock.get.return_value.status_code = 500
        url = MagicMock()

        with self.assertRaises(Exception):
            Twitter._download_file(url, MagicMock())

        requests_mock.get.assert_called_once_with(url)

    @patch("helpers.twitter.requests")
    def test_given_file_can_be_downloaded_when_download_file_then_file_is_written(self, requests_mock):
        chunk1 = MagicMock()
        chunk2 = MagicMock()
        requests_mock.get.return_value.status_code = 200
        requests_mock.get.return_value.__iter__ = lambda x: iter([chunk1, chunk2])
        url = MagicMock()
        file = MagicMock()

        Twitter._download_file(url, file)

        requests_mock.get.assert_called_once_with(url)
        file.write.assert_has_calls([call(chunk1), call(chunk2)])
        file.flush.assert_called_once_with()
