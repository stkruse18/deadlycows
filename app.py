from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import database

app = Flask(__name__)
# Secure secret key, using environment variable or safe default
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'udderly_secret_cow_key')

# Simple admin passphrase, defaulting to 'moo'
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'moo')

# Ensure database is initialized and seeded on start if not present
if not os.path.exists(database.DB_PATH):
    with app.app_context():
        database.init_db()
        database.seed_db()

def is_admin():
    return session.get('logged_in') == True

@app.context_processor
def inject_globals():
    # Make admin status, current betting user, and betting paused status available to all templates
    betting_user = None
    if session.get('betting_user_id'):
        betting_user = database.get_betting_user(session.get('betting_user_id'))
    paused = database.is_betting_paused()
    return dict(is_admin=is_admin, current_betting_user=betting_user, betting_paused=paused)


@app.route('/')
def index():
    games = database.get_all_games()
    
    # Calculate Wins and Udders (Losses)
    wins = sum(1 for g in games if g['outcome'].upper() == 'W')
    udders = sum(1 for g in games if g['outcome'].upper() == 'L')
    
    # Get last 3 games for recent results
    recent_games = games[:3]
    
    # Get team leader averages
    averages = database.get_player_averages()
    ppg_leader = averages[0] if averages and averages[0]['avg_points'] > 0 else None
    rpg_leader = sorted(averages, key=lambda x: x['avg_rebounds'], reverse=True)[0] if averages and averages[0]['avg_rebounds'] > 0 else None
    apg_leader = sorted(averages, key=lambda x: x['avg_assists'], reverse=True)[0] if averages and averages[0]['avg_assists'] > 0 else None
    
    # Funny leaders
    airball_leader = sorted(averages, key=lambda x: x['avg_airballs'], reverse=True)[0] if averages and averages[0]['avg_airballs'] > 0 else None
    bozo_leader = sorted(averages, key=lambda x: x['avg_bozo_moments'], reverse=True)[0] if averages and averages[0]['avg_bozo_moments'] > 0 else None

    return render_template(
        'index.html',
        games=games,
        wins=wins,
        udders=udders,
        recent_games=recent_games,
        ppg_leader=ppg_leader,
        rpg_leader=rpg_leader,
        apg_leader=apg_leader,
        airball_leader=airball_leader,
        bozo_leader=bozo_leader
    )

@app.route('/averages')
def averages():
    player_averages = database.get_player_averages()
    return render_template('averages.html', averages=player_averages)

@app.route('/totals')
def totals():
    player_totals = database.get_player_totals()
    records = database.get_single_game_records()
    return render_template('totals.html', totals=player_totals, records=records)

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    game = database.get_game(game_id)
    if not game:
        flash("That game went out to pasture. (Not found)", "danger")
        return redirect(url_for('index'))
    
    stats, moo_vp, lip = database.get_game_stats(game_id)
    return render_template(
        'game.html',
        game=game,
        stats=stats,
        moo_vp=moo_vp,
        lip=lip
    )

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("Welcome to the Cattle Ranch, Coach!", "success")
            return redirect(url_for('manage'))
        else:
            flash("Wrong password! Don't be a cow-ard.", "danger")
            return render_template('manage_login.html')

    if not is_admin():
        return render_template('manage_login.html')

    players = database.get_all_players()
    games = database.get_all_games()
    return render_template('manage.html', players=players, games=games)

