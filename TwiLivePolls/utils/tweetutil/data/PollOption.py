from __future__ import annotations # PEP 563: posponed evaluation of annotations

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PollOption:
    position: int
    label: str
    votes: int
    rate: float
