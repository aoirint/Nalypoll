from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PublicMetrics:
    retweet: int
    reply: int
    like: int
    quote: int

    @classmethod
    def create(cls, data) -> PublicMetrics:
        retweet = data['retweet_count']
        reply = data['reply_count']
        like = data['like_count']
        quote = data['quote_count']

        return cls(retweet=retweet, reply=reply, like=like, quote=quote)
