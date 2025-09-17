# main.py

import os
from dotenv import load_dotenv
import pandas as pd
import time
from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder
from data.collector import collect_matches

def load_existing_matches(filepath: str) -> pd.DataFrame:
    """Load existing match data from a CSV file if it exists."""
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
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
    top = 10
    print(f"Fetching top {top} players from NA ladder...")
    ladder_df = get_ladder(client, region="na1", top=top, queue="RANKED_SOLO_5x5")
    if ladder_df.empty:
        print("❌ Failed to fetch ladder.")
        return

    print(f"✅ Retrieved {len(ladder_df)} players.")
    print(ladder_df.head())

    # Step 2: Prepare for match collection
    puuids = ladder_df["puuid"].dropna().tolist()
    matches_per_player = 5

    # Step 3: Load existing matches and get seen game_ids
    csv_path = "ladder_matches.csv"
    existing_df = load_existing_matches(csv_path)
    if not existing_df.empty:
        existing_match_ids = set(existing_df["game_id"].astype(str).unique())
        print(f"Found {len(existing_match_ids)} existing matches.")
    else:
        existing_match_ids = set()
        print("No existing match data found.")

    # Step 4: Collect matches using collector, skipping already-seen matches
    df_new = collect_matches(
        client=client,
        player_puuids=puuids,
        matches_per_player=matches_per_player,
        existing_match_ids=existing_match_ids
    )

    print("\n✅ Match collection complete.")

    # Step 5: Combine, deduplicate, and save
    if not df_new.empty:
        # Combine new + existing
        combined_df = pd.concat([existing_df, df_new], ignore_index=True)

        # Deduplicate on game_id (since each row = one match now)
        combined_df.drop_duplicates(subset=["game_id"], inplace=True)

        print(f"✅ Total {len(combined_df)} matches saved.")
        print(combined_df.head())

        # Save to CSV
        combined_df.to_csv(csv_path, index=False)
        print(f"✅ Data saved to {csv_path}")
    else:
        print("⚠️ No new match data collected.")

if __name__ == "__main__":
    main()