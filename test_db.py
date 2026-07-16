import database
import random

def test_database():
    print("Running database tests...")
    
    # 1. Initialize DB
    database.init_db()
    print("Database initialized.")
    
    # 2. Seed DB
    database.seed_db()
    print("Database seeded.")
    
    # 3. Test players retrieval
    players = database.get_all_players()
    assert len(players) == 11, f"Expected 11 players, got {len(players)}"
    print("✓ Successfully loaded 11 players.")
    
    # 4. Test games retrieval
    games = database.get_all_games()
    assert len(games) >= 2, f"Expected at least 2 games, got {len(games)}"
    opponent_names = [g['opponent'] for g in games]
    assert 'Legacy' in opponent_names, f"Expected Legacy in games list, got {opponent_names}"
    assert "Daddy's Home" in opponent_names, f"Expected Daddy's Home in games list, got {opponent_names}"
    print("✓ Successfully verified Daddy's Home and Legacy in games.")
    
    # 5. Check Legacy Game Stats & Ratings
    legacy_game = [g for g in games if g['opponent'] == 'Legacy'][0]
    stats, moo_vp, lip = database.get_game_stats(legacy_game['id'])
    
    assert len(stats) == 8, f"Expected 8 stats rows, got {len(stats)}"
    print("✓ Successfully fetched stats for 8 active players.")

    # Find Nik Gundrum
    nik = [s for s in stats if s['name'] == 'Nik Gundrum'][0]
    assert nik['rating'] == 98, f"Nik rating expected 98, got {nik['rating']}"
    assert nik['fg'] == 7, f"Nik fg expected 7, got {nik['fg']}"
    assert nik['fga'] == 17, f"Nik fga expected 17, got {nik['fga']}"
    assert nik['ft'] == 0, f"Nik ft expected 0, got {nik['ft']}"
    assert nik['fta'] == 1, f"Nik fta expected 1, got {nik['fta']}"
    print("✓ Nik Gundrum stats, field goals (7/17), free throws (0/1), and computed rating (98) are correct.")

    # Find Michael Abrams
    abrams = [s for s in stats if s['name'] == 'Michael Abrams'][0]
    assert abrams['ft'] == 1, f"Abrams ft expected 1, got {abrams['ft']}"
    assert abrams['fta'] == 4, f"Abrams fta expected 4, got {abrams['fta']}"
    assert abrams['notes'] == "Bozo: violation on missed free throw", f"Abrams notes incorrect: {abrams['notes']}"
    print("✓ Michael Abrams stats, free throws (1/4), and custom note verified.")

    # Find Stephen Kruse
    stephen = [s for s in stats if s['name'] == "Stephen Kruse"][0]
    assert stephen['rating'] == 74, f"Stephen rating expected 74, got {stephen['rating']}"
    assert stephen['fg'] == 4, f"Stephen fg expected 4, got {stephen['fg']}"
    assert stephen['fga'] == 10, f"Stephen fga expected 10, got {stephen['fga']}"
    assert stephen['three_pt'] == 4, f"Stephen three_pt expected 4, got {stephen['three_pt']}"
    assert stephen['three_pta'] == 8, f"Stephen three_pta expected 8, got {stephen['three_pta']}"
    assert stephen['notes'] == "Bozo: Shot a buzzer beater airball with 3 seconds left", f"Stephen notes incorrect: {stephen['notes']}"
    print("✓ Stephen Kruse stats, field goals (4/10), 3-pointers (4/8), computed rating (74), and custom note verified.")
    
    # Verify awards: Moo-VP is Nik Gundrum (highest rating: 98) and LIP is Patrick Rossiello (lowest rating: 69)
    assert moo_vp['name'] == 'Nik Gundrum', f"Expected Moo-VP Nik Gundrum, got {moo_vp['name']}"
    assert lip['name'] == "Patrick Rossiello", f"Expected LIP Patrick Rossiello, got {lip['name']}"
    assert lip['rating'] == 69, f"Expected LIP rating 69, got {lip['rating']}"
    print(f"✓ Game awards: Moo-VP = {moo_vp['name']} ({moo_vp['rating']}), LIP = {lip['name']} ({lip['rating']}).")
    
    # 6. Test Averages and Totals
    averages = database.get_player_averages()
    assert len(averages) == 11, f"Expected 11 player averages, got {len(averages)}"
    nik_avg = [a for a in averages if a['name'] == 'Nik Gundrum'][0]
    assert nik_avg['avg_fg'] == 5.5, f"Expected avg_fg 5.5, got {nik_avg['avg_fg']}"
    assert nik_avg['avg_fga'] == 16.5, f"Expected avg_fga 16.5, got {nik_avg['avg_fga']}"
    assert nik_avg['avg_ft'] == 0.0, f"Expected avg_ft 0.0, got {nik_avg['avg_ft']}"
    assert nik_avg['avg_fta'] == 1.0, f"Expected avg_fta 1.0, got {nik_avg['avg_fta']}"
    assert nik_avg['avg_three_pt'] == 1.5, f"Expected avg_three_pt 1.5, got {nik_avg['avg_three_pt']}"
    assert nik_avg['avg_three_pta'] == 6.0, f"Expected avg_three_pta 6.0, got {nik_avg['avg_three_pta']}"
    print("✓ Player averages retrieved successfully.")
    
    totals = database.get_player_totals()
    assert len(totals) == 11, f"Expected 11 player totals, got {len(totals)}"
    print("✓ Player totals retrieved successfully.")
    
    # 7. Test Betting System
    print("\nRunning betting system tests...")
    
    # User registration with randomized nickname for test isolation
    test_nick = f"cow_punter_{random.randint(1000, 9999)}"
    reg_success, msg = database.create_betting_user(test_nick, "4321")
    assert reg_success is True, f"Failed to register user: {msg}"
    print(f"✓ Successfully registered '{test_nick}'.")
    
    # Double registration fails
    reg_fail, msg = database.create_betting_user(test_nick, "1111")
    assert reg_fail is False, "Expected registration fail for duplicate user"
    print("✓ Prevented duplicate user registration.")
    
    # Verification
    user = database.verify_betting_user(test_nick, "4321")
    assert user is not None, "Failed to verify correct PIN"
    assert user['nickname'] == test_nick, f"Expected nickname {test_nick}"
    assert user['balance'] == 100000, f"Expected 100000 balance, got {user['balance']}"
    
    user_invalid = database.verify_betting_user(test_nick, "1111")
    assert user_invalid is None, "Expected None verification for invalid PIN"
    print("✓ User verification and balances behave correctly.")
    
    # Create Props
    # Get game ID for Legacy
    games = database.get_all_games()
    legacy_game_id = [g['id'] for g in games if g['opponent'] == 'Legacy'][0]
    
    # Get player ID for Nik Gundrum
    players = database.get_all_players()
    nik_id = [p['id'] for p in players if p['name'] == 'Nik Gundrum'][0]
    
    database.create_prop(legacy_game_id, "points", nik_id, 15.5, -110, -110, "Nik Gundrum Over 15.5 Points")
    database.create_prop(legacy_game_id, "outcome", None, 0.5, 150, -110, "Deadly Cows Win Game 1")
    active_props = database.get_active_props()
    prop_points = [p for p in active_props if p['description'] == "Nik Gundrum Over 15.5 Points"][0]
    prop_outcome = [p for p in active_props if p['description'] == "Deadly Cows Win Game 1"][0]
    
    # Place Bets
    bet1_ok, m1 = database.place_bet(user['id'], prop_points['id'], 100, "over")
    assert bet1_ok is True, f"Failed to place bet 1: {m1}"
    
    bet2_ok, m2 = database.place_bet(user['id'], prop_outcome['id'], 200, "yes")
    assert bet2_ok is True, f"Failed to place bet 2: {m2}"
    
    # Insufficient balance check
    bet3_fail, m3 = database.place_bet(user['id'], prop_points['id'], 150000, "under")
    assert bet3_fail is False, "Expected bet to fail due to insufficient balance"
    print("✓ Placed valid bets and verified balance checks.")
    
    # Verify deducted balance
    updated_user = database.get_betting_user(user['id'])
    assert updated_user['balance'] == 99700, f"Expected balance of 99700, got {updated_user['balance']}"
    
    # Auto grade game
    # Nik scored 16 points (Over 15.5). The Cows lost (Outcome W/L is L -> Yes/No winner is 'no').
    database.auto_grade_game_props(legacy_game_id)
    
    # Verify outcomes and payouts
    # Payout 1 (Over): $100 wager at -110 -> win $91 + refund $100 = $191 payout.
    # Payout 2 (Yes): Lost -> $0 payout.
    # Ending balance: 700 + 191 = 891.
    final_user = database.get_betting_user(user['id'])
    assert final_user['balance'] == 99891, f"Expected final balance of 99891, got {final_user['balance']}"
    print("✓ Verified auto-grading results: Payouts match American odds formulas.")
    
    # Leaderboard ranking
    leaderboard = database.get_leaderboard()
    assert len(leaderboard) >= 1, f"Expected at least 1 user on leaderboard, got {len(leaderboard)}"
    matched_leaders = [l for l in leaderboard if l['nickname'] == test_nick]
    assert len(matched_leaders) == 1, f"Expected {test_nick} to be on leaderboard, got list of length {len(matched_leaders)}"
    assert matched_leaders[0]['balance'] == 99891, f"Expected balance 99891, got {matched_leaders[0]['balance']}"
    # --- Parlay Specific Integration Test ---
    print("\nRunning Parlay integration tests...")
    database.create_prop(legacy_game_id, "rebounds", nik_id, 5.5, 100, -110, "Nik Gundrum Over 5.5 Rebounds")
    database.create_prop(legacy_game_id, "assists", nik_id, 3.5, -120, 100, "Nik Gundrum Over 3.5 Assists")
    
    active_props2 = database.get_active_props()
    p_rebounds = [p for p in active_props2 if p['description'] == "Nik Gundrum Over 5.5 Rebounds"][0]
    p_assists = [p for p in active_props2 if p['description'] == "Nik Gundrum Over 3.5 Assists"][0]
    
    selections = [
        {'prop_id': p_rebounds['id'], 'selection': 'over'},
        {'prop_id': p_assists['id'], 'selection': 'under'}
    ]
    
    parlay_ok, parlay_msg = database.place_bets(user['id'], selections, is_parlay=True, parlay_wager=100)
    assert parlay_ok is True, f"Failed to place parlay: {parlay_msg}"
    
    user_after_parlay = database.get_betting_user(user['id'])
    assert user_after_parlay['balance'] == 99791, f"Expected balance of 99791, got {user_after_parlay['balance']}"
    print("✓ Successfully placed a 2-leg parlay and verified balance deduction.")
    
    database.grade_prop(p_rebounds['id'], 'over')
    database.grade_prop(p_assists['id'], 'under')
    
    user_final_parlay = database.get_betting_user(user['id'])
    assert user_final_parlay['balance'] == 100191, f"Expected final parlay balance of 100191, got {user_final_parlay['balance']}"
    print("✓ Successfully graded parlay and verified correct multiplied payout.")

    # --- New Feature Verification Tests (Toggling Pause, Editing, Categories, and Ordering) ---
    print("\nRunning New Features (Pause, Edit, Order, Category) tests...")
    
    # 1. Verify defaults and toggle pause
    assert database.is_betting_paused() is False, "Expected betting_paused to default to False"
    database.set_betting_paused(True)
    assert database.is_betting_paused() is True, "Expected betting_paused to be True after toggling"
    
    # 2. Placing a bet when paused should fail
    paused_bet_ok, paused_bet_msg = database.place_bets(user['id'], [{'prop_id': p_rebounds['id'], 'selection': 'over', 'wager_amount': 100}])
    assert paused_bet_ok is False, "Expected bet placement to fail when betting is paused"
    assert "paused" in paused_bet_msg.lower(), f"Expected message to mention paused, got: {paused_bet_msg}"
    print("✓ Successfully rejected bet placement when betting is paused.")
    
    # Resume betting for subsequent tests
    database.set_betting_paused(False)
    assert database.is_betting_paused() is False
    
    # 3. Create prop with custom category and display_order
    database.create_prop(legacy_game_id, "custom", None, 0.5, 110, -110, "Custom Team Prop A", category="team", display_order=-5)
    database.create_prop(legacy_game_id, "custom", None, 0.5, 110, -110, "Custom Team Prop B", category="team", display_order=10)
    
    active_props3 = database.get_active_props()
    # Confirm Team Prop A sorts before Team Prop B
    prop_a = [p for p in active_props3 if p['description'] == "Custom Team Prop A"][0]
    prop_b = [p for p in active_props3 if p['description'] == "Custom Team Prop B"][0]
    
    assert prop_a['category'] == 'team', "Expected category to be 'team'"
    assert prop_a['display_order'] == -5, "Expected display_order to be -5"
    assert prop_b['display_order'] == 10, "Expected display_order to be 10"
    
    # Assert prop_a is positioned earlier in active_props3 than prop_b
    idx_a = active_props3.index(prop_a)
    idx_b = active_props3.index(prop_b)
    assert idx_a < idx_b, "Expected prop_a with lower display_order to sort before prop_b"
    print("✓ Successfully verified custom prop categories and display order sorting.")
    
    # 4. Edit an existing prop line
    prop_to_edit = prop_b
    database.update_prop(
        prop_id=prop_to_edit['id'],
        game_id=prop_to_edit['game_id'],
        prop_type="custom",
        player_id=None,
        line_value=1.5,
        odds_over=120,
        odds_under=-120,
        description="Updated Prop B Description",
        category="player",
        display_order=20
    )
    
    edited_prop = database.get_prop(prop_to_edit['id'])
    assert edited_prop['description'] == "Updated Prop B Description", "Expected description to be updated"
    assert edited_prop['line_value'] == 1.5, "Expected line_value to be updated"
    assert edited_prop['odds_over'] == 120, "Expected odds_over to be updated"
    assert edited_prop['odds_under'] == -120, "Expected odds_under to be updated"
    assert edited_prop['category'] == 'player', "Expected category to be updated"
    assert edited_prop['display_order'] == 20, "Expected display_order to be updated"
    print("✓ Successfully verified get_prop and update_prop (prop editing).")

    print("\nALL DATABASE & BETTING TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_database()

