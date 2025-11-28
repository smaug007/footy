#!/usr/bin/env python3
"""
Import Cards Statistics for Bundesliga (German League) - Season 2025
=====================================================================
Imports yellow and red cards data for all completed Bundesliga matches.
Stores data in matches table (yellow_cards_home, yellow_cards_away, red_cards_home, red_cards_away, total_cards)
"""
import logging
import time
from datetime import datetime
from data.data_importer import DataImporter
from data.league_manager import get_league_manager
from data.api_client import get_api_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'bundesliga_cards_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bundesliga configuration
BUNDESLIGA_CONFIG = {
    'name': 'Bundesliga',
    'country': 'Germany',
    'api_league_id': 78,
    'season': 2025
}

def import_bundesliga_cards():
    """Import cards statistics for Bundesliga 2025 season."""
    try:
        logger.info("="*70)
        logger.info("BUNDESLIGA CARDS STATISTICS IMPORT - Season 2025")
        logger.info("="*70)
        logger.info(f"League: {BUNDESLIGA_CONFIG['name']}")
        logger.info(f"Country: {BUNDESLIGA_CONFIG['country']}")
        logger.info(f"API League ID: {BUNDESLIGA_CONFIG['api_league_id']}")
        logger.info(f"Season: {BUNDESLIGA_CONFIG['season']}")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Initialize services
        importer = DataImporter()
        league_manager = get_league_manager()
        api_client = get_api_client()
        
        # Get Bundesliga league ID from database
        bundesliga = league_manager.get_league_by_api_id(BUNDESLIGA_CONFIG['api_league_id'])
        
        if not bundesliga:
            logger.error(f"Bundesliga (API ID: {BUNDESLIGA_CONFIG['api_league_id']}) not found in database!")
            logger.info("Make sure Bundesliga teams and matches are imported first")
            return False
        
        logger.info(f"Found Bundesliga in database - League ID: {bundesliga.id}")
        logger.info("")
        
        # Check API status
        logger.info("Checking API status...")
        rate_limit_status = api_client.get_rate_limit_status()
        logger.info(f"API Calls Today: {rate_limit_status['daily_calls']}/{rate_limit_status['daily_limit']}")
        logger.info(f"API Calls This Minute: {rate_limit_status['minute_calls']}/{rate_limit_status['minute_limit']}")
        logger.info("")
        
        # Import cards statistics
        logger.info("Starting cards data import...")
        logger.info("-"*70)
        
        start_time = time.time()
        cards_imported = importer.import_match_cards(
            league_id=bundesliga.id,
            season=BUNDESLIGA_CONFIG['season'],
            limit=None  # Import all available matches
        )
        elapsed_time = time.time() - start_time
        
        logger.info("-"*70)
        logger.info("")
        
        # Final summary
        logger.info("="*70)
        logger.info("IMPORT COMPLETED")
        logger.info("="*70)
        logger.info(f"Matches Updated with Cards: {cards_imported}")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"API Calls Used: ~{cards_imported} (1 per match)")
        logger.info("")
        
        # Check final API status
        final_rate_limit = api_client.get_rate_limit_status()
        logger.info(f"Final API Calls Today: {final_rate_limit['daily_calls']}/{final_rate_limit['daily_limit']}")
        logger.info(f"Remaining Daily Calls: {final_rate_limit['daily_limit'] - final_rate_limit['daily_calls']}")
        logger.info("")
        
        if cards_imported > 0:
            logger.info("SUCCESS! Bundesliga cards statistics imported successfully")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Run cards analyzer to calculate team averages")
            logger.info("2. Test cards predictions for Bundesliga matches")
            logger.info("3. Verify data quality and accuracy")
            return True
        else:
            logger.warning("WARNING: No cards data was imported")
            logger.info("Possible reasons:")
            logger.info("- All matches already have cards data")
            logger.info("- No completed matches found")
            logger.info("- API returned no cards statistics")
            return False
        
    except Exception as e:
        logger.error(f"FATAL ERROR during import: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_import():
    """Verify that cards data was imported correctly."""
    try:
        logger.info("")
        logger.info("="*70)
        logger.info("VERIFYING IMPORT")
        logger.info("="*70)
        
        from data.database import get_db_manager
        db_manager = get_db_manager()
        
        with db_manager.get_connection() as conn:
            # Get Bundesliga league ID
            cursor = conn.execute("""
                SELECT id FROM leagues WHERE api_league_id = ?
            """, (BUNDESLIGA_CONFIG['api_league_id'],))
            league_row = cursor.fetchone()
            
            if not league_row:
                logger.error("Bundesliga not found in database")
                return False
            
            league_id = league_row[0]
            
            # Count matches with cards data
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_matches,
                    COUNT(yellow_cards_home) as matches_with_cards,
                    AVG(total_cards) as avg_cards,
                    MIN(total_cards) as min_cards,
                    MAX(total_cards) as max_cards
                FROM matches
                WHERE league_id = ? AND season = ? AND status = 'FT'
            """, (league_id, BUNDESLIGA_CONFIG['season']))
            
            stats = cursor.fetchone()
            
            logger.info(f"Total Completed Matches: {stats[0]}")
            logger.info(f"Matches with Cards Data: {stats[1]}")
            logger.info(f"Average Cards per Match: {stats[2]:.2f}" if stats[2] else "Average Cards per Match: N/A")
            logger.info(f"Min Cards in a Match: {stats[3]}" if stats[3] is not None else "Min Cards in a Match: N/A")
            logger.info(f"Max Cards in a Match: {stats[4]}" if stats[4] is not None else "Max Cards in a Match: N/A")
            logger.info("")
            
            # Sample some matches with cards
            cursor = conn.execute("""
                SELECT 
                    m.id,
                    ht.name as home_team,
                    at.name as away_team,
                    m.yellow_cards_home,
                    m.yellow_cards_away,
                    m.red_cards_home,
                    m.red_cards_away,
                    m.total_cards,
                    m.match_date
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.league_id = ? AND m.season = ? AND m.yellow_cards_home IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 5
            """, (league_id, BUNDESLIGA_CONFIG['season']))
            
            sample_matches = cursor.fetchall()
            
            if sample_matches:
                logger.info("Sample Matches with Cards Data:")
                logger.info("-"*70)
                for match in sample_matches:
                    logger.info(f"{match[1]} vs {match[2]}")
                    logger.info(f"  Yellow: {match[3]}-{match[4]} | Red: {match[5]}-{match[6]} | Total: {match[7]}")
                    logger.info(f"  Date: {match[8]}")
                    logger.info("")
            
            logger.info("="*70)
            logger.info("VERIFICATION COMPLETE")
            logger.info("="*70)
            
            if stats[1] > 0:
                logger.info("Data import verified successfully!")
                return True
            else:
                logger.warning("No cards data found after import")
                return False
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    print("="*70)
    print(" "*15 + "BUNDESLIGA CARDS IMPORT SCRIPT")
    print("="*70)
    print()
    
    # Run import
    success = import_bundesliga_cards()
    
    # Verify import
    if success:
        verify_import()
    
    print()
    print("="*70)
    if success:
        print("IMPORT COMPLETED SUCCESSFULLY")
    else:
        print("IMPORT FAILED - Check logs for details")
    print("="*70)
    print()

