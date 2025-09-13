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
    calculation_details: Optional[Dict] = None

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
    calculation_details: Optional[Dict] = None

class ConsistencyAnalyzer:
    """Advanced consistency analyzer for corner predictions."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.team_analyzer = TeamCornerAnalyzer()
        
        logger.info("Consistency Analyzer initialized")
    
    def analyze_match_consistency(self, home_team_id: int, away_team_id: int, 
                                season: int, cutoff_date = None) -> Optional[ConsistencyAnalysis]:
        """Perform comprehensive consistency analysis for a match."""
        try:
            # Get team analyses (with cutoff date for backtesting)
            home_analysis = self.team_analyzer.analyze_team_corners(home_team_id, season, cutoff_date=cutoff_date)
            away_analysis = self.team_analyzer.analyze_team_corners(away_team_id, season, cutoff_date=cutoff_date)
            
            if cutoff_date:
                logger.info(f"🕐 Analyzing consistency with cutoff date: {cutoff_date}")
            
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
            prediction_confidence, calculation_details = self._calculate_prediction_confidence(
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
                prediction_confidence=prediction_confidence,
                calculation_details=calculation_details
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
                                       predicted_total: float) -> Tuple[Dict[str, float], Dict]:
        """Calculate dynamic confidence based on actual team line performance."""
        
        # Get database connection for historical match data
        db_manager = get_db_manager()
        
        lines = [5.5, 6.5, 7.5, 8.5]
        line_confidences = {}
        
        calculation_details = {}
        
        for line in lines:
            confidence, breakdown = self._calculate_dynamic_line_confidence(
                home_analysis, away_analysis, line, db_manager
            )
            line_confidences[f'over_{line}'] = confidence
            calculation_details[f'over_{line}'] = breakdown
        
        return line_confidences, calculation_details
    
    def _calculate_dynamic_line_confidence(self, home_analysis: TeamCornerAnalysis, 
                                         away_analysis: TeamCornerAnalysis,
                                         line_value: float, db_manager) -> Tuple[float, Dict]:
        """Calculate dynamic confidence for a specific line based on team performance."""
        
        # Get historical matches for both teams
        home_matches = db_manager.get_team_matches(home_analysis.team_id, home_analysis.season, limit=20)
        away_matches = db_manager.get_team_matches(away_analysis.team_id, away_analysis.season, limit=20)
        
        # Calculate individual team line performance with venue weighting
        home_line_rate = self._calculate_team_line_performance(home_matches, home_analysis.team_id, line_value, is_home_team=True)
        away_line_rate = self._calculate_team_line_performance(away_matches, away_analysis.team_id, line_value, is_home_team=False)
        
        # Base confidence (average of both teams)
        base_confidence = (home_line_rate + away_line_rate) / 2
        
        # Sample size penalty (minimum 7 games for reliable confidence)
        home_games = len(home_matches) if home_matches else 0
        away_games = len(away_matches) if away_matches else 0
        min_games = min(home_games, away_games)
        
        if min_games < 7:
            # Penalty for insufficient data
            sample_penalty = min_games / 7  # e.g., 5 games = 0.71 multiplier
        else:
            sample_penalty = 1.0  # No penalty
        
        # Consistency factor based on team reliability
        consistency_factor = self._calculate_team_consistency_factor(
            home_analysis, away_analysis, home_games, away_games
        )
        
        # Final confidence calculation
        final_confidence = base_confidence * sample_penalty * consistency_factor
        
        # Only minimum limit (5% minimum, no maximum cap)
        final_confidence = max(5.0, final_confidence)
        
        # Create calculation breakdown for analysis display
        calculation_breakdown = {
            'home_line_rate': home_line_rate,
            'away_line_rate': away_line_rate, 
            'base_confidence': base_confidence,
            'sample_penalty': sample_penalty,
            'consistency_factor': consistency_factor,
            'final_confidence': final_confidence,
            'home_games': home_games,
            'away_games': away_games,
            'min_games': min_games
        }
        
        return final_confidence, calculation_breakdown
    
    def _calculate_team_line_performance(self, matches: List[Dict], team_id: int, line_value: float, is_home_team: bool = True) -> float:
        """Calculate team's historical performance for a specific line with venue weighting."""
        if not matches:
            return 50.0  # Default neutral confidence
        
        over_count = 0
        total_count = len(matches)
        
        # Weight recent games and venue relevance
        weighted_over = 0.0
        total_weight = 0.0
        venue_weighting_applied = False
        venue_weighting_error = None
        
        try:
            # Count venue-specific games for minimum threshold
            relevant_venue_games = 0
            for match in matches:
                is_team_playing_home = match.get('home_team_id') == team_id
                if (is_home_team and is_team_playing_home) or (not is_home_team and not is_team_playing_home):
                    relevant_venue_games += 1
            
            # Apply venue weighting only if we have sufficient data (3+ games at relevant venue)
            use_venue_weighting = relevant_venue_games >= 3
            
            for i, match in enumerate(matches):
                home_corners = match.get('corners_home', 0) or 0
                away_corners = match.get('corners_away', 0) or 0
                match_total = home_corners + away_corners
                
                # Time-based weighting (recent games matter more)
                time_weight = np.exp(-0.05 * i)
                
                # Venue-based weighting
                venue_weight = 1.0  # Default weight
                if use_venue_weighting:
                    is_team_playing_home = match.get('home_team_id') == team_id
                    
                    if (is_home_team and is_team_playing_home) or (not is_home_team and not is_team_playing_home):
                        venue_weight = 1.3  # 30% boost for relevant venue
                        venue_weighting_applied = True
                    else:
                        venue_weight = 1.0  # Standard weight for less relevant venue
                
                # Combined weighting
                combined_weight = time_weight * venue_weight
                total_weight += combined_weight
                
                if match_total > line_value:
                    over_count += 1
                    weighted_over += combined_weight
                    
        except Exception as e:
            # Fallback to equal weighting on error
            venue_weighting_error = str(e)
            logger.warning(f"Venue weighting failed for team {team_id}, falling back to equal weighting: {e}")
            
            weighted_over = 0.0
            total_weight = 0.0
            
            for i, match in enumerate(matches):
                home_corners = match.get('corners_home', 0) or 0
                away_corners = match.get('corners_away', 0) or 0
                match_total = home_corners + away_corners
                
                # Simple time weighting only
                weight = np.exp(-0.05 * i)
                total_weight += weight
                
                if match_total > line_value:
                    weighted_over += weight
        
        # Calculate weighted percentage
        if total_weight > 0:
            weighted_rate = (weighted_over / total_weight) * 100
        else:
            weighted_rate = (over_count / total_count) * 100 if total_count > 0 else 50.0
        
        # Store weighting info for transparency (attach to result)
        weighted_rate = float(weighted_rate)
        if hasattr(weighted_rate, '__dict__'):
            weighted_rate.venue_weighting_applied = venue_weighting_applied
            weighted_rate.venue_weighting_error = venue_weighting_error
        
        return weighted_rate
    
    def _calculate_team_consistency_factor(self, home_analysis: TeamCornerAnalysis, 
                                         away_analysis: TeamCornerAnalysis,
                                         home_games: int, away_games: int) -> float:
        """Calculate consistency factor using pure line consistency method."""
        
        # Get historical matches to calculate line consistency
        home_matches = self.db_manager.get_team_matches(home_analysis.team_id, home_analysis.season, limit=20)
        away_matches = self.db_manager.get_team_matches(away_analysis.team_id, away_analysis.season, limit=20)
        
        # Calculate line consistency for Over 5.5 (our primary line)
        home_line_consistency = self._calculate_pure_line_consistency(home_matches, home_analysis.team_id, 5.5)
        away_line_consistency = self._calculate_pure_line_consistency(away_matches, away_analysis.team_id, 5.5)
        
        # Average line consistency
        avg_line_consistency = (home_line_consistency + away_line_consistency) / 2
        
        # Convert line consistency to factor (higher line consistency = higher confidence)
        # Line consistency ranges from 0-100, we want factor range 0.8-1.0
        consistency_factor = 0.8 + (avg_line_consistency / 100) * 0.2
        
        # Additional penalty for very small samples
        if min(home_games, away_games) < 5:
            consistency_factor *= 0.85  # Extra penalty for very limited data
        
        return consistency_factor
    
    def _calculate_pure_line_consistency(self, matches: List[Dict], team_id: int, line_value: float) -> float:
        """Calculate pure line consistency - how often the team hits the betting line."""
        if not matches:
            return 50.0  # Default neutral consistency
        
        total_corners_list = []
        for match in matches:
            home_corners = match.get('corners_home', 0) or 0
            away_corners = match.get('corners_away', 0) or 0
            total_corners = home_corners + away_corners
            total_corners_list.append(total_corners)
        
        if not total_corners_list:
            return 50.0
        
        # Calculate how often total corners exceed the line
        line_hits = sum(1 for total in total_corners_list if total > line_value)
        line_consistency = (line_hits / len(total_corners_list)) * 100
        
        # Line consistency IS the line performance rate
        # This is the pure line consistency method we want
        return line_consistency
    
    def generate_prediction(self, home_team_id: int, away_team_id: int, 
                          season: int, cutoff_date = None) -> Optional[PredictionResult]:
        """Generate comprehensive corner prediction for a match."""
        try:
            # Perform consistency analysis (with cutoff date for backtesting)
            consistency_analysis = self.analyze_match_consistency(home_team_id, away_team_id, season, cutoff_date)
            
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
                analysis_report=analysis_report,
                calculation_details=consistency_analysis.calculation_details
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
        return max(5, confidence)
    
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
def analyze_match_consistency(home_team_id: int, away_team_id: int, season: int = None, cutoff_date = None) -> Optional[ConsistencyAnalysis]:
    """Analyze consistency for a match."""
    if season is None:
        season = datetime.now().year
    
    analyzer = ConsistencyAnalyzer()
    return analyzer.analyze_match_consistency(home_team_id, away_team_id, season, cutoff_date)

def predict_match_corners(home_team_id: int, away_team_id: int, season: int = None, cutoff_date = None) -> Optional[PredictionResult]:
    """Generate corner prediction for a match."""
    if season is None:
        season = datetime.now().year
    
    analyzer = ConsistencyAnalyzer()
    return analyzer.generate_prediction(home_team_id, away_team_id, season, cutoff_date)
