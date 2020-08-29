from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import requests

from tweetutil import get_tweets
from validateutil import TWEET_ID_OR_URL_PATTERN
from main.models import *
from main.forms import *

# Create your views here.
def index(request):
    form = RegisterForm(initial={
    })

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            tweet_id_or_url = form.cleaned_data['tweet_id_or_url']
            m = TWEET_ID_OR_URL_PATTERN.match(tweet_id_or_url)
            tweet_id = m.group('id') or m.group('id_in_url')
            assert tweet_id

            tweet_id = int(tweet_id)

            do_redirect = False
            _tweet = Tweet.objects.filter(remote_id=tweet_id).first()
            if _tweet is not None:
                do_redirect = True

            checked_at = timezone.now()
            tweets = get_tweets(ids=[ str(tweet_id), ])
            if len(tweets) != 0:
                tweet = tweets[0]

                # TODO: to use shared task pool (to reduce API call)
                # TODO: scheduled data updater
                tweet_update = TweetUpdate.update_or_create(tweet, checked_at)
                tweet_update.save()

                do_redirect = True

            if do_redirect:
                return redirect('main:view', tweet_id=tweet_id)
        else:
            print('invalid')

    return render(request, 'index.html', {
        'form': form,
    })

def view(request, tweet_id: int):
    tweet = Tweet.objects.get(remote_id=tweet_id)

    print(tweet.last_polls)

    return render(request, 'view.html', {
        'tweet_id': tweet_id,
        'tweet': tweet,
    })
