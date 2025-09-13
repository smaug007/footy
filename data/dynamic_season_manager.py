#!/usr/bin/env python3
"""
Dynamic Season Manager
Handles fetching, analyzing, and storing predictions for any season dynamically.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests
from dataclasses import dataclass

from .database import get_db_manager
from .goal_analyzer import GoalAnalyzer
from .api_client import get_api_client

logger = logging.getLogger(__name__)

@dataclass
class MatchStatus:
    """Represents the status of a match for prediction purposes."""
    match_id: int
    match_date: date
    status: str  # 'FT', 'NS', 'LIVE', etc.
    is_completed: bool
    is_upcoming: bool
    has_prediction: bool
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str

class DynamicSeasonManager:
    """Manages dynamic season data fetching, analysis, and prediction storage."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.api_client = get_api_client()
        self.goal_analyzer = GoalAnalyzer(self.db_manager, use_enhanced_storage=True)
        
    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons from the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT season 
                    FROM matches 
                    ORDER BY season DESC
                """)
                seasons = [row[0] for row in cursor.fetchall()]
                
                # Add current year if not present (for upcoming season)
                current_year = datetime.now().year
                if current_year not in seasons:
                    seasons.insert(0, current_year)
                    
                logger.info(f"Available seasons: {seasons}")
                return seasons
                
        except Exception as e:
            logger.error(f"Error getting available seasons: {e}")
            return [2024, 2025]  # Fallback
    
    def fetch_season_data_from_api(self, season: int, league_id: int = 307) -> bool:
        """Fetch complete season data from API if not already in database."""
        try:
            logger.info(f"🔄 Fetching season {season} data from API...")
            
            # Check if season data already exists
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM matches WHERE season = ?
                """, (season,))
                existing_matches = cursor.fetchone()[0]
                
            if existing_matches > 0:
                logger.info(f"✅ Season {season} data already exists ({existing_matches} matches)")
                return True
            
            # Fetch from API
            if not self.api_client:
                logger.error("API client not available")
                return False
                
            # Get fixtures for the season
            fixtures_data = self.api_client.get_league_fixtures(league_id, season)
            
            if not fixtures_data:
                logger.error(f"No fixtures data received for season {season}")
                return False
            
            # Process and store fixtures
            stored_count = 0
            for fixture in fixtures_data:
                if self._store_fixture_from_api(fixture, season):
                    stored_count += 1
            
            logger.info(f"✅ Fetched and stored {stored_count} matches for season {season}")
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"Error fetching season {season} data: {e}")
            return False
    
    def _store_fixture_from_api(self, fixture_data: Dict, season: int) -> bool:
        """Store a single fixture from API data."""
        try:
            # Extract fixture information
            fixture_id = fixture_data.get('fixture', {}).get('id')
            match_date = fixture_data.get('fixture', {}).get('date')
            status = fixture_data.get('fixture', {}).get('status', {}).get('short', 'NS')
            venue_name = fixture_data.get('fixture', {}).get('venue', {}).get('name', '')
            
            # Extract teams
            home_team = fixture_data.get('teams', {}).get('home', {})
            away_team = fixture_data.get('teams', {}).get('away', {})
            
            home_team_name = home_team.get('name', '')
            away_team_name = away_team.get('name', '')
            
            # Extract scores and statistics
            goals = fixture_data.get('goals', {})
            home_goals = goals.get('home') if status == 'FT' else None
            away_goals = goals.get('away') if status == 'FT' else None
            
            # Get or create teams
            home_team_id = self._get_or_create_team(home_team_name, home_team.get('id'))
            away_team_id = self._get_or_create_team(away_team_name, away_team.get('id'))
            
            if not home_team_id or not away_team_id:
                logger.error(f"Failed to get team IDs for {home_team_name} vs {away_team_name}")
                return False
            
            # Store match
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO matches (
                        api_fixture_id, home_team_id, away_team_id, match_date,
                        venue_name, season, status, goals_home, goals_away,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture_id, home_team_id, away_team_id, match_date,
                    venue_name, season, status, home_goals, away_goals,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
                
                logger.debug(f"Stored match: {home_team_name} vs {away_team_name} ({status})")
                return True
                
        except Exception as e:
            logger.error(f"Error storing fixture: {e}")
            return False
    
    def _get_or_create_team(self, team_name: str, api_team_id: Optional[int] = None) -> Optional[int]:
        """Get existing team ID or create new team."""
        try:
            with self.db_manager.get_connection() as conn:
                # Try to find existing team
                cursor = conn.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Create new team
                cursor = conn.execute("""
                    INSERT INTO teams (name, api_team_id, created_at, updated_at) 
                    VALUES (?, ?, ?, ?)
                """, (team_name, api_team_id, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error getting/creating team {team_name}: {e}")
            return None
    
    def analyze_season_matches(self, season: int) -> Dict[str, Any]:
        """Analyze all matches in a season and generate predictions for completed ones."""
        try:
            logger.info(f"🧠 Analyzing season {season} matches...")
            
            # Ensure season data exists
            self.fetch_season_data_from_api(season)
            
            # Get all matches for the season
            match_statuses = self.get_season_match_statuses(season)
            
            results = {
                'season': season,
                'total_matches': len(match_statuses),
                'completed_matches': 0,
                'upcoming_matches': 0,
                'predictions_generated': 0,
                'predictions_failed': 0,
                'next_fixtures': [],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Process completed matches
            for match_status in match_statuses:
                if match_status.is_completed and not match_status.has_prediction:
                    # Generate prediction for completed match
                    if self._generate_match_prediction(match_status, season):
                        results['predictions_generated'] += 1
                    else:
                        results['predictions_failed'] += 1
                        
                if match_status.is_completed:
                    results['completed_matches'] += 1
                elif match_status.is_upcoming:
                    results['upcoming_matches'] += 1
            
            # Get next fixtures for each team
            results['next_fixtures'] = self._get_next_fixtures_by_team(match_statuses)
            
            logger.info(f"✅ Season {season} analysis complete: {results['predictions_generated']} predictions generated")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing season {season}: {e}")
            return {'error': str(e), 'season': season}
    
    def get_season_match_statuses(self, season: int) -> List[MatchStatus]:
        """Get status of all matches in a season."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT m.id, m.match_date, m.status, m.home_team_id, m.away_team_id,
                           ht.name as home_team_name, at.name as away_team_name,
                           ep.id as enhanced_prediction_id
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    LEFT JOIN enhanced_predictions ep ON ep.match_id = m.id
                    WHERE m.season = ?
                    ORDER BY m.match_date
                """, (season,))
                
                matches = []
                for row in cursor.fetchall():
                    match_date = datetime.fromisoformat(row[1]).date() if row[1] else date.today()
                    is_completed = row[2] == 'FT'
                    is_upcoming = row[2] in ['NS'] and match_date >= date.today()
                    has_prediction = row[7] is not None
                    
                    matches.append(MatchStatus(
                        match_id=row[0],
                        match_date=match_date,
                        status=row[2],
                        is_completed=is_completed,
                        is_upcoming=is_upcoming,
                        has_prediction=has_prediction,
                        home_team_id=row[3],
                        away_team_id=row[4],
                        home_team_name=row[5],
                        away_team_name=row[6]
                    ))
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting season match statuses: {e}")
            return []
    
    def _generate_match_prediction(self, match_status: MatchStatus, season: int) -> bool:
        """Generate and store prediction for a completed match."""
        try:
            logger.debug(f"Generating prediction for {match_status.home_team_name} vs {match_status.away_team_name}")
            
            # Generate BTTS prediction
            btts_prediction = self.goal_analyzer.predict_btts(
                match_status.home_team_id, 
                match_status.away_team_id, 
                season
            )
            
            if not btts_prediction:
                logger.warning(f"Failed to generate BTTS prediction for match {match_status.match_id}")
                return False
            
            # Store enhanced prediction
            storage_result = self.goal_analyzer.store_enhanced_btts_prediction(
                btts_prediction=btts_prediction,
                match_id=match_status.match_id,
                home_team_id=match_status.home_team_id,
                away_team_id=match_status.away_team_id,
                season=season
            )
            
            if storage_result:
                logger.debug(f"✅ Stored prediction for match {match_status.match_id}: {btts_prediction['btts_probability']:.1f}%")
                return True
            else:
                logger.warning(f"Failed to store prediction for match {match_status.match_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating prediction for match {match_status.match_id}: {e}")
            return False
    
    def _get_next_fixtures_by_team(self, match_statuses: List[MatchStatus]) -> List[Dict]:
        """Get the next upcoming fixture for each team."""
        try:
            team_next_fixtures = {}
            
            for match in match_statuses:
                if match.is_upcoming:
                    # Check if this is the next fixture for home team
                    if match.home_team_id not in team_next_fixtures:
                        team_next_fixtures[match.home_team_id] = {
                            'team_name': match.home_team_name,
                            'next_match': match,
                            'is_home': True
                        }
                    
                    # Check if this is the next fixture for away team
                    if match.away_team_id not in team_next_fixtures:
                        team_next_fixtures[match.away_team_id] = {
                            'team_name': match.away_team_name,
                            'next_match': match,
                            'is_home': False
                        }
            
            return list(team_next_fixtures.values())
            
        except Exception as e:
            logger.error(f"Error getting next fixtures by team: {e}")
            return []
    
    def get_season_dashboard_data(self, season: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a season."""
        try:
            # Ensure season data and predictions exist
            analysis_results = self.analyze_season_matches(season)
            
            # Get enhanced predictions for the season
            from .enhanced_database_manager import get_enhanced_db_manager
            enhanced_db = get_enhanced_db_manager()
            enhanced_predictions = enhanced_db.get_enhanced_predictions_by_season(season, limit=None)
            
            # Calculate dashboard metrics
            if enhanced_predictions:
                total_predictions = len(enhanced_predictions)
                avg_btts_probability = sum(p.get('btts_probability', 0) for p in enhanced_predictions) / total_predictions
                avg_confidence = sum(p.get('confidence_score', 0) for p in enhanced_predictions) / total_predictions
            else:
                total_predictions = 0
                avg_btts_probability = 0.0
                avg_confidence = 0.0
            
            dashboard_data = {
                'season': season,
                'total_predictions': total_predictions,
                'avg_btts_probability': round(avg_btts_probability, 1),
                'avg_confidence': round(avg_confidence, 1),
                'enhanced_predictions': enhanced_predictions[:50],  # Limit for display
                'analysis_results': analysis_results,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'storage_status': 'Active' if total_predictions > 0 else 'No Data'
            }
            
            logger.info(f"Generated dashboard data for season {season}: {total_predictions} predictions")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting season dashboard data: {e}")
            return {
                'season': season,
                'error': str(e),
                'total_predictions': 0,
                'avg_btts_probability': 0.0,
                'avg_confidence': 0.0,
                'enhanced_predictions': [],
                'storage_status': 'Error'
            }
