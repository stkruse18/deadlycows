import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deadlycows.db')
DATABASE_URL = os.environ.get('DATABASE_URL')
import decimal

def convert_value(val):
    if isinstance(val, decimal.Decimal):
        return float(val)
    return val

class PostgresRowWrapper(dict):
    def __init__(self, raw_dict):
        converted = {k: convert_value(v) for k, v in raw_dict.items()}
        super().__init__(converted)
        self._values = list(converted.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

class PostgresCursorWrapper:
    def __init__(self, raw_cursor):
        self.raw_cursor = raw_cursor
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql = sql.replace('?', '%s')
        # Check if INSERT statement and might need returning row ID
        is_insert = sql.strip().upper().startswith("INSERT INTO")
        needs_returning = is_insert and ("games" in sql or "players" in sql or "stats" in sql or "betting_users" in sql or "props" in sql or "bets" in sql or "wagers" in sql)
        
        if needs_returning and "RETURNING" not in sql.upper():
            sql += " RETURNING id"
            self.raw_cursor.execute(sql, params)
            res = self.raw_cursor.fetchone()
            if res:
                self.lastrowid = res.get('id') or list(res.values())[0]
        else:
            self.raw_cursor.execute(sql, params)

    def executemany(self, sql, seq_of_parameters):
        sql = sql.replace('?', '%s')
        self.raw_cursor.executemany(sql, seq_of_parameters)

    def fetchone(self):
        row = self.raw_cursor.fetchone()
        if row is None:
            return None
        return PostgresRowWrapper(row)

    def fetchall(self):
        rows = self.raw_cursor.fetchall()
        return [PostgresRowWrapper(r) for r in rows]

    def close(self):
        self.raw_cursor.close()

class PostgresConnectionWrapper:
    def __init__(self, raw_conn):
        self.raw_conn = raw_conn

    def cursor(self):
        return PostgresCursorWrapper(self.raw_conn.cursor())

    def execute(self, sql, params=()):
        cursor = self.cursor()
        cursor.execute(sql, params)
        return cursor

    def commit(self):

        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

def get_db_connection():
    if DATABASE_URL:
        # Use Postgres in production / cloud environment
        try:
            raw_conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return PostgresConnectionWrapper(raw_conn)
        except Exception as e:
            import sys
            print(f"DATABASE CONNECTION ERROR: {e}", file=sys.stderr)
            raise e
    else:
        # Fallback to local SQLite file
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    if DATABASE_URL:
        # Do not run sqlite3 scripts directly on Postgres
        return
    conn = get_db_connection()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('betting_paused', 'false');")
    conn.commit()
    conn.close()


def calculate_rating(points, rebounds, assists, steals, blocks, turnovers, airballs, bozo_moments, fg, fga):
    misses = max(0, fga - fg)
    rating = (
        67.0
        + (points * 1.0)
        + (rebounds * 0.8)
        + (assists * 1.0)
        + (steals * 1.5)
        + (blocks * 1.5)
        - (turnovers * 1.0)
        - (airballs * 1.0)
        - (bozo_moments * 2.0)
        - (misses * 0.4)
    )
    return int(round(max(60.0, min(99.0, rating))))

def get_all_players():
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY name').fetchall()
    conn.close()
    return players

def add_player(name, jersey_number, nickname):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO players (name, jersey_number, nickname) VALUES (?, ?, ?)',
        (name, jersey_number, nickname)
    )
    conn.commit()
    conn.close()

