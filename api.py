from fastapi import FastAPI
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from constants import DATA_PATH
import json
from fastapi import Request

# attributes
ATTRIBUTE_COLUMNS = {
    "overallAttribute",
    "closeShot",
    "midRangeShot",
    "threePointShot",
    "freeThrow",
    "shotIQ",
    "offensiveConsistency",
    "layup",
    "standingDunk",
    "drivingDunk",
    "postHook",
    "postFade",
    "postControl",
    "drawFoul",
    "hands",
    "interiorDefense",
    "perimeterDefense",
    "steal",
    "block",
    "helpDefenseIQ",
    "passPerception",
    "defensiveConsistency",
    "speed",
    "strength",
    "vertical",
    "stamina",
    "hustle",
    "overallDurability",
    "passAccuracy",
    "ballHandle",
    "speedWithBall",
    "passIQ",
    "passVision",
    "offensiveRebound",
    "defensiveRebound",
    "agility"
}

def apply_query_filters(df, query_params):
    data = df

    for key, value in query_params.items():
        if key == "season":
            data = data[data["season"] == int(value)]

        elif key == "starting_season":
            data = data[data["season"] >= int(value)]

        elif key == "ending_season":
            data = data[data["season"] < int(value)]

        elif key == "team":
            data = data[data["team"] == value]

        elif key == "position_group":
            data = data[data["position_group"] == value]

        elif key.startswith("min_"):
            column = key.removeprefix("min_")

            if column in ATTRIBUTE_COLUMNS:
                data = data[data[column] >= float(value)]

        elif key.startswith("max_"):
            column = key.removeprefix("max_")

            if column in ATTRIBUTE_COLUMNS:
                data = data[data[column] <= float(value)]
        
        elif key == ("height"):
            data = data[data["height_inches"] == int(value)]

        elif key == ("weight"):
            data = data[data["weight_lbs"] == int(value)]

        elif key == "name":
            data = data[data["name"] == value]

    return data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    app.state.df = pd.read_csv(DATA_PATH / "master_attributes_with_bio.csv")
    yield
    del app.state.df # cleanup code to free memory
    # Shutdown code here

# Initialize the FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)

def clean_for_json(df):
    # Replace inf values with None for JSON serialization
    data = df.replace([np.inf, -np.inf], pd.NA)
    # Convert NaN values to None for JSON serialization
    data = data.astype(object).where(pd.notnull(data), None)
    return data

@app.get("/players")
async def read_players(request: Request):
    data = apply_query_filters(app.state.df, request.query_params)
    data = clean_for_json(data)
    return json.loads(data.to_json(orient="records"))

@app.get("/players/summary")
async def read_players_summary():
    data = clean_for_json(app.state.df)
    return JSONResponse(json.loads(data.describe().to_json()))
