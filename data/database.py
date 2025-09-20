import sqlite3
import json

def connect(db_path: str):
    """Connect to SQLite DB (creates file if not exists)."""
    conn = sqlite3.connect(db_path)
    return conn

def create_raw_matches_table(conn):
    """Ensure raw_matches table exists."""
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS raw_matches (
                   match_id TEXT PRIMARY KEY,
                   data TEXT NOT NULL
                   )
                   """)
    conn.commit()
    
    return

def match_exists(conn, match_id: str) -> bool:
    """Check if a match ID is already in the raw_matches table."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM raw_matches WHERE match_id = ?", (match_id,))
    except sqlite3.OperationalError:
        # Table doesn't exist yet → treat as not found
        return False
    return cursor.fetchone() is not None

def insert_raw_match(conn, raw_match: dict):
    """Insert raw JSON match data into the DB."""
    cursor = conn.cursor()
    match_id = raw_match.get("metadata", {}).get("matchId")
    if not match_id:
        return
    cursor.execute(
        "INSERT OR IGNORE INTO raw_matches (match_id, data) VALUES (?, ?)",
        (match_id, json.dumps(raw_match))
    )
    conn.commit()

    return

def create_clean_matches_table(conn):
    """Ensures clean table exists"""
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS matches (
                   match_id TEXT PRIMARY KEY,
                   endOfGameResult TEXT,
                   gameDuration INT,
                   gameVersion TEXT
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS participants (
                   match_id TEXT NOT NULL,
                   puuid TEXT NOT NULL,
                   championName TEXT,
                   teamId INT,
                   teamPosition TEXT,
                   kills INT,
                   deaths INT,
                   assists INT,
                   win INT,

                   -- Damage breakdown
                   totalDamageDealt INT,
                   totalDamageDealtToChampions INT,
                   physicalDamageDealt INT,
                   physicalDamageDealtToChampions INT,
                   magicDamageDealt INT,
                   magicDamageDealtToChampions INT,
                   trueDamageDealt INT,
                   trueDamageDealtToChampions INT,
                   
                   -- Healing and mitigation
                   totalHeal INT,
                   totalHealsOnTeammates INT,
                   damageSelfMitigated INT,

                   -- Crowd control
                   totalTimeCrowdControlDealt INT,
                   longestTimeSpentLiving INT,

                   -- Objectives and minions
                   totalMinionsKilled INT,
                   neutralMinionsKilled INT,
                   turretKills INT,
                   inhibitorKills INT,
                   dragonKills INT,
                   baronKills INT,

                   -- Spells and summoner
                   spell1Casts INT,
                   spell2Casts INT,
                   spell3Casts INT,
                   spell4Casts INT,
                   summoner1Id INT,
                   summoner2Id INT,

                   -- Player Augments
                   playerAugment1 INT,
                   playerAugment2 INT,
                   playerAugment3 INT,
                   playerAugment4 INT,

                   PRIMARY KEY (match_id, puuid),
                   FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
                   )
                   """)
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS perk_stats(
                   match_id TEXT NOT NULL,
                   puuid TEXT NOT NULL,
                   defense INT,
                   flex INT,
                   offense INT,
                   PRIMARY KEY (match_id, puuid),
                   FOREIGN KEY (match_id, puuid) REFERENCES participants(match_id, puuid) ON DELETE CASCADE
                   )
                   """)
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS perk_styles(
                   match_id TEXT NOT NULL,
                   puuid TEXT NOT NULL,
                   style_order INT NOT NULL,
                   style_id INT NOT NULL,
                   description TEXT,
                   PRIMARY KEY (match_id, puuid, style_order),
                   FOREIGN KEY (match_id, puuid) REFERENCES participants(match_id, puuid) ON DELETE CASCADE
                   )
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS perk_selections(
                   match_id TEXT NOT NULL,
                   puuid TEXT NOT NULL,
                   style_order INT NOT NULL,
                   perk_id INT NOT NULL,
                   var1 INT,
                   var2 INT,
                   var3 INT,
                   PRIMARY KEY (match_id, puuid, style_order, perk_id),
                   FOREIGN KEY (match_id, puuid, style_order) REFERENCES perk_styles(match_id, puuid, style_order) ON DELETE CASCADE
                   )
                   """)
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS teams(
                   match_id TEXT NOT NULL,
                   team_id INT NOT NULL,
                   win INT,
                   PRIMARY KEY (match_id, team_id),
                   FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
                   )
                   """)
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS team_objectives(
                   match_id TEXT NOT NULL,
                   team_id INT NOT NULL,
                   objective_name TEXT NOT NULL,
                   first INT,
                   kills INT,
                   PRIMARY KEY (match_id, team_id, objective_name),
                   FOREIGN KEY (match_id, team_id) REFERENCES teams(match_id, team_id) ON DELETE CASCADE
                   )
                   """)
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS team_bans(
                   match_id TEXT NOT NULL,
                   team_id INT NOT NULL,
                   pick_turn INT NOT NULL,
                   champion_id INT,
                   PRIMARY KEY (match_id, team_id, pick_turn),
                   FOREIGN KEY (match_id, team_id) REFERENCES teams(match_id, team_id) ON DELETE CASCADE
                   )
                   """)
    conn.commit()

    return

