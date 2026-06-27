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
    assert len(players) == 9, f"Expected 9 players, got {len(players)}"
    print("✓ Successfully loaded 9 players.")
    
    # 4. Test games retrieval
    games = database.get_all_games()
    assert len(games) == 1, f"Expected 1 game, got {len(games)}"
    assert games[0]['opponent'] == 'Legacy', f"Expected opponent Legacy, got {games[0]['opponent']}"
    print("✓ Successfully loaded 1 game (Legacy).")
    
    # 5. Check Legacy Game Stats & Ratings
    legacy_game = games[0]
    stats, moo_vp, lip = database.get_game_stats(legacy_game['id'])
    
    assert len(stats) == 8, f"Expected 8 stats rows, got {len(stats)}"
    print("✓ Successfully fetched stats for 8 active players.")

    # Find Nik Gundrum
    nik = [s for s in stats if s['name'] == 'Nik Gundrum'][0]
    assert nik['rating'] == 98, f"Nik rating expected 98, got {nik['rating']}"
    assert nik['fg'] == 7, f"Nik fg expected 7, got {nik['fg']}"
    assert nik['fga'] == 17, f"Nik fga expected 17, got {nik['fga']}"
    assert nik['notes'] != "", "Nik notes should not be empty"
    print("✓ Nik Gundrum stats, field goals (7/17), and computed rating (98) are correct.")

    # Find Stephen Kruse
    stephen = [s for s in stats if s['name'] == "Stephen Kruse"][0]
    assert stephen['rating'] == 74, f"Stephen rating expected 74, got {stephen['rating']}"
    assert stephen['fg'] == 4, f"Stephen fg expected 4, got {stephen['fg']}"
    assert stephen['fga'] == 9, f"Stephen fga expected 9, got {stephen['fga']}"
    print("✓ Stephen Kruse stats, field goals (4/9), and computed rating (74) are correct.")
    
    # Verify awards: Moo-VP is Nik Gundrum (highest rating: 98) and LIP is Patrick Rossiello (lowest rating: 69)
    assert moo_vp['name'] == 'Nik Gundrum', f"Expected Moo-VP Nik Gundrum, got {moo_vp['name']}"
    assert lip['name'] == "Patrick Rossiello", f"Expected LIP Patrick Rossiello, got {lip['name']}"
    assert lip['rating'] == 69, f"Expected LIP rating 69, got {lip['rating']}"
    print(f"✓ Game awards: Moo-VP = {moo_vp['name']} ({moo_vp['rating']}), LIP = {lip['name']} ({lip['rating']}).")
    
    # 6. Test Averages and Totals
    averages = database.get_player_averages()
    assert len(averages) == 9
    # Check that Nik has an average FG/FGA
    nik_avg = [a for a in averages if a['name'] == 'Nik Gundrum'][0]
    assert nik_avg['avg_fg'] == 7.0
    assert nik_avg['avg_fga'] == 17.0
    print("✓ Player averages retrieved successfully.")
    
    totals = database.get_player_totals()
    assert len(totals) == 9
    print("✓ Player totals retrieved successfully.")
    
    print("\nALL DATABASE TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_database()
