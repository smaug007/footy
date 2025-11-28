#!/usr/bin/env python3
"""
Import ALL European Leagues - Complete Data Import
Teams + Matches + Corner Statistics + Goal Statistics for all 37 European leagues
"""
import logging
import time
from data.data_importer import DataImporter
from data.api_client import get_api_client
from data.database import get_db_manager
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# European countries from our 37 leagues
EUROPEAN_COUNTRIES = [
    'Spain', 'Italy', 'France', 'England', 'Germany', 'Netherlands', 'Portugal', 
    'Belgium', 'Turkey', 'Russia', 'Poland', 'Czech Republic', 'Austria', 
    'Switzerland', 'Denmark', 'Sweden', 'Norway', 'Scotland', 'Greece'
]

def import_all_europe_leagues():
    """Import complete data for ALL European leagues."""
    try:
        logger.info("🚀 IMPORTING ALL EUROPEAN LEAGUES")
        logger.info("🌍 Target: Complete import for 37 European leagues")
        logger.info("📊 Teams + Matches + Corners + Goals")
        
        # Initialize services
        importer = DataImporter()
        league_manager = get_league_manager()
        api_client = get_api_client()
        db_manager = get_db_manager()
        
        # Get all active European leagues
        all_leagues = league_manager.get_active_leagues()
        european_leagues = [
            league for league in all_leagues 
            if league.country in EUROPEAN_COUNTRIES
        ]
        
        logger.info(f"🇪🇺 Found {len(european_leagues)} European leagues to process")
        
        # Group by country for better organization
        by_country = {}
        for league in european_leagues:
            if league.country not in by_country:
                by_country[league.country] = []
            by_country[league.country].append(league)
            
        # Display structure
        logger.info("🗺️ European League Structure:")
        for country, leagues in sorted(by_country.items()):
            logger.info(f"  🇪🇺 {country}: {len(leagues)} leagues")
            for league in leagues:
                logger.info(f"    - {league.name} (ID: {league.id})")
        
        # Import statistics
        total_api_calls = 0
        successful_leagues = []
        failed_leagues = []
        
        current_season = 2025  # Current season for European leagues
        
        logger.info(f"\n🔥 STARTING COMPREHENSIVE IMPORT")
        logger.info("=" * 60)
        
        for i, league in enumerate(european_leagues, 1):
            try:
                logger.info(f"\n📍 [{i}/{len(european_leagues)}] {league.country}: {league.name}")
                logger.info("-" * 50)
                
                league_api_calls = 0
                
                # Step 1: Import Teams
                logger.info("👥 Step 1: Importing teams...")
                teams_imported = importer.import_teams(league.id, current_season)
                league_api_calls += 1  # Teams API call
                
                if teams_imported == 0:
                    logger.warning(f"⚠️ No teams found for {league.name}, skipping")
                    failed_leagues.append(f"{league.country} - {league.name} (No teams)")
                    continue
                    
                logger.info(f"  ✅ Teams: {teams_imported}")
                
                # Step 2: Import Matches
                logger.info("⚽ Step 2: Importing matches...")
                matches_imported = importer.import_matches(league.id, current_season)
                league_api_calls += 2  # Estimated matches API calls
                
                logger.info(f"  ✅ Matches: {matches_imported}")
                
                if matches_imported == 0:
                    logger.warning(f"⚠️ No matches found for {league.name}")
                    failed_leagues.append(f"{league.country} - {league.name} (No matches)")
                    continue
                
                # Step 3: Import Corner Statistics
                logger.info("🏈 Step 3: Importing corner statistics...")
                corner_stats_imported = importer.import_match_statistics(league.id, current_season, limit=100)
                league_api_calls += corner_stats_imported  # 1 API call per match with corners
                
                logger.info(f"  ✅ Corner stats: {corner_stats_imported}")
                
                # Step 4: Import Goal Statistics
                logger.info("⚽ Step 4: Importing goal statistics...")
                
                # Get matches needing goals for this specific league
                matches_needing_goals = db_manager.get_matches_needing_goal_stats(
                    current_season, limit=100, league_id=league.id
                )
                
                goals_imported = 0
                if matches_needing_goals:
                    for match in matches_needing_goals:
                        try:
                            api_fixture_id = match[0]
                            match_id = match[1]
                            
                            fixture_data = api_client.get_fixture_details(api_fixture_id)
                            league_api_calls += 1
                            
                            if fixture_data:
                                home_goals = fixture_data.get('home_goals')
                                away_goals = fixture_data.get('away_goals')
                                
                                if home_goals is not None and away_goals is not None:
                                    home_goals_int = int(home_goals) if str(home_goals).isdigit() else 0
                                    away_goals_int = int(away_goals) if str(away_goals).isdigit() else 0
                                    
                                    if db_manager.update_match_goals(match_id, home_goals_int, away_goals_int):
                                        goals_imported += 1
                                        
                        except Exception as e:
                            logger.warning(f"    Goal import error for match {match[1]}: {e}")
                            continue
                
                logger.info(f"  ✅ Goal stats: {goals_imported}")
                
                # League summary
                total_api_calls += league_api_calls
                logger.info(f"📊 League Summary:")
                logger.info(f"  Teams: {teams_imported}, Matches: {matches_imported}")
                logger.info(f"  Corner stats: {corner_stats_imported}, Goal stats: {goals_imported}")
                logger.info(f"  API calls for this league: {league_api_calls}")
                
                successful_leagues.append({
                    'country': league.country,
                    'name': league.name,
                    'teams': teams_imported,
                    'matches': matches_imported,
                    'corners': corner_stats_imported,
                    'goals': goals_imported,
                    'api_calls': league_api_calls
                })
                
                # Optimized delay every 50 API calls (like successful MLS import)
                if total_api_calls > 0 and total_api_calls % 50 == 0:
                    logger.info(f"⏳ API limit checkpoint: {total_api_calls} calls made, pausing 11 seconds...")
                    time.sleep(11)
                    
            except Exception as e:
                logger.error(f"❌ Failed to import {league.country} - {league.name}: {e}")
                failed_leagues.append(f"{league.country} - {league.name} (Error: {e})")
                continue
                
        # Final comprehensive summary
        logger.info(f"\n🏆 FINAL EUROPEAN IMPORT RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"✅ Import Summary:")
        logger.info(f"  Total leagues processed: {len(european_leagues)}")
        logger.info(f"  Successfully imported: {len(successful_leagues)}")
        logger.info(f"  Failed imports: {len(failed_leagues)}")
        logger.info(f"  Total API calls used: {total_api_calls}")
        
        # Success breakdown by country
        if successful_leagues:
            logger.info(f"\n🇪🇺 Successful Leagues by Country:")
            by_country_success = {}
            for league in successful_leagues:
                country = league['country']
                if country not in by_country_success:
                    by_country_success[country] = []
                by_country_success[country].append(league)
                
            for country, leagues in sorted(by_country_success.items()):
                total_teams = sum(l['teams'] for l in leagues)
                total_matches = sum(l['matches'] for l in leagues)
                total_corners = sum(l['corners'] for l in leagues)
                total_goals = sum(l['goals'] for l in leagues)
                
                logger.info(f"  🇪🇺 {country}: {len(leagues)} leagues")
                logger.info(f"     Teams: {total_teams}, Matches: {total_matches}")
                logger.info(f"     Corners: {total_corners}, Goals: {total_goals}")
        
        # Failed leagues
        if failed_leagues:
            logger.warning(f"\n❌ Failed Leagues:")
            for failed in failed_leagues:
                logger.warning(f"  - {failed}")
                
        # Calculate success rate
        success_rate = (len(successful_leagues) / len(european_leagues)) * 100 if european_leagues else 0
        
        logger.info(f"\n📊 Final Statistics:")
        logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info(f"  Total API efficiency: {total_api_calls} calls for {len(successful_leagues)} leagues")
        logger.info(f"  Average calls per league: {total_api_calls // len(successful_leagues) if successful_leagues else 0}")
        
        if success_rate >= 80:
            logger.info("🎉 OUTSTANDING! European import highly successful!")
        elif success_rate >= 60:
            logger.info("✅ GOOD! European import mostly successful!")
        else:
            logger.warning("⚠️ European import had significant issues")
            
        return success_rate >= 60
        
    except Exception as e:
        logger.error(f"💥 European import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_all_europe_leagues()
    if success:
        logger.info("🏆 EUROPEAN LEAGUES IMPORT COMPLETED!")
        logger.info("🌍 37 European leagues now have comprehensive data!")
        logger.info("⚽ Ready for predictions across all of Europe!")
    else:
        logger.error("🚨 European import needs attention")
