from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import Tuple, List, Dict

from datetime import datetime, timedelta
from dateutil.parser import isoparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import requests_oauthlib
from requests_oauthlib import OAuth1Session, OAuth1
from urllib.parse import urlparse, parse_qsl

from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone

from main.models import *

class TwitterSession:
    def __init__(self):
        retry = Retry(
            total=5,
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry)
        http = requests.Session()
        http.mount('https://', adapter)
        http.mount('http://', adapter)

        self.http_session = http

    def is_authenticated(self) -> bool:
        return False



    def call_api_tweets(self,
        tweet_ids: List[str],
        timeout: float = 3.0,
    ) -> Dict:
        if not self.is_authenticated():
            raise Exception('Not Authorized')

        tweet_ids = [ str(int(tweet_id)) for tweet_id in tweet_ids ] # validate

        url = 'https://api.twitter.com/2/tweets'
        params = {
            'ids': ','.join(tweet_ids),
            'tweet.fields': 'public_metrics,created_at',
            'poll.fields': 'duration_minutes,end_datetime,voting_status',
            'user.fields': 'protected',
            'expansions': 'attachments.poll_ids,author_id',
        }

        return self.http_session.get(url, params=params, timeout=timeout)

    def call_api_recent_search(self,
        query: str,
        max_results: int = 10,
        timeout: float = 3.0,
    ) -> Dict:
        if not self.is_authenticated():
            raise Exception('Not Authorized')

        url = 'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': query,
            'max_results': max_results,
            'tweet.fields': 'public_metrics,created_at',
            'poll.fields': 'duration_minutes,end_datetime,voting_status',
            'user.fields': 'protected',
            'expansions': 'attachments.poll_ids,author_id',
        }

        return self.http_session.get(url, params=params, timeout=timeout)



    def _update_users(self,
        users: List[Dict],
        user_id_filter: List[str],
        checked_at: datetime,
    ) -> List[TwitterUser]:
        _users: List[TwitterUser] = []

        for user in users:
            remote_id = user['id']
            if user_id_filter is not None and remote_id not in user_id_filter:
                continue

            _user = TwitterUser.objects.filter(remote_id=remote_id).first()
            if _user is None:
                _user = TwitterUser(remote_id=remote_id)

            _user.screen_name = user['username']
            _user.name = user['name']
            _user.protected = user['protected']
            _user.checked_at = checked_at

            _user.save()
            _users.append(_user)

        return _users

    def _update_public_metrics(self,
        tweet: Tweet,
        public_metrics: Dict,
        checked_at: datetime,
    ) -> PublicMetrics:
        _public_metrics = PublicMetrics(
            tweet=tweet,
            retweet=public_metrics['retweet_count'],
            reply=public_metrics['reply_count'],
            like=public_metrics['like_count'],
            quote=public_metrics['quote_count'],
            checked_at=checked_at,
        )
        _public_metrics.save()

        return _public_metrics


    def _update_tweets(self,
        tweets: List[Dict],
        userid2user: Dict[str, TwitterUser],
        user_id_filter: List[str],
        checked_at: datetime,
    ) -> List[Tweet]:
        _tweets: List[Tweet] = []

        for tweet in tweets:
            remote_id = tweet['id']

            author_id = tweet['author_id']
            if user_id_filter is not None and author_id not in user_id_filter:
                continue

            _author = userid2user[author_id]

            _tweet = Tweet.objects.filter(remote_id=remote_id).first()
            if _tweet is None:
                _tweet = Tweet(remote_id=remote_id, first_checked_at=checked_at)

            _tweet.text = tweet['text']
            _tweet.author = _author
            _tweet.remote_created_at = isoparse(tweet['created_at'])
            _tweet.last_checked_at = checked_at

            _tweet.save()

            public_metrics = tweet['public_metrics']
            self._update_public_metrics(
                tweet=_tweet,
                public_metrics=public_metrics,
                checked_at=checked_at
            )

            _tweets.append(_tweet)

        return _tweets

    def _update_polls(self,
        polls: List[Dict],
        pollid2tweet: Dict[str, Tweet],
        checked_at: datetime,
    ) -> List[Poll]:
        _polls = []

        for poll in polls:
            remote_id = poll['id']
            _tweet = pollid2tweet.get(remote_id)
            if _tweet is None: # filtered
                continue

            options: List[Dict] = poll['options']
            total_votes = sum([ opt['votes'] for opt in options ])

            _poll = Poll(
                tweet=_tweet,
                remote_id=remote_id,
                end_datetime=isoparse(poll['end_datetime']),
                duration_minutes=poll['duration_minutes'],
                voting_status=poll['voting_status'],
                total_votes=total_votes,
                checked_at=checked_at,
            )
            _poll.save()
            _polls.append(_poll)

            for opt in options:
                votes = opt['votes']
                rate = votes / total_votes if total_votes != 0 else 0.0

                _opt = PollOption(
                    poll=_poll,
                    position=opt['position'],
                    label=opt['label'],
                    votes=votes,
                    rate=rate,
                )
                _opt.save()

        return _polls

    def _update_with_api_response(self,
        root: Dict,
        checked_at: datetime,
        requested_tweet_ids: List[str] = None,
        user_id_filter: List[str] = None,
    ) -> List[Tweet]:
        with transaction.atomic():
            tweets: List[Dict] = root.get('data', [])
            includes: Dict[Dict] = root.get('includes', {})

            # User
            users: List[Dict] = includes.get('users', [])
            _users: List[TwitterUser] = self._update_users(
                users=users,
                user_id_filter=user_id_filter,
                checked_at=checked_at,
            )
            userid2user: Dict[str, TwitterUser] = { _user.remote_id: _user for _user in _users }


            # Tweet
            _tweets: List[Tweet] = self._update_tweets(
                tweets=tweets,
                userid2user=userid2user,
                user_id_filter=user_id_filter,
                checked_at=checked_at,
            )
            tweetid2tweet: Dict[str, Tweet] = { _tweet.remote_id: _tweet for _tweet in _tweets }
            pollid2tweet: Dict[str, Tweet] = {}
            for tweet in tweets:
                _tweet = tweetid2tweet.get(tweet['id'])
                if _tweet is None: # filtered
                    continue
                for poll_id in tweet.get('attachments', {}).get('poll_ids', []):
                    pollid2tweet[poll_id] = _tweet

            # Poll
            polls: List[Dict] = includes.get('polls', [])
            _polls: List[Poll] = self._update_polls(
                polls=polls,
                pollid2tweet=pollid2tweet,
                checked_at=checked_at,
            )


            # Remove deleted tweets on Twitter
            if requested_tweet_ids is not None:
                # Delete tweets not responded
                fetched_tweet_ids = set([ str(tweet['id']) for tweet in tweets ])
                requested_tweet_ids = set([ str(tweet_id) for tweet_id in requested_tweet_ids ])

                deleted_tweet_ids = requested_tweet_ids - fetched_tweet_ids
                Tweet.objects.filter(remote_id__in=deleted_tweet_ids).delete()

            # Remove old no poll tweets (7 days)
            now = checked_at
            threshold_no_poll_delete = now - timedelta(days=7)
            # threshold_poll_delete = now - timedelta(days=60)
            Tweet.objects.filter(poll__isnull=True, remote_created_at__lt=threshold_no_poll_delete).delete()

        return _tweets


    # TODO: to use shared task pool (to reduce API call)
    # TODO: scheduled data updater
    def update_tweets(self,
        tweet_ids: List[str],
        user_id_filter: List[str] = None,
        timeout: float = 3.0,
    ) -> List[Tweet]:
        checked_at = timezone.now()
        r = self.call_api_tweets(tweet_ids=tweet_ids, timeout=timeout)
        root = r.json()

        # TODO: handling exception (e.g. Not Found, Connection Error)
        tweets: List[Tweet] = self._update_with_api_response(
            root=root,
            checked_at=checked_at,
            requested_tweet_ids=tweet_ids,
            user_id_filter=user_id_filter,
        )

        return tweets

    def get_recent_user_tweets(self,
        user_id: str,
        max_results: int = 10,
        timeout: float = 3.0,
        raw: bool = False,
    ):
        # TODO: validate user_id?
        checked_at = timezone.now()
        r = self.call_api_recent_search(query='from:%s -is:retweet' % user_id, max_results=max_results, timeout=timeout)
        root = r.json()

        if raw:
            return root

        tweets: List[Tweet] = self._update_with_api_response(
            root=root,
            checked_at=checked_at,
        )

        return tweets