def delete_player(player_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
    conn.commit()
    conn.close()

def get_all_games():
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games ORDER BY date DESC, id DESC').fetchall()
    conn.close()
    return games

def get_game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    conn.close()
    return game

def get_game_stats(game_id):
    conn = get_db_connection()
    # Fetch player stats for the game along with player details
    stats = conn.execute('''
        SELECT s.*, p.name, p.jersey_number, p.nickname
        FROM stats s
        JOIN players p ON s.player_id = p.id
        WHERE s.game_id = ?
    ''', (game_id,)).fetchall()
    conn.close()

    # Convert to list of dicts
    stats_list = []
    for s in stats:
        stats_list.append(dict(s))

    if not stats_list:
        return [], None, None

    # Determine Moo-VP (highest rating) and LIP (lowest rating)
    # Sort stats by rating descending
    stats_list = sorted(stats_list, key=lambda x: (x['rating'], -x['turnovers'] - x['airballs'] - x['bozo_moments']), reverse=True)
    moo_vp = stats_list[0]
    
    # Sort for LIP (lowest rating)
    sorted_lip = sorted(stats_list, key=lambda x: (x['rating'], -x['turnovers'] - x['airballs'] - x['bozo_moments']))
    lip = sorted_lip[0]

    return stats_list, moo_vp, lip

def add_game(opponent, date, cows_score, opponent_score, outcome, location, player_stats):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (opponent, date, cows_score, opponent_score, outcome, location))
    game_id = cursor.lastrowid

    for stat in player_stats:
        cursor.execute('''
            INSERT INTO stats (
                player_id, game_id, points, rebounds, assists, steals, blocks,
                turnovers, airballs, bozo_moments, fg, fga, ft, fta, three_pt, three_pta, rating, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stat['player_id'], game_id, stat['points'], stat['rebounds'], stat['assists'],
            stat['steals'], stat['blocks'], stat['turnovers'],
            stat['airballs'], stat['bozo_moments'], stat['fg'], stat['fga'], stat['ft'], stat['fta'],
            stat['three_pt'], stat['three_pta'], stat['rating'], stat['notes']
        ))
    conn.commit()
    conn.close()
    return game_id

def update_game(game_id, opponent, date, cows_score, opponent_score, outcome, location, player_stats):
    conn = get_db_connection()
    conn.execute('''
        UPDATE games
        SET opponent = ?, date = ?, cows_score = ?, opponent_score = ?, outcome = ?, location = ?
        WHERE id = ?
    ''', (opponent, date, cows_score, opponent_score, outcome, location, game_id))

    # Remove old stats
    conn.execute('DELETE FROM stats WHERE game_id = ?', (game_id,))

    # Insert new stats
    for stat in player_stats:
        conn.execute('''
            INSERT INTO stats (
                player_id, game_id, points, rebounds, assists, steals, blocks,
                turnovers, airballs, bozo_moments, fg, fga, ft, fta, three_pt, three_pta, rating, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stat['player_id'], game_id, stat['points'], stat['rebounds'], stat['assists'],
            stat['steals'], stat['blocks'], stat['turnovers'],
            stat['airballs'], stat['bozo_moments'], stat['fg'], stat['fga'], stat['ft'], stat['fta'],
            stat['three_pt'], stat['three_pta'], stat['rating'], stat['notes']
        ))
    conn.commit()
    conn.close()

