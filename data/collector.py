# collector.py

import time
import pandas as pd
from api.endpoints import get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data
from api.riot_client import RiotAPIClient

def collect_matches(client:RiotAPIClient, player_puuids:list[str], matches_per_player:int=20, region:str='americas') -> pd.DataFrame:
    """Collect and clean match data from a list of players.

    This version does not perform ETA/tracking. It only fetches and cleans matches,
    printing simple progress updates.
    """

    all_matches = []
    seen_matches = set()

    for player_idx, puuid in enumerate(player_puuids):
        # Step 1: Get match IDs
        match_ids = get_match_history(client=client, puuid=puuid, region=region, count=matches_per_player)
        if not match_ids:
            continue

        # Step 2: Fetch and clean each match
        for match_idx, match_id in enumerate(match_ids):
            if match_id in seen_matches:
                continue  # skip duplicates
            seen_matches.add(match_id)

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=region)

            cleaned = clean_match_data(raw_match)
            if cleaned:
                match_data, participants = cleaned
                for participant in participants:
                    # Merge match-level data into participant row
                    row = {**match_data, **participant}
                    all_matches.append(row)

                # Simple progress print (no ETA)
                print(f'\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)}', end='', flush=True)
        print()

    # Step 3: Convert to DataFrame
    return pd.DataFrame(all_matches)