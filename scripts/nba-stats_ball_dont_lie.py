from balldontlie import BalldontlieAPI
import os
from dotenv import load_dotenv

load_dotenv()

api = BalldontlieAPI(api_key=os.getenv("API_KEY_BALL_DONT_LIE"))
players = api.nba.players.list(per_page=25)