-- ================================================================
-- CLEAN LAYER: matches
-- One row per match. Derived from info{} in the raw JSON.
-- ================================================================

CREATE TABLE IF NOT EXISTS matches (
    id TEXT NOT NULL,
    game_version TEXT NOT NULL, -- e.g. "15.14" (major.minor only)
    tier TEXT NOT NULL, -- ladder tier this match was collected from
    game_duration INT NOT NULL, -- seconds
    game_start INT NOT NULL, -- unix timestamp ms
    end_of_game_result TEXT, -- "GameComplete" etc.

    PRIMARY KEY (id)
);