"""
Head-to-head historical data analyzer for corner predictions.
Analyzes historical matchups between specific teams to improve prediction accuracy.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from data.database import get_db_manager
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class HeadToHeadAnalysis:
    """Head-to-head analysis results between two teams."""
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    season: int
    
    # Historical matchup data
    total_meetings: int
    meetings_with_corner_data: int
    seasons_analyzed: List[int]
    
    # Corner statistics from head-to-head
    avg_total_corners: float
    avg_home_corners: float
    avg_away_corners: float
    
    # Consistency in head-to-head
    h2h_consistency: float
    corner_range: Tuple[int, int]  # (min, max)
    
    # Trends in recent meetings
    recent_trend: str  # 'increasing', 'decreasing', 'stable'
    recent_meetings: List[Dict[str, Any]]
    
    # Home advantage in this matchup
    home_advantage_factor: float
    
    # Reliability of h2h data
    h2h_reliability: str  # 'High', 'Medium', 'Low', 'Insufficient'
    
    # Prediction adjustments based on h2h
    h2h_adjustment_factor: float
    confidence_boost: float

class HeadToHeadAnalyzer:
    """Analyzes head-to-head historical data between teams."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.min_meetings_for_analysis = 2
        self.max_seasons_lookback = 3
        
        logger.info("Head-to-Head Analyzer initialized")
    
    def analyze_head_to_head(self, home_team_id: int, away_team_id: int, 
                           season: int) -> Optional[HeadToHeadAnalysis]:
        """Perform comprehensive head-to-head analysis."""
        try:
            # Get team information
            home_team = self._get_team_info(home_team_id, season)
            away_team = self._get_team_info(away_team_id, season)
            
            if not home_team or not away_team:
                logger.warning(f"Could not find team information for h2h analysis")
                return None
            
            # Get historical meetings
            historical_meetings = self._get_historical_meetings(
                home_team_id, away_team_id, season
            )
            
            if len(historical_meetings) < self.min_meetings_for_analysis:
                logger.info(f"Insufficient h2h data: {len(historical_meetings)} meetings (need {self.min_meetings_for_analysis})")
                return None
            
            # Analyze corner statistics
            corner_stats = self._analyze_corner_statistics(historical_meetings, home_team_id)
            
            # Calculate consistency
            h2h_consistency = self._calculate_h2h_consistency(historical_meetings)
            
            # Analyze trends
            recent_trend = self._analyze_recent_trend(historical_meetings)
            
            # Calculate home advantage
            home_advantage = self._calculate_home_advantage_factor(historical_meetings, home_team_id)
            
            # Assess reliability
            reliability = self._assess_h2h_reliability(historical_meetings, season)
            
            # Calculate adjustment factors
            adjustment_factor, confidence_boost = self._calculate_adjustment_factors(
                historical_meetings, corner_stats, h2h_consistency
            )
            
            # Get seasons analyzed
            seasons_analyzed = sorted(list(set(m['season'] for m in historical_meetings)))
            
            analysis = HeadToHeadAnalysis(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team['name'],
                away_team_name=away_team['name'],
                season=season,
                
                total_meetings=len(historical_meetings),
                meetings_with_corner_data=len([m for m in historical_meetings if m['corners_home'] is not None]),
                seasons_analyzed=seasons_analyzed,
                
                avg_total_corners=corner_stats['avg_total'],
                avg_home_corners=corner_stats['avg_home'],
                avg_away_corners=corner_stats['avg_away'],
                
                h2h_consistency=h2h_consistency,
                corner_range=corner_stats['range'],
                
                recent_trend=recent_trend,
                recent_meetings=historical_meetings[-3:],  # Last 3 meetings
                
                home_advantage_factor=home_advantage,
                
                h2h_reliability=reliability,
                
                h2h_adjustment_factor=adjustment_factor,
                confidence_boost=confidence_boost
            )
            
            logger.info(f"H2H analysis completed: {home_team['name']} vs {away_team['name']} - {len(historical_meetings)} meetings")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze head-to-head data: {e}")
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
    
    def _get_historical_meetings(self, home_team_id: int, away_team_id: int, 
                               current_season: int) -> List[Dict]:
        """Get historical meetings between two teams."""
        with self.db_manager.get_connection() as conn:
            # Look back up to max_seasons_lookback seasons
            season_range = list(range(
                current_season - self.max_seasons_lookback, 
                current_season
            ))
            
            if not season_range:
                return []
            
            placeholders = ','.join('?' * len(season_range))
            
            # Get matches where these teams played against each other
            cursor = conn.execute(f"""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (
                    (m.home_team_id = ? AND m.away_team_id = ?) OR
                    (m.home_team_id = ? AND m.away_team_id = ?)
                ) AND m.season IN ({placeholders})
                AND m.status = 'FT'
                ORDER BY m.match_date DESC
            """, (home_team_id, away_team_id, away_team_id, home_team_id, *season_range))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _analyze_corner_statistics(self, meetings: List[Dict], home_team_id: int) -> Dict:
        """Analyze corner statistics from historical meetings."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        
        if not meetings_with_corners:
            return {
                'avg_total': 0.0,
                'avg_home': 0.0,
                'avg_away': 0.0,
                'range': (0, 0)
            }
        
        total_corners = []
        home_corners = []
        away_corners = []
        
        for meeting in meetings_with_corners:
            total = meeting['corners_home'] + meeting['corners_away']
            total_corners.append(total)
            
            # Determine which team was home in this meeting
            if meeting['home_team_id'] == home_team_id:
                # Current home team was home in this meeting
                home_corners.append(meeting['corners_home'])
                away_corners.append(meeting['corners_away'])
            else:
                # Current home team was away in this meeting
                home_corners.append(meeting['corners_away'])
                away_corners.append(meeting['corners_home'])
        
        return {
            'avg_total': float(np.mean(total_corners)),
            'avg_home': float(np.mean(home_corners)),
            'avg_away': float(np.mean(away_corners)),
            'range': (min(total_corners), max(total_corners))
        }
    
    def _calculate_h2h_consistency(self, meetings: List[Dict]) -> float:
        """Calculate consistency score for head-to-head meetings."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        
        if len(meetings_with_corners) < 2:
            return 50.0  # Default for insufficient data
        
        total_corners = [m['corners_home'] + m['corners_away'] for m in meetings_with_corners]
        
        if len(total_corners) < 2:
            return 50.0
        
        std_dev = np.std(total_corners)
        mean_val = np.mean(total_corners)
        
        if mean_val == 0:
            return 0.0
        
        # Coefficient of variation (lower = more consistent)
        cv = std_dev / mean_val
        consistency = max(0, 100 - (cv * 100))
        
        return min(100, consistency)
    
    def _analyze_recent_trend(self, meetings: List[Dict]) -> str:
        """Analyze trend in recent meetings."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        
        if len(meetings_with_corners) < 3:
            return 'insufficient_data'
        
        # Get total corners for recent meetings (already sorted by date DESC)
        recent_totals = [
            m['corners_home'] + m['corners_away'] 
            for m in meetings_with_corners[:3]
        ]
        
        # Reverse to get chronological order
        recent_totals.reverse()
        
        # Simple trend analysis
        if len(recent_totals) >= 3:
            first_avg = np.mean(recent_totals[:2])
            last_avg = np.mean(recent_totals[1:])
            
            diff = last_avg - first_avg
            
            if diff > 1.0:
                return 'increasing'
            elif diff < -1.0:
                return 'decreasing'
            else:
                return 'stable'
        
        return 'stable'
    
    def _calculate_home_advantage_factor(self, meetings: List[Dict], home_team_id: int) -> float:
        """Calculate home advantage factor for this specific matchup."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        
        if len(meetings_with_corners) < 2:
            return 1.0  # Neutral
        
        home_performance = []
        away_performance = []
        
        for meeting in meetings_with_corners:
            if meeting['home_team_id'] == home_team_id:
                # This team was home
                home_performance.append(meeting['corners_home'])
            else:
                # This team was away
                away_performance.append(meeting['corners_away'])
        
        if not home_performance or not away_performance:
            return 1.0  # Neutral
        
        avg_home = np.mean(home_performance)
        avg_away = np.mean(away_performance)
        
        if avg_away == 0:
            return 1.2  # Default boost
        
        # Calculate advantage factor (ratio of home to away performance)
        advantage = avg_home / avg_away
        
        # Cap the advantage factor between 0.8 and 1.3
        return max(0.8, min(1.3, advantage))
    
    def _assess_h2h_reliability(self, meetings: List[Dict], current_season: int) -> str:
        """Assess reliability of head-to-head data."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        total_meetings = len(meetings)
        corner_data_meetings = len(meetings_with_corners)
        
        # Check recency of data
        most_recent_season = max(m['season'] for m in meetings) if meetings else current_season - 10
        seasons_since_last_meeting = current_season - most_recent_season
        
        # Reliability scoring
        if corner_data_meetings >= 4 and seasons_since_last_meeting <= 1:
            return 'High'
        elif corner_data_meetings >= 3 and seasons_since_last_meeting <= 2:
            return 'Medium'
        elif corner_data_meetings >= 2 and seasons_since_last_meeting <= 3:
            return 'Low'
        else:
            return 'Insufficient'
    
    def _calculate_adjustment_factors(self, meetings: List[Dict], corner_stats: Dict, 
                                    consistency: float) -> Tuple[float, float]:
        """Calculate adjustment factors for predictions based on h2h data."""
        meetings_with_corners = [m for m in meetings if m['corners_home'] is not None]
        
        if not meetings_with_corners:
            return 1.0, 0.0
        
        # Base adjustment on number of meetings and consistency
        meeting_count_factor = min(1.0, len(meetings_with_corners) / 5.0)  # Max factor at 5+ meetings
        consistency_factor = consistency / 100.0
        
        # Adjustment factor (how much to weight h2h data vs general team stats)
        adjustment_factor = 0.1 + (meeting_count_factor * consistency_factor * 0.3)  # Range: 0.1 to 0.4
        
        # Confidence boost based on reliability
        if consistency >= 80 and len(meetings_with_corners) >= 4:
            confidence_boost = 10.0  # High boost for very reliable h2h data
        elif consistency >= 70 and len(meetings_with_corners) >= 3:
            confidence_boost = 5.0   # Medium boost
        elif consistency >= 60 and len(meetings_with_corners) >= 2:
            confidence_boost = 2.0   # Small boost
        else:
            confidence_boost = 0.0   # No boost
        
        return adjustment_factor, confidence_boost
    
    def get_h2h_prediction_adjustment(self, h2h_analysis: HeadToHeadAnalysis, 
                                    base_prediction: float) -> float:
        """Get adjusted prediction based on head-to-head analysis."""
        if h2h_analysis.h2h_reliability == 'Insufficient':
            return base_prediction
        
        h2h_prediction = h2h_analysis.avg_total_corners
        adjustment_factor = h2h_analysis.h2h_adjustment_factor
        
        # Blend base prediction with h2h prediction
        adjusted_prediction = (
            base_prediction * (1 - adjustment_factor) + 
            h2h_prediction * adjustment_factor
        )
        
        # Apply home advantage factor
        adjusted_prediction *= h2h_analysis.home_advantage_factor
        
        return adjusted_prediction
    
    def get_h2h_confidence_boost(self, h2h_analysis: HeadToHeadAnalysis) -> float:
        """Get confidence boost from head-to-head analysis."""
        return h2h_analysis.confidence_boost

# Convenience functions
def analyze_head_to_head(home_team_id: int, away_team_id: int, 
                        season: int = None) -> Optional[HeadToHeadAnalysis]:
    """Analyze head-to-head data between two teams."""
    if season is None:
        season = datetime.now().year
    
    analyzer = HeadToHeadAnalyzer()
    return analyzer.analyze_head_to_head(home_team_id, away_team_id, season)
