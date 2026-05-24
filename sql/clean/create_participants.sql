-- ================================================================
-- CLEAN LAYER: participants
-- One row per player per match. Derived from info.participants[]
-- in the raw JSON.
-- ================================================================

CREATE TABLE IF NOT EXISTS participants (
    match_id TEXT NOT NULL,
    puuid TEXT NOT NULL,

    -- Identity
    champion_name TEXT,
    champion_id INT,
    champ_level INT,
    team_id INT, -- 100 = blue, 200 = red
    lane TEXT, -- teamPosition: TOP/JUNGLE/MIDDLE/BOTTOM/UTILITY

    -- Outcome
    win INT NOT NULL, -- 1 = win, 0 = loss

    -- KDA
    kills INT,
    deaths INT,
    assists INT,

    -- Economy
    gold_earned INT,
    gold_spent INT,

    -- CS
    minions_killed INT, -- totalMinionsKilled
    neutral_minions_killed INT, -- neutralMinionsKilled

    -- Vision
    vision_score INT, 
    wards_placed INT,
    control_wards_bought INT, -- visionWardsBoughtInGame

    -- Damage dealt
    total_damage_dealt INT,
    total_damage_dealt_to_champions INT,
    physical_damage_dealt INT,
    physical_damage_dealt_to_champions INT,
    magic_damage_dealt INT,
    magic_damage_dealt_to_champions INT,
    true_damage_dealt INT,
    true_damage_dealt_to_champions INT,
    damage_to_buildings INT,
    damage_to_objectives INT,
    damage_to_turrets INT,

    -- Damage taken / mitigation
    total_damage_taken INT,
    damage_self_mitigated INT,
    total_heal INT,
    heals_on_teammates INT,

    -- Crowd Control
    total_cc_dealt INT, -- totalTimeCrowdControlDealt (seconds)
    longest_time_living INT, -- seconds

    -- Objectives
    turret_kills INT,
    inhibitor_kills INT,
    dragon_kills INT,
    baron_kills INT,

    -- Summoner spells
    summoner1_id INT,
    summoner2_id INT,

    -- Items (0-5 = core, 6 = trinket)
    item0 INT,
    item1 INT,
    item2 INT,
    item3 INT,
    item4 INT,
    item5 INT,
    item6 INT,

    PRIMARY KEY (match_id, puuid),
    FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
);