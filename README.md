# NBA Player Attributes

This project builds NBA 2K-style player attributes from real NBA statistics. The goal was to make player profiles easier to understand at a glance: instead of reading raw percentages, rates, and box-score columns, the project translates those stats into familiar basketball attributes such as `threePointShot`, `ballHandle`, `perimeterDefense`, `standingDunk`, `passVision`, and `overallAttribute`.

The training labels came from several NBA 2K roster seasons found online. Those ratings were combined with NBA statistical data, then used to train models that learn how real production maps to simplified 2K-style attributes. The final output is a generated historical ratings dataset that can be used to compare players and seasons in a more intuitive format.

## Project Motivation

Traditional NBA stats are accurate, but they are not always easy to interpret quickly. For example, a player's three-point percentage, attempts, usage, minutes, and offensive role all matter when deciding whether they should be considered a good shooter. NBA 2K attributes compress that kind of information into a single rating that is easier to scan.

This project explores whether machine learning can learn that translation:

- Use NBA 2K attributes as simplified labels for player skills.
- Use real NBA stats as model features.
- Generate estimated 2K-style ratings for historical NBA seasons.
- Make player style, strengths, and weaknesses easier to compare across seasons.

## Data

The project uses three main categories of data:

- `data/raw/`: original NBA stats and NBA 2K roster files.
- `data/processed/`: cleaned and merged modeling datasets.
- `data/generated/`: generated historical player attributes.

Important files:

- `data/processed/all_attributes.csv`: combined NBA 2K roster attributes from the available seasons.
- `data/processed/nba_ml_dataset.csv`: final merged dataset of NBA stats plus 2K attributes.
- `data/generated/historical_generated_attributes.csv`: generated historical NBA 2K-style attributes.

The merged modeling dataset contains seasons 2022, 2023, 2024, and 2026. The generated historical file contains 6,043 player-season rows from 2011 through 2025.

## Workflow

The notebooks follow this general pipeline:

1. Clean NBA stats data.
2. Clean historical NBA stats data.
3. Clean and combine NBA 2K roster attributes.
4. Merge NBA stats with 2K attributes.
5. Split the data by season.
6. Select useful statistical features.
7. Compare model types.
8. Train one model per attribute.
9. Generate historical attributes.

The season-based split used:

- Training: 2022 and 2023
- Validation: 2024
- Test: 2026

Using a season-based split is useful because it tests whether the model can generalize to a newer roster season instead of only memorizing random rows from the same year.

## Features

The final modeling features include traditional, advanced, and efficiency stats:

- Playing time and volume: `GP_base`, `MIN_base`, `PTS`, `POSS`, `FGM_PG`, `FGA_PG`
- Shooting: `FG_PCT_base`, `FG3M`, `FG3A`, `FG3_PCT`, `FTM`, `FTA`, `FT_PCT`, `EFG_PCT`, `TS_PCT`
- Rebounding and defense: `OREB`, `DREB`, `REB`, `STL`, `BLK`, `DEF_RATING`
- Playmaking: `AST`, `TOV`, `AST_PCT`, `AST_TO`, `AST_RATIO`
- Team/context stats: `PLUS_MINUS`, `OFF_RATING`, `NET_RATING`, `PACE`, `PIE`, `USG_PCT`

During feature engineering, highly duplicated columns were removed. For example, multiple versions of offensive rating, defensive rating, net rating, pace, field goals made, and field goals attempted were strongly correlated, so the project kept a cleaner feature set.

One interesting finding from the correlation analysis was that guard-like attributes such as `speedWithBall` and `passVision` tended to be negatively correlated with big-man attributes such as `interiorDefense` and `block`. That makes sense because the data naturally separates smaller ball-handlers from interior-focused bigs.

## Model Selection

The first benchmark model was Ridge Regression. It was used because it is simple, interpretable, and keeps all features in the model rather than forcing some coefficients to zero.

