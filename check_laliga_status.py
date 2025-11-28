#!/usr/bin/env python3
"""
Check La Liga's current data status
"""
from data.database import get_db_manager

def check_laliga_status():
    """Check La Liga's current data status."""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Teams
        cursor.execute("SELECT COUNT(*) FROM teams WHERE league_id = 2")
        teams = cursor.fetchone()[0]
        
        # Total matches
        cursor.execute("SELECT COUNT(*) FROM matches WHERE league_id = 2")
        matches = cursor.fetchone()[0]
        
        # Completed matches
        cursor.execute("SELECT COUNT(*) FROM matches WHERE league_id = 2 AND status = 'FT'")
        completed = cursor.fetchone()[0]
        
        # Matches with goals
        cursor.execute("SELECT COUNT(*) FROM matches WHERE league_id = 2 AND goals_home IS NOT NULL")
        goals = cursor.fetchone()[0]
        
        # Matches with corners
        cursor.execute("SELECT COUNT(*) FROM matches WHERE league_id = 2 AND corners_home IS NOT NULL")
        corners = cursor.fetchone()[0]
    
    print("🇪🇸 La Liga (League ID: 2) Current Status:")
    print("=" * 40)
    print(f"  Teams: {teams}")
    print(f"  Total Matches: {matches}")
    print(f"  Completed Matches: {completed}")
    print(f"  Matches with Goals: {goals}")
    print(f"  Matches with Corners: {corners}")
    
    if teams == 0:
        print("\n❌ NO TEAMS - Need complete import!")
    elif matches == 0:
        print("\n❌ NO MATCHES - Need match import!")
    elif completed > 0 and goals == 0:
        print("\n⚠️ NO GOALS - Need goal statistics import!")
    elif completed > 0 and corners == 0:
        print("\n⚠️ NO CORNERS - Need corner statistics import!")
    else:
        coverage_goals = (goals / completed) * 100 if completed > 0 else 0
        coverage_corners = (corners / completed) * 100 if completed > 0 else 0
        print(f"\n📊 Coverage:")
        print(f"  Goals: {coverage_goals:.1f}%")
        print(f"  Corners: {coverage_corners:.1f}%")

if __name__ == "__main__":
    check_laliga_status()
