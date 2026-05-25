import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY is not set in your .env file")

# response = requests.get(
#     'https://api.nba2kapi.com/api/players/slug/lebron-james',
#     headers={'X-API-Key': '2k_lxhohgxmrv1zakjzc3c2g9mc7weo3l79'}
# )

# data = response.json()

# if data['success']:
#     print(data['data']['name'])     # "LeBron James"
#     print(data['data']['overall'])  # 97
#     print(data['data']['positions']) # ["SF", "PF"]
#     print(data['data']['team'])     # "Los Angeles Lakers"

# # For players on multiple teams, add team param:
# # ?teamType=class&team='95-'96 Bulls

response = requests.get(
    'https://api.nba2kapi.com/api/players',
    params={
        'teamType': 'curr'
    },
    headers={'X-API-Key': API_KEY}
)

data = response.json()
with open("2k26_roster.json", "w") as f:
    json.dump(data['data'], f, indent=4)


