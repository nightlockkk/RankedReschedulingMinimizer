from flask import Flask, render_template, request, redirect, url_for, session
from parse import calendar_event_creation, parse_users, parse_meeting_requests
from models.calendarEvent import CalendarEvent
from typing import List
from compromise import multi_meeting_schedule_cp
from datetime import datetime
from typing import List, Tuple

import os

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploadedFiles = request.files.getlist('Calendars')
        allEvents  = []
        filepaths = []

        for uploadedFile in uploadedFiles:
            if uploadedFile.filename != '':
                filepath = os.path.join(UPLOAD_FOLDER, uploadedFile.filename)
                filepaths.append(filepath)
                uploadedFile.save(filepath)
                events = calendar_event_creation(filepath)
            allEvents.extend(events)
        results = carryOutBackendLogic(allEvents, filepaths)       
        session['results'] = [str(r) for r in results]
        return redirect(url_for('result'))
    return render_template('index.html')  

@app.route('/result')
def result():
    results = session.get('result', [])
    return render_template('result.html', results=results)

def carryOutBackendLogic(allEvents: List[CalendarEvent], filepaths: List[str]) -> List[Tuple[str, datetime, List[Tuple[str, datetime]]]]:
    users = parse_users(filepaths)
    meetingTitles = request.form.getlist('Meeting Name')
    meetingDurations = request.form.getlist('Meeting Duration')
    earliestTimes = request.form.getlist('Earliest Time')
    latestTimes = request.form.getlist('Latest Time')

    meetingRequests = parse_meeting_requests(meetingTitles, meetingDurations, earliestTimes, latestTimes, users)

    return multi_meeting_schedule_cp(allEvents, meetingRequests)