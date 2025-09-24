# collector.py

import os
import json
from api.riot_client import RiotAPIClient
from .database import connect, create_raw_matches_table, delete_old_patches
from api.endpoints import get_ladder, get_match_history, get_match_data_from_id


def match_exists(cursor, match_id: str) -> bool:
    """Check if a match ID is already in the raw_matches table."""
    cursor.execute("SELECT 1 FROM raw_matches WHERE match_id = ?", (match_id,))
    return cursor.fetchone() is not None


def insert_raw_match(cursor, raw_match: dict):
    """Insert raw JSON match data into the DB (commit immediately)."""
    match_id = raw_match.get("metadata", {}).get("matchId")
    game_version = raw_match.get("info", {}).get("gameVersion", "")

    if not match_id:
        return

    cursor.execute(
        "INSERT OR IGNORE INTO raw_matches (match_id, gameVersion, data) VALUES (?, ?, ?)",
        (match_id, ".".join(game_version.split(".")[:2]), json.dumps(raw_match))
    )
    cursor.connection.commit()


def parse_version(v: str) -> tuple[int, int]:
    """Convert patch string like '15.14' -> (15, 14) for comparison."""
    parts = v.split(".")
    try:
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return (0, 0)


def collect_matches(
    client: RiotAPIClient,
    db_path: str,
    top: int = 500,
    matches_per_player: int = 10,
    ladder_queue: str = "RANKED_SOLO_5x5",
    ladder_region: str = "na1",
    match_queue: int = 420,
    match_region: str = "americas",
    match_type: str = "ranked",
    min_patch: str | None = None
):
    """
    Collect raw match data for a list of players, appending each new match as JSON.
    Deduplicates using match_id. Writes immediately after each successful fetch.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        db_path (str): Path to database file to store raw matches.
        top (str, optional): X number of players in ladder. Defaults to 500.
        matches_per_player (int, optional): Number of matches to collect per player. Defaults to 10.
        ladder_queue (str, optional): Queue type for matches. Defaults to "RANKED_SOLO_5x5".
        ladder_region (str, optional): Region. Defaults to "na1".
        match_queue (int, optional): Queue filter for match IDs. Defaults to 420.
        match_region (str, optional): Region for match collection. Defaults to "americas".
        match_type (str, optional): Type for match collection. Defaults to "ranked".
        min_patch (str, optional): Minimum patch to keep in DB. e.g. "15.15".
    """
    conn = connect(db_path)
    create_raw_matches_table(conn)

    cursor = conn.cursor()

    # Delete old patches before collecting
    if min_patch:
        delete_old_patches(conn, min_patch)
        keep_major, keep_minor = parse_version(min_patch)
    else:
        keep_major, keep_minor = (0, 0)

    new_matches_count = 0
    old_games_skipped = 0

    # Stream players instead of holding full list
    ladder_df = get_ladder(client=client, region=ladder_region, top=top, queue=ladder_queue)

    for player_idx, puuid in enumerate(ladder_df["puuid"].dropna(), start=1):
        match_ids = get_match_history(
            client=client,
            puuid=puuid,
            region=match_region,
            count=matches_per_player,
            queue=match_queue,
            type=match_type
        )
        if not match_ids:
            continue

        for match_idx, match_id in enumerate(match_ids, start=1):
            print("\r" + " " * 250, end="", flush=True)
            print(
                f"\rPlayer {player_idx}/{len(ladder_df)} | "
                f"Match {match_idx}/{len(match_ids)} | "
                f"New matches: {new_matches_count} | "
                f"Old games skipped: {old_games_skipped}",
                end=""
            )

            # Skip if match_id already exists
            if match_exists(cursor, match_id):
                continue

            raw_match = get_match_data_from_id(client=client, match_id=match_id, region=match_region)
            if not raw_match:
                continue

            # Skip if below min_patch
            if min_patch:
                game_version = raw_match.get("info", {}).get("gameVersion", "")
                major, minor = parse_version(game_version)
                if (major, minor) < (keep_major, keep_minor):
                    old_games_skipped += 1
                    continue

            insert_raw_match(cursor, raw_match)
            new_matches_count += 1
            del raw_match  # free memory immediately

    print("\r" + " " * 250, end="", flush=True)
    print(
        f"\rFinished | Players: {len(ladder_df)} | "
        f"New matches: {new_matches_count} | "
        f"Old games skipped: {old_games_skipped}"
    )

    conn.close()
    return
