from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from constants import DATA_PATH
import json
from fastapi import Request
from fastapi import limits

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

EXACT_FILTER_COLUMNS = {
    "name",
    "season",
    "starting_season",
    "ending_season",
    "team",
    "position_group",
    "height_inches",
    "weight_lbs",
}

def validate_query_filters(query_params):
    invalid_filters = []

    for key in query_params:
        if key in EXACT_FILTER_COLUMNS:
            continue

        if key.startswith("min_"):
            column = key.removeprefix("min_")
            if column in ATTRIBUTE_COLUMNS:
                continue

        if key.startswith("max_"):
            column = key.removeprefix("max_")
            if column in ATTRIBUTE_COLUMNS:
                continue

        invalid_filters.append(key)

    if invalid_filters:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported query filter",
                "invalid_filters": invalid_filters,
            },
        )

def apply_query_filters(df, query_params):
    data = df

    for key, value in query_params.items():
        if key == "season":
            try:
                data = data[data["season"] == int(value)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == "starting_season":
            try:
                data = data[data["season"] >= int(value)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == "ending_season":
            try:
                data = data[data["season"] <= int(value)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == "team":
            try:
                data = data[data["team"].str.casefold() == value.casefold()]
            except AttributeError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == "position_group":
            try:
                data = data[data["position_group"].str.casefold() == value.casefold()]
            except AttributeError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key.startswith("min_"):
            column = key.removeprefix("min_")

            if column in ATTRIBUTE_COLUMNS:
                try:
                    data = data[data[column] >= float(value)]
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail={"message": f"Invalid value for {key}"},
                    )

        elif key.startswith("max_"):
            column = key.removeprefix("max_")

            if column in ATTRIBUTE_COLUMNS:
                try:
                    data = data[data[column] <= float(value)]
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail={"message": f"Invalid value for {key}"},
                    )

        elif key == ("height_inches"):
            try:
                data = data[data["height_inches"] == int(value)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == ("weight_lbs"):
            try:
                data = data[data["weight_lbs"] == int(value)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

        elif key == "name":
            try:
                data = data[data["name"].str.casefold() == value.casefold()]
            except AttributeError:
                raise HTTPException(
                    status_code=400,
                    detail={"message": f"Invalid value for {key}"},
                )

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
    validate_query_filters(request.query_params)
    data = apply_query_filters(app.state.df, request.query_params)
    data = clean_for_json(data)
    return json.loads(data.to_json(orient="records"))

@app.get("/players/summary")
async def read_players_summary():
    data = clean_for_json(app.state.df)
    return json.loads(data.describe().to_json())
