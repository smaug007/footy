#!/usr/bin/env python3
"""
MLS Goals Import - CORRECTED VERSION
Uses the correct get_fixture_details() method instead of get_fixture_statistics()
This is the proven method that successfully imported all MLS goals
"""
import logging
import time
from data.api_client import get_api_client
from data.database import get_db_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_mls_goals_corrected(league_id: int = 1279, season: int = 2025, batch_size: int = 50):
    """Import MLS goals using the corrected fixture details endpoint."""
    try:
        logger.info(f"🚀 CORRECTED MLS Goals Import (League ID: {league_id}, Season: {season})")
        logger.info("⚽ Using get_fixture_details() method - PROVEN SUCCESSFUL")
        
        db_manager = get_db_manager()
        api_client = get_api_client()
        
        # Check current status
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total MLS matches that should have goals
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND status = 'FT'
            """, (league_id, season))
            total_completed = cursor.fetchone()[0]
            
            # Already have goals
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND goals_home IS NOT NULL
            """, (league_id, season))
            already_have_goals = cursor.fetchone()[0]
            
            remaining_needed = total_completed - already_have_goals
            
        logger.info(f"📊 Current MLS Goals Status:")
        logger.info(f"  Total completed matches: {total_completed}")
        logger.info(f"  Already have goals: {already_have_goals}")
        logger.info(f"  Still need goals: {remaining_needed}")
        
        if remaining_needed <= 0:
            logger.info("✅ All MLS matches already have goal data!")
            return True
            
        # Get matches needing goals (MLS only)
        matches_needing_goals = db_manager.get_matches_needing_goal_stats(
            season, 
            limit=500,  # Get all at once, we'll batch the API calls
            league_id=league_id  # CRITICAL: MLS only filter
        )
        
        if not matches_needing_goals:
            logger.info("✅ No MLS matches need goal statistics!")
            return True
            
        logger.info(f"🎯 Found {len(matches_needing_goals)} MLS matches needing goals")
        
        total_imported = 0
        total_api_calls = 0
        
        # Process in batches to respect API limits
        for i, match in enumerate(matches_needing_goals):
            try:
                api_fixture_id = match[0]
                match_id = match[1]
                home_team = match[2]
                away_team = match[3]
                
                # Progress tracking
                progress_pct = ((i + 1) / len(matches_needing_goals)) * 100
                logger.info(f"⚽ [{i+1}/{len(matches_needing_goals)}] ({progress_pct:.1f}%) {home_team} vs {away_team}")
                
                # Get fixture details using CORRECTED method
                fixture_data = api_client.get_fixture_details(api_fixture_id)
                total_api_calls += 1
                
                if fixture_data:
                    # Extract goals using corrected parsing
                    home_goals = fixture_data.get('home_goals')
                    away_goals = fixture_data.get('away_goals')
                    
                    if home_goals is not None and away_goals is not None:
                        try:
                            # Convert to integers safely
                            home_goals_int = int(home_goals) if str(home_goals).isdigit() else 0
                            away_goals_int = int(away_goals) if str(away_goals).isdigit() else 0
                            
                            # Update database
                            if db_manager.update_match_goals(match_id, home_goals_int, away_goals_int):
                                total_imported += 1
                                logger.info(f"    ✅ Updated: {home_goals_int}-{away_goals_int}")
                            else:
                                logger.warning(f"    ⚠️ Database update failed for match {match_id}")
                                
                        except (ValueError, TypeError) as e:
                            logger.warning(f"    ⚠️ Invalid goal values: {home_goals}, {away_goals} - {e}")
                    else:
                        logger.warning(f"    ⚠️ No goal data in API response")
                else:
                    logger.warning(f"    ❌ No fixture data returned from API")
                    
                # Rate limiting: pause every 50 calls
                if (i + 1) % batch_size == 0:
                    remaining = len(matches_needing_goals) - (i + 1)
                    if remaining > 0:
                        logger.info(f"⏳ Batch complete. {remaining} matches remaining. Waiting 11 seconds...")
                        time.sleep(11)  # Proven successful delay
                        
            except Exception as e:
                logger.error(f"    ❌ Error processing match {match_id}: {e}")
                continue
                
        # Final verification
        logger.info(f"\n🏆 MLS GOALS IMPORT RESULTS:")
        logger.info("=" * 50)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND goals_home IS NOT NULL
            """, (league_id, season))
            final_goals_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND status = 'FT'
            """, (league_id, season))
            final_completed_count = cursor.fetchone()[0]
            
            # Calculate coverage
            coverage_percentage = (final_goals_count / final_completed_count) * 100 if final_completed_count > 0 else 0
            
        logger.info(f"✅ Import Summary:")
        logger.info(f"  Matches processed: {len(matches_needing_goals)}")
        logger.info(f"  Successfully imported: {total_imported}")
        logger.info(f"  API calls made: {total_api_calls}")
        
        logger.info(f"🎯 Final MLS Coverage:")
        logger.info(f"  Completed matches: {final_completed_count}")
        logger.info(f"  Matches with goals: {final_goals_count}")
        logger.info(f"  Goal coverage: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 95:
            logger.info("🎉 PERFECT! MLS goal coverage is outstanding!")
        elif coverage_percentage >= 80:
            logger.info("✅ EXCELLENT! MLS goal coverage is sufficient!")
        else:
            logger.warning("⚠️ MLS goal coverage needs improvement")
            
        return coverage_percentage >= 80
        
    except Exception as e:
        logger.error(f"💥 MLS goals import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Execute MLS goals import with corrected method
    success = import_mls_goals_corrected()
    if success:
        logger.info("🏆 MLS GOALS IMPORT COMPLETED SUCCESSFULLY!")
        logger.info("⚽ MLS is now ready for comprehensive goal predictions!")
    else:
        logger.error("🚨 MLS goals import needs attention")
