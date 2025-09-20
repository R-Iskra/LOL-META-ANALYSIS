# collector.py

import os
import json
from api.riot_client import RiotAPIClient
from .database import connect, create_raw_matches_table, match_exists, insert_raw_match, delete_old_patches
from api.endpoints import get_ladder, get_match_history, get_match_data_from_id


def collect_matches(
    client: RiotAPIClient,
    db_path: str,
    top: int = 500,
    matches_per_player: int = 10,
    ladder_queue: str = "RANKED_SOLO_5x5",
    ladder_region: str = "na1",
    match_queue: int = 420,
    match_region: str = "americas",
    match_type: str = "ranked",
    min_patch: str|None = None
):
    """
    Collect raw match data for a list of players, appending each new match as JSON to jsonl_path.
    Deduplicates using match_id. Writes immediately after each successful fetch.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        db_path (str): Path to database file to store raw matches.
        top (str, optional): X number of players in ladder. Defaults to 500.
        matches_per_player (int, optional): Number of matches to collect per player. Defaults to 10.
        ladder_queue (str, optional): Queue type for matches. "RANKED_SOLO_5x5", "RANKED_FLEX_SR", or "RANKED_FLEX_TT". Defaults to "RANKED_SOLO_5x5"
        ladder_region (str, optional): Region. Defaults to "na1"
        match_queue (int, optional): Filter for list of match ids. Defaults to 420, queue_id for 5x5 Ranked Solo Summoner"s Rift.
        match_region (str, optional): Region for match collection. Defaults to "americas".
        match_type (str, optional): Type for match collection. Defaults to "ranked"
        min_patch (str, optional): Minimum patch to keep in DB. e.g. "15.15". Defaults to None.
    """
    conn = connect(db_path)
    create_raw_matches_table(conn=conn)

    # Delete old patches before collecting
    if min_patch:
        delete_old_patches(conn, min_patch)

    new_matches_count = 0

    old_games_skipped = 0

    player_puuids = get_ladder(client=client, region=ladder_region, top=top, queue=ladder_queue)["puuid"].dropna().tolist()

    def parse_version(v: str) -> tuple[int, int]:
        parts = v.split(".")
        try:
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return (0, 0)
        
    keep_major, keep_minor = parse_version(min_patch) if min_patch else (0, 0)

    for player_idx, puuid in enumerate(player_puuids):
        match_ids = get_match_history(client=client, puuid=puuid, region=match_region, count=matches_per_player, queue=match_queue, type=match_type)
        if not match_ids:
            continue

        for match_idx, match_id in enumerate(match_ids):
            print("\r" + " " * 250, end="", flush=True)
            print(f"\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count} | Old games skipped: {old_games_skipped}", end="")

            # Skip if match_id exists in db
            if match_exists(conn, match_id):
                continue

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=match_region)
            if not raw_match:
                continue

            # Skip if gameVersion is below min_patch
            if min_patch:
                game_version = raw_match.get("info", {}).get("gameVersion", "")
                major, minor = parse_version(game_version)
                if (major, minor) < (keep_major, keep_minor):
                    old_games_skipped += 1
                    continue

            # Insert raw JSON into SQL
            insert_raw_match(conn, raw_match)
            new_matches_count += 1

    print("\r" + " " * 250, end="", flush=True)
    print(f"\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count} | Old games skipped: {old_games_skipped}", end="")
    conn.close()
    print()

    return