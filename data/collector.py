# collector.py

import os
import json
from api.riot_client import RiotAPIClient
from . import database 
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
    match_type: str = "ranked"
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
    """
    conn = database.connect(db_path)
    database.create_raw_matches_table(conn=conn)

    new_matches_count = 0

    player_puuids = get_ladder(client=client, region=ladder_region, top=top, queue=ladder_queue)["puuid"].dropna().tolist()
    print("Got players")

    for player_idx, puuid in enumerate(player_puuids):
        match_ids = get_match_history(client=client, puuid=puuid, region=match_region, count=matches_per_player, queue=match_queue, type=match_type)
        if not match_ids:
            continue

        for match_idx, match_id in enumerate(match_ids):
            print("\r" + " " * 150, end="", flush=True)
            print(f"\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count}", end="")

            # Skip if match_id exists in db
            if database.match_exists(conn, match_id):
                continue

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=match_region)
            if not raw_match:
                continue

            # Insert raw JSON into SQL
            database.insert_raw_match(conn, raw_match)
            new_matches_count += 1

    print("\r" + " " * 150, end="", flush=True)
    print(f"\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count}", end="")
    conn.close()
    print(f"\nFinished collecting. Total new matches: {new_matches_count}")