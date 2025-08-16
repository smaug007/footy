"""
Accuracy tracking system for China Super League corner prediction system.
Handles prediction validation, accuracy calculation, and performance monitoring.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from data.database import get_db_manager
from config import Config

logger = logging.getLogger(__name__)

class AccuracyTracker:
    """Track and manage prediction accuracy with detailed analytics."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.corner_tolerance = Config.CORNER_TOLERANCE
        
    def verify_prediction(self, prediction_id: int, actual_home_corners: int, 
                         actual_away_corners: int, manual_verification: bool = False,
                         notes: str = None) -> Dict:
        """Verify a prediction against actual results and update accuracy."""
        try:
            # Get prediction details
            prediction = self._get_prediction_details(prediction_id)
            if not prediction:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            # Calculate accuracy metrics
            accuracy_results = self._calculate_accuracy_metrics(
                prediction, actual_home_corners, actual_away_corners
            )
            
            # Store prediction results
            result_data = {
                'prediction_id': prediction_id,
                'actual_home_corners': actual_home_corners,
                'actual_away_corners': actual_away_corners,
                'home_prediction_correct': accuracy_results['home_correct'],
                'away_prediction_correct': accuracy_results['away_correct'],
                'total_prediction_margin': accuracy_results['total_margin'],
                'over_5_5_correct': accuracy_results['over_5_5_correct'],
                'over_6_5_correct': accuracy_results['over_6_5_correct'],
                'verified_manually': manual_verification,
                'notes': notes
            }
            
            result_id = self.db_manager.insert_prediction_result(result_data)
            
            # Update team accuracy statistics
            self._update_team_accuracy_stats(prediction, accuracy_results)
            
            # Record accuracy history
            self._record_accuracy_history(prediction, accuracy_results)
            
            logger.info(f"Verified prediction {prediction_id}: {accuracy_results}")
            
            return {
                'prediction_id': prediction_id,
                'result_id': result_id,
                'accuracy_results': accuracy_results,
                'verification_summary': self._generate_verification_summary(accuracy_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to verify prediction {prediction_id}: {e}")
            raise
    
    def _get_prediction_details(self, prediction_id: int) -> Optional[Dict]:
        """Get prediction details with match and team information."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, m.api_fixture_id, m.home_team_id, m.away_team_id, m.match_date,
                       ht.name as home_team_name, ht.api_team_id as home_api_id,
                       at.name as away_team_name, at.api_team_id as away_api_id
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE p.id = ?
            """, (prediction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _calculate_accuracy_metrics(self, prediction: Dict, actual_home: int, 
                                  actual_away: int) -> Dict:
        """Calculate all accuracy metrics for a prediction."""
        predicted_home = prediction['home_team_expected']
        predicted_away = prediction['away_team_expected']
        predicted_total = prediction['predicted_total_corners']
        actual_total = actual_home + actual_away
        
        # Individual team accuracy (within tolerance)
        home_correct = abs(predicted_home - actual_home) <= self.corner_tolerance
        away_correct = abs(predicted_away - actual_away) <= self.corner_tolerance
        
        # Total corners accuracy
        total_margin = abs(predicted_total - actual_total)
        total_correct = total_margin <= self.corner_tolerance
        
        # Over/Under line accuracy
        over_5_5_correct = (predicted_total > 5.5) == (actual_total > 5.5)
        over_6_5_correct = (predicted_total > 6.5) == (actual_total > 6.5)
        
        return {
            'home_correct': home_correct,
            'away_correct': away_correct,
            'total_correct': total_correct,
            'total_margin': total_margin,
            'over_5_5_correct': over_5_5_correct,
            'over_6_5_correct': over_6_5_correct,
            'predicted_home': predicted_home,
            'predicted_away': predicted_away,
            'predicted_total': predicted_total,
            'actual_home': actual_home,
            'actual_away': actual_away,
            'actual_total': actual_total
        }
    
    def _update_team_accuracy_stats(self, prediction: Dict, accuracy_results: Dict) -> None:
        """Update accuracy statistics for both teams."""
        home_team_id = prediction['home_team_id']
        away_team_id = prediction['away_team_id']
        season = prediction['season']
        
        # Update home team corners won accuracy
        self.db_manager.update_team_accuracy_stats(
            home_team_id, season, 'corners_won', accuracy_results['home_correct']
        )
        
        # Update away team corners won accuracy
        self.db_manager.update_team_accuracy_stats(
            away_team_id, season, 'corners_won', accuracy_results['away_correct']
        )
        
        # Update over/under line accuracy for both teams
        for team_id in [home_team_id, away_team_id]:
            self.db_manager.update_team_accuracy_stats(
                team_id, season, 'over_5_5', accuracy_results['over_5_5_correct']
            )
            self.db_manager.update_team_accuracy_stats(
                team_id, season, 'over_6_5', accuracy_results['over_6_5_correct']
            )
    
    def _record_accuracy_history(self, prediction: Dict, accuracy_results: Dict) -> None:
        """Record detailed accuracy history."""
        prediction_id = prediction['id']
        season = prediction['season']
        match_date = datetime.strptime(prediction['match_date'][:10], '%Y-%m-%d').date()
        
        # Record for home team
        home_history = {
            'team_id': prediction['home_team_id'],
            'prediction_id': prediction_id,
            'season': season,
            'prediction_type': 'corners_won',
            'was_correct': accuracy_results['home_correct'],
            'margin_of_error': abs(accuracy_results['predicted_home'] - accuracy_results['actual_home']),
            'confidence_level': prediction.get('confidence_5_5', 0),
            'match_date': match_date
        }
        
        # Record for away team
        away_history = {
            'team_id': prediction['away_team_id'],
            'prediction_id': prediction_id,
            'season': season,
            'prediction_type': 'corners_won',
            'was_correct': accuracy_results['away_correct'],
            'margin_of_error': abs(accuracy_results['predicted_away'] - accuracy_results['actual_away']),
            'confidence_level': prediction.get('confidence_5_5', 0),
            'match_date': match_date
        }
        
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO team_accuracy_history (
                    team_id, prediction_id, season, prediction_type, was_correct,
                    margin_of_error, confidence_level, match_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                home_history['team_id'], home_history['prediction_id'], 
                home_history['season'], home_history['prediction_type'],
                home_history['was_correct'], home_history['margin_of_error'],
                home_history['confidence_level'], home_history['match_date']
            ))
            
            conn.execute("""
                INSERT INTO team_accuracy_history (
                    team_id, prediction_id, season, prediction_type, was_correct,
                    margin_of_error, confidence_level, match_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                away_history['team_id'], away_history['prediction_id'], 
                away_history['season'], away_history['prediction_type'],
                away_history['was_correct'], away_history['margin_of_error'],
                away_history['confidence_level'], away_history['match_date']
            ))
            
            conn.commit()
    
    def _generate_verification_summary(self, accuracy_results: Dict) -> Dict:
        """Generate human-readable verification summary."""
        return {
            'overall_accuracy': (
                accuracy_results['home_correct'] and 
                accuracy_results['away_correct'] and 
                accuracy_results['total_correct']
            ),
            'individual_accuracy': {
                'home_team': 'Correct' if accuracy_results['home_correct'] else 'Incorrect',
                'away_team': 'Correct' if accuracy_results['away_correct'] else 'Incorrect'
            },
            'total_corners': {
                'predicted': accuracy_results['predicted_total'],
                'actual': accuracy_results['actual_total'],
                'margin': accuracy_results['total_margin'],
                'within_tolerance': accuracy_results['total_correct']
            },
            'line_accuracy': {
                'over_5_5': 'Correct' if accuracy_results['over_5_5_correct'] else 'Incorrect',
                'over_6_5': 'Correct' if accuracy_results['over_6_5_correct'] else 'Incorrect'
            }
        }
    
    def get_team_accuracy_report(self, team_id: int, season: int = None) -> Dict:
        """Get comprehensive accuracy report for a team."""
        try:
            accuracy_stats = self.db_manager.get_team_accuracy(team_id, season)
            
            if not accuracy_stats:
                return {
                    'team_id': team_id,
                    'season': season,
                    'message': 'No accuracy data available',
                    'stats': {}
                }
            
            # Organize stats by prediction type
            stats_by_type = {}
            for stat in accuracy_stats:
                stats_by_type[stat['prediction_type']] = {
                    'total_predictions': stat['total_predictions'],
                    'correct_predictions': stat['correct_predictions'],
                    'accuracy_percentage': stat['accuracy_percentage'],
                    'last_updated': stat['last_updated']
                }
            
            # Calculate overall accuracy
            total_predictions = sum(stat['total_predictions'] for stat in accuracy_stats)
            total_correct = sum(stat['correct_predictions'] for stat in accuracy_stats)
            overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
            
            # Get recent accuracy trend
            recent_trend = self._get_recent_accuracy_trend(team_id, season)
            
            return {
                'team_id': team_id,
                'season': season,
                'overall_accuracy': overall_accuracy,
                'total_predictions': total_predictions,
                'stats_by_type': stats_by_type,
                'recent_trend': recent_trend,
                'difficulty_classification': self._classify_prediction_difficulty(overall_accuracy)
            }
            
        except Exception as e:
            logger.error(f"Failed to get accuracy report for team {team_id}: {e}")
            raise
    
    def _get_recent_accuracy_trend(self, team_id: int, season: int, days: int = 30) -> Dict:
        """Get recent accuracy trend for a team."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT was_correct, match_date
                FROM team_accuracy_history
                WHERE team_id = ? AND season = ?
                AND match_date >= date('now', '-{} days')
                ORDER BY match_date DESC
                LIMIT 10
            """.format(days), (team_id, season))
            
            recent_results = cursor.fetchall()
            
            if not recent_results:
                return {'trend': 'insufficient_data', 'recent_accuracy': 0}
            
            recent_correct = sum(1 for result in recent_results if result[0])
            recent_accuracy = (recent_correct / len(recent_results)) * 100
            
            # Determine trend
            if len(recent_results) >= 5:
                first_half = recent_results[:len(recent_results)//2]
                second_half = recent_results[len(recent_results)//2:]
                
                first_half_accuracy = sum(1 for r in first_half if r[0]) / len(first_half) * 100
                second_half_accuracy = sum(1 for r in second_half if r[0]) / len(second_half) * 100
                
                if second_half_accuracy > first_half_accuracy + 10:
                    trend = 'improving'
                elif second_half_accuracy < first_half_accuracy - 10:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'trend': trend,
                'recent_accuracy': recent_accuracy,
                'recent_predictions': len(recent_results)
            }
    
    def _classify_prediction_difficulty(self, accuracy_percentage: float) -> str:
        """Classify how difficult a team is to predict."""
        if accuracy_percentage >= 80:
            return 'Easy to predict'
        elif accuracy_percentage >= 65:
            return 'Moderate difficulty'
        else:
            return 'Difficult to predict'
    
    def get_system_accuracy_overview(self, season: int = None) -> Dict:
        """Get overall system accuracy overview."""
        try:
            with self.db_manager.get_connection() as conn:
                # Get overall statistics
                if season:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_predictions,
                            SUM(CASE WHEN over_5_5_correct THEN 1 ELSE 0 END) as over_5_5_correct,
                            SUM(CASE WHEN over_6_5_correct THEN 1 ELSE 0 END) as over_6_5_correct,
                            AVG(total_prediction_margin) as avg_margin
                        FROM prediction_results pr
                        JOIN predictions p ON pr.prediction_id = p.id
                        WHERE p.season = ?
                    """, (season,))
                else:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_predictions,
                            SUM(CASE WHEN over_5_5_correct THEN 1 ELSE 0 END) as over_5_5_correct,
                            SUM(CASE WHEN over_6_5_correct THEN 1 ELSE 0 END) as over_6_5_correct,
                            AVG(total_prediction_margin) as avg_margin
                        FROM prediction_results
                    """)
                
                result = cursor.fetchone()
                
                if not result or result[0] == 0:
                    return {
                        'message': 'No prediction results available',
                        'total_predictions': 0
                    }
                
                total_predictions = result[0]
                over_5_5_accuracy = (result[1] / total_predictions * 100) if total_predictions > 0 else 0
                over_6_5_accuracy = (result[2] / total_predictions * 100) if total_predictions > 0 else 0
                avg_margin = result[3] or 0
                
                # Get team-specific accuracy summary
                if season:
                    cursor = conn.execute("""
                        SELECT 
                            t.name,
                            AVG(tas.accuracy_percentage) as avg_accuracy,
                            SUM(tas.total_predictions) as total_predictions
                        FROM team_accuracy_stats tas
                        JOIN teams t ON tas.team_id = t.id
                        WHERE tas.season = ?
                        GROUP BY tas.team_id, t.name
                        ORDER BY avg_accuracy DESC
                    """, (season,))
                else:
                    cursor = conn.execute("""
                        SELECT 
                            t.name,
                            AVG(tas.accuracy_percentage) as avg_accuracy,
                            SUM(tas.total_predictions) as total_predictions
                        FROM team_accuracy_stats tas
                        JOIN teams t ON tas.team_id = t.id
                        GROUP BY tas.team_id, t.name
                        ORDER BY avg_accuracy DESC
                    """)
                
                team_accuracies = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'season': season,
                    'total_predictions': total_predictions,
                    'line_accuracy': {
                        'over_5_5': over_5_5_accuracy,
                        'over_6_5': over_6_5_accuracy
                    },
                    'average_margin': avg_margin,
                    'team_accuracies': team_accuracies,
                    'performance_rating': self._calculate_performance_rating(
                        over_5_5_accuracy, over_6_5_accuracy, avg_margin
                    )
                }
                
        except Exception as e:
            logger.error(f"Failed to get system accuracy overview: {e}")
            raise
    
    def _calculate_performance_rating(self, over_5_5_acc: float, over_6_5_acc: float, 
                                    avg_margin: float) -> str:
        """Calculate overall system performance rating."""
        avg_line_accuracy = (over_5_5_acc + over_6_5_acc) / 2
        
        if avg_line_accuracy >= 80 and avg_margin <= 1.5:
            return 'Excellent'
        elif avg_line_accuracy >= 70 and avg_margin <= 2.0:
            return 'Good'
        elif avg_line_accuracy >= 60 and avg_margin <= 2.5:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def bulk_verify_predictions(self, season: int) -> Dict:
        """Bulk verify predictions against actual match results."""
        try:
            # Get predictions that haven't been verified yet
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT p.id, p.match_id, m.corners_home, m.corners_away
                    FROM predictions p
                    JOIN matches m ON p.match_id = m.id
                    LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE p.season = ? AND pr.id IS NULL 
                    AND m.corners_home IS NOT NULL AND m.corners_away IS NOT NULL
                """, (season,))
                
                unverified_predictions = cursor.fetchall()
            
            verified_count = 0
            error_count = 0
            
            for pred_id, match_id, corners_home, corners_away in unverified_predictions:
                try:
                    self.verify_prediction(pred_id, corners_home, corners_away, False)
                    verified_count += 1
                except Exception as e:
                    logger.error(f"Failed to verify prediction {pred_id}: {e}")
                    error_count += 1
            
            return {
                'season': season,
                'verified_count': verified_count,
                'error_count': error_count,
                'total_processed': len(unverified_predictions)
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk verify predictions for season {season}: {e}")
            raise

# Convenience functions
def verify_prediction(prediction_id: int, actual_home_corners: int, 
                     actual_away_corners: int, manual: bool = False) -> Dict:
    """Verify a single prediction."""
    tracker = AccuracyTracker()
    return tracker.verify_prediction(prediction_id, actual_home_corners, 
                                   actual_away_corners, manual)

def get_team_accuracy(team_id: int, season: int = None) -> Dict:
    """Get team accuracy report."""
    tracker = AccuracyTracker()
    return tracker.get_team_accuracy_report(team_id, season)

def get_system_overview(season: int = None) -> Dict:
    """Get system accuracy overview."""
    tracker = AccuracyTracker()
    return tracker.get_system_accuracy_overview(season)

def bulk_verify_season(season: int) -> Dict:
    """Bulk verify all predictions for a season."""
    tracker = AccuracyTracker()
    return tracker.bulk_verify_predictions(season)
