# main.py

import os
from dotenv import load_dotenv
import pandas as pd
import time
from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder, get_match_history, get_match_data_from_id
from data.cleaner import clean_match_data

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.environ.get("riot_api_key")
    if not api_key:
        raise EnvironmentError("❌ riot_api_key not found in .env file.")

    # Initialize Riot client
    client = RiotAPIClient(max_requests=100, window_seconds=120)

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

    all_rows = []

    # Step 3: Collect matches
    for player_idx, puuid in enumerate(puuids):
        match_ids = get_match_history(client, puuid, region="americas", count=matches_per_player)
        if not match_ids:
            continue

        for match_idx, match_id in enumerate(match_ids):
            raw_match = get_match_data_from_id(client, match_id, region="americas")

            cleaned = clean_match_data(raw_match)
            if not cleaned:
                continue

            match_data, participants = cleaned
            for p in participants:
                row = {**match_data, **p}
                all_rows.append(row)

            # Simple live progress print (no ETA)
            print('\r' + ' ' * 150, end='', flush=True)
            print(f"\rPlayer {player_idx+1}/{len(puuids)} | Match {match_idx+1}/{len(match_ids)}", end='', flush=True)


    print("\n✅ Match collection complete.")

    # Step 4: Convert to DataFrame
    df = pd.DataFrame(all_rows)
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