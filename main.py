import requests
import json
from os.path import isfile

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'

baseUrl = 'https://www.thebluealliance.com/api/v3'
teamNum = 1405
year = 2019
eventName = 'Finger Lakes Regional'

with open('headerfile') as headerfile:
    header = headerfile.readlines()[0]

events = requests.get(f'{baseUrl}/events/{year}/simple',
                      headers={'X-TBA-Auth-Key': header,
                               'year': str(year)})
for event in events.json():
    if event['name'] == eventName:
        break
assert event['name'] == eventName, f'No such event as {eventName}'

matches = requests.get(f'{baseUrl}/event/{event["key"]}/matches/simple',
                       headers={'X-TBA-Auth-Key': header,
                                'event_key': event['key']})

print(matches.json())
