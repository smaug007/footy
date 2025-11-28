#!/usr/bin/env python3
"""
Test La Liga Corner Statistics Import
Complete the La Liga test by importing corner statistics
"""
import logging
import time
from data.api_client import get_api_client
from data.database import get_db_manager
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_laliga_corners():
    """Import corner statistics for La Liga matches."""
    try:
        logger.info("🚀 IMPORTING LA LIGA CORNER STATISTICS")
        logger.info("🏴 Target: Import corners for ALL 40 completed matches")
        
        db_manager = get_db_manager()
        api_client = get_api_client()
        league_manager = get_league_manager()
        
        # Get La Liga config
        laliga_config = league_manager.get_league_by_id(2)  # La Liga is league_id=2
        if not laliga_config:
            logger.error("❌ La Liga config not found!")
            return False
        
        logger.info(f"🇪🇸 League: {laliga_config.name}, API ID: {laliga_config.api_league_id}")
        
        # Get matches needing corner statistics using our adaptive method
        matches_needing_corners = db_manager.get_matches_needing_corner_stats(
            league_id=2, 
            season=2025, 
            limit=50
        )
        
        if not matches_needing_corners:
            logger.info("✅ All La Liga matches already have corner statistics!")
            return True
        
        logger.info(f"🎯 Found {len(matches_needing_corners)} matches needing corner stats")
        
        total_imported = 0
        total_api_calls = 0
        
        for i, match_data in enumerate(matches_needing_corners):
            try:
                match_id = match_data['id']
                api_fixture_id = match_data['api_fixture_id']
                home_team = match_data['home_team_name']
                away_team = match_data['away_team_name']
                
                # Progress indicator
                progress_pct = ((i + 1) / len(matches_needing_corners)) * 100
                logger.info(f"🏴 [{i+1}/{len(matches_needing_corners)}] ({progress_pct:.1f}%) {home_team} vs {away_team}")
                
                # Get fixture statistics (corners are in statistics endpoint)
                stats_data = api_client.get_fixture_statistics(api_fixture_id)
                total_api_calls += 1
                
                if stats_data and 'response' in stats_data:
                    # Extract corner data
                    home_corners = None
                    away_corners = None
                    
                    for team_stats in stats_data['response']:
                        for stat in team_stats.get('statistics', []):
                            if stat.get('type') == 'Corner Kicks':
                                corners_value = stat.get('value')
                                if corners_value is not None and str(corners_value).isdigit():
                                    corners_int = int(corners_value)
                                    
                                    # Determine home/away based on team data
                                    team_name = team_stats['team']['name']
                                    if team_name == home_team:
                                        home_corners = corners_int
                                    elif team_name == away_team:
                                        away_corners = corners_int
                    
                    # Update database if we have corner data
                    if home_corners is not None and away_corners is not None:
                        if db_manager.update_match_corners(match_id, home_corners, away_corners):
                            total_imported += 1
                            logger.info(f"    ✅ Corners: {home_corners}-{away_corners}")
                        else:
                            logger.warning(f"    ⚠️ Database update failed for match {match_id}")
                    else:
                        logger.warning(f"    ⚠️ No corner data found in API response")
                else:
                    logger.warning(f"    ❌ No statistics data returned from API")
                
                # Rate limiting - pause every 10 calls
                if (i + 1) % 10 == 0:
                    remaining = len(matches_needing_corners) - (i + 1)
                    if remaining > 0:
                        logger.info(f"⏳ Batch complete. {remaining} matches remaining. Waiting 3 seconds...")
                        time.sleep(3)
                        
            except Exception as e:
                logger.error(f"    ❌ Error processing match {match_id}: {e}")
                continue
        
        # Final verification
        logger.info(f"\n🏆 LA LIGA CORNER IMPORT RESULTS:")
        logger.info("=" * 50)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = 2 AND season = 2025 AND corners_home IS NOT NULL
            """)
            final_corners_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = 2 AND season = 2025 
                AND (status = 'FT' OR status = 'Match Finished')
            """)
            completed_count = cursor.fetchone()[0]
        
        corner_coverage = (final_corners_count / completed_count) * 100 if completed_count > 0 else 0
        
        logger.info(f"✅ Corner Import Summary:")
        logger.info(f"  Matches processed: {len(matches_needing_corners)}")
        logger.info(f"  Successfully imported: {total_imported}")
        logger.info(f"  API calls made: {total_api_calls}")
        logger.info(f"  Final corner coverage: {corner_coverage:.1f}% ({final_corners_count}/{completed_count})")
        
        if corner_coverage >= 95:
            logger.info("🎉 PERFECT! La Liga corner coverage is outstanding!")
        elif corner_coverage >= 80:
            logger.info("✅ EXCELLENT! La Liga corner coverage is sufficient!")
        else:
            logger.warning("⚠️ La Liga corner coverage needs improvement")
        
        return corner_coverage >= 80
        
    except Exception as e:
        logger.error(f"💥 La Liga corner import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_laliga_corners()
    if success:
        logger.info("🏆 LA LIGA CORNER IMPORT COMPLETED SUCCESSFULLY!")
        logger.info("🎯 La Liga now has BOTH goals AND corners!")
    else:
        logger.error("🚨 La Liga corner import needs attention")
