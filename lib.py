def sortBy(listOfDicts, key):
    keysIndices = {dictionary[key]: listOfDicts.index(dictionary) for dictionary in listOfDicts}
    sortedKeys = sorted(list(keysIndices.keys()))
    return [listOfDicts[keysIndices[k]] for k in sortedKeys]


def sortBy4Keys(listOfDicts, key1, key2, key3, key4):
    keysIndices = {dictionary[key1][key2][key3][key4]: listOfDicts.index(dictionary) for dictionary in listOfDicts}
    sortedKeys = sorted(list(keysIndices.keys()))
    return [listOfDicts[keysIndices[k]] for k in sortedKeys]


def matchesForTeam(teamKey, matchesList):
    return list(filter(lambda match: teamKey in match['alliances']['blue']['team_keys']
                       or teamKey in match['alliances']['red']['team_keys'], matchesList))


def uniqueVals(list_):
    newList = []
    for val in list_:
        if val in newList: continue
        newList.append(val)
    return newList
