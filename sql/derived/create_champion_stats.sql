-- ================================================================
-- DERIVED LAYER: champion_stats
-- Aggregated champion performance per lane per patch per rank.
-- Computed from the clean participants + matches tables.
--
-- Rows with games < MIN_SAMPLE_SIZE should be excluded from
-- analysis (see analysis/champuons.py for the threshold).
-- ================================================================

CREATE TABLE IF NOT EXISTS champion_stats (
    champion TEXT NOT NULL,
    lane TEXT NOT NULL,
    game_version TEXT NOT NULL, -- patch, e.g. "15.14"
    tier TEXT NOT NULL, -- e.g. CHALLENGER, GOLD

    -- Volume
    games INT NOT NULL,
    wins INT NOT NULL,
    win_rate REAL NOT NULL, -- wins / games

    -- KDA averages
    avg_kills REAL,
    avg_deaths REAL,
    avg_assists REAL,
    avg_kda REAL, -- (kills + assists) / max(deaths, 1)

    -- Economy averages
    avg_gold_earned REAL,
    avg_cs REAL, -- minions + neutral minions

    -- Combat averages
    avg_damage_to_champions REAL,
    avg_damage_taken REAL,
    avg_damage_mitigated REAL,

    -- Vision averages
    avg_vision_score REAL,

    PRIMARY KEY (champion, lane, game_version, tier)
);