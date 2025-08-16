"""
Advanced corner prediction engine for China Super League.
Integrates consistency analysis with sophisticated prediction algorithms.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from data.database import get_db_manager
from data.consistency_analyzer import ConsistencyAnalyzer, PredictionResult, predict_match_corners
from data.team_analyzer import analyze_team
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class MatchPrediction:
    """Complete match prediction with all analysis."""
    # Match identification
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    season: int
    
    # Core predictions
    predicted_total_corners: float
    predicted_home_corners: float
    predicted_away_corners: float
    
    # Line predictions with confidence
    over_5_5_prediction: bool
    over_5_5_confidence: float
    over_6_5_prediction: bool
    over_6_5_confidence: float
    over_7_5_prediction: bool
    over_7_5_confidence: float
    
    # Expected value and range
    expected_total_range: Tuple[float, float]  # (min, max)
    most_likely_outcome: str
    
    # Quality metrics
    prediction_quality: str
    statistical_confidence: float
    data_reliability: str
    
    # Supporting analysis
    consistency_score: float
    home_team_form: str
    away_team_form: str
    
    # Detailed report
    analysis_summary: str
    recommendation: str

class PredictionEngine:
    """Advanced prediction engine for corner betting."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.consistency_analyzer = ConsistencyAnalyzer()
        
        logger.info("Prediction Engine initialized")
    
    def predict_match(self, home_team_id: int, away_team_id: int, 
                     season: int = None) -> Optional[MatchPrediction]:
        """Generate comprehensive match prediction."""
        try:
            if season is None:
                season = datetime.now().year
            
            logger.info(f"Generating prediction for match: Team {home_team_id} vs Team {away_team_id}")
            
            # Generate core prediction
            prediction_result = predict_match_corners(home_team_id, away_team_id, season)
            
            if not prediction_result:
                logger.warning("Could not generate prediction - insufficient data")
                return None
            
            # Get team names
            home_team = self._get_team_info(home_team_id, season)
            away_team = self._get_team_info(away_team_id, season)
            
            if not home_team or not away_team:
                logger.warning("Could not find team information")
                return None
            
            # Generate line predictions
            line_predictions = self._generate_line_predictions(prediction_result)
            
            # Calculate expected range
            expected_range = self._calculate_expected_range(prediction_result)
            
            # Determine most likely outcome
            most_likely_outcome = self._determine_most_likely_outcome(prediction_result)
            
            # Get team form analysis
            home_form, away_form = self._analyze_team_forms(home_team_id, away_team_id, season)
            
            # Generate analysis summary and recommendation
            analysis_summary = self._generate_analysis_summary(prediction_result)
            recommendation = self._generate_recommendation(prediction_result, line_predictions)
            
            # Assess data reliability
            data_reliability = self._assess_data_reliability(prediction_result)
            
            match_prediction = MatchPrediction(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team['name'],
                away_team_name=away_team['name'],
                season=season,
                
                predicted_total_corners=prediction_result.predicted_total_corners,
                predicted_home_corners=prediction_result.predicted_home_corners,
                predicted_away_corners=prediction_result.predicted_away_corners,
                
                over_5_5_prediction=line_predictions['over_5_5']['prediction'],
                over_5_5_confidence=line_predictions['over_5_5']['confidence'],
                over_6_5_prediction=line_predictions['over_6_5']['prediction'],
                over_6_5_confidence=line_predictions['over_6_5']['confidence'],
                over_7_5_prediction=line_predictions['over_7_5']['prediction'],
                over_7_5_confidence=line_predictions['over_7_5']['confidence'],
                
                expected_total_range=expected_range,
                most_likely_outcome=most_likely_outcome,
                
                prediction_quality=prediction_result.prediction_quality,
                statistical_confidence=prediction_result.statistical_confidence,
                data_reliability=data_reliability,
                
                consistency_score=prediction_result.consistency_analysis.match_consistency_score,
                home_team_form=home_form,
                away_team_form=away_form,
                
                analysis_summary=analysis_summary,
                recommendation=recommendation
            )
            
            logger.info(f"Prediction completed: {match_prediction.predicted_total_corners:.1f} total corners")
            return match_prediction
            
        except Exception as e:
            logger.error(f"Failed to generate match prediction: {e}")
            raise
    
    def _get_team_info(self, team_id: int, season: int) -> Optional[Dict]:
        """Get team information."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM teams WHERE id = ? AND season = ?",
                (team_id, season)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _generate_line_predictions(self, prediction: PredictionResult) -> Dict[str, Dict[str, Any]]:
        """Generate over/under line predictions."""
        lines = {
            'over_5_5': {
                'line': 5.5,
                'confidence': prediction.confidence_5_5,
                'prediction': prediction.predicted_total_corners > 5.5
            },
            'over_6_5': {
                'line': 6.5,
                'confidence': prediction.confidence_6_5,
                'prediction': prediction.predicted_total_corners > 6.5
            },
            'over_7_5': {
                'line': 7.5,
                'confidence': prediction.confidence_7_5,
                'prediction': prediction.predicted_total_corners > 7.5
            }
        }
        
        return lines
    
    def _calculate_expected_range(self, prediction: PredictionResult) -> Tuple[float, float]:
        """Calculate expected range of total corners."""
        # Use standard deviation based on prediction confidence
        base_std = 2.5
        confidence_factor = prediction.statistical_confidence / 100
        adjusted_std = base_std * (2 - confidence_factor)  # Lower confidence = higher std
        
        predicted = prediction.predicted_total_corners
        min_expected = max(0, predicted - (1.96 * adjusted_std))  # 95% confidence interval
        max_expected = predicted + (1.96 * adjusted_std)
        
        return (round(min_expected, 1), round(max_expected, 1))
    
    def _determine_most_likely_outcome(self, prediction: PredictionResult) -> str:
        """Determine most likely outcome description."""
        total = prediction.predicted_total_corners
        
        if total >= 12:
            return "High-scoring match (12+ corners)"
        elif total >= 9:
            return "Above-average corners (9-11)"
        elif total >= 7:
            return "Average corner count (7-8)"
        elif total >= 5:
            return "Below-average corners (5-6)"
        else:
            return "Low-scoring match (<5 corners)"
    
    def _analyze_team_forms(self, home_team_id: int, away_team_id: int, 
                          season: int) -> Tuple[str, str]:
        """Analyze recent form for both teams."""
        try:
            home_analysis = analyze_team(home_team_id, season)
            away_analysis = analyze_team(away_team_id, season)
            
            if not home_analysis or not away_analysis:
                return "Unknown", "Unknown"
            
            # Analyze form based on recent performance and trends
            home_form = self._classify_team_form(
                home_analysis.corners_won_trend,
                home_analysis.corners_won_consistency,
                home_analysis.form_analysis
            )
            
            away_form = self._classify_team_form(
                away_analysis.corners_won_trend,
                away_analysis.corners_won_consistency,
                away_analysis.form_analysis
            )
            
            return home_form, away_form
            
        except Exception as e:
            logger.error(f"Failed to analyze team forms: {e}")
            return "Unknown", "Unknown"
    
    def _classify_team_form(self, trend: str, consistency: float, 
                          form_analysis: Dict[str, Any]) -> str:
        """Classify team form based on multiple factors."""
        if trend == 'improving' and consistency >= 70:
            return "Excellent"
        elif trend == 'improving' or (trend == 'stable' and consistency >= 75):
            return "Good"
        elif trend == 'stable' or (trend == 'declining' and consistency >= 60):
            return "Fair"
        else:
            return "Poor"
    
    def _generate_analysis_summary(self, prediction: PredictionResult) -> str:
        """Generate concise analysis summary."""
        analysis = prediction.consistency_analysis
        
        summary_points = [
            f"Expected total corners: {prediction.predicted_total_corners:.1f}",
            f"Match consistency score: {analysis.match_consistency_score:.1f}%",
            f"Statistical confidence: {prediction.statistical_confidence:.1f}%",
            f"Prediction quality: {prediction.prediction_quality}",
        ]
        
        # Add confidence levels
        if prediction.confidence_6_5 >= 70:
            summary_points.append(f"Strong confidence in Over 6.5 corners ({prediction.confidence_6_5:.1f}%)")
        elif prediction.confidence_5_5 >= 70:
            summary_points.append(f"Strong confidence in Over 5.5 corners ({prediction.confidence_5_5:.1f}%)")
        
        return " | ".join(summary_points)
    
    def _generate_recommendation(self, prediction: PredictionResult, 
                               line_predictions: Dict[str, Dict[str, Any]]) -> str:
        """Generate betting recommendation."""
        recommendations = []
        
        # Check for strong predictions
        for line_name, line_data in line_predictions.items():
            if line_data['confidence'] >= 75 and line_data['prediction']:
                line_value = line_data['line']
                confidence = line_data['confidence']
                recommendations.append(f"STRONG: Over {line_value} corners ({confidence:.1f}% confidence)")
            elif line_data['confidence'] >= 65 and line_data['prediction']:
                line_value = line_data['line']
                confidence = line_data['confidence']
                recommendations.append(f"MODERATE: Over {line_value} corners ({confidence:.1f}% confidence)")
        
        # Overall quality assessment
        if prediction.prediction_quality in ['Excellent', 'Good']:
            quality_note = f"High-quality prediction ({prediction.prediction_quality})"
        else:
            quality_note = f"Lower confidence prediction ({prediction.prediction_quality})"
        
        if recommendations:
            return f"{'; '.join(recommendations)} | {quality_note}"
        else:
            return f"No strong betting opportunities identified | {quality_note}"
    
    def _assess_data_reliability(self, prediction: PredictionResult) -> str:
        """Assess data reliability for the prediction."""
        analysis = prediction.consistency_analysis
        
        # Check team data quality
        home_difficulty = analysis.home_prediction_difficulty
        away_difficulty = analysis.away_prediction_difficulty
        
        if home_difficulty == "Easy" and away_difficulty == "Easy":
            return "High"
        elif home_difficulty in ["Easy", "Moderate"] and away_difficulty in ["Easy", "Moderate"]:
            return "Good"
        elif "Difficult" in [home_difficulty, away_difficulty]:
            return "Fair"
        else:
            return "Poor"
    
    def predict_multiple_matches(self, match_list: List[Tuple[int, int]], 
                               season: int = None) -> List[Optional[MatchPrediction]]:
        """Predict multiple matches at once."""
        predictions = []
        
        for home_team_id, away_team_id in match_list:
            try:
                prediction = self.predict_match(home_team_id, away_team_id, season)
                predictions.append(prediction)
            except Exception as e:
                logger.error(f"Failed to predict match {home_team_id} vs {away_team_id}: {e}")
                predictions.append(None)
        
        return predictions
    
    def get_best_betting_opportunities(self, predictions: List[MatchPrediction], 
                                     min_confidence: float = 70) -> List[Dict[str, Any]]:
        """Identify best betting opportunities from predictions."""
        opportunities = []
        
        for prediction in predictions:
            if not prediction:
                continue
            
            # Check each line for strong opportunities
            lines_to_check = [
                ('over_5_5', prediction.over_5_5_confidence, prediction.over_5_5_prediction),
                ('over_6_5', prediction.over_6_5_confidence, prediction.over_6_5_prediction),
                ('over_7_5', prediction.over_7_5_confidence, prediction.over_7_5_prediction)
            ]
            
            for line_name, confidence, prediction_bool in lines_to_check:
                if confidence >= min_confidence and prediction_bool:
                    opportunities.append({
                        'match': f"{prediction.home_team_name} vs {prediction.away_team_name}",
                        'line': line_name,
                        'confidence': confidence,
                        'predicted_total': prediction.predicted_total_corners,
                        'quality': prediction.prediction_quality,
                        'recommendation': prediction.recommendation
                    })
        
        # Sort by confidence descending
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        return opportunities

# Convenience functions
def predict_match_comprehensive(home_team_id: int, away_team_id: int, 
                              season: int = None) -> Optional[MatchPrediction]:
    """Generate comprehensive match prediction."""
    if season is None:
        season = datetime.now().year
    
    engine = PredictionEngine()
    return engine.predict_match(home_team_id, away_team_id, season)

def find_betting_opportunities(match_list: List[Tuple[int, int]], 
                             season: int = None, min_confidence: float = 70) -> List[Dict[str, Any]]:
    """Find best betting opportunities from multiple matches."""
    if season is None:
        season = datetime.now().year
    
    engine = PredictionEngine()
    predictions = engine.predict_multiple_matches(match_list, season)
    valid_predictions = [p for p in predictions if p is not None]
    
    return engine.get_best_betting_opportunities(valid_predictions, min_confidence)
