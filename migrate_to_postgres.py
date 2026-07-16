import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Retrieve configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deadlycows.db')
DATABASE_URL = os.environ.get('DATABASE_URL')

def migrate():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please export DATABASE_URL or set it in your environment before running this script.")
        return

    print("Connecting to local SQLite database...")
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    print("Connecting to remote PostgreSQL database...")
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()

    # Drop existing tables to perform a clean schema reset
    pg_cursor.execute("DROP TABLE IF EXISTS bets, wagers, props, betting_users, stats, games, players CASCADE;")

    # 1. Create players
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            jersey_number VARCHAR(10) NOT NULL,
            nickname VARCHAR(255) NOT NULL
        );
    ''')
    
    # 2. Create games
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id SERIAL PRIMARY KEY,
            opponent VARCHAR(255) NOT NULL,
            date VARCHAR(50) NOT NULL,
            cows_score INTEGER NOT NULL,
            opponent_score INTEGER NOT NULL,
            outcome VARCHAR(5) NOT NULL,
            location VARCHAR(255) NOT NULL DEFAULT 'The Pasture (Home)'
        );
    ''')

    # 3. Create stats
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id SERIAL PRIMARY KEY,
            player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
            game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
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
            rating INTEGER NOT NULL DEFAULT 60,
            notes TEXT NOT NULL DEFAULT '',
            UNIQUE(player_id, game_id)
        );
    ''')

    # 4. Create betting users
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS betting_users (
            id SERIAL PRIMARY KEY,
            nickname VARCHAR(50) UNIQUE NOT NULL,
            pin_hash VARCHAR(255) NOT NULL,
            balance INTEGER NOT NULL DEFAULT 100000
        );
    ''')

    # 5. Create props
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS props (
            id SERIAL PRIMARY KEY,
            game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            prop_type VARCHAR(50) NOT NULL,
            player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
            line_value REAL NOT NULL,
            odds_over INTEGER NOT NULL DEFAULT -110,
            odds_under INTEGER NOT NULL DEFAULT -110,
            description VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'open'
        );
    ''')

    # 6. Create wagers
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS wagers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES betting_users(id) ON DELETE CASCADE,
            wager_amount INTEGER NOT NULL,
            odds_at_placed INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            payout INTEGER DEFAULT 0,
            placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # 7. Create bets (legs)
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            wager_id INTEGER NOT NULL REFERENCES wagers(id) ON DELETE CASCADE,
            prop_id INTEGER NOT NULL REFERENCES props(id) ON DELETE CASCADE,
            selection VARCHAR(10) NOT NULL,
            odds_at_placed INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending'
        );
    ''')
    
    pg_conn.commit()
    print("Tables created successfully.")

    print("\n--- Step 2: Migrating Players ---")
    sqlite_cursor.execute("SELECT * FROM players")
    players = sqlite_cursor.fetchall()
    
    # We want to preserve IDs, so we can insert with explicit IDs
    for p in players:
        pg_cursor.execute('''
            INSERT INTO players (id, name, jersey_number, nickname)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                jersey_number = EXCLUDED.jersey_number,
                nickname = EXCLUDED.nickname
        ''', (p['id'], p['name'], p['jersey_number'], p['nickname']))
    pg_conn.commit()
    print(f"Migrated {len(players)} players.")

    # Fix primary key serial sequences
    pg_cursor.execute("SELECT setval('players_id_seq', COALESCE((SELECT MAX(id)+1 FROM players), 1), false)")

    print("\n--- Step 3: Migrating Games ---")
    sqlite_cursor.execute("SELECT * FROM games")
    games = sqlite_cursor.fetchall()
    for g in games:
        pg_cursor.execute('''
            INSERT INTO games (id, opponent, date, cows_score, opponent_score, outcome, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                opponent = EXCLUDED.opponent,
                date = EXCLUDED.date,
                cows_score = EXCLUDED.cows_score,
                opponent_score = EXCLUDED.opponent_score,
                outcome = EXCLUDED.outcome,
                location = EXCLUDED.location
        ''', (g['id'], g['opponent'], g['date'], g['cows_score'], g['opponent_score'], g['outcome'], g['location']))
    pg_conn.commit()
    print(f"Migrated {len(games)} games.")
    
    pg_cursor.execute("SELECT setval('games_id_seq', COALESCE((SELECT MAX(id)+1 FROM games), 1), false)")

    print("\n--- Step 4: Migrating Player Stats ---")
    sqlite_cursor.execute("SELECT * FROM stats")
    stats = sqlite_cursor.fetchall()
    for s in stats:
        pg_cursor.execute('''
            INSERT INTO stats (
                id, player_id, game_id, points, rebounds, assists, steals, blocks,
                turnovers, airballs, bozo_moments, fg, fga, ft, fta, three_pt, three_pta, rating, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, game_id) DO UPDATE SET
                points = EXCLUDED.points,
                rebounds = EXCLUDED.rebounds,
                assists = EXCLUDED.assists,
                steals = EXCLUDED.steals,
                blocks = EXCLUDED.blocks,
                turnovers = EXCLUDED.turnovers,
                airballs = EXCLUDED.airballs,
                bozo_moments = EXCLUDED.bozo_moments,
                fg = EXCLUDED.fg,
                fga = EXCLUDED.fga,
                ft = EXCLUDED.ft,
                fta = EXCLUDED.fta,
                three_pt = EXCLUDED.three_pt,
                three_pta = EXCLUDED.three_pta,
                rating = EXCLUDED.rating,
                notes = EXCLUDED.notes
        ''', (
            s['id'], s['player_id'], s['game_id'], s['points'], s['rebounds'], s['assists'],
            s['steals'], s['blocks'], s['turnovers'], s['airballs'], s['bozo_moments'],
            s['fg'], s['fga'], s['ft'], s['fta'], s['three_pt'], s['three_pta'], s['rating'], s['notes']
        ))
    pg_conn.commit()
    print(f"Migrated {len(stats)} stat rows.")
    
    pg_cursor.execute("SELECT setval('stats_id_seq', COALESCE((SELECT MAX(id)+1 FROM stats), 1), false)")

    print("\n--- Database Migration Completed Successfully! ---")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == '__main__':
    migrate()
