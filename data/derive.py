"""
derive.py

Computes all derived tables from the clean database layer.

Derived tables:
    champion_stats      — win rates + avg stats per champion/lane/patch/tier
    champion_presence   — pick/ban/presence rates per champion/patch/tier
    lane_matchups       — raw head-to-head matchup events per lane per match
    matchup_stats       — aggregated matchup win rates per champion pair
    champion_synergies  — win rates for champion pairs on the same team
"""

import logging
import sqlite3

from data.database import (
    connect,
    create_derived_schema,
    insert_champion_stats,
    insert_champion_presence,
    insert_lane_matchup,
    insert_matchup_stats,
    insert_champion_synergy,
)

logger = logging.getLogger(__name__)

def derive(
    clean_db_path: str,
    derived_db_path: str,
):
    """
    Compute all derived tables from the clean database.

    Args:
        clean_db_path (str): Path to the clean SQLite database.
        derived_db_path (str): Path to the derived SQLite database.
    """
    clean_conn = connect(clean_db_path)
    derived_conn = connect(derived_db_path)
    create_derived_schema(derived_conn)

    clean_cursor = clean_conn.cursor()
    derived_cursor = derived_conn.cursor()

    logger.info("Deriving champion_stats...")
    n = _derive_champion_stats(clean_cursor, derived_cursor)
    derived_conn.commit()
    logger.info("  champion_stats: %d rows", n)

    logger.info("Deriving champion_presence...")
    n = _derive_champion_presence(clean_cursor, derived_cursor)
    derived_conn.commit()
    logger.info("  champion_presence: %d rows", n)

    logger.info("Deriving lane_matchups...")
    n = _derive_lane_matchups(clean_cursor, derived_cursor)
    derived_conn.commit()
    logger.info("  lane_matchups: %d rows", n)

    logger.info("Deriving matchup_stats...")
    n = _derive_matchup_stats(derived_cursor)
    derived_conn.commit()
    logger.info("  matchup_stats: %d rows", n)

    logger.info("Deriving champion_synergies...")
    n = _derive_champion_synergies(clean_cursor, derived_cursor)
    derived_conn.commit()
    logger.info("  champion_synergies: %d rows", n)

    logger.info("Derivation complete.")

    clean_conn.close()
    derived_conn.close()

# --------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------

def _derive_champion_stats(clean_cursor: sqlite3.Cursor, derived_cursor: sqlite3.Cursor) -> int:
    """Compute and insert champion_stats rows. Returns number of rows inserted."""
    rows = clean_cursor.execute("""
        SELECT
            p.champion_name,
            p.lane,
            m.game_version,
            m.tier,
            COUNT(*) AS games,
            SUM(p.win) AS wins,
            ROUND(CAST(SUM(p.win) AS REAL) / COUNT(*), 4) AS win_rate,
            ROUND(AVG(p.kills), 2) AS avg_kills,
            ROUND(AVG(p.deaths), 2) AS avg_deaths,
            ROUND(AVG(p.assists), 2) AS avg_assists,
            ROUND(AVG(CAST(p.kills + p.assists AS REAL) / MAX(p.deaths, 1)), 2) AS avg_kda,
            ROUND(AVG(p.gold_earned), 0) AS avg_gold_earned,
            ROUND(AVG(p.minions_killed + p.neutral_minions_killed), 1) AS avg_cs,
            ROUND(AVG(p.total_damage_dealt_to_champions), 0) AS avg_damage_to_champions,
            ROUND(AVG(p.total_damage_taken), 0) AS avg_damage_taken,
            ROUND(AVG(p.damage_self_mitigated), 0) AS avg_damage_mitigated,
            ROUND(AVG(p.vision_score), 1) AS avg_vision_score
        FROM participants p
        JOIN matches m ON p.match_id = m.id
        WHERE p.champion_name IS NOT NULL
          AND p.lane != ''
        GROUP BY p.champion_name, p.lane, m.game_version, m.tier
    """).fetchall()

    columns = (
        "champion", "lane", "game_version", "tier",
        "games", "wins", "win_rate",
        "avg_kills", "avg_deaths", "avg_assists", "avg_kda",
        "avg_gold_earned", "avg_cs",
        "avg_damage_to_champions", "avg_damage_taken", "avg_damage_mitigated",
        "avg_vision_score",
    )

    for row in rows:
        insert_champion_stats(derived_cursor, dict(zip(columns, row)))

    return len(rows)