class TwitterSessionOAuth(TwitterSession):
    def __init__(self, request):
        super().__init__()

        self.request = request

    def is_authenticated(self) -> bool:
        return self.screen_name is not None


    def update_my_tweets(self,
        tweet_ids: List[str],
        timeout: float = 3.0,
    ) -> List[Tweet]:
        return self.update_tweets(tweet_ids=tweet_ids, user_id_filter=[ self.user_id, ], timeout=timeout)

    def get_recent_my_tweets(self,
        max_results: int = 10,
        timeout: float = 3.0,
        raw: bool = False,
    ):
        user_id = self.user_id
        return self.get_recent_user_tweets(user_id=user_id, max_results=max_results, timeout=timeout, raw=raw)


    def start_oauth(self):
        request_token_url = 'https://api.twitter.com/oauth/request_token'
        # authorization_url = 'https://api.twitter.com/oauth/authorize'
        authorization_url = 'https://api.twitter.com/oauth/authenticate'

        session = OAuth1Session(
            client_key=settings.TWITTER_API_KEY,
            client_secret=settings.TWITTER_API_SECRET,
            callback_uri=settings.TWITTER_OAUTH_CALLBACK,
        )

        token = session.fetch_request_token(request_token_url)
        oauth_token = token.get('oauth_token')
        oauth_token_secret = token.get('oauth_token_secret')

        paramed_auth_url = session.authorization_url(authorization_url)

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

    def on_oauth_callback(self):
        access_token_url = 'https://api.twitter.com/oauth/access_token'

        oauth_token_in_url = self.request.GET.get('oauth_token')
        oauth_verifier_in_url = self.request.GET.get('oauth_verifier')

        # oauth_token = self.request.COOKIES.get('oauth_token')
        oauth_token_secret = self.request.COOKIES.get('oauth_token_secret')

        session = OAuth1Session(
            client_key=settings.TWITTER_API_KEY,
            client_secret=settings.TWITTER_API_SECRET,
            resource_owner_key=oauth_token_in_url,
            resource_owner_secret=oauth_token_secret,
        )

        try:
            token = session.fetch_access_token(access_token_url, verifier=oauth_verifier_in_url)
        except requests_oauthlib.oauth1_session.TokenRequestDenied as err:
            # Token request failed with code 401, response was '現在この機能は一時的にご利用いただけません'
            raise err

        access_token = token.get('oauth_token')
        access_token_secret = token.get('oauth_token_secret')
        screen_name = token.get('screen_name')
        user_id = token.get('user_id')

        self.request.session['access_token'] = access_token
        self.request.session['access_token_secret'] = access_token_secret
        self.request.session['screen_name'] = screen_name
        self.request.session['user_id'] = user_id

        # save tokens for scheduled auto crawling
        user = TwitterUser.objects.filter(remote_id=user_id).first()
        if user is None:
            user = TwitterUser(remote_id=user_id)
        user.screen_name = screen_name
        user.access_token = access_token
        user.access_token_secret = access_token_secret
        user.token_saved_at = timezone.now()
        user.save()

    def remove_oauth(self, response=None):
        user_id = self.request.session['user_id']

        user = TwitterUser.objects.filter(remote_id=user_id).first()
        user.access_token = None
        user.access_token_secret = None
        user.token_saved_at = None
        user.save()

        self.logout(response)

    def logout(self, response=None):
        self.request.session['access_token'] = None
        self.request.session['access_token_secret'] = None
        self.request.session['screen_name'] = None
        self.request.session['user_id'] = None

        if response is not None:
            response.delete_cookie('oauth_token')
            response.delete_cookie('oauth_token_secret')

    @property
    def http_session(self):
        s = self._http_session
        s.auth = OAuth1(
            client_key=settings.TWITTER_API_KEY,
            client_secret=settings.TWITTER_API_SECRET,
            resource_owner_key=self.request.session['access_token'],
            resource_owner_secret=self.request.session['access_token_secret'],
        )
        return s
    @http_session.setter
    def http_session(self, value):
        self._http_session = value

    @property
    def screen_name(self):
        return self.request.session.get('screen_name')

    @property
    def user_id(self):
        return self.request.session.get('user_id')

class TwitterSessionBearer(TwitterSession):
    def __init__(self, request):
        super().__init__()

        self.request = request

        self.http_session.headers.update({
            'Authorization': 'Bearer %s' % settings.TWITTER_TOKEN,
        })

    def is_authenticated(self) -> bool:
        return True
