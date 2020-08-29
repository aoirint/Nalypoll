from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

from datetime import datetime
from dateutil.parser import isoparse

from .PollOption import *

class VotingStatus(Enum):
    OPEN = 'open'
    CLOSED = 'closed'

@dataclass
class Poll:
    id: str
    total_votes: int
    options: PollOption
    duration_minutes: int
    end_datetime: datetime
    voting_status: VotingStatus

    @classmethod
    def create(cls, data: Dict) -> Poll:
        id = data['id']
        options = data['options']

        end_datetime = data['end_datetime']
        _end_datetime = isoparse(end_datetime)

        duration_minutes = data['duration_minutes']

        voting_status = data['voting_status']
        _voting_status = VotingStatus[voting_status.upper()]

        total_votes = sum([ opt['votes'] for opt in options ])

        _options: List[PollOption] = []
        for opt in options:
            position = opt['position']
            label = opt['label']
            votes = opt['votes']
            rate = votes / total_votes if total_votes != 0 else 0.0

            _opt = PollOption(position=position, label=label, votes=votes, rate=rate)
            _options.append(_opt)

        return cls(
            id=id, total_votes=total_votes, options=_options,
            duration_minutes=duration_minutes,
            end_datetime=_end_datetime,
            voting_status=_voting_status,
        )

    @classmethod
    def create_map(cls, polls: List[Dict]) -> Dict[str, Poll]:
        _polls: Dict[str, Poll] = {}

        for poll in polls:
            _poll = cls.create(poll)
            _polls[_poll.id] = _poll

        return _polls

    @classmethod
    def create_map_from_root(cls, root) -> Dict[str, Poll]:
        includes = root.get('includes', {})
        polls = includes.get('polls', [])

        return cls.create_map(polls)
