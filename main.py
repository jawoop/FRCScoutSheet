from os.path import isfile
from pprint import pprint
import requests
import gspread, gspread_formatting
from oauth2client.service_account import ServiceAccountCredentials

from lib import *

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'
# TODO Public: anonymize
assert isfile('TripleS-0df52047ef76.json'), \
    'This program requires a G Suite service account file. If you don\'t have one, please make your own.'

# initialize Sheets integration
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('TripleS-0df52047ef76.json', SCOPE)
gc = gspread.authorize(credentials)

# for TBA API calls
baseUrl = 'https://www.thebluealliance.com/api/v3'
ourTeamKey = 'frc1405'
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

matchesReq = requests.get(f'{baseUrl}/event/{event["key"]}/matches/simple',
                          headers={'X-TBA-Auth-Key': header,
                                   'event_key': event['key']})
matches = matchesReq.json()

ourMatches = matchesForTeam(ourTeamKey, matches)

# pprint([match['match_number'] for match in sortBy(matches, 'match_number') if match in ourMatches])

opponents = []
for match in ourMatches:
    if ourTeamKey in match['alliances']['blue']['team_keys']:
        opponents.extend(match['alliances']['red']['team_keys'])
    elif ourTeamKey in match['alliances']['red']['team_keys']:
        opponents.extend(match['alliances']['blue']['team_keys'])
    else:
        assert f"Team key {ourTeamKey} is not in either alliance in match {match['match_number']} \
        , which is supposed to contain them"

# print(opponents)
opponentsMatches = []
for opponent in opponents:
    opponentsMatches.extend(matchesForTeam(opponent, matches))

try:
    spreadsheet = gc.open(f"{event['key']} Testing")
except gspread.exceptions.SpreadsheetNotFound:
    spreadsheet = gc.create(f"{event['key']} Testing")
    # TODO Public: anonymize
    spreadsheet.share('jake.postema@gmail.com', perm_type='user', role='writer')

sheet = spreadsheet.sheet1
# TODO update en masse
for row in range(1, len(matches)+1):
    for redAlliance in matches[row]['alliances']['red']['team_keys']:
        for column in range(1, 4):
            sheet.update_cell(row, column, redAlliance[column-1][3:])
    for blueAlliance in matches[row]['alliances']['blue']['team_keys']:
        for column in range(1, 4):
            sheet.update_cell(row, column, blueAlliance[column-1][3:])


# print(uniqueVals(sorted([match['match_number'] for match in opponentsMatches])))

# opponentMatches = {team: matchesForTeam(team, matches) for team in opponents}
# pprint(sorted([match['match_number'] for match in opponentMatches.values()]))
