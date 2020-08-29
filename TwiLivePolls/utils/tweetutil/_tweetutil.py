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
) -> List[TweetPoll]:
    from django.conf import settings

    url = 'https://api.twitter.com/2/tweets'
    params = {
        'ids': ','.join(ids),
        'tweet.fields': 'public_metrics',
        'poll.fields': 'duration_minutes,end_datetime,voting_status',
        'expansions': 'attachments.poll_ids',
    }
    headers = {
        'Authorization': 'Bearer %s' % settings.TWITTER_TOKEN
    }

    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    root = r.json()
    if raw:
        return root

    tweets = TweetPoll.create_list_from_root(root)

    return tweets
