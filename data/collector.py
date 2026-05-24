"""
collector.py

Collects raw match data from the Riot Games API and stores it
as JSON blobs in the raw database layer.
"""

import json
import logging
from datetime import datetime, timezone

from api.riot_client import RiotAPIClient
from api.endpoints import (
    APEX_TIERS,
    ENTRY_TIERS,
    ALL_DIVISIONS,
    get_apex_ladder,
    get_ranked_entries,
    get_match_ids,
    get_match
)
from data.database import (
    connect,
    create_raw_schema,
    raw_match_exists,
    insert_raw_match,
    delete_raw_patches_below
)
from utils import parse_version, normalize_version

logger = logging.getLogger(__name__)


def collect(
        client: RiotAPIClient,
        db_path: str,
        tiers: list[str],
        queue: str = "RANKED_SOLO_5x5",
        region: str = "na1",
        match_region: str = "americas",
        match_queue: int = 420,
        match_type: str = "ranked",
        top: int | None = 500,
        matches_per_player: int = 10,
        min_patch: str | None = None
):
    """
    Collect raw match data for players in a given tier and store in the raw DB

    Args:
        client (RiotAPIClient): Authenticated Riot API client.
        db_path (str): Path to the raw SQLite database file.
        tiers (str): Tiers to collect from e.g.
            ["CHALLENGER", "GRANDMASTER", "GOLD", "SILVER"]
        queue (str): Ladder queue type. Defaults to "RANKED_SOLO_5x5".
        region (str): Platform region for ladder e.g. "na1". Defaults to "na1".
        match_region (str): Routing region for match data. Defaults to "amercias"
        match_queue (int): Queue ID filter for matches. Defaults to 420 (Ranked Solo).
        match_type (str): Match type filter. Defaults to "ranked".
        top (int): Max Number of players to collect from. Defaults to 500.
        matches_per_player (int): Matches to collect per player. Defaults to 10.
        min_patch (str, optional): Skip matches below this patch e.g. "15.15".
                                   Also deletes older patches from the DB.
    """
    conn = connect(db_path)
    create_raw_schema(conn)

    if min_patch:
        deleted = delete_raw_patches_below(conn, min_patch)
        if deleted:
            logger.info("Deleted %d matches below patch %s.", deleted, min_patch)

    for tier in tiers:
        tier = tier.upper()

        if tier not in APEX_TIERS and tier not in ENTRY_TIERS:
            logger.warning("Invalid tier '%s', skipping.", tier)
            continue

        _collect_tier(
            client=client,
            conn=conn,
            tier=tier,
            queue=queue,
            region=region,
            match_region=match_region,
            match_queue=match_queue,
            match_type=match_type,
            top=top,
            matches_per_player=matches_per_player,
            min_patch=min_patch
        )

    conn.close()
    logger.info("All tiers collected.")

# --------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------

def _get_puuids_for_tier(
        client: RiotAPIClient,
        tier: str,
        queue: str,
        region: str,
        top: int
) -> list[str]:
    """
    Get up to `top` puuids for a given tier
    Apex tiers use a single endpoint. Entry tiers iterate through 
    divisons I->IV.
    """
    if tier in APEX_TIERS:
        return get_apex_ladder(
            client=client, tier=tier, queue=queue, region=region, top=top
        )
    
    puuids = []
    for division in ALL_DIVISIONS:
        remaining = top - len(puuids)
        if remaining <= 0:
            break
        division_puuids = get_ranked_entries(
            client=client,
            tier=tier,
            division=division,
            queue=queue,
            region=region,
            top=remaining,
        )
        puuids.extend(division_puuids)
        logger.info(
            " %s %s: %d players collected (%d/%d total).",
            tier, division, len(division_puuids), len(puuids), top
        )

    return puuids

