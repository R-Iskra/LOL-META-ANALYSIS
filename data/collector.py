# collector.py

import time
import pandas as pd
from api.endpoints import get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data
from api.riot_client import RiotAPIClient

def collect_matches(
    client: RiotAPIClient,
    player_puuids: list[str],
    matches_per_player: int = 20,
    region: str = 'americas',
    existing_match_ids: set = None
) -> pd.DataFrame:
    """
    Collect and clean match data from a list of players, skipping matches already in existing_match_ids.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        player_puuids (list[str]): List of player puuids.
        matches_per_player (int, optional): Number of matches to collect per player. Defaults to 20.
        region (str, optional): Region for match collection. Defaults to 'americas'.
        existing_match_ids (set, optional): Set of match game_ids to skip (already in database). Defaults to None.

    Returns:
        pd.DataFrame: DataFrame of cleaned match-level data (one row per match, teams grouped).
    """

    all_matches = []
    seen_matches = set() if existing_match_ids is None else set(existing_match_ids)

    queue = 420     # 5x5 Ranked Solo, Summoner's Rift
    type = "ranked"

    for player_idx, puuid in enumerate(player_puuids):
        match_ids = get_match_history(
            client=client,
            puuid=puuid,
            region=region,
            count=matches_per_player,
            queue=queue,
            type=type
        )
        if not match_ids:
            continue

        for match_idx, match_id in enumerate(match_ids):
            if match_id in seen_matches:
                continue  # skip duplicates or already-seen matches

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=region)
            cleaned = clean_match_data(raw_match)
            if not cleaned:
                continue

            match_data = cleaned  # <-- now a dict with teams + participants

            game_id = match_data.get("game_id")
            if game_id in seen_matches:
                continue
            seen_matches.add(game_id)

            all_matches.append(match_data)

            # Progress logging
            print('\r' + ' ' * 150, end='', flush=True)
            print(
                f'\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)}',
                end='',
                flush=True
            )

    return pd.DataFrame(all_matches)