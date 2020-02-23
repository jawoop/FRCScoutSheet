import datetime
import time
from os.path import isfile

import gspread
import requests
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials

from lib import *

now = datetime.datetime.now

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

doNotTrackList = []
pickList1 = []
pickList2 = []

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

dataUploaded = True
needFormattingUpdates = True
needMatchAllianceUpdates = True
forceAllUpdate = False
disregardForceUpdate = False
needCustomListUpdates = True

while True:
    cycleStart = now()
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
        if sheet.acell('L2').value and not disregardForceUpdate: forceAllUpdate = True
    except gspread.exceptions.APIError:
        print('Force update could not be accessed, please wait until the next cycle')

    try:
        if doNotTrackList != sheet.col_values(8)[1:] or pickList1 != sheet.col_values(9)[
                                                                     1:] or pickList2 != sheet.col_values(10)[1:]:
            needCustomListUpdates = True
        doNotTrackList = filterEntropy(sheet.col_values(8)[1:])
        pickList1 = filterEntropy(sheet.col_values(9)[1:])
        pickList2 = filterEntropy(sheet.col_values(10)[1:])
        print(doNotTrackList, pickList1, pickList2)
    except gspread.exceptions.APIError:
        print('Lists unable to be updated, please wait until next cycle')

    if needFormattingUpdates or forceAllUpdate:
        matchUpdateStart = now()
        matchesReq = requests.get(f"{baseUrl}/event/{event['key']}/matches/simple",
                                  headers={'X-TBA-Auth-Key': header,
                                           'event_key': event['key']})
        matches = sortBy(matchesReq.json(), 'actual_time')

        rankingsReq = requests.get(f"{baseUrl}/event/{event['key']}/rankings",
                                   headers={'X-TBA-Auth-Key': header,
                                            'event_key': event['key']})
        rankings = rankingsReq.json()
        rankings = sortBy(rankings['rankings'], 'rank')
        print(rankings)

        ourMatches = matchesForTeam(ourTeamKey, matches)
        print('Found which matches we are in')

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

        opponentsMatches = []
        partnersMatches = []
        for opponent in opponents:
            opponentsMatches.extend(matchesForTeam(opponent, matches))
        print('Found which matches our opponents are in')
        for partner in partners:
            partnersMatches.extend(matchesForTeam(partner, matches))
        matchUpdateEnd = now()
        print(f'Updating match data took {matchUpdateEnd-matchUpdateStart}.')

    dataUploadStart = now()
    while not dataUploaded:
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
            dataUploaded = True
        except gspread.exceptions.APIError:
            print('Read requests overflow -- waiting 100 seconds')
            time.sleep(100)
    dataUploadEnd = now()
    print(f'Uploading match data took {dataUploadEnd-dataUploadStart}.')

    cellsNeedingFormatting = []
    if needFormattingUpdates or forceAllUpdate:
        formattingUpdateStart = now()
        try:
            if needMatchAllianceUpdates or forceAllUpdate:
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
                needMatchAllianceUpdates = False

            print('Highlighting us...')
            for cell in sheet.findall('1405'):
                cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                               CellFormat(
                                                   backgroundColor=Color(1, 1, 0.75),
                                                   textFormat=TextFormat(underline=True, foregroundColor=Color(0.38, 0.38, 0.13))
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
            for ranking in rankings:
                print(f"Ranking team {ranking['team_key'][3:]} -- ranked {ranking['rank']}")
                for cell in sheet.findall(ranking['team_key'][3:]):
                    if rankings.index(ranking) < len(rankings)*0.25:
                        if ranking['team_key'] == ourTeamKey:
                            cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                                           CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.38, 0.13, 0.13))
                                                           )))
                        else:
                            cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                                           CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.38, 0.13, 0.13))
                                                           ) if cell.col <= 3 else CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.13, 0.13, 0.38))
                                                           )))

                    elif rankings.index(ranking) >= len(rankings)*0.75:
                        if ranking['team_key'] == ourTeamKey:
                            cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                                           CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.63, 0.63, 0.38))
                                                           )))
                        else:
                            cellsNeedingFormatting.append((gspread.utils.rowcol_to_a1(cell.row, cell.col),
                                                           CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.63, 0.38, 0.38))
                                                           ) if cell.col <= 3 else CellFormat(
                                                               textFormat=TextFormat(foregroundColor=Color(0.38, 0.38, 0.63))
                                                           )))
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
                                                   match['alliances'][match['winning_alliance']]['team_keys'].index(
                                                       ourTeamKey)
                                                   + (1 if ourTeamKey in match['alliances']['red'][
                                                       'team_keys'] else 4)),
                        CellFormat(
                            textFormat=TextFormat(bold=True),
                            backgroundColor=Color(1, 1, 0.5)
                        )))
            needFormattingUpdates = False
        except gspread.exceptions.APIError:
            print('Read requests overload: Waiting until cycle to update highlighting')
            needFormattingUpdates = True

        cellsNeedingFormatting.append((
            gspread.utils.rowcol_to_a1(1, 5), CellFormat(
                backgroundColor=Color(0.2, 0.6, 0.2),
                textFormat=TextFormat(foregroundColor=Color(0.1, 0.3, 0.1))
            )))

        if needCustomListUpdates:
            for match in matches:
                if len(doNotTrackList) >= 1:
                    for dntTeam in doNotTrackList:
                        print(f'Highlighting for pick list 2 team {dntTeam} in row {matches.index(match) + 1}')
                        if 'frc' + str(dntTeam) in match['alliances']['red']['team_keys']:
                            print('Found them in the red alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['red']['team_keys'].index(
                                                               'frc' + str(dntTeam)) + 1),
                                # TODO Solve formatting issue on foregroundColor for all custom lists (see lines 269,
                                #  294, 304, 319, 329
                                CellFormat(
                                    backgroundColor=Color(0.5, 0.5, 0.5),
                                    # textFormat=TextFormat(foregroundColor=Color(0.8, 0.8, 0.8))
                                )))
                        elif 'frc' + str(dntTeam) in match['alliances']['blue']['team_keys']:
                            print('Found them in the blue alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['blue']['team_keys'].index(
                                                               'frc' + str(dntTeam)) + 4),
                                CellFormat(
                                    backgroundColor=Color(0.5, 0.5, 0.5),
                                    # textFormat=TextFormat(foregroundColor=Color(0.8, 0.8, 0.8)),
                                )))
                        else:
                            print("Couldn't find them in this match, time to keep looking!")
                if len(pickList1) >= 1:
                    for pickList1Team in pickList1:
                        print(f'Highlighting for pick list 1 team {pickList1Team} in row {matches.index(match) + 1}')
                        if 'frc' + str(pickList1Team) in match['alliances']['red']['team_keys']:
                            print('Found them in the red alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['red']['team_keys'].index(
                                                               'frc' + str(pickList1Team)) + 1),
                                CellFormat(
                                    backgroundColor=Color(0.29, 0.89, 0.45),
                                    # textFormat=TextFormat(foregroundColor=Color(0.1, 0.3, 0.1))
                                )))
                        elif 'frc' + str(pickList1Team) in match['alliances']['blue']['team_keys']:
                            print('Found them in the blue alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['blue']['team_keys'].index(
                                                               'frc' + str(pickList1Team)) + 4),
                                CellFormat(
                                    backgroundColor=Color(0.29, 0.89, 0.45),
                                    # textFormat=TextFormat(foregroundColor=Color(0.1, 0.3, 0.1))
                                )))
                        else:
                            print("Couldn't find them in this match, time to keep looking!")
                if len(pickList2) >= 1:
                    for pickList2Team in pickList2:
                        print(f'Highlighting for pick list 2 team {pickList2Team} in row {matches.index(match) + 1}')
                        if 'frc' + str(pickList2Team) in match['alliances']['red']['team_keys']:
                            print('Found them in the red alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['red']['team_keys'].index(
                                                               'frc' + str(pickList2Team)) + 1),
                                CellFormat(
                                    backgroundColor=Color(0.76, 0.48, 0.63),
                                    # textFormat=TextFormat(foregroundColor=(0.3, 0.1, 0.4))
                                )))
                        elif 'frc' + str(pickList2Team) in match['alliances']['blue']['team_keys']:
                            print('Found them in the blue alliance!')
                            cellsNeedingFormatting.append((
                                gspread.utils.rowcol_to_a1(matches.index(match) + 1,
                                                           match['alliances']['blue']['team_keys'].index(
                                                               'frc' + str(pickList2Team)) + 1),
                                CellFormat(
                                    backgroundColor=Color(0.76, 0.48, 0.63),
                                    # textFormat=TextFormat(foregroundColor=Color(0.3, 0.1, 0.4))
                                )))
                        else:
                            print("Couldn't find them in this match, time to keep looking!")
            needCustomListUpdates = False
        formattingUpdateEnd = now()
        print(f'Highlighting and formatting matches took {formattingUpdateEnd-formattingUpdateStart}')
    print(cellsNeedingFormatting)
    print('Formatting all cells...')
    if cellsNeedingFormatting: format_cell_ranges(sheet, cellsNeedingFormatting)
    print('Formatting completed!')

    try:
        sheet.update_acell('L2', '')
    except gspread.exceptions.APIError:
        disregardForceUpdate = True
        print('Not able to automatically update FORCEUPDATE cell L2; disregarding value')
    cycleStop = now()
    print(f"Cycle took {str(cycleStop-cycleStart)} long.")
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
