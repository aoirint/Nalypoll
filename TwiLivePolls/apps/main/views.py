from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import requests

from tweetutil import get_tweets
from main.models import *

# Create your views here.
def index(request):
    return render(request, 'index.html', {
    })

def view(request, tweet_id: int):
    checked_at = timezone.now()

    tweets = Tweet.objects.all()
    print(tweets)

    tweets = get_tweets(ids=[ str(tweet_id), ])
    tweet = tweets[0]

    class DummyException(Exception):
        pass

    try:
        with transaction.atomic():
            tweet_update = TweetUpdate.update_or_create(tweet, checked_at)
            raise DummyException
    except DummyException:
        pass

    return render(request, 'view.html', {
        'tweet_id': tweet_id,
        'tweet_update': tweet_update,
    })
