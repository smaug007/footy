#!/usr/bin/env python3
"""
Import Goal Statistics for ALL Leagues - Extended from successful MLS approach  
Uses get_fixture_details() method which provides clean goal data structure
OVERWRITES existing goal data to ensure accuracy
"""
import logging
import time
from data.api_client import get_api_client
from data.database import get_db_manager
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_all_leagues_goals():
    """Import goal statistics for all active leagues using proven MLS method."""
    try:
        logger.info("🚀 IMPORTING GOAL STATISTICS FOR ALL LEAGUES")
        logger.info("⚽ Using proven MLS approach with get_fixture_details()")
        logger.info("📊 Goal data: 'home_goals', 'away_goals', 'total_goals', 'goals'")
        logger.info("🔄 OVERWRITES existing goal data to ensure accuracy")
        
        # Initialize services
        api_client = get_api_client()
        db_manager = get_db_manager()
        league_manager = get_league_manager()
        
        # Get all active leagues
        all_leagues = league_manager.get_active_leagues()
        logger.info(f"📈 Processing goal statistics for {len(all_leagues)} leagues")
        
        successful_leagues = []
        failed_leagues = []
        total_goals_imported = 0
        total_api_calls = 0
        current_season = 2025
        
        for i, league in enumerate(all_leagues, 1):
            try:
                logger.info(f"\n📍 [{i}/{len(all_leagues)}] {league.country}: {league.name}")
                logger.info("-" * 50)
                
                # Get completed matches for this league (regardless of existing goal data)
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT api_fixture_id, id, 
                               (SELECT name FROM teams t1 WHERE t1.id = matches.home_team_id) as home_team,
                               (SELECT name FROM teams t2 WHERE t2.id = matches.away_team_id) as away_team
                        FROM matches 
                        WHERE league_id = ? AND season = ? AND status = 'FT'
                        ORDER BY match_date DESC
                        LIMIT 50
                    """, (league.id, current_season))
                    matches_to_process = cursor.fetchall()
                    
                if not matches_to_process:
                    logger.warning(f"  ⚠️ No completed matches found for {league.name}")
                    failed_leagues.append(f"{league.country} - {league.name} (No matches)")
                    continue
                    
                logger.info(f"📊 Processing {len(matches_to_process)} completed matches...")
                
                league_goals_imported = 0
                league_api_calls = 0
                
                for match in matches_to_process:
                    if league_api_calls >= 40:  # Conservative API limit per league
                        logger.info(f"  ⏸️ League API limit reached: {league_api_calls} calls")
                        break
                        
                    try:
                        api_fixture_id = match[0]
                        match_id = match[1]
                        home_team = match[2]
                        away_team = match[3]
                        
                        # Get fixture details using the proven method
                        fixture_data = api_client.get_fixture_details(api_fixture_id)
                        league_api_calls += 1
                        total_api_calls += 1
                        
                        if fixture_data:
                            # Extract goals using the clean structure (as proven with MLS)
                            home_goals = fixture_data.get('home_goals')
                            away_goals = fixture_data.get('away_goals')
                            
                            if home_goals is not None and away_goals is not None:
                                try:
                                    home_goals_int = int(home_goals) if str(home_goals).isdigit() else 0
                                    away_goals_int = int(away_goals) if str(away_goals).isdigit() else 0
                                    
                                    # Update database (OVERWRITE existing data)
                                    if db_manager.update_match_goals(match_id, home_goals_int, away_goals_int):
                                        league_goals_imported += 1
                                        total_goals_imported += 1
                                    
                                except (ValueError, TypeError):
                                    logger.warning(f"    ⚠️ Invalid goal values: {home_goals}, {away_goals}")
                            else:
                                logger.warning(f"    ⚠️ No goal data: {home_team} vs {away_team}")
                        else:
                            logger.warning(f"    ❌ No fixture data for {api_fixture_id}")
                            
                    except Exception as match_error:
                        logger.warning(f"    ❌ Match error: {match_error}")
                        continue
                        
                # League summary
                if league_goals_imported > 0:
                    logger.info(f"  ✅ Goal stats imported: {league_goals_imported} matches")
                    logger.info(f"  🔌 API calls used: {league_api_calls}")
                    
                    successful_leagues.append({
                        'country': league.country,
                        'name': league.name,
                        'goals': league_goals_imported,
                        'api_calls': league_api_calls
                    })
                else:
                    logger.warning(f"  ⚠️ No goal statistics imported for {league.name}")
                    failed_leagues.append(f"{league.country} - {league.name} (No goals imported)")
                
                # Rate limiting every 50 API calls
                if total_api_calls > 0 and total_api_calls % 50 == 0:
                    logger.info(f"⏳ API checkpoint: {total_api_calls} calls, pausing 11 seconds...")
                    time.sleep(11)
                    
            except Exception as e:
                logger.error(f"❌ League failed: {league.country} - {league.name}: {e}")
                failed_leagues.append(f"{league.country} - {league.name} (Error: {str(e)[:50]})")
                continue
                
        # Final comprehensive summary
        logger.info(f"\n🏆 GOAL STATISTICS IMPORT RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Successful leagues: {len(successful_leagues)}")
        logger.info(f"❌ Failed leagues: {len(failed_leagues)}")
        logger.info(f"⚽ Total goal stats imported: {total_goals_imported}")
        logger.info(f"🔌 Total API calls used: {total_api_calls}")
        
        if successful_leagues:
            logger.info(f"\n✅ Successfully imported goal statistics:")
            by_country = {}
            for league in successful_leagues:
                country = league['country']
                if country not in by_country:
                    by_country[country] = []
                by_country[country].append(league)
                
            for country, leagues in sorted(by_country.items()):
                country_goals = sum(l['goals'] for l in leagues)
                country_api_calls = sum(l['api_calls'] for l in leagues)
                logger.info(f"  🌍 {country}: {len(leagues)} leagues, {country_goals} matches, {country_api_calls} API calls")
                for league in leagues:
                    logger.info(f"    - {league['name']}: {league['goals']} matches")
        
        if failed_leagues:
            logger.info(f"\n❌ Failed leagues:")
            for failure in failed_leagues:
                logger.info(f"  - {failure}")
                
        success_rate = len(successful_leagues) / len(all_leagues) * 100 if all_leagues else 0
        logger.info(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 70:
            logger.info("🎉 EXCELLENT! Goal import highly successful!")
        elif success_rate >= 50:
            logger.info("✅ GOOD! Goal import mostly successful!")  
        else:
            logger.warning("⚠️ Goal import had significant issues")
            
        return success_rate >= 50
        
    except Exception as e:
        logger.error(f"💥 Global goal import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_all_leagues_goals()
    if success:
        logger.info("🏆 GLOBAL GOAL STATISTICS IMPORT COMPLETED!")
        logger.info("⚽ All leagues now have goal data for BTTS predictions!")
    else:
        logger.error("🚨 Global goal import needs attention")