def _derive_champion_presence(clean_cursor: sqlite3.Cursor, derived_cursor: sqlite3.Cursor) -> int:
    """Compute and insert champion_presence rows. Returns number of rows inserted."""

    # Total matches per game_version + tier (denominator for all rates)
    totals = {
        (row[0], row[1]): row[2]
        for row in clean_cursor.execute("""
            SELECT game_version, tier, COUNT(*) AS total_matches
            FROM matches
            GROUP BY game_version, tier
        """).fetchall()
    }

    # Picks per champion per lane per version/tier
    picks_rows = clean_cursor.execute("""
        SELECT
            p.champion_name,
            p.lane,
            m.game_version,
            m.tier,
            COUNT(DISTINCT p.match_id) AS picks
        FROM participants p
        JOIN matches m ON p.match_id = m.id
        WHERE p.champion_name IS NOT NULL
          AND p.lane != ''
        GROUP BY p.champion_name, p.lane, m.game_version, m.tier
    """).fetchall()

    # Bans per champion per version/tier
    bans_rows = clean_cursor.execute("""
        SELECT
            tb.champion_id,
            m.game_version,
            m.tier,
            COUNT(*) AS bans
        FROM team_bans tb
        JOIN matches m ON tb.match_id = m.id
        WHERE tb.champion_id != -1
        GROUP BY tb.champion_id, m.game_version, m.tier
    """).fetchall()

    # Build picks dict: {(champion, version, tier): {lane: count}}
    picks: dict = {}
    for champion, lane, version, tier, count in picks_rows:
        key = (champion, version, tier)
        if key not in picks:
            picks[key] = {}
        picks[key][lane] = count

    champion_id_to_name = {
        row[0]: row[1]
        for row in clean_cursor.execute(
            "SELECT DISTINCT champion_id, champion_name FROM participants WHERE champion_name IS NOT NULL"
        ).fetchall()
    }

    bans: dict = {}
    for champion_id, version, tier, count in bans_rows:
        champion = champion_id_to_name.get(champion_id)
        if not champion:
            continue
        key = (champion, version, tier)
        bans[key] = bans.get(key, 0) + count

    # Collect all unique (champion, version, tier) keys
    all_keys = set(picks.keys()) | set(bans.keys())

    for champion, version, tier in all_keys:
        total_matches = totals.get((version, tier), 0)
        if total_matches == 0:
            continue

        lane_picks = picks.get((champion, version, tier), {})
        total_bans = bans.get((champion, version, tier), 0)

        picks_top = lane_picks.get("TOP", 0)
        picks_jungle = lane_picks.get("JUNGLE", 0)
        picks_middle = lane_picks.get("MIDDLE", 0)
        picks_bottom = lane_picks.get("BOTTOM", 0)
        picks_support = lane_picks.get("UTILITY", 0)

        total_picks = picks_top + picks_jungle + picks_middle + picks_bottom + picks_support
        presence = min((total_picks + total_bans) / total_matches, 1.0)

        insert_champion_presence(derived_cursor, {
            "champion": champion,
            "game_version": version,
            "tier": tier,
            "total_matches": total_matches,
            "picks_top": picks_top,
            "picks_jungle": picks_jungle,
            "picks_middle": picks_middle,
            "picks_bottom": picks_bottom,
            "picks_support": picks_support,
            "pick_rate_top": round(picks_top / total_matches, 4),
            "pick_rate_jungle": round(picks_jungle / total_matches, 4),
            "pick_rate_middle": round(picks_middle / total_matches, 4),
            "pick_rate_bottom": round(picks_bottom / total_matches, 4),
            "pick_rate_support": round(picks_support / total_matches, 4),
            "bans": total_bans,
            "ban_rate": round(total_bans / total_matches, 4),
            "presence_rate": round(presence, 4),
        })

    return len(all_keys)


