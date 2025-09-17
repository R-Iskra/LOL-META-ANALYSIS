import os
import pandas as pd
from api.endpoints import get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data
from api.riot_client import RiotAPIClient

def load_existing_match_ids(filepath: str) -> set:
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            return set(df["match_id"].astype(str).unique())
        except Exception:
            return set()
    else:
        return set()

def collect_matches(
    client: RiotAPIClient,
    player_puuids: list[str],
    matches_per_player: int = 20,
    region: str = 'americas',
    csv_path: str = "match_data.csv"
) -> int:
    """
    Collect and clean match data for a list of players, appending each new match to csv_path.
    Deduplicates using match_id. Writes immediately after each successful cleaning.
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        player_puuids (list[str]): List of player puuids.
        matches_per_player (int, optional): Number of matches to collect per player. Defaults to 20.
        region (str, optional): Region for match collection. Defaults to 'americas'.
        
    Returns:
        int: Number of new matches written.
    """
    queue = 420
    type = "ranked"
    new_matches_count = 0
    file_exists = os.path.exists(csv_path)
    header_written = file_exists

    # Only load existing match_ids once at the start
    seen_match_ids = load_existing_match_ids(csv_path)

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
            print('\r' + ' ' * 150, end='', flush=True)
            print(
                f'\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count}',
                end='', flush=True
            )
            if match_id in seen_match_ids:
                continue

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=region)
            cleaned = clean_match_data(raw_match)
            if not cleaned:
                continue

            match_data = cleaned
            cleaned_id = match_data.get("match_id")
            if not cleaned_id or cleaned_id in seen_match_ids:
                continue

            # Write out immediately
            df_row = pd.DataFrame([match_data])
            df_row.to_csv(csv_path, mode='a', header=not header_written, index=False)
            header_written = True
            new_matches_count += 1

            # Update our in-memory set
            seen_match_ids.add(cleaned_id)


    print('\r' + ' ' * 150, end='', flush=True)
    print(
        f'\rPlayer {player_idx+1}/{len(player_puuids)} | Match {match_idx+1}/{len(match_ids)} | New matches: {new_matches_count}',
        end='', flush=True
    )
    return new_matches_count