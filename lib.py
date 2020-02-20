def sortBy(listOfDicts, key):
    keysIndices = {dictionary[key]: listOfDicts.index(dictionary) for dictionary in listOfDicts}
    sortedKeys = sorted(list(keysIndices.keys()))
    return [listOfDicts[keysIndices[k]] for k in sortedKeys]
