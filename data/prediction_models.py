#!/usr/bin/env python3
"""
Data models for predictions to avoid circular imports.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date

@dataclass
class MatchInfo:
    """Match information."""
    home_team: str
    away_team: str
    home_team_id: int
    away_team_id: int
    season: int
    prediction_date: str

@dataclass
class PredictionData:
    """Core prediction data."""
    predicted_total_corners: float
    predicted_home_corners: float
    predicted_away_corners: float
    expected_total_range: Tuple[float, float]
    most_likely_outcome: str

@dataclass
class LinePredictions:
    """Over/under line predictions."""
    over_5_5_prediction: str
    over_5_5_confidence: float
    over_6_5_prediction: str
    over_6_5_confidence: float
    over_7_5_prediction: str
    over_7_5_confidence: float

@dataclass
class GoalPredictions:
    """BTTS and goal-related predictions."""
    btts: Dict[str, Any]  # Full 1+ goals BTTS prediction from GoalAnalyzer
    btts_2plus: Optional[Dict[str, Any]] = None  # Full 2+ goals BTTS prediction from GoalAnalyzer

@dataclass
class QualityMetrics:
    """Prediction quality metrics."""
    prediction_quality: str
    statistical_confidence: float
    data_reliability: str
    consistency_score: float

@dataclass
class TeamAnalysis:
    """Team analysis data."""
    home_team_form: str
    away_team_form: str

@dataclass
class AnalysisData:
    """Analysis and recommendation data."""
    analysis_summary: str
    recommendation: str

@dataclass
class MatchPrediction:
    """Complete match prediction with all analysis data."""
    
    # Core identification
    match_info: MatchInfo
    
    # Predictions
    predictions: PredictionData
    
    # Line predictions
    line_predictions: LinePredictions
    
    # Goal predictions (BTTS, etc.)
    goal_predictions: Optional[GoalPredictions]
    
    # Quality metrics
    quality_metrics: QualityMetrics
    
    # Team analysis
    team_analysis: TeamAnalysis
    
    # Analysis
    analysis: AnalysisData
    
    # Legacy fields for backward compatibility
    @property
    def home_team_name(self) -> str:
        return self.match_info.home_team
    
    @property
    def away_team_name(self) -> str:
        return self.match_info.away_team
    
    @property
    def season(self) -> int:
        return self.match_info.season
    
    @property
    def prediction_date(self) -> str:
        return self.match_info.prediction_date
    
    @property
    def predicted_total_corners(self) -> float:
        return self.predictions.predicted_total_corners
    
    @property
    def predicted_home_corners(self) -> float:
        return self.predictions.predicted_home_corners
    
    @property
    def predicted_away_corners(self) -> float:
        return self.predictions.predicted_away_corners
    
    @property
    def expected_total_range(self) -> Tuple[float, float]:
        return self.predictions.expected_total_range
    
    @property
    def most_likely_outcome(self) -> str:
        return self.predictions.most_likely_outcome
    
    @property
    def over_5_5_prediction(self) -> str:
        return self.line_predictions.over_5_5_prediction
    
    @property
    def over_5_5_confidence(self) -> float:
        return self.line_predictions.over_5_5_confidence
    
    @property
    def over_6_5_prediction(self) -> str:
        return self.line_predictions.over_6_5_prediction
    
    @property
    def over_6_5_confidence(self) -> float:
        return self.line_predictions.over_6_5_confidence
    
    @property
    def over_7_5_prediction(self) -> str:
        return self.line_predictions.over_7_5_prediction
    
    @property
    def over_7_5_confidence(self) -> float:
        return self.line_predictions.over_7_5_confidence
    
    @property
    def prediction_quality(self) -> str:
        return self.quality_metrics.prediction_quality
    
    @property
    def statistical_confidence(self) -> float:
        return self.quality_metrics.statistical_confidence
    
    @property
    def data_reliability(self) -> str:
        return self.quality_metrics.data_reliability
    
    @property
    def consistency_score(self) -> float:
        return self.quality_metrics.consistency_score
    
    @property
    def home_team_form(self) -> str:
        return self.team_analysis.home_team_form
    
    @property
    def away_team_form(self) -> str:
        return self.team_analysis.away_team_form
    
    @property
    def analysis_summary(self) -> str:
        return self.analysis.analysis_summary
    
    @property
    def recommendation(self) -> str:
        return self.analysis.recommendation