def _collect_tier(
        client: RiotAPIClient,
        conn,
        tier: str,
        queue: str,
        region: str,
        match_region: str,
        match_queue: int,
        match_type: str,
        top: int | None,
        matches_per_player: int,
        min_patch: str | None
) -> None:
    """
    Collect matches for a single tier.
    """
    min_version = parse_version(min_patch) if min_patch else (0, 0)
    cursor = conn.cursor()

    # Region prefix for match ID validation e.g. "na1" -> "NA1_"
    region_prefix = region.upper() + "_"

    # Highest # match ID known
    # Used to skip API calls preemptively that would skip
    # due to being below min_patch
    old_patch_cutoff: int | None = None

    logger.info("Fetching %s ladder (%s)...", tier, region)
    puuids = _get_puuids_for_tier(
        client=client, tier=tier, queue=queue, region=region, top=top
    )

    if not puuids:
        logger.warning("No players returned for %s. Skipping.", tier)
        return
    
    total_players = len(puuids)
    logger.info("Collecting matches for %d players in %s...", total_players, tier)

    total_matches_in_db = cursor.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0]

    new_matches = 0
    skipped_existing = 0
    skipped_old_patch = 0
    skipped_no_data = 0

    for player_idx, puuid in enumerate(puuids, start=1):
        match_id_list = get_match_ids(
            client=client,
            puuid=puuid,
            region=match_region,
            count=matches_per_player,
            queue=match_queue,
            match_type=match_type
        )

        if not match_id_list:
            continue

        for match_idx, match_id in enumerate(match_id_list, start=1):
            print(
                f"\r[{tier}] Player {player_idx}/{total_players} | "
                f"Match {match_idx}/{len(match_id_list)} | "
                f"Total matches: {total_matches_in_db + new_matches} | "
                f"New: {new_matches} | "
                f"Skipped (exists): {skipped_existing} | "
                f"Skipped (patch): {skipped_old_patch}"
                f"{'':10}",
                end="", flush=True
            )

            if not match_id.startswith(region_prefix):
                skipped_no_data += 1
                continue

            if old_patch_cutoff is not None:
                try:
                    match_num = int(match_id.split("_")[1])
                    if match_num <= old_patch_cutoff:
                        skipped_old_patch += len(match_id_list) - match_idx + 1
                        break
                except (IndexError, ValueError):
                    pass

            if raw_match_exists(cursor, match_id):
                skipped_existing += 1
                continue

            raw_match = get_match(client=client, match_id=match_id, region=match_region)

            if not raw_match:
                skipped_no_data += 1
                continue

            # Parse version for patch filtering and storage
            full_version = raw_match.get("info", {}).get("gameVersion", "")
            game_version = normalize_version(full_version)

            if min_patch and parse_version(game_version) < min_version:
                try:
                    match_num = int(match_id.split("_")[1])
                    if old_patch_cutoff is None or match_num > old_patch_cutoff:
                        old_patch_cutoff = match_num
                except (IndexError, ValueError):
                    pass
                skipped_old_patch += len(match_id_list) - match_idx + 1
                del raw_match
                break

            match_id_from_data = raw_match.get("metadata", {}).get("matchId")
            if not match_id_from_data:
                skipped_no_data += 1
                del raw_match
                continue

            collected_at = datetime.now(timezone.utc).isoformat()

            insert_raw_match(
                cursor=cursor,
                match_id=match_id_from_data,
                game_version=game_version,
                tier=tier,
                collected_at=collected_at,
                data=json.dumps(raw_match)
            )
            conn.commit()
            new_matches += 1
            del raw_match

    print(
        f"\r[{tier}] Player {total_players}/{total_players} | "
        f"Done | "
        f"Total matches: {total_matches_in_db + new_matches} | "
        f"New: {new_matches} | "
        f"Skipped (exists): {skipped_existing} | "
        f"Skipped (patch): {skipped_old_patch}"
        f"{'':10}"
    )

    logger.info(
        "Collection complete for %s. Total: %d | New: %d | Exists %d | Old patch: %d | No data: %d",
        tier, (total_matches_in_db + new_matches), new_matches, skipped_existing, skipped_old_patch, skipped_no_data
    )