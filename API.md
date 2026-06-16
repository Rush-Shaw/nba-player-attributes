# NBA Player Attributes API

This API exposes the processed NBA player attribute dataset as JSON. It is built with FastAPI and reads from:

```text
data/processed/master_attributes_with_bio.csv
```

The API currently runs locally. If someone else wants to use it, they need to clone the project, install dependencies, and run the server on their machine.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API from the project root:

```bash
uvicorn api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Data Refresh

The CSV is loaded once when the API starts. If `data/processed/master_attributes_with_bio.csv` changes while the server is already running, restart the server to load the updated data.

## Response Shape

`GET /players` returns paginated results:

```json
{
  "total": 8158,
  "limit": 25,
  "offset": 0,
  "data": [
    {
      "name": "Trae Young",
      "season": 2025,
      "team": "Atlanta Hawks",
      "overallAttribute": 88.0,
      "threePointShot": 85.0,
      "position_group": "Guard",
      "height_inches": 73,
      "weight_lbs": 164
    }
  ]
}
```

`total` is the number of rows after filters are applied, before pagination.

## Endpoints

### `GET /health`

Checks whether the API is running.

Example:

```bash
curl "http://127.0.0.1:8000/health"
```

Response:

```json
{"status": "ok"}
```

### `GET /players`

Returns player attribute rows. Supports filtering, range filtering, sorting, and pagination.

Basic request:

```bash
curl "http://127.0.0.1:8000/players"
```

Filter by season and team:

```bash
curl "http://127.0.0.1:8000/players?season=2025&team=Atlanta%20Hawks"
```

Filter by player name:

```bash
curl "http://127.0.0.1:8000/players?name=Trae%20Young"
```

Filter by position group:

```bash
curl "http://127.0.0.1:8000/players?position_group=Guard"
```

Filter by season range:

```bash
curl "http://127.0.0.1:8000/players?starting_season=2020&ending_season=2025"
```

`ending_season` is inclusive, so `ending_season=2025` includes 2025.

Filter by height or weight:

```bash
curl "http://127.0.0.1:8000/players?height_inches=78"
curl "http://127.0.0.1:8000/players?weight_lbs=220"
```

### Range Filters

Numeric attributes support `min_` and `max_` filters.

Examples:

```bash
curl "http://127.0.0.1:8000/players?min_overallAttribute=85"
curl "http://127.0.0.1:8000/players?min_threePointShot=80&max_threePointShot=90"
curl "http://127.0.0.1:8000/players?season=2025&min_speed=80&min_ballHandle=85"
```

Range filters use the dataset column names. For example:

```text
min_overallAttribute
max_overallAttribute
min_threePointShot
max_threePointShot
min_speedWithBall
max_speedWithBall
```

### Sorting

Use `sort_by` and `sort_order`.

Examples:

```bash
curl "http://127.0.0.1:8000/players?sort_by=overallAttribute&sort_order=desc"
curl "http://127.0.0.1:8000/players?season=2025&sort_by=threePointShot&sort_order=desc&limit=10"
```

`sort_order` must be:

```text
asc
desc
```

If `sort_order` is omitted, it defaults to `asc`.

### Pagination

Use `limit` and `offset`.

Defaults:

```text
limit=25
offset=0
```

The maximum `limit` is `100`.

Examples:

```bash
curl "http://127.0.0.1:8000/players?limit=10"
curl "http://127.0.0.1:8000/players?limit=10&offset=20"
```

### `GET /players/summary`

Returns descriptive statistics for numeric player attribute columns.

Example:

```bash
curl "http://127.0.0.1:8000/players/summary"
```

### `GET /players/filters`

Returns the filters, range-filterable attributes, pagination settings, and sortable columns supported by the API.

Example:

```bash
curl "http://127.0.0.1:8000/players/filters"
```

This endpoint is useful because the `/players` endpoint accepts dynamic query parameters, so not every possible filter appears automatically in FastAPI's generated docs.

## Supported Exact Filters

Exact filters:

```text
name
season
starting_season
ending_season
team
position_group
height_inches
weight_lbs
```

Text filters such as `name`, `team`, and `position_group` are case-insensitive.

## Supported Range Attributes

The following attributes support `min_` and `max_` range filters:

```text
overallAttribute
closeShot
midRangeShot
threePointShot
freeThrow
shotIQ
offensiveConsistency
layup
standingDunk
drivingDunk
postHook
postFade
postControl
drawFoul
hands
interiorDefense
perimeterDefense
steal
block
helpDefenseIQ
passPerception
defensiveConsistency
speed
strength
vertical
stamina
hustle
overallDurability
passAccuracy
ballHandle
speedWithBall
passIQ
passVision
offensiveRebound
defensiveRebound
agility
```

## Error Examples

Unsupported filter:

```bash
curl "http://127.0.0.1:8000/players?unknown=value"
```

Response:

```json
{
  "detail": {
    "message": "Unsupported query filter",
    "invalid_filters": ["unknown"]
  }
}
```

Invalid pagination:

```bash
curl "http://127.0.0.1:8000/players?limit=abc"
```

Response:

```json
{
  "detail": {
    "message": "Invalid pagination parameters"
  }
}
```

Invalid sort order:

```bash
curl "http://127.0.0.1:8000/players?sort_by=overallAttribute&sort_order=sideways"
```

Response:

```json
{
  "detail": {
    "message": "sort_order must be 'asc' or 'desc'"
  }
}
```

## Running Tests

Install `pytest` if it is not already available:

```bash
pip install pytest
```

Run the API tests:

```bash
pytest tests/test_api.py
```
