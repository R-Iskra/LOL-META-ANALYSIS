"""
cleaner.py

Reads the match JSON blobs from the raw database and parses them
into the clean relational tables in the clean database.
"""

import json
import logging
import sqlite3

from data.database import (
    connect,
    create_clean_schema,
    clean_match_exists,
    insert_match,
    insert_participant,
    insert_team,
    insert_team_objective,
    insert_team_ban,
    insert_perk_stats,
    insert_perk_style,
    insert_perk_selection
)
from utils import parse_version, normalize_version

logger = logging.getLogger(__name__)

def clean(
        raw_db_path: str,
        clean_db_path: str,
        min_duration: int | None = None,
        min_patch: str | None = None
):
    """
    Parse raw match JSON blobs into clean relational tables.

    Args:
        raw_db_path (str): Path to the raw SQLite database.
        clean_db_path (str): Path to the clean SQLite database.
        min_duration (int, optional): Minimum game duration in seconds.
        min_patch (str, optional): Minimum patch to clean e.g. "15.15".
    """
    min_version = parse_version(min_patch) if min_patch else (0, 0)

    raw_conn = connect(raw_db_path)
    clean_conn = connect(clean_db_path)
    create_clean_schema(clean_conn)

    raw_cursor = raw_conn.cursor()
    clean_cursor = clean_conn.cursor()

    total = raw_cursor.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0]

    processed = 0
    cleaned = 0
    already_cleaned = 0
    filtered = 0
    errors = 0

    for match_id, tier, raw_data in raw_cursor.execute(
        "SELECT match_id, tier, data FROM raw_matches"
    ):
        processed += 1
        print(
            f"\rProcessed {processed}/{total} | "
            f"Cleaned: {cleaned} | "
            f"Already cleaned: {already_cleaned} | "
            f"Filtered: {filtered} | "
            f"Errors: {errors}"
            f"{'':10}",
            end="", flush=True
        )

        if clean_match_exists(clean_cursor, match_id):
            already_cleaned += 1
            continue

        try:
            match_json = json.loads(raw_data)
            metadata = match_json["metadata"]
            info = match_json["info"]

            if info.get("endOfGameResult") != "GameComplete":
                filtered += 1
                continue

            if min_duration and info.get("gameDuration", 0) < min_duration:
                filtered += 1
                continue

            game_version = normalize_version(info.get("gameVersion", ""))
            if min_patch and parse_version(game_version) < min_version:
                filtered += 1
                continue

            match_id_from_data = metadata.get("matchId")

            insert_match(clean_cursor, {
                "id": match_id_from_data,
                "game_version": game_version,
                "tier": tier,
                "game_duration": info.get("gameDuration"),
                "game_start": info.get("gameStartTimestamp"),
                "end_of_game_result": info.get("endOfGameResult")
            })

            for p in info.get("participants", []):
                _parse_participant(clean_cursor, match_id_from_data, p)
            
            for t in info.get("teams", []):
                _parse_team(clean_cursor, match_id_from_data, t)

            clean_conn.commit()
            cleaned += 1
        
        except Exception as e:
            print("")
            logger.error("Error processing match %s: %s", match_id, e)
            errors += 1
            continue
    
    print(
        f"\rProcessed {processed}/{total} | "
        f"Cleaned: {cleaned} | "
        f"Already cleaned: {already_cleaned} | "
        f"Filtered: {filtered} | "
        f"Errors: {errors}"
        f"{'':10}"
    )

    logger.info(
        "Cleaning complete. Cleaned: %d | Already cleaned: %d | Filtered: %d | Errors: %d",
        cleaned, already_cleaned, filtered, errors
    )

    raw_conn.close()
    clean_conn.close()

# --------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------

