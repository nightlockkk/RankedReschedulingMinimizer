from ics import Calendar
import os
from models.calendarEvent import CalendarEvent
from typing import List
from compromise import MeetingRequest
from models.user import User

#for now, assuming required users is all the same: all the users who are included
def parse_meeting_requests(meetingTitles, meetingDurations, earliestTimes, latestTimes, users):
    allMeetingRequests: List[MeetingRequest] = []
    for i in range(len(meetingTitles)):
        meetingReq = MeetingRequest(
            title=meetingTitles[i],
            duration=int(meetingDurations[i]),
            earliest=earliestTimes[i],
            latest=latestTimes[i],
            requiredUsers=users
        ) 
        allMeetingRequests.append(meetingReq)
    return allMeetingRequests

def parse_users(filepaths): #filepath = os.path.join(UPLOAD_FOLDER, uploadedFile.filename)
    users = []
    for i, filepath in enumerate(filepaths):
        user = User(
            id = get_username_from_file(filepath),
            rank = i+1,
            events = calendar_event_creation(filepath)
        )
        users.append(user)
    return users


def get_username_from_file(filepath: str):
    return os.path.basename(filepath)
    #base = os.path.basename(filepath)
    #username = base.split('_')[0]
    #return username

def parse_ics_events(filepath):
    with open(filepath, encoding='utf-8') as f:
        cal = Calendar(f.read())
    events = []
    for i, event in enumerate(cal.events):
        events.append({
            'title': event.name,
            'start': event.begin.datetime,
            'end': event.end.datetime,
            'user_id': get_username_from_file(filepath),
            'rank': i+1
        })
    return events

def calendar_event_creation(filepath):
    rawEvents = parse_ics_events(filepath)
    events = []
    for event in rawEvents:
        calev = CalendarEvent(
            start=event['start'],
            end=event['end'],
            title=event['title'],
            user_id=event['user_id'],
            rank=event['rank']
        )
        events.append(calev)
    return events