For the first test target, `threePointShot`, Ridge Regression produced:

- MAE: 4.88
- R²: 0.618

This means the model was off by about 5 rating points on average for three-point rating, and the stats explained about 62% of the variation in the 2K three-point attribute.

The Ridge coefficients were also useful for interpretation. Stats like `FG3_PCT`, `PTS`, `FGM_PG`, `TS_PCT`, and `PIE` were positively related to three-point rating, which matched basketball intuition. Some features, such as total three-point attempts and field-goal percentage, showed negative coefficients in the linear model, likely because the model was separating high-efficiency shooters from players whose scoring profile came from other shot types.

After the Ridge baseline, tree-based models were tested because basketball attributes are not perfectly linear. XGBoost, LightGBM, and CatBoost all improved performance on the initial `threePointShot` task:

| Model | MAE | R² |
| --- | ---: | ---: |
| Ridge Regression | 4.88 | 0.618 |
| XGBoost | 3.18 | 0.750 |
| LightGBM | 3.28 | 0.764 |
| CatBoost | 3.00 | 0.798 |

CatBoost performed best in this comparison, so the final generation step trained CatBoost models for each attribute.

## Attribute Evaluation

The final evaluation trained separate CatBoost models for 36 different attributes. Across all attributes:

- Average MAE: 6.47 rating points
- Average R²: 0.500
- Median MAE: 6.89 rating points
- Median R²: 0.480

Some attributes were predicted much better than others.

Best-performing attributes:

| Attribute | MAE | R² |
| --- | ---: | ---: |
| offensiveRebound | 3.64 | 0.870 |
| passVision | 3.50 | 0.860 |
| overallAttribute | 1.78 | 0.858 |
| defensiveRebound | 3.01 | 0.855 |
| block | 4.83 | 0.796 |
| threePointShot | 3.47 | 0.767 |

These results suggest that attributes tied closely to measurable production are easier to model. Rebounding, blocking, overall rating, and shooting all have strong statistical signals in the available data.

Lower-performing attributes:

| Attribute | MAE | R² |
| --- | ---: | ---: |
| overallDurability | 1.93 | 0.076 |
| hustle | 6.29 | 0.142 |
| vertical | 6.68 | 0.184 |
| hands | 5.81 | 0.235 |
| midRangeShot | 7.45 | 0.248 |
| stamina | 3.52 | 0.255 |

These weaker results make sense because many of these attributes are not captured cleanly by standard NBA stats. Durability, hustle, hands, vertical, and stamina depend on context, tracking data, scouting judgment, injuries, athletic testing, and subjective roster-rating decisions. The model can still estimate them, but the available box-score and advanced-stat features do not fully explain them.

## Generated Output

The final models generate historical player attributes in:

`data/generated/historical_generated_attributes.csv`

Each row contains:

- Player name
- Team abbreviation
- Season
- 36 generated NBA 2K-style attributes

Example generated attributes include:

- `overallAttribute`
- `threePointShot`
- `layup`
- `standingDunk`
- `perimeterDefense`
- `passAccuracy`
- `ballHandle`
- `offensiveRebound`
- `defensiveRebound`
- `agility`

This makes it possible to look at historical seasons through a simplified skill-rating lens instead of only raw statistical output.

## Repository Structure

```text
data/
  raw/          Original stats and roster data
  processed/    Cleaned and merged datasets
  splits/       Train/validation/test splits
  generated/    Generated historical attribute outputs
models/         Saved CatBoost models, one per attribute
notebooks/      Data cleaning, feature engineering, modeling, and inference notebooks
scripts/        Data retrieval and attribute extraction scripts
api.py          FastAPI app for querying the processed player attributes
schemas.py      Pydantic response models for the API
tests/          API tests
requirements.txt
```

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

The modeling notebooks also use CatBoost, LightGBM, and Joblib. If they are not already installed in the environment, install them with:

```bash
pip install catboost lightgbm joblib
```

