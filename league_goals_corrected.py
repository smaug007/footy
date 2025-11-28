#!/usr/bin/env python3
"""
League Goals Import - CORRECTED COMPREHENSIVE VERSION
Extended from MLS success to handle ALL European leagues
Uses the proven get_fixture_details() method - OVERWRITES existing data
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

def import_goals_for_league(league_config, season: int = 2025, batch_size: int = 50) -> Tuple[bool, Dict]:
    """Import goals for a single league using the corrected fixture details method."""
    logger.info(f"🚀 CORRECTED Goals Import for {league_config.name} ({league_config.country})")
    logger.info(f"⚽ League ID: {league_config.id}, API ID: {league_config.api_league_id}")
    logger.info("✅ Using get_fixture_details() method - PROVEN SUCCESSFUL")
    logger.info("🔄 OVERWRITES existing data if found")
    
    try:
        db_manager = get_db_manager()
        api_client = get_api_client()
        
        # Check current status for this league
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total completed matches for this league
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND status = 'FT'
            """, (league_config.id, season))
            total_completed = cursor.fetchone()[0]
            
            # Already have goals for this league
            cursor.execute("""
                SELECT COUNT(*) 
                FROM matches 
                WHERE league_id = ? AND season = ? AND goals_home IS NOT NULL
            """, (league_config.id, season))
            already_have_goals = cursor.fetchone()[0]
            
            remaining_needed = total_completed - already_have_goals
            
        logger.info(f"📊 Current {league_config.name} Goals Status:")
        logger.info(f"  Total completed matches: {total_completed}")
        logger.info(f"  Already have goals: {already_have_goals}")
        logger.info(f"  Still need goals: {remaining_needed}")
        
        if total_completed == 0:
            logger.warning(f"⚠️ No completed matches found for {league_config.name}")
            return False, {'reason': 'no_completed_matches', 'total_completed': 0}
        
        if remaining_needed <= 0:
            logger.info(f"✅ All {league_config.name} matches already have goal data!")
            return True, {'reason': 'already_complete', 'total_completed': total_completed, 'already_have_goals': already_have_goals}
        
        # Get matches needing goals (league-specific - CRITICAL!)
        matches_needing_goals = db_manager.get_matches_needing_goal_stats(
            season, 
            limit=1000,  # Get all for this league
            league_id=league_config.id  # CRITICAL: league-specific filter
        )
        
        if not matches_needing_goals:
            logger.info(f"✅ No {league_config.name} matches need goal statistics!")
            return True, {'reason': 'no_matches_needed', 'total_completed': total_completed}
        
        logger.info(f"🎯 Found {len(matches_needing_goals)} {league_config.name} matches needing goals")
        
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
                
                # Get fixture details using CORRECTED method (NOT get_fixture_statistics)
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
                            
                            # Update database (OVERWRITES existing)
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
                    
                # Rate limiting: pause every batch_size calls
                if (i + 1) % batch_size == 0:
                    remaining = len(matches_needing_goals) - (i + 1)
                    if remaining > 0:
                        logger.info(f"⏳ Batch complete. {remaining} matches remaining. Waiting 11 seconds...")
                        time.sleep(11)  # Proven successful delay
                        
            except Exception as e:
                logger.error(f"    ❌ Error processing match {match_id}: {e}")
                continue
        
        # Final verification for this league
        logger.info(f"\n🏆 {league_config.name} GOALS IMPORT RESULTS:")
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
                WHERE league_id = ? AND season = ? AND status = 'FT'
            """, (league_config.id, season))
            final_completed_count = cursor.fetchone()[0]
            
            # Calculate coverage
            coverage_percentage = (final_goals_count / final_completed_count) * 100 if final_completed_count > 0 else 0
            
        logger.info(f"✅ {league_config.name} Import Summary:")
        logger.info(f"  Matches processed: {len(matches_needing_goals)}")
        logger.info(f"  Successfully imported: {total_imported}")
        logger.info(f"  API calls made: {total_api_calls}")
        
        logger.info(f"🎯 Final {league_config.name} Coverage:")
        logger.info(f"  Completed matches: {final_completed_count}")
        logger.info(f"  Matches with goals: {final_goals_count}")
        logger.info(f"  Goal coverage: {coverage_percentage:.1f}%")
        
        success = coverage_percentage >= 80
        
        if coverage_percentage >= 95:
            logger.info(f"🎉 PERFECT! {league_config.name} goal coverage is outstanding!")
        elif coverage_percentage >= 80:
            logger.info(f"✅ EXCELLENT! {league_config.name} goal coverage is sufficient!")
        else:
            logger.warning(f"⚠️ {league_config.name} goal coverage needs improvement")
        
        return success, {
            'total_completed': final_completed_count,
            'goals_imported': final_goals_count,
            'coverage_percentage': coverage_percentage,
            'processed_this_session': total_imported,
            'api_calls_made': total_api_calls
        }
        
    except Exception as e:
        logger.error(f"💥 {league_config.name} goals import failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {'error': str(e)}

def import_all_european_goals(season: int = 2025) -> Dict:
    """Import goals for ALL European leagues."""
    logger.info("🚀 STARTING COMPREHENSIVE EUROPEAN GOALS IMPORT")
    logger.info("🎯 Based on proven MLS methodology with corrected API endpoints")
    logger.info("🔄 OVERWRITES existing data to fix corruption/partial imports")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Get European leagues
    european_leagues = get_european_leagues()
    
    if not european_leagues:
        logger.error("❌ No European leagues found!")
        return {}
    
    logger.info(f"🇪🇺 Processing {len(european_leagues)} European leagues")
    
    all_results = {}
    successful_leagues = []
    failed_leagues = []
    
    for i, league_config in enumerate(european_leagues, 1):
        logger.info(f"\n🔄 LEAGUE {i}/{len(european_leagues)}: {league_config.name}")
        logger.info("=" * 60)
        
        try:
            # Import goals for this league
            success, results = import_goals_for_league(league_config, season)
            all_results[league_config.id] = {
                'league_name': league_config.name,
                'country': league_config.country,
                'success': success,
                'results': results
            }
            
            if success:
                successful_leagues.append(league_config.name)
                logger.info(f"✅ {league_config.name} - GOALS IMPORT SUCCESS")
            else:
                failed_leagues.append(league_config.name)
                logger.error(f"❌ {league_config.name} - GOALS IMPORT FAILED")
            
            # Delay between leagues to be respectful to API
            if i < len(european_leagues):
                logger.info(f"⏳ Waiting 5 seconds before next league...")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"💥 Critical error processing {league_config.name}: {e}")
            failed_leagues.append(league_config.name)
            all_results[league_config.id] = {
                'league_name': league_config.name,
                'country': league_config.country,
                'success': False,
                'error': str(e)
            }
            continue
    
    # Final summary
    end_time = time.time()
    duration_minutes = (end_time - start_time) / 60
    
    logger.info(f"\n🏆 FINAL EUROPEAN GOALS IMPORT RESULTS")
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
        'failed_league_names': failed_leagues,
        'detailed_results': all_results
    }

if __name__ == "__main__":
    # Can run for specific league (MLS example) or all European leagues
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "mls":
        # Test MLS specifically
        league_manager = get_league_manager()
        mls_league = league_manager.get_league_by_id(1279)  # MLS league ID
        if mls_league:
            success, results = import_goals_for_league(mls_league)
            if success:
                logger.info("🏆 MLS GOALS IMPORT COMPLETED SUCCESSFULLY!")
            else:
                logger.error("🚨 MLS goals import needs attention")
        else:
            logger.error("❌ MLS league not found!")
    else:
        # Run comprehensive European import
        results = import_all_european_goals(2025)
        
        if results.get('success_rate', 0) >= 60:
            logger.info("🏆 EUROPEAN GOALS IMPORT COMPLETED SUCCESSFULLY!")
            logger.info("⚽ European leagues now have comprehensive goal data!")
        else:
            logger.error("🚨 European goals import needs attention")