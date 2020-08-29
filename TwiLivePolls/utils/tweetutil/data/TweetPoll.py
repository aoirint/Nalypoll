from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

from datetime import datetime
from dateutil.parser import isoparse

from .Poll import *
from .PublicMetrics import *

# https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet

@dataclass
class TweetPoll:
    id: str
    text: str
    public_metrics: PublicMetrics
    polls: List[Poll]
    created_at: datetime

    @classmethod
    def create_list(cls, tweets: List[Dict], polls: Dict[int, Poll]) -> List[TweetPoll]:
        _tweets: List[TweetPoll] = []

        for tweet in tweets:
            id = tweet['id']
            text = tweet['text']

            public_metrics = tweet['public_metrics']
            _public_metrics = PublicMetrics.create(public_metrics)

            tweet_polls: List[Poll] = []

            attachments = tweet.get('attachments', {})
            poll_ids = attachments.get('poll_ids', [])
            for poll_id in poll_ids:
                poll = polls[poll_id]
                tweet_polls.append(poll)

            created_at = tweet['created_at']
            _created_at = isoparse(created_at)

            _tweet = TweetPoll(
                id=id, text=text, public_metrics=_public_metrics,
                polls=tweet_polls, created_at=_created_at,
            )
            _tweets.append(_tweet)
        return _tweets

    @classmethod
    def create_list_from_root(cls, root) -> List[TweetPoll]:
        polls = Poll.create_map_from_root(root)
        tweets = root.get('data')
        if tweets is None:
            # Not Found or something
            return []

        _tweets = cls.create_list(tweets, polls)
        return _tweets
