DROP TABLE IF EXISTS stats;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    jersey_number TEXT NOT NULL,
    nickname TEXT NOT NULL
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opponent TEXT NOT NULL,
    date TEXT NOT NULL,
    cows_score INTEGER NOT NULL,
    opponent_score INTEGER NOT NULL,
    outcome TEXT NOT NULL, -- 'W' or 'L'
    location TEXT NOT NULL DEFAULT 'The Pasture (Home)'
);

CREATE TABLE stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    rebounds INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    steals INTEGER NOT NULL DEFAULT 0,
    blocks INTEGER NOT NULL DEFAULT 0,
    turnovers INTEGER NOT NULL DEFAULT 0,
    airballs INTEGER NOT NULL DEFAULT 0,
    bozo_moments INTEGER NOT NULL DEFAULT 0,
    fg INTEGER NOT NULL DEFAULT 0,
    fga INTEGER NOT NULL DEFAULT 0,
    ft INTEGER NOT NULL DEFAULT 0,
    fta INTEGER NOT NULL DEFAULT 0,
    rating INTEGER NOT NULL DEFAULT 60, -- Overall Performance Rating (60-99)
    notes TEXT NOT NULL DEFAULT '', -- Game notes for the player
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(player_id, game_id)
);
