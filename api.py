from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from constants import DATA_PATH
import json
from fastapi import Request
from schemas import PaginatedResponse

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

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

ALLOWED_QUERY_PARAMS = {
    "name",
    "season",
    "starting_season",
    "ending_season",
    "team",
    "position_group",
    "height_inches",
    "weight_lbs",
    "limit",
    "offset",
    "sort_by",
    "sort_order",
}

SORTABLE_COLUMNS = ATTRIBUTE_COLUMNS | {
    "name",
    "season",
    "team",
    "position_group",
    "height_inches",
    "weight_lbs",
}

def validate_query_filters(query_params):
    invalid_filters = []

    for key in query_params:
        if key in ALLOWED_QUERY_PARAMS:
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
    """
    data = data[data["key"] == int(value)]

    essentially we want to loop through all query parameters and apply the appropriate filter to the dataframe based on the parameter key and value.
    so if the key is something like position_group, then we will first get
    data["position_group"] which will give us a series of pos groups
    eg) guard, wing, big, etc
    then the comparision is a boolean so if the value is guard, then we will get a boolean series 
    where the value is True for all rows where the position group is guard and False otherwise
    eg) True, False, False, etc
    then we can use this boolean series to filter the dataframe and 
    only keep the rows where the pos group is a guard 
    so data[True, False, False, etc] will give us a dataframe with only guards
    as it keeps the rows where boolean is True
    """
    data = df

    for key, value in query_params.items():
        if key in ("limit", "offset", "sort_by", "sort_order"):
            continue

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

def apply_sorting(df, sort_by, sort_order):
    if sort_by is None:
        return df

    if sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail={"message": f"Unsupported sort column: {sort_by}"},
        )

    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail={"message": "sort_order must be 'asc' or 'desc'"},
        )

    return df.sort_values(by=sort_by, ascending=sort_order == "asc")

def get_pagination_params(query_params):
    try:
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        offset = int(query_params.get("offset", 0))
    # If limit or offset cannot be converted to integers, return a 400 error
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid pagination parameters"},
        )

    # Ensure limit and offset are within valid bounds
    if limit < 1 or limit > MAX_LIMIT or offset < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"limit must be between 1 and {MAX_LIMIT}; offset must be 0 or greater"
            },
        )

    return limit, offset

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

@app.get("/players", response_model=PaginatedResponse)
async def read_players(request: Request):
    # Validate query filters to ensure only supported filters are used
    validate_query_filters(request.query_params)

    # Apply filters to the DataFrame based on query parameters
    data = apply_query_filters(app.state.df, request.query_params)
    data = apply_sorting(
        data,
        request.query_params.get("sort_by"),
        request.query_params.get("sort_order", "asc"),
    )
    total = len(data)

    # Apply pagination parameters
    limit, offset = get_pagination_params(request.query_params)

    # Paginate the data (iloc is used here for slicing the DataFrame based on offset and limit)
    data = data.iloc[offset : offset + limit]
    data = clean_for_json(data)

    # Apply pagination
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": json.loads(data.to_json(orient="records")),
    }

@app.get("/players/summary")
async def read_players_summary():
    data = clean_for_json(app.state.df)
    return json.loads(data.describe().to_json())
