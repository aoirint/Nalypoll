from pathlib import Path
import os
import sys
sys.path.append(str(Path(__file__).resolve(strict=True).parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TwiAnalyPolls.settings')

import django
django.setup()

from django.utils import timezone
from django.db import connection

import time
from datetime import timedelta
from itertools import islice

from main.models import *
from tweetutil import TwitterSessionBearer

@dataclass
class PollUpdater:
    delta_check_tweets: timedelta = timedelta(minutes=15)
    delta_check_users: timedelta = timedelta(hours=6)
    # Twitter API Limit per one call = 100: https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
    tweet_chunk_size: int = 100
    # Twitter API Limit per one call = 100: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users
    user_chunk_size: int = 100
    # one try timeout
    api_timeout: float = 3.0
    request_interval: float = 3.0
    twitter_bearer = TwitterSessionBearer()

    def update(self):
        print('%s: Updating' % timezone.now())

        self.check_tweet_update()
        self.check_user_update()

        print('%s: Done' % timezone.now())

        connection.close() # explicitly close connection

    def check_tweet_update(self):
        tweets_with_open_poll = Tweet.objects.filter(
            registered_user__isnull=False,
            author__protected=False,
            is_poll_open=True,
            last_checked_at__lt=timezone.now() - self.delta_check_tweets,
        )

        tweets_with_open_poll_iter = iter(tweets_with_open_poll)

        while tweet_chunk := list(islice(tweets_with_open_poll_iter, self.tweet_chunk_size)):
            tweet_remote_ids = [ tweet.remote_id for tweet in tweet_chunk ]
            self.twitter_bearer.update_tweets(tweet_ids=tweet_remote_ids, timeout=self.api_timeout)

            print(tweet_chunk)
            time.sleep(self.request_interval)

    def check_user_update(self):
        # check if user is protected
        users_recent_unchecked = TwitterUser.objects.filter(
            checked_at__lt=timezone.now() - self.delta_check_users,
        )

        users_recent_unchecked_iter = iter(users_recent_unchecked)

        user_chunk_size = 100
        while user_chunk := list(islice(users_recent_unchecked_iter, self.user_chunk_size)):
            user_remote_ids = [ user.remote_id for user in user_chunk ]
            self.twitter_bearer.update_users(user_ids=user_remote_ids, timeout=self.api_timeout)

            print(user_chunk)
            time.sleep(self.request_interval)


if __name__ == '__main__':
    import schedule

    updater = PollUpdater(
        delta_check_tweets=timedelta(minutes=1),
        delta_check_users=timedelta(minutes=1),
    )

    schedule.every(15).minutes.do(updater.update)

    print('%s: Start waiting' % timezone.now())
    while True:
        schedule.run_pending()
        time.sleep(1)
