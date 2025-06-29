# Working Around Schedules
This program will take in n amount of calendar ics files (must have no errors or damage since the parser is sensitive) and k amount of meeting requests.
Entering a meeting request entails including its title, duration, and the earliest date+time and latest date+time allowed for it. 
Given these calendars of n users, the program will find the most optimal way to include all k meetings in terms of the number of reschedulings each user has to do. 
Additionally, the program considers rank. So while the number of reschedulings is overall reduced, what is prioritized is that higher ranking users will have less
rescheduling to do than users who are ranked lower, and so on. 
Be aware of the order you upload the files in - calendars uploaded earlier will be considered higher ranking. 

The logic revolves around constraint programming to achieve this.
Currently in the program that I wish to change in the near future:
- the program only outputs one solution. I intend to output a list of possible solutions.
- the program is very sensitive to errors in the ics file.
- the rank is calculated based on the order that the user inputs the files. I would rather there be an interactive UI where the user can select tags, etc to indicate so.

SETUP -> pip install the following
- ics
- ortools
- Flask