Then run the notebooks in order from `notebooks/`, starting with data cleanup and ending with historical inference:

```text
01_nba_stats_cleanup.ipynb
01_nba_historical_stats_cleanup.ipynb
01_2k26_roster_cleanup.ipynb
02_combine_attributes.ipynb
02_merge_attribute_and_stats_data.ipynb
03_data_splits.ipynb
04_feature_engineering.ipynb
05_model_selection.ipynb
06_attribute_model_evaluation.ipynb
07_model_generation.ipynb
08_model_inferencing_historical_data.ipynb
```

## API Usage

This project also includes a local FastAPI app for querying the processed player attribute dataset as JSON.

The API reads from:

`data/processed/master_attributes_with_bio.csv`

Run the API from the project root:

```bash
uvicorn api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive docs are available at:

```text
http://127.0.0.1:8000/docs
```

Detailed API documentation is available in [`API.md`](API.md).

Useful endpoints:

```text
GET /health
GET /players
GET /players/summary
GET /players/filters
```

Example requests:

```bash
curl "http://127.0.0.1:8000/players?season=2025&team=Atlanta%20Hawks"
curl "http://127.0.0.1:8000/players?name=Trae%20Young"
curl "http://127.0.0.1:8000/players?min_overallAttribute=85&sort_by=overallAttribute&sort_order=desc"
curl "http://127.0.0.1:8000/players?season=2025&min_threePointShot=80&limit=10"
```

`GET /players` supports:

- Exact filters: `name`, `season`, `starting_season`, `ending_season`, `team`, `position_group`, `height_inches`, `weight_lbs`
- Range filters using `min_` and `max_`, such as `min_overallAttribute`, `max_threePointShot`, and `min_speedWithBall`
- Pagination with `limit` and `offset`
- Sorting with `sort_by` and `sort_order`

The API loads the CSV once when the server starts. If the dataset changes while the server is running, restart the server to load the updated data.

## Future Expansion

This project can be expanded in several useful directions.

More data analysis:

- Compare generated attributes against real player archetypes.
- Track how a player's style changes across seasons.
- Find players with similar attribute profiles across eras.
- Analyze which NBA stats are most important for each generated attribute.
- Study whether certain attributes are biased by role, minutes, team quality, or usage.

Better modeling:

- Tune CatBoost hyperparameters for each attribute separately.
- Add uncertainty estimates so each rating has a confidence range.
- Use multi-output models that learn relationships between attributes together.
- Add player position, height, weight, age, and role features.
- Add tracking data, play-by-play data, injury data, and shot-location data.

Scouting applications:

- Project future player attributes from college, G League, or international stats.
- Identify prospects whose statistical profile resembles current NBA players.
- Build archetype labels such as stretch big, rim-running center, 3-and-D wing, scoring guard, or pass-first creator.
- Compare a prospect's predicted attributes against team needs.

Team fit and chemistry:

- Measure how well players complement each other by combining generated attributes.
- Identify lineup strengths and weaknesses across shooting, defense, rebounding, and playmaking.
- Build a team-fit score based on spacing, defensive coverage, usage balance, and passing.
- Simulate how adding a player might change a team's overall attribute profile.

The main idea is that these generated attributes can become a simpler layer on top of detailed NBA data. They are not meant to replace scouting or deeper statistics, but they can make player comparison and style analysis faster and more intuitive.

## Acknowledgements and Data Sources

This project was made possible by the following tools and data sources:

- [`nba_api`](https://github.com/swar/nba_api): used to retrieve NBA statistics from NBA.com.
- [NBA2K API](https://www.nba2kapi.com): provided NBA 2K player and roster data.
- [MikeYan01/nba2k-player-ratings](https://github.com/MikeYan01/nba2k-player-ratings): provided the NBA 2K22, NBA 2K23, and NBA 2K24 player-rating data used in this project.

Thank you to the maintainers and contributors who made these resources publicly available.
