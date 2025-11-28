#!/usr/bin/env python3
"""
Import cards data for TARGET LEAGUES ONLY:
- Spain: La Liga
- Italy: Serie A
- England: Premier League + Championship
- Germany: Bundesliga
- Scotland: Premiership
- USA: MLS
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

# Exact leagues requested by user (verified IDs from database)
TARGET_LEAGUES = [
    {'id': 2, 'name': 'La Liga', 'country': 'Spain', 'api_id': 140},
    {'id': 4, 'name': 'Serie A', 'country': 'Italy', 'api_id': 135},
    {'id': 747, 'name': 'Premier League', 'country': 'England', 'api_id': 39},
    {'id': 748, 'name': 'Championship', 'country': 'England', 'api_id': 40},
    {'id': 754, 'name': 'Bundesliga', 'country': 'Germany', 'api_id': 78},
    {'id': 1267, 'name': 'Scottish Premiership', 'country': 'Scotland', 'api_id': 179},
    {'id': 1279, 'name': 'Major League Soccer', 'country': 'United States', 'api_id': 253}
]

def import_cards_for_target_leagues():
    """Import cards data ONLY for specified target leagues."""
    print("\n" + "="*70)
    print("IMPORTING CARDS DATA - TARGET LEAGUES ONLY")
    print("="*70)
    print("\nTarget Leagues:")
    for league in TARGET_LEAGUES:
        print(f"  - {league['country']:15s} | {league['name']}")
    print("="*70 + "\n")
    
    db_manager = get_db_manager()
    importer = DataImporter()
    
    total_updated = 0
    successful_leagues = 0
    failed_leagues = []
    
    for idx, league in enumerate(TARGET_LEAGUES, 1):
        print(f"\n[{idx}/{len(TARGET_LEAGUES)}] Processing: {league['name']} ({league['country']})")
        print("-" * 70)
        
        try:
            # Import cards for this league
            updated_count = importer.import_match_cards(
                league_id=league['id'],
                season=2025,
                limit=None  # Import all available matches
            )
            
            if updated_count > 0:
                print(f"[SUCCESS] Updated {updated_count} matches with cards data")
                total_updated += updated_count
                successful_leagues += 1
            else:
                print(f"[WARNING] No matches updated (might already have data or no FT matches)")
                # Not counting as failure if no updates (might already have data)
            
        except Exception as e:
            print(f"[ERROR] Failed to import cards: {e}")
            failed_leagues.append(league['name'])
            logger.error(f"Error importing {league['name']}: {e}", exc_info=True)
    
    # Final summary
    print(f"\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"Target leagues: {len(TARGET_LEAGUES)}")
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
    try:
        success = import_cards_for_target_leagues()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        logger.error("Fatal error during import", exc_info=True)
        sys.exit(1)

