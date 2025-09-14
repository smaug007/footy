"""
Data import scripts for China Super League corner prediction system.
Imports teams, matches, and statistics from API-Football into local database.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from data.api_client import get_api_client, APIException
from data.database import get_db_manager
from config import Config

logger = logging.getLogger(__name__)

class DataImporter:
    """Import China Super League data from API-Football to local database."""
    
    def __init__(self):
        self.api_client = get_api_client()
        self.db_manager = get_db_manager()
        self.imported_counts = {
            'teams': 0,
            'matches': 0,
            'statistics': 0,
            'errors': 0
        }
        
    def import_season_data(self, league_id: int, season: int, import_matches: bool = True, 
                          import_statistics: bool = True) -> Dict:
        """Import complete season data for any league (teams, matches, statistics)."""
        from data.league_manager import get_league_manager
        league_manager = get_league_manager()
        league_config = league_manager.get_league_by_id(league_id)
        
        if not league_config:
            logger.error(f"League {league_id} not found")
            return self.imported_counts
        
        logger.info(f"Starting import for {league_config.name} season {season}")
        
        try:
            # Step 1: Import teams
            teams_imported = self.import_teams(league_id, season)
            logger.info(f"Imported {teams_imported} teams for {league_config.name} season {season}")
            
            if import_matches:
                # Step 2: Import matches
                matches_imported = self.import_matches(league_id, season)
                logger.info(f"Imported {matches_imported} matches for {league_config.name} season {season}")
                
                if import_statistics:
                    # Step 3: Import match statistics (corners)
                    stats_imported = self.import_match_statistics(league_id, season)
                    logger.info(f"Imported statistics for {stats_imported} matches")
            
            logger.info(f"{league_config.name} season {season} import completed successfully")
            return self.imported_counts
            
        except Exception as e:
            logger.error(f"Failed to import {league_config.name} season {season} data: {e}")
            self.imported_counts['errors'] += 1
            raise
    
    def import_league_data(self, league_id: int, season: int = None):
        """Import complete data for specific league (MULTI-LEAGUE SUPPORT)."""
        from data.league_manager import get_league_manager
        league_manager = get_league_manager()
        league_config = league_manager.get_league_by_id(league_id)
        
        if not league_config:
            logger.error(f"League {league_id} not found")
            return None
        
        if not season:
            season = league_manager.get_current_season(league_id)
            
        logger.info(f"Importing league data: {league_config.name} season {season}")
        
        # Reset counters for this league import
        self.imported_counts = {'teams': 0, 'matches': 0, 'statistics': 0, 'errors': 0}
        
        # Import teams with league_id
        teams_imported = self.import_teams(league_id, season)
        
        # Import matches with league_id  
        matches_imported = self.import_matches(league_id, season)
        
        # Import statistics with league_id
        stats_imported = self.import_match_statistics(league_id, season)
        
        return {
            'league_id': league_id,
            'league_name': league_config.name,
            'season': season,
            'teams_imported': teams_imported,
            'matches_imported': matches_imported,
            'stats_imported': stats_imported
        }
    
    def import_teams(self, league_id: int, season: int) -> int:
        """Import teams for any league and season."""
        try:
            # Get league config for API league ID
            from data.league_manager import get_league_manager
            league_manager = get_league_manager()
            league_config = league_manager.get_league_by_id(league_id)
            
            if not league_config:
                logger.error(f"League {league_id} not found")
                return 0
            
            # Get teams from API using generic method
            teams_response = self.api_client.get_league_teams(league_config.api_league_id, season)
            teams_data = teams_response.get('response', [])
            
            if not teams_data:
                logger.warning(f"No teams found for {league_config.name} season {season}")
                return 0
            
            imported_count = 0
            
            for team_data in teams_data:
                try:
                    team_info = team_data.get('team', {})
                    venue_info = team_data.get('venue', {})
                    
                    # Prepare team data for database (with league_id)
                    db_team_data = {
                        'api_team_id': team_info.get('id'),
                        'name': team_info.get('name'),
                        'code': team_info.get('code'),
                        'country': team_info.get('country', league_config.country),
                        'logo_url': team_info.get('logo'),
                        'founded': team_info.get('founded'),
                        'venue_name': venue_info.get('name'),
                        'venue_capacity': venue_info.get('capacity'),
                        'venue_city': venue_info.get('city'),
                        'season': season,
                        'league_id': league_id  # MULTI-LEAGUE SUPPORT
                    }
                    
                    # Insert/update team in database
                    team_id = self.db_manager.insert_team(db_team_data)
                    imported_count += 1
                    
                    logger.debug(f"Imported team: {team_info.get('name')} to {league_config.name} (ID: {team_id})")
                    
                except Exception as e:
                    logger.error(f"Failed to import team {team_info.get('name', 'Unknown')}: {e}")
                    self.imported_counts['errors'] += 1
                    continue
            
            self.imported_counts['teams'] = imported_count
            logger.info(f"Imported {imported_count} teams for {league_config.name} season {season}")
            return imported_count
            
        except APIException as e:
            logger.error(f"API error importing teams for league {league_id} season {season}: {e}")
            raise
    
    def import_matches(self, league_id: int, season: int) -> int:
        """Import matches for any league and season."""
        try:
            # Get league config for API league ID
            from data.league_manager import get_league_manager
            league_manager = get_league_manager()
            league_config = league_manager.get_league_by_id(league_id)
            
            if not league_config:
                logger.error(f"League {league_id} not found")
                return 0
            
            # Get fixtures from API using generic method
            fixtures_response = self.api_client.get_league_fixtures(league_config.api_league_id, season)
            fixtures_data = fixtures_response.get('response', [])
            
            if not fixtures_data:
                logger.warning(f"No fixtures found for {league_config.name} season {season}")
                return 0
            
            imported_count = 0
            
            for fixture_data in fixtures_data:
                try:
                    fixture_info = fixture_data.get('fixture', {})
                    teams_info = fixture_data.get('teams', {})
                    
                    # Get team IDs from database (league-specific lookup)
                    home_team_api_id = teams_info.get('home', {}).get('id')
                    away_team_api_id = teams_info.get('away', {}).get('id')
                    
                    # Find teams within this league and season
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.execute("""
                            SELECT id, name FROM teams 
                            WHERE api_team_id = ? AND league_id = ? AND season = ?
                        """, (home_team_api_id, league_id, season))
                        home_team = cursor.fetchone()
                        home_team = dict(home_team) if home_team else None
                        
                        cursor = conn.execute("""
                            SELECT id, name FROM teams 
                            WHERE api_team_id = ? AND league_id = ? AND season = ?
                        """, (away_team_api_id, league_id, season))
                        away_team = cursor.fetchone()
                        away_team = dict(away_team) if away_team else None
                    
                    if not home_team or not away_team:
                        logger.warning(f"Teams not found for fixture {fixture_info.get('id')} in {league_config.name}")
                        continue
                    
                    # Prepare match data for database (with league_id)
                    db_match_data = {
                        'api_fixture_id': fixture_info.get('id'),
                        'home_team_id': home_team['id'],
                        'away_team_id': away_team['id'],
                        'match_date': fixture_info.get('date'),
                        'venue_name': fixture_info.get('venue', {}).get('name'),
                        'season': season,
                        'status': fixture_info.get('status', {}).get('short', 'NS'),
                        'referee': fixture_info.get('referee'),
                        'league_id': league_id,  # MULTI-LEAGUE SUPPORT
                        'corners_home': None,  # Will be updated with statistics
                        'corners_away': None   # Will be updated with statistics
                    }
                    
                    # Insert/update match in database
                    match_id = self.db_manager.insert_match(db_match_data)
                    imported_count += 1
                    
                    logger.debug(f"Imported match: {home_team['name']} vs {away_team['name']} to {league_config.name} (ID: {match_id})")
                    
                except Exception as e:
                    logger.error(f"Failed to import fixture {fixture_info.get('id', 'Unknown')}: {e}")
                    self.imported_counts['errors'] += 1
                    continue
            
            self.imported_counts['matches'] = imported_count
            logger.info(f"Imported {imported_count} matches for {league_config.name} season {season}")
            return imported_count
            
        except APIException as e:
            logger.error(f"API error importing matches for league {league_id} season {season}: {e}")
            raise
    
    def import_match_statistics(self, league_id: int, season: int, limit: int = None) -> int:
        """Import match statistics (corners) for completed matches in specific league using correct API approach."""
        try:
            # Get league config
            from data.league_manager import get_league_manager
            league_manager = get_league_manager()
            league_config = league_manager.get_league_by_id(league_id)
            
            if not league_config:
                logger.error(f"League {league_id} not found")
                return 0
            
            # Get completed matches from database that don't have corner data yet (league-specific)
            completed_matches = self.db_manager.get_matches_needing_corner_stats(league_id, season, limit)
            
            if not completed_matches:
                logger.info(f"No completed matches found for {league_config.name} season {season}")
                return 0
            
            imported_count = 0
            
            for match in completed_matches:
                # Skip if corners already imported
                if match['corners_home'] is not None:
                    continue
                
                try:
                    # Use the corner-specific API method
                    corner_data = self.api_client.get_fixture_corner_statistics(match['api_fixture_id'])
                    
                    if not corner_data or corner_data['home_corners'] is None:
                        logger.debug(f"No corner statistics found for match {match['api_fixture_id']} in {league_config.name}")
                        continue
                    
                    # Update match with corner data
                    success = self.db_manager.update_match_corners(
                        match['id'],
                        corner_data['home_corners'],
                        corner_data['away_corners']
                    )
                    
                    if success:
                        imported_count += 1
                        logger.debug(f"Updated {league_config.name} match {match['api_fixture_id']} with corners: {corner_data['home_corners']}-{corner_data['away_corners']}")
                    else:
                        logger.warning(f"Failed to update match {match['api_fixture_id']} with corner data")
                
                except Exception as e:
                    logger.error(f"Error importing statistics for match {match['api_fixture_id']}: {e}")
                    continue
            
            self.imported_counts['statistics'] = imported_count
            logger.info(f"Imported corner statistics for {imported_count} matches in {league_config.name} season {season}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing match statistics for {league_config.name if league_config else league_id} season {season}: {e}")
            raise
    
    def import_recent_matches(self, days: int = 7) -> int:
        """Import recent matches and their statistics."""
        try:
            # This would typically get recent fixtures, but for CSL we'll focus on completed matches
            current_season = datetime.now().year
            return self.import_match_statistics(current_season, limit=days * 5)  # Approximate
            
        except Exception as e:
            logger.error(f"Failed to import recent matches: {e}")
            raise
    
    def verify_data_integrity(self, season: int) -> Dict:
        """Verify imported data integrity."""
        try:
            stats = self.db_manager.get_database_stats()
            
            # Get season-specific counts
            teams = self.db_manager.get_teams_by_season(season)
            matches = self.db_manager.get_completed_matches(season)
            
            # Count matches with corner data
            matches_with_corners = sum(1 for m in matches if m['corners_home'] is not None)
            
            verification = {
                'season': season,
                'teams_count': len(teams),
                'total_matches': len(matches),
                'matches_with_corners': matches_with_corners,
                'corner_data_percentage': (matches_with_corners / len(matches) * 100) if matches else 0,
                'database_stats': stats
            }
            
            logger.info(f"Data verification for season {season}: {verification}")
            return verification
            
        except Exception as e:
            logger.error(f"Failed to verify data integrity: {e}")
            raise
    
    def get_import_summary(self) -> Dict:
        """Get summary of import operation."""
        return {
            'imported_counts': self.imported_counts,
            'total_imported': sum(v for k, v in self.imported_counts.items() if k != 'errors'),
            'error_count': self.imported_counts['errors'],
            'success_rate': (
                (sum(v for k, v in self.imported_counts.items() if k != 'errors') / 
                 max(1, sum(self.imported_counts.values()))) * 100
            )
        }

# Convenience functions
def import_current_season(include_statistics: bool = True) -> Dict:
    """Import current season data."""
    importer = DataImporter()
    current_season = datetime.now().year
    return importer.import_season_data(current_season, True, include_statistics)

def import_season(season: int, include_statistics: bool = True) -> Dict:
    """Import specific season data."""
    importer = DataImporter()
    return importer.import_season_data(season, True, include_statistics)

def update_recent_statistics() -> Dict:
    """Update statistics for recent matches."""
    importer = DataImporter()
    return importer.import_recent_matches()

def verify_database(season: int = None) -> Dict:
    """Verify database integrity."""
    importer = DataImporter()
    if season is None:
        season = datetime.now().year
    return importer.verify_data_integrity(season)
