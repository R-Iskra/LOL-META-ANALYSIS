-- ================================================================
-- DERIVED LAYER: lane_matchups, matchup_stats
-- Head-to-head champion matchup outcomes per lane.
--
-- lane_matchups: one row per lane per match per rank (raw matchup events)
-- matchup_stats: aggregated win rates for each cahmp pair
-- ================================================================

-- ----------------------------------------------------------------
-- Raw matchup events. Joined from participants on:
--      same match_id + same lane + different team_id.
-- blue = team 100, red = team 200.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lane_matchups (
    match_id TEXT NOT NULL,
    lane TEXT NOT NULL,
    champ_blue TEXT NOT NULL, -- team 100 champion
    champ_red TEXT NOT NULL, -- team 200 champion
    blue_win INT NOT NULL, -- 1 = blue won, 0 = red won
    game_version TEXT NOT NULL,
    tier TEXT NOT NULL, -- e.g. CHALLENGER, GOLD

    PRIMARY KEY (match_id, lane)
);

-- ----------------------------------------------------------------
-- Aggregated matchup statistics.
-- champion is always stored alphabetically before opponent so
-- each pair is stored exactly once.
--
-- To get win rate for either side:
--      champion's win rate: champion_win_rate
--      opponent's win rate: (1 - champion_win_rate)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matchup_stats (
    champion TEXT NOT NULL,
    opponent TEXT NOT NULL,
    lane TEXT NOT NULL,
    game_version TEXT NOT NULL,
    tier TEXT NOT NULL,
    games INT NOT NULL,
    champion_wins INT NOT NULL,
    champion_win_rate REAL NOT NULL,

    PRIMARY KEY (champion, opponent, lane, game_version, tier)
);