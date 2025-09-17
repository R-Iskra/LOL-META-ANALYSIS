# cleaner.py

import os
import ast
import pandas as pd

def clean_match_data(match:dict) -> tuple[dict, list[dict]] | None:
    """Extract relevant match data, including challenges metrics for Ranked Solo 5v5.
    
    Args: 
        match (dict): Raw JSON response from Riot API

    Returns:
        dict | None: A dictionary with match-level metadata and nested team data, or None if match payload is invalid.
        Structure:
            - match_id (str): Riot match identifier.
            - game_id (str): Numeric match identifier.
            - game_duration (float): Duration in seconds.
            - game_version (str): Game client version string.
            - queue_id (int): Queue type identifier (e.g., 420 = Ranked Solo/Duo).
            - map_id (int): Map identifier (e.g., 11 = Summoner's Rift).
            - teams (dict):
                - "blue": list of participant dicts
                - "red": list of participant dicts

        Each participant dict contains:
            - puuid (str)
            - team_position (str)
            - champion_name (str)
            - champ_level (int)
            - kills, deaths, assists (int)
            - gold_earned (int)
            - total_minions_killed (int)
            - neutral_minions_killed (int)
            - total_damage_dealt_to_champions (int)
            - damage_self_mitigated (int)
            - vision_score (int)
            - wards_placed (int)
            - items (list[int])  # item0 through item6
            - first_blood_kill / first_blood_assist (bool)
            - first_tower_kill / first_tower_assist (bool)
            - turret_kills (int)
            - challenges (dict):
                - kda (float)
                - kill_participation (float)
                - damage_per_minute (float)
                - damage_taken_on_team_percentage (float)
                - vision_score_advantage_lane_opponent (float)
                - early_laning_phase_gold_exp_advantage (float)
                - baron_takedowns (int)
                - dragon_takedowns (int)
                - rift_herald_takedowns (int)
                - turret_takedowns (int)
                - control_wards_placed (int)
                - vision_score_per_minute (float)
            - win (bool)
    """

    if not match or 'info' not in match:
        return None
    
    info = match["info"]
    meta = match["metadata"]

    match_data = {
        "match_id": meta.get("matchId"),
        "game_id": info.get("gameId"),
        "game_duration": info.get("gameDuration"),
        "game_version": info.get("gameVersion"),
        "queue_id": info.get("queueId"),
        "map_id": info.get("mapId"),
        "teams": {"blue": [], "red": []}
    }

    for p in info.get("participants", []):
        challenges = p.get("challenges", {})
        participant_data = {
            "puuid": p.get("puuid"),
            "team_position": p.get("individualPosition"),
            "champion_name": p.get("championName"),
            "champ_level": p.get("champLevel"),
            "kills": p.get("kills"),
            "deaths": p.get("deaths"),
            "assists": p.get("assists"),
            "gold_earned": p.get("goldEarned"),
            "total_minions_killed": p.get("totalMinionsKilled"),
            "neutral_minions_killed": p.get("neutralMinionsKilled"),
            "total_damage_dealt_to_champions": p.get("totalDamageDealtToChampions"),
            "damage_self_mitigated": p.get("damageSelfMitigated"),
            "vision_score": p.get("visionScore"),
            "wards_placed": p.get("wardsPlaced"),
            "items": [p.get(f"item{i}") for i in range(7)],
            "first_blood_kill": p.get("firstBloodKill"),
            "first_blood_assist": p.get("firstBloodAssist"),
            "first_tower_kill": p.get("firstTowerKill"),
            "first_tower_assist": p.get("firstTowerAssist"),
            "turret_kills": p.get("turretKills"),
            "challenges": {
                "kda": challenges.get("kda"),
                "kill_participation": challenges.get("killParticipation"),
                "damage_per_minute": challenges.get("damagePerMinute"),
                "damage_taken_on_team_percentage": challenges.get("damageTakenOnTeamPercentage"),
                "vision_score_advantage_lane_opponent": challenges.get("visionScoreAdvantageLaneOpponent"),
                "early_laning_phase_gold_exp_advantage": challenges.get("earlyLaningPhaseGoldExpAdvantage"),
                "baron_takedowns": challenges.get("baronTakedowns"),
                "dragon_takedowns": challenges.get("dragonTakedowns"),
                "rift_herald_takedowns": challenges.get("riftHeraldTakedowns"),
                "turret_takedowns": challenges.get("turretTakedowns"),
                "control_wards_placed": challenges.get("controlWardsPlaced"),
                "vision_score_per_minute": challenges.get("visionScorePerMinute"),
            },
            "win": p.get("win"),
        }

        team = "blue" if p.get("teamId") == 100 else "red"
        match_data["teams"][team].append(participant_data)

    return match_data

def flatten_matches_to_csv(match_csv_path: str, output_csv_path: str = "player_match_data.csv"):
    """
    Read a match-per-row CSV and flatten it into player-per-row CSV.
    Incrementally writes each new player row, deduplicating using (match_id, puuid).

    Args:
        match_csv_path (str): Path to the match-level CSV.
        output_csv_path (str): Path to the output player-per-line CSV.
    """
    # Load existing player-per-line CSV to track what we've already written
    seen = set()
    if os.path.exists(output_csv_path):
        df_existing = pd.read_csv(output_csv_path)
        seen = set(zip(df_existing["match_id"].astype(str), df_existing["puuid"].astype(str)))
        header_written = True
    else:
        header_written = False

    # Load match CSV
    df_matches = pd.read_csv(match_csv_path)

    new_rows = 0

    for _, row in df_matches.iterrows():
        match_id = str(row["match_id"])
        teams_dict = ast.literal_eval(row["teams"])  # convert stringified dict back to dict

        for team_name in ["blue", "red"]:
            for player in teams_dict.get(team_name, []):
                puuid = player.get("puuid")
                key = (match_id, puuid)
                if key in seen:
                    continue

                # Flatten participant data for CSV
                flat_row = {
                    "match_id": match_id,
                    "puuid": puuid,
                    "team": team_name,
                    "team_position": player.get("team_position"),
                    "champion_name": player.get("champion_name"),
                    "champ_level": player.get("champ_level"),
                    "kills": player.get("kills"),
                    "deaths": player.get("deaths"),
                    "assists": player.get("assists"),
                    "gold_earned": player.get("gold_earned"),
                    "total_minions_killed": player.get("total_minions_killed"),
                    "neutral_minions_killed": player.get("neutral_minions_killed"),
                    "total_damage_dealt_to_champions": player.get("total_damage_dealt_to_champions"),
                    "damage_self_mitigated": player.get("damage_self_mitigated"),
                    "vision_score": player.get("vision_score"),
                    "wards_placed": player.get("wards_placed"),
                    "items": player.get("items"),
                    "first_blood_kill": player.get("first_blood_kill"),
                    "first_blood_assist": player.get("first_blood_assist"),
                    "first_tower_kill": player.get("first_tower_kill"),
                    "first_tower_assist": player.get("first_tower_assist"),
                    "turret_kills": player.get("turret_kills"),
                    "win": player.get("win"),
                    **player.get("challenges", {})  # flatten challenges directly
                }

                # Append row immediately
                pd.DataFrame([flat_row]).to_csv(
                    output_csv_path,
                    mode='a',
                    header=not header_written,
                    index=False
                )
                header_written = True
                new_rows += 1
                seen.add(key)

    print(f"✅ Flattening complete. {new_rows} new player rows added.")