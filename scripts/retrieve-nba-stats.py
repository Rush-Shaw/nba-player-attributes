from nba_api.stats.endpoints import leaguedashplayerstats
import pandas as pd

seasons = [
    "2021-22",
    "2022-23",
    "2023-24",
    "2025-26"
]

all_stats = []

for season in seasons:
    base_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed='PerGame',
        measure_type_detailed_defense='Base'
    )

    advanced_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed='PerGame',
        measure_type_detailed_defense='Advanced'
    )

    # get_data_frames() returns a list of dataframes (in this case it will just be one dataframe) so we take the first element of the list to get our dataframe
    base_df = base_stats.get_data_frames()[0]

    # get_data_frames() returns a list of dataframes (in this case it will just be one dataframe) so we take the first element of the list to get our dataframe
    advanced_df = advanced_stats.get_data_frames()[0]

    merged = base_df.merge(
        advanced_df,
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

# Concatenate all seasons into a single DataFrame
final_stats_df = pd.concat(all_stats)

# save it in raw data as json format
final_stats_df.to_json(
    "../data/raw/all_nba_stats.json",
    orient="records",
    indent=4
)