def _parse_participant(cursor: sqlite3.Cursor, match_id: str, p: dict) -> None:
    insert_participant(cursor, {
        "match_id": match_id,
        "puuid": p.get("puuid"),
        "champion_name": p.get("championName"),
        "champion_id": p.get("championId"),
        "champ_level": p.get("champLevel"),
        "team_id": p.get("teamId"),
        "lane": p.get("teamPosition"),
        "win": int(p.get("win", False)),
        "kills": p.get("kills"),
        "deaths": p.get("deaths"),
        "assists": p.get("assists"),
        "gold_earned": p.get("goldEarned"),
        "gold_spent": p.get("goldSpent"),
        "minions_killed": p.get("totalMinionsKilled"),
        "neutral_minions_killed": p.get("neutralMinionsKilled"),
        "vision_score": p.get("visionScore"),
        "wards_placed": p.get("wardsPlaced"),
        "control_wards_bought": p.get("visionWardsBoughtInGame"),
        "total_damage_dealt": p.get("totalDamageDealt"),
        "total_damage_dealt_to_champions": p.get("totalDamageDealtToChampions"),
        "physical_damage_dealt": p.get("physicalDamageDealt"),
        "physical_damage_dealt_to_champions": p.get("physicalDamageDealtToChampions"),
        "magic_damage_dealt": p.get("magicDamageDealt"),
        "magic_damage_dealt_to_champions": p.get("magicDamageDealtToChampions"),
        "true_damage_dealt": p.get("trueDamageDealt"),
        "true_damage_dealt_to_champions": p.get("trueDamageDealtToChampions"),
        "damage_to_buildings": p.get("damageDealtToBuildings"),
        "damage_to_objectives": p.get("damageDealtToObjectives"),
        "damage_to_turrets": p.get("damageDealtToTurrets"),
        "total_damage_taken": p.get("totalDamageTaken"),
        "damage_self_mitigated": p.get("damageSelfMitigated"),
        "total_heal": p.get("totalHeal"),
        "heals_on_teammates": p.get("totalHealsOnTeammates"),
        "total_cc_dealt": p.get("totalTimeCCDealt"),
        "longest_time_living": p.get("longestTimeSpentLiving"),
        "turret_kills": p.get("turretKills"),
        "inhibitor_kills": p.get("inhibitorKills"),
        "dragon_kills": p.get("dragonKills"),
        "baron_kills": p.get("baronKills"),
        "summoner1_id": p.get("summoner1Id"),
        "summoner2_id": p.get("summoner2Id"),
        "item0": p.get("item0"),
        "item2": p.get("item1"),
        "item2": p.get("item2"),
        "item3": p.get("item3"),
        "item4": p.get("item4"),
        "item5": p.get("item5"),
        "item6": p.get("item6")
    })

    perks = p.get("perks", {})
    stat_perks = perks.get("statPerks", {})

    insert_perk_stats(cursor, {
        "match_id": match_id,
        "puuid": p.get("puuid"),
        "defense": stat_perks.get("defense"),
        "flex": stat_perks.get("flex"),
        "offense": stat_perks.get("offense")
    })

    for idx, style in enumerate(perks.get("styles", [])):
        insert_perk_style(cursor, {
            "match_id": match_id,
            "puuid": p.get("puuid"),
            "style_order": idx,
            "style_id": style.get("style"),
            "description": style.get("description")
        })
        for sel in style.get("selections", []):
            insert_perk_selection(cursor, {
                "match_id": match_id,
                "puuid": p.get("puuid"),
                "style_order": idx,
                "perk_id": sel.get("perk"),
                "var1": sel.get("var1"),
                "var2": sel.get("var2"),
                "var3": sel.get("var3")
            })

def _parse_team(cursor: sqlite3.Cursor, match_id: str, t: dict) -> None:
    insert_team(cursor, {
        "match_id": match_id,
        "team_id": t.get("teamId"),
        "win": int(t.get("win", False))
    })

    for obj_name, obj_vals in t.get("objectives", {}).items():
        insert_team_objective(cursor, {
            "match_id": match_id,
            "team_id": t.get("teamId"),
            "objective_name": obj_name,
            "first": int(obj_vals.get("first", False)),
            "kills": obj_vals.get("kills")
        })
    
    for ban in t.get("bans", []):
        insert_team_ban(cursor, {
            "match_id": match_id,
            "team_id": t.get("teamId"),
            "pick_turn": ban.get("pickTurn"),
            "champion_id": ban.get("championId")
        })