def delete_game(game_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()

def get_player_averages():
    conn = get_db_connection()
    # SQL query to get averages, rounded to 1 decimal place
    averages = conn.execute('''
        SELECT p.id as player_id, p.name, p.jersey_number, p.nickname,
               COUNT(s.game_id) as games_played,
               ROUND(AVG(s.points), 1) as avg_points,
               ROUND(AVG(s.rebounds), 1) as avg_rebounds,
               ROUND(AVG(s.assists), 1) as avg_assists,
               ROUND(AVG(s.steals), 1) as avg_steals,
               ROUND(AVG(s.blocks), 1) as avg_blocks,
               ROUND(AVG(s.turnovers), 1) as avg_turnovers,
               ROUND(AVG(s.airballs), 1) as avg_airballs,
               ROUND(AVG(s.bozo_moments), 1) as avg_bozo_moments,
               ROUND(AVG(s.fg), 1) as avg_fg,
               ROUND(AVG(s.fga), 1) as avg_fga,
               ROUND(AVG(s.ft), 1) as avg_ft,
               ROUND(AVG(s.fta), 1) as avg_fta,
               ROUND(AVG(s.three_pt), 1) as avg_three_pt,
               ROUND(AVG(s.three_pta), 1) as avg_three_pta,
               ROUND(AVG(s.rating), 1) as avg_rating
        FROM players p
        LEFT JOIN stats s ON p.id = s.player_id
        GROUP BY p.id
        ORDER BY avg_points DESC, p.name ASC
    ''').fetchall()
    conn.close()

    averages_list = []
    for avg in averages:
        row = dict(avg)
        if row['games_played'] > 0:
            row['avg_fg_pct'] = round((row['avg_fg'] / row['avg_fga'] * 100.0), 1) if row['avg_fga'] > 0 else 0.0
        else:
            row['avg_rating'] = 0.0
            row['avg_fg_pct'] = 0.0
            for key in ['avg_points', 'avg_rebounds', 'avg_assists', 'avg_steals', 'avg_blocks', 
                        'avg_turnovers', 'avg_airballs', 'avg_bozo_moments', 'avg_fg', 'avg_fga', 
                        'avg_ft', 'avg_fta', 'avg_three_pt', 'avg_three_pta']:
                row[key] = 0.0
        averages_list.append(row)

    return averages_list

def get_player_totals():
    conn = get_db_connection()
    totals = conn.execute('''
        SELECT p.id as player_id, p.name, p.jersey_number, p.nickname,
               COUNT(s.game_id) as games_played,
               SUM(s.points) as total_points,
               SUM(s.rebounds) as total_rebounds,
               SUM(s.assists) as total_assists,
               SUM(s.steals) as total_steals,
               SUM(s.blocks) as total_blocks,
               SUM(s.turnovers) as total_turnovers,
               SUM(s.airballs) as total_airballs,
               SUM(s.bozo_moments) as total_bozo_moments,
               SUM(s.fg) as total_fg,
               SUM(s.fga) as total_fga,
               SUM(s.ft) as total_ft,
               SUM(s.fta) as total_fta,
               SUM(s.three_pt) as total_three_pt,
               SUM(s.three_pta) as total_three_pta,
               ROUND(AVG(s.rating), 1) as avg_rating
        FROM players p
        LEFT JOIN stats s ON p.id = s.player_id
        GROUP BY p.id
        ORDER BY total_points DESC, p.name ASC
    ''').fetchall()
    conn.close()

    totals_list = []
    for tot in totals:
        row = dict(tot)
        if row['games_played'] > 0:
            row['total_fg_pct'] = round((row['total_fg'] / row['total_fga'] * 100.0), 1) if row['total_fga'] > 0 else 0.0
        else:
            row['avg_rating'] = 0.0
            row['total_fg_pct'] = 0.0
            # Replace None with 0 for display
            for key in ['total_points', 'total_rebounds', 'total_assists', 'total_steals', 'total_blocks', 
                        'total_turnovers', 'total_airballs', 'total_bozo_moments', 'total_fg', 'total_fga', 
                        'total_ft', 'total_fta', 'total_three_pt', 'total_three_pta']:
                row[key] = 0
        totals_list.append(row)

    return totals_list

def get_single_game_records():
    conn = get_db_connection()
    categories = [
        ('points', 'Points', '🏀 Most Points'),
        ('rebounds', 'Rebounds', '🌾 Most Rebounds'),
        ('assists', 'Assists', '🥛 Most Assists'),
        ('steals', 'Steals', '🥩 Most Steals'),
        ('blocks', 'Blocks', '🛡️ Most Blocks'),
        ('turnovers', 'Turnovers', '💥 Most Turnovers'),
        ('airballs', 'Airballs', '💨 Most Airballs'),
        ('bozo_moments', 'Bozo Moments', '🤡 Most Bozo Moments'),
        ('rating', 'Rating', '⭐ Highest Rating')
    ]
    
    records = []
    for col, name, label in categories:
        row = conn.execute(f'''
            SELECT s.{col} as value, p.name, p.jersey_number, p.nickname, g.opponent, g.date, g.id as game_id
            FROM stats s
            JOIN players p ON s.player_id = p.id
            JOIN games g ON s.game_id = g.id
            ORDER BY s.{col} DESC, g.date DESC, p.name ASC
            LIMIT 1
        ''').fetchone()
        
        if row and row['value'] is not None and row['value'] > 0:
            records.append({
                'category': name,
                'label': label,
                'value': row['value'],
                'player_name': row['name'],
                'jersey_number': row['jersey_number'],
                'nickname': row['nickname'],
                'opponent': row['opponent'],
                'date': row['date'],
                'game_id': row['game_id']
            })
    conn.close()
    return records

def seed_db():
    if DATABASE_URL:
        return
    conn = get_db_connection()
    
    # Check if we have players already
    player_count = conn.execute('SELECT COUNT(*) FROM players').fetchone()[0]
    if player_count > 0:
        # If games exist, don't re-seed
        game_count = conn.execute('SELECT COUNT(*) FROM games').fetchone()[0]
        if game_count > 0:
            conn.close()
            return
    else:
        # Seed players
        players_data = [
            ("John Andreou", "50", "Big Man John"),
            ("Phillip Lee", "21", "Phlig"),
            ("Maxwell Glaubinger", "6", "GlubGlub"),
            ("Noah Shulman", "0", "Shylock Holmes"),
            ("Michael Abrams", "22", "Mikel"),
            ("Jack Slivken", "8", "Slivy"),
            ("Patrick Rossiello", "17", "Buckets"),
            ("Nik Gundrum", "11", "Gunny"),
            ("Stephen Kruse", "18", "Goose"),
            ("David Malitz", "N/A", "Money Malitz"),
            ("Chris Andreou", "N/A", "Big Man Chris")
        ]
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO players (name, jersey_number, nickname) VALUES (?, ?, ?)',
            players_data
        )
        conn.commit()

    # Retrieve inserted player IDs
    players_rows = conn.execute('SELECT id, name FROM players').fetchall()
    players_map = {row['name']: row['id'] for row in players_rows}

    cursor = conn.cursor()
    
    # 1. Seed Legacy Game
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES ('Legacy', '2026-06-25', 39, 47, 'L', 'Bouncy rims court')
    ''')
    game1_id = cursor.lastrowid
    
    raw_stats1 = [
        ("Jack Slivken", 0, 1, 3, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, ""),
        ("John Andreou", 0, 6, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, ""),
        ("Michael Abrams", 7, 5, 5, 2, 0, 0, 0, 1, 3, 4, 1, 4, 0, 0, "Bozo: violation on missed free throw"),
        ("Nik Gundrum", 16, 15, 2, 1, 2, 0, 0, 0, 7, 17, 0, 1, 2, 7, ""),
        ("Noah Shulman", 4, 4, 0, 2, 0, 2, 0, 1, 1, 5, 2, 5, 0, 1, "Bozo: Traveled while laying on the floor"),
        ("Patrick Rossiello", 0, 6, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, "Bozo: dribbled out of bounds"),
        ("Phillip Lee", 0, 1, 3, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, ""),
        ("Stephen Kruse", 12, 3, 0, 0, 0, 2, 1, 1, 4, 10, 0, 0, 4, 8, "Bozo: Shot a buzzer beater airball with 3 seconds left")
    ]
    
    game_stats = []
    for row in raw_stats1:
        p_name, pts, reb, ast, stl, blk, to, air, bozo, fg, fga, ft, fta, three_pt, three_pta, notes = row
        p_id = players_map[p_name]
        rating = calculate_rating(pts, reb, ast, stl, blk, to, air, bozo, fg, fga)
        game_stats.append((p_id, game1_id, pts, reb, ast, stl, blk, to, air, bozo, fg, fga, ft, fta, three_pt, three_pta, rating, notes))

    # 2. Seed Daddy's Home Game
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES ('Daddy''s Home', '2026-07-09', 48, 50, 'L', 'The Pasture (Home)')
    ''')
    game2_id = cursor.lastrowid
    
    raw_stats2 = [
        ("Chris Andreou", 5, 3, 2, 0, 1, 0, 1, 1, 2, 10, 0, 0, 1, 5, "Ball teleported out of his hands into the opponent"),
        ("David Malitz", 24, 7, 0, 0, 1, 2, 0, 0, 10, 24, 1, 1, 3, 13, ""),
        ("John Andreou", 0, 7, 3, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, ""),
        ("Nik Gundrum", 9, 10, 2, 2, 0, 0, 0, 0, 4, 16, 0, 1, 1, 5, ""),
        ("Noah Shulman", 7, 10, 1, 4, 0, 2, 0, 2, 3, 7, 0, 0, 1, 2, "Ran out of bounds, missed layup in clutch time"),
        ("Patrick Rossiello", 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, ""),
        ("Stephen Kruse", 3, 3, 2, 0, 0, 2, 1, 1, 1, 6, 0, 0, 1, 6, "Dribbled out of bounds")
    ]
    
    for row in raw_stats2:
        p_name, pts, reb, ast, stl, blk, to, air, bozo, fg, fga, ft, fta, three_pt, three_pta, notes = row
        p_id = players_map[p_name]
        rating = calculate_rating(pts, reb, ast, stl, blk, to, air, bozo, fg, fga)
        game_stats.append((p_id, game2_id, pts, reb, ast, stl, blk, to, air, bozo, fg, fga, ft, fta, three_pt, three_pta, rating, notes))

    cursor.executemany('''
        INSERT INTO stats (
            player_id, game_id, points, rebounds, assists, steals, blocks,
            turnovers, airballs, bozo_moments, fg, fga, ft, fta, three_pt, three_pta, rating, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', game_stats)
    conn.commit()
    conn.close()

def calculate_payout(wager, odds):
    if odds > 0:
        payout = wager + (wager * odds / 100.0)
    else:
        payout = wager + (wager * 100.0 / abs(odds))
    return int(round(payout))

def create_betting_user(nickname, pin):
    conn = get_db_connection()
    # Check if nickname already exists
    existing = conn.execute("SELECT id FROM betting_users WHERE nickname = ?", (nickname,)).fetchone()
    if existing:
        conn.close()
        return False, "Nickname already taken"
        
    pin_hash = generate_password_hash(pin)
    conn.execute('''
        INSERT INTO betting_users (nickname, pin_hash, balance)
        VALUES (?, ?, 100000)
    ''', (nickname, pin_hash))
    conn.commit()
    conn.close()
    return True, "User registered successfully!"

def verify_betting_user(nickname, pin):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM betting_users WHERE nickname = ?", (nickname,)).fetchone()
    conn.close()
    if user and check_password_hash(user['pin_hash'], pin):
        return dict(user)
    return None

def get_betting_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM betting_users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_prop(game_id, prop_type, player_id, line_value, odds_over, odds_under, description, category='player', display_order=0):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO props (game_id, prop_type, player_id, line_value, odds_over, odds_under, description, status, category, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    ''', (game_id, prop_type, player_id or None, line_value, odds_over, odds_under, description, category, display_order))
    conn.commit()
    conn.close()

