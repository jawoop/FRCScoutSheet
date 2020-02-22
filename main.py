from os.path import isfile
import datetime, time

import gspread
import requests
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials

from lib import *

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'
# TODO Public: anonymize
assert isfile('TripleS-0df52047ef76.json'), \
    "This program requires a G Suite service account file. If you don't have one, please make your own."

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
opponents = []
partners = []
matches = []
rankings = []

with open('headerfile') as headerfile:
    header = headerfile.readlines()[0]

print('Getting events...')
events = requests.get(f'{baseUrl}/events/{year}/simple',
                      headers={'X-TBA-Auth-Key': header,
                               'year': str(year)})
for event in events.json():
    if event['name'] == eventName: break
assert event['name'] == eventName, f'No such event as {eventName}'
print(f"Found our event: event['key'] = {event['key']}")

needMatchUpdates = True
resetFormatting = True

while True:
    if needMatchUpdates:
        matchesReq = requests.get(f"{baseUrl}/event/{event['key']}/matches/simple",
                                  headers={'X-TBA-Auth-Key': header,
                                           'event_key': event['key']})
        matches = sortBy(matchesReq.json(), 'actual_time')

        rankingsReq = requests.get(f"{baseUrl}/event/{event['key']}/rankings",
                                   headers={'X-TBA-Auth-Key': header,
                                            'event_key': event['key']})
        rankings = rankingsReq.json()
        rankings = sortBy(rankings['rankings'], 'team_key')
        print(rankings)

        ourMatches = matchesForTeam(ourTeamKey, matches)
        print('Found which matches we are in')

        # pprint([match['match_number'] for match in sortBy(matches, 'match_number') if match in ourMatches])

        for match in ourMatches:
            if ourTeamKey in match['alliances']['blue']['team_keys']:
                opponents.extend(match['alliances']['red']['team_keys'])
                partners.extend(match['alliances']['blue']['team_keys'])
                partners.remove(ourTeamKey)
            elif ourTeamKey in match['alliances']['red']['team_keys']:
                opponents.extend(match['alliances']['blue']['team_keys'])
                partners.extend(match['alliances']['red']['team_keys'])
                partners.remove(ourTeamKey)
            else:
                assert f"Team key {ourTeamKey} is not in either alliance in match {match['match_number']} \
                , which is supposed to contain them"

        # print(opponents)
        opponentsMatches = []
        partnersMatches = []
        for opponent in opponents:
            opponentsMatches.extend(matchesForTeam(opponent, matches))
        print('Found which matches our opponents are in')
        for partner in partners:
            partnersMatches.extend(matchesForTeam(partner, matches))

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
    try:
        print('Inserting data...')
        teamsListRange = sheet.range(f'A1:F{len(matches)}')
        for matchNum in range(1, int(len(teamsListRange) / 6 + 1)):
            # print(matches[matchNum-1]['alliances'])
            for col in range(1, 4):
                teamsListRange[(matchNum - 1) * 6 + col - 1].value = \
                    matches[matchNum - 1]['alliances']['red']['team_keys'][col - 1][3:]
            for col in range(4, 7):
                teamsListRange[(matchNum - 1) * 6 + col - 1].value = \
                    matches[matchNum - 1]['alliances']['blue']['team_keys'][col - 4][3:]
        print('Uploading data in batch...')
        sheet.update_cells(teamsListRange)
        print('Upload complete. Please check to make sure information was successfully uploaded.')
    except gspread.exceptions.APIError:
        print('Read requests overflow -- waiting 100 seconds')
        time.sleep(100)

    if resetFormatting:
        format_cell_range(sheet, f'A1:C{len(matches)}', CellFormat(
            backgroundColor=Color(1, 0.9, 0.9),
            textFormat=TextFormat(bold=False, italic=False, underline=False, foregroundColor=Color(0.5, 0, 0)),
            horizontalAlignment='CENTER'
        ))
        format_cell_range(sheet, f'D1:F{len(matches)}', CellFormat(
            backgroundColor=Color(0.9, 0.9, 1),
            textFormat=TextFormat(bold=False, italic=False, underline=False, foregroundColor=Color(0, 0, 0.5)),
            horizontalAlignment='CENTER'
        ))
        resetFormatting = False

    print('Highlighting us...')
    cellsNeedingFormatting = []

    if needMatchUpdates:
        for cell in sheet.findall('1405'):
            cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                           CellFormat(
                                               backgroundColor=Color(1, 1, 0.75),
                                               textFormat=TextFormat(underline=True, foregroundColor=Color(0.5, 0.5, 0))
                                           )))

        for opponent in opponents:
            print(f'Highlighting opponent {opponent[3:]}')
            for cell in sheet.findall(opponent[3:]):
                cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                               CellFormat(
                                                   textFormat=TextFormat(bold=True)
                                               )))

        for partner in partners:
            print(f'Highlighting partner {partner[3:]}')
            for cell in sheet.findall(partner[3:]):
                cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                               CellFormat(
                                                   textFormat=TextFormat(italic=True)
                                               )))
        needMatchUpdates = False

    try:
        for match in matches:
            print(f"Highlighting winner of match {match['match_number']}")
            cellsNeedingFormatting.append((
                f"{gspread.utils.rowcol_to_a1(matches.index(match) + 1, 1 if match['winning_alliance'] == 'red' else 4)}:"
                f"{gspread.utils.rowcol_to_a1(matches.index(match) + 1, 3 if match['winning_alliance'] == 'red' else 6)}",
                CellFormat(
                    backgroundColor=Color(1, 0.75, 0.75)
                ) if match['winning_alliance'] == 'red' else CellFormat(
                    backgroundColor=Color(0.75, 0.75, 1)
                )))
            if ourTeamKey in match['alliances'][match['winning_alliance']]['team_keys']:
                cellsNeedingFormatting.append((
                    gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                               match['alliances'][match['winning_alliance']]['team_keys'].index(ourTeamKey)
                                               + (1 if ourTeamKey in match['alliances']['red']['team_keys'] else 4)),
                    CellFormat(
                        textFormat=TextFormat(bold=True),
                        backgroundColor=Color(1, 1, 0.5)
                    )))
    except gspread.exceptions.APIError:
        print('Read requests overload: Waiting until cycle to update')

    print(cellsNeedingFormatting)
    print('Formatting all cells...')
    format_cell_ranges(sheet, cellsNeedingFormatting)
    print('Formatting completed!')

    time.sleep(100)

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
