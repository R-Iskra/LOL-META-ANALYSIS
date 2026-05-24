"""
champions.py

Analysis functions for champion level insights.
"""

import sqlite3
 
import pandas as pd

from utils import parse_version
 
# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------
 
MASTER_PLUS = ["CHALLENGER", "GRANDMASTER", "MASTER"]
DIAMOND_PLUS = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND"]
EMERALD_PLUS = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "EMERALD"]
PLATINUM_PLUS = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "EMERALD", "PLATINUM"]
 
LANES = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
 
# --------------------------------------------------------------------
# Champion overview
# --------------------------------------------------------------------
 
def get_champion_stats(
    db_path: str,
    champion: str,
    lane: str | None = None,
    tier: str | list[str] | None = None,
    version: str | list[str] | None = None,
    min_games: int = 30,
) -> pd.DataFrame:
    """
    Get win rate and average performance stats for a specific champion.
    Aggregates across tiers/versions if multiple are supplied.
 
    Args:
        db_path (str): Path to the derived database.
        champion (str): Champion name e.g. "Ahri".
        lane (str, optional): Lane filter e.g. "MIDDLE". None = all lanes.
        tier: Tier filter. None = all tiers.
        version: Patch filter. None = all patches.
        min_games (int): Minimum games threshold. Defaults to 30.
 
    Returns:
        pd.DataFrame with columns: lane, games, wins, win_rate, avg_kills,
        avg_deaths, avg_assists, avg_kda, avg_gold_earned, avg_cs,
        avg_damage_to_champions, avg_damage_taken, avg_damage_mitigated,
        avg_vision_score. Sorted by game_version descending.
    """
    conn = sqlite3.connect(db_path)

    tier_sql, tier_params = _tier_filter(tier)
    version_sql, version_params = _version_filter(version)
    lane_sql = "AND lane = ?" if lane else ""
    lane_params = [lane] if lane else []
 
    query = f"""
        SELECT
            lane,
            game_version,
            SUM(games) AS games,
            SUM(wins) AS wins,
            ROUND(CAST(SUM(wins) AS REAL) / SUM(games), 4) AS win_rate,
            ROUND(SUM(avg_kills * games) / SUM(games), 2) AS avg_kills,
            ROUND(SUM(avg_deaths * games) / SUM(games), 2) AS avg_deaths,
            ROUND(SUM(avg_assists * games) / SUM(games), 2) AS avg_assists,
            ROUND(SUM(avg_kda * games) / SUM(games), 2) AS avg_kda,
            ROUND(SUM(avg_gold_earned * games) / SUM(games), 0) AS avg_gold_earned,
            ROUND(SUM(avg_cs * games) / SUM(games), 1) AS avg_cs,
            ROUND(SUM(avg_damage_to_champions * games) / SUM(games), 0) AS avg_damage_to_champions,
            ROUND(SUM(avg_damage_taken * games) / SUM(games), 0) AS avg_damage_taken,
            ROUND(SUM(avg_damage_mitigated * games) / SUM(games), 0) AS avg_damage_mitigated,
            ROUND(SUM(avg_vision_score * games) / SUM(games), 1) AS avg_vision_score
        FROM champion_stats
        WHERE champion = ?
          {lane_sql}
          {tier_sql}
          {version_sql}
        GROUP BY lane, game_version
        HAVING SUM(games) >= ?
        ORDER BY game_version DESC
    """
 
    params = [champion] + lane_params + tier_params + version_params + [min_games]
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df
 
def get_best_champions(
    db_path: str,
    lane: str,
    tier: str | list[str] | None = None,
    version: str | list[str] | None = None,
    min_games: int = 30,
) -> pd.DataFrame:
    """
    Get champions ranked by win rate for a given lane.
    Aggregates across tiers/versions if multiple are supplied.
 
    Args:
        db_path (str): Path to the derived database.
        lane (str): Lane to query e.g. "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY".
        tier: Tier filter. None = all tiers.
        version: Patch filter. None = all patches.
        min_games (int): Minimum games threshold. Defaults to 30.
 
    Returns:
        pd.DataFrame sorted by win_rate descending with columns:
        champion, games, wins, win_rate, avg_kda, avg_cs, avg_damage_to_champions.
    """
    conn = sqlite3.connect(db_path)

    tier_sql, tier_params = _tier_filter(tier)
    version_sql, version_params = _version_filter(version)
 
    query = f"""
        SELECT
            champion,
            SUM(games) AS games,
            SUM(wins) AS wins,
            ROUND(CAST(SUM(wins) AS REAL) / SUM(games), 4) AS win_rate,
            ROUND(SUM(avg_kda * games) / SUM(games), 2) AS avg_kda,
            ROUND(SUM(avg_cs * games) / SUM(games), 1) AS avg_cs,
            ROUND(SUM(avg_damage_to_champions * games) / SUM(games), 0) AS avg_damage_to_champions
        FROM champion_stats
        WHERE lane = ?
          {tier_sql}
          {version_sql}
        GROUP BY champion
        HAVING SUM(games) >= ?
        ORDER BY win_rate DESC
    """
 
    params = [lane] + tier_params + version_params + [min_games]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
 
