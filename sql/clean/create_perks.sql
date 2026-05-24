-- ================================================================
-- CLEAN LAYER: perk_stats, perk_styles, perk_selections
-- Derived from info.participants[].perks{} in the raw JSON.
--
-- Structure mirrors the API response:
--      perks.statPerks -> perk_stats
--      perks.styles[] -> perk_styles
--      styles.selections[] -> perk_selections
-- ================================================================

-- ----------------------------------------------------------------
-- Adaptive stat shards chosen pre-game (offense/flex/defense row).
-- IDs map to the Data Dragon runes reforged constants.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perk_stats (
    match_id TEXT NOT NULL,
    puuid TEXT NOT NULL,
    defense INT,
    flex INT,
    offense INT,

    PRIMARY KEY (match_id, puuid),
    FOREIGN KEY (match_id, puuid) REFERENCES participants (match_id, puuid) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- Rune path selections.
-- style_order: 0 = primary path, 1 = secondary path
-- description: "primarStyle" or "subStyle"
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perk_styles (
    match_id TEXT NOT NULL,
    puuid TEXT NOT NULL,
    style_order INT NOT NULL,
    style_id INT NOT NULL,
    description TEXT,

    PRIMARY KEY (match_id, puuid, style_order),
    FOREIGN KEY (match_id, puuid) REFERENCES participants (match_id, puuid) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- Individual rune selections within each rune path.
-- var1/var2/var3/ are the rune's scoring variables
-- (e.g.) damage dealt for Electrocute).
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perk_selections (
    match_id TEXT NOT NULL,
    puuid TEXT NOT NULL,
    style_order INT NOT NULL,
    perk_id INT NOT NULL,
    var1 INT,
    var2 INT,
    var3 INT,

    PRIMARY KEY (match_id, puuid, style_order, perk_id),
    FOREIGN KEY (match_id, puuid, style_order)
        REFERENCES perk_styles (match_id, puuid, style_order) ON DELETE CASCADE
);