"""
Prediction validation system for corner predictions.
Validates predictions against actual results and provides quality metrics.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from data.database import get_db_manager
from data.accuracy_tracker import AccuracyTracker
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of prediction validation."""
    prediction_id: int
    match_info: Dict[str, Any]
    
    # Actual vs predicted
    actual_total_corners: int
    predicted_total_corners: float
    total_corners_error: float
    
    actual_home_corners: int
    predicted_home_corners: float
    home_corners_error: float
    
    actual_away_corners: int
    predicted_away_corners: float
    away_corners_error: float
    
    # Line accuracy
    over_5_5_correct: bool
    over_6_5_correct: bool
    over_7_5_correct: bool
    
    # Confidence validation
    confidence_5_5_predicted: float
    confidence_6_5_predicted: float
    confidence_7_5_predicted: float
    
    # Overall validation metrics
    total_accuracy_within_tolerance: bool
    individual_accuracy_score: float  # 0-100%
    line_accuracy_score: float       # 0-100%
    confidence_calibration_score: float  # How well confidence matched reality
    
    # Quality assessment
    prediction_quality_actual: str
    validation_notes: str

@dataclass
class ValidationSummary:
    """Summary of validation results for multiple predictions."""
    total_predictions_validated: int
    validation_period: str
    
    # Accuracy metrics
    total_corners_mae: float  # Mean Absolute Error
    total_corners_rmse: float # Root Mean Square Error
    within_tolerance_percentage: float
    
    # Line accuracy
    over_5_5_accuracy: float
    over_6_5_accuracy: float
    over_7_5_accuracy: float
    
    # Confidence calibration
    avg_confidence_calibration: float
    overconfident_predictions: int
    underconfident_predictions: int
    
    # Quality distribution
    excellent_predictions: int
    good_predictions: int
    fair_predictions: int
    poor_predictions: int
    
    # Recommendations
    model_performance_rating: str
    improvement_recommendations: List[str]

