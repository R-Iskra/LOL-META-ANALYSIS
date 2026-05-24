-- ================================================================
-- RAW LAYER
-- Store API responses as JSON blobs for re-runnability
-- ================================================================

CREATE TABLE IF NOT EXISTS raw_matches (
    match_id TEXT NOT NULL,
    game_version TEXT NOT NULL, -- e.g. "15.14" (major.minor only)
    tier TEXT NOT NULL, -- ladder tier used to find this match
                        -- e.g. CHALLENGER, GRANDMASTER, MASTER, etc.
    collected_at INT NOT NULL, -- timestamp of collection
    data TEXT NOT NULL, -- full match-v5 JSON response

    PRIMARY KEY (match_id)
);