def get_patch_trends(
    db_path: str,
    champion: str,
    lane: str,
    tier: str | list[str] | None = None,
    min_games: int = 30,
) -> pd.DataFrame:
    """
    Get win rate trend across patches for a champion in a lane.
 
    Args:
        db_path (str): Path to the derived database.
        champion (str): Champion name e.g. "Ahri".
        lane (str): Lane e.g. "MIDDLE".
        tier: Tier filter. None = all tiers.
        min_games (int): Minimum games per patch to include. Defaults to 30.
 
    Returns:
        pd.DataFrame sorted by game_version ascending with columns:
        game_version, games, wins, win_rate, avg_kda, avg_cs,
        avg_damage_to_champions.
    """
    conn = sqlite3.connect(db_path)

    tier_sql, tier_params = _tier_filter(tier)
 
    query = f"""
        SELECT
            game_version,
            SUM(games) AS games,
            SUM(wins)  AS wins,
            ROUND(CAST(SUM(wins) AS REAL) / SUM(games), 4) AS win_rate,
            ROUND(SUM(avg_kda * games) / SUM(games), 2) AS avg_kda,
            ROUND(SUM(avg_cs * games) / SUM(games), 1) AS avg_cs,
            ROUND(SUM(avg_damage_to_champions * games) / SUM(games), 0) AS avg_damage_to_champions
        FROM champion_stats
        WHERE champion = ?
          AND lane = ?
          {tier_sql}
        GROUP BY game_version
        HAVING SUM(games) >= ?
        ORDER BY game_version ASC
    """
 
    params = [champion, lane] + tier_params + [min_games]
    df = pd.read_sql_query(query, conn, params=params)
    df["_sort_key"] = df["game_version"].apply(parse_version)
    df = df.sort_values("_sort_key").drop(columns="_sort_key").reset_index(drop=True)
    conn.close()
    return df
 
# --------------------------------------------------------------------
# Matchups
# --------------------------------------------------------------------
 
def get_matchups(
    db_path: str,
    champion: str,
    lane: str,
    tier: str | list[str] | None = None,
    version: str | list[str] | None = None,
    min_games: int = 10,
) -> pd.DataFrame:
    """
    Get matchup win rates for a champion against all opponents in a lane.
 
    Args:
        db_path (str): Path to the derived database.
        champion (str): Champion name e.g. "Ahri".
        lane (str): Lane e.g. "MIDDLE".
        tier: Tier filter. None = all tiers.
        version: Patch filter. None = all patches.
        min_games (int): Minimum games per matchup. Defaults to 10.
 
    Returns:
        pd.DataFrame sorted by win_rate descending with columns:
        opponent, games, champion_wins, win_rate.
    """
    conn = sqlite3.Connection(db_path)

    tier_sql, tier_params = _tier_filter(tier)
    version_sql, version_params = _version_filter(version)
 
    query = f"""
        SELECT
            CASE
                WHEN champion = ? THEN opponent
                ELSE champion
            END AS opponent,
            SUM(games) AS games,
            SUM(CASE WHEN champion = ? THEN champion_wins
                     ELSE games - champion_wins END) AS champion_wins,
            ROUND(
                CAST(SUM(CASE WHEN champion = ? THEN champion_wins
                              ELSE games - champion_wins END) AS REAL)
                / SUM(games), 4
            ) AS win_rate
        FROM matchup_stats
        WHERE (champion = ? OR opponent = ?)
          AND lane = ?
          {tier_sql}
          {version_sql}
        GROUP BY opponent
        HAVING SUM(games) >= ?
        ORDER BY win_rate DESC
    """
 
    params = (
        [champion, champion, champion, champion, champion, lane]
        + tier_params
        + version_params
        + [min_games]
    )
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
 
# --------------------------------------------------------------------
# Synergies
# --------------------------------------------------------------------
 
def get_synergies(
    db_path: str,
    champion: str,
    lane: str,
    tier: str | list[str] | None = None,
    version: str | list[str] | None = None,
    min_games: int = 10,
) -> pd.DataFrame:
    """
    Get win rates for champion pairs that include the given champion in the given lane.
 
    Args:
        db_path (str): Path to the derived database.
        champion (str): Champion name e.g. "Ahri".
        lane (str): Lane the champion played e.g. "MIDDLE".
        tier: Tier filter. None = all tiers.
        version: Patch filter. None = all patches.
        min_games (int): Minimum games per synergy pair. Defaults to 10.
 
    Returns:
        pd.DataFrame sorted by win_rate descending with columns:
        ally_champion, ally_lane, games, wins, win_rate.
    """
    conn = sqlite3.Connection(db_path)

    tier_sql, tier_params = _tier_filter(tier)
    version_sql, version_params = _version_filter(version)
 
    query = f"""
        SELECT
            CASE
                WHEN champion_a = ? AND lane_a = ? THEN champion_b
                ELSE champion_a
            END AS ally_champion,
            CASE
                WHEN champion_a = ? AND lane_a = ? THEN lane_b
                ELSE lane_a
            END AS ally_lane,
            SUM(games) AS games,
            SUM(wins) AS wins,
            ROUND(CAST(SUM(wins) AS REAL) / SUM(games), 4) AS win_rate
        FROM champion_synergies
        WHERE (champion_a = ? AND lane_a = ?)
           OR (champion_b = ? AND lane_b = ?)
          {tier_sql}
          {version_sql}
        GROUP BY ally_champion, ally_lane
        HAVING SUM(games) >= ?
        ORDER BY win_rate DESC
    """
 
    params = (
        [champion, lane, champion, lane, champion, lane, champion, lane]
        + tier_params
        + version_params
        + [min_games]
    )
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
 
