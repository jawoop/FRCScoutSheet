from os.path import isfile

import gspread
import requests
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials

from lib import *

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'
# TODO Public: anonymize
assert isfile('TripleS-0df52047ef76.json'), \
    'This program requires a G Suite service account file. If you don\'t have one, please make your own.'

# initialize Sheets integration
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('TripleS-0df52047ef76.json', SCOPE)
print('Beginning authorization...')
gc = gspread.authorize(credentials)
print('Authorization completed')

# for TBA API calls
baseUrl = 'https://www.thebluealliance.com/api/v3'
ourTeamKey = 'frc1405'
year = 2019
eventName = 'Finger Lakes Regional'

with open('headerfile') as headerfile:
    header = headerfile.readlines()[0]
print('Getting events...')
events = requests.get(f'{baseUrl}/events/{year}/simple',
                      headers={'X-TBA-Auth-Key': header,
                               'year': str(year)})
for event in events.json():
    if event['name'] == eventName:
        break
assert event['name'] == eventName, f'No such event as {eventName}'
print(f"Found our event: event['key'] = {event['key']}")

matchesReq = requests.get(f"{baseUrl}/event/{event['key']}/matches/simple",
                          headers={'X-TBA-Auth-Key': header,
                                   'event_key': event['key']})
matches = sortBy(matchesReq.json(), 'actual_time')

ourMatches = matchesForTeam(ourTeamKey, matches)
print('Found which matches we are in')

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
print('Found which matches our opponents are in')

try:
    print('Opening the spreadsheet...')
    spreadsheet = gc.open(f"{event['key']} Testing")
except gspread.exceptions.SpreadsheetNotFound:
    print("Rats, it doesn't exist. Creating a new spreadsheet...")
    spreadsheet = gc.create(f"{event['key']} Testing")
    # TODO Public: anonymize
    print('Sharing spreadsheet with admin...')
    spreadsheet.share('jake.postema@gmail.com', perm_type='user', role='writer')
finally:
    print('Opened the spreadsheet')

sheet = spreadsheet.sheet1
teamsListRange = sheet.range(f'A1:F{len(matches)}')
print(teamsListRange)
print('Inserting data...')

for matchNum in range(1, int(len(teamsListRange) / 6 + 1)):
    # print(matches[matchNum-1]['alliances'])
    for col in range(1, 4):
        teamsListRange[(matchNum - 1) * 6 + col - 1].value = \
            matches[matchNum - 1]['alliances']['red']['team_keys'][col - 1][3:]
    for col in range(4, 7):
        teamsListRange[(matchNum - 1) * 6 + col - 1].value = \
            matches[matchNum - 1]['alliances']['blue']['team_keys'][col - 4][3:]

print(teamsListRange)
print('Uploading data in batch...')
sheet.update_cells(teamsListRange)
print('Upload complete. Please check to make sure information was successfully uploaded.')

format_cell_range(sheet, f'A1:C{len(matches)}', CellFormat(
    backgroundColor=Color(1, 0.9, 0.9),
    textFormat=TextFormat(bold=True, foregroundColor=Color(0.5, 0, 0)),
    horizontalAlignment='CENTER'
))
format_cell_range(sheet, f'D1:F{len(matches)}', CellFormat(
    backgroundColor=Color(0.9, 0.9, 1),
    textFormat=TextFormat(bold=True, foregroundColor=Color(0, 0, 0.5)),
    horizontalAlignment='CENTER'
))

# for row in range(1, len(matches)+1):
#     for redAlliance in matches[row]['alliances']['red']['team_keys']:
#         for column in range(1, 4):
#             sheet.update_cell(row, column, redAlliance[column-1][3:])
#     for blueAlliance in matches[row]['alliances']['blue']['team_keys']:
#         for column in range(1, 4):
#             sheet.update_cell(row, column, blueAlliance[column-1][3:])


# print(uniqueVals(sorted([match['match_number'] for match in opponentsMatches])))

# opponentMatches = {team: matchesForTeam(team, matches) for team in opponents}
# pprint(sorted([match['match_number'] for match in opponentMatches.values()]))
