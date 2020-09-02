from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse, Http404
from django.views.decorators.http import require_http_methods

import re
import requests
import requests_oauthlib
from urllib.parse import urlparse, parse_qsl

from tweetutil import TwitterSessionOAuth, TwitterSessionBearer
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
    twitter_bearer = TwitterSessionBearer(request)
    current_user = twitter.current_user

    if not twitter.is_authenticated():
        return redirect('main:index')

    if request.method == 'POST':
        tweet_id = request.POST.get('tweet_id')

        # validation
        if not re.match(r'^\d+$', tweet_id):
            return HttpResponseBadRequest()

        tweet = Tweet.objects.filter(
            remote_id=tweet_id,
            # author=current_user,
        ).first()

        if tweet is not None and tweet.registered_user == current_user:
            return redirect('main:poll', tweet_id)

        if tweet is None or tweet.registered_user is None:
            user_id_filter = [ current_user.remote_id ]
            if settings.CAN_REGISTER_ALL_TWEET:
                user_id_filter = []

            tweets = twitter_bearer.update_tweets(
                tweet_ids=[ tweet_id ],
                user_id_filter=user_id_filter,
            )
            if len(tweets) == 0:
                # invalid request
                return HttpResponseBadRequest() # forbidden or badrequest, protected user

            tweet = tweets[0]

        assert tweet is not None
        tweet.registered_user = current_user
        tweet.save()

        return redirect('main:poll', tweet_id)


    root: Dict = twitter_bearer.get_recent_user_tweets(current_user.remote_id, raw=True)

    tweets: List[Dict] = root.get('data', [])
    includes: Dict = root.get('includes', {})
    polls: List[Dict] = includes.get('polls', [])
    pollid2poll: Dict[str, Dict] = { poll['id']: poll for poll in polls }
    users: List[Dict] = includes.get('users', [])
    userid2user: Dict[str, Dict] = { user['id']: user for user in users }

    for poll in polls:
        poll['total_votes'] = sum([ option['votes'] for option in poll['options'] ])
        for option in poll['options']:
            option['rate'] = option['votes'] / poll['total_votes'] if poll['total_votes'] != 0 else 0.0
            option['percentage'] = option['rate'] * 100

    for tweet in tweets:
        _tweet = Tweet.objects.filter(remote_id=tweet['id']).first()

        poll_ids = tweet.get('attachments', {}).get('poll_ids', [])
        tweet['author'] = userid2user[tweet['author_id']]
        tweet['polls'] = [ pollid2poll[poll_id] for poll_id in poll_ids ]
        tweet['registered'] = _tweet is not None and _tweet.registered_user == current_user

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

    if not twitter.is_authenticated():
        return redirect('main:index')

    tweet = Tweet.objects.filter(
        remote_id=tweet_id,
        author__remote_id=twitter.user_id,
        poll__isnull=False,
        # author__protected=False,
    ).distinct().first()
    if tweet is None:
        raise Http404('Not Found')

    return render(request, 'poll.html', {
        'tweet_id': tweet_id,
        'tweet': tweet,
        'twitter': twitter,
    })

@require_http_methods([ 'POST' ])
def remove_poll(request, tweet_id: int):
    twitter = TwitterSessionOAuth(request)

    if not twitter.is_authenticated():
        return redirect('main:index')

    tweet = Tweet.objects.filter(
        remote_id=tweet_id,
        author__remote_id=twitter.user_id,
        poll__isnull=False,
        # author__protected=False,
    ).distinct().first()

    if tweet is None:
        return HttpResponseBadRequest()

    tweet.delete()
    return redirect('main:me')

@require_http_methods([ 'POST' ])
def remove_user_polls(request):
    twitter = TwitterSessionOAuth(request)
    if not twitter.is_authenticated():
        return HttpResponse('Forbidden', code=403)

    current_user = twitter.current_user

    Poll.objects.filter(tweet__author=current_user).delete()

    for tweet in Tweet.objects.filter(registered_user=current_user):
        tweet.registered_user = None
        tweet.save()

    return redirect('main:menu')

# temporary
def update(request, tweet_id: int):
    twitter = TwitterSessionOAuth(request)
    twitter_bearer = TwitterSessionBearer(request)

    tweets: List[Tweet] = twitter_bearer.update_tweets(tweet_ids=[ str(tweet_id), ])

    return redirect('main:poll', tweet_id=tweet_id)


# start oauth (redirect to twitter.com)
@require_http_methods([ 'POST' ])
def oauth(request):
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
@require_http_methods([ 'POST' ])
def oauth_remove(request):
    twitter = TwitterSessionOAuth(request)

    response = redirect('main:index')
    twitter.remove_oauth(response)

    return response

# remove tokens from user session
@require_http_methods([ 'POST' ])
def oauth_logout(request):
    twitter = TwitterSessionOAuth(request)

    response = redirect('main:index')
    twitter.logout(response)

    return response
