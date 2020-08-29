from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

from .Poll import *
from .PublicMetrics import *

@dataclass
class TweetPoll:
    id: str
    text: str
    public_metrics: PublicMetrics
    polls: List[Poll]

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

            _tweet = TweetPoll(id=id, text=text, public_metrics=_public_metrics, polls=tweet_polls)
            _tweets.append(_tweet)
        return _tweets

    @classmethod
    def create_list_from_root(cls, root) -> List[TweetPoll]:
        polls = Poll.create_map_from_root(root)
        tweets = root['data']

        _tweets = cls.create_list(tweets, polls)
        return _tweets
