#!/usr/bin/env python3
"""
CORNER DATA CORRECTION SCRIPT
============================
Fixes matches that have corrupted corner data (0-0 corners but real goal scores).
This script identifies matches with suspicious corner data and re-fetches corner statistics.

Target: Completed matches with goals ≠ 0-0 but corners = 0-0 (likely corrupted)
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple
import time
import sys
from data.database import get_db_manager
from data.api_client import APIFootballClient  
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'corner_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CornerDataCorrector:
    """Corrects corrupted corner data in the database"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.league_manager = get_league_manager()
        self.api_client = APIFootballClient()
        self.api_calls_used = 0
        
        logger.info("CORNER DATA CORRECTOR INITIALIZED")
        logger.info(f"Fix Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def find_corrupted_corner_matches(self) -> List[Tuple]:
        """Find matches with likely corrupted corner data (0-0 corners but real goals)"""
        
        with self.db_manager.get_connection() as conn:
            # Find completed matches where:
            # 1. Goals are NOT 0-0 (indicating real match data)  
            # 2. Corners are 0-0 (indicating corrupted/missing data)
            # 3. Match is completed (not a legitimate 0-0 corner game)
            cursor = conn.execute("""
                SELECT m.id, m.api_fixture_id, m.league_id, m.season,
                       ht.name as home_team, at.name as away_team,
                       m.goals_home, m.goals_away, m.corners_home, m.corners_away,
                       m.status, l.name as league_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id  
                JOIN teams at ON m.away_team_id = at.id
                JOIN leagues l ON m.league_id = l.id
                WHERE m.status IN ('FT', 'Match Finished', 'AET', 'PEN')
                  AND m.goals_home IS NOT NULL 
                  AND m.goals_away IS NOT NULL
                  AND (m.goals_home > 0 OR m.goals_away > 0)  -- Real match (not 0-0)
                  AND m.corners_home = 0 
                  AND m.corners_away = 0  -- Suspicious 0-0 corners
                ORDER BY m.league_id, m.match_date DESC
            """)
            return cursor.fetchall()
    
    def fix_match_corners(self, match_data: Tuple) -> bool:
        """Fix corner data for a specific match"""
        
        match_id, api_fixture_id, league_id, season, home_team, away_team, \
        goals_home, goals_away, corners_home, corners_away, status, league_name = match_data
        
        match_name = f"{home_team} vs {away_team}"
        logger.info(f"   Fixing: {match_name} ({goals_home}-{goals_away} goals, {corners_home}-{corners_away} corners)")
        
        try:
            # Get fixture details from API
            fixture_details = self.api_client.get_fixture_details(api_fixture_id)
            self.api_calls_used += 1
            
            if not fixture_details:
                logger.warning(f"   WARNING: No API data for {match_name}")
                return False
            
            # Extract corner data using the corrected logic
            new_corners_home = 0
            new_corners_away = 0
            
            raw_data = fixture_details.get('raw_data', {})
            if 'statistics' in raw_data:
                statistics = raw_data['statistics']
                
                for team_stats in statistics:
                    team_type = 'home' if team_stats.get('team', {}).get('id') == raw_data.get('teams', {}).get('home', {}).get('id') else 'away'
                    
                    for stat in team_stats.get('statistics', []):
                        if stat.get('type') == 'Corner Kicks':
                            corners_value = stat.get('value') or '0'
                            corners_count = int(str(corners_value).replace('%', '').strip()) if str(corners_value).strip() else 0
                            
                            if team_type == 'home':
                                new_corners_home = corners_count
                            else:
                                new_corners_away = corners_count
            
            # Update database with corrected corner data
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE matches 
                    SET corners_home = ?, corners_away = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_corners_home, new_corners_away, match_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"   SUCCESS: Updated to {new_corners_home}-{new_corners_away} corners")
                    conn.commit()
                    return True
                else:
                    logger.warning(f"   WARNING: Database update failed for {match_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"   ERROR: Failed to fix {match_name}: {e}")
            return False
    
    def run_corner_correction(self):
        """Main correction process"""
        
        start_time = datetime.now()
        
        print("CORNER DATA CORRECTION TOOL")
        print("=" * 50)
        print("This will fix matches with corrupted corner data (0-0 corners but real goals).")
        print("Only completed matches with suspicious corner data will be updated.")
        print("=" * 50)
        
        # Find corrupted matches
        logger.info("STEP 1: Finding matches with corrupted corner data...")
        corrupted_matches = self.find_corrupted_corner_matches()
        
        if not corrupted_matches:
            logger.info("SUCCESS: No corrupted corner data found! All matches look correct.")
            return
        
        logger.info(f"FOUND: {len(corrupted_matches)} matches with suspicious corner data")
        
        # Group by league for better reporting
        league_groups = {}
        for match in corrupted_matches:
            league_name = match[11]  # league_name is at index 11
            if league_name not in league_groups:
                league_groups[league_name] = []
            league_groups[league_name].append(match)
        
        logger.info("BREAKDOWN BY LEAGUE:")
        for league_name, matches in league_groups.items():
            logger.info(f"   {league_name}: {len(matches)} matches")
        
        # Confirmation
        confirm = input(f"\nProceed to fix {len(corrupted_matches)} matches? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y']:
            print("Corner correction cancelled.")
            return
        
        # Process corrections
        logger.info(f"STEP 2: Correcting corner data for {len(corrupted_matches)} matches...")
        logger.info("=" * 70)
        
        fixed_count = 0
        failed_count = 0
        
        for i, match_data in enumerate(corrupted_matches, 1):
            league_name = match_data[11]
            logger.info(f"[{i}/{len(corrupted_matches)}] {league_name}")
            
            success = self.fix_match_corners(match_data)
            if success:
                fixed_count += 1
            else:
                failed_count += 1
            
            # API rate limiting every 50 calls
            if self.api_calls_used % 50 == 0:
                logger.info(f"   API Rate Limit: Waiting 11 seconds... (Used {self.api_calls_used} calls)")
                time.sleep(11)
            else:
                time.sleep(0.5)  # Small delay between requests
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 70)
        logger.info("CORNER CORRECTION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Matches Fixed: {fixed_count}/{len(corrupted_matches)}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"API Calls Used: {self.api_calls_used}")
        logger.info("=" * 70)
        
        if failed_count > 0:
            logger.warning(f"Corner correction completed with {failed_count} failures. Check logs for details.")
        else:
            logger.info("Corner correction completed successfully with no failures!")

def main():
    """Main execution function"""
    try:
        corrector = CornerDataCorrector()
        corrector.run_corner_correction()
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
