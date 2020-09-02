from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

from django.db import models
from django.utils import timezone

import json
from datetime import datetime

# Create your models here.

class TwitterUser(models.Model):
    remote_id = models.CharField(max_length=255, unique=True)
    screen_name = models.CharField(max_length=255)

    name = models.CharField(max_length=255, null=True)
    protected = models.BooleanField(null=True)

    checked_at = models.DateTimeField(null=True)

    access_token = models.CharField(max_length=255, null=True)
    access_token_secret = models.CharField(max_length=255, null=True)
    token_saved_at = models.DateTimeField(null=True)

    last_access_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # unused
    def on_access(self):
        self.last_access_at = timezone.now()

        self.save()


class Tweet(models.Model):
    remote_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()

    first_checked_at = models.DateTimeField()
    last_checked_at = models.DateTimeField()
    is_poll_open = models.BooleanField(null=True)
    registered_user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE, null=True, related_name='registering_tweets')

    remote_created_at = models.DateTimeField()
    author = models.ForeignKey(TwitterUser, on_delete=models.CASCADE, null=True, related_name='tweets')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def text_oneline(self):
        return self.text.replace('\n', ' ')

    @property
    def registered(self):
        return self.registered_user is not None

    @property
    def has_poll_log(self):
        return self.polls.count() > 0

    @property
    def json(self):
        ret = {
            'id': self.remote_id,
            'text': self.text,
            'author': {
                'name': self.author.name,
                'screen_name': self.author.screen_name,
            },
            'posted_at': int(self.remote_created_at.timestamp()),
        }
        return json.dumps(ret, ensure_ascii=False)

    @property
    def polls_json(self):
        remote_ids = self.poll_remote_ids

        ret_polls = []
        for remote_id in remote_ids:
            one_poll_logs = Poll.objects.filter(tweet=self, remote_id=remote_id).order_by('checked_at')
            assert one_poll_logs.count() > 0

            ret_votes = {}
            ret_timestamps = []
            for poll in one_poll_logs: # loop one poll logs
                timestamp = poll.checked_at
                ret_timestamps.append(int(timestamp.timestamp()))

                for option in poll.options:
                    label = option.label
                    votes = option.votes
                    if label not in ret_votes:
                        ret_votes[label] = []
                    ret_votes[label].append(votes)

            last_poll_log = one_poll_logs.last()
            ret_polls.append({
                'id': remote_id,
                'end_time': last_poll_log.end_datetime.timestamp(),
                'voting_status': last_poll_log.voting_status,
                'votes': ret_votes,
                'timestamps': ret_timestamps,
            })

        return json.dumps(ret_polls, ensure_ascii=False)

    @property
    def polls(self):
        return Poll.objects.filter(tweet=self)

    @property
    def poll_remote_ids(self):
        uniq_polls = Poll.objects.filter(tweet=self).values('remote_id').distinct()

        remote_ids = [ poll['remote_id'] for poll in uniq_polls ]
        return remote_ids

    @property
    def last_polls(self):
        remote_ids = self.poll_remote_ids

        ids = []
        for remote_id in remote_ids:
            last_poll = Poll.objects.filter(tweet=self, remote_id=remote_id).order_by('-checked_at').first()
            ids.append(last_poll.id)

        return Poll.objects.filter(id__in=ids)


class PublicMetrics(models.Model):
    retweet = models.IntegerField()
    reply = models.IntegerField()
    like = models.IntegerField()
    quote = models.IntegerField()

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    checked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Poll(models.Model):
    remote_id = models.CharField(max_length=255)
    total_votes = models.IntegerField()
    duration_minutes = models.IntegerField()
    end_datetime = models.DateTimeField()
    voting_status = models.CharField(max_length=255, choices=tuple([ (name, name) for name in [ 'open', 'closed' ] ]))

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    checked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def options(self):
        return PollOption.objects.filter(poll=self)


class PollOption(models.Model):
    position = models.IntegerField()
    label = models.TextField()
    votes = models.IntegerField()
    rate = models.FloatField()
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def percentage(self):
        return self.rate * 100
