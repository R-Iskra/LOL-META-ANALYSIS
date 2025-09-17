# main.py

import os
from dotenv import load_dotenv
import time
import pandas as pd
from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder
from data.collector import collect_matches
from data.cleaner import flatten_matches_to_csv

def load_existing_matches(filepath: str) -> pd.DataFrame:
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.environ.get("riot_api_key")
    if not api_key:
        raise EnvironmentError("❌ riot_api_key not found in .env file.")

    # Initialize Riot client
    client = RiotAPIClient()

    # Step 1: Fetch top X ladder players
    top = 500
    print(f"Fetching top {top} players from NA ladder...")
    ladder_df = get_ladder(client, region="na1", top=top, queue="RANKED_SOLO_5x5")
    if ladder_df.empty:
        print("❌ Failed to fetch ladder.")
        return
    print(f"✅ Retrieved {len(ladder_df)} players.")
    print(ladder_df.head())

    # Step 2: Prepare for match collection
    puuids = ladder_df["puuid"].dropna().tolist()
    matches_per_player = 10
    match_csv_path = "match_data.csv"
    player_csv_path = "player_match_data.csv"

    # Step 3: Collect matches incrementally
    new_matches = collect_matches(
        client=client,
        player_puuids=puuids,
        matches_per_player=matches_per_player,
        csv_path=match_csv_path
    )

    print(f"\n✅ Match collection complete. {new_matches} new matches added.")

    # Step 4: Flatten match CSV to player-per-row CSV
    flatten_matches_to_csv(match_csv_path, player_csv_path)

if __name__ == "__main__":
    main()