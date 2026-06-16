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
    assert len(games) == 3, f"Expected 3 games, got {len(games)}"
    print("✓ Successfully loaded 3 games.")
    
    # 5. Check Game 1 Stats & MVI
    # Find Game 1 (vs Bacon Blazers)
    game1 = [g for g in games if g['opponent'] == 'Bacon Blazers'][0]
    stats, moo_vp, lip = database.get_game_stats(game1['id'])
    
    # Find John Andreou
    john = [s for s in stats if s['name'] == 'John Andreou'][0]
    # MVI calculation check:
    # MVI = 28 + 1.2*10 + 1.5*8 + 2.0*2 + 2.0*1 - 1.5*3 - 1.0*2 - 3.0*0 - 5.0*0
    #     = 28 + 12 + 12 + 4 + 2 - 4.5 - 2 = 51.5
    assert john['mvi'] == 51.5, f"John MVI expected 51.5, got {john['mvi']}"
    print("✓ John Andreou Game 1 MVI calculation is correct (51.5).")

    # Find Stephen Kruse
    stephen = [s for s in stats if s['name'] == "Stephen Kruse"][0]
    # MVI calculation check:
    # MVI = 10 + 1.2*15 + 1.5*1 + 2.0*0 + 2.0*4 - 1.5*1 - 1.0*4 - 3.0*2 - 5.0*2
    #     = 10 + 18 + 1.5 + 8 - 1.5 - 4 - 6 - 10 = 16.0
    assert stephen['mvi'] == 16.0, f"Stephen MVI expected 16.0, got {stephen['mvi']}"
    print("✓ Stephen Kruse Game 1 MVI calculation is correct (16.0).")
    
    # Verify LIP is Noah Shulman (MVI -2.6) and Moo-VP is John Andreou (MVI 51.5)
    assert moo_vp['name'] == 'John Andreou', f"Expected Moo-VP John Andreou, got {moo_vp['name']}"
    assert lip['name'] == "Noah Shulman", f"Expected LIP Noah Shulman, got {lip['name']}"
    print("✓ Game 1 awards: Moo-VP = John Andreou, LIP = Noah Shulman.")
    
    # 6. Test Averages
    averages = database.get_player_averages()
    assert len(averages) == 9
    print("✓ Player averages retrieved successfully.")
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_database()