# --- insert functions ---
def insert_match(cursor, match_data: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO matches (match_id, endOfGameResult, gameDuration, gameVersion)
        VALUES (?, ?, ?, ?)
    """, (
        match_data["match_id"],
        match_data.get("endOfGameResult"),
        match_data.get("gameDuration"),
        match_data.get("gameVersion")
    ))

def insert_participant(cursor, participant_data: dict):
    keys = (
        "match_id", "puuid", "championName", "teamId", "teamPosition", "kills", "deaths", "assists", "win",
        "totalDamageDealt", "totalDamageDealtToChampions", "physicalDamageDealt", "physicalDamageDealtToChampions",
        "magicDamageDealt", "magicDamageDealtToChampions", "trueDamageDealt", "trueDamageDealtToChampions",
        "totalHeal", "totalHealsOnTeammates", "damageSelfMitigated", "totalTimeCrowdControlDealt", "longestTimeSpentLiving",
        "totalMinionsKilled", "neutralMinionsKilled", "turretKills", "inhibitorKills", "dragonKills", "baronKills",
        "spell1Casts", "spell2Casts", "spell3Casts", "spell4Casts", "summoner1Id", "summoner2Id",
        "playerAugment1", "playerAugment2", "playerAugment3", "playerAugment4"
    )
    values = tuple(participant_data.get(k) for k in keys)
    cursor.execute(f"""
        INSERT OR IGNORE INTO participants ({', '.join(keys)})
        VALUES ({', '.join(['?'] * len(keys))})
    """, values)

def insert_perk_stats(cursor, perk_stats: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO perk_stats (match_id, puuid, defense, flex, offense)
        VALUES (?, ?, ?, ?, ?)
    """, (
        perk_stats["match_id"],
        perk_stats["puuid"],
        perk_stats.get("defense"),
        perk_stats.get("flex"),
        perk_stats.get("offense")
    ))

def insert_perk_style(cursor, style: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO perk_styles (match_id, puuid, style_order, style_id, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        style["match_id"],
        style["puuid"],
        style["style_order"],
        style["style_id"],
        style.get("description")
    ))

def insert_perk_selection(cursor, selection: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO perk_selections (match_id, puuid, style_order, perk_id, var1, var2, var3)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        selection["match_id"],
        selection["puuid"],
        selection["style_order"],
        selection["perk_id"],
        selection.get("var1"),
        selection.get("var2"),
        selection.get("var3")
    ))

def insert_team(cursor, team: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO teams (match_id, team_id, win)
        VALUES (?, ?, ?)
    """, (
        team["match_id"],
        team["team_id"],
        team.get("win")
    ))

def insert_team_objective(cursor, objective: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO team_objectives (match_id, team_id, objective_name, first, kills)
        VALUES (?, ?, ?, ?, ?)
    """, (
        objective["match_id"],
        objective["team_id"],
        objective["objective_name"],
        objective.get("first"),
        objective.get("kills")
    ))

def insert_team_ban(cursor, ban: dict):
    cursor.execute("""
        INSERT OR IGNORE INTO team_bans (match_id, team_id, pick_turn, champion_id)
        VALUES (?, ?, ?, ?)
    """, (
        ban["match_id"],
        ban["team_id"],
        ban["pick_turn"],
        ban.get("champion_id")
    ))