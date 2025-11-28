#!/usr/bin/env python3
"""
Import European Leagues - FILTERED VERSION
Only import actual league matches, skip cup/friendly matches with external teams
"""
import logging
import time
from data.data_importer import DataImporter
from data.database import get_db_manager
from data.league_manager import get_league_manager
from data.api_client import get_api_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_league_matches_only(league_id: int, season: int, league_config):
    """Import only actual league matches, skip cup/friendly matches."""
    try:
        api_client = get_api_client()
        db_manager = get_db_manager()
        
        logger.info(f"🔍 Getting fixtures for {league_config.name}...")
        
        # Get all fixtures
        fixtures_response = api_client.get_fixtures(league_config.api_league_id, season)
        
        if 'response' not in fixtures_response:
            logger.error(f"❌ No fixtures response")
            return 0
            
        all_fixtures = fixtures_response['response']
        logger.info(f"📊 Total fixtures from API: {len(all_fixtures)}")
        
        # Get all team API IDs that exist in our database for this league
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT api_team_id FROM teams 
                WHERE league_id = ? AND season = ?
            """, (league_id, season))
            valid_team_api_ids = set(row[0] for row in cursor.fetchall())
            
        logger.info(f"📊 Valid team API IDs in database: {len(valid_team_api_ids)}")
        
        # Filter fixtures to only include matches between teams in our database
        league_fixtures = []
        cup_fixtures_skipped = 0
        
        for fixture in all_fixtures:
            teams_info = fixture.get('teams', {})
            league_info = fixture.get('league', {})
            
            home_api_id = teams_info.get('home', {}).get('id')
            away_api_id = teams_info.get('away', {}).get('id')
            
            # Only include if BOTH teams are in our database
            if home_api_id in valid_team_api_ids and away_api_id in valid_team_api_ids:
                # Also check if it's actually the correct league
                fixture_league_id = league_info.get('id')
                if fixture_league_id == league_config.api_league_id:
                    league_fixtures.append(fixture)
                else:
                    cup_fixtures_skipped += 1
            else:
                cup_fixtures_skipped += 1
                
        logger.info(f"✅ Filtered league fixtures: {len(league_fixtures)}")
        logger.info(f"⚠️ Cup/external fixtures skipped: {cup_fixtures_skipped}")
        
        # Import the filtered fixtures
        imported_count = 0
        
        for fixture_data in league_fixtures:
            try:
                fixture_info = fixture_data.get('fixture', {})
                teams_info = fixture_data.get('teams', {})
                
                # Get team IDs from database
                home_team_api_id = teams_info.get('home', {}).get('id')
                away_team_api_id = teams_info.get('away', {}).get('id')
                
                # Find teams in database
                with db_manager.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT id FROM teams 
                        WHERE api_team_id = ? AND league_id = ? AND season = ?
                    """, (home_team_api_id, league_id, season))
                    home_team = cursor.fetchone()
                    
                    cursor = conn.execute("""
                        SELECT id FROM teams 
                        WHERE api_team_id = ? AND league_id = ? AND season = ?
                    """, (away_team_api_id, league_id, season))
                    away_team = cursor.fetchone()
                
                if not home_team or not away_team:
                    logger.warning(f"⚠️ Teams not found (should not happen with filtering): {fixture_info.get('id')}")
                    continue
                
                # Prepare match data
                match_data = {
                    'api_fixture_id': fixture_info.get('id'),
                    'home_team_id': home_team[0],
                    'away_team_id': away_team[0],
                    'match_date': fixture_info.get('date'),
                    'venue_name': fixture_info.get('venue', {}).get('name'),
                    'season': season,
                    'status': fixture_info.get('status', {}).get('long', 'Unknown'),
                    'referee': fixture_info.get('referee'),
                    'league_id': league_id
                }
                
                # Insert match
                match_id = db_manager.insert_match(match_data)
                if match_id:
                    imported_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to import fixture {fixture_info.get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"✅ Successfully imported {imported_count} league matches")
        return imported_count
        
    except Exception as e:
        logger.error(f"💥 Filtered import failed: {e}")
        return 0

def import_europe_filtered():
    """Import European leagues with filtered matches only."""
    try:
        logger.info("🚀 IMPORTING EUROPEAN LEAGUES - FILTERED")
        logger.info("🔧 Only importing actual league matches, no cup/external matches")
        
        # Initialize services
        importer = DataImporter()
        league_manager = get_league_manager()
        db_manager = get_db_manager()
        
        # Focus on major European leagues first
        major_countries = ['Spain', 'Italy', 'France', 'England', 'Germany']
        
        all_leagues = league_manager.get_active_leagues()
        major_leagues = [
            league for league in all_leagues 
            if league.country in major_countries
        ]
        
        # Sort by priority
        major_leagues.sort(key=lambda x: x.priority_order)
        
        logger.info(f"🇪🇺 Processing {len(major_leagues)} major European leagues")
        
        successful = []
        failed = []
        total_api_calls = 0
        current_season = 2025
        
        for i, league in enumerate(major_leagues, 1):
            try:
                logger.info(f"\n📍 [{i}/{len(major_leagues)}] {league.country}: {league.name}")
                logger.info("-" * 50)
                
                league_api_calls = 0
                
                # Step 1: Teams
                teams_count = importer.import_teams(league.id, current_season)
                league_api_calls += 1
                logger.info(f"  👥 Teams: {teams_count}")
                
                if teams_count == 0:
                    logger.warning(f"  ⚠️ No teams, skipping {league.name}")
                    failed.append(f"{league.country} - {league.name} (No teams)")
                    continue
                
                # Step 2: Filtered Matches (using custom method)
                matches_count = import_league_matches_only(league.id, current_season, league)
                league_api_calls += 2  # Estimated API calls for matches
                logger.info(f"  ⚽ League matches: {matches_count}")
                
                # Step 3: Corner Statistics (limited)
                corners_count = 0
                if matches_count > 0:
                    try:
                        corners_count = importer.import_match_statistics(league.id, current_season, limit=30)
                        league_api_calls += corners_count
                        logger.info(f"  🏈 Corner stats: {corners_count}")
                    except Exception as corner_error:
                        logger.warning(f"  ⚠️ Corner stats failed: {corner_error}")
                        corners_count = 0
                
                # Step 4: Goal Statistics (limited)
                goals_count = 0
                if matches_count > 0:
                    try:
                        matches_needing_goals = db_manager.get_matches_needing_goal_stats(
                            current_season, limit=15, league_id=league.id
                        )
                        
                        if matches_needing_goals:
                            api_client = get_api_client()
                            for match in matches_needing_goals[:15]:
                                try:
                                    fixture_data = api_client.get_fixture_details(match[0])
                                    league_api_calls += 1
                                    
                                    if fixture_data:
                                        home_goals = fixture_data.get('home_goals')
                                        away_goals = fixture_data.get('away_goals')
                                        
                                        if home_goals is not None and away_goals is not None:
                                            home_goals_int = int(home_goals) if str(home_goals).isdigit() else 0
                                            away_goals_int = int(away_goals) if str(away_goals).isdigit() else 0
                                            
                                            if db_manager.update_match_goals(match[1], home_goals_int, away_goals_int):
                                                goals_count += 1
                                                
                                except Exception:
                                    continue
                                    
                        logger.info(f"  ⚽ Goal stats: {goals_count}")
                        
                    except Exception as goal_error:
                        logger.warning(f"  ⚠️ Goal stats failed: {goal_error}")
                        
                # Success
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
                
                # Rate limiting
                if total_api_calls > 0 and total_api_calls % 50 == 0:
                    logger.info(f"⏳ API checkpoint: {total_api_calls} calls, pausing 11 seconds...")
                    time.sleep(11)
                    
            except Exception as e:
                logger.error(f"❌ {league.country} - {league.name} failed: {e}")
                failed.append(f"{league.country} - {league.name}")
                continue
                
        # Final summary
        logger.info(f"\n🏆 FILTERED EUROPEAN IMPORT RESULTS")
        logger.info("=" * 50)
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        logger.info(f"🔌 Total API calls: {total_api_calls}")
        
        if successful:
            logger.info(f"\n✅ Successfully imported:")
            total_teams = sum(l['teams'] for l in successful)
            total_matches = sum(l['matches'] for l in successful)
            total_corners = sum(l['corners'] for l in successful)
            total_goals = sum(l['goals'] for l in successful)
            
            for league in successful:
                logger.info(f"  🇪🇺 {league['country']}: {league['name']}")
                logger.info(f"     {league['teams']}T, {league['matches']}M, {league['corners']}C, {league['goals']}G")
                
            logger.info(f"\n📊 GRAND TOTALS:")
            logger.info(f"  🏆 Teams: {total_teams}")
            logger.info(f"  ⚽ Matches: {total_matches}")  
            logger.info(f"  🏈 Corner stats: {total_corners}")
            logger.info(f"  ⚽ Goal stats: {total_goals}")
        
        if failed:
            logger.info(f"\n❌ Failed leagues:")
            for failure in failed:
                logger.info(f"  - {failure}")
                
        return len(successful) > 0
        
    except Exception as e:
        logger.error(f"💥 Filtered European import failed: {e}")
        return False

if __name__ == "__main__":
    success = import_europe_filtered()
    if success:
        logger.info("🏆 Filtered European import completed!")
    else:
        logger.error("🚨 Filtered European import failed")
