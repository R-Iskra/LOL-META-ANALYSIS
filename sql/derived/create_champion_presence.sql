-- ================================================================
-- DERIVED LAYER: champion_presence
-- Pick rates per lane, ban rate, and presence rate per champion
-- per patch per tier. 
--
-- Pick rates are per-lane in order to have one record per champion.
--
-- Presence = (picked in any lane + banned) / total_matches.
-- ================================================================

CREATE TABLE IF NOT EXISTS champion_presence (
    champion TEXT NOT NULL,
    game_version TEXT NOT NULL,
    tier TEXT NOT NULL, -- e.g. CHALLENGER, GOLD

    total_matches INT NOT NULL,

    -- Pick counts per lane
    picks_top INT NOT NULL DEFAULT 0,
    picks_jungle INT NOT NULL DEFAULT 0,
    picks_middle INT NOT NULL DEFAULT 0,
    picks_bottom INT NOT NULL DEFAULT 0,
    picks_support INT NULL DEFAULT 0,

    -- Pick rates per lane
    pick_rate_top REAL NOT NULL DEFAULT 0.0,
    pick_rate_jungle REAL NOT NULL DEFAULT 0.0,
    pick_rate_middle REAL NOT NULL DEFAULT 0.0,
    pick_rate_bottom REAL NOT NULL DEFAULT 0.0,
    pick_rate_support REAL NOT NULL DEFAULT 0.0,

    -- Bans (not lane-specific)
    bans INT NOT NULL DEFAULT 0,
    ban_rate REAL NOT NULL DEFAULT 0.0,

    -- Presence ((picks in any lane + bans) / total_matches)
    presence_rate REAL NOT NULL DEFAULT 0.0,

    PRIMARY KEY (champion, game_version, tier)
);