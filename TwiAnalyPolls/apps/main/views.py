from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse, Http404

import re
import requests
import requests_oauthlib
from urllib.parse import urlparse, parse_qsl

from tweetutil import TwitterSessionOAuth
from validateutil import TWEET_ID_OR_URL_PATTERN
from main.models import *
from main.forms import *

# Create your views here.
def index(request):
    twitter = TwitterSessionOAuth(request)

    return render(request, 'index.html', {
        'twitter': twitter,
    })

# show recent tweets
def me(request):
    twitter = TwitterSessionOAuth(request)

    if not twitter.is_authenticated():
        return redirect('main:index')

    if request.method == 'POST':
        tweet_id = request.POST.get('tweet_id')

        # validation
        if not re.match(r'^\d+$', tweet_id):
            return HttpResponseBadRequest()

        # already registered
        if Poll.objects.filter(tweet__remote_id=tweet_id).count() != 0:
            return redirect('main:poll', tweet_id)

        tweets: List[Tweet] = twitter.update_tweets(tweet_ids=[ tweet_id, ])
        if len(tweets) == 0:
            return HttpResponseBadRequest() # invalid tweet ID or other user's tweet ID

        return redirect('main:poll', tweet_id)


    root: Dict = twitter.get_recent_my_tweets(raw=True)
    tweets: List[Dict] = root.get('data', [])
    includes: Dict = root.get('includes', {})
    polls: List[Dict] = includes.get('polls', [])
    pollid2poll: Dict[str, Dict] = { poll['id']: poll for poll in polls }
    users: List[Dict] = includes.get('users', [])
    userid2user: Dict[str, Dict] = { user['id']: user for user in users }

    for poll in polls:
        poll['registered'] = Poll.objects.filter(remote_id=poll['id']).first() is not None

        poll['total_votes'] = sum([ option['votes'] for option in poll['options'] ])
        for option in poll['options']:
            option['rate'] = option['votes'] / poll['total_votes'] if poll['total_votes'] != 0 else 0.0
            option['percentage'] = option['rate'] * 100

    for tweet in tweets:
        poll_ids = tweet.get('attachments', {}).get('poll_ids', [])
        tweet['author'] = userid2user[tweet['author_id']]
        tweet['polls'] = [ pollid2poll[poll_id] for poll_id in poll_ids ]

    return render(request, 'me.html', {
        'tweets': tweets,
        'twitter': twitter,
    })

# user menu
def menu(request):
    twitter = TwitterSessionOAuth(request)

    if not twitter.is_authenticated():
        return redirect('main:index')

    return render(request, 'menu.html', {
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

def remove_user_polls(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed([ 'POST', ], content='Method Not Allowed')

    twitter = TwitterSessionOAuth(request)
    if not twitter.is_authenticated():
        return HttpResponse('Forbidden', code=403)

    user_id = twitter.user_id
    Poll.objects.filter(tweet__author__remote_id=user_id).delete()

    return redirect('main:menu')

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

    return redirect('main:me')

# remove tokens from DB
def oauth_remove(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed([ 'POST', ], content='Method Not Allowed')

    twitter = TwitterSessionOAuth(request)

    response = redirect('main:index')
    twitter.remove_oauth(response)

    return response

# remove tokens from user session
def oauth_logout(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed([ 'POST', ], content='Method Not Allowed')

    twitter = TwitterSessionOAuth(request)

    response = redirect('main:index')
    twitter.logout(response)

    return response
