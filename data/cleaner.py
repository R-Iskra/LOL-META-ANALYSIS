import os
import json
import pandas as pd


def load_raw_matches(jsonl_path: str) -> list[dict]:
    """
    Load raw match data from JSONL file into a list of dicts.
    
    Args:
        jsonl_path (str): Path to JSONL file to load.

    Returns:
        matches (list[dict]): list of dictionaries containing match data
    """
    matches = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                matches.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return matches

def sort_csv(
        csv_path:str, 
        sort_values:list[str], 
        sort_ascending:list[bool]|None = None
        ):
    """
    Read cleaned csv, sort, and rewrite

    Args:
        csv_path (str): Path to csv file to load and write to.
        sort_values (list[str]): List of string values to sort by.
        sort_ascending (list[bool], optional): List of bools linked to values. If None, defauts to True for all columns.
    """
    
    if sort_ascending is None:
        sort_ascending = [True] * len(sort_values)
    elif len(sort_ascending) != len(sort_values):
        raise ValueError(
            f"Length of sort_ascending ({len(sort_ascending)}) "
            f"does not match number of sort_values ({len(sort_values)})."
        )

    df = pd.read_csv(csv_path)
    df = df.sort_values(by = sort_values, ascending = sort_ascending)
    df.to_csv(csv_path, header=True, index=False)

def clean_matches(
        jsonl_path: str, 
        csv_path: str, 
        min_duration: int|None = None,
        sort_values: list[str]|None = None,
        sort_ascending: list[bool]|None = None
        ):
    """
    Clean raw JSONL matches into a player-level CSV.

    Args:
        jsonl_path (str): Path to JSONL file to load.
        csv_path (str): Path to CSV file to load and store player level data.
        min_duration (int, optional): Minimum time in seconds a match must be. Defaults to None.
        sort_values (list[str], optional): List of string values to sort by. Defaults to None.
        sort_ascending (list[bool], optional): List of bools linked to sort_values. Defaults to None.
    """
     # Load existing keys to avoid duplicates
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path, dtype={"matchId": str, "puuid": str})
        existing_keys = set(zip(existing_df["matchId"], existing_df["puuid"]))
    else:
        existing_keys = set()

    total_added = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            try:
                match = json.loads(line)
            except json.JSONDecodeError:
                continue

            metadata = match["metadata"]
            info = match["info"]

            if min_duration and info.get("gameDuration") < min_duration:
                continue


            match_rows = []
            for participant in info["participants"]:
                key = (metadata.get("matchId"), participant.get("puuid"))
                if key in existing_keys:
                    continue

                row = {
                    "matchId": metadata.get("matchId"),
                    "gameId": info.get("gameId"),
                    "gameDuration": info.get("gameDuration"),
                    "gameVersion": ".".join(info.get("gameVersion").split(".")[:2]),
                    "queueId": info.get("queueId"),
                    "mapId": info.get("mapId"),
                    "puuid": participant.get("puuid"),
                    "teamId": participant.get("teamId"),
                    "championName": participant.get("championName"),
                    "role": participant.get("individualPosition"),
                    "teamPosition": participant.get("teamPosition"),
                    "win": participant.get("win"),
                    "kills": participant.get("kills"),
                    "deaths": participant.get("deaths"),
                    "assists": participant.get("assists"),
                    "totalDamageDealtToChampions": participant.get("totalDamageDealtToChampions"),
                    "goldEarned": participant.get("goldEarned"),
                    "champLevel": participant.get("champLevel"),
                    "totalMinionsKilled": participant.get("totalMinionsKilled"),
                    "neutralMinionsKilled": participant.get("neutralMinionsKilled"),
                    "totalDamageTaken": participant.get("totalDamageTaken"),
                    "damageSelfMitigated": participant.get("damageSelfMitigated"),
                    "wardsPlaced": participant.get("wardsPlaced"),
                    "wardsKilled": participant.get("wardsKilled"),
                    "firstBloodKill": participant.get("firstBloodKill"),
                    "firstTowerKill": participant.get("firstTowerKill"),
                    "visionScore": participant.get("visionScore"),
                    "totalHeal": participant.get("totalHeal"),
                    "totalTimeCrowdControlDealt": participant.get("totalTimeCrowdControlDealt"),
                    "largestMultiKill": participant.get("largestMultiKill"),
                    "summoner1Id": participant.get("summoner1Id"),
                    "summoner2Id": participant.get("summoner2Id"),
                    "perks": participant.get("perks")
                }

                challenges = participant.get("challenges", {})
                if challenges:
                    row.update({
                        "dpm": challenges.get("damagePerMinute"),
                        "kp": challenges.get("killParticipation"),
                        "visionScorePerMinute": challenges.get("visionScorePerMinute"),
                    })

                match_rows.append(row)
                existing_keys.add(key)

            # Write all participants for this match immediately
            if match_rows:
                df = pd.DataFrame(match_rows)
                df.to_csv(csv_path, mode="a", header=not os.path.exists(csv_path), index=False)
                total_added += len(match_rows)
            print("\r" + " " * 150, end="", flush=True)
            print(f"\rProcessed line {line_idx}, total new player rows added: {total_added}", end="", flush=True)

    if sort_values:
        sort_csv(
            csv_path=csv_path,
            sort_values=sort_values,
            sort_ascending=sort_ascending
            )
    
    return