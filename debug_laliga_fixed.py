#!/usr/bin/env python3
"""
Debug La Liga matches - FIXED VERSION
Check actual database schema and use correct column names
"""
from data.database import get_db_manager

def debug_laliga_fixed():
    """Debug La Liga's current match data with correct column names."""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        print("🇪🇸 La Liga (League ID: 2) FIXED DETAILED DEBUG:")
        print("=" * 50)
        
        # First, check the actual matches table schema
        cursor.execute("PRAGMA table_info(matches)")
        columns = cursor.fetchall()
        
        print("\n🔧 Actual Matches Table Schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check match statuses with correct status names
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM matches 
            WHERE league_id = 2 
            GROUP BY status 
            ORDER BY COUNT(*) DESC
        """)
        statuses = cursor.fetchall()
        
        print("\n📊 Match Status Distribution:")
        total_matches = sum(count for _, count in statuses)
        for status, count in statuses:
            percentage = (count / total_matches) * 100
            print(f"  '{status}': {count} matches ({percentage:.1f}%)")
        
        # Count finished matches using correct status
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matches 
            WHERE league_id = 2 AND status = 'Match Finished'
        """)
        finished_matches = cursor.fetchone()[0]
        
        print(f"\n✅ FIXED: La Liga finished matches: {finished_matches}")
        
        # Check goals in finished matches
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matches 
            WHERE league_id = 2 AND status = 'Match Finished' AND goals_home IS NOT NULL
        """)
        matches_with_goals = cursor.fetchone()[0]
        
        print(f"⚽ Finished matches with goals: {matches_with_goals}")
        
        # Check corners in finished matches  
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matches 
            WHERE league_id = 2 AND status = 'Match Finished' AND corners_home IS NOT NULL
        """)
        matches_with_corners = cursor.fetchone()[0]
        
        print(f"🏴 Finished matches with corners: {matches_with_corners}")
        
        # Show recent matches using correct column names (probably home_team_id/away_team_id)
        cursor.execute("""
            SELECT id, match_date, home_team_id, away_team_id, status, goals_home, goals_away, corners_home, corners_away
            FROM matches 
            WHERE league_id = 2 AND status = 'Match Finished'
            ORDER BY match_date DESC 
            LIMIT 5
        """)
        recent_finished = cursor.fetchall()
        
        print(f"\n📅 5 Most Recent FINISHED La Liga Matches:")
        for match in recent_finished:
            match_id, date, home_id, away_id, status, h_goals, a_goals, h_corners, a_corners = match
            goals = f"{h_goals}-{a_goals}" if h_goals is not None and a_goals is not None else "No goals"
            corners = f"{h_corners}-{a_corners}" if h_corners is not None and a_corners is not None else "No corners"
            print(f"  {date}: Team{home_id} vs Team{away_id} [{goals}] [{corners}]")
        
        # Calculate coverage percentages
        if finished_matches > 0:
            goal_coverage = (matches_with_goals / finished_matches) * 100
            corner_coverage = (matches_with_corners / finished_matches) * 100
            
            print(f"\n📈 La Liga Statistics Coverage:")
            print(f"  Goal coverage: {goal_coverage:.1f}% ({matches_with_goals}/{finished_matches})")
            print(f"  Corner coverage: {corner_coverage:.1f}% ({matches_with_corners}/{finished_matches})")
            
            if goal_coverage < 100:
                print(f"🎯 NEED: Import goals for {finished_matches - matches_with_goals} matches")
            if corner_coverage < 100:
                print(f"🎯 NEED: Import corners for {finished_matches - matches_with_corners} matches")

if __name__ == "__main__":
    debug_laliga_fixed()
