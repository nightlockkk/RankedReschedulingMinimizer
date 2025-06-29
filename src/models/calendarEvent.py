from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalendarEvent:
    start: datetime
    end: datetime
    title: str
    user_id: str #this should be user. user id should be referenced FROM user not calendar event
    rank: int 

    def __str__(self):
        return f"CalendarEvent([{self.title}]: start={self.start}, end={self.end} || USER:{self.user_id}"