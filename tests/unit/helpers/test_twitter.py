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
        twitter._split_tweets = MagicMock()
        twitter._publish_tweets = MagicMock()
        sentences = MagicMock()
        header = MagicMock()

        twitter.publish_tweets(sentences, header)

        twitter._split_tweets.assert_called_once_with(sentences, header)
        twitter._publish_tweets.assert_called_once_with(twitter._split_tweets.return_value)

    def test_given_one_short_sentence_without_header_when_split_tweets_then_one_tweet_returned(self):

        sentence = "this is a shot sentence"
        sentences = [sentence]
        twitter = Twitter()

        result = twitter._split_tweets(sentences, None)

        self.assertEqual(sentences, result)

    def test_given_one_short_sentence_with_header_when_split_tweets_then_sentence_with_header_returned(self):

        sentence = "this is a shot sentence"
        header = "this is a header"
        sentences = [sentence]
        twitter = Twitter()

        result = twitter._split_tweets(sentences, header)

        self.assertEqual([header + " (1/1):\n\n" + sentence], result)

    def test_given_sentences_with_length_below_280_with_header_when_split_tweets_then_one_tweet_returned(self):
        sentence1 = "this is a shot sentence"
        sentence2 = "this is another sentence"
        header = "this is a header"
        sentences = [sentence1, sentence2]
        twitter = Twitter()

        result = twitter._split_tweets(sentences, header)

        self.assertEqual([header + " (1/1):\n\n" + sentence1 + "\n" + sentence2], result)

    def test_given_sentences_with_length_above_280_with_header_when_split_tweets_then_two_tweet_returned(self):
        sentence = "this is a shot sentence"
        header = "this is a header"
        sentences = 20 * [sentence]
        twitter = Twitter()

        result = twitter._split_tweets(sentences, header)

        self.assertEqual(2, len(result))
        self.assertTrue(result[0].startswith(header + " (1/2):\n\n"))
        self.assertTrue(result[1].startswith(header + " (2/2):\n\n"))

    def test_no_emoji_in_text_when_get_tweet_length_then_normal_length_returned(self):
        twitter = Twitter()
        sentence = "this is a test"

        self.assertEqual(len(sentence), twitter._get_tweet_length(sentence))

    def test_one_emoji_in_text_when_get_tweet_length_then_length_plus_1_returned(self):
        twitter = Twitter()
        sentence = "this is a test 🔺"

        self.assertEqual(len(sentence) + 1, twitter._get_tweet_length(sentence))

    def test_given_tweets_when_publish_tweets_then_client_called(self):
        with patch.object(Twitter, 'client'):
            twitter = Twitter()
            twitter.client = MagicMock()

            tweet1 = "text1"
            tweet2 = "text2"
            tweets = [tweet1, tweet2]

            twitter._publish_tweets(tweets)

            twitter.client.update_status.assert_has_calls([call(tweet1, None),
                                                           call(tweet2, twitter.client.update_status.return_value.id)])

    def test_when_send_dm_error_then_send_dm_error_called(self):
        with patch.object(Twitter, 'client'):
            twitter = Twitter()
            twitter.client = MagicMock()

            twitter.send_dm_error()

            twitter.client.get_user.assert_called_once_with("aitormagan")
            twitter.client.send_direct_message(twitter.client.get_user.return_value.id,
                                               "There was an error, please, check!")
