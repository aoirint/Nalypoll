from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

from django.db import models
from django.utils import timezone

from datetime import datetime

# Create your models here.
import tweetutil.data as data


@dataclass
class PollCreate:
    poll: Poll
    options: List[PollOption]

    @classmethod
    def create(cls, tweet: Tweet, poll: data.Poll, checked_at: datetime) -> PollCreate:
        _poll, _poll_options = Poll.create(tweet, poll, checked_at)

        return cls(poll=_poll, options=_poll_options)

    def save(self):
        poll = self.poll
        options = self.options

        poll.save()
        for opt in options:
            opt.save()

@dataclass
class TweetUpdate:
    tweet: Tweet
    public_metrics: PublicMetrics
    polls: List[PollCreate]

    @classmethod
    def update_or_create(cls, tweet: data.TweetPoll, checked_at: datetime) -> TweetUpdate:
        _tweet, _ = Tweet.update_or_create(tweet, checked_at)

        public_metrics: data.PublicMetrics = tweet.public_metrics
        _public_metrics = PublicMetrics.create(_tweet, public_metrics, checked_at)

        polls: List[data.Poll] = tweet.polls
        _polls: List[PollCreate] = []
        for poll in polls:
            _poll  = PollCreate.create(_tweet, poll, checked_at)
            _polls.append(_poll)

        return cls(tweet=_tweet, public_metrics=_public_metrics, polls=_polls)

    def save(self):
        tweet: Tweet = self.tweet
        public_metrics: PublicMetrics = self.public_metrics
        polls: List[PollCreate] = self.polls

        tweet.save()
        public_metrics.save()

        for poll in polls:
            poll.save()

class Tweet(models.Model):
    remote_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()

    first_checked_at = models.DateTimeField()
    last_checked_at = models.DateTimeField()

    remote_created_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def update_or_create(cls, tweet: data.TweetPoll, checked_at: datetime) -> Tweet:
        _tweet, created = Tweet.objects.update_or_create(
            remote_id=tweet.id,
            defaults={
                'text': tweet.text,
                'remote_created_at': tweet.created_at,
                'last_checked_at': checked_at,
                'first_checked_at': checked_at,
            }
        )

        _tweet.text = tweet.text
        _tweet.remote_created_at = tweet.created_at
        _tweet.last_checked_at = checked_at

        return _tweet, created


class PublicMetrics(models.Model):
    retweet = models.IntegerField()
    reply = models.IntegerField()
    like = models.IntegerField()
    quote = models.IntegerField()

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    checked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, tweet: Tweet, public_metrics: data.PublicMetrics, checked_at: datetime) -> PublicMetrics:
        _public_metrics = PublicMetrics.objects.create(
            tweet=tweet,
            retweet=public_metrics.retweet,
            reply=public_metrics.reply,
            like=public_metrics.like,
            quote=public_metrics.quote,
            checked_at=checked_at,
        )

        return _public_metrics

class Poll(models.Model):
    remote_id = models.CharField(max_length=255)
    total_votes = models.IntegerField()
    duration_minutes = models.IntegerField()
    end_datetime = models.DateTimeField()
    voting_status = models.CharField(max_length=255, choices=tuple([ (vs.value, vs.value) for vs in data.VotingStatus ]))

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    checked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, tweet: Tweet, poll: data.Poll, checked_at: datetime) -> Poll:
        _poll = Poll.objects.create(
            tweet=tweet,
            remote_id=poll.id,
            total_votes=poll.total_votes,
            duration_minutes=poll.duration_minutes,
            end_datetime=poll.end_datetime,
            voting_status=poll.voting_status.value,
            checked_at=checked_at,
        )

        options: List[data.PollOption] = poll.options
        _options: PollOption = []

        for opt in options:
            _opt = PollOption.create(_poll, opt)
            _options.append(_opt)

        return _poll, _options

class PollOption(models.Model):
    position = models.IntegerField()
    label = models.TextField()
    votes = models.IntegerField()
    rate = models.FloatField()
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def percentage(self):
        return self.rate * 100

    @classmethod
    def create(cls, poll: Poll, option: data.PollOption) -> PollOption:
        _option = PollOption.objects.create(
            poll=poll,
            position=option.position,
            label=option.label,
            votes=option.votes,
            rate=option.rate,
        )

        return _option
