# main.py

import os
from dotenv import load_dotenv
import pandas as pd
import time
from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder, get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data
from data.collector import collect_matches

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.environ.get("riot_api_key")
    if not api_key:
        raise EnvironmentError("❌ riot_api_key not found in .env file.")

    # Initialize Riot client
    client = RiotAPIClient()

    # Step 1: Fetch top 100 ladder players
    print("Fetching top 100 players from NA ladder...")
    ladder_df = get_ladder(client, region="na1", top=50, queue="RANKED_SOLO_5x5")
    if ladder_df.empty:
        print("❌ Failed to fetch ladder.")
        return

    print(f"✅ Retrieved {len(ladder_df)} players.")
    print(ladder_df.head())

    # Step 2: Prepare for match collection
    puuids = ladder_df["puuid"].dropna().tolist()
    matches_per_player = 5

    # Step 3: Collect matches using collector
    df = collect_matches(client=client, player_puuids=puuids, matches_per_player=matches_per_player)

    print("\n✅ Match collection complete.")

    # Step 4: Convert to DataFrame
    if not df.empty:
        print(f"✅ Collected {len(df)} participant rows across {df['game_id'].nunique()} matches.")
        print(df.head())
    else:
        print("⚠️ No match data collected.")

    # Step 5: Save to CSV
    df.to_csv("ladder_matches.csv", index=False)
    print("✅ Data saved to ladder_matches.csv")

if __name__ == "__main__":
    main()