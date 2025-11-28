#!/usr/bin/env python3
"""
Import European Leagues - CORRECTED VERSION
Fixed team ID mapping issues and foreign key constraints
"""
import logging
import time
from data.data_importer import DataImporter
from data.database import get_db_manager
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_europe_fixed():
    """Import European leagues with proper error handling."""
    try:
        logger.info("🚀 IMPORTING EUROPEAN LEAGUES - CORRECTED")
        logger.info("🔧 Fixed team ID mapping and foreign key issues")
        
        # Initialize services
        importer = DataImporter()
        league_manager = get_league_manager()
        db_manager = get_db_manager()
        
        # Get European leagues (focus on major ones first)
        european_countries = [
            'Spain', 'Italy', 'France', 'England', 'Germany', 'Netherlands', 
            'Portugal', 'Belgium'  # Start with major leagues
        ]
        
        all_leagues = league_manager.get_active_leagues()
        major_european_leagues = [
            league for league in all_leagues 
            if league.country in european_countries
        ]
        
        # Sort by priority (major leagues first)
        major_leagues_first = sorted(major_european_leagues, key=lambda x: x.priority_order)
        
        logger.info(f"🇪🇺 Processing {len(major_leagues_first)} major European leagues")
        
        successful = []
        failed = []
        total_api_calls = 0
        current_season = 2025
        
        for i, league in enumerate(major_leagues_first, 1):
            try:
                logger.info(f"\n📍 [{i}/{len(major_leagues_first)}] {league.country}: {league.name}")
                logger.info("-" * 50)
                
                league_api_calls = 0
                
                # Step 1: Teams (should work - we know this works for La Liga)
                teams_count = importer.import_teams(league.id, current_season)
                league_api_calls += 1
                logger.info(f"  👥 Teams: {teams_count}")
                
                if teams_count == 0:
                    logger.warning(f"  ⚠️ No teams for {league.name}, skipping")
                    failed.append(f"{league.country} - {league.name} (No teams)")
                    continue
                
                # Verify teams were actually inserted
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM teams 
                        WHERE league_id = ? AND season = ?
                    """, (league.id, current_season))
                    db_teams_count = cursor.fetchone()[0]
                    
                if db_teams_count == 0:
                    logger.error(f"  ❌ Teams not in database despite import success!")
                    failed.append(f"{league.country} - {league.name} (Teams not persisted)")
                    continue
                    
                logger.info(f"  ✅ Teams verified in database: {db_teams_count}")
                
                # Step 2: Matches (with better error handling)
                try:
                    matches_count = importer.import_matches(league.id, current_season)
                    league_api_calls += 2
                    logger.info(f"  ⚽ Matches: {matches_count}")
                    
                    if matches_count == 0:
                        logger.warning(f"  ⚠️ No matches imported for {league.name}")
                        # Continue anyway - maybe season hasn't started
                        
                except Exception as match_error:
                    logger.error(f"  ❌ Match import failed: {match_error}")
                    # Don't fail the entire league - continue with statistics
                    matches_count = 0
                
                # Step 3: Corner Statistics (for completed matches only)
                corners_count = 0
                if matches_count > 0:
                    try:
                        corners_count = importer.import_match_statistics(league.id, current_season, limit=50)
                        league_api_calls += corners_count
                        logger.info(f"  🏈 Corner stats: {corners_count}")
                    except Exception as corner_error:
                        logger.warning(f"  ⚠️ Corner stats failed: {corner_error}")
                        corners_count = 0
                
                # Step 4: Goal Statistics (limited batch)
                goals_count = 0
                if matches_count > 0:
                    try:
                        matches_needing_goals = db_manager.get_matches_needing_goal_stats(
                            current_season, limit=20, league_id=league.id
                        )
                        
                        if matches_needing_goals:
                            from data.api_client import get_api_client
                            api_client = get_api_client()
                            
                            for match in matches_needing_goals[:20]:  # Limit to 20 for testing
                                try:
                                    fixture_data = api_client.get_fixture_details(match[0])
                                    league_api_calls += 1
                                    
                                    if fixture_data and fixture_data.get('home_goals') is not None:
                                        home_goals = int(fixture_data.get('home_goals', 0))
                                        away_goals = int(fixture_data.get('away_goals', 0))
                                        
                                        if db_manager.update_match_goals(match[1], home_goals, away_goals):
                                            goals_count += 1
                                            
                                except Exception:
                                    continue  # Skip failed matches
                                    
                        logger.info(f"  ⚽ Goal stats: {goals_count}")
                        
                    except Exception as goal_error:
                        logger.warning(f"  ⚠️ Goal stats failed: {goal_error}")
                        goals_count = 0
                
                # Success summary
                total_api_calls += league_api_calls
                successful.append({
                    'country': league.country,
                    'name': league.name,
                    'teams': teams_count,
                    'matches': matches_count,
                    'corners': corners_count,
                    'goals': goals_count
                })
                
                logger.info(f"  📊 Summary: {teams_count}T, {matches_count}M, {corners_count}C, {goals_count}G")
                logger.info(f"  🔌 API calls: {league_api_calls}")
                
                # Rate limiting
                if total_api_calls > 0 and total_api_calls % 50 == 0:
                    logger.info(f"⏳ API checkpoint: {total_api_calls} calls, pausing 11 seconds...")
                    time.sleep(11)
                    
            except Exception as e:
                logger.error(f"❌ League failed: {league.country} - {league.name}: {e}")
                failed.append(f"{league.country} - {league.name} (Error: {str(e)[:50]})")
                continue
                
        # Final summary
        logger.info(f"\n🏆 EUROPEAN IMPORT RESULTS")
        logger.info("=" * 50)
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        logger.info(f"🔌 Total API calls: {total_api_calls}")
        
        if successful:
            logger.info(f"\n✅ Successfully imported:")
            for league in successful:
                logger.info(f"  🇪🇺 {league['country']}: {league['name']}")
                logger.info(f"     {league['teams']}T, {league['matches']}M, {league['corners']}C, {league['goals']}G")
        
        if failed:
            logger.info(f"\n❌ Failed leagues:")
            for failure in failed:
                logger.info(f"  - {failure}")
                
        success_rate = len(successful) / len(major_leagues_first) * 100
        logger.info(f"\n📊 Success rate: {success_rate:.1f}%")
        
        return success_rate > 50
        
    except Exception as e:
        logger.error(f"💥 European import failed: {e}")
        return False

if __name__ == "__main__":
    success = import_europe_fixed()
    if success:
        logger.info("🏆 European import completed with good success rate!")
    else:
        logger.error("🚨 European import had significant issues")
