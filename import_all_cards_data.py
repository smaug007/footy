#!/usr/bin/env python3
"""
Import historical cards data for all leagues with existing matches.
"""
import sys
sys.path.insert(0, '.')

from data.data_importer import DataImporter
from data.database import get_db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_all_cards():
    """Import cards data for all leagues that have matches."""
    print("\n" + "="*70)
    print("IMPORTING CARDS DATA FOR ALL LEAGUES")
    print("="*70 + "\n")
    
    db_manager = get_db_manager()
    importer = DataImporter()
    
    # Get all leagues that have matches in 2025
    print("[STEP 1] Finding leagues with matches...")
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT l.id, l.name, l.api_league_id as api_id, COUNT(m.id) as match_count
            FROM leagues l
            JOIN teams t ON t.league_id = l.id
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE m.season = 2025
            GROUP BY l.id, l.name, l.api_league_id
            ORDER BY match_count DESC
        """)
        leagues = [dict(row) for row in cursor.fetchall()]
    
    if not leagues:
        print("[ERROR] No leagues with matches found!")
        return False
    
    print(f"[OK] Found {len(leagues)} leagues with matches:\n")
    for league in leagues:
        print(f"  - {league['name']} (API ID: {league['api_id']}, {league['match_count']} matches)")
    
    print(f"\n{'='*70}")
    print("STARTING CARDS DATA IMPORT")
    print(f"{'='*70}\n")
    
    total_updated = 0
    successful_leagues = 0
    failed_leagues = []
    
    for idx, league in enumerate(leagues, 1):
        print(f"\n[{idx}/{len(leagues)}] Processing: {league['name']}")
        print("-" * 70)
        
        try:
            # Import cards for this league
            updated_count = importer.import_match_cards(
                league_id=league['id'],
                season=2025,
                limit=None  # Import all matches
            )
            
            if updated_count > 0:
                print(f"[OK] Updated {updated_count} matches with cards data")
                total_updated += updated_count
                successful_leagues += 1
            else:
                print(f"[WARNING] No matches updated (might be missing API data)")
                failed_leagues.append(league['name'])
            
        except Exception as e:
            print(f"[ERROR] Failed to import cards for {league['name']}: {e}")
            failed_leagues.append(league['name'])
    
    # Final summary
    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"Total leagues processed: {len(leagues)}")
    print(f"Successful: {successful_leagues}")
    print(f"Failed: {len(failed_leagues)}")
    print(f"Total matches updated with cards: {total_updated}")
    
    if failed_leagues:
        print(f"\nFailed leagues:")
        for league_name in failed_leagues:
            print(f"  - {league_name}")
    
    print(f"{'='*70}\n")
    
    return successful_leagues > 0

if __name__ == "__main__":
    success = import_all_cards()
    sys.exit(0 if success else 1)

