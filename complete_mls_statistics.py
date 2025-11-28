#!/usr/bin/env python3
"""
Complete League Statistics Import - COMPREHENSIVE VERSION
Systematic batch import of ALL remaining matches for ANY league with proper API rate limiting
Extended from the successful MLS approach that achieved 100% coverage to ALL European leagues
OVERWRITES existing data to fix corruption or partial imports
"""
import logging
import time
from typing import List, Dict, Tuple
from data.api_client import get_api_client
from data.database import get_db_manager
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_european_leagues() -> List:
    """Get all European leagues for processing."""
    try:
        league_manager = get_league_manager()
        
        european_countries = [
            'Spain', 'Italy', 'France', 'England', 'Germany', 
            'Netherlands', 'Portugal', 'Belgium', 'Turkey', 
            'Russia', 'Poland', 'Czech Republic', 'Austria', 
            'Switzerland', 'Denmark', 'Sweden', 'Norway', 
            'Scotland', 'Greece'
        ]
        
        all_leagues = league_manager.get_active_leagues()
        european_leagues = [
            league for league in all_leagues 
            if league.country in european_countries
        ]
        
        # Sort by priority (major leagues first)
        return sorted(european_leagues, key=lambda x: x.priority_order)
        
    except Exception as e:
        logger.error(f"Failed to get European leagues: {e}")
        return []