def get_active_props():
    conn = get_db_connection()
    props = conn.execute('''
        SELECT pr.*, g.opponent, g.date, pl.name as player_name
        FROM props pr
        JOIN games g ON pr.game_id = g.id
        LEFT JOIN players pl ON pr.player_id = pl.id
        WHERE pr.status = 'open'
        ORDER BY pr.display_order ASC, g.date DESC, pr.id ASC
    ''').fetchall()
    conn.close()
    return [dict(p) for p in props]

def get_props_for_game(game_id):
    conn = get_db_connection()
    props = conn.execute('''
        SELECT pr.*, pl.name as player_name
        FROM props pr
        LEFT JOIN players pl ON pr.player_id = pl.id
        WHERE pr.game_id = ?
        ORDER BY pr.display_order ASC, pr.id ASC
    ''', (game_id,)).fetchall()
    conn.close()
    return [dict(p) for p in props]

def get_leaderboard():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT id, nickname, balance
        FROM betting_users
        ORDER BY balance DESC, nickname ASC
    ''').fetchall()
    conn.close()
    return [dict(u) for u in users]

def get_user_bets(user_id):
    conn = get_db_connection()
    wagers = conn.execute('''
        SELECT * FROM wagers
        WHERE user_id = ?
        ORDER BY placed_at DESC
    ''', (user_id,)).fetchall()
    
    wagers_list = []
    for w in wagers:
        w_dict = dict(w)
        legs = conn.execute('''
            SELECT b.*, pr.description, pr.prop_type, pr.line_value, g.opponent, g.date, pl.name as player_name
            FROM bets b
            JOIN props pr ON b.prop_id = pr.id
            JOIN games g ON pr.game_id = g.id
            LEFT JOIN players pl ON pr.player_id = pl.id
            WHERE b.wager_id = ?
            ORDER BY b.id ASC
        ''', (w_dict['id'],)).fetchall()
        w_dict['legs'] = [dict(l) for l in legs]
        wagers_list.append(w_dict)
        
    conn.close()
    return wagers_list

def american_to_decimal(odds):
    if odds > 0:
        return (odds / 100.0) + 1.0
    else:
        return (100.0 / abs(odds)) + 1.0

def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.0:
        return int(round((decimal_odds - 1.0) * 100.0))
    else:
        return int(round(-100.0 / (decimal_odds - 1.0)))

def calculate_parlay_odds(odds_list):
    if not odds_list:
        return -110
    total_decimal = 1.0
    for odds in odds_list:
        total_decimal *= american_to_decimal(odds)
    return decimal_to_american(total_decimal)

def place_bets(user_id, selections, is_parlay=False, parlay_wager=0):
    if is_betting_paused():
        return False, "🔒 Betting is currently paused by admin (Live Game In Progress)."

    if not selections:
        return False, "No selections provided"
        
    conn = get_db_connection()
    
    user = conn.execute("SELECT balance FROM betting_users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return False, "User not found"
        
    if is_parlay:
        total_wager = parlay_wager
        if total_wager <= 0:
            conn.close()
            return False, "Wager amount must be positive"
    else:
        total_wager = sum(int(sel.get('wager_amount', 0)) for sel in selections)
        if total_wager <= 0:
            conn.close()
            return False, "Wager amounts must be positive"
            
    if user['balance'] < total_wager:
        conn.close()
        return False, "Insufficient balance"
        
    prop_ids = [int(sel['prop_id']) for sel in selections]
    
    # PostgreSQL vs SQLite parameter placeholder length workaround
    placeholders = ','.join(['?'] * len(prop_ids))
    props = conn.execute(f"SELECT * FROM props WHERE id IN ({placeholders})", prop_ids).fetchall()
    props_map = {p['id']: p for p in props}
    
    for p_id in prop_ids:
        if p_id not in props_map or props_map[p_id]['status'] != 'open':
            conn.close()
            return False, "One or more props are closed or unavailable"
            
    if is_parlay:
        odds_list = []
        legs_data = []
        for sel in selections:
            p_id = int(sel['prop_id'])
            prop = props_map[p_id]
            selection = sel['selection']
            
            if selection in ['over', 'yes']:
                leg_odds = prop['odds_over']
            else:
                leg_odds = prop['odds_under']
                
            odds_list.append(leg_odds)
            legs_data.append((p_id, selection, leg_odds))
            
        combined_odds = calculate_parlay_odds(odds_list)
        
        conn.execute("UPDATE betting_users SET balance = balance - ? WHERE id = ?", (total_wager, user_id))
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wagers (user_id, wager_amount, odds_at_placed, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, total_wager, combined_odds))
        wager_id = cursor.lastrowid
        
        for p_id, selection, leg_odds in legs_data:
            cursor.execute('''
                INSERT INTO bets (wager_id, prop_id, selection, odds_at_placed, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (wager_id, p_id, selection, leg_odds))
            
    else:
        conn.execute("UPDATE betting_users SET balance = balance - ? WHERE id = ?", (total_wager, user_id))
        
        for sel in selections:
            p_id = int(sel['prop_id'])
            prop = props_map[p_id]
            selection = sel['selection']
            wager = int(sel['wager_amount'])
            
            if selection in ['over', 'yes']:
                leg_odds = prop['odds_over']
            else:
                leg_odds = prop['odds_under']
                
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO wagers (user_id, wager_amount, odds_at_placed, status)
                VALUES (?, ?, ?, 'pending')
            ''', (user_id, wager, leg_odds))
            wager_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO bets (wager_id, prop_id, selection, odds_at_placed, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (wager_id, p_id, selection, leg_odds))
            
    conn.commit()
    conn.close()
    return True, "Bets placed successfully!"

def place_bet(user_id, prop_id, wager_amount, selection):
    # Legacy wrapper function to keep tests passing
    selections = [{'prop_id': prop_id, 'selection': selection, 'wager_amount': wager_amount}]
    success, msg = place_bets(user_id, selections, is_parlay=False)
    return success, msg

def delete_prop(prop_id):
    conn = get_db_connection()
    pending_bets = conn.execute("SELECT DISTINCT wager_id FROM bets WHERE prop_id = ? AND status = 'pending'", (prop_id,)).fetchall()
    
    for row in pending_bets:
        wager_id = row['wager_id']
        wager = conn.execute("SELECT user_id, wager_amount, status FROM wagers WHERE id = ?", (wager_id,)).fetchone()
        if wager and wager['status'] == 'pending':
            conn.execute("UPDATE betting_users SET balance = balance + ? WHERE id = ?", (wager['wager_amount'], wager['user_id']))
            conn.execute("UPDATE wagers SET status = 'push', payout = ? WHERE id = ?", (wager['wager_amount'], wager_id))
            conn.execute("UPDATE bets SET status = 'push' WHERE wager_id = ?", (wager_id,))
            
    conn.execute("DELETE FROM props WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()

def grade_single_prop_conn(conn, prop_id, outcome):
    status_str = f"graded_{outcome}" if outcome != 'push' else 'push'
    conn.execute("UPDATE props SET status = ? WHERE id = ?", (status_str, prop_id))
    
    legs = conn.execute("SELECT * FROM bets WHERE prop_id = ? AND status = 'pending'", (prop_id,)).fetchall()
    wager_ids = set()
    
    for leg in legs:
        leg_id = leg['id']
        selection = leg['selection']
        wager_ids.add(leg['wager_id'])
        
        leg_status = 'lost'
        if outcome == 'push':
            leg_status = 'push'
        elif selection == outcome:
            leg_status = 'won'
            
        conn.execute("UPDATE bets SET status = ? WHERE id = ?", (leg_status, leg_id))
        
    for w_id in wager_ids:
        wager = conn.execute("SELECT * FROM wagers WHERE id = ?", (w_id,)).fetchone()
        if not wager or wager['status'] != 'pending':
            continue
            
        all_legs = conn.execute("SELECT * FROM bets WHERE wager_id = ?", (w_id,)).fetchall()
        
        has_lost = any(l['status'] == 'lost' for l in all_legs)
        any_pending = any(l['status'] == 'pending' for l in all_legs)
        
        if has_lost:
            conn.execute("UPDATE wagers SET status = 'lost', payout = 0 WHERE id = ?", (w_id,))
        elif not any_pending:
            multiplier = 1.0
            any_won = False
            
            for l in all_legs:
                if l['status'] == 'won':
                    multiplier *= american_to_decimal(l['odds_at_placed'])
                    any_won = True
                
            wager_amount = wager['wager_amount']
            user_id = wager['user_id']
            
            if not any_won:
                payout = wager_amount
                conn.execute("UPDATE wagers SET status = 'push', payout = ? WHERE id = ?", (payout, w_id))
                conn.execute("UPDATE betting_users SET balance = balance + ? WHERE id = ?", (payout, user_id))
            else:
                payout = int(round(wager_amount * multiplier))
                conn.execute("UPDATE wagers SET status = 'won', payout = ? WHERE id = ?", (payout, w_id))
                conn.execute("UPDATE betting_users SET balance = balance + ? WHERE id = ?", (payout, user_id))

def grade_prop(prop_id, outcome):
    conn = get_db_connection()
    grade_single_prop_conn(conn, prop_id, outcome)
    conn.commit()
    conn.close()

def auto_grade_game_props(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    if not game:
        conn.close()
        return

    stats_rows = conn.execute('SELECT * FROM stats WHERE game_id = ?', (game_id,)).fetchall()
    stats_map = {row['player_id']: row for row in stats_rows}

    props_to_grade = conn.execute("SELECT * FROM props WHERE game_id = ? AND status = 'open'", (game_id,)).fetchall()

    for prop in props_to_grade:
        prop_id = prop['id']
        prop_type = prop['prop_type']
        player_id = prop['player_id']
        line_value = prop['line_value']
        
        outcome = None

        if prop_type == 'outcome':
            game_outcome = game['outcome'].upper() # 'W' or 'L'
            outcome = 'yes' if game_outcome == 'W' else 'no'

        elif prop_type in ['points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'airballs', 'bozo_moments', 'rating', 'three_pt']:
            if player_id in stats_map:
                stat_row = stats_map[player_id]
                stat_value = stat_row[prop_type]
                
                if stat_value > line_value:
                    outcome = 'over'
                elif stat_value < line_value:
                    outcome = 'under'
                else:
                    outcome = 'push'
            else:
                # Did Not Play -> refund
                outcome = 'push'

        if outcome:
            grade_single_prop_conn(conn, prop_id, outcome)

    conn.commit()
    conn.close()

def is_betting_paused():
    try:
        conn = get_db_connection()
        val = conn.execute("SELECT value FROM settings WHERE key = 'betting_paused'").fetchone()
        conn.close()
        return val is not None and val['value'] == 'true'
    except Exception:
        return False

def set_betting_paused(paused):
    conn = get_db_connection()
    val_str = 'true' if paused else 'false'
    exists = conn.execute("SELECT 1 FROM settings WHERE key = 'betting_paused'").fetchone()
    if exists:
        conn.execute("UPDATE settings SET value = ? WHERE key = 'betting_paused'", (val_str,))
    else:
        conn.execute("INSERT INTO settings (key, value) VALUES ('betting_paused', ?)", (val_str,))
    conn.commit()
    conn.close()

def get_prop(prop_id):
    conn = get_db_connection()
    prop = conn.execute("SELECT * FROM props WHERE id = ?", (prop_id,)).fetchone()
    conn.close()
    return dict(prop) if prop else None

def update_prop(prop_id, game_id, prop_type, player_id, line_value, odds_over, odds_under, description, category, display_order):
    conn = get_db_connection()
    conn.execute('''
        UPDATE props
        SET game_id = ?, prop_type = ?, player_id = ?, line_value = ?, odds_over = ?, odds_under = ?, description = ?, category = ?, display_order = ?
        WHERE id = ?
    ''', (game_id, prop_type, player_id or None, line_value, odds_over, odds_under, description, category, display_order, prop_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")

