"""
Advanced consistency analysis algorithm for corner prediction system.
Implements sophisticated statistical models for corner prediction with confidence calculations.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats
from scipy.stats import norm, poisson
from data.database import get_db_manager
from data.team_analyzer import TeamCornerAnalyzer, TeamCornerAnalysis
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ConsistencyAnalysis:
    """Advanced consistency analysis results."""
    # Basic info
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    season: int
    analysis_date: str
    
    # Home team consistency metrics
    home_corners_won_consistency: float
    home_corners_conceded_consistency: float
    home_overall_consistency: float
    home_prediction_difficulty: str
    home_reliability_90: Dict[str, float]
    
    # Away team consistency metrics
    away_corners_won_consistency: float
    away_corners_conceded_consistency: float
    away_overall_consistency: float
    away_prediction_difficulty: str
    away_reliability_90: Dict[str, float]
    
    # Match prediction metrics
    predicted_total_corners: float
    predicted_home_corners: float
    predicted_away_corners: float
    match_consistency_score: float
    prediction_confidence: Dict[str, float]

@dataclass
class PredictionResult:
    """Comprehensive corner prediction result."""
    # Match info
    home_team_name: str
    away_team_name: str
    season: int
    prediction_date: str
    
    # Predictions
    predicted_total_corners: float
    predicted_home_corners: float
    predicted_away_corners: float
    
    # Confidence levels
    confidence_5_5: float  # Over 5.5 corners
    confidence_6_5: float  # Over 6.5 corners
    confidence_7_5: float  # Over 7.5 corners
    confidence_8_5: float  # Over 8.5 corners
    
    # Statistical certainty
    statistical_confidence: float
    prediction_quality: str
    
    # Detailed analysis
    consistency_analysis: ConsistencyAnalysis
    analysis_report: str

class ConsistencyAnalyzer:
    """Advanced consistency analyzer for corner predictions."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.team_analyzer = TeamCornerAnalyzer()
        
        logger.info("Consistency Analyzer initialized")
    
    def analyze_match_consistency(self, home_team_id: int, away_team_id: int, 
                                season: int) -> Optional[ConsistencyAnalysis]:
        """Perform comprehensive consistency analysis for a match."""
        try:
            # Get team analyses
            home_analysis = self.team_analyzer.analyze_team_corners(home_team_id, season)
            away_analysis = self.team_analyzer.analyze_team_corners(away_team_id, season)
            
            if not home_analysis or not away_analysis:
                logger.warning(f"Insufficient data for consistency analysis")
                return None
            
            # Calculate match consistency metrics
            match_consistency = self._calculate_match_consistency(home_analysis, away_analysis)
            
            # Calculate predictions
            predicted_total, predicted_home, predicted_away = self._calculate_corner_predictions(
                home_analysis, away_analysis
            )
            
            # Calculate prediction confidence
            prediction_confidence = self._calculate_prediction_confidence(
                home_analysis, away_analysis, predicted_total
            )
            
            consistency_analysis = ConsistencyAnalysis(
                home_team_id=home_analysis.team_id,
                away_team_id=away_analysis.team_id,
                home_team_name=home_analysis.team_name,
                away_team_name=away_analysis.team_name,
                season=season,
                analysis_date=datetime.now().isoformat(),
                
                # Home team metrics
                home_corners_won_consistency=home_analysis.corners_won_consistency,
                home_corners_conceded_consistency=home_analysis.corners_conceded_consistency,
                home_overall_consistency=(home_analysis.corners_won_consistency + 
                                        home_analysis.corners_conceded_consistency) / 2,
                home_prediction_difficulty=home_analysis.prediction_difficulty,
                home_reliability_90={
                    'corners_won': home_analysis.corners_won_reliability_90,
                    'corners_conceded': home_analysis.corners_conceded_reliability_90
                },
                
                # Away team metrics
                away_corners_won_consistency=away_analysis.corners_won_consistency,
                away_corners_conceded_consistency=away_analysis.corners_conceded_consistency,
                away_overall_consistency=(away_analysis.corners_won_consistency + 
                                        away_analysis.corners_conceded_consistency) / 2,
                away_prediction_difficulty=away_analysis.prediction_difficulty,
                away_reliability_90={
                    'corners_won': away_analysis.corners_won_reliability_90,
                    'corners_conceded': away_analysis.corners_conceded_reliability_90
                },
                
                # Match predictions
                predicted_total_corners=predicted_total,
                predicted_home_corners=predicted_home,
                predicted_away_corners=predicted_away,
                match_consistency_score=match_consistency,
                prediction_confidence=prediction_confidence
            )
            
            logger.info(f"Consistency analysis completed: {home_analysis.team_name} vs {away_analysis.team_name}")
            return consistency_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze match consistency: {e}")
            raise
    
    def _calculate_match_consistency(self, home_analysis: TeamCornerAnalysis, 
                                   away_analysis: TeamCornerAnalysis) -> float:
        """Calculate overall match consistency score."""
        # Weight factors for different consistency metrics
        weights = {
            'home_won': 0.25,
            'home_conceded': 0.25,
            'away_won': 0.25,
            'away_conceded': 0.25
        }
        
        weighted_consistency = (
            home_analysis.corners_won_consistency * weights['home_won'] +
            home_analysis.corners_conceded_consistency * weights['home_conceded'] +
            away_analysis.corners_won_consistency * weights['away_won'] +
            away_analysis.corners_conceded_consistency * weights['away_conceded']
        )
        
        return weighted_consistency
    
    def _calculate_corner_predictions(self, home_analysis: TeamCornerAnalysis, 
                                    away_analysis: TeamCornerAnalysis) -> Tuple[float, float, float]:
        """Calculate corner predictions using advanced statistical models."""
        
        # Method 1: Direct averaging (baseline)
        home_corners_direct = (home_analysis.corners_won_avg + away_analysis.corners_conceded_avg) / 2
        away_corners_direct = (away_analysis.corners_won_avg + home_analysis.corners_conceded_avg) / 2
        
        # Method 2: Weighted by consistency (more consistent teams get higher weight)
        home_consistency_weight = (home_analysis.corners_won_consistency + 
                                 away_analysis.corners_conceded_consistency) / 200
        away_consistency_weight = (away_analysis.corners_won_consistency + 
                                 home_analysis.corners_conceded_consistency) / 200
        
        # Normalize weights
        total_weight = home_consistency_weight + away_consistency_weight
        if total_weight > 0:
            home_consistency_weight /= total_weight
            away_consistency_weight /= total_weight
        else:
            home_consistency_weight = away_consistency_weight = 0.5
        
        # Method 3: Trend-adjusted predictions
        home_trend_adjustment = self._get_trend_adjustment(home_analysis.corners_won_trend)
        away_trend_adjustment = self._get_trend_adjustment(away_analysis.corners_won_trend)
        
        # Combine methods with weights
        method_weights = [0.4, 0.4, 0.2]  # Direct, consistency-weighted, trend-adjusted
        
        home_corners_predicted = (
            home_corners_direct * method_weights[0] +
            (home_analysis.corners_won_avg * home_consistency_weight + 
             away_analysis.corners_conceded_avg * (1 - home_consistency_weight)) * method_weights[1] +
            (home_corners_direct + home_trend_adjustment) * method_weights[2]
        )
        
        away_corners_predicted = (
            away_corners_direct * method_weights[0] +
            (away_analysis.corners_won_avg * away_consistency_weight + 
             home_analysis.corners_conceded_avg * (1 - away_consistency_weight)) * method_weights[1] +
            (away_corners_direct + away_trend_adjustment) * method_weights[2]
        )
        
        # Apply home advantage factor (slight boost for home team)
        home_advantage = 0.1  # 10% boost for home team
        home_corners_predicted *= (1 + home_advantage)
        away_corners_predicted *= (1 - home_advantage * 0.5)  # Slight reduction for away team
        
        total_corners_predicted = home_corners_predicted + away_corners_predicted
        
        return float(total_corners_predicted), float(home_corners_predicted), float(away_corners_predicted)
    
    def _get_trend_adjustment(self, trend: str) -> float:
        """Get trend adjustment factor."""
        trend_adjustments = {
            'improving': 0.3,
            'stable': 0.0,
            'declining': -0.3,
            'insufficient_data': 0.0
        }
        return trend_adjustments.get(trend, 0.0)
    
    def _calculate_prediction_confidence(self, home_analysis: TeamCornerAnalysis, 
                                       away_analysis: TeamCornerAnalysis, 
                                       predicted_total: float) -> Dict[str, float]:
        """Calculate statistical confidence for predictions."""
        
        # Base confidence from team consistency
        avg_consistency = (
            home_analysis.corners_won_consistency + 
            home_analysis.corners_conceded_consistency +
            away_analysis.corners_won_consistency + 
            away_analysis.corners_conceded_consistency
        ) / 4
        
        # Data quality factor
        min_matches = min(home_analysis.matches_analyzed, away_analysis.matches_analyzed)
        data_quality_factor = min(1.0, min_matches / 10)  # Full confidence with 10+ matches
        
        # Calculate line confidences using normal distribution
        std_dev = 2.5  # Typical corner standard deviation
        
        lines = [5.5, 6.5, 7.5, 8.5]
        line_confidences = {}
        
        for line in lines:
            z_score = (predicted_total - line) / std_dev
            base_confidence = norm.cdf(z_score) * 100
            
            # Adjust based on consistency and data quality
            consistency_multiplier = 0.7 + (avg_consistency / 100) * 0.6  # Range: 0.7-1.3
            data_multiplier = 0.8 + (data_quality_factor * 0.4)  # Range: 0.8-1.2
            
            adjusted_confidence = base_confidence * consistency_multiplier * data_multiplier
            adjusted_confidence = max(5, min(95, adjusted_confidence))  # Cap between 5-95%
            
            line_confidences[f'over_{line}'] = adjusted_confidence
        
        return line_confidences
    
    def generate_prediction(self, home_team_id: int, away_team_id: int, 
                          season: int) -> Optional[PredictionResult]:
        """Generate comprehensive corner prediction for a match."""
        try:
            # Perform consistency analysis
            consistency_analysis = self.analyze_match_consistency(home_team_id, away_team_id, season)
            
            if not consistency_analysis:
                logger.warning(f"Cannot generate prediction - insufficient data")
                return None
            
            # Calculate statistical confidence
            statistical_confidence = self._calculate_statistical_confidence(consistency_analysis)
            
            # Generate analysis report
            analysis_report = self._generate_analysis_report(consistency_analysis)
            
            # Determine prediction quality
            prediction_quality = self._classify_prediction_quality(statistical_confidence, 
                                                                 consistency_analysis.match_consistency_score)
            
            prediction = PredictionResult(
                home_team_name=consistency_analysis.home_team_name,
                away_team_name=consistency_analysis.away_team_name,
                season=season,
                prediction_date=datetime.now().isoformat(),
                
                predicted_total_corners=consistency_analysis.predicted_total_corners,
                predicted_home_corners=consistency_analysis.predicted_home_corners,
                predicted_away_corners=consistency_analysis.predicted_away_corners,
                
                confidence_5_5=consistency_analysis.prediction_confidence.get('over_5.5', 50),
                confidence_6_5=consistency_analysis.prediction_confidence.get('over_6.5', 50),
                confidence_7_5=consistency_analysis.prediction_confidence.get('over_7.5', 50),
                confidence_8_5=consistency_analysis.prediction_confidence.get('over_8.5', 50),
                
                statistical_confidence=statistical_confidence,
                prediction_quality=prediction_quality,
                
                consistency_analysis=consistency_analysis,
                analysis_report=analysis_report
            )
            
            logger.info(f"Prediction generated: {prediction.home_team_name} vs {prediction.away_team_name} - {prediction.predicted_total_corners:.1f} corners")
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to generate prediction: {e}")
            raise
    
    def _calculate_statistical_confidence(self, analysis: ConsistencyAnalysis) -> float:
        """Calculate overall statistical confidence."""
        factors = [
            analysis.match_consistency_score / 100,  # Consistency factor
            min(1.0, min(3, 3) / 5),  # Data availability factor (placeholder)
            0.8,  # Model reliability factor (placeholder)
        ]
        
        # Geometric mean for conservative confidence
        confidence = (np.prod(factors) ** (1/len(factors))) * 100
        return min(95, max(5, confidence))
    
    def _classify_prediction_quality(self, statistical_confidence: float, 
                                   consistency_score: float) -> str:
        """Classify prediction quality."""
        if statistical_confidence >= 80 and consistency_score >= 75:
            return 'Excellent'
        elif statistical_confidence >= 70 and consistency_score >= 65:
            return 'Good'
        elif statistical_confidence >= 60 and consistency_score >= 55:
            return 'Fair'
        else:
            return 'Poor'
    
    def _generate_analysis_report(self, analysis: ConsistencyAnalysis) -> str:
        """Generate detailed analysis report."""
        report_lines = [
            f"CORNER PREDICTION ANALYSIS REPORT",
            f"Match: {analysis.home_team_name} vs {analysis.away_team_name}",
            f"Season: {analysis.season}",
            f"Analysis Date: {analysis.analysis_date}",
            f"",
            f"PREDICTED CORNERS:",
            f"- Total Match Corners: {analysis.predicted_total_corners:.1f}",
            f"- {analysis.home_team_name} (Home): {analysis.predicted_home_corners:.1f}",
            f"- {analysis.away_team_name} (Away): {analysis.predicted_away_corners:.1f}",
            f"",
            f"CONFIDENCE LEVELS:",
        ]
        
        for line, confidence in analysis.prediction_confidence.items():
            report_lines.append(f"- {line.replace('_', ' ').title()}: {confidence:.1f}%")
        
        report_lines.extend([
            f"",
            f"CONSISTENCY ANALYSIS:",
            f"- {analysis.home_team_name} Overall Consistency: {analysis.home_overall_consistency:.1f}%",
            f"  * Corners Won Consistency: {analysis.home_corners_won_consistency:.1f}%",
            f"  * Corners Conceded Consistency: {analysis.home_corners_conceded_consistency:.1f}%",
            f"  * Prediction Difficulty: {analysis.home_prediction_difficulty}",
            f"",
            f"- {analysis.away_team_name} Overall Consistency: {analysis.away_overall_consistency:.1f}%",
            f"  * Corners Won Consistency: {analysis.away_corners_won_consistency:.1f}%",
            f"  * Corners Conceded Consistency: {analysis.away_corners_conceded_consistency:.1f}%",
            f"  * Prediction Difficulty: {analysis.away_prediction_difficulty}",
            f"",
            f"MATCH CONSISTENCY SCORE: {analysis.match_consistency_score:.1f}%",
            f"",
            f"RELIABILITY THRESHOLDS (90% Hit Rate):",
            f"- {analysis.home_team_name}: Won {analysis.home_reliability_90['corners_won']:.1f}, Conceded {analysis.home_reliability_90['corners_conceded']:.1f}",
            f"- {analysis.away_team_name}: Won {analysis.away_reliability_90['corners_won']:.1f}, Conceded {analysis.away_reliability_90['corners_conceded']:.1f}",
        ])
        
        return "\n".join(report_lines)

# Convenience functions
def analyze_match_consistency(home_team_id: int, away_team_id: int, season: int = None) -> Optional[ConsistencyAnalysis]:
    """Analyze consistency for a match."""
    if season is None:
        season = datetime.now().year
    
    analyzer = ConsistencyAnalyzer()
    return analyzer.analyze_match_consistency(home_team_id, away_team_id, season)

def predict_match_corners(home_team_id: int, away_team_id: int, season: int = None) -> Optional[PredictionResult]:
    """Generate corner prediction for a match."""
    if season is None:
        season = datetime.now().year
    
    analyzer = ConsistencyAnalyzer()
    return analyzer.generate_prediction(home_team_id, away_team_id, season)
