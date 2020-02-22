def sortBy(listOfDicts, key):
    if '/' in key:
        if key.count('/') > 1:
            raise Exception("I don't know how to deal with this level of nested keys, please raise an issue on GitHub!")
        else:
            keysIndices = {dictionary[key.split('/')[0]][key.split('/')[1]]: listOfDicts.index(dictionary)
                           for dictionary in listOfDicts}
    else:
        keysIndices = {dictionary[key]: listOfDicts.index(dictionary) for dictionary in listOfDicts}
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
