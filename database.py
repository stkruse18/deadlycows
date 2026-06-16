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

def calculate_mvi(points, rebounds, assists, steals, blocks, turnovers, fouls, airballs, bozo_moments):
    """
    Moo-Value Index (MVI):
    MVI = Points + 1.2*Rebounds + 1.5*Assists + 2.0*Steals + 2.0*Blocks - 1.5*Turnovers - 1.0*Fouls - 3.0*Airballs - 5.0*Bozo_Moments
    """
    return (
        points 
        + 1.2 * rebounds 
        + 1.5 * assists 
        + 2.0 * steals 
        + 2.0 * blocks 
        - 1.5 * turnovers 
        - 1.0 * fouls 
        - 3.0 * airballs 
        - 5.0 * bozo_moments
    )

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

    # Convert to list of dicts and calculate MVI
    stats_list = []
    for s in stats:
        row = dict(s)
        row['mvi'] = round(calculate_mvi(
            row['points'], row['rebounds'], row['assists'], row['steals'], row['blocks'],
            row['turnovers'], row['fouls'], row['airballs'], row['bozo_moments']
        ), 1)
        stats_list.append(row)

    if not stats_list:
        return [], None, None

    # Determine Moo-VP (highest MVI) and LIP (lowest MVI)
    # Sort stats by MVI descending
    sorted_stats = sorted(stats_list, key=lambda x: x['mvi'], reverse=True)
    moo_vp = sorted_stats[0]
    lip = sorted_stats[-1]

    # Handle single player edge case (could be both, but we show them accordingly)
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
                turnovers, fouls, minutes, airballs, bozo_moments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stat['player_id'], game_id, stat['points'], stat['rebounds'], stat['assists'],
            stat['steals'], stat['blocks'], stat['turnovers'], stat['fouls'], stat['minutes'],
            stat['airballs'], stat['bozo_moments']
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
                turnovers, fouls, minutes, airballs, bozo_moments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stat['player_id'], game_id, stat['points'], stat['rebounds'], stat['assists'],
            stat['steals'], stat['blocks'], stat['turnovers'], stat['fouls'], stat['minutes'],
            stat['airballs'], stat['bozo_moments']
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
               ROUND(AVG(s.fouls), 1) as avg_fouls,
               ROUND(AVG(s.minutes), 1) as avg_minutes,
               ROUND(AVG(s.airballs), 1) as avg_airballs,
               ROUND(AVG(s.bozo_moments), 1) as avg_bozo_moments
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
            row['avg_mvi'] = round(calculate_mvi(
                row['avg_points'], row['avg_rebounds'], row['avg_assists'], row['avg_steals'], row['avg_blocks'],
                row['avg_turnovers'], row['avg_fouls'], row['avg_airballs'], row['avg_bozo_moments']
            ), 1)
        else:
            row['avg_mvi'] = 0.0
            for key in ['avg_points', 'avg_rebounds', 'avg_assists', 'avg_steals', 'avg_blocks', 
                        'avg_turnovers', 'avg_fouls', 'avg_minutes', 'avg_airballs', 'avg_bozo_moments']:
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
               SUM(s.fouls) as total_fouls,
               SUM(s.minutes) as total_minutes,
               SUM(s.airballs) as total_airballs,
               SUM(s.bozo_moments) as total_bozo_moments
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
            row['total_mvi'] = round(calculate_mvi(
                row['total_points'] or 0, row['total_rebounds'] or 0, row['total_assists'] or 0, 
                row['total_steals'] or 0, row['total_blocks'] or 0, row['total_turnovers'] or 0, 
                row['total_fouls'] or 0, row['total_airballs'] or 0, row['total_bozo_moments'] or 0
            ), 1)
        else:
            row['total_mvi'] = 0.0
            # Replace None with 0 for display
            for key in ['total_points', 'total_rebounds', 'total_assists', 'total_steals', 'total_blocks', 
                        'total_turnovers', 'total_fouls', 'total_minutes', 'total_airballs', 'total_bozo_moments']:
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
        ('fouls', 'Fouls', '⚠️ Most Fouls'),
        ('airballs', 'Airballs', '💨 Most Airballs'),
        ('bozo_moments', 'Bozo Moments', '🤡 Most Bozo Moments')
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
        conn.close()
        return

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
        ("Stephen Kruse", "18", "Goose")
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

    # Seed 3 games
    # Game 1 vs Bacon Blazers
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES ('Bacon Blazers', '2026-05-15', 115, 92, 'W', 'The Pasture (Home)')
    ''')
    game1_id = cursor.lastrowid
    
    game1_stats = [
        (players_map["John Andreou"], game1_id, 28, 10, 8, 2, 1, 3, 2, 36, 0, 0),
        (players_map["Phillip Lee"], game1_id, 35, 5, 4, 3, 2, 2, 1, 38, 1, 0),
        (players_map["Maxwell Glaubinger"], game1_id, 22, 3, 11, 1, 0, 4, 3, 34, 0, 1),
        (players_map["Stephen Kruse"], game1_id, 10, 15, 1, 0, 4, 1, 4, 28, 2, 2),
        (players_map["Michael Abrams"], game1_id, 3, 18, 2, 4, 1, 1, 5, 32, 0, 0),
        (players_map["Noah Shulman"], game1_id, 6, 2, 4, 1, 0, 2, 2, 15, 1, 1),
        (players_map["Jack Slivken"], game1_id, 4, 3, 1, 0, 1, 1, 1, 12, 0, 0),
        (players_map["Patrick Rossiello"], game1_id, 5, 1, 2, 1, 0, 0, 1, 14, 0, 0),
        (players_map["Nik Gundrum"], game1_id, 2, 5, 1, 1, 1, 1, 2, 15, 0, 1)
    ]
    
    # Game 2 vs Porkers Spurs
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES ('Porkers Spurs', '2026-05-20', 103, 110, 'L', 'The Pigpen (Away)')
    ''')
    game2_id = cursor.lastrowid
    
    game2_stats = [
        (players_map["John Andreou"], game2_id, 20, 8, 5, 1, 0, 6, 4, 32, 1, 2),
        (players_map["Phillip Lee"], game2_id, 40, 6, 3, 2, 1, 1, 2, 40, 0, 0),
        (players_map["Maxwell Glaubinger"], game2_id, 15, 2, 5, 0, 0, 2, 1, 30, 3, 0),
        (players_map["Stephen Kruse"], game2_id, 8, 12, 0, 1, 3, 3, 5, 25, 1, 3),
        (players_map["Michael Abrams"], game2_id, 2, 22, 1, 2, 2, 2, 4, 35, 0, 1),
        (players_map["Noah Shulman"], game2_id, 5, 1, 3, 1, 0, 1, 1, 15, 1, 0),
        (players_map["Jack Slivken"], game2_id, 3, 2, 2, 0, 1, 1, 2, 15, 0, 0),
        (players_map["Patrick Rossiello"], game2_id, 4, 1, 1, 0, 0, 0, 1, 12, 0, 0),
        (players_map["Nik Gundrum"], game2_id, 6, 3, 0, 1, 0, 1, 2, 16, 1, 1)
    ]

    # Game 3 vs Milk Shakers
    cursor.execute('''
        INSERT INTO games (opponent, date, cows_score, opponent_score, outcome, location)
        VALUES ('Milk Shakers', '2026-05-28', 132, 110, 'W', 'The Pasture (Home)')
    ''')
    game3_id = cursor.lastrowid
    
    game3_stats = [
        (players_map["John Andreou"], game3_id, 30, 12, 12, 3, 2, 2, 3, 38, 0, 0),
        (players_map["Phillip Lee"], game3_id, 32, 4, 6, 1, 1, 3, 2, 36, 0, 1),
        (players_map["Maxwell Glaubinger"], game3_id, 38, 1, 4, 2, 0, 1, 2, 35, 1, 0),
        (players_map["Stephen Kruse"], game3_id, 6, 8, 2, 0, 2, 4, 6, 20, 2, 2),
        (players_map["Michael Abrams"], game3_id, 6, 15, 3, 5, 3, 0, 3, 33, 0, 0),
        (players_map["Noah Shulman"], game3_id, 8, 2, 4, 1, 0, 1, 2, 16, 0, 0),
        (players_map["Jack Slivken"], game3_id, 6, 4, 1, 1, 1, 1, 2, 15, 1, 1),
        (players_map["Patrick Rossiello"], game3_id, 4, 2, 1, 0, 0, 0, 1, 14, 0, 0),
        (players_map["Nik Gundrum"], game3_id, 2, 3, 1, 2, 1, 1, 1, 13, 0, 0)
    ]

    all_game_stats = game1_stats + game2_stats + game3_stats
    cursor.executemany('''
        INSERT INTO stats (
            player_id, game_id, points, rebounds, assists, steals, blocks,
            turnovers, fouls, minutes, airballs, bozo_moments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', all_game_stats)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Initialize and seed database if run directly
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")
