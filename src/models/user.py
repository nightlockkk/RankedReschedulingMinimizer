from dataclasses import dataclass, field
from typing import List
from .calendarEvent import CalendarEvent

@dataclass
class User:
    id: str
    rank: int
    events: List[CalendarEvent] = field(default_factory=list)
