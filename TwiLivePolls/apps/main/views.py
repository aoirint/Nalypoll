from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
import requests
from requests_oauthlib import OAuth1Session, OAuth1
from urllib.parse import urlparse, parse_qsl
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed

from tweetutil import get_tweets
from validateutil import TWEET_ID_OR_URL_PATTERN
from main.models import *
from main.forms import *

# Create your views here.
def index(request):
    form = RegisterForm(initial={
    })

    screen_name = request.session.get('screen_name')

    # TODO: User auth & limit to register user's own tweets only
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
            else:
                access_token = request.session.get('access_token')
                access_token_secret = request.session.get('access_token_secret')

                oauth = OAuth1(
                    client_key=settings.TWITTER_API_KEY,
                    client_secret=settings.TWITTER_API_SECRET,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret,
                )

                checked_at = timezone.now()
                tweets = get_tweets(ids=[ str(tweet_id), ], oauth=oauth)
                if len(tweets) != 0:
                    tweet = tweets[0]

                    # TODO: make cache to ignore no poll tweet
                    if len(tweet.polls) != 0:
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
        'screen_name': screen_name,
    })

# show recent tweets
def user(request):
    pass

# TODO: user can set public/private poll dynamics or random id?
# public view
def view(request, tweet_id: int):
    tweet = Tweet.objects.get(remote_id=tweet_id)

    print(tweet.last_polls)

    return render(request, 'view.html', {
        'tweet_id': tweet_id,
        'tweet': tweet,
    })

# temporary
def update(request, tweet_id: int):
    checked_at = timezone.now()
    tweets = get_tweets(ids=[ str(tweet_id), ], bearer_token=settings.TWITTER_TOKEN)
    if len(tweets) != 0:
        tweet = tweets[0]

        if len(tweet.polls) != 0:
            tweet_update = TweetUpdate.update_or_create(tweet, checked_at)
            tweet_update.save()

    return redirect('main:view', tweet_id=tweet_id)


def oauth(request):
    callback_url = 'http://localhost:8000/oauth/callback'
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    # auth_url = 'https://api.twitter.com/oauth/authorize'
    auth_url = 'https://api.twitter.com/oauth/authenticate'

    if request.method != 'POST':
        # return HttpResponseNotAllowed([ 'POST', ], content='Method Not Allowed')
        return redirect('main:index') # Method Not Allowed

    session = OAuth1Session(
        client_key=settings.TWITTER_API_KEY,
        client_secret=settings.TWITTER_API_SECRET,
        callback_uri=callback_url,
    )

    token = session.fetch_request_token(request_token_url)
    oauth_token = token.get('oauth_token')
    oauth_token_secret = token.get('oauth_token_secret')

    paramed_auth_url = session.authorization_url(auth_url)
    response = redirect(paramed_auth_url)

    response.set_cookie('oauth_token', oauth_token,
        max_age=90, httponly=True,
        # secure=True,
    )
    response.set_cookie('oauth_token_secret', oauth_token_secret,
        max_age=90, httponly=True,
        # secure=True,
    )
    return response

# redirected from twitter.com
def oauth_callback(request):
    access_token_url = 'https://api.twitter.com/oauth/access_token'

    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')
    oauth_token_secret = request.COOKIES.get('oauth_token_secret')

    session = OAuth1Session(
        client_key=settings.TWITTER_API_KEY,
        client_secret=settings.TWITTER_API_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
    )

    token = session.fetch_access_token(access_token_url, verifier=oauth_verifier)

    request.session['user_id'] = token.get('user_id')
    request.session['screen_name'] = token.get('screen_name')
    request.session['access_token'] = token.get('oauth_token')
    request.session['access_token_secret'] = token.get('oauth_token_secret')

    return redirect('main:index')
