# collector.py

import time
import pandas as pd
from api.endpoints import get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data
from api.riot_client import RiotAPIClient
from utils.timing import PerformanceTracker

def collect_matches(client:RiotAPIClient, player_puuids:list[str], matches_per_player:int=20, region:str='americas') -> pd.DataFrame:
    """Collect and clean match data from a list of players.
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        player_puuids (list[str]): List of player puuids.
        matches_per_player (int, optional): Number of recent matches to fetch per player. Defaults to 20.
        region (str, optional): Region. Defaults to 'americas'
        
    Returns:
        pd.DataFrame: Cleaned match data with participants for all players.
    """

    total_requests = len(player_puuids) * (1 + matches_per_player)
    tracker = PerformanceTracker()
    tracker.start(total_requests=total_requests)

    all_matches = []
    seen_matches = set()
    completed_requests = 0
    eta_start = time.time()
    for player_idx, puuid in enumerate(player_puuids):
        # Step 1: Get match IDs
        t0 = time.time()
        match_ids = get_match_history(client=client, puuid=puuid, region=region, count=matches_per_player)
        tracker.record_process(time.time() - t0)
        if not match_ids:
            continue

        # Step 2: Fetch and clean each match
        for match_idx, match_id in enumerate(match_ids):
            if match_id in seen_matches:
                continue # skip duplicates
            seen_matches.add(match_id)

            t0 = time.time()
            raw_match = get_match_data_from_id(client=client, match_id=match_id)
            tracker.record_process(time.time() - t0)

            cleaned = clean_match_data(raw_match)
            if cleaned:
                match_data, participants = cleaned
                for participant in participants:
                    # Merge match-level data into participant row
                    row = {**match_data, **participant}
                    all_matches.append(row)
                
                completed_requests += 1
                elapsed_time = time.time() - eta_start
                avg_time = elapsed_time / completed_requests if completed_requests else 3
                remaining = total_requests - completed_requests
                eta_seconds = int(avg_time * remaining)
                mins, secs = divmod(eta_seconds, 60)
                print(f'\r[ETA] ~{mins}m{secs:02d}s | Player {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)}', end='', flush=True)
            print()
    
    # Step 3: Convert to DataFrame
    return pd.DataFrame(all_matches)