@app.route('/manage/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out from the barn.", "info")
    return redirect(url_for('index'))

@app.route('/manage/players', methods=['POST'])
def manage_players():
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    name = request.form.get('name')
    jersey = request.form.get('jersey_number')
    nickname = request.form.get('nickname')

    if name and jersey:
        database.add_player(name, jersey, nickname or "")
        flash(f"Drafted {name} successfully!", "success")
    else:
        flash("Failed to draft player. Name and Jersey are required.", "danger")
    
    return redirect(url_for('manage'))

@app.route('/manage/players/delete/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    database.delete_player(player_id)
    flash("Sent player out to greener pastures (Deleted).", "info")
    return redirect(url_for('manage'))

@app.route('/manage/game/new', methods=['GET', 'POST'])
def new_game():
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    players = database.get_all_players()

    if request.method == 'POST':
        opponent = request.form.get('opponent')
        date = request.form.get('date')
        cows_score = int(request.form.get('cows_score', 0))
        opponent_score = int(request.form.get('opponent_score', 0))
        outcome = request.form.get('outcome', 'W')
        location = request.form.get('location', 'The Pasture (Home)')

        # Gather player stats
        player_stats = []
        for p in players:
            p_id = p['id']
            # Only add stats if the player played (checkbox checked)
            played = request.form.get(f'played_{p_id}') == 'on'
            if played:
                points = int(request.form.get(f'points_{p_id}', 0))
                rebounds = int(request.form.get(f'rebounds_{p_id}', 0))
                assists = int(request.form.get(f'assists_{p_id}', 0))
                steals = int(request.form.get(f'steals_{p_id}', 0))
                blocks = int(request.form.get(f'blocks_{p_id}', 0))
                turnovers = int(request.form.get(f'turnovers_{p_id}', 0))
                airballs = int(request.form.get(f'airballs_{p_id}', 0))
                bozo_moments = int(request.form.get(f'bozo_moments_{p_id}', 0))
                fg = int(request.form.get(f'fg_{p_id}', 0))
                fga = int(request.form.get(f'fga_{p_id}', 0))
                ft = int(request.form.get(f'ft_{p_id}', 0))
                fta = int(request.form.get(f'fta_{p_id}', 0))
                three_pt = int(request.form.get(f'three_pt_{p_id}', 0))
                three_pta = int(request.form.get(f'three_pta_{p_id}', 0))
                
                # Dynamic rating calculation
                rating = database.calculate_rating(
                    points, rebounds, assists, steals, blocks, 
                    turnovers, airballs, bozo_moments, fg, fga
                )
                
                stat_row = {
                    'player_id': p_id,
                    'points': points,
                    'rebounds': rebounds,
                    'assists': assists,
                    'steals': steals,
                    'blocks': blocks,
                    'turnovers': turnovers,
                    'airballs': airballs,
                    'bozo_moments': bozo_moments,
                    'fg': fg,
                    'fga': fga,
                    'ft': ft,
                    'fta': fta,
                    'three_pt': three_pt,
                    'three_pta': three_pta,
                    'rating': rating,
                    'notes': request.form.get(f'notes_{p_id}', '').strip()
                }
                player_stats.append(stat_row)

        if opponent and date:
            game_id = database.add_game(opponent, date, cows_score, opponent_score, outcome, location, player_stats)
            database.auto_grade_game_props(game_id)
            flash("Game and player box score logged successfully!", "success")
            return redirect(url_for('manage'))
        else:
            flash("Opponent and Date are required.", "danger")

    return render_template('edit_game.html', title="Log New Slaughter (Game)", players=players, game=None)

@app.route('/manage/game/edit/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    game = database.get_game(game_id)
    if not game:
        flash("Game not found.", "danger")
        return redirect(url_for('manage'))

    players = database.get_all_players()
    game_stats_rows, _, _ = database.get_game_stats(game_id)
    
    # Map stats by player_id for easy form population
    stats_map = {row['player_id']: row for row in game_stats_rows}

    if request.method == 'POST':
        opponent = request.form.get('opponent')
        date = request.form.get('date')
        cows_score = int(request.form.get('cows_score', 0))
        opponent_score = int(request.form.get('opponent_score', 0))
        outcome = request.form.get('outcome', 'W')
        location = request.form.get('location', 'The Pasture (Home)')

        # Gather player stats
        player_stats = []
        for p in players:
            p_id = p['id']
            played = request.form.get(f'played_{p_id}') == 'on'
            if played:
                points = int(request.form.get(f'points_{p_id}', 0))
                rebounds = int(request.form.get(f'rebounds_{p_id}', 0))
                assists = int(request.form.get(f'assists_{p_id}', 0))
                steals = int(request.form.get(f'steals_{p_id}', 0))
                blocks = int(request.form.get(f'blocks_{p_id}', 0))
                turnovers = int(request.form.get(f'turnovers_{p_id}', 0))
                airballs = int(request.form.get(f'airballs_{p_id}', 0))
                bozo_moments = int(request.form.get(f'bozo_moments_{p_id}', 0))
                fg = int(request.form.get(f'fg_{p_id}', 0))
                fga = int(request.form.get(f'fga_{p_id}', 0))
                ft = int(request.form.get(f'ft_{p_id}', 0))
                fta = int(request.form.get(f'fta_{p_id}', 0))
                three_pt = int(request.form.get(f'three_pt_{p_id}', 0))
                three_pta = int(request.form.get(f'three_pta_{p_id}', 0))
                
                # Dynamic rating calculation
                rating = database.calculate_rating(
                    points, rebounds, assists, steals, blocks, 
                    turnovers, airballs, bozo_moments, fg, fga
                )
                
                stat_row = {
                    'player_id': p_id,
                    'points': points,
                    'rebounds': rebounds,
                    'assists': assists,
                    'steals': steals,
                    'blocks': blocks,
                    'turnovers': turnovers,
                    'airballs': airballs,
                    'bozo_moments': bozo_moments,
                    'fg': fg,
                    'fga': fga,
                    'ft': ft,
                    'fta': fta,
                    'three_pt': three_pt,
                    'three_pta': three_pta,
                    'rating': rating,
                    'notes': request.form.get(f'notes_{p_id}', '').strip()
                }
                player_stats.append(stat_row)

        if opponent and date:
            database.update_game(game_id, opponent, date, cows_score, opponent_score, outcome, location, player_stats)
            database.auto_grade_game_props(game_id)
            flash("Game details and box score updated!", "success")
            return redirect(url_for('manage'))
        else:
            flash("Opponent and Date are required.", "danger")

    return render_template(
        'edit_game.html',
        title="Edit Slaughter Details",
        players=players,
        game=game,
        stats_map=stats_map
    )

@app.route('/manage/game/delete/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    database.delete_game(game_id)
    flash("Game deleted successfully.", "info")
    return redirect(url_for('manage'))

@app.route('/betting')
def betting():
    user_id = session.get('betting_user_id')
    user_bets = []
    if user_id:
        user_bets = database.get_user_bets(user_id)
    
    active_props = database.get_active_props()
    player_props = [p for p in active_props if p.get('category', 'player') == 'player']
    team_props = [p for p in active_props if p.get('category', 'player') == 'team']
    return render_template('betting.html', player_props=player_props, team_props=team_props, user_bets=user_bets)

@app.route('/betting/signup', methods=['GET', 'POST'])
def betting_signup():
    if session.get('betting_user_id'):
        return redirect(url_for('betting'))

    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        pin = request.form.get('pin', '').strip()

        if not nickname or not pin:
            flash("Nickname and PIN are required.", "danger")
            return render_template('betting_auth.html', action='signup')

        if len(pin) != 4 or not pin.isdigit():
            flash("PIN must be exactly 4 digits.", "danger")
            return render_template('betting_auth.html', action='signup')

        success, message = database.create_betting_user(nickname, pin)
        if success:
            user = database.verify_betting_user(nickname, pin)
            if user:
                session['betting_user_id'] = user['id']
                session['betting_nickname'] = user['nickname']
                flash(f"Welcome to the Book, {nickname}! Starting balance: $100,000.", "success")
                return redirect(url_for('betting'))
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('betting_login'))
        else:
            flash(message, "danger")

    return render_template('betting_auth.html', action='signup')

@app.route('/betting/login', methods=['GET', 'POST'])
def betting_login():
    if session.get('betting_user_id'):
        return redirect(url_for('betting'))

    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        pin = request.form.get('pin', '').strip()

        user = database.verify_betting_user(nickname, pin)
        if user:
            session['betting_user_id'] = user['id']
            session['betting_nickname'] = user['nickname']
            flash(f"Welcome back, {nickname}!", "success")
            return redirect(url_for('betting'))
        else:
            flash("Invalid nickname or PIN.", "danger")

    return render_template('betting_auth.html', action='login')

@app.route('/betting/logout')
def betting_logout():
    session.pop('betting_user_id', None)
    session.pop('betting_nickname', None)
    flash("Successfully logged out of the Book.", "info")
    return redirect(url_for('betting'))

@app.route('/betting/place-bets', methods=['POST'])
def place_bets():
    user_id = session.get('betting_user_id')
    if not user_id:
        return jsonify({"success": False, "message": "You must be logged in to place bets."}), 401

    if database.is_betting_paused():
        return jsonify({"success": False, "message": "🔒 Betting is currently paused by admin (Live Game In Progress)."}), 400

    data = request.get_json() or {}
    is_parlay = data.get('is_parlay', False)
    parlay_wager = data.get('parlay_wager', 0)
    selections = data.get('selections', [])

    if not selections:
        return jsonify({"success": False, "message": "No selections provided."}), 400

    try:
        if is_parlay:
            parlay_wager = int(parlay_wager)
            if parlay_wager <= 0:
                return jsonify({"success": False, "message": "Wager amount must be a positive integer."}), 400
        else:
            # Validate individual selections
            for sel in selections:
                sel['wager_amount'] = int(sel.get('wager_amount', 0))
                if sel['wager_amount'] <= 0:
                    return jsonify({"success": False, "message": "Wager amounts must be positive integers."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Wager amount must be a positive integer."}), 400

    success, message = database.place_bets(user_id, selections, is_parlay=is_parlay, parlay_wager=parlay_wager)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message})

@app.route('/betting/leaderboard')
def betting_leaderboard():
    leaderboard = database.get_leaderboard()
    return render_template('betting_leaderboard.html', leaderboard=leaderboard)

@app.route('/manage/props', methods=['GET', 'POST'])
def manage_props():
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    if request.method == 'POST':
        game_id = request.form.get('game_id')
        prop_type = request.form.get('prop_type')
        player_id = request.form.get('player_id')
        line_value = request.form.get('line_value')
        odds_over = request.form.get('odds_over')
        odds_under = request.form.get('odds_under')
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'player')
        display_order = request.form.get('display_order', '0')

        if not game_id or not prop_type or not line_value or not odds_over or not odds_under or not description:
            flash("All fields are required to create a prop.", "danger")
        else:
            try:
                p_id = int(player_id) if player_id and player_id != 'None' else None
                database.create_prop(
                    game_id=int(game_id),
                    prop_type=prop_type,
                    player_id=p_id,
                    line_value=float(line_value),
                    odds_over=int(odds_over),
                    odds_under=int(odds_under),
                    description=description,
                    category=category,
                    display_order=int(display_order)
                )
                flash("Prop created successfully!", "success")
            except ValueError:
                flash("Error parsing numeric values.", "danger")

    games = database.get_all_games()
    players = database.get_all_players()
    active_props = database.get_active_props()
    
    all_props = []
    if games:
        for g in games[:3]:
            g_props = database.get_props_for_game(g['id'])
            for gp in g_props:
                gp['opponent'] = g['opponent']
                gp['date'] = g['date']
                all_props.append(gp)

    return render_template('manage_props.html', games=games, players=players, active_props=active_props, all_props=all_props)

@app.route('/manage/props/delete/<int:prop_id>', methods=['POST'])
def delete_prop(prop_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    database.delete_prop(prop_id)
    flash("Prop deleted and pending bets refunded.", "info")
    return redirect(url_for('manage_props'))

@app.route('/manage/props/grade/<int:prop_id>', methods=['POST'])
def grade_prop(prop_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    outcome = request.form.get('outcome')
    if outcome not in ['over', 'under', 'yes', 'no', 'push']:
        flash("Invalid grading outcome.", "danger")
    else:
        database.grade_prop(prop_id, outcome)
        flash(f"Prop graded successfully as '{outcome.upper()}'!", "success")

    return redirect(url_for('manage_props'))

@app.route('/manage/props/edit/<int:prop_id>', methods=['GET', 'POST'])
def edit_prop(prop_id):
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    prop = database.get_prop(prop_id)
    if not prop:
        flash("Prop not found.", "danger")
        return redirect(url_for('manage_props'))

    if request.method == 'POST':
        game_id = request.form.get('game_id')
        prop_type = request.form.get('prop_type')
        player_id = request.form.get('player_id')
        line_value = request.form.get('line_value')
        odds_over = request.form.get('odds_over')
        odds_under = request.form.get('odds_under')
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'player')
        display_order = request.form.get('display_order', '0')

        if not game_id or not prop_type or not line_value or not odds_over or not odds_under or not description:
            flash("All fields are required to update the prop.", "danger")
        else:
            try:
                p_id = int(player_id) if player_id and player_id != 'None' else None
                database.update_prop(
                    prop_id=prop_id,
                    game_id=int(game_id),
                    prop_type=prop_type,
                    player_id=p_id,
                    line_value=float(line_value),
                    odds_over=int(odds_over),
                    odds_under=int(odds_under),
                    description=description,
                    category=category,
                    display_order=int(display_order)
                )
                flash("Prop updated successfully!", "success")
                return redirect(url_for('manage_props'))
            except ValueError:
                flash("Error parsing numeric values.", "danger")

    games = database.get_all_games()
    players = database.get_all_players()
    return render_template('manage_props_edit.html', prop=prop, games=games, players=players)

@app.route('/manage/betting/toggle-pause', methods=['POST'])
def toggle_betting_pause():
    if not is_admin():
        flash("Unauthorized pasture access!", "danger")
        return redirect(url_for('manage'))

    current_state = database.is_betting_paused()
    database.set_betting_paused(not current_state)
    new_state = "PAUSED" if not current_state else "RESUMED"
    flash(f"Betting has been successfully {new_state}!", "success")
    return redirect(url_for('manage_props'))

if __name__ == '__main__':
    # Run locally in debug mode
    app.run(host='0.0.0.0', port=5001, debug=True)

