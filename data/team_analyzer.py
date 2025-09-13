"""
Team statistics calculator and analyzer for corner prediction system.
Calculates comprehensive team corner statistics with consistency analysis.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats
from data.database import get_db_manager
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class TeamCornerAnalysis:
    """Comprehensive team corner analysis results."""
    # Basic info
    team_id: int
    team_name: str
    season: int
    matches_analyzed: int
    analysis_date: str
    
    # Corners won analysis
    corners_won_avg: float
    corners_won_median: float
    corners_won_std: float
    corners_won_min: int
    corners_won_max: int
    corners_won_consistency: float
    corners_won_trend: str
    corners_won_reliability_90: float
    corners_won_recent_form: List[int]
    
    # Corners conceded analysis
    corners_conceded_avg: float
    corners_conceded_median: float
    corners_conceded_std: float
    corners_conceded_min: int
    corners_conceded_max: int
    corners_conceded_consistency: float
    corners_conceded_trend: str
    corners_conceded_reliability_90: float
    corners_conceded_recent_form: List[int]
    
    # Advanced metrics
    home_away_split: Dict[str, Dict[str, float]]
    vs_opponent_strength: Dict[str, Dict[str, float]]
    monthly_trends: Dict[str, float]
    form_analysis: Dict[str, Any]
    prediction_difficulty: str

class TeamCornerAnalyzer:
    """Analyzes team corner statistics for prediction purposes."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.min_games = Config.MIN_GAMES_FOR_PREDICTION
        self.max_games = Config.MAX_GAMES_FOR_ANALYSIS
        
        logger.info("Team Corner Analyzer initialized")
    
    def analyze_team_corners(self, team_id: int, season: int, limit_games: int = None, cutoff_date = None) -> Optional[TeamCornerAnalysis]:
        """Perform comprehensive corner analysis for a team."""
        try:
            # Get team info
            team = self.db_manager.get_team_by_api_id(team_id, season)
            if not team:
                # Try by database ID
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT * FROM teams WHERE id = ? AND season = ?", (team_id, season))
                    team_row = cursor.fetchone()
                    team = dict(team_row) if team_row else None
            
            if not team:
                logger.warning(f"Team {team_id} not found for season {season}")
                return None
            
            # Get team matches with corner data (with cutoff date for backtesting)
            if cutoff_date:
                team_matches = self._get_team_matches_with_corners_before_date(team['id'], season, cutoff_date, limit_games)
                logger.info(f"🕐 Using cutoff date {cutoff_date} for {team['name']} corner analysis")
            else:
                team_matches = self._get_team_matches_with_corners(team['id'], season, limit_games)
            
            if len(team_matches) < self.min_games:
                logger.warning(f"Insufficient data for team {team['name']}: {len(team_matches)} matches (need {self.min_games})")
                return None
            
            logger.info(f"Analyzing {len(team_matches)} matches for {team['name']}")
            
            # Extract corner data
            corners_won, corners_conceded = self._extract_corner_data(team_matches, team['id'])
            
            if not corners_won or not corners_conceded:
                logger.warning(f"No corner data found for team {team['name']}")
                return None
            
            # Perform comprehensive analysis
            analysis = TeamCornerAnalysis(
                team_id=team['id'],
                team_name=team['name'],
                season=season,
                matches_analyzed=len(team_matches),
                analysis_date=datetime.now().isoformat(),
                
                # Corners won analysis
                corners_won_avg=self._calculate_weighted_average(corners_won),
                corners_won_median=float(np.median(corners_won)),
                corners_won_std=float(np.std(corners_won)),
                corners_won_min=int(min(corners_won)),
                corners_won_max=int(max(corners_won)),
                corners_won_consistency=self._calculate_consistency_score(corners_won),
                corners_won_trend=self._calculate_trend(corners_won),
                corners_won_reliability_90=self._calculate_reliability_threshold(corners_won, 0.90),
                corners_won_recent_form=corners_won[-5:] if len(corners_won) >= 5 else corners_won,
                
                # Corners conceded analysis
                corners_conceded_avg=self._calculate_weighted_average(corners_conceded),
                corners_conceded_median=float(np.median(corners_conceded)),
                corners_conceded_std=float(np.std(corners_conceded)),
                corners_conceded_min=int(min(corners_conceded)),
                corners_conceded_max=int(max(corners_conceded)),
                corners_conceded_consistency=self._calculate_consistency_score(corners_conceded),
                corners_conceded_trend=self._calculate_trend(corners_conceded),
                corners_conceded_reliability_90=self._calculate_reliability_threshold(corners_conceded, 0.90),
                corners_conceded_recent_form=corners_conceded[-5:] if len(corners_conceded) >= 5 else corners_conceded,
                
                # Advanced metrics
                home_away_split=self._calculate_home_away_split(team_matches, team['id']),
                vs_opponent_strength=self._analyze_vs_opponent_strength(team_matches, team['id'], season),
                monthly_trends=self._calculate_monthly_trends(team_matches, team['id']),
                form_analysis=self._analyze_recent_form(corners_won, corners_conceded),
                prediction_difficulty=self._classify_prediction_difficulty(corners_won, corners_conceded)
            )
            
            logger.info(f"Analysis completed for {team['name']}: {analysis.matches_analyzed} matches analyzed")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze team {team_id} for season {season}: {e}")
            raise
    
    def _get_team_matches_with_corners(self, team_id: int, season: int, limit: int = None) -> List[Dict]:
        """Get team matches that have corner data."""
        limit = limit or self.max_games
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.season = ? AND m.status = 'FT'
                AND m.corners_home IS NOT NULL AND m.corners_away IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (team_id, team_id, season, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_team_matches_with_corners_before_date(self, team_id: int, season: int, cutoff_date, limit: int = None) -> List[Dict]:
        """Get team matches that have corner data BEFORE a specific cutoff date (for time-travel predictions)."""
        from datetime import date
        limit = limit or self.max_games
        
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
                AND m.corners_home IS NOT NULL AND m.corners_away IS NOT NULL
                AND date(m.match_date) < ?
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (team_id, team_id, season, cutoff_date, limit))
            
            matches = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Retrieved {len(matches)} corner matches for team {team_id} before {cutoff_date}")
            return matches
    
    def _extract_corner_data(self, matches: List[Dict], team_id: int) -> Tuple[List[int], List[int]]:
        """Extract corners won and conceded from matches."""
        corners_won = []
        corners_conceded = []
        
        for match in matches:
            if match['home_team_id'] == team_id:
                # Team is home
                corners_won.append(match['corners_home'])
                corners_conceded.append(match['corners_away'])
            else:
                # Team is away
                corners_won.append(match['corners_away'])
                corners_conceded.append(match['corners_home'])
        
        return corners_won, corners_conceded
    
    def _calculate_weighted_average(self, values: List[int], recent_weight: float = 0.6) -> float:
        """Calculate weighted average giving more importance to recent games."""
        if not values:
            return 0.0
        
        weights = []
        total_games = len(values)
        
        for i in range(total_games):
            # More recent games (later in list) get higher weights
            weight = 1 + (i / total_games) * recent_weight
            weights.append(weight)
        
        return float(np.average(values, weights=weights))
    
    def _calculate_consistency_score(self, values: List[int]) -> float:
        """Calculate consistency score (0-100%). Higher = more consistent."""
        if len(values) < 3:
            return 50.0  # Default for insufficient data
        
        std_dev = np.std(values)
        mean_val = np.mean(values)
        
        if mean_val == 0:
            return 0.0
        
        # Coefficient of variation (normalized)
        cv = std_dev / mean_val
        
        # Convert to consistency score (0-100%)
        # Lower CV = higher consistency
        consistency = max(0, 100 - (cv * 100))
        return min(100, consistency)
    
    def _calculate_trend(self, values: List[int]) -> str:
        """Calculate trend direction (improving/stable/declining)."""
        if len(values) < 5:
            return 'insufficient_data'
        
        # Use linear regression to determine trend
        x = np.arange(len(values))
        slope, _, r_value, p_value, _ = stats.linregress(x, values)
        
        # Determine significance
        if p_value > 0.1:  # Not statistically significant
            return 'stable'
        
        # Determine trend direction
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_reliability_threshold(self, values: List[int], reliability_percentage: float = 0.90) -> float:
        """Find the corner line that the team hits X% of the time."""
        if len(values) < 5:
            return 0.5  # Default for insufficient data
        
        sorted_values = sorted(values)
        
        # Test different corner lines (0.5, 1.5, 2.5, etc.)
        for line in [i + 0.5 for i in range(0, 15)]:
            games_over_line = sum(1 for value in values if value >= line)
            hit_rate = games_over_line / len(values)
            
            if hit_rate >= reliability_percentage:
                continue  # This line is hit too often, try higher
            else:
                # Previous line was the highest with 90%+ hit rate
                return max(0.5, line - 1.0)
        
        # If team consistently hits very high numbers
        return float(sorted_values[int(len(sorted_values) * (1 - reliability_percentage))])
    
    def _calculate_home_away_split(self, matches: List[Dict], team_id: int) -> Dict[str, Dict[str, float]]:
        """Calculate home vs away performance split."""
        home_won, home_conceded = [], []
        away_won, away_conceded = [], []
        
        for match in matches:
            if match['home_team_id'] == team_id:
                # Team is home
                home_won.append(match['corners_home'])
                home_conceded.append(match['corners_away'])
            else:
                # Team is away
                away_won.append(match['corners_away'])
                away_conceded.append(match['corners_home'])
        
        return {
            'home': {
                'matches': len(home_won),
                'corners_won_avg': float(np.mean(home_won)) if home_won else 0,
                'corners_conceded_avg': float(np.mean(home_conceded)) if home_conceded else 0
            },
            'away': {
                'matches': len(away_won),
                'corners_won_avg': float(np.mean(away_won)) if away_won else 0,
                'corners_conceded_avg': float(np.mean(away_conceded)) if away_conceded else 0
            }
        }
    
    def _analyze_vs_opponent_strength(self, matches: List[Dict], team_id: int, season: int) -> Dict[str, Dict[str, float]]:
        """Analyze performance against different opponent strengths."""
        # This is a simplified version - in reality, you'd rank teams by league position
        # For now, we'll use a basic analysis
        
        all_corners_won = []
        all_corners_conceded = []
        
        for match in matches:
            if match['home_team_id'] == team_id:
                all_corners_won.append(match['corners_home'])
                all_corners_conceded.append(match['corners_away'])
            else:
                all_corners_won.append(match['corners_away'])
                all_corners_conceded.append(match['corners_home'])
        
        # Simple classification for now
        return {
            'all_opponents': {
                'matches': len(matches),
                'corners_won_avg': float(np.mean(all_corners_won)) if all_corners_won else 0,
                'corners_conceded_avg': float(np.mean(all_corners_conceded)) if all_corners_conceded else 0
            }
        }
    
    def _calculate_monthly_trends(self, matches: List[Dict], team_id: int) -> Dict[str, float]:
        """Calculate monthly performance trends."""
        monthly_data = {}
        
        for match in matches:
            match_date = datetime.fromisoformat(match['match_date'].replace('Z', '+00:00'))
            month_key = match_date.strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            
            if match['home_team_id'] == team_id:
                total_corners = match['corners_home'] + match['corners_away']
            else:
                total_corners = match['corners_away'] + match['corners_home']
            
            monthly_data[month_key].append(total_corners)
        
        # Calculate average for each month
        monthly_trends = {}
        for month, corners_list in monthly_data.items():
            monthly_trends[month] = float(np.mean(corners_list))
        
        return monthly_trends
    
    def _analyze_recent_form(self, corners_won: List[int], corners_conceded: List[int]) -> Dict[str, Any]:
        """Analyze recent form and momentum."""
        if len(corners_won) < 5:
            return {'status': 'insufficient_data'}
        
        # Get last 5 games
        recent_won = corners_won[-5:]
        recent_conceded = corners_conceded[-5:]
        
        # Compare with earlier games
        if len(corners_won) >= 10:
            earlier_won = corners_won[-10:-5]
            earlier_conceded = corners_conceded[-10:-5]
            
            won_improvement = np.mean(recent_won) - np.mean(earlier_won)
            conceded_improvement = np.mean(earlier_conceded) - np.mean(recent_conceded)  # Lower is better
            
            return {
                'recent_won_avg': float(np.mean(recent_won)),
                'recent_conceded_avg': float(np.mean(recent_conceded)),
                'won_trend': 'improving' if won_improvement > 0.5 else 'declining' if won_improvement < -0.5 else 'stable',
                'conceded_trend': 'improving' if conceded_improvement > 0.5 else 'declining' if conceded_improvement < -0.5 else 'stable',
                'overall_form': 'good' if won_improvement > 0 and conceded_improvement > 0 else 'poor' if won_improvement < 0 and conceded_improvement < 0 else 'mixed'
            }
        else:
            return {
                'recent_won_avg': float(np.mean(recent_won)),
                'recent_conceded_avg': float(np.mean(recent_conceded)),
                'status': 'limited_data'
            }
    
    def _classify_prediction_difficulty(self, corners_won: List[int], corners_conceded: List[int]) -> str:
        """Classify how difficult this team is to predict."""
        won_consistency = self._calculate_consistency_score(corners_won)
        conceded_consistency = self._calculate_consistency_score(corners_conceded)
        
        avg_consistency = (won_consistency + conceded_consistency) / 2
        
        if avg_consistency >= 75:
            return 'Easy'
        elif avg_consistency >= 60:
            return 'Moderate'
        else:
            return 'Difficult'
    
    def analyze_multiple_teams(self, team_ids: List[int], season: int) -> Dict[int, Optional[TeamCornerAnalysis]]:
        """Analyze multiple teams at once."""
        results = {}
        
        for team_id in team_ids:
            try:
                analysis = self.analyze_team_corners(team_id, season)
                results[team_id] = analysis
            except Exception as e:
                logger.error(f"Failed to analyze team {team_id}: {e}")
                results[team_id] = None
        
        return results
    
    def get_team_comparison(self, team1_id: int, team2_id: int, season: int) -> Dict[str, Any]:
        """Compare two teams' corner statistics."""
        try:
            team1_analysis = self.analyze_team_corners(team1_id, season)
            team2_analysis = self.analyze_team_corners(team2_id, season)
            
            if not team1_analysis or not team2_analysis:
                return {'error': 'Insufficient data for one or both teams'}
            
            comparison = {
                'team1': {
                    'name': team1_analysis.team_name,
                    'corners_won_avg': team1_analysis.corners_won_avg,
                    'corners_conceded_avg': team1_analysis.corners_conceded_avg,
                    'consistency': (team1_analysis.corners_won_consistency + team1_analysis.corners_conceded_consistency) / 2,
                    'prediction_difficulty': team1_analysis.prediction_difficulty
                },
                'team2': {
                    'name': team2_analysis.team_name,
                    'corners_won_avg': team2_analysis.corners_won_avg,
                    'corners_conceded_avg': team2_analysis.corners_conceded_avg,
                    'consistency': (team2_analysis.corners_won_consistency + team2_analysis.corners_conceded_consistency) / 2,
                    'prediction_difficulty': team2_analysis.prediction_difficulty
                },
                'expected_match_corners': team1_analysis.corners_won_avg + team2_analysis.corners_conceded_avg + 
                                         team2_analysis.corners_won_avg + team1_analysis.corners_conceded_avg,
                'match_predictability': 'High' if team1_analysis.prediction_difficulty == 'Easy' and team2_analysis.prediction_difficulty == 'Easy' else 'Low'
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare teams {team1_id} and {team2_id}: {e}")
            raise

# Convenience functions
def analyze_team(team_id: int, season: int = None, cutoff_date = None) -> Optional[TeamCornerAnalysis]:
    """Analyze a single team's corner statistics."""
    if season is None:
        season = datetime.now().year
    
    analyzer = TeamCornerAnalyzer()
    return analyzer.analyze_team_corners(team_id, season, cutoff_date=cutoff_date)

def compare_teams(team1_id: int, team2_id: int, season: int = None) -> Dict[str, Any]:
    """Compare two teams' corner statistics."""
    if season is None:
        season = datetime.now().year
    
    analyzer = TeamCornerAnalyzer()
    return analyzer.get_team_comparison(team1_id, team2_id, season)
