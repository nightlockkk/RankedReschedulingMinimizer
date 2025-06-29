#goal: finding the least disruptive rescheduling of events for n meetings of interest,
#      while prioritizing the ranking of members/events.
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from models.calendarEvent import CalendarEvent
from models.user import User

#representing meetings desired to be scheduled by the client
class MeetingRequest:
    def __init__(self, title, duration, earliest, latest, requiredUsers):
        self.title = title
        self.duration = timedelta(minutes=duration)
        self.earliest = datetime.fromisoformat(earliest)
        self.latest = datetime.fromisoformat(latest)
        self.requiredUsers = requiredUsers

def extract_schedule(meetingRequests, events, slots, solver, meetingVars, eventVars
) -> List[Tuple[str, datetime, List[Tuple[str, datetime]]]]:
    result = []
    for req in meetingRequests:
        meetingidx = solver.Value(meetingVars[req.title])
        meetingSlot = slots[meetingidx]

        rescheduledEvents = []
        for event in events:
            eventidx = solver.Value(eventVars[event.title])
            prioridx = min(range(len(slots)), key=lambda i: abs((slots[i] - event.start).total_seconds()))
            if eventidx != prioridx: #then the event was rescheduled
                eventSlot = slots[eventidx]
                rescheduledEvents.append((event.title, eventSlot))
        result.append((req.title, meetingSlot, rescheduledEvents))
    return result

def multi_meeting_schedule_cp(
        events: List[CalendarEvent],
        meetingRequests: List[MeetingRequest],
        timeGranularity: int = 15 #1 would be most accurate
) -> Dict[str, List[Tuple[datetime, datetime]]]:
    #returning meeting title -> list of (scheduled start, scheduled end)
    allUsers = set()
    for req in meetingRequests:
        allUsers.update(req.requiredUsers)

    earliest = min([req.earliest for req in meetingRequests] + [event.start for event in events])
    latest = max([req.latest for req in meetingRequests] + [event.end for event in events])

    slots = []
    t = earliest
    while t + timedelta(minutes = timeGranularity) <= latest:
        slots.append(t)
        t += timedelta(minutes = timeGranularity)
    
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()

    #variables for each meeting request
    meetingVars = {}
    meetingDurations = {}
    meetingUsers = {}
    for req in meetingRequests:
        possibleStarts = []
        for i, slot in enumerate(slots):
            slotEnd = slot + req.duration
            if slot >= req.earliest and slotEnd <= req.latest:
                possibleStarts.append(i)
        var = model.NewIntVarFromDomain(cp_model.Domain.FromValues(possibleStarts), req.title)
        meetingVars[req.title] = var
        meetingDurations[req.title] = int(req.duration.total_seconds() // 60)
        meetingUsers[req.title] = req.requiredUsers

    #variables for the existing events that can be rescheduled
    #getting slots for posisble reschedules for each event
    eventVars = {}
    eventDurations = {}
    for event in events:
        possibleStarts = []
        eventDuration = int((event.end - event.start).total_seconds() // 60)
        for i, slot in enumerate(slots):
            slotEnd = slot + timedelta(minutes=eventDuration)
            if slot >= earliest and slotEnd <= latest:
                possibleStarts.append(i)
        var = model.NewIntVarFromDomain(cp_model.Domain.FromValues(possibleStarts), event.title)
        eventVars[event.title] = var
        eventDurations[event.title] = int((event.end - event.start).total_seconds() // 60)

    #ensuring each user doesn't have any overlapping events from the rescheduled mess
    users = {user_id: user for user in allUsers} #mapping of user id to user object
    for user_id, user in users.items():
        userItems = [] #contains tuples of (title, cp var - time slot, duration) for all its events and meetings its included in
        for event in user.events:
            userItems.append((
                event.title,
                eventVars[event.title],
                eventDurations[event.title]
            ))
        for req in meetingRequests:
            if user_id in req.requiredUsers:
                userItems.append((
                    req.title,
                    meetingVars[req.title],
                    meetingDurations[req.title]
                ))
        #iterating over every other user event/meeting and ensuring no overlaps by adding 
        #constraints to the model
        for i in range(len(userItems)):
            for j in range(i+1, len(userItems)):
                m1, v1, d1 = userItems[i]
                m2, v2, d2 = userItems[j]
                bool1 = model.NewBoolVar(f"{m1}_before_{m2}_{user}")
                bool2 = model.NewBoolVar(f"{m2}_before_{m1}_{user}")
                model.Add(v1 + d1 <= v2).OnlyEnforceIf(bool1)
                model.Add(v2 + d2 <= v1).OnlyEnforceIf(bool2)
                model.AddBoolOr([bool1, bool2])

    #tracking all possible ways to reschedule the events
    rescheduleBools = []
    rankWeights = []
    for event in events:
        orig_idx = min(range(len(slots)), key=lambda i: abs((slots[i] - event.start).total_seconds()))
        moved = model.NewBoolVar(f"rescheduled_{event.title}")
        model.Add(eventVars[event.title] != orig_idx).OnlyEnforceIf(moved)
        model.Add(eventVars[event.title] == orig_idx).OnlyEnforceIf(moved.Not())
        rescheduleBools.append(moved)
        rankWeights.append(10**(5-event.rank))
    weightedTotal = sum(rescheduleBools[i]*rankWeights[i] for i in range(len(rescheduleBools)))
    model.Minimize(weightedTotal) #minmizing number of reschedules and ranked moves

    #solves for ONE solution. in the future I want to make this multiple solutions to
    #allow for flexibility. for each user i can also add a variable for what times
    #they are not available for reschedules.
    status = solver.Solve(model)
    schedule = {}
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for req in meetingRequests:
            idx = solver.Value(meetingVars[req.title])
            start = slots[idx]
            end = start + req.duration
            schedule[req.title] = [(start, end)]
        for event in events:
            idx = solver.Value(eventVars[event.title])
            start = slots[idx]
            end = start + timedelta(minutes = eventDurations[event.title])
            schedule[event.title] = [(start, end)]
    else:
        print("No reschedulings available for the given meeting requests.")
        return []
    return extract_schedule(meetingRequests, events, slots, solver, meetingVars, eventVars)

#if the rescheduling was unsuccessful, then we alter the meeting duration minimally to allow for
#the rescheduling to occur.

#if the meeting duration has to be altered by more than 30 minutes, then we will attempt to split
#the original meeting into two parts each of which will be rescheduled separately. The 2 meeting
#splits will result in optimal durations, such that they are both as maximal as possible before
#the rescheduling becomes impossible again.

#i will implement this later. 