def _derive_lane_matchups(clean_cursor: sqlite3.Cursor, derived_cursor: sqlite3.Cursor) -> int:
    """
    Compute and insert lane_matchups rows.
    Joins participants on same match, same lane, different team.
    Returns number of rows inserted.
    """
    rows = clean_cursor.execute("""
        SELECT
            p1.match_id,
            p1.lane,
            p1.champion_name AS champ_blue,
            p2.champion_name AS champ_red,
            p1.win AS blue_win,
            m.game_version,
            m.tier
        FROM participants p1
        JOIN participants p2
            ON  p1.match_id = p2.match_id
            AND p1.lane = p2.lane
            AND p1.team_id = 100
            AND p2.team_id = 200
        JOIN matches m ON p1.match_id = m.id
        WHERE p1.champion_name IS NOT NULL
          AND p2.champion_name IS NOT NULL
          AND p1.lane != ''
    """).fetchall()

    columns = ("match_id", "lane", "champ_blue", "champ_red", "blue_win", "game_version", "tier")
    for row in rows:
        insert_lane_matchup(derived_cursor, dict(zip(columns, row)))

    return len(rows)


def _derive_matchup_stats(derived_cursor: sqlite3.Cursor) -> int:
    """
    Aggregate lane_matchups into matchup_stats.
    champion is always alphabetically before opponent.
    Returns number of rows inserted.
    """
    rows = derived_cursor.execute("""
        SELECT lane, champ_blue, champ_red, game_version, tier,
               SUM(blue_win) AS blue_wins, COUNT(*) AS games
        FROM lane_matchups
        GROUP BY lane, champ_blue, champ_red, game_version, tier
    """).fetchall()

    count = 0
    for lane, champ_blue, champ_red, game_version, tier, blue_wins, games in rows:
        # Enforce alphabetical ordering
        if champ_blue <= champ_red:
            champion, opponent = champ_blue, champ_red
            champion_wins = blue_wins
        else:
            champion, opponent = champ_red, champ_blue
            champion_wins = games - blue_wins

        win_rate = round(champion_wins / games, 4) if games > 0 else 0.0

        insert_matchup_stats(derived_cursor, {
            "champion": champion,
            "opponent": opponent,
            "lane": lane,
            "game_version": game_version,
            "tier": tier,
            "games": games,
            "champion_wins": champion_wins,
            "champion_win_rate": win_rate,
        })
        count += 1

    return count


def _derive_champion_synergies(clean_cursor: sqlite3.Cursor, derived_cursor: sqlite3.Cursor) -> int:
    """
    Compute champion synergies from participants on the same team.
    champion_a is always alphabetically before champion_b.
    Returns number of rows inserted.
    """
    rows = clean_cursor.execute("""
        SELECT
            p1.champion_name,
            p1.lane,
            p2.champion_name,
            p2.lane,
            m.game_version,
            m.tier,
            p1.win
        FROM participants p1
        JOIN participants p2
            ON  p1.match_id = p2.match_id
            AND p1.team_id = p2.team_id
            AND p1.puuid < p2.puuid
        JOIN matches m ON p1.match_id = m.id
        WHERE p1.champion_name IS NOT NULL
          AND p2.champion_name IS NOT NULL
          AND p1.lane != ''
          AND p2.lane != ''
    """).fetchall()

    # Aggregate in Python to enforce alphabetical ordering
    synergy: dict = {}
    for champ1, lane1, champ2, lane2, game_version, tier, win in rows:
        # Enforce alphabetical ordering
        if (champ1, lane1) <= (champ2, lane2):
            a, la, b, lb = champ1, lane1, champ2, lane2
        else:
            a, la, b, lb = champ2, lane2, champ1, lane1

        key = (a, la, b, lb, game_version, tier)
        if key not in synergy:
            synergy[key] = {"games": 0, "wins": 0}
        synergy[key]["games"] += 1
        synergy[key]["wins"] += win

    for (a, la, b, lb, game_version, tier), stats in synergy.items():
        games = stats["games"]
        wins = stats["wins"]
        insert_champion_synergy(derived_cursor, {
            "champion_a": a,
            "lane_a": la,
            "champion_b": b,
            "lane_b": lb,
            "game_version": game_version,
            "tier": tier,
            "games": games,
            "wins": wins,
            "win_rate": round(wins / games, 4) if games > 0 else 0.0,
        })

    return len(synergy)