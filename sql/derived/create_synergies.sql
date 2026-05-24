-- ================================================================
-- DERIVED LAYER: champion_synergies
-- Win rates for champion pairs that appear on the same team.
-- 
-- champion_a is always alphabetically before champion_b
-- to avoid storing duplicate mirror pairs.
-- To get win rate for either side:
--      champion_a's win rate: win_rate
--      champion_a's win rate: (1 - win_rate)
-- ================================================================

CREATE TABLE IF NOT EXISTS champion_synergies (
    champion_a TEXT NOT NULL,
    lane_a TEXT NOT NULL,
    champion_b TEXT NOT NULL,
    lane_b TEXT NOT NULL,
    game_version TEXT NOT NULL,
    tier TEXT NOT NULL, -- e.g. CHALLENGER, GOLD
    games INT NOT NULL,
    wins INT NOT NULL,
    win_rate REAL NOT NULL,

    PRIMARY KEY (champion_a, lane_a, champion_b, lane_b, game_version, tier)
);