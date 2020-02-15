import requests
from os.path import isfile

assert isfile('headerfile'), 'This program requires a header file in the same directory called headerfile.'

with open('headerfile') as headerfile:
    header = headerfile.readlines()[0]

print(requests.get('https://www.thebluealliance.com/api/v3/status',
                   headers={'X-TBA-Auth-Key': header}))
