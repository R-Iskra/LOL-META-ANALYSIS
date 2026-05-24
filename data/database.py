"""
database.py

Schema management and insert functions for all three data layers.

SQL schemas live in /sql/.
"""

import sqlite3
from pathlib import Path

from utils import parse_version

# --------------------------------------------------------------------
# Path resolution
# --------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SQL_DIR = _PROJECT_ROOT / "sql"

_RAW_SQL_FILES = [
    _SQL_DIR / "raw" / "create_raw.sql"
]

_CLEAN_SQL_FILES = [
    _SQL_DIR / "clean" / "create_matches.sql",
    _SQL_DIR / "clean" / "create_participants.sql",
    _SQL_DIR / "clean" / "create_teams.sql",
    _SQL_DIR / "clean" / "create_perks.sql"
]

_DERIVED_SQL_FILES = [
    _SQL_DIR / "derived" / "create_champion_stats.sql",
    _SQL_DIR / "derived" / "create_champion_presence.sql",
    _SQL_DIR / "derived" / "create_matchups.sql",
    _SQL_DIR / "derived" / "create_synergies.sql"
]

# --------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# --------------------------------------------------------------------
# Schema creation
# --------------------------------------------------------------------

def _execute_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    with open(path, "r") as f:
        conn.executescript(f.read())

def create_raw_schema(conn: sqlite3.Connection) -> None:
    for path in _RAW_SQL_FILES:
        _execute_sql_file(conn, path)

def create_clean_schema(conn: sqlite3.Connection) -> None:
    for path in _CLEAN_SQL_FILES:
        _execute_sql_file(conn, path)

def create_derived_schema(conn: sqlite3.Connection) -> None:
    for path in _DERIVED_SQL_FILES:
        _execute_sql_file(conn, path)

# --------------------------------------------------------------------
# Raw layer inserts
# --------------------------------------------------------------------

def insert_raw_match(cursor: sqlite3.Cursor, match_id: str, game_version: str,
                     tier: str, collected_at: str, data: str) -> None:
    cursor.execute(
        """
        INSERT OR IGNORE INTO raw_matches (match_id, game_version, tier, collected_at, data)
        VALUES (?, ?, ?, ?, ?)
        """,
        (match_id, game_version, tier, collected_at, data)
    )

# --------------------------------------------------------------------
# Clean layer inserts
# --------------------------------------------------------------------

def insert_match(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected Keys: id, game_version, tier, game_duration, game_start,
                    end_of_game_result
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO matches
            (id, game_version, tier, game_duration, game_start,
            end_of_game_result)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["game_version"],
            row["tier"],
            row["game_duration"],
            row["game_start"],
            row.get("end_of_game_result")
        )
    )

def insert_participant(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys match the participants table columns exactly.
    """
    keys = (
        "match_id", "puuid",
        "champion_name", "champion_id", "champ_level", "team_id", "lane",
        "win",
        "kills", "deaths", "assists",
        "gold_earned", "gold_spent",
        "minions_killed", "neutral_minions_killed",
        "vision_score", "wards_placed", "control_wards_bought",
        "total_damage_dealt", "total_damage_dealt_to_champions",
        "physical_damage_dealt", "physical_damage_dealt_to_champions",
        "magic_damage_dealt", "magic_damage_dealt_to_champions",
        "true_damage_dealt", "true_damage_dealt_to_champions",
        "damage_to_buildings", "damage_to_objectives", "damage_to_turrets",
        "total_damage_taken", "damage_self_mitigated",
        "total_heal", "heals_on_teammates",
        "total_cc_dealt", "longest_time_living",
        "turret_kills", "inhibitor_kills", "dragon_kills", "baron_kills",
        "summoner1_id", "summoner2_id",
        "item0", "item1", "item2", "item3", "item4", "item5", "item6"
    )
    values = tuple(row.get(k) for k in keys)
    placeholders = ", ".join("?" * len(keys))
    cursor.execute(
        f"INSERT OR IGNORE INTO participants ({', '.join(keys)}) VALUES ({placeholders})",
        values
    )

def insert_team(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, team_id, win
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO teams (match_id, team_id, win)
        VALUES (?, ?, ?)
        """,
        (row["match_id"], row["team_id"], row["win"])
    )

def insert_team_objective(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, team_id, objective_name, first, kills
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO team_objectives
            (match_id, team_id, objective_name, first, kills)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["match_id"],
            row["team_id"],
            row["objective_name"],
            row.get("first"),
            row.get("kills")
        )
    )

