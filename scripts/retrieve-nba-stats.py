import time
from pathlib import Path
from random import uniform

from nba_api.stats.endpoints import leaguedashplayerstats
from requests.exceptions import RequestException
import pandas as pd

# seasons = [
#     "2021-22",
#     "2022-23",
#     "2023-24",
#     "2025-26"
# ]

seasons = [
    "2010-11",
    "2011-12",
    "2012-13",
    "2013-14",
    "2014-15",
    "2015-16",
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2024-25"
]

all_stats = []
failed_seasons = []

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CACHE_DIR = RAW_DATA_DIR / "nba_stats_cache"
OUTPUT_PATH = RAW_DATA_DIR / "all_nba_stats_historical.json"

REQUEST_HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}


def cache_path_for(season, measure_type_detailed_defense):
    safe_season = season.replace("-", "_")
    safe_measure = measure_type_detailed_defense.lower()
    return CACHE_DIR / f"{safe_season}_{safe_measure}.json"


def write_combined_stats(stats_frames):
    final_stats_df = pd.concat(stats_frames, ignore_index=True)
    final_stats_df.to_json(
        OUTPUT_PATH,
        orient="records",
        indent=4,
    )
    return final_stats_df


def fetch_league_dash_player_stats(season, measure_type_detailed_defense, attempts=8, timeout=300):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached_path = cache_path_for(season, measure_type_detailed_defense)

    if cached_path.exists():
        print(f"Loaded cached {measure_type_detailed_defense} stats for {season}")
        return pd.read_json(cached_path)

    for attempt in range(1, attempts + 1):
        try:
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                per_mode_detailed='PerGame',
                measure_type_detailed_defense=measure_type_detailed_defense,
                headers=REQUEST_HEADERS.copy(),
                timeout=timeout,
            )
            df = stats.get_data_frames()[0]
            df.to_json(cached_path, orient="records", indent=4)
            return df
        except RequestException as exc:
            if attempt == attempts:
                raise

            wait_seconds = min(120, 2 ** (attempt - 1)) + uniform(0, 2)
            print(
                f"Request failed for season {season} ({measure_type_detailed_defense}): {exc}; "
                f"retrying in {wait_seconds:.1f} seconds ({attempt}/{attempts})..."
            )
            time.sleep(wait_seconds)


for season in seasons:
    try:
        print(f"Fetching season {season}")
        base_stats = fetch_league_dash_player_stats(season, 'Base')
        time.sleep(uniform(3, 8))
        advanced_stats = fetch_league_dash_player_stats(season, 'Advanced')

        merged = base_stats.merge(
            advanced_stats,
            on=[
                "PLAYER_ID",
                "PLAYER_NAME",
                "TEAM_ID",
                "TEAM_ABBREVIATION"
            ],
            suffixes=("_base", "_advanced")
        )

        # adds the season key to the merged dataframe so we can keep track of which season the stats are from after we concatenate all seasons together
        merged["season"] = season

        # append each dataframe on top of each other rather than the contents inside
        all_stats.append(merged)
        write_combined_stats(all_stats)
        print(f"Finished season {season}")
    except RequestException as exc:
        failed_seasons.append(season)
        print(f"Skipping season {season} after repeated timeout/error: {exc}")

if not all_stats:
    raise RuntimeError("No season data could be retrieved from stats.nba.com")

# Concatenate all seasons into a single DataFrame
final_stats_df = write_combined_stats(all_stats)

# save it in raw data as json format
print(f"Saved {len(final_stats_df)} rows to {OUTPUT_PATH}")

if failed_seasons:
    print(f"Completed with failed seasons: {', '.join(failed_seasons)}")
