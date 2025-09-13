"""
Backtesting Engine for CornERD
Generates historical predictions using the same logic as live predictions
but with data cutoff dates to simulate real-time conditions.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .prediction_engine import PredictionEngine
from .consistency_analyzer import ConsistencyAnalyzer  
from .goal_analyzer import GoalAnalyzer
from .database import get_db_manager


@dataclass
class BacktestMatch:
    """Represents a match to be backtested"""
    match_id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    match_date: date
    matchday: int
    actual_corners: Optional[int] = None


@dataclass
class BacktestResult:
    """Results from a backtesting run"""
    match_id: int
    matchday: int
    predicted_total: float
    confidence_5_5: float
    confidence_6_5: float
    home_expected: float
    away_expected: float
    home_score_prob: float
    away_score_prob: float
    actual_corners: Optional[int]
    over_5_5_correct: Optional[bool]
    over_6_5_correct: Optional[bool]
    accuracy: Optional[float]
    data_cutoff_date: date
    analysis_report: str


class BacktestingEngine:
    """Engine for running backtesting on historical matches"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.logger = logging.getLogger(__name__)
        
    def get_backtest_matches(self, season: int = 2025, start_matchday: int = 10) -> List[BacktestMatch]:
        """Get all matches from the specified matchday onwards for backtesting"""
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.id, m.home_team_id, m.away_team_id, 
                       ht.name as home_team_name, at.name as away_team_name,
                       m.match_date, m.matchday, (m.corners_home + m.corners_away) as total_corners
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id  
                WHERE m.season = ? AND m.matchday >= ?
                ORDER BY m.match_date ASC
            """, (season, start_matchday))
            
            matches = []
            for row in cursor.fetchall():
                matches.append(BacktestMatch(
                    match_id=row[0],
                    home_team_id=row[1], 
                    away_team_id=row[2],
                    home_team_name=row[3],
                    away_team_name=row[4],
                    match_date=datetime.strptime(row[5], '%Y-%m-%d').date() if row[5] else None,
                    matchday=row[6],
                    actual_corners=row[7]
                ))
            
            return matches
    
    def run_backtest_for_match(self, match: BacktestMatch) -> BacktestResult:
        """Run backtest prediction for a single match using only historical data"""
        
        try:
            # Use match date as cutoff - only use data from before this match
            cutoff_date = match.match_date
            
            # Create prediction engine with historical data filtering
            prediction_engine = PredictionEngine()
            
            # Get historical matches for both teams (before this match date)
            home_matches = self._get_historical_matches(
                match.home_team_id, cutoff_date, match.match_id
            )
            away_matches = self._get_historical_matches(
                match.away_team_id, cutoff_date, match.match_id
            )
            
            if len(home_matches) < 3 or len(away_matches) < 3:
                raise ValueError(f"Insufficient historical data for match {match.match_id}")
            
            # Create team data objects using historical matches only
            home_team_data = self._create_team_data(match.home_team_id, home_matches, True)
            away_team_data = self._create_team_data(match.away_team_id, away_matches, False)
            
            # Generate prediction using same logic as live system
            prediction = prediction_engine.generate_prediction(
                home_team_data, away_team_data, 
                season=2025, match_date=match.match_date
            )
            
            # Calculate accuracy if actual result is available
            over_5_5_correct = None
            over_6_5_correct = None
            accuracy = None
            
            if match.actual_corners is not None:
                over_5_5_correct = match.actual_corners > 5.5
                over_6_5_correct = match.actual_corners > 6.5
                
                # Simple accuracy calculation
                prediction_error = abs(prediction.predicted_total_corners - match.actual_corners)
                accuracy = max(0, 100 - (prediction_error * 20))  # Penalty of 20% per corner difference
            
            return BacktestResult(
                match_id=match.match_id,
                matchday=match.matchday,
                predicted_total=prediction.predicted_total_corners,
                confidence_5_5=prediction.over_5_5_confidence,
                confidence_6_5=prediction.over_6_5_confidence,
                home_expected=prediction.predicted_home_corners,
                away_expected=prediction.predicted_away_corners,
                home_score_prob=getattr(prediction, 'home_score_probability', 50.0),
                away_score_prob=getattr(prediction, 'away_score_probability', 50.0),
                actual_corners=match.actual_corners,
                over_5_5_correct=over_5_5_correct,
                over_6_5_correct=over_6_5_correct,
                accuracy=accuracy,
                data_cutoff_date=cutoff_date,
                analysis_report=getattr(prediction, 'analysis_report', '')
            )
            
        except Exception as e:
            self.logger.error(f"Error generating backtest for match {match.match_id}: {str(e)}")
            raise
    
    def _get_historical_matches(self, team_id: int, cutoff_date: date, exclude_match_id: int) -> List[Dict]:
        """Get historical matches for a team before the cutoff date"""
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?)
                    AND m.match_date < ?
                    AND m.id != ?
                    AND m.season = 2025
                    AND m.corners_home IS NOT NULL AND m.corners_away IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 20
            """, (team_id, team_id, cutoff_date.isoformat(), exclude_match_id))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _create_team_data(self, team_id: int, historical_matches: List[Dict], is_home: bool) -> Dict:
        """Create team data object from historical matches"""
        
        # Calculate averages from historical data
        corners_for = []
        corners_against = []
        
        for match in historical_matches:
            if match['home_team_id'] == team_id:
                # Team was playing at home
                corners_for.append(match['corners_home'])
                corners_against.append(match['corners_away'])
            else:
                # Team was playing away
                corners_for.append(match['corners_away'])
                corners_against.append(match['corners_home'])
        
        avg_corners_for = sum(corners_for) / len(corners_for) if corners_for else 4.0
        avg_corners_against = sum(corners_against) / len(corners_against) if corners_against else 4.0
        
        return {
            'team_id': team_id,
            'recent_matches': historical_matches,
            'avg_corners_for': avg_corners_for,
            'avg_corners_against': avg_corners_against,
            'form_trend': self._calculate_form_trend(historical_matches, team_id),
            'is_home': is_home
        }
    
    def _calculate_form_trend(self, matches: List[Dict], team_id: int) -> str:
        """Calculate simple form trend from recent matches"""
        if len(matches) < 3:
            return "insufficient_data"
        
        recent_corners = []
        for match in matches[:5]:  # Last 5 matches
            if match['home_team_id'] == team_id:
                recent_corners.append(match['corners_home'])
            else:
                recent_corners.append(match['corners_away'])
        
        avg_recent = sum(recent_corners) / len(recent_corners)
        
        if avg_recent > 5.5:
            return "strong"
        elif avg_recent > 4.5:
            return "good"
        elif avg_recent > 3.5:
            return "average"
        else:
            return "weak"
    
    def store_backtest_result(self, result: BacktestResult, match: BacktestMatch) -> int:
        """Store backtest result in database"""
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO backtest_predictions (
                    original_match_id, match_date, prediction_date, matchday, 
                    home_team_name, away_team_name, predicted_total_corners, 
                    predicted_home_corners, predicted_away_corners, confidence_5_5, confidence_6_5,
                    home_team_score_probability, away_team_score_probability, actual_total_corners, 
                    over_5_5_correct, over_6_5_correct, prediction_accuracy, data_cutoff_date, 
                    analysis_report, backtest_run_id, season
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.match_id, match.match_date.isoformat(), datetime.now().date().isoformat(), 
                result.matchday, match.home_team_name, match.away_team_name, result.predicted_total,
                result.home_expected, result.away_expected, result.confidence_5_5, result.confidence_6_5,
                result.home_score_prob, result.away_score_prob, result.actual_corners, 
                result.over_5_5_correct, result.over_6_5_correct, result.accuracy, 
                result.data_cutoff_date.isoformat(), result.analysis_report,
                f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                result.data_cutoff_date.year  # Use actual year from cutoff date
            ))
            
            return cursor.lastrowid
    
    def get_backtest_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all backtest results"""
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(prediction_accuracy) as avg_accuracy,
                    SUM(CASE WHEN over_5_5_correct = 1 THEN 1 ELSE 0 END) as over_5_5_wins,
                    SUM(CASE WHEN over_6_5_correct = 1 THEN 1 ELSE 0 END) as over_6_5_wins,
                    COUNT(CASE WHEN actual_total_corners IS NOT NULL THEN 1 END) as verified_predictions
                FROM backtest_predictions
            """)
            
            row = cursor.fetchone()
            
            return {
                'total_predictions': row[0],
                'average_accuracy': round(row[1] or 0, 2),
                'over_5_5_success_rate': round((row[2] or 0) / (row[4] or 1) * 100, 2),
                'over_6_5_success_rate': round((row[3] or 0) / (row[4] or 1) * 100, 2),
                'verified_predictions': row[4]
            }
