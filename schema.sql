DROP TABLE IF EXISTS bets;
DROP TABLE IF EXISTS wagers;
DROP TABLE IF EXISTS props;
DROP TABLE IF EXISTS betting_users;
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
    three_pt INTEGER NOT NULL DEFAULT 0,
    three_pta INTEGER NOT NULL DEFAULT 0,
    rating INTEGER NOT NULL DEFAULT 60, -- Overall Performance Rating (60-99)
    notes TEXT NOT NULL DEFAULT '', -- Game notes for the player
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(player_id, game_id)
);

CREATE TABLE betting_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT UNIQUE NOT NULL,
    pin_hash TEXT NOT NULL,
    balance INTEGER NOT NULL DEFAULT 100000
);

CREATE TABLE props (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    prop_type TEXT NOT NULL,
    player_id INTEGER,
    line_value REAL NOT NULL,
    odds_over INTEGER NOT NULL DEFAULT -110,
    odds_under INTEGER NOT NULL DEFAULT -110,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE SET NULL
);

CREATE TABLE wagers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    wager_amount INTEGER NOT NULL,
    odds_at_placed INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payout INTEGER DEFAULT 0,
    placed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES betting_users(id) ON DELETE CASCADE
);

CREATE TABLE bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wager_id INTEGER NOT NULL,
    prop_id INTEGER NOT NULL,
    selection TEXT NOT NULL,
    odds_at_placed INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY(wager_id) REFERENCES wagers(id) ON DELETE CASCADE,
    FOREIGN KEY(prop_id) REFERENCES props(id) ON DELETE CASCADE
);

