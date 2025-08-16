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
        
    def import_season_data(self, season: int, import_matches: bool = True, 
                          import_statistics: bool = True) -> Dict:
        """Import complete season data (teams, matches, statistics)."""
        logger.info(f"Starting import for season {season}")
        
        try:
            # Step 1: Import teams
            teams_imported = self.import_teams(season)
            logger.info(f"Imported {teams_imported} teams for season {season}")
            
            if import_matches:
                # Step 2: Import matches
                matches_imported = self.import_matches(season)
                logger.info(f"Imported {matches_imported} matches for season {season}")
                
                if import_statistics:
                    # Step 3: Import match statistics (corners)
                    stats_imported = self.import_match_statistics(season)
                    logger.info(f"Imported statistics for {stats_imported} matches")
            
            logger.info(f"Season {season} import completed successfully")
            return self.imported_counts
            
        except Exception as e:
            logger.error(f"Failed to import season {season} data: {e}")
            self.imported_counts['errors'] += 1
            raise
    
    def import_teams(self, season: int) -> int:
        """Import CSL teams for a season."""
        try:
            # Get teams from API
            teams_response = self.api_client.get_china_super_league_teams(season)
            teams_data = teams_response.get('response', [])
            
            if not teams_data:
                logger.warning(f"No teams found for season {season}")
                return 0
            
            imported_count = 0
            
            for team_data in teams_data:
                try:
                    team_info = team_data.get('team', {})
                    venue_info = team_data.get('venue', {})
                    
                    # Prepare team data for database
                    db_team_data = {
                        'api_team_id': team_info.get('id'),
                        'name': team_info.get('name'),
                        'code': team_info.get('code'),
                        'country': team_info.get('country', 'China'),
                        'logo_url': team_info.get('logo'),
                        'founded': team_info.get('founded'),
                        'venue_name': venue_info.get('name'),
                        'venue_capacity': venue_info.get('capacity'),
                        'venue_city': venue_info.get('city'),
                        'season': season
                    }
                    
                    # Insert/update team in database
                    team_id = self.db_manager.insert_team(db_team_data)
                    imported_count += 1
                    
                    logger.debug(f"Imported team: {team_info.get('name')} (ID: {team_id})")
                    
                except Exception as e:
                    logger.error(f"Failed to import team {team_info.get('name', 'Unknown')}: {e}")
                    self.imported_counts['errors'] += 1
                    continue
            
            self.imported_counts['teams'] = imported_count
            return imported_count
            
        except APIException as e:
            logger.error(f"API error importing teams for season {season}: {e}")
            raise
    
    def import_matches(self, season: int) -> int:
        """Import CSL matches for a season."""
        try:
            # Get fixtures from API
            fixtures_response = self.api_client.get_china_super_league_fixtures(season)
            fixtures_data = fixtures_response.get('response', [])
            
            if not fixtures_data:
                logger.warning(f"No fixtures found for season {season}")
                return 0
            
            imported_count = 0
            
            for fixture_data in fixtures_data:
                try:
                    fixture_info = fixture_data.get('fixture', {})
                    teams_info = fixture_data.get('teams', {})
                    
                    # Get team IDs from database
                    home_team_api_id = teams_info.get('home', {}).get('id')
                    away_team_api_id = teams_info.get('away', {}).get('id')
                    
                    home_team = self.db_manager.get_team_by_api_id(home_team_api_id, season)
                    away_team = self.db_manager.get_team_by_api_id(away_team_api_id, season)
                    
                    if not home_team or not away_team:
                        logger.warning(f"Teams not found for fixture {fixture_info.get('id')}")
                        continue
                    
                    # Prepare match data for database
                    db_match_data = {
                        'api_fixture_id': fixture_info.get('id'),
                        'home_team_id': home_team['id'],
                        'away_team_id': away_team['id'],
                        'match_date': fixture_info.get('date'),
                        'venue_name': fixture_info.get('venue', {}).get('name'),
                        'season': season,
                        'status': fixture_info.get('status', {}).get('short', 'NS'),
                        'referee': fixture_info.get('referee'),
                        'corners_home': None,  # Will be updated with statistics
                        'corners_away': None   # Will be updated with statistics
                    }
                    
                    # Insert/update match in database
                    match_id = self.db_manager.insert_match(db_match_data)
                    imported_count += 1
                    
                    logger.debug(f"Imported match: {home_team['name']} vs {away_team['name']} (ID: {match_id})")
                    
                except Exception as e:
                    logger.error(f"Failed to import fixture {fixture_info.get('id', 'Unknown')}: {e}")
                    self.imported_counts['errors'] += 1
                    continue
            
            self.imported_counts['matches'] = imported_count
            return imported_count
            
        except APIException as e:
            logger.error(f"API error importing matches for season {season}: {e}")
            raise
    
    def import_match_statistics(self, season: int, limit: int = None) -> int:
        """Import match statistics (corners) for completed matches."""
        try:
            # Get completed matches from database that don't have corner data yet
            completed_matches = self.db_manager.get_completed_matches(season, limit)
            
            if not completed_matches:
                logger.info(f"No completed matches found for season {season}")
                return 0
            
            imported_count = 0
            
            for match in completed_matches:
                # Skip if corners already imported
                if match['corners_home'] is not None:
                    continue
                
                try:
                    # Get match statistics from API
                    stats_response = self.api_client.get_fixture_statistics(match['api_fixture_id'])
                    stats_data = stats_response.get('response', [])
                    
                    if not stats_data:
                        logger.debug(f"No statistics found for match {match['api_fixture_id']}")
                        continue
                    
                    # Extract corner statistics
                    corners_home = None
                    corners_away = None
                    
                    for team_stats in stats_data:
                        team_id = team_stats.get('team', {}).get('id')
                        statistics = team_stats.get('statistics', [])
                        
                        # Find corner kicks statistic
                        for stat in statistics:
                            if stat.get('type') == 'Corner Kicks':
                                corner_value = stat.get('value')
                                if corner_value is not None:
                                    # Convert to integer if it's a string
                                    try:
                                        corner_count = int(corner_value)
                                        
                                        # Determine if home or away team
                                        home_team = self.db_manager.get_team_by_api_id(
                                            match['home_team_id'], season
                                        )
                                        if home_team and home_team.get('api_team_id') == team_id:
                                            corners_home = corner_count
                                        else:
                                            corners_away = corner_count
                                    except (ValueError, TypeError):
                                        logger.warning(f"Invalid corner value: {corner_value}")
                    
                    # Update match with corner statistics
                    if corners_home is not None and corners_away is not None:
                        updated_match_data = {
                            'api_fixture_id': match['api_fixture_id'],
                            'home_team_id': match['home_team_id'],
                            'away_team_id': match['away_team_id'],
                            'match_date': match['match_date'],
                            'venue_name': match['venue_name'],
                            'corners_home': corners_home,
                            'corners_away': corners_away,
                            'season': season,
                            'status': match['status'],
                            'referee': match['referee']
                        }
                        
                        self.db_manager.insert_match(updated_match_data)
                        imported_count += 1
                        
                        logger.debug(f"Updated match statistics: {match['home_team_name']} {corners_home} - {corners_away} {match['away_team_name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to import statistics for match {match['api_fixture_id']}: {e}")
                    self.imported_counts['errors'] += 1
                    continue
            
            self.imported_counts['statistics'] = imported_count
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing match statistics for season {season}: {e}")
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