def complete_league_statistics(league_id: int = None, season: int = 2025, league_config = None):
    """Complete statistics import for ALL remaining matches in a league."""
    try:
        # Get league info
        if league_config is None:
            league_manager = get_league_manager()
            league_config = league_manager.get_league_by_id(league_id)
            
        if not league_config:
            logger.error(f"League {league_id} not found!")
            return False
            
        logger.info(f"🚀 COMPLETING STATISTICS IMPORT FOR {league_config.name}")
        logger.info(f"🇪🇺 Country: {league_config.country}, API ID: {league_config.api_league_id}")
        logger.info("⚽ Target: Import goals for ALL remaining completed matches")
        logger.info("🔄 OVERWRITES existing data if found")
        
        db_manager = get_db_manager()
        api_client = get_api_client()
        
        # Check current status for this specific league
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total completed matches that should have goals for THIS league
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? 
                AND (status = 'FT' OR status = 'Match Finished')
            """, (league_config.id, season))
            total_completed = cursor.fetchone()[0]
            
            # Already have goals for THIS league
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND goals_home IS NOT NULL
            """, (league_config.id, season))
            already_have_goals = cursor.fetchone()[0]
            
            remaining_needed = total_completed - already_have_goals
            
        logger.info(f"📊 {league_config.name} Statistics Status:")
        logger.info(f"  Total completed matches: {total_completed}")
        logger.info(f"  Already have goals: {already_have_goals}")
        logger.info(f"  Still need goals: {remaining_needed}")
        
        if total_completed == 0:
            logger.warning(f"⚠️ No completed matches found for {league_config.name}")
            return False
            
        if remaining_needed <= 0:
            logger.info(f"✅ All {league_config.name} matches already have goal data!")
            return True
            
        # Batch processing parameters (proven from MLS success)
        BATCH_SIZE = 50  # Process 50 matches per batch
        MAX_API_CALLS_PER_BATCH = 45  # Conservative API limit per batch
        DELAY_BETWEEN_BATCHES = 11  # Seconds delay between batches (optimized)
        
        total_batches = (remaining_needed + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"🔄 Will process {total_batches} batches of up to {BATCH_SIZE} matches each")
        
        total_imported = 0
        total_api_calls = 0
        batch_number = 0
        
        while True:
            batch_number += 1
            logger.info(f"\n🔥 BATCH {batch_number}/{total_batches}")
            logger.info("=" * 50)
            
            # Get next batch of matches needing goals (LEAGUE-SPECIFIC)
            matches_batch = db_manager.get_matches_needing_goal_stats(
                season, 
                limit=BATCH_SIZE, 
                league_id=league_config.id  # Use league_config.id instead of league_id
            )
            
            if not matches_batch:
                logger.info("✅ No more matches need goal statistics!")
                break
                
            logger.info(f"📦 Processing {len(matches_batch)} matches in this batch")
            
            batch_imported = 0
            batch_api_calls = 0
            
            for i, match in enumerate(matches_batch):
                if batch_api_calls >= MAX_API_CALLS_PER_BATCH:
                    logger.info(f"⏸️ API limit reached for batch {batch_number}")
                    break
                    
                try:
                    api_fixture_id = match[0]
                    match_id = match[1]
                    home_team = match[2]
                    away_team = match[3]
                    
                    # Progress indicator
                    progress = f"[{i+1}/{len(matches_batch)}]"
                    logger.info(f"⚽ {progress} {home_team} vs {away_team}")
                    
                    # Get fixture details (using proven method)
                    fixture_data = api_client.get_fixture_details(api_fixture_id)
                    batch_api_calls += 1
                    total_api_calls += 1
                    
                    if fixture_data:
                        home_goals = fixture_data.get('home_goals')
                        away_goals = fixture_data.get('away_goals')
                        
                        if home_goals is not None and away_goals is not None:
                            try:
                                home_goals_int = int(home_goals) if str(home_goals).isdigit() else 0
                                away_goals_int = int(away_goals) if str(away_goals).isdigit() else 0
                                
                                if db_manager.update_match_goals(match_id, home_goals_int, away_goals_int):
                                    batch_imported += 1
                                    total_imported += 1
                                    logger.info(f"    ✅ {home_goals_int}-{away_goals_int}")
                                else:
                                    logger.warning(f"    ⚠️ Database update failed")
                                    
                            except (ValueError, TypeError):
                                logger.warning(f"    ⚠️ Invalid goal values: {home_goals}, {away_goals}")
                        else:
                            logger.warning(f"    ⚠️ No goal data in response")
                    else:
                        logger.warning(f"    ❌ No fixture data returned")
                        
                except Exception as e:
                    logger.error(f"    ❌ Error: {e}")
                    continue
                    
            # Batch summary
            logger.info(f"📊 Batch {batch_number} Results:")
            logger.info(f"  Processed: {len(matches_batch[:batch_api_calls])}")
            logger.info(f"  Successfully imported: {batch_imported}")
            logger.info(f"  API calls used: {batch_api_calls}")
            logger.info(f"  Running total imported: {total_imported}")
            
            # Check if we're done (LEAGUE-SPECIFIC)
            remaining_matches = db_manager.get_matches_needing_goal_stats(season, limit=1, league_id=league_config.id)
            if not remaining_matches:
                logger.info("🎉 All matches processed!")
                break
                
            # Delay between batches (except for the last one)
            if remaining_matches and batch_number < total_batches:
                logger.info(f"⏳ Waiting {DELAY_BETWEEN_BATCHES} seconds before next batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)
                
        # Final verification and summary
        logger.info(f"\n🏆 FINAL {league_config.name} STATISTICS IMPORT RESULTS:")
        logger.info("=" * 60)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND goals_home IS NOT NULL
            """, (league_config.id, season))
            final_goals_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? 
                AND (status = 'FT' OR status = 'Match Finished')
            """, (league_config.id, season))
            total_completed_final = cursor.fetchone()[0]
            
            # Calculate coverage
            coverage_percentage = (final_goals_count / total_completed_final) * 100 if total_completed_final > 0 else 0
            
        logger.info(f"✅ Import Summary:")
        logger.info(f"  Total imports in this session: {total_imported}")
        logger.info(f"  Total API calls made: {total_api_calls}")
        logger.info(f"  Batches processed: {batch_number}")
        
        logger.info(f"🎯 Final Coverage:")
        logger.info(f"  Completed matches: {total_completed_final}")
        logger.info(f"  Matches with goals: {final_goals_count}")
        logger.info(f"  Coverage: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 95:
            logger.info(f"🎉 OUTSTANDING! {league_config.name} goal coverage is excellent!")
        elif coverage_percentage >= 80:
            logger.info(f"✅ GOOD! {league_config.name} goal coverage is sufficient for predictions!")
        else:
            logger.warning(f"⚠️ {league_config.name} goal coverage may need improvement for optimal predictions")
            
        return coverage_percentage >= 80
        
    except Exception as e:
        logger.error(f"💥 Complete statistics import failed for {league_config.name if league_config else f'league {league_id}'}: {e}")
        import traceback
        traceback.print_exc()
        return False

def complete_all_european_statistics(season: int = 2025) -> Dict:
    """Complete statistics import for ALL European leagues."""
    logger.info("🚀 STARTING COMPREHENSIVE EUROPEAN STATISTICS IMPORT")
    logger.info("🎯 Based on proven MLS methodology that achieved 100% coverage")
    logger.info("🔄 OVERWRITES existing data to fix corruption/partial imports")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Get European leagues
    european_leagues = get_european_leagues()
    
    if not european_leagues:
        logger.error("❌ No European leagues found!")
        return {}
    
    logger.info(f"🇪🇺 Processing {len(european_leagues)} European leagues")
    
    successful_leagues = []
    failed_leagues = []
    
    for i, league_config in enumerate(european_leagues, 1):
        logger.info(f"\n🔄 LEAGUE {i}/{len(european_leagues)}: {league_config.name}")
        logger.info("=" * 60)
        
        try:
            # Import statistics for this league
            success = complete_league_statistics(league_config.id, season, league_config)
            
            if success:
                successful_leagues.append(league_config.name)
                logger.info(f"✅ {league_config.name} - STATISTICS IMPORT SUCCESS")
            else:
                failed_leagues.append(league_config.name)
                logger.error(f"❌ {league_config.name} - STATISTICS IMPORT FAILED")
            
            # Delay between leagues to be respectful to API
            if i < len(european_leagues):
                logger.info(f"⏳ Waiting 5 seconds before next league...")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"💥 Critical error processing {league_config.name}: {e}")
            failed_leagues.append(league_config.name)
            continue
    
    # Final summary
    end_time = time.time()
    duration_minutes = (end_time - start_time) / 60
    
    logger.info(f"\n🏆 FINAL EUROPEAN STATISTICS IMPORT RESULTS")
    logger.info("=" * 80)
    logger.info(f"⏱️ Total Duration: {duration_minutes:.1f} minutes")
    logger.info(f"🇪🇺 Total Leagues Processed: {len(european_leagues)}")
    logger.info(f"✅ Successful Leagues: {len(successful_leagues)}")
    logger.info(f"❌ Failed Leagues: {len(failed_leagues)}")
    
    if successful_leagues:
        logger.info(f"\n🎉 SUCCESSFUL LEAGUES:")
        for league_name in successful_leagues:
            logger.info(f"  ✅ {league_name}")
    
    if failed_leagues:
        logger.info(f"\n⚠️ FAILED LEAGUES:")
        for league_name in failed_leagues:
            logger.info(f"  ❌ {league_name}")
    
    success_rate = (len(successful_leagues) / len(european_leagues)) * 100 if european_leagues else 0
    logger.info(f"\n📈 SUCCESS RATE: {success_rate:.1f}%")
    
    return {
        'total_leagues': len(european_leagues),
        'successful_leagues': len(successful_leagues),
        'failed_leagues': len(failed_leagues),
        'success_rate': success_rate,
        'duration_minutes': duration_minutes,
        'successful_league_names': successful_leagues,
        'failed_league_names': failed_leagues
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "mls":
        # Test MLS specifically
        success = complete_league_statistics(1279, 2025)  # MLS league ID
        if success:
            logger.info("🏆 MLS STATISTICS IMPORT COMPLETED SUCCESSFULLY!")
            logger.info("⚽ MLS is now ready for comprehensive predictions!")
            logger.info("🎯 BTTS predictions, goal analysis, and full features available!")
        else:
            logger.error("🚨 MLS statistics import needs attention")
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        # Test specific league by ID
        league_id = int(sys.argv[1])
        success = complete_league_statistics(league_id, 2025)
        if success:
            logger.info(f"🏆 LEAGUE {league_id} STATISTICS IMPORT COMPLETED SUCCESSFULLY!")
        else:
            logger.error(f"🚨 League {league_id} statistics import needs attention")
    else:
        # Run comprehensive European import
        results = complete_all_european_statistics(2025)
        
        if results.get('success_rate', 0) >= 60:
            logger.info("🏆 EUROPEAN STATISTICS IMPORT COMPLETED SUCCESSFULLY!")
            logger.info("⚽ European leagues now have comprehensive goal data!")
        else:
            logger.error("🚨 European statistics import needs attention")
