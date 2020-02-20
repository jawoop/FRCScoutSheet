from os.path import isfile
from pprint import pprint

import requests

from lib import *

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'

baseUrl = 'https://www.thebluealliance.com/api/v3'
teamKey = 'frc1405'
year = 2019
eventName = 'Finger Lakes Regional'

with open('headerfile') as headerfile:
    header = headerfile.readlines()[0]

events = requests.get(f'{baseUrl}/events/{year}/simple',
                      headers={'X-TBA-Auth-Key': header,
                               'year': str(year)})
print(events)
for event in events.json():
    if event['name'] == eventName:
        break
assert event['name'] == eventName, f'No such event as {eventName}'

matchesReq = requests.get(f'{baseUrl}/event/{event["key"]}/matches/simple',
                          headers={'X-TBA-Auth-Key': header,
                                   'event_key': event['key']})
matches = matchesReq.json()

ourMatches = list(filter(lambda match: teamKey in match['alliances']['blue']['team_keys']
                                       or teamKey in match['alliances']['red']['team_keys'], matches))
pprint(sortBy(ourMatches, 'actual_time'))
print([index + 1 for index in range(len(sortBy(matches, 'actual_time'))) if matches[index] in ourMatches])
