#!/usr/bin/env python3
"""
Debug La Liga matches - check what we actually have
"""
from data.database import get_db_manager

def debug_laliga_matches():
    """Debug La Liga's current match data in detail."""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        print("🇪🇸 La Liga (League ID: 2) DETAILED DEBUG:")
        print("=" * 50)
        
        # Check match statuses
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM matches 
            WHERE league_id = 2 
            GROUP BY status 
            ORDER BY COUNT(*) DESC
        """)
        statuses = cursor.fetchall()
        
        print("\n📊 Match Status Distribution:")
        for status, count in statuses:
            print(f"  {status}: {count} matches")
        
        # Check seasons
        cursor.execute("""
            SELECT season, COUNT(*) 
            FROM matches 
            WHERE league_id = 2 
            GROUP BY season 
            ORDER BY season DESC
        """)
        seasons = cursor.fetchall()
        
        print("\n📅 Seasons in Database:")
        for season, count in seasons:
            print(f"  Season {season}: {count} matches")
        
        # Check recent matches
        cursor.execute("""
            SELECT match_date, home_team_name, away_team_name, status, goals_home, goals_away
            FROM matches 
            WHERE league_id = 2 
            ORDER BY match_date DESC 
            LIMIT 10
        """)
        recent_matches = cursor.fetchall()
        
        print("\n📅 10 Most Recent La Liga Matches:")
        for match in recent_matches:
            date, home, away, status, h_goals, a_goals = match
            goals = f"{h_goals}-{a_goals}" if h_goals is not None and a_goals is not None else "No goals"
            print(f"  {date}: {home} vs {away} ({status}) [{goals}]")
        
        # Check what season should be used for current date
        from datetime import datetime
        current_date = datetime.now()
        print(f"\n🗓️ Current Date: {current_date.strftime('%Y-%m-%d')}")
        print(f"🤔 La Liga 2024/25 season typically runs Aug 2024 - May 2025")
        print(f"🤔 La Liga 2025/26 season would start Aug 2025")
        
        # Check if we should be using season 2024 instead of 2025
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matches 
            WHERE league_id = 2 AND season = 2024 AND status = 'FT'
        """)
        completed_2024 = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matches 
            WHERE league_id = 2 AND season = 2025 AND status = 'FT'
        """)
        completed_2025 = cursor.fetchone()[0]
        
        print(f"\n🔍 Season Analysis:")
        print(f"  2024 season completed matches: {completed_2024}")
        print(f"  2025 season completed matches: {completed_2025}")
        
        if completed_2024 > completed_2025:
            print(f"💡 INSIGHT: Season 2024 has more completed matches!")
            print(f"💡 We should probably be importing 2024 season data!")

if __name__ == "__main__":
    debug_laliga_matches()
