"""
Goal analysis functions for BTTS (Both Teams To Score) predictions.
Provides strict venue-specific analysis for goal scoring patterns.
"""
import logging
from typing import Dict, List, Tuple, Optional
from data.database import DatabaseManager
from data.dynamic_weighting import DynamicWeightingEngine
from data.api_client import get_api_client

logger = logging.getLogger(__name__)

class GoalAnalyzer:
    """
    Analyzes team goal performance with strict venue-specific filtering.
    Provides data for BTTS predictions using dynamic weighting.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize goal analyzer with database manager and dynamic weighting."""
        self.db_manager = db_manager or DatabaseManager()
        self.weighting_engine = DynamicWeightingEngine()
        self.api_client = get_api_client()
    
    def analyze_team_goal_performance_strict_venue(self, team_id: int, season: int, venue: str) -> Dict:
        """
        Analyze team's goal performance with strict venue filtering.
        
        Args:
            team_id: Internal team ID
            season: Season year
            venue: 'home' or 'away' - only considers games at this venue
            
        Returns:
            Dictionary with goal performance metrics
        """
        try:
            # Get matches with goal data (similar to corner system approach)
            matches_with_goals = self._get_team_matches_with_goals(team_id, season, limit=20)
            
            if not matches_with_goals:
                logger.info(f"No goal data available for team {team_id} in season {season}")
                return self._get_empty_goal_performance()
            
            # Filter for venue-specific matches only
            if venue == 'home':
                venue_matches = [m for m in matches_with_goals if m['home_team_id'] == team_id]
            elif venue == 'away':
                venue_matches = [m for m in matches_with_goals if m['away_team_id'] == team_id]
            else:
                logger.error(f"Invalid venue: {venue}. Must be 'home' or 'away'")
                return self._get_empty_goal_performance()
            
            if not venue_matches:
                logger.info(f"No {venue} goal data available for team {team_id} in season {season}")
                return self._get_empty_goal_performance()
            
            # Analyze goal performance
            return self._calculate_goal_metrics(venue_matches, team_id, venue)
            
        except Exception as e:
            logger.error(f"Error analyzing goal performance for team {team_id}: {e}")
            return self._get_empty_goal_performance()
    
    def _calculate_goal_metrics(self, matches: List, team_id: int, venue: str) -> Dict:
        """Calculate goal performance metrics from matches."""
        
        total_games = len(matches)
        scores_1plus = 0
        concedes_1plus = 0
        scores_2plus = 0
        concedes_2plus = 0
        total_goals_scored = 0
        total_goals_conceded = 0
        
        for match in matches:
            home_team_id = match['home_team_id']
            goals_home = match['goals_home']
            goals_away = match['goals_away']
            
            if home_team_id == team_id:  # Team is playing at home
                team_goals = goals_home
                opponent_goals = goals_away
            else:  # Team is playing away
                team_goals = goals_away
                opponent_goals = goals_home
            
            # Count scoring patterns
            if team_goals >= 1:
                scores_1plus += 1
            if team_goals >= 2:
                scores_2plus += 1
            if opponent_goals >= 1:
                concedes_1plus += 1
            if opponent_goals >= 2:
                concedes_2plus += 1
                
            total_goals_scored += team_goals
            total_goals_conceded += opponent_goals
        
        # Calculate rates
        scores_1plus_rate = (scores_1plus / total_games) * 100 if total_games > 0 else 0
        concedes_1plus_rate = (concedes_1plus / total_games) * 100 if total_games > 0 else 0
        scores_2plus_rate = (scores_2plus / total_games) * 100 if total_games > 0 else 0
        concedes_2plus_rate = (concedes_2plus / total_games) * 100 if total_games > 0 else 0
        
        avg_goals_scored = total_goals_scored / total_games if total_games > 0 else 0
        avg_goals_conceded = total_goals_conceded / total_games if total_games > 0 else 0
        
        return {
            'team_id': team_id,
            'venue': venue,
            'total_games': total_games,
            'scores_1plus_count': scores_1plus,
            'scores_1plus_rate': round(scores_1plus_rate, 1),
            'concedes_1plus_count': concedes_1plus,
            'concedes_1plus_rate': round(concedes_1plus_rate, 1),
            'scores_2plus_count': scores_2plus,
            'scores_2plus_rate': round(scores_2plus_rate, 1),
            'concedes_2plus_count': concedes_2plus,
            'concedes_2plus_rate': round(concedes_2plus_rate, 1),
            'avg_goals_scored': round(avg_goals_scored, 2),
            'avg_goals_conceded': round(avg_goals_conceded, 2),
            'total_goals_scored': total_goals_scored,
            'total_goals_conceded': total_goals_conceded,
            'data_quality': self._assess_data_quality(total_games),
            'venue_specific': True  # Flag to indicate strict venue filtering was used
        }
    
    def predict_btts(self, home_team_id: int, away_team_id: int, season: int) -> Dict:
        """
        Predict Both Teams To Score using PURE backtesting logic (identical except current date).
        
        Args:
            home_team_id: Internal ID of home team
            away_team_id: Internal ID of away team
            season: Season year
            
        Returns:
            Dictionary with BTTS prediction and detailed reasoning
        """
        try:
            from datetime import datetime
            
            # Import backtesting functions from app.py
            from app import calculate_real_btts_breakdown, get_team_historical_goal_data_all_games, calculate_real_goal_statistics
            
            # Use current date as cutoff (only difference from backtesting)
            current_date = datetime.now().date()
            
            # Get comprehensive historical goal data (ALL games - home and away)
            home_historical = get_team_historical_goal_data_all_games(self.db_manager, home_team_id, current_date, season)
            away_historical = get_team_historical_goal_data_all_games(self.db_manager, away_team_id, current_date, season)
            
            # Check if we have sufficient data (simple check like backtesting)
            if not home_historical or not away_historical:
                return {
                    'btts_probability': 50.0,
                    'confidence': 'Low', 
                    'confidence_score': 30.0,
                    'reasoning': 'Insufficient data',
                    'home_team_score_probability': 50.0,
                    'away_team_score_probability': 50.0,
                    'home_team_reasoning': 'Insufficient data',
                    'away_team_reasoning': 'Insufficient data',
                    'home_team_stats': self._get_empty_goal_performance(),
                    'away_team_stats': self._get_empty_goal_performance(),
                    'data_quality': 'Poor',
                    'methodology': 'Pure backtesting logic with current date'
                }
            
            # Use PURE backtesting calculation - no modifications
            btts_breakdown = calculate_real_btts_breakdown(home_historical, away_historical, home_team_id, away_team_id, current_date)
            
            # Get team statistics for return data
            home_team_stats = calculate_real_goal_statistics(home_historical, home_team_id, current_date)
            away_team_stats = calculate_real_goal_statistics(away_historical, away_team_id, current_date)
            
            # Extract probabilities exactly as backtesting does
            home_probability = btts_breakdown['home_team_calculation']['attack_rate'] * btts_breakdown['home_team_calculation']['dynamic_weights'][0] + btts_breakdown['home_team_calculation']['opponent_defense_vulnerability'] * btts_breakdown['home_team_calculation']['dynamic_weights'][1]
            away_probability = btts_breakdown['away_team_calculation']['attack_rate'] * btts_breakdown['away_team_calculation']['dynamic_weights'][0] + btts_breakdown['away_team_calculation']['opponent_defense_vulnerability'] * btts_breakdown['away_team_calculation']['dynamic_weights'][1]
            
            # Use simple confidence based on data quality only (like original GoalAnalyzer)
            min_games = min(len(home_historical), len(away_historical))
            confidence_score = self._calculate_btts_confidence({'probability': home_probability}, {'probability': away_probability}, min_games)
            
            return {
                'btts_probability': round(btts_breakdown['btts_probability'], 1),
                'confidence': self._get_confidence_label(confidence_score),
                'confidence_score': confidence_score,
                'home_team_score_probability': round(home_probability, 1),
                'away_team_score_probability': round(away_probability, 1),
                'home_team_reasoning': btts_breakdown['home_team_calculation']['reasoning'],
                'away_team_reasoning': btts_breakdown['away_team_calculation']['reasoning'],
                'home_team_stats': home_team_stats,
                'away_team_stats': away_team_stats,
                'data_quality': self._assess_combined_data_quality(min_games),
                'methodology': 'Pure backtesting logic with current date'
            }
            
        except Exception as e:
            logger.error(f"Error predicting BTTS for teams {home_team_id} vs {away_team_id}: {e}")
            return {
                'btts_probability': 50.0,
                'confidence': 'Low',
                'confidence_score': 20.0,
                'reasoning': f'Prediction error: {str(e)}',
                'home_team_score_probability': 50.0,
                'away_team_score_probability': 50.0,
                'home_team_reasoning': f'Error: {str(e)}',
                'away_team_reasoning': f'Error: {str(e)}',
                'home_team_stats': self._get_empty_goal_performance(),
                'away_team_stats': self._get_empty_goal_performance(),
                'data_quality': 'Error',
                'methodology': 'Error fallback'
            }
    
    def predict_btts_2plus(self, home_team_id: int, away_team_id: int, season: int) -> Dict:
        """
        Predict Both Teams To Score 2+ Goals using PURE backtesting logic.
        
        Args:
            home_team_id: Internal ID of home team
            away_team_id: Internal ID of away team
            season: Season year
            
        Returns:
            Dictionary with BTTS 2+ prediction and detailed reasoning
        """
        try:
            from datetime import datetime
            
            # Import backtesting functions from app.py
            from app import calculate_real_btts_2plus_breakdown, get_team_historical_goal_data_all_games, calculate_real_goal_statistics
            
            # Use current date as cutoff (only difference from backtesting)
            current_date = datetime.now().date()
            
            # Get comprehensive historical goal data (ALL games - home and away)
            home_historical = get_team_historical_goal_data_all_games(self.db_manager, home_team_id, current_date, season)
            away_historical = get_team_historical_goal_data_all_games(self.db_manager, away_team_id, current_date, season)
            
            # Check if we have sufficient data (simple check like backtesting)
            if not home_historical or not away_historical:
                return {
                    'btts_2plus_probability': 50.0,
                    'confidence': 'Low', 
                    'confidence_score': 30.0,
                    'reasoning': 'Insufficient data for 2+ goals prediction',
                    'home_team_2plus_probability': 50.0,
                    'away_team_2plus_probability': 50.0,
                    'home_team_reasoning': 'Insufficient data',
                    'away_team_reasoning': 'Insufficient data',
                    'home_team_stats': self._get_empty_goal_performance(),
                    'away_team_stats': self._get_empty_goal_performance(),
                    'data_quality': 'Poor',
                    'methodology': 'Pure backtesting logic with current date - 2+ goals'
                }
            
            # Use PURE backtesting calculation for 2+ goals
            btts_2plus_breakdown = calculate_real_btts_2plus_breakdown(home_historical, away_historical, home_team_id, away_team_id, current_date)
            
            # Get team statistics for return data
            home_team_stats = calculate_real_goal_statistics(home_historical, home_team_id, current_date)
            away_team_stats = calculate_real_goal_statistics(away_historical, away_team_id, current_date)
            
            # Extract probabilities exactly as backtesting does
            home_probability = btts_2plus_breakdown['home_team_calculation']['attack_rate'] * btts_2plus_breakdown['home_team_calculation']['dynamic_weights'][0] + btts_2plus_breakdown['home_team_calculation']['opponent_defense_vulnerability'] * btts_2plus_breakdown['home_team_calculation']['dynamic_weights'][1]
            away_probability = btts_2plus_breakdown['away_team_calculation']['attack_rate'] * btts_2plus_breakdown['away_team_calculation']['dynamic_weights'][0] + btts_2plus_breakdown['away_team_calculation']['opponent_defense_vulnerability'] * btts_2plus_breakdown['away_team_calculation']['dynamic_weights'][1]
            
            # Use IDENTICAL confidence calculation as 1+ goals (same centralized method)
            min_games = min(len(home_historical), len(away_historical))
            confidence_score = self._calculate_btts_confidence({'probability': home_probability}, {'probability': away_probability}, min_games)
            
            return {
                'btts_2plus_probability': round(btts_2plus_breakdown['btts_probability'], 1),
                'confidence': self._get_confidence_label(confidence_score),
                'confidence_score': confidence_score,
                'home_team_2plus_probability': round(home_probability, 1),
                'away_team_2plus_probability': round(away_probability, 1),
                'home_team_reasoning': btts_2plus_breakdown['home_team_calculation']['reasoning'],
                'away_team_reasoning': btts_2plus_breakdown['away_team_calculation']['reasoning'],
                'home_team_stats': home_team_stats,
                'away_team_stats': away_team_stats,
                'data_quality': self._assess_combined_data_quality(min_games),
                'methodology': 'Pure backtesting logic with current date - 2+ goals'
            }
            
        except Exception as e:
            logger.error(f"Error predicting BTTS 2+ for teams {home_team_id} vs {away_team_id}: {e}")
            return {
                'btts_2plus_probability': 50.0,
                'confidence': 'Low',
                'confidence_score': 20.0,
                'reasoning': f'2+ goals prediction error: {str(e)}',
                'home_team_2plus_probability': 50.0,
                'away_team_2plus_probability': 50.0,
                'home_team_reasoning': f'Error: {str(e)}',
                'away_team_reasoning': f'Error: {str(e)}',
                'home_team_stats': self._get_empty_goal_performance(),
                'away_team_stats': self._get_empty_goal_performance(),
                'data_quality': 'Error',
                'methodology': 'Error fallback - 2+ goals'
            }
    
    def _calculate_team_scoring_probability(self, attacking_stats: Dict, defending_stats: Dict, venue: str) -> Dict:
        """Calculate team's probability to score using dynamic weighting."""
        
        attack_rate = attacking_stats['scores_1plus_rate']
        defense_vulnerability = defending_stats['concedes_1plus_rate']
        attack_games = attacking_stats['total_games']
        defense_games = defending_stats['total_games']
        
        # Calculate dynamic weights
        attack_weight, defense_weight, reasoning = self.weighting_engine.calculate_dynamic_weights(
            attack_rate, defense_vulnerability
        )
        
        # Apply sample size adjustments
        adj_attack_weight, adj_defense_weight = self.weighting_engine.adjust_weights_for_sample_size(
            attack_weight, defense_weight, attack_games, defense_games
        )
        
        # Calculate probability
        probability = (attack_rate * adj_attack_weight) + (defense_vulnerability * adj_defense_weight)
        
        # Calculate confidence boost
        confidence_boost = self.weighting_engine.calculate_confidence_boost(adj_attack_weight, adj_defense_weight)
        
        return {
            'probability': round(probability, 1),
            'attack_rate': attack_rate,
            'defense_vulnerability': defense_vulnerability,
            'weights_used': (adj_attack_weight, adj_defense_weight),
            'confidence_boost': confidence_boost,
            'reasoning': reasoning['description'],
            'venue': venue,
            'sample_adjusted': (adj_attack_weight, adj_defense_weight) != (attack_weight, defense_weight)
        }
    
    def _calculate_btts_confidence(self, home_prob: Dict, away_prob: Dict, min_games: int) -> float:
        """Calculate BTTS confidence using pure line consistency method.
        
        Works for both 1+ goals and 2+ goals predictions - uses the calculated
        probabilities after dynamic weighting is applied.
        """
        
        # Use pure line consistency instead of complex confidence boosts
        # This is the calculated probability for each team to score (after dynamic weighting)
        home_scoring_rate = home_prob['probability']  # Calculated probability (1+ or 2+ goals)
        away_scoring_rate = away_prob['probability']  # Calculated probability (1+ or 2+ goals)
        
        # Combined line consistency (average of both teams' scoring rates)
        line_consistency = (home_scoring_rate + away_scoring_rate) / 2
        
        # Sample size factor (more lenient for pure line consistency)
        if min_games >= 10:
            sample_factor = 1.0  # No penalty for 10+ games
        elif min_games >= 7:
            sample_factor = 0.95  # Very small penalty for 7-9 games
        elif min_games >= 5:
            sample_factor = 0.9   # Small penalty for 5-6 games
        else:
            sample_factor = 0.8   # Moderate penalty for <5 games
        
        # Apply sample size penalty to line consistency
        final_confidence = line_consistency * sample_factor
        
        # Only minimum limit (5% minimum, no maximum cap)
        final_confidence = max(5.0, final_confidence)
        
        return round(final_confidence, 1)
    
    def _get_confidence_label(self, confidence_score: float) -> str:
        """Convert confidence score to label."""
        if confidence_score >= 90:
            return 'Very High'
        elif confidence_score >= 75:
            return 'High'
        elif confidence_score >= 60:
            return 'Medium'
        elif confidence_score >= 40:
            return 'Low'
        else:
            return 'Very Low'
    
    def _assess_data_quality(self, games_count: int) -> str:
        """Assess data quality based on number of games."""
        if games_count >= 15:
            return 'Excellent'
        elif games_count >= 10:
            return 'Good'
        elif games_count >= 5:
            return 'Fair'
        else:
            return 'Poor'
    
    def _assess_combined_data_quality(self, min_games: int) -> str:
        """Assess combined data quality for both teams."""
        return self._assess_data_quality(min_games)
    
    def _get_empty_goal_performance(self) -> Dict:
        """Return empty goal performance structure."""
        return {
            'team_id': None,
            'venue': None,
            'total_games': 0,
            'scores_1plus_count': 0,
            'scores_1plus_rate': 0.0,
            'concedes_1plus_count': 0,
            'concedes_1plus_rate': 0.0,
            'scores_2plus_count': 0,
            'scores_2plus_rate': 0.0,
            'concedes_2plus_count': 0,
            'concedes_2plus_rate': 0.0,
            'avg_goals_scored': 0.0,
            'avg_goals_conceded': 0.0,
            'total_goals_scored': 0,
            'total_goals_conceded': 0,
            'data_quality': 'No Data',
            'venue_specific': True,
            # Additional fields for template compatibility
            'goals_per_game': 0.0,
            'goals_conceded_per_game': 0.0,
            'scoring_rate': 0.0,
            'clean_sheet_rate': 0.0,
            'home_goals_per_game': 0.0,
            'away_goals_per_game': 0.0,
            'home_scoring_rate': 0.0,
            'away_scoring_rate': 0.0,
            'home_conceded_per_game': 0.0,
            'away_conceded_per_game': 0.0,
            'home_clean_sheet_rate': 0.0,
            'away_clean_sheet_rate': 0.0,
            'strength_classification': 'Unknown'
        }
    
    def _get_team_matches_with_goals(self, team_id: int, season: int, limit: int = 20) -> List[Dict]:
        """Get team matches that have goal data (similar to corner system approach)."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.season = ? AND m.status = 'FT'
                AND m.goals_home IS NOT NULL AND m.goals_away IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (team_id, team_id, season, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_team_matches_with_goals_before_date(self, team_id: int, season: int, cutoff_date, limit: int = 20) -> List[Dict]:
        """Get team matches that have goal data BEFORE a specific cutoff date (for time-travel predictions)."""
        from datetime import date
        
        # Convert cutoff_date to date object if it's a string
        if isinstance(cutoff_date, str):
            from datetime import datetime
            cutoff_date = datetime.strptime(cutoff_date, '%Y-%m-%d').date()
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.season = ? AND m.status = 'FT'
                AND m.goals_home IS NOT NULL AND m.goals_away IS NOT NULL
                AND date(m.match_date) < ?
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (team_id, team_id, season, cutoff_date, limit))
            
            matches = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Retrieved {len(matches)} goal matches for team {team_id} before {cutoff_date}")
            return matches
    
    def _get_current_league_standings(self, season: int) -> Dict[int, Dict]:
        """Get current league standings from API-Football."""
        try:
            # Get standings from API
            standings_response = self.api_client.get_china_super_league_standings(season)
            
            if not standings_response or 'response' not in standings_response:
                logger.warning(f"No standings data from API for season {season}, using placeholder")
                return self._get_placeholder_standings(season)
            
            standings_data = standings_response.get('response', [])
            
            if not standings_data:
                logger.warning(f"Empty standings response for season {season}, using placeholder")
                return self._get_placeholder_standings(season)
            
            # Process API standings data
            standings = {}
            
            # API-Football returns standings in a nested structure
            # standings_data[0]['league']['standings'][0] contains the table
            league_standings = standings_data[0].get('league', {}).get('standings', [[]])[0]
            
            for team_standing in league_standings:
                team_data = team_standing.get('team', {})
                api_team_id = team_data.get('id')
                
                # Find our internal team ID from the API team ID
                internal_team_id = self._get_internal_team_id(api_team_id, season)
                
                if internal_team_id:
                    standings[internal_team_id] = {
                        'name': team_data.get('name', 'Unknown'),
                        'position': team_standing.get('rank', 0),
                        'points': team_standing.get('points', 0),
                        'played': team_standing.get('played', 0),
                        'won': team_standing.get('win', 0),
                        'drawn': team_standing.get('draw', 0),
                        'lost': team_standing.get('lose', 0),
                        'goals_for': team_standing.get('goals', {}).get('for', 0),
                        'goals_against': team_standing.get('goals', {}).get('against', 0),
                        'goal_difference': team_standing.get('goalsDiff', 0)
                    }
            
            logger.info(f"Retrieved current league standings for {len(standings)} teams from API")
            return standings
            
        except Exception as e:
            logger.error(f"Error getting league standings from API: {e}")
            return self._get_placeholder_standings(season)
    
    def _get_internal_team_id(self, api_team_id: int, season: int) -> Optional[int]:
        """Get internal team ID from API team ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id FROM teams 
                    WHERE api_team_id = ? AND season = ?
                """, (api_team_id, season))
                
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Error mapping API team ID {api_team_id}: {e}")
            return None
    
    def _get_placeholder_standings(self, season: int) -> Dict[int, Dict]:
        """Generate placeholder standings when goal data is not available."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get all teams for the season
                cursor = conn.execute("""
                    SELECT DISTINCT t.id, t.name
                    FROM teams t
                    JOIN matches m ON (t.id = m.home_team_id OR t.id = m.away_team_id)
                    WHERE m.season = ?
                    ORDER BY t.name
                """, (season,))
                
                teams = [dict(row) for row in cursor.fetchall()]
                
                # Create placeholder positions (alphabetical order for now)
                standings = {}
                for position, team in enumerate(teams, 1):
                    standings[team['id']] = {
                        'name': team['name'],
                        'position': position,
                        'points': 0,
                        'played': 0,
                        'won': 0,
                        'drawn': 0,
                        'lost': 0,
                        'goals_for': 0,
                        'goals_against': 0,
                        'goal_difference': 0
                    }
                
                logger.info(f"Generated placeholder standings for {len(teams)} teams")
                return standings
                
        except Exception as e:
            logger.error(f"Error generating placeholder standings: {e}")
            return {}
    
    def format_games_for_display_venue_specific(self, team_id: int, season: int, venue: str, limit: int = 10) -> List[Dict]:
        """Format team games for display with venue-specific filtering and opponent positions."""
        
        try:
            # Get all games first
            all_games = self._get_team_matches_with_goals(team_id, season, limit * 2)  # Get more to filter
            
            # Filter by venue
            if venue == 'home':
                venue_games = [g for g in all_games if g['home_team_id'] == team_id]
            elif venue == 'away':
                venue_games = [g for g in all_games if g['away_team_id'] == team_id]
            else:
                logger.error(f"Invalid venue: {venue}. Must be 'home' or 'away'")
                return []
            
            # Limit to requested number
            venue_games = venue_games[:limit]
            
            # Get current league standings for position lookup
            standings = self._get_current_league_standings(season)
            
            formatted_games = []
            for game in venue_games:
                # Determine if team scored and if BTTS occurred
                if game['home_team_id'] == team_id:
                    goals_for = game['goals_home']
                    goals_against = game['goals_away']
                    opponent_id = game['away_team_id']
                    opponent_name = game['away_team_name']
                    is_home = True
                else:
                    goals_for = game['goals_away']
                    goals_against = game['goals_home']
                    opponent_id = game['home_team_id']
                    opponent_name = game['home_team_name']
                    is_home = False
                
                # Get opponent's current league position
                opponent_position = standings.get(opponent_id, {}).get('position', '?')
                
                formatted_games.append({
                    'goals_scored': goals_for or 0,
                    'goals_conceded': goals_against or 0,
                    'btts': (goals_for or 0) > 0 and (goals_against or 0) > 0,
                    'team_scored': (goals_for or 0) > 0,
                    'is_home': is_home,
                    'venue': 'H' if is_home else 'A',
                    'opponent': opponent_name,
                    'opponent_position': opponent_position,
                    'match_date': game.get('match_date', '')[:10] if game.get('match_date') else 'Unknown'
                })
            
            return formatted_games
            
        except Exception as e:
            logger.error(f"Error formatting games for team {team_id}: {e}")
            return []

    def format_games_for_display(self, team_id: int, season: int, limit: int = 10) -> List[Dict]:
        """Format team games for display in analysis table."""
        
        try:
            games = self._get_team_matches_with_goals(team_id, season, limit)
            formatted_games = []
            
            for game in games:
                # Determine if team scored and if BTTS occurred
                if game['home_team_id'] == team_id:
                    goals_for = game['goals_home']
                    goals_against = game['goals_away']
                    venue = 'H'
                    opponent = game.get('away_team_name', f"Team {game['away_team_id']}")
                else:
                    goals_for = game['goals_away']
                    goals_against = game['goals_home']
                    venue = 'A'
                    opponent = game.get('home_team_name', f"Team {game['home_team_id']}")
                
                scored = goals_for > 0
                btts = game['goals_home'] > 0 and game['goals_away'] > 0
                
                formatted_games.append({
                    'date': game['match_date'][:10] if game.get('match_date') else 'Unknown',  # YYYY-MM-DD format
                    'opponent': opponent,
                    'venue': venue,
                    'goals_for': goals_for or 0,
                    'goals_against': goals_against or 0,
                    'scored': scored,
                    'btts': btts
                })
            
            return formatted_games
            
        except Exception as e:
            logger.error(f"Error formatting games for team {team_id}: {e}")
            return []
    
    def get_detailed_btts_analysis(self, home_team_id: int, away_team_id: int, season: int) -> Dict:
        """Get comprehensive BTTS analysis with all calculation details."""
        
        try:
            # Get basic BTTS prediction
            btts_prediction = self.predict_btts(home_team_id, away_team_id, season)
            
            # Get detailed team performance
            home_performance = self.analyze_team_goal_performance_strict_venue(home_team_id, season, 'home')
            away_performance = self.analyze_team_goal_performance_strict_venue(away_team_id, season, 'away')
            
            # Get calculation breakdown
            calculation_details = self._get_calculation_breakdown(
                home_performance, away_performance, btts_prediction
            )
            
            return {
                'btts_prediction': btts_prediction,
                'home_performance': home_performance,
                'away_performance': away_performance,
                'calculation_details': calculation_details
            }
            
        except Exception as e:
            logger.error(f"Error in detailed BTTS analysis: {e}")
            return {
                'btts_prediction': {'btts_probability': 50.0, 'confidence': 'Error'},
                'home_performance': self._get_empty_goal_performance(),
                'away_performance': self._get_empty_goal_performance(),
                'calculation_details': {'error': str(e)}
            }

    def _get_calculation_breakdown(self, home_perf: Dict, away_perf: Dict, btts: Dict) -> Dict:
        """Generate detailed calculation breakdown for transparency."""
        
        try:
            # Extract dynamic weighting details
            home_reasoning = btts.get('home_team_reasoning', '')
            away_reasoning = btts.get('away_team_reasoning', '')
            
            # Parse weighting from reasoning (or calculate fresh)
            if 'heavily favored' in home_reasoning.lower():
                attack_weight = 0.65
                defense_weight = 0.35
                reasoning = 'Strong Attack vs Average Defense'
                confidence_boost = 1.15
            elif 'balanced' in home_reasoning.lower():
                attack_weight = 0.50
                defense_weight = 0.50
                reasoning = 'Balanced matchup'
                confidence_boost = 1.0
            else:
                attack_weight = 0.60  # Default
                defense_weight = 0.40
                reasoning = 'Standard weighting applied'
                confidence_boost = 1.05
            
            # Generate step-by-step calculations
            home_scoring_rate = home_perf.get('scores_1plus_rate', 50.0)
            away_clean_sheet_rate = 100 - away_perf.get('concedes_1plus_rate', 50.0)
            away_scoring_rate = away_perf.get('scores_1plus_rate', 50.0)  
            home_clean_sheet_rate = 100 - home_perf.get('concedes_1plus_rate', 50.0)
            
            home_steps = [
                f"1. Venue-weighted scoring rate: {home_scoring_rate:.1f}%",
                f"2. Opponent clean sheet rate (away): {away_clean_sheet_rate:.1f}%",
                f"3. Dynamic weighting: {attack_weight*100:.0f}% attack / {defense_weight*100:.0f}% defense",
                f"4. Formula: ({home_scoring_rate:.1f}% × {attack_weight:.2f}) + ((100% - {away_clean_sheet_rate:.1f}%) × {defense_weight:.2f})",
                f"5. Base calculation: {(home_scoring_rate * attack_weight + (100 - away_clean_sheet_rate) * defense_weight):.1f}%",
                f"6. Confidence boost ({confidence_boost}x): {btts.get('home_team_to_score', {}).get('probability', 50.0):.1f}%"
            ]
            
            away_steps = [
                f"1. Venue-weighted scoring rate: {away_scoring_rate:.1f}%",
                f"2. Opponent clean sheet rate (home): {home_clean_sheet_rate:.1f}%",
                f"3. Dynamic weighting: {attack_weight*100:.0f}% attack / {defense_weight*100:.0f}% defense",
                f"4. Formula: ({away_scoring_rate:.1f}% × {attack_weight:.2f}) + ((100% - {home_clean_sheet_rate:.1f}%) × {defense_weight:.2f})",
                f"5. Base calculation: {(away_scoring_rate * attack_weight + (100 - home_clean_sheet_rate) * defense_weight):.1f}%",
                f"6. Confidence boost ({confidence_boost}x): {btts.get('away_team_to_score', {}).get('probability', 50.0):.1f}%"
            ]
            
            home_prob = btts.get('home_team_to_score', {}).get('probability', 50.0)
            away_prob = btts.get('away_team_to_score', {}).get('probability', 50.0)
            final_calculation = f"{home_prob:.1f}% × {away_prob:.1f}% = {btts.get('btts_probability', 50.0):.1f}%"
            
            return {
                'dynamic_weighting': {
                    'attack_weight': attack_weight,
                    'defense_weight': defense_weight,
                    'confidence_boost': confidence_boost,
                    'reasoning': reasoning
                },
                'probability_breakdown': {
                    'home_calculation_steps': home_steps,
                    'away_calculation_steps': away_steps,
                    'final_btts_calculation': final_calculation
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating calculation breakdown: {e}")
            # Return fallback breakdown
            return {
                'dynamic_weighting': {
                    'attack_weight': 0.60,
                    'defense_weight': 0.40,
                    'confidence_boost': 1.0,
                    'reasoning': 'Calculation error - using defaults'
                },
                'probability_breakdown': {
                    'home_calculation_steps': ['Error calculating steps'],
                    'away_calculation_steps': ['Error calculating steps'],
                    'final_btts_calculation': 'Calculation unavailable'
                }
            }
    
    def generate_chart_data_for_teams(self, home_team_id: int, away_team_id: int, season: int) -> Dict:
        """Generate chart data for both teams for visualization."""
        
        try:
            # Get historical games for both teams
            home_games = self._get_team_matches_with_goals(home_team_id, season, limit=10)
            away_games = self._get_team_matches_with_goals(away_team_id, season, limit=10)
            
            # Generate goal trends data
            home_chart_data = self._generate_goal_trends_data(home_games, home_team_id, 'home')
            away_chart_data = self._generate_goal_trends_data(away_games, away_team_id, 'away')
            
            # Generate BTTS rate data for different periods
            btts_rate_data = self._generate_btts_rate_data(home_games, away_games, home_team_id, away_team_id)
            
            return {
                'home_team_chart': home_chart_data,
                'away_team_chart': away_chart_data,
                'btts_rate_chart': btts_rate_data
            }
            
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return self._get_empty_chart_data()
    
    def _generate_goal_trends_data(self, games: List[Dict], team_id: int, team_name: str) -> Dict:
        """Generate goal trends chart data for a specific team."""
        
        if not games:
            return self._get_empty_goal_trends()
        
        # Sort games by date (newest first for display)
        sorted_games = sorted(games, key=lambda x: x.get('match_date', ''), reverse=True)
        
        labels = []
        goals_scored = []
        goals_conceded = []
        
        for i, game in enumerate(sorted_games[:10]):  # Last 10 games
            # Create label (Game 1, Game 2, etc. - newest first)
            labels.append(f'Game {i+1}')
            
            # Determine goals for this team
            if game['home_team_id'] == team_id:
                team_goals = game['goals_home'] or 0
                opponent_goals = game['goals_away'] or 0
            else:
                team_goals = game['goals_away'] or 0
                opponent_goals = game['goals_home'] or 0
            
            goals_scored.append(team_goals)
            goals_conceded.append(opponent_goals)
        
        return {
            'labels': labels,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'team_name': team_name
        }
    
    def _generate_btts_rate_data(self, home_games: List[Dict], away_games: List[Dict], home_team_id: int, away_team_id: int) -> Dict:
        """Generate BTTS rate data for different time periods."""
        
        try:
            # Combine and sort all games by date
            all_games = []
            
            # Add home team games
            for game in home_games:
                if game['home_team_id'] == home_team_id or game['away_team_id'] == home_team_id:
                    all_games.append(game)
            
            # Add away team games (avoid duplicates)
            for game in away_games:
                if game['away_team_id'] == away_team_id or game['home_team_id'] == away_team_id:
                    # Check if this game is already in all_games
                    if not any(g.get('id') == game.get('id') for g in all_games):
                        all_games.append(game)
            
            # Sort by date (newest first)
            all_games = sorted(all_games, key=lambda x: x.get('match_date', ''), reverse=True)
            
            # Calculate BTTS rates for different periods
            periods = [5, 10, 15, len(all_games)]
            labels = ['Last 5', 'Last 10', 'Last 15', 'Season']
            btts_rates = []
            
            for period in periods:
                games_subset = all_games[:period] if period <= len(all_games) else all_games
                
                if not games_subset:
                    btts_rates.append(0)
                    continue
                
                btts_count = 0
                for game in games_subset:
                    home_goals = game.get('goals_home', 0) or 0
                    away_goals = game.get('goals_away', 0) or 0
                    
                    if home_goals > 0 and away_goals > 0:
                        btts_count += 1
                
                btts_rate = (btts_count / len(games_subset)) * 100 if games_subset else 0
                btts_rates.append(round(btts_rate, 1))
            
            return {
                'labels': labels,
                'btts_rates': btts_rates,
                'colors': ['#28a745', '#20c997', '#17a2b8', '#6f42c1']
            }
            
        except Exception as e:
            logger.error(f"Error generating BTTS rate data: {e}")
            return {
                'labels': ['Last 5', 'Last 10', 'Last 15', 'Season'],
                'btts_rates': [0, 0, 0, 0],
                'colors': ['#28a745', '#20c997', '#17a2b8', '#6f42c1']
            }
    
    def _get_empty_chart_data(self) -> Dict:
        """Return empty chart data structure."""
        return {
            'home_team_chart': self._get_empty_goal_trends(),
            'away_team_chart': self._get_empty_goal_trends(),
            'btts_rate_chart': {
                'labels': ['Last 5', 'Last 10', 'Last 15', 'Season'],
                'btts_rates': [0, 0, 0, 0],
                'colors': ['#28a745', '#20c997', '#17a2b8', '#6f42c1']
            }
        }
    
    def _get_empty_goal_trends(self) -> Dict:
        """Return empty goal trends data."""
        return {
            'labels': [],
            'goals_scored': [],
            'goals_conceded': [],
            'team_name': 'Unknown'
        }