def insert_team_ban(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, team_id, pick_turn, champion_id
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO team_bans
            (match_id, team_id, pick_turn, champion_id)
        VALUES (?, ?, ?, ?)
        """,
        (row["match_id"], row["team_id"], row["pick_turn"], row.get("champion_id"))
    )

def insert_perk_stats(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, puuid, defense, flex, offense
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO perk_stats (match_id, puuid, defense, flex, offense)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["match_id"],
            row["puuid"],
            row.get("defense"),
            row.get("flex"),
            row.get("offense")
        )
    )

def insert_perk_style(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, puuid, style_order, style_id, description
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO perk_styles
            (match_id, puuid, style_order, style_id, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["match_id"],
            row["puuid"],
            row["style_order"],
            row["style_id"],
            row.get("description")
        )
    )

def insert_perk_selection(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, puuid, style_order, perk_id, var1, var2, var3
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO perk_selections
            (match_id, puuid, style_order, perk_id, var1, var2, var3)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["match_id"],
            row["puuid"],
            row["style_order"],
            row["perk_id"],
            row.get("var1"),
            row.get("var2"),
            row.get("var3")
        )
    )

# --------------------------------------------------------------------
# Derived layer inserts
# --------------------------------------------------------------------

def insert_champion_stats(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys match the champion_stats table columns exactly.
    """
    keys = (
        "champion", "lane", "game_version", "tier",
        "games", "wins", "win_rate",
        "avg_kills", "avg_deaths", "avg_assists", "avg_kda",
        "avg_gold_earned", "avg_cs",
        "avg_damage_to_champions", "avg_damage_taken", "avg_damage_mitigated",
        "avg_vision_score"
    )
    values = tuple(row.get(k) for k in keys)
    placeholders = ", ".join("?" * len(keys))
    cursor.execute(
        f"INSERT OR REPLACE INTO champion_stats ({', '.join(keys)}) VALUES ({placeholders})",
        values
    )

def insert_champion_presence(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys match the champion_presence table columns exactly.
    """
    keys = (
        "champion", "game_version", "tier", "total_matches",
        "picks_top", "picks_jungle", "picks_middle", "picks_bottom", "picks_support",
        "pick_rate_top", "pick_rate_jungle", "pick_rate_middle", 
        "pick_rate_bottom", "pick_rate_support",
        "bans", "ban_rate", "presence_rate"
    )
    values = tuple(row.get(k) for k in keys)
    placeholders = ", ".join("?" * len(keys))
    cursor.execute(
        f"INSERT OR REPLACE INTO champion_presence ({', '.join(keys)}) VALUES ({placeholders})",
        values
    )

def insert_lane_matchup(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    Expected keys: match_id, lane, champ_blue, champ_red, blue_win,
    game_version, tier
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO lane_matchups
            (match_id, lane, champ_blue, champ_red, blue_win, game_version, tier)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["match_id"],
            row["lane"],
            row["champ_blue"],
            row["champ_red"],
            row["blue_win"],
            row["game_version"],
            row["tier"]
        )
    )

def insert_matchup_stats(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    champion should be alphabetically before opponent.

    Expected keys: champion, opponent, lane, tier, games, champion_wins,
                    champion_win_rate
    """
    cursor.execute(
        """
        INSERT OR REPLACE INTO matchup_stats
            (champion, opponent, lane, game_version, tier, games, champion_wins, champion_win_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["champion"],
            row["opponent"],
            row["lane"],
            row["game_version"],
            row["tier"],
            row["games"],
            row["champion_wins"],
            row["champion_win_rate"]
        )
    )

def insert_champion_synergy(cursor: sqlite3.Cursor, row: dict) -> None:
    """
    champion_a should be alphabetically before champion_b.

    Expected keys: champion_a, lane_a, champion_b, lane_b, tier,
                    games, wins, win_rate
    """
    cursor.execute(
        """
        INSERT OR REPLACE INTO champion_synergies
            (champion_a, lane_a, champion_b, lane_b, game_version, tier, games, wins, win_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["champion_a"],
            row["lane_a"],
            row["champion_b"],
            row["lane_b"],
            row["game_version"],
            row["tier"],
            row["games"],
            row["wins"],
            row["win_rate"]
        )
    )

# --------------------------------------------------------------------
# Utility
# --------------------------------------------------------------------

def raw_match_exists(cursor: sqlite3.Cursor, match_id: str) -> bool:
    cursor.execute("SELECT 1 FROM raw_matches WHERE match_id = ?", (match_id,))
    return cursor.fetchone() is not None

def clean_match_exists(cursor: sqlite3.Cursor, match_id: str) -> bool:
    cursor.execute("SELECT 1 FROM matches WHERE id = ?", (match_id,))
    return cursor.fetchone() is not None

def delete_raw_patches_below(conn: sqlite3.Connection, min_version: str) -> int:
    """
    Delete all raw_matches with a game_version older than min_version.
    Patch strings are compared (major, minor).

    Args:
        conn: Active database connection.
        min_version (str): Minimum patch to keep, e.g. "15.15".

    Returns:
        int: Number of rows deleted.
    """
        
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT game_version FROM raw_matches")
    versions = [row[0] for row in cursor.fetchall()]

    keep = parse_version(min_version)
    to_delete = [v for v in versions if parse_version(v) < keep]

    if not to_delete:
        return 0
    
    cursor.executemany(
        "DELETE FROM raw_matches WHERE game_version = ?",
        [(v,) for v in to_delete]
    )
    conn.commit()
    return cursor.rowcount