-- ================================================================
-- CLEAN LAYER: teams, team_objectives, team_bans
-- Derived from into.teams[] in the raw JSON.
-- ================================================================

CREATE TABLE IF NOT EXISTS teams (
    match_id TEXT NOT NULL,
    team_id INT NOT NULL, -- 100 = blue, 200 = red
    win INT NOT NULL, -- 1 = win, 0 = loss

    PRIMARY KEY (match_id, team_id),
    FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- One row per objective type per team per match.
-- objective_name: baron, champion, dragon, horde, inhibitor
--                  riftHerald, tower
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS team_objectives (
    match_id TEXT NOT NULL,
    team_id INT NOT NULL,
    objective_name TEXT NOT NULL,
    first INT, -- 1 = team got first of this objective
    kills INT, -- total secured

    PRIMARY KEY (match_id, team_id, objective_name),
    FOREIGN KEY (match_id, team_id) REFERENCES teams (match_id, team_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- One row per ban slot per team per match.
-- pick_turn: 1-5 per team (10 bans total per game)
-- champion_id: -1 means no ban made
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS team_bans (
    match_id TEXT NOT NULL,
    team_id INT NOT NULL,
    pick_turn INT NOT NULL,
    champion_id INT,

    PRIMARY KEY (match_id, team_id, pick_turn),
    FOREIGN KEY (match_id, team_id) REFERENCES teams (match_id, team_id) ON DELETE CASCADE
);