class PredictionValidator:
    """Validates corner predictions against actual results."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.accuracy_tracker = AccuracyTracker()
        self.tolerance = Config.CORNER_TOLERANCE
        
        logger.info("Prediction Validator initialized")
    
    def validate_prediction(self, prediction_id: int, actual_home_corners: int, 
                          actual_away_corners: int, manual_verification: bool = False,
                          notes: str = None) -> ValidationResult:
        """Validate a single prediction against actual results."""
        try:
            # Get prediction details
            prediction = self._get_prediction_details(prediction_id)
            
            if not prediction:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            # Calculate errors
            actual_total = actual_home_corners + actual_away_corners
            total_error = abs(prediction['predicted_total_corners'] - actual_total)
            home_error = abs(prediction['home_team_expected'] - actual_home_corners)
            away_error = abs(prediction['away_team_expected'] - actual_away_corners)
            
            # Validate line predictions
            line_validation = self._validate_line_predictions(
                prediction, actual_total
            )
            
            # Calculate accuracy scores
            accuracy_scores = self._calculate_accuracy_scores(
                prediction, actual_home_corners, actual_away_corners, actual_total
            )
            
            # Assess confidence calibration
            confidence_calibration = self._assess_confidence_calibration(
                prediction, actual_total
            )
            
            # Determine actual prediction quality
            actual_quality = self._assess_actual_prediction_quality(
                total_error, accuracy_scores['individual'], accuracy_scores['line']
            )
            
            # Create validation result
            validation_result = ValidationResult(
                prediction_id=prediction_id,
                match_info={
                    'home_team': prediction['home_team_name'],
                    'away_team': prediction['away_team_name'],
                    'match_date': prediction['match_date'],
                    'season': prediction['season']
                },
                
                actual_total_corners=actual_total,
                predicted_total_corners=prediction['predicted_total_corners'],
                total_corners_error=total_error,
                
                actual_home_corners=actual_home_corners,
                predicted_home_corners=prediction['home_team_expected'],
                home_corners_error=home_error,
                
                actual_away_corners=actual_away_corners,
                predicted_away_corners=prediction['away_team_expected'],
                away_corners_error=away_error,
                
                over_5_5_correct=line_validation['over_5_5'],
                over_6_5_correct=line_validation['over_6_5'],
                over_7_5_correct=line_validation['over_7_5'],
                
                confidence_5_5_predicted=prediction['confidence_5_5'],
                confidence_6_5_predicted=prediction['confidence_6_5'],
                confidence_7_5_predicted=prediction.get('confidence_7_5', 0),
                
                total_accuracy_within_tolerance=total_error <= self.tolerance,
                individual_accuracy_score=accuracy_scores['individual'],
                line_accuracy_score=accuracy_scores['line'],
                confidence_calibration_score=confidence_calibration,
                
                prediction_quality_actual=actual_quality,
                validation_notes=notes or ""
            )
            
            # Store validation result using accuracy tracker
            self.accuracy_tracker.verify_prediction(
                prediction_id, actual_home_corners, actual_away_corners,
                manual_verification, notes
            )
            
            logger.info(f"Validated prediction {prediction_id}: Total error {total_error:.1f}, Quality: {actual_quality}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate prediction {prediction_id}: {e}")
            raise
    
    def _get_prediction_details(self, prediction_id: int) -> Optional[Dict]:
        """Get prediction details from database."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, m.api_fixture_id, m.match_date, m.season,
                       ht.name as home_team_name, at.name as away_team_name
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE p.id = ?
            """, (prediction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _validate_line_predictions(self, prediction: Dict, actual_total: int) -> Dict[str, bool]:
        """Validate over/under line predictions."""
        predicted_total = prediction['predicted_total_corners']
        
        return {
            'over_5_5': (predicted_total > 5.5) == (actual_total > 5.5),
            'over_6_5': (predicted_total > 6.5) == (actual_total > 6.5),
            'over_7_5': (predicted_total > 7.5) == (actual_total > 7.5)
        }
    
    def _calculate_accuracy_scores(self, prediction: Dict, actual_home: int, 
                                 actual_away: int, actual_total: int) -> Dict[str, float]:
        """Calculate various accuracy scores."""
        # Individual accuracy (home and away corners)
        home_error = abs(prediction['home_team_expected'] - actual_home)
        away_error = abs(prediction['away_team_expected'] - actual_away)
        
        home_accuracy = max(0, 100 - (home_error * 20))  # 20% penalty per corner error
        away_accuracy = max(0, 100 - (away_error * 20))
        individual_score = (home_accuracy + away_accuracy) / 2
        
        # Line accuracy
        line_validation = self._validate_line_predictions(prediction, actual_total)
        correct_lines = sum(line_validation.values())
        line_score = (correct_lines / len(line_validation)) * 100
        
        return {
            'individual': individual_score,
            'line': line_score
        }
    
    def _assess_confidence_calibration(self, prediction: Dict, actual_total: int) -> float:
        """Assess how well confidence levels matched actual outcomes."""
        calibration_scores = []
        
        # Check 5.5 line
        predicted_over_5_5 = prediction['predicted_total_corners'] > 5.5
        actual_over_5_5 = actual_total > 5.5
        confidence_5_5 = prediction['confidence_5_5']
        
        if predicted_over_5_5 == actual_over_5_5:
            # Correct prediction - higher confidence should give higher score
            calibration_scores.append(confidence_5_5)
        else:
            # Incorrect prediction - higher confidence should give lower score
            calibration_scores.append(100 - confidence_5_5)
        
        # Check 6.5 line
        predicted_over_6_5 = prediction['predicted_total_corners'] > 6.5
        actual_over_6_5 = actual_total > 6.5
        confidence_6_5 = prediction['confidence_6_5']
        
        if predicted_over_6_5 == actual_over_6_5:
            calibration_scores.append(confidence_6_5)
        else:
            calibration_scores.append(100 - confidence_6_5)
        
        return np.mean(calibration_scores)
    
    def _assess_actual_prediction_quality(self, total_error: float, individual_score: float, 
                                        line_score: float) -> str:
        """Assess actual prediction quality based on results."""
        if total_error <= 1 and individual_score >= 80 and line_score >= 80:
            return 'Excellent'
        elif total_error <= 2 and individual_score >= 60 and line_score >= 60:
            return 'Good'
        elif total_error <= 3 and individual_score >= 40 and line_score >= 40:
            return 'Fair'
        else:
            return 'Poor'
    
    def validate_multiple_predictions(self, prediction_ids: List[int], 
                                    actual_results: List[Tuple[int, int]]) -> List[ValidationResult]:
        """Validate multiple predictions at once."""
        if len(prediction_ids) != len(actual_results):
            raise ValueError("Number of prediction IDs must match number of actual results")
        
        validation_results = []
        
        for pred_id, (actual_home, actual_away) in zip(prediction_ids, actual_results):
            try:
                result = self.validate_prediction(pred_id, actual_home, actual_away)
                validation_results.append(result)
            except Exception as e:
                logger.error(f"Failed to validate prediction {pred_id}: {e}")
                continue
        
        return validation_results
    
    def generate_validation_summary(self, validation_results: List[ValidationResult],
                                  period_description: str = "Recent") -> ValidationSummary:
        """Generate summary of validation results."""
        if not validation_results:
            return ValidationSummary(
                total_predictions_validated=0,
                validation_period=period_description,
                total_corners_mae=0, total_corners_rmse=0, within_tolerance_percentage=0,
                over_5_5_accuracy=0, over_6_5_accuracy=0, over_7_5_accuracy=0,
                avg_confidence_calibration=0, overconfident_predictions=0, underconfident_predictions=0,
                excellent_predictions=0, good_predictions=0, fair_predictions=0, poor_predictions=0,
                model_performance_rating="Insufficient Data", improvement_recommendations=[]
            )
        
        # Calculate error metrics
        total_errors = [result.total_corners_error for result in validation_results]
        mae = np.mean(total_errors)
        rmse = np.sqrt(np.mean([e**2 for e in total_errors]))
        within_tolerance = sum(1 for result in validation_results if result.total_accuracy_within_tolerance)
        within_tolerance_pct = (within_tolerance / len(validation_results)) * 100
        
        # Calculate line accuracies
        over_5_5_correct = sum(1 for result in validation_results if result.over_5_5_correct)
        over_6_5_correct = sum(1 for result in validation_results if result.over_6_5_correct)
        over_7_5_correct = sum(1 for result in validation_results if result.over_7_5_correct)
        
        over_5_5_acc = (over_5_5_correct / len(validation_results)) * 100
        over_6_5_acc = (over_6_5_correct / len(validation_results)) * 100
        over_7_5_acc = (over_7_5_correct / len(validation_results)) * 100
        
        # Analyze confidence calibration
        calibration_scores = [result.confidence_calibration_score for result in validation_results]
        avg_calibration = np.mean(calibration_scores)
        
        overconfident = sum(1 for result in validation_results 
                          if result.confidence_calibration_score < 50)
        underconfident = sum(1 for result in validation_results 
                           if result.confidence_calibration_score > 80 and 
                           result.total_corners_error > 2)
        
        # Quality distribution
        quality_counts = {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Poor': 0}
        for result in validation_results:
            quality_counts[result.prediction_quality_actual] += 1
        
        # Performance rating
        performance_rating = self._calculate_performance_rating(
            mae, over_5_5_acc, over_6_5_acc, avg_calibration
        )
        
        # Generate recommendations
        recommendations = self._generate_improvement_recommendations(
            mae, over_5_5_acc, over_6_5_acc, avg_calibration, quality_counts
        )
        
        return ValidationSummary(
            total_predictions_validated=len(validation_results),
            validation_period=period_description,
            
            total_corners_mae=mae,
            total_corners_rmse=rmse,
            within_tolerance_percentage=within_tolerance_pct,
            
            over_5_5_accuracy=over_5_5_acc,
            over_6_5_accuracy=over_6_5_acc,
            over_7_5_accuracy=over_7_5_acc,
            
            avg_confidence_calibration=avg_calibration,
            overconfident_predictions=overconfident,
            underconfident_predictions=underconfident,
            
            excellent_predictions=quality_counts['Excellent'],
            good_predictions=quality_counts['Good'],
            fair_predictions=quality_counts['Fair'],
            poor_predictions=quality_counts['Poor'],
            
            model_performance_rating=performance_rating,
            improvement_recommendations=recommendations
        )
    
    def _calculate_performance_rating(self, mae: float, over_5_5_acc: float, 
                                    over_6_5_acc: float, calibration: float) -> str:
        """Calculate overall model performance rating."""
        # Weighted score
        score = (
            (100 - mae * 10) * 0.3 +  # MAE component (lower is better)
            over_5_5_acc * 0.3 +       # 5.5 line accuracy
            over_6_5_acc * 0.25 +      # 6.5 line accuracy  
            calibration * 0.15         # Confidence calibration
        )
        
        if score >= 85:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 65:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def _generate_improvement_recommendations(self, mae: float, over_5_5_acc: float,
                                            over_6_5_acc: float, calibration: float,
                                            quality_counts: Dict[str, int]) -> List[str]:
        """Generate improvement recommendations based on validation results."""
        recommendations = []
        
        if mae > 2.0:
            recommendations.append("Consider improving total corners prediction accuracy - high mean absolute error")
        
        if over_5_5_acc < 70:
            recommendations.append("Improve Over 5.5 corners line predictions - accuracy below target")
        
        if over_6_5_acc < 65:
            recommendations.append("Improve Over 6.5 corners line predictions - accuracy below target")
        
        if calibration < 60:
            recommendations.append("Improve confidence calibration - predictions are poorly calibrated")
        
        if quality_counts['Poor'] > quality_counts['Good'] + quality_counts['Excellent']:
            recommendations.append("Overall prediction quality needs improvement - too many poor predictions")
        
        if not recommendations:
            recommendations.append("Model performance is satisfactory - continue monitoring")
        
        return recommendations

# Convenience functions
def validate_prediction_by_id(prediction_id: int, actual_home: int, actual_away: int,
                             manual: bool = False, notes: str = None) -> ValidationResult:
    """Validate a single prediction."""
    validator = PredictionValidator()
    return validator.validate_prediction(prediction_id, actual_home, actual_away, manual, notes)

def validate_recent_predictions(days: int = 30) -> ValidationSummary:
    """Validate recent predictions."""
    # This would need to be implemented based on how you want to identify recent predictions
    validator = PredictionValidator()
    # Implementation would depend on your specific needs
    return ValidationSummary(
        total_predictions_validated=0, validation_period=f"Last {days} days",
        total_corners_mae=0, total_corners_rmse=0, within_tolerance_percentage=0,
        over_5_5_accuracy=0, over_6_5_accuracy=0, over_7_5_accuracy=0,
        avg_confidence_calibration=0, overconfident_predictions=0, underconfident_predictions=0,
        excellent_predictions=0, good_predictions=0, fair_predictions=0, poor_predictions=0,
        model_performance_rating="No Data", improvement_recommendations=[]
    )
