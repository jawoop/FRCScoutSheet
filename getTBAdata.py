import requests
import json

authKey = "ipBlikZFqLQ5MVrRvQpZvsJR9eA66DXAMf0KM2NYVQKnQ5guGxFV8F6UV4bPyuRT"
baseUrl = "https://www.thebluealliance.com/api/v3"
year = "2020"
eventName = "Finger Lakes Regional"

eventsResp = requests.get(baseUrl+"/events/"+year, headers = {"X-TBA-Auth-Key":authKey})
events = json.loads(eventsResp.json())
theEvent = events[name[eventName]]
print(theEvent)