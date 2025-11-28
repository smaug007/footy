#!/usr/bin/env python3
"""
BATCH 1: EUROPEAN LEAGUES DATA UPDATE (Windows Compatible)
==========================================================
Updates completed matches and their statistics (goals + corners) for European leagues.
Run this on Tuesday after European competitions have settled.

League Coverage: 37 European leagues
Estimated API calls: ~925 calls (well within 7500 daily limit)
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
import time
import sys
from data.database import get_db_manager
from data.api_client import APIFootballClient  
from data.league_manager import get_league_manager

# Configure logging (Windows compatible - no emojis)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'batch1_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EuropeanLeaguesUpdater:
    """Updates completed match data for European leagues"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.league_manager = get_league_manager()
        self.api_client = APIFootballClient()
        self.api_calls_used = 0
        self.leagues_processed = 0
        self.total_matches_updated = 0
        
        logger.info("EUROPEAN LEAGUES UPDATER INITIALIZED")
        logger.info(f"Update Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_european_leagues(self) -> List:
        """Get all European leagues for batch processing"""
        all_leagues = self.league_manager.get_active_leagues()
        
        # European countries (excluding MLS which was miscategorized)
        european_countries = {
            'Spain', 'Italy', 'France', 'England', 'Germany', 'Portugal', 
            'Netherlands', 'Belgium', 'Turkey', 'Russia', 'Poland', 
            'Czech Republic', 'Austria', 'Switzerland', 'Denmark', 
            'Sweden', 'Norway', 'Scotland', 'Greece'
        }
        
        european_leagues = [
            league for league in all_leagues 
            if league.country in european_countries
        ]
        
        logger.info(f"Found {len(european_leagues)} European leagues to update")
        return sorted(european_leagues, key=lambda x: x.priority_order)
    
    def update_league_completed_matches(self, league) -> Dict[str, int]:
        """Update completed matches and statistics for a specific league"""
        
        current_season = self.league_manager.get_current_season(league.id)
        logger.info(f"Processing: {league.name} ({league.country}) - Season {current_season}")
        
        results = {
            'matches_processed': 0,
            'goals_updated': 0,
            'corners_updated': 0,
            'api_calls': 0,
            'errors': 0,
            'statuses_updated': 0
        }
        
        try:
            # Step 1: Update match statuses from API (CRITICAL FIX)
            logger.info(f"   Step 1: Updating match statuses for {league.name}...")
            
            # Get ALL matches for this league/season from API to check current statuses
            api_fixtures_response = self.api_client.get_league_fixtures(league.api_league_id, current_season)
            self.api_calls_used += 1
            results['api_calls'] += 1
            
            if 'response' in api_fixtures_response and api_fixtures_response['response']:
                api_matches = api_fixtures_response['response']
                
                # Update statuses in database
                for api_match in api_matches:
                    api_match_id = api_match['fixture']['id']
                    current_status = api_match['fixture']['status']['short']
                    
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.execute("""
                            UPDATE matches 
                            SET status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE api_fixture_id = ? AND league_id = ? AND season = ?
                        """, (current_status, api_match_id, league.id, current_season))
                        
                        if cursor.rowcount > 0:
                            results['statuses_updated'] += 1
                        
                        conn.commit()
                
                logger.info(f"   SUCCESS: Updated {results['statuses_updated']} match statuses")
                
                # Small delay after status update
                time.sleep(2)
            
            # Step 2: Get completed matches needing updates (now with correct statuses)
            completed_matches_goals = self.db_manager.get_matches_needing_goal_stats(current_season, league_id=league.id)
            completed_matches_corners = self.db_manager.get_matches_needing_corner_stats(league.id, current_season)
            
            # Combine and deduplicate matches
            all_match_ids = set()
            all_match_ids.update(match[1] for match in completed_matches_goals)  # Goals: match[1] is the database ID (Tuple)
            all_match_ids.update(match['id'] for match in completed_matches_corners)  # Corners: match['id'] is the database ID (Dict)
            
            if not all_match_ids:
                logger.info(f"   SUCCESS: No matches need updates for {league.name}")
                return results
            
            logger.info(f"   Found {len(all_match_ids)} matches needing statistics updates")
            
            # Step 3: Update match statistics
            for i, match_id in enumerate(all_match_ids, 1):
                try:
                    # Get match details from database
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.execute("""
                            SELECT m.api_fixture_id, ht.name as home_team, at.name as away_team, m.match_date, m.status
                            FROM matches m
                            JOIN teams ht ON m.home_team_id = ht.id  
                            JOIN teams at ON m.away_team_id = at.id
                            WHERE m.id = ? AND m.league_id = ? AND m.season = ?
                        """, (match_id, league.id, current_season))
                        match_row = cursor.fetchone()
                    
                    if not match_row:
                        continue
                        
                    api_match_id = match_row[0]
                    home_team = match_row[1]
                    away_team = match_row[2]
                    
                    # Create display-safe team names for logging (Windows CP1252 compatible)
                    def make_display_safe(text):
                        """Convert text to Windows Command Prompt safe characters"""
                        if not text:
                            return text
                        return text.encode('ascii', 'replace').decode('ascii')
                    
                    display_match_name = f"{make_display_safe(home_team)} vs {make_display_safe(away_team)}"
                    match_name = f"{home_team} vs {away_team}"  # Keep original for processing
                    
                    logger.info(f"   [{i}/{len(all_match_ids)}] Updating: {display_match_name}")
                    
                    # Get fixture details for goals and corners
                    fixture_details = self.api_client.get_fixture_details(api_match_id)
                    self.api_calls_used += 1
                    results['api_calls'] += 1
                    
                    if fixture_details:
                        fixture_data = fixture_details
                        
                        # Extract goals (using correct API response structure)
                        goals_home = fixture_data.get('home_goals', 0)
                        goals_away = fixture_data.get('away_goals', 0)
                        
                        # Extract corners (check for corners in raw_data)
                        corners_home = 0
                        corners_away = 0
                        
                        # Try to get corners from raw_data statistics
                        raw_data = fixture_data.get('raw_data', {})
                        if 'statistics' in raw_data:
                            statistics = raw_data['statistics']
                            
                            for team_stats in statistics:
                                team_type = 'home' if team_stats.get('team', {}).get('id') == raw_data.get('teams', {}).get('home', {}).get('id') else 'away'
                                
                                for stat in team_stats.get('statistics', []):
                                    if stat.get('type') == 'Corner Kicks':
                                        corners_value = stat.get('value') or '0'
                                        corners_count = int(str(corners_value).replace('%', '').strip()) if str(corners_value).strip() else 0
                                        
                                        if team_type == 'home':
                                            corners_home = corners_count
                                        else:
                                            corners_away = corners_count
                        
                        # Update database
                        with self.db_manager.get_connection() as conn:
                            # Update goals and corners
                            cursor = conn.execute("""
                                UPDATE matches 
                                SET goals_home = ?, goals_away = ?, corners_home = ?, corners_away = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (goals_home, goals_away, corners_home, corners_away, match_id))
                            
                            if cursor.rowcount > 0:
                                results['matches_processed'] += 1
                                if goals_home is not None and goals_away is not None:
                                    results['goals_updated'] += 1
                                if corners_home > 0 or corners_away > 0:
                                    results['corners_updated'] += 1
                                    
                                logger.info(f"      SUCCESS: Updated: {goals_home}-{goals_away} (goals), {corners_home}-{corners_away} (corners)")
                            
                            conn.commit()
                    
                    # API rate limiting (every 50 calls)
                    if self.api_calls_used % 50 == 0:
                        logger.info(f"   API Rate Limit: Waiting 11 seconds... (Used {self.api_calls_used} calls)")
                        time.sleep(11)
                        
                except Exception as e:
                    logger.error(f"   ERROR: Error updating match {match_id}: {e}")
                    results['errors'] += 1
                    continue
            
            # League processing complete
            self.total_matches_updated += results['matches_processed']
            logger.info(f"   COMPLETE: {league.name} - {results['statuses_updated']} statuses, {results['matches_processed']} matches, {results['goals_updated']} goals, {results['corners_updated']} corners")
            
            # Small delay between leagues
            if len(all_match_ids) > 0:
                logger.info("   Inter-league delay: 5 seconds...")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"ERROR: Critical error processing {league.name}: {e}")
            results['errors'] += 1
            
        return results
    
    def run_batch_update(self):
        """Run the complete European leagues batch update"""
        
        logger.info("STARTING BATCH 1: EUROPEAN LEAGUES UPDATE")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        european_leagues = self.get_european_leagues()
        
        total_results = {
            'leagues_processed': 0,
            'statuses_updated': 0,
            'matches_updated': 0,
            'goals_updated': 0,
            'corners_updated': 0,
            'total_errors': 0
        }
        
        try:
            for i, league in enumerate(european_leagues, 1):
                self.leagues_processed += 1
                
                logger.info(f"\nLEAGUE {i}/{len(european_leagues)}: {league.name}")
                logger.info("-" * 60)
                
                # Update this league
                league_results = self.update_league_completed_matches(league)
                
                # Aggregate results
                total_results['leagues_processed'] += 1
                total_results['statuses_updated'] += league_results['statuses_updated']
                total_results['matches_updated'] += league_results['matches_processed']
                total_results['goals_updated'] += league_results['goals_updated']
                total_results['corners_updated'] += league_results['corners_updated']
                total_results['total_errors'] += league_results['errors']
                
                # Progress update
                logger.info(f"BATCH PROGRESS: {i}/{len(european_leagues)} leagues, {self.api_calls_used} API calls used")
        
        except KeyboardInterrupt:
            logger.warning("UPDATE INTERRUPTED BY USER")
        except Exception as e:
            logger.error(f"CRITICAL BATCH ERROR: {e}")
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "BATCH 1 COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Leagues:  {total_results['leagues_processed']}/{len(european_leagues)}")
        logger.info(f"Statuses: {total_results['statuses_updated']} updated")
        logger.info(f"Matches:  {total_results['matches_updated']} updated")
        logger.info(f"Goals:    {total_results['goals_updated']} updated")
        logger.info(f"Corners:  {total_results['corners_updated']} updated")
        logger.info(f"API:      {self.api_calls_used} calls used (limit: 7500)")
        logger.info(f"Errors:   {total_results['total_errors']}")
        logger.info("=" * 80)
        
        if total_results['total_errors'] > 0:
            logger.warning(f"Batch completed with {total_results['total_errors']} errors. Check logs for details.")
        else:
            logger.info("Batch completed successfully with no errors!")

def main():
    """Main execution function"""
    
    print("EUROPEAN LEAGUES DATA UPDATER")
    print("=" * 50)
    print("This will update completed match statistics for European leagues.")
    print("Estimated API calls: ~925 calls")
    print("Estimated time: 15-30 minutes")
    print("=" * 50)
    
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("Update cancelled.")
        sys.exit(0)
    
    try:
        updater = EuropeanLeaguesUpdater()
        updater.run_batch_update()
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
