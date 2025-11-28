#!/usr/bin/env python3
"""
Check current status of all leagues to determine best import approach
"""
from data.database import get_db_manager
from data.league_manager import get_league_manager

def check_leagues_status():
    """Check current data status for all leagues."""
    db_manager = get_db_manager()
    league_manager = get_league_manager()
    
    print("🔍 CURRENT LEAGUE STATUS ANALYSIS")
    print("=" * 60)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all league data
        cursor.execute("""
            SELECT 
                l.id, l.name, l.country,
                COUNT(DISTINCT t.id) as teams,
                COUNT(DISTINCT m.id) as matches,
                COUNT(CASE WHEN m.goals_home IS NOT NULL THEN m.id END) as matches_with_goals,
                COUNT(CASE WHEN m.corners_home IS NOT NULL THEN m.id END) as matches_with_corners,
                COUNT(CASE WHEN m.status IN ('FT', 'Match Finished') THEN m.id END) as completed_matches
            FROM leagues l
            LEFT JOIN teams t ON l.id = t.league_id
            LEFT JOIN matches m ON l.id = m.league_id  
            WHERE l.active = 1
            GROUP BY l.id, l.name, l.country
            ORDER BY l.priority_order, l.name
        """)
        
        results = cursor.fetchall()
    
    print(f"📊 Found {len(results)} active leagues:")
    print()
    
    leagues_need_full_import = []
    leagues_need_statistics = []
    leagues_complete = []
    
    for row in results:
        league_id, name, country, teams, matches, goals, corners, completed = row
        
        print(f"🏆 {name} ({country}) - League ID: {league_id}")
        print(f"  Teams: {teams}")
        print(f"  Total Matches: {matches}")
        print(f"  Completed Matches: {completed}")
        print(f"  Matches with Goals: {goals}")
        print(f"  Matches with Corners: {corners}")
        
        # Determine what this league needs
        if teams == 0:
            status = "❌ NEEDS FULL IMPORT (no teams)"
            leagues_need_full_import.append(name)
        elif matches == 0:
            status = "❌ NEEDS FULL IMPORT (no matches)"
            leagues_need_full_import.append(name)
        elif completed > 0 and (goals == 0 or corners == 0):
            missing = []
            if goals == 0:
                missing.append("goals")
            if corners == 0:
                missing.append("corners")
            status = f"⚠️ NEEDS STATISTICS ({', '.join(missing)})"
            leagues_need_statistics.append(name)
        elif completed > 0 and goals > 0 and corners > 0:
            goal_coverage = (goals / completed) * 100
            corner_coverage = (corners / completed) * 100
            status = f"✅ COMPLETE ({goal_coverage:.0f}% goals, {corner_coverage:.0f}% corners)"
            leagues_complete.append(name)
        else:
            status = "⏳ NO COMPLETED MATCHES YET"
        
        print(f"  Status: {status}")
        print()
    
    # Summary
    print("📋 SUMMARY:")
    print("=" * 40)
    print(f"✅ Complete leagues: {len(leagues_complete)}")
    print(f"⚠️ Need statistics only: {len(leagues_need_statistics)}")
    print(f"❌ Need full import: {len(leagues_need_full_import)}")
    print()
    
    if leagues_need_full_import:
        print("🚨 Leagues needing FULL IMPORT:")
        for league in leagues_need_full_import:
            print(f"  - {league}")
        print()
    
    if leagues_need_statistics:
        print("📊 Leagues needing STATISTICS ONLY:")
        for league in leagues_need_statistics:
            print(f"  - {league}")
        print()
    
    if leagues_complete:
        print("🎉 Leagues already COMPLETE:")
        for league in leagues_complete:
            print(f"  - {league}")
        print()
    
    # Recommendation
    print("💡 RECOMMENDATION:")
    if len(leagues_need_full_import) > len(leagues_need_statistics):
        print("Use Option A: import_all_europe_comprehensive.py")
        print("Reason: Most leagues need complete import (teams + matches + statistics)")
    elif len(leagues_need_statistics) > 0:
        print("Use Option C: complete_mls_statistics.py + corner import")
        print("Reason: Most leagues have teams/matches but need statistics")
    else:
        print("All leagues appear complete!")
    
if __name__ == "__main__":
    check_leagues_status()

