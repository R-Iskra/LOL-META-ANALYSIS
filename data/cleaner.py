import json
from . import database as db

def version_to_tuple(v: str) -> tuple[int, int]:
    """Convert '15.14' -> (15, 14) for comparison."""
    try:
        parts = v.split(".")
        return int(parts[0]), int(parts[1])
    except Exception:
        return (0, 0)


def clean_matches_from_db(
        raw_db_path: str, 
        clean_db_path: str,
        min_duration: int|None = None,
        min_patch: str|None = None
        ):
    """
    Clean a database containing raw match data JSONs into a clean database.

    Args:
        raw_db_path (str): Path to database containing raw match data.
        clean_db_path (str): Path to pre-existing database or database that will be created for clean match data.
        min_duration (str, optional): Minimum time in seconds a match must last to be used for analysis. Defaults to None.
        min_patch (str, optional): Minimum patch a match must be to used for analysis. Defaults to None.
    """
    raw_conn = db.connect(raw_db_path)
    clean_conn = db.connect(clean_db_path)

    clean_cursor = clean_conn.cursor()
    # make sure clean tables exist
    db.create_clean_matches_table(clean_conn)

    raw_cursor = raw_conn.cursor()

    # get total match count for progress display
    total_matches = raw_cursor.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0]

    processed = 0
    successful_cleans = 0
    already_cleaned = 0
    filtered = 0

    # iterate one row at a time instead of fetchall()
    for match_id, raw_data in raw_cursor.execute("SELECT match_id, data FROM raw_matches"):
        processed += 1
        print("\r" + " " * 120, end="", flush=True)  # clear line
        print(
            f"\rProcessed {processed}/{total_matches} "
            f"| New cleans: {successful_cleans} "
            f"| Already cleaned: {already_cleaned} "
            f"| Filtered/skipped: {filtered}",
            end="", flush=True
        )

        # skip if match already in clean DB
        clean_cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,))
        if clean_cursor.fetchone():
            already_cleaned += 1
            continue

        try:
            match_json = json.loads(raw_data)
            metadata = match_json["metadata"]
            info = match_json["info"]

            if min_duration and info.get("gameDuration") < min_duration:
                filtered += 1
                continue

            game_version = ".".join(info.get("gameVersion", "").split(".")[:2])
            if min_patch and version_to_tuple(game_version) < version_to_tuple(min_patch):
                filtered += 1
                continue

            end_result = info.get("endOfGameResult")
            if end_result != "GameComplete":
                filtered += 1
                continue

            # Insert match row
            match_row = {
                "match_id": metadata.get("matchId"),
                "endOfGameResult": info.get("endOfGameResult"),
                "gameEndedInSurrender": int(info.get("participants", [])[0].get("gameEndedInSurrender", False)),
                "gameDuration": info.get("gameDuration"),
                "gameVersion": game_version
            }
            db.insert_match(clean_cursor, match_row)

            # Participants + perks
            for p in info["participants"]:
                participant_row = {
                    "match_id": metadata.get("matchId"),
                    "puuid": p.get("puuid"),
                    "championName": p.get("championName"),
                    "teamId": p.get("teamId"),
                    "teamPosition": p.get("teamPosition"),
                    "kills": p.get("kills"),
                    "deaths": p.get("deaths"),
                    "assists": p.get("assists"),
                    "win": int(p.get("win", False)),
                    "totalDamageDealt": p.get("totalDamageDealt"),
                    "totalDamageDealtToChampions": p.get("totalDamageDealtToChampions"),
                    "physicalDamageDealt": p.get("physicalDamageDealt"),
                    "physicalDamageDealtToChampions": p.get("physicalDamageDealtToChampions"),
                    "magicDamageDealt": p.get("magicDamageDealt"),
                    "magicDamageDealtToChampions": p.get("magicDamageDealtToChampions"),
                    "trueDamageDealt": p.get("trueDamageDealt"),
                    "trueDamageDealtToChampions": p.get("trueDamageDealtToChampions"),
                    "totalHeal": p.get("totalHeal"),
                    "totalHealsOnTeammates": p.get("totalHealsOnTeammates"),
                    "damageSelfMitigated": p.get("damageSelfMitigated"),
                    "totalTimeCrowdControlDealt": p.get("totalTimeCrowdControlDealt"),
                    "longestTimeSpentLiving": p.get("longestTimeSpentLiving"),
                    "totalMinionsKilled": p.get("totalMinionsKilled"),
                    "neutralMinionsKilled": p.get("neutralMinionsKilled"),
                    "turretKills": p.get("turretKills"),
                    "inhibitorKills": p.get("inhibitorKills"),
                    "dragonKills": p.get("dragonKills"),
                    "baronKills": p.get("baronKills"),
                    "spell1Casts": p.get("spell1Casts"),
                    "spell2Casts": p.get("spell2Casts"),
                    "spell3Casts": p.get("spell3Casts"),
                    "spell4Casts": p.get("spell4Casts"),
                    "summoner1Id": p.get("summoner1Id"),
                    "summoner2Id": p.get("summoner2Id"),
                    "playerAugment1": p.get("playerAugment1"),
                    "playerAugment2": p.get("playerAugment2"),
                    "playerAugment3": p.get("playerAugment3"),
                    "playerAugment4": p.get("playerAugment4")
                }
                db.insert_participant(clean_cursor, participant_row)

                # perks
                perks = p.get("perks", {})
                statPerks = perks.get("statPerks", {})
                db.insert_perk_stats(clean_cursor, {
                    "match_id": metadata.get("matchId"),
                    "puuid": p.get("puuid"),
                    "defense": statPerks.get("defense"),
                    "flex": statPerks.get("flex"),
                    "offense": statPerks.get("offense")
                })

                styles = perks.get("styles", [])
                for idx, style in enumerate(styles):
                    style_row = {
                        "match_id": metadata.get("matchId"),
                        "puuid": p.get("puuid"),
                        "style_order": idx,
                        "style_id": style.get("style"),
                        "description": style.get("description")
                    }
                    db.insert_perk_style(clean_cursor, style_row)

                    for sel in style.get("selections", []):
                        sel_row = {
                            "match_id": metadata.get("matchId"),
                            "puuid": p.get("puuid"),
                            "style_order": idx,
                            "perk_id": sel.get("perk"),
                            "var1": sel.get("var1"),
                            "var2": sel.get("var2"),
                            "var3": sel.get("var3")
                        }
                        db.insert_perk_selection(clean_cursor, sel_row)

            # Teams
            for t in info.get("teams", []):
                team_row = {
                    "match_id": metadata.get("matchId"),
                    "team_id": t.get("teamId"),
                    "win": int(t.get("win", False))
                }
                db.insert_team(clean_cursor, team_row)

                for obj_name, obj_vals in t.get("objectives", {}).items():
                    db.insert_team_objective(clean_cursor, {
                        "match_id": metadata.get("matchId"),
                        "team_id": t.get("teamId"),
                        "objective_name": obj_name,
                        "first": obj_vals.get("first"),
                        "kills": obj_vals.get("kills")
                    })

                for ban in t.get("bans", []):
                    db.insert_team_ban(clean_cursor, {
                        "match_id": metadata.get("matchId"),
                        "team_id": t.get("teamId"),
                        "pick_turn": ban.get("pickTurn"),
                        "champion_id": ban.get("championId")
                    })

            # Commit per match for safety
            successful_clean += 1
            clean_conn.commit()

        except Exception as e:
            print(f"\nError processing match {match_id}: {e}")
            filtered += 1
            continue

    # Final progress line
    print("\r" + " " * 120, end="", flush=True)
    print(
        f"\rProcessed {processed}/{total_matches} "
        f"| New cleans: {successful_cleans} "
        f"| Already cleaned: {already_cleaned} "
        f"| Filtered/skipped: {filtered}",
    )

    raw_conn.close()
    clean_conn.close()

    return