import argparse
import csv
import json
import os
import re
import time
import unicodedata
from pathlib import Path

import requests
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.static import players as nba_players


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "master_attributes.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "master_attributes_with_bio.csv"
DEFAULT_2K26_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "2k26_roster_raw.json"
DEFAULT_BDL_CACHE_PATH = PROJECT_ROOT / "data" / "raw" / "balldontlie_players.json"
DEFAULT_NBA_BIO_CACHE_PATH = PROJECT_ROOT / "data" / "raw" / "nba_player_bios.json"
BALLDONTLIE_PLAYERS_URL = "https://api.balldontlie.io/v1/players"
VALID_POSITIONS = {"PG", "SG", "SF", "PF", "C", "G", "F"}


def load_dotenv(path):
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def normalize_name(name):
    cleaned = name.replace("’", "'").replace("`", "'")
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    return "".join(char.lower() for char in cleaned if char.isalnum())


def normalize_team(team):
    return "".join(char.lower() for char in team if char.isalnum())


def first_present(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def format_nba_position(position):
    position = position.strip()
    aliases = {
        "Guard": "G",
        "Forward": "F",
        "Center": "C",
        "Guard-Forward": "G/F",
        "Forward-Guard": "F/G",
        "Forward-Center": "F/C",
        "Center-Forward": "C/F",
    }
    return aliases.get(position, position)


def parse_height_inches(height):
    if not height:
        return ""

    match = re.search(r"(\d+)\s*(?:-|')\s*(\d+)", str(height))
    if not match:
        return ""

    feet = int(match.group(1))
    inches = int(match.group(2))
    return str(feet * 12 + inches)


def parse_weight_lbs(weight):
    if not weight:
        return ""

    match = re.search(r"\d+", str(weight))
    if not match:
        return ""

    return match.group(0)


def split_positions(position):
    if not position:
        return []

    normalized = str(position).upper().replace("-", "/")
    parts = [part.strip() for part in normalized.split("/") if part.strip()]
    canonical_parts = []

    for part in parts:
        if part in VALID_POSITIONS and part not in canonical_parts:
            canonical_parts.append(part)

    return canonical_parts


def derive_position_group(primary_position, secondary_position):
    positions = {primary_position, secondary_position} - {""}

    if not positions:
        return ""

    if "C" in positions:
        return "Big"

    if positions <= {"PG", "SG", "G"}:
        return "Guard"

    if positions <= {"PF", "F"} or "PF" in positions:
        return "Forward"

    if positions <= {"SF", "F"}:
        return "Wing"

    if positions & {"SG", "SF", "G", "F"}:
        return "Wing"

    return ""


def normalize_position_fields(position):
    positions = split_positions(position)
    primary_position = positions[0] if positions else ""
    secondary_position = positions[1] if len(positions) > 1 else ""

    return {
        "primary_position": primary_position,
        "secondary_position": secondary_position,
        "position_group": derive_position_group(primary_position, secondary_position),
    }


def load_master_rows(input_path):
    with input_path.open(newline="") as input_file:
        reader = csv.DictReader(input_file)
        return list(reader), list(reader.fieldnames or [])


def load_2k26_bios(roster_path):
    if not roster_path.exists():
        return {}, {}

    with roster_path.open() as roster_file:
        players = json.load(roster_file)

    by_name_team = {}
    by_name = {}

    for player in players:
        name = player.get("name")
        if not name:
            continue

        positions = player.get("positions") or []
        bio = {
            "position": "/".join(positions),
            "height": player.get("height", ""),
            "weight": player.get("weight", ""),
        }

        name_key = normalize_name(name)
        team = player.get("team", "")
        if team:
            by_name_team[(name_key, normalize_team(team))] = bio

        by_name.setdefault(name_key, bio)

    return by_name_team, by_name


def fetch_balldontlie_players(api_key, cache_path, sleep_seconds):
    if cache_path.exists():
        with cache_path.open() as cache_file:
            return json.load(cache_file)

    if not api_key:
        return []

    players = []
    cursor = None
    headers = {"Authorization": api_key}

    while True:
        params = {"per_page": 100}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            BALLDONTLIE_PLAYERS_URL,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        players.extend(payload.get("data", []))
        cursor = payload.get("meta", {}).get("next_cursor")

        if not cursor:
            break

        if sleep_seconds:
            time.sleep(sleep_seconds)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w") as cache_file:
        json.dump(players, cache_file, indent=2)

    return players


def build_balldontlie_bios(players):
    bios = {}

    for player in players:
        first_name = player.get("first_name", "")
        last_name = player.get("last_name", "")
        name = f"{first_name} {last_name}".strip()
        if not name:
            continue

        bios.setdefault(
            normalize_name(name),
            {
                "position": player.get("position", ""),
                "height": player.get("height", ""),
                "weight": player.get("weight", ""),
            },
        )

    return bios


def load_json_cache(cache_path, default):
    if cache_path.exists():
        with cache_path.open() as cache_file:
            return json.load(cache_file)

    return default


def write_json_cache(cache_path, data):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w") as cache_file:
        json.dump(data, cache_file, indent=2)


def fetch_nba_bio(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, timeout=30)
    frames = info.get_data_frames()
    if not frames or frames[0].empty:
        return {}

    row = frames[0].iloc[0].to_dict()
    return {
        "position": format_nba_position(str(row.get("POSITION", "") or "")),
        "height": row.get("HEIGHT", "") or "",
        "weight": row.get("WEIGHT", "") or "",
    }


def build_nba_api_bios(names, cache_path, sleep_seconds):
    cache = load_json_cache(cache_path, {})
    bios = {}
    changed = False

    for name in sorted(names):
        name_key = normalize_name(name)

        if name_key in cache:
            bios[name_key] = cache[name_key]
            continue

        matches = nba_players.find_players_by_full_name(name)
        exact_matches = [
            match for match in matches if normalize_name(match["full_name"]) == name_key
        ]
        match = exact_matches[0] if exact_matches else (matches[0] if matches else None)

        if not match:
            cache[name_key] = {}
            changed = True
            continue

        try:
            bio = fetch_nba_bio(match["id"])
        except Exception as exc:
            print(f"NBA API bio lookup failed for {name}: {exc}")
            bio = {}

        cache[name_key] = bio
        bios[name_key] = bio
        changed = True

        if sleep_seconds:
            time.sleep(sleep_seconds)

    if changed:
        write_json_cache(cache_path, cache)

    return bios


def enrich_rows(rows, two_k26_by_name_team, two_k26_by_name, balldontlie_by_name, nba_api_by_name):
    enriched_rows = []
    missing_names = set()
    matched_from_2k26 = 0
    matched_from_balldontlie = 0

    for row in rows:
        name_key = normalize_name(row["name"])
        team_key = normalize_team(row.get("team", ""))

        bio = two_k26_by_name_team.get((name_key, team_key)) or two_k26_by_name.get(name_key)
        if bio:
            matched_from_2k26 += 1
        else:
            bio = balldontlie_by_name.get(name_key)
            if bio:
                matched_from_balldontlie += 1

        nba_bio = nba_api_by_name.get(name_key, {})
        if bio or nba_bio:
            bio = {
                "position": first_present(bio.get("position") if bio else "", nba_bio.get("position")),
                "height": first_present(bio.get("height") if bio else "", nba_bio.get("height")),
                "weight": first_present(bio.get("weight") if bio else "", nba_bio.get("weight")),
            }

        if not bio or not any(bio.values()):
            missing_names.add(row["name"])
            bio = {}

        enriched_row = {
            **row,
            "position": first_present(bio.get("position")),
            "height": first_present(bio.get("height")),
            "weight": first_present(bio.get("weight")),
        }
        enriched_row["height_inches"] = parse_height_inches(enriched_row["height"])
        enriched_row["weight_lbs"] = parse_weight_lbs(enriched_row["weight"])
        enriched_row.update(normalize_position_fields(enriched_row["position"]))
        enriched_rows.append(enriched_row)

    return enriched_rows, matched_from_2k26, matched_from_balldontlie, missing_names


def write_csv(rows, fieldnames, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_fieldnames = fieldnames + [
        field
        for field in [
            "position",
            "primary_position",
            "secondary_position",
            "position_group",
            "height",
            "weight",
            "height_inches",
            "weight_lbs",
        ]
        if field not in fieldnames
    ]

    with output_path.open("w", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create master_attributes_with_bio.csv with player position, height, and weight."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--2k26-raw", dest="two_k26_raw", type=Path, default=DEFAULT_2K26_RAW_PATH)
    parser.add_argument("--balldontlie-cache", type=Path, default=DEFAULT_BDL_CACHE_PATH)
    parser.add_argument("--nba-bio-cache", type=Path, default=DEFAULT_NBA_BIO_CACHE_PATH)
    parser.add_argument(
        "--skip-balldontlie",
        action="store_true",
        help="Only use local 2K26 roster data; missing historical players will be blank.",
    )
    parser.add_argument(
        "--skip-nba-api",
        action="store_true",
        help="Do not use stats.nba.com as a fallback for missing bio fields.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=12,
        help="Delay between balldontlie pages. Free keys are limited to 5 requests/minute.",
    )
    parser.add_argument(
        "--nba-sleep-seconds",
        type=float,
        default=0.6,
        help="Delay between stats.nba.com player bio lookups.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")

    rows, fieldnames = load_master_rows(args.input)
    two_k26_by_name_team, two_k26_by_name = load_2k26_bios(args.two_k26_raw)

    balldontlie_by_name = {}
    if not args.skip_balldontlie:
        api_key = os.getenv("API_KEY_BALL_DONT_LIE")
        players = fetch_balldontlie_players(api_key, args.balldontlie_cache, args.sleep_seconds)
        balldontlie_by_name = build_balldontlie_bios(players)

    nba_api_by_name = {}
    if not args.skip_nba_api:
        names_needing_nba_api = {
            row["name"]
            for row in rows
            if not (
                two_k26_by_name_team.get((normalize_name(row["name"]), normalize_team(row.get("team", ""))))
                or (
                    (bio := two_k26_by_name.get(normalize_name(row["name"])))
                    and bio.get("position")
                    and bio.get("height")
                    and bio.get("weight")
                )
                or (
                    (bio := balldontlie_by_name.get(normalize_name(row["name"])))
                    and bio.get("position")
                    and bio.get("height")
                    and bio.get("weight")
                )
            )
        }
        nba_api_by_name = build_nba_api_bios(
            names_needing_nba_api,
            args.nba_bio_cache,
            args.nba_sleep_seconds,
        )

    enriched_rows, matched_2k26, matched_balldontlie, missing_names = enrich_rows(
        rows,
        two_k26_by_name_team,
        two_k26_by_name,
        balldontlie_by_name,
        nba_api_by_name,
    )
    write_csv(enriched_rows, fieldnames, args.output)

    coverage = {
        "position": sum(1 for row in enriched_rows if row["position"]),
        "primary_position": sum(1 for row in enriched_rows if row["primary_position"]),
        "secondary_position": sum(1 for row in enriched_rows if row["secondary_position"]),
        "position_group": sum(1 for row in enriched_rows if row["position_group"]),
        "height": sum(1 for row in enriched_rows if row["height"]),
        "weight": sum(1 for row in enriched_rows if row["weight"]),
        "height_inches": sum(1 for row in enriched_rows if row["height_inches"]),
        "weight_lbs": sum(1 for row in enriched_rows if row["weight_lbs"]),
        "all_three": sum(
            1 for row in enriched_rows if row["position"] and row["height"] and row["weight"]
        ),
        "all_database_fields": sum(
            1
            for row in enriched_rows
            if row["position"] and row["height_inches"] and row["weight_lbs"]
        ),
    }

    print(f"Wrote {len(enriched_rows)} rows to {args.output}")
    print(f"Matched rows from 2K26 local roster: {matched_2k26}")
    print(f"Matched rows from balldontlie: {matched_balldontlie}")
    print(f"Rows with position: {coverage['position']}")
    print(f"Rows with primary_position: {coverage['primary_position']}")
    print(f"Rows with secondary_position: {coverage['secondary_position']}")
    print(f"Rows with position_group: {coverage['position_group']}")
    print(f"Rows with height: {coverage['height']}")
    print(f"Rows with weight: {coverage['weight']}")
    print(f"Rows with height_inches: {coverage['height_inches']}")
    print(f"Rows with weight_lbs: {coverage['weight_lbs']}")
    print(f"Rows with all three bio fields: {coverage['all_three']}")
    print(f"Rows with all database bio fields: {coverage['all_database_fields']}")
    print(f"Unique names with no bio data: {len(missing_names)}")


if __name__ == "__main__":
    main()
