from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
import requests
import requests_oauthlib
from urllib.parse import urlparse, parse_qsl
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse, Http404

from tweetutil import TwitterSessionOAuth
from validateutil import TWEET_ID_OR_URL_PATTERN
from main.models import *
from main.forms import *

# Create your views here.
def index(request):
    twitter = TwitterSessionOAuth(request)

    form = RegisterForm(initial={
    })

    # TODO: User auth & limit to register user's own tweets only
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            tweet_id_or_url = form.cleaned_data['tweet_id_or_url']
            m = TWEET_ID_OR_URL_PATTERN.match(tweet_id_or_url)
            tweet_id = m.group('id') or m.group('id_in_url')
            assert tweet_id

            tweets: List[Tweet] = twitter.update_tweets(tweet_ids=[ tweet_id, ])

            if len(tweets) != 0:
                return redirect('main:poll', tweet_id=tweet_id)

    return render(request, 'index.html', {
        'form': form,
        'twitter': twitter,
    })

# show recent tweets
def user(request):
    twitter = TwitterSessionOAuth(request)

    if not twitter.is_authenticated():
        return redirect('main:index')

    return render(request, 'index.html', {
        'form': form,
        'twitter': twitter,
    })

# TODO: user can set public/private poll dynamics or random id?
# public view
def poll(request, tweet_id: int):
    twitter = TwitterSessionOAuth(request)

    tweet = Tweet.objects.filter(remote_id=tweet_id, poll__isnull=False).distinct().first()
    if tweet is None:
        raise Http404('Not Found')

    return render(request, 'poll.html', {
        'tweet_id': tweet_id,
        'tweet': tweet,
        'twitter': twitter,
    })

# temporary
def update(request, tweet_id: int):
    twitter = TwitterSessionOAuth(request)

    tweets: List[Tweet] = twitter.update_tweets(tweet_ids=[ str(tweet_id), ])

    return redirect('main:poll', tweet_id=tweet_id)


# start oauth (redirect to twitter.com)
def oauth(request):
    if request.method != 'POST':
        # return HttpResponseNotAllowed([ 'POST', ], content='Method Not Allowed')
        return redirect('main:index') # Method Not Allowed

    twitter = TwitterSessionOAuth(request)
    try:
        response = twitter.start_oauth()
    except requests_oauthlib.oauth1_session.TokenRequestDenied as err:
        return HttpResponse('Token request to Twitter failed with code %d.' % err.status_code, status=400)

    return response

# redirected from twitter.com
def oauth_callback(request):
    twitter = TwitterSessionOAuth(request)

    try:
        twitter.on_oauth_callback()
    except requests_oauthlib.oauth1_session.TokenRequestDenied as err:
        # Token request failed with code 401, response was '現在この機能は一時的にご利用いただけません'
        return HttpResponse('Token request to Twitter failed with code %d.' % err.status_code, status=400)

    return redirect('main:index')
