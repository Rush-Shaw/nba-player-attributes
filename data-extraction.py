import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY is not set in your .env file")

url = "https://api.nba2kapi.com/api/players"
all_players = []

# vars for pagination
cursor = None # first request doesn't need a cursor hence init to none
limit = 100
headers = {

    "X-API-Key": API_KEY

}

# Loop to fetch all players using pagination
while True:
    params = {
        "limit": limit # max limit of players per request
    }

    # If we have a cursor from the previous response, include it in the next request
    if cursor:
        params["cursor"] = cursor

    # Make the API request (url is the api endpoint, param is the limit, and headers is the key)
    response = requests.get(url, params=params, headers=headers)
    # https://api.nba2kapi.com/api/players?limit=100&cursor=100
    result = response.json() # convert the response to json format

    if not result.get("success"):
        print(json.dumps(result, indent=4))
        break

    # retrieve the list of players from the response and add them to our all_players list
    # data is the key in the dict that contains the list of players else we get an empty list
    players = result.get("data", [])
    # extend: [1,2,3].extend([4,5]) => [1,2,3,4,5]
    all_players.extend(players)

    # essentially result has a bunch of metadata including our data
    # so result would be like
    # result = {
    #     "success": true,
    #     "data": [list of players],
    #     "meta": {
    #         "pagination": {
    #             "nextCursor": "cursor_value",
    #             "hasMore": true
    #         }
    #     }
    # }
    # what we want to do is to get the nextCursor and hasMore values from the pagination metadata to know if we need to make another request and what cursor to use for that request
    pagination = result.get("meta", {}).get("pagination", {})

    cursor = pagination.get("nextCursor")

    has_more = pagination.get("hasMore", False)

    print(f"Retrieved {len(players)} players | Total: {len(all_players)} | Next cursor: {cursor}")

    # If hasMore is false, it means we've retrieved all the players and we can break out of the loop
    if not has_more:
        break

# dump into json file
with open("2k26_roster_raw.json", "w") as f:
    json.dump(all_players, f, indent=4)

print(f"Final player count: {len(all_players)}")