from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

import requests

from .data import *

# https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/introduction
def get_tweets(
    ids: List[str],
    raw: bool = False,
    timeout: float = 3.0,
    bearer_token: str = None,
    oauth: OAuth1 = None
) -> List[TweetPoll]:
    from django.conf import settings

    url = 'https://api.twitter.com/2/tweets'
    params = {
        'ids': ','.join(ids),
        'tweet.fields': 'public_metrics,created_at',
        'poll.fields': 'duration_minutes,end_datetime,voting_status',
        'expansions': 'attachments.poll_ids',
    }

    headers = {
    }
    if bearer_token:
        headers['Authorization'] = 'Bearer %s' % bearer_token

    auth = None
    if oauth:
        auth = oauth

    r = requests.get(url, params=params, headers=headers, auth=auth, timeout=timeout)

    root = r.json()
    if raw:
        return root

    if r.status_code != 200:
        return []

    tweets = TweetPoll.create_list_from_root(root)

    return tweets


def get_recent_tweets(screen_name: str, oauth: OAuth1):
    pass