# --------------------------------------------------------------------
# Presence
# --------------------------------------------------------------------
 
def get_presence(
    db_path: str,
    tier: str | list[str] | None = None,
    version: str | list[str] | None = None,
    min_games: int = 30,
) -> pd.DataFrame:
    """
    Get pick rate, ban rate, and presence rate for all champions.
 
    Args:
        db_path (str): Path to the derived database.
        tier: Tier filter. None = all tiers.
        version: Patch filter. None = all patches.
        min_games (int): Minimum total picks to include a champion. Defaults to 30.
 
    Returns:
        pd.DataFrame sorted by presence_rate descending with columns:
        champion, total_matches, picks_top, picks_jungle, picks_middle,
        picks_bottom, picks_support, pick_rate_top, pick_rate_jungle,
        pick_rate_middle, pick_rate_bottom, pick_rate_support,
        bans, ban_rate, presence_rate.
    """
    conn = sqlite3.Connection(db_path)

    tier_sql, tier_params = _tier_filter(tier)
    version_sql, version_params = _version_filter(version)
 
    query = f"""
        SELECT
            champion,
            SUM(total_matches) AS total_matches,
            SUM(picks_top) AS picks_top,
            SUM(picks_jungle) AS picks_jungle,
            SUM(picks_middle) AS picks_middle,
            SUM(picks_bottom) AS picks_bottom,
            SUM(picks_support) AS picks_support,
            ROUND(CAST(SUM(picks_top) AS REAL) / SUM(total_matches), 4) AS pick_rate_top,
            ROUND(CAST(SUM(picks_jungle) AS REAL) / SUM(total_matches), 4) AS pick_rate_jungle,
            ROUND(CAST(SUM(picks_middle) AS REAL) / SUM(total_matches), 4) AS pick_rate_middle,
            ROUND(CAST(SUM(picks_bottom) AS REAL) / SUM(total_matches), 4) AS pick_rate_bottom,
            ROUND(CAST(SUM(picks_support) AS REAL) / SUM(total_matches), 4) AS pick_rate_support,
            SUM(bans) AS bans,
            ROUND(CAST(SUM(bans) AS REAL) / SUM(total_matches), 4) AS ban_rate,
            ROUND(
                CAST(SUM(picks_top + picks_jungle + picks_middle + picks_bottom + picks_support + bans) AS REAL)
                / SUM(total_matches), 4
            ) AS presence_rate
        FROM champion_presence
        WHERE 1=1
          {tier_sql}
          {version_sql}
        GROUP BY champion
        HAVING SUM(picks_top + picks_jungle + picks_middle + picks_bottom + picks_support) >= ?
        ORDER BY presence_rate DESC
    """
 
    params = tier_params + version_params + [min_games]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------
 
def _tier_filter(tier: str | list[str] | None, alias: str = "") -> tuple[str, list]:
    """
    Build a SQL WHERE fragment and parameter list for tier filtering.
 
    Args:
        tier: None, a single tier string, or a list of tier strings.
        alias: Optional table alias prefix e.g. "m" -> "m.tier".
 
    Returns:
        (sql_fragment, params) where sql_fragment is "" or "AND tier IN (?,...)"
    """
    col = f"{alias}.tier" if alias else "tier"
 
    if tier is None:
        return "", []
    if isinstance(tier, str):
        return f"AND {col} = ?", [tier]
    return f"AND {col} IN ({', '.join('?' * len(tier))})", list(tier)
 
def _version_filter(version: str | list[str] | None, alias: str = "") -> tuple[str, list]:
    """
    Build a SQL WHERE fragment and parameter list for version filtering.
 
    Args:
        version: None, a single version string, or a list of version strings.
        alias: Optional table alias prefix e.g. "m" -> "m.game_version".
 
    Returns:
        (sql_fragment, params) where sql_fragment is "" or "AND game_version IN (?,...)"
    """
    col = f"{alias}.game_version" if alias else "game_version"
 
    if version is None:
        return "", []
    if isinstance(version, str):
        return f"AND {col} = ?", [version]
    return f"AND {col} IN ({', '.join('?' * len(version))})", list(version)