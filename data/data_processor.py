"""
Data analysis and processing engine for China Super League corner prediction system.
Handles historical data collection, team statistics calculation, and data validation.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from data.database import get_db_manager
from data.api_client import get_api_client
from data.data_importer import DataImporter
from config import Config
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TeamCornerStats:
    """Data class for team corner statistics."""
    team_id: int
    team_name: str
    season: int
    matches_analyzed: int
    
    # Corners won statistics
    corners_won_avg: float
    corners_won_consistency: float
    corners_won_trend: str
    corners_won_reliability_threshold: float
    corners_won_recent_form: List[int]
    
    # Corners conceded statistics  
    corners_conceded_avg: float
    corners_conceded_consistency: float
    corners_conceded_trend: str
    corners_conceded_reliability_threshold: float
    corners_conceded_recent_form: List[int]
    
    # Additional metrics
    home_away_split: Dict[str, float]
    vs_top_teams: Dict[str, float]
    vs_bottom_teams: Dict[str, float]

class CSLDataProcessor:
    """China Super League data processor for corner prediction analysis."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.api_client = get_api_client()
        self.data_importer = DataImporter()
        self.min_games = Config.MIN_GAMES_FOR_PREDICTION
        self.max_games = Config.MAX_GAMES_FOR_ANALYSIS
        
        logger.info("CSL Data Processor initialized")
    
    def fetch_and_process_season_data(self, season: int, force_refresh: bool = False) -> Dict:
        """Fetch and process complete season data for analysis."""
        logger.info(f"Processing season {season} data (force_refresh={force_refresh})")
        
        try:
            # Step 1: Ensure we have basic data (teams and matches)
            data_status = self._ensure_season_data(season, force_refresh)
            
            # Step 2: Import corner statistics for analysis
            corner_stats_status = self._import_corner_statistics(season)
            
            # Step 3: Validate data quality
            validation_results = self._validate_season_data(season)
            
            # Step 4: Generate summary
            processing_summary = {
                'season': season,
                'data_status': data_status,
                'corner_stats_status': corner_stats_status,
                'validation_results': validation_results,
                'teams_available': len(self._get_teams_with_sufficient_data(season)),
                'ready_for_analysis': validation_results['sufficient_for_analysis']
            }
            
            logger.info(f"Season {season} processing completed: {processing_summary}")
            return processing_summary
            
        except Exception as e:
            logger.error(f"Failed to process season {season} data: {e}")
            raise
    
    def _ensure_season_data(self, season: int, force_refresh: bool) -> Dict:
        """Ensure we have teams and matches data for the season."""
        db_stats = self.db_manager.get_database_stats()
        
        # Check if we already have data
        teams_count = len(self.db_manager.get_teams_by_season(season))
        matches_count = len(self.db_manager.get_completed_matches(season))
        
        if force_refresh or teams_count == 0:
            logger.info(f"Importing teams and matches for season {season}")
            
            # Import teams
            teams_imported = self.data_importer.import_teams(season)
            
            # Import matches
            matches_imported = self.data_importer.import_matches(season)
            
            return {
                'teams_imported': teams_imported,
                'matches_imported': matches_imported,
                'forced_refresh': force_refresh
            }
        else:
            return {
                'teams_imported': 0,
                'matches_imported': 0,
                'existing_teams': teams_count,
                'existing_matches': matches_count,
                'forced_refresh': False
            }
    
    def _import_corner_statistics(self, season: int, limit: int = None) -> Dict:
        """Import corner statistics for matches that don't have them."""
        # Get matches without corner statistics
        with self.db_manager.get_connection() as conn:
            if limit:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM matches 
                    WHERE season = ? AND status = 'FT' AND corners_home IS NULL
                    LIMIT ?
                """, (season, limit))
            else:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM matches 
                    WHERE season = ? AND status = 'FT' AND corners_home IS NULL
                """, (season,))
            
            matches_needing_stats = cursor.fetchone()[0]
        
        if matches_needing_stats == 0:
            return {'matches_needing_stats': 0, 'stats_imported': 0, 'message': 'All matches have corner statistics'}
        
        # Import statistics (with rate limiting consideration)
        import_limit = min(matches_needing_stats, limit or 20)  # Limit to avoid excessive API calls
        stats_imported = self.data_importer.import_match_statistics(season, import_limit)
        
        return {
            'matches_needing_stats': matches_needing_stats,
            'stats_imported': stats_imported,
            'import_limit_applied': import_limit,
            'message': f'Imported corner statistics for {stats_imported} matches'
        }
    
    def _validate_season_data(self, season: int) -> Dict:
        """Validate that we have sufficient data for analysis."""
        teams = self.db_manager.get_teams_by_season(season)
        
        validation_results = {
            'total_teams': len(teams),
            'teams_with_matches': 0,
            'teams_with_corner_data': 0,
            'total_matches_with_corners': 0,
            'average_matches_per_team': 0,
            'sufficient_for_analysis': False,
            'team_details': []
        }
        
        teams_with_sufficient_data = 0
        total_matches_count = 0
        
        for team in teams:
            # Get matches for this team
            team_matches = self.db_manager.get_team_matches(team['id'], season)
            
            # Count matches with corner data
            matches_with_corners = sum(1 for match in team_matches 
                                     if match['corners_home'] is not None)
            
            team_detail = {
                'team_name': team['name'],
                'total_matches': len(team_matches),
                'matches_with_corners': matches_with_corners,
                'sufficient_data': matches_with_corners >= self.min_games
            }
            
            validation_results['team_details'].append(team_detail)
            total_matches_count += len(team_matches)
            
            if len(team_matches) > 0:
                validation_results['teams_with_matches'] += 1
            
            if matches_with_corners > 0:
                validation_results['teams_with_corner_data'] += 1
            
            if matches_with_corners >= self.min_games:
                teams_with_sufficient_data += 1
        
        # Calculate overall metrics
        if validation_results['total_teams'] > 0:
            validation_results['average_matches_per_team'] = total_matches_count / validation_results['total_teams']
        
        # Get total matches with corner data across all teams
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM matches 
                WHERE season = ? AND corners_home IS NOT NULL AND corners_away IS NOT NULL
            """, (season,))
            validation_results['total_matches_with_corners'] = cursor.fetchone()[0]
        
        # Determine if we have sufficient data for analysis
        validation_results['sufficient_for_analysis'] = (
            teams_with_sufficient_data >= 4 and  # At least 4 teams with sufficient data
            validation_results['total_matches_with_corners'] >= 10  # At least 10 matches with corner data
        )
        
        return validation_results
    
    def _get_teams_with_sufficient_data(self, season: int) -> List[Dict]:
        """Get teams that have sufficient data for analysis."""
        teams = self.db_manager.get_teams_by_season(season)
        sufficient_teams = []
        
        for team in teams:
            team_matches = self.db_manager.get_team_matches(team['id'], season)
            matches_with_corners = sum(1 for match in team_matches 
                                     if match['corners_home'] is not None)
            
            if matches_with_corners >= self.min_games:
                team['matches_available'] = matches_with_corners
                sufficient_teams.append(team)
        
        return sufficient_teams
    
    def get_historical_data_summary(self, season: int) -> Dict:
        """Get comprehensive summary of historical data available."""
        try:
            teams = self.db_manager.get_teams_by_season(season)
            
            if not teams:
                return {
                    'season': season,
                    'status': 'no_data',
                    'message': f'No teams found for season {season}'
                }
            
            # Analyze data availability
            data_summary = {
                'season': season,
                'total_teams': len(teams),
                'teams_analysis': [],
                'overall_stats': {
                    'total_matches': 0,
                    'matches_with_corners': 0,
                    'average_corners_per_match': 0,
                    'teams_ready_for_analysis': 0
                }
            }
            
            total_corners = 0
            matches_with_corners_count = 0
            
            for team in teams:
                team_matches = self.db_manager.get_team_matches(team['id'], season, self.max_games)
                matches_with_corners = [m for m in team_matches if m['corners_home'] is not None]
                
                team_analysis = {
                    'team_name': team['name'],
                    'api_team_id': team['api_team_id'],
                    'total_matches': len(team_matches),
                    'matches_with_corners': len(matches_with_corners),
                    'data_quality': 'sufficient' if len(matches_with_corners) >= self.min_games else 'insufficient',
                    'corner_stats': None
                }
                
                # Calculate basic corner statistics if we have data
                if matches_with_corners:
                    corners_won = []
                    corners_conceded = []
                    
                    for match in matches_with_corners:
                        if match['home_team_id'] == team['id']:
                            # Team is home
                            corners_won.append(match['corners_home'])
                            corners_conceded.append(match['corners_away'])
                        else:
                            # Team is away
                            corners_won.append(match['corners_away'])
                            corners_conceded.append(match['corners_home'])
                    
                    if corners_won:
                        team_analysis['corner_stats'] = {
                            'avg_corners_won': round(np.mean(corners_won), 2),
                            'avg_corners_conceded': round(np.mean(corners_conceded), 2),
                            'corners_won_range': f"{min(corners_won)}-{max(corners_won)}",
                            'corners_conceded_range': f"{min(corners_conceded)}-{max(corners_conceded)}"
                        }
                        
                        total_corners += sum(corners_won) + sum(corners_conceded)
                        matches_with_corners_count += len(matches_with_corners)
                
                data_summary['teams_analysis'].append(team_analysis)
                data_summary['overall_stats']['total_matches'] += len(team_matches)
                
                if len(matches_with_corners) >= self.min_games:
                    data_summary['overall_stats']['teams_ready_for_analysis'] += 1
            
            # Calculate overall statistics
            data_summary['overall_stats']['matches_with_corners'] = matches_with_corners_count
            if matches_with_corners_count > 0:
                data_summary['overall_stats']['average_corners_per_match'] = round(
                    total_corners / matches_with_corners_count, 2
                )
            
            # Determine overall status
            if data_summary['overall_stats']['teams_ready_for_analysis'] >= 4:
                data_summary['status'] = 'ready'
                data_summary['message'] = f"Ready for analysis with {data_summary['overall_stats']['teams_ready_for_analysis']} teams"
            else:
                data_summary['status'] = 'insufficient'
                data_summary['message'] = f"Need more data. Only {data_summary['overall_stats']['teams_ready_for_analysis']} teams have sufficient data"
            
            return data_summary
            
        except Exception as e:
            logger.error(f"Failed to get historical data summary for season {season}: {e}")
            raise
    
    def import_additional_corner_statistics(self, season: int, max_imports: int = 15) -> Dict:
        """Import additional corner statistics with controlled API usage."""
        try:
            logger.info(f"Importing additional corner statistics for season {season} (max: {max_imports})")
            
            # Get matches that need corner statistics
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    WHERE m.season = ? AND m.status = 'FT' AND m.corners_home IS NULL
                    ORDER BY m.match_date DESC
                    LIMIT ?
                """, (season, max_imports))
                
                matches_to_process = cursor.fetchall()
            
            if not matches_to_process:
                return {
                    'status': 'complete',
                    'message': 'All matches already have corner statistics',
                    'imported_count': 0
                }
            
            logger.info(f"Found {len(matches_to_process)} matches that need corner statistics")
            
            imported_count = 0
            error_count = 0
            
            for match in matches_to_process:
                try:
                    # Get match statistics from API
                    stats_response = self.api_client.get_fixture_statistics(match['api_fixture_id'])
                    stats_data = stats_response.get('response', [])
                    
                    if not stats_data:
                        logger.debug(f"No statistics available for match {match['api_fixture_id']}")
                        continue
                    
                    # Extract corner statistics
                    corners_home = None
                    corners_away = None
                    
                    # Get team API IDs for matching
                    home_team = self.db_manager.get_team_by_api_id(match['home_team_id'], season)
                    away_team = self.db_manager.get_team_by_api_id(match['away_team_id'], season)
                    
                    if not home_team or not away_team:
                        logger.warning(f"Could not find team data for match {match['api_fixture_id']}")
                        continue
                    
                    for team_stats in stats_data:
                        team_api_id = team_stats.get('team', {}).get('id')
                        statistics = team_stats.get('statistics', [])
                        
                        # Find corner kicks statistic
                        team_corners = None
                        for stat in statistics:
                            if stat.get('type') == 'Corner Kicks':
                                corner_value = stat.get('value')
                                if corner_value is not None:
                                    try:
                                        team_corners = int(corner_value)
                                        break
                                    except (ValueError, TypeError):
                                        continue
                        
                        if team_corners is not None:
                            # Match to home or away team
                            if team_api_id == home_team['api_team_id']:
                                corners_home = team_corners
                            elif team_api_id == away_team['api_team_id']:
                                corners_away = team_corners
                    
                    # Update database if we have both corner counts
                    if corners_home is not None and corners_away is not None:
                        with self.db_manager.get_connection() as conn:
                            conn.execute("""
                                UPDATE matches 
                                SET corners_home = ?, corners_away = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (corners_home, corners_away, match['id']))
                            conn.commit()
                        
                        imported_count += 1
                        logger.debug(f"Updated corners: {match['home_team_name']} {corners_home} - {corners_away} {match['away_team_name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to process match {match['api_fixture_id']}: {e}")
                    error_count += 1
                    continue
            
            return {
                'status': 'completed',
                'imported_count': imported_count,
                'error_count': error_count,
                'processed_matches': len(matches_to_process),
                'message': f'Successfully imported corner statistics for {imported_count} matches'
            }
            
        except Exception as e:
            logger.error(f"Failed to import additional corner statistics: {e}")
            raise

# Convenience functions
def process_season_data(season: int = None, force_refresh: bool = False) -> Dict:
    """Process season data for analysis."""
    if season is None:
        season = datetime.now().year
    
    processor = CSLDataProcessor()
    return processor.fetch_and_process_season_data(season, force_refresh)

def get_data_summary(season: int = None) -> Dict:
    """Get historical data summary."""
    if season is None:
        season = datetime.now().year
    
    processor = CSLDataProcessor()
    return processor.get_historical_data_summary(season)

def import_more_corner_stats(season: int = None, max_imports: int = 15) -> Dict:
    """Import additional corner statistics."""
    if season is None:
        season = datetime.now().year
    
    processor = CSLDataProcessor()
    return processor.import_additional_corner_statistics(season, max_imports)
