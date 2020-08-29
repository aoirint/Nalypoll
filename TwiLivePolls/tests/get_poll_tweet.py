import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TwiLivePolls.settings')

import django
django.setup()

import unittest

import requests
from tweetutil import get_tweets

class TestGetPollTweet(unittest.TestCase):
    def test_get_invalid(self):
        tweets = get_tweets(ids=[ '1', ])
        print(tweets)

    def test_get_invalid_partial(self):
        tweets = get_tweets(ids=[ '1', '1071224244627861504', ])
        print(tweets)

    def test_get(self):
        tweets = get_tweets(ids=[ '1071224244627861504', '1299547404178305024', ])
        print(tweets)

    def test_server_down_exception(self):
        with self.assertRaises(requests.exceptions.Timeout):
            tweets = get_tweets(ids=[ '1071224244627861504', '1299547404178305024', ], timeout=0.000001)

if __name__ == '__main__':
    unittest.main()
