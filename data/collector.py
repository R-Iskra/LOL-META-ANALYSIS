# collector.py

import os
import json
from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder, get_match_history, get_match_data_from_id


def load_existing_match_ids(jsonl_path: str) -> set:
    """
    Load existing match IDs from a JSONL file to avoid duplicates.

    Args: 
        jsonl_path (str): Path to JSONL file to load.
    """
    if not os.path.exists(jsonl_path):
        return set()

    match_ids = set()
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    raw_match = json.loads(line)
                    match_ids.add(str(raw_match["metadata"]["matchId"]))
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception:
        return set()
    return match_ids


def collect_matches(
    client: RiotAPIClient,
    jsonl_path: str,
    top: int = 500,
    matches_per_player: int = 10,
    region: str = "americas",
):
    """
    Collect raw match data for a list of players, appending each new match as JSON to jsonl_path.
    Deduplicates using match_id. Writes immediately after each successful fetch.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        jsonl_path (str): Path to JSONL file to load and store.
        top (str, optional): X number of players in ladder. Defaults to 500.
        matches_per_player (int, optional): Number of matches to collect per player. Defaults to 10.
        region (str, optional): Region for match collection. Defaults to 'americas'.
    """
    queue = 420
    type = "ranked"
    new_matches_count = 0

    player_puuids = get_ladder(client=client, top=top)["puuid"].dropna().tolist()

    # Load existing matches once
    seen_match_ids = load_existing_match_ids(jsonl_path)

    with open(jsonl_path, "a", encoding="utf-8") as f_out:
        for player_idx, puuid in enumerate(player_puuids):
            match_ids = get_match_history(
                client=client,
                puuid=puuid,
                region=region,
                count=matches_per_player,
                queue=queue,
                type=type,
            )
            if not match_ids:
                continue

            for match_idx, match_id in enumerate(match_ids):
                print("\r" + " " * 150, end="", flush=True)
                print(
                    f"\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count}",
                    end="",
                    flush=True,
                )

                if match_id in seen_match_ids:
                    continue

                raw_match = get_match_data_from_id(client=client, match_id=match_id, region=region)
                if not raw_match:
                    continue

                # Write raw JSON as a new line
                f_out.write(json.dumps(raw_match) + "\n")
                f_out.flush()

                new_matches_count += 1
                seen_match_ids.add(match_id)

    print("\r" + " " * 150, end="", flush=True)
    print(
        f"\rFinished | Total new matches collected: {new_matches_count}",
        end="",
        flush=True,
    )
    return