import database

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
    assert len(games) == 2, f"Expected 2 games, got {len(games)}"
    assert games[1]['opponent'] == 'Legacy', f"Expected opponent Legacy, got {games[1]['opponent']}"
    assert games[0]['opponent'] == "Daddy's Home", f"Expected opponent Daddy's Home, got {games[0]['opponent']}"
    print("✓ Successfully loaded 2 games (Daddy's Home, Legacy).")
    
    # 5. Check Legacy Game Stats & Ratings
    legacy_game = games[1]
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
    
    print("\nALL DATABASE TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_database()
