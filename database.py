import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deadlycows.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
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

if __name__ == '__main__':
    # Initialize and seed database if run directly
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")
