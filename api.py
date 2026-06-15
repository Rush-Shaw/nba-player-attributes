from fastapi import FastAPI
from contextlib import asynccontextmanager
import numpy as np
import pandas as pd
from constants import DATA_PATH
import json
from fastapi.responses import JSONResponse

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
async def read_players_data():
    data = clean_for_json(app.state.df)
    return JSONResponse(json.loads(data.to_json(orient="records")))

@app.get("/players/summary")
async def read_players_summary():
    data = clean_for_json(app.state.df)
    return JSONResponse(json.loads(data.describe().to_json()))
