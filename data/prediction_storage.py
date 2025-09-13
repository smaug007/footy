"""
Prediction storage system for future verification and accuracy tracking.
Stores predictions in database and manages prediction lifecycle.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
from data.database import get_db_manager
from data.prediction_models import MatchPrediction
from data.consistency_analyzer import PredictionResult
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class StoredPrediction:
    """Stored prediction with metadata."""
    id: int
    match_id: int
    prediction_date: str
    season: int
    
    # Core predictions
    predicted_total_corners: float
    predicted_home_corners: float
    predicted_away_corners: float
    
    # Confidence levels
    confidence_5_5: float
    confidence_6_5: float
    confidence_7_5: float
    
    # Quality metrics
    statistical_confidence: float
    prediction_quality: str
    consistency_score: float
    
    # Analysis data
    analysis_report: str
    prediction_metadata: Dict[str, Any]
    
    # Verification status
    is_verified: bool
    verification_date: Optional[str]
    actual_result: Optional[Dict[str, Any]]

class PredictionStorageManager:
    """Manages prediction storage and retrieval."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        logger.info("Prediction Storage Manager initialized")
    
    def store_prediction(self, match_prediction: MatchPrediction, 
                        match_id: int = None) -> int:
        """Store a match prediction in the database."""
        try:
            # If match_id not provided, try to find it
            if match_id is None:
                match_id = self._find_match_id(
                    match_prediction.match_info.home_team_id,
                    match_prediction.match_info.away_team_id,
                    match_prediction.match_info.season
                )
            
            if match_id is None:
                # Create a match record if it doesn't exist
                match_id = self._create_match_record(match_prediction)
            
            # Prepare prediction data
            prediction_data = {
                'match_id': match_id,
                'predicted_total_corners': match_prediction.predicted_total_corners,
                'confidence_5_5': match_prediction.over_5_5_confidence,
                'confidence_6_5': match_prediction.over_6_5_confidence,
                'home_team_expected': match_prediction.predicted_home_corners,
                'away_team_expected': match_prediction.predicted_away_corners,
                'home_team_consistency': match_prediction.consistency_score,
                'away_team_consistency': match_prediction.consistency_score,  # Simplified
                'home_team_score_probability': (
                    match_prediction.goal_predictions.btts.get('home_team_score_probability', 0) 
                    if match_prediction.goal_predictions and match_prediction.goal_predictions.btts 
                    else None
                ),
                'away_team_score_probability': (
                    match_prediction.goal_predictions.btts.get('away_team_score_probability', 0)
                    if match_prediction.goal_predictions and match_prediction.goal_predictions.btts 
                    else None
                ),
                'analysis_report': self._create_detailed_report(match_prediction),
                'season': match_prediction.match_info.season
            }
            
            # Store in database
            prediction_id = self.db_manager.insert_prediction(prediction_data)
            
            # Store additional metadata
            self._store_prediction_metadata(prediction_id, match_prediction)
            
            logger.info(f"Stored prediction {prediction_id} for match {match_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            raise
    
    def store_prediction_result(self, prediction_result: PredictionResult,
                              match_id: int = None) -> int:
        """Store a PredictionResult from consistency analyzer."""
        try:
            # Convert PredictionResult to MatchPrediction format for storage
            # This is a simplified conversion - you might want to enhance this
            
            if match_id is None:
                # Try to find match based on team names (this would need enhancement)
                match_id = self._find_match_by_team_names(
                    prediction_result.home_team_name,
                    prediction_result.away_team_name,
                    prediction_result.season
                )
            
            if match_id is None:
                logger.warning("Could not find match ID for prediction result")
                return None
            
            # Prepare prediction data
            prediction_data = {
                'match_id': match_id,
                'predicted_total_corners': prediction_result.predicted_total_corners,
                'confidence_5_5': prediction_result.confidence_5_5,
                'confidence_6_5': prediction_result.confidence_6_5,
                'home_team_expected': prediction_result.predicted_home_corners,
                'away_team_expected': prediction_result.predicted_away_corners,
                'analysis_report': prediction_result.analysis_report,
                'season': prediction_result.season
            }
            
            prediction_id = self.db_manager.insert_prediction(prediction_data)
            
            # Store metadata
            metadata = {
                'prediction_quality': prediction_result.prediction_quality,
                'statistical_confidence': prediction_result.statistical_confidence,
                'consistency_analysis': asdict(prediction_result.consistency_analysis),
                'storage_source': 'consistency_analyzer'
            }
            
            self._store_prediction_metadata(prediction_id, metadata)
            
            logger.info(f"Stored prediction result {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Failed to store prediction result: {e}")
            raise
    
    def _find_match_id(self, home_team_id: int, away_team_id: int, season: int) -> Optional[int]:
        """Find match ID for given teams and season."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id FROM matches 
                WHERE home_team_id = ? AND away_team_id = ? AND season = ?
                ORDER BY match_date DESC LIMIT 1
            """, (home_team_id, away_team_id, season))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _find_match_by_team_names(self, home_team_name: str, away_team_name: str,
                                season: int) -> Optional[int]:
        """Find match ID by team names."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.id FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE ht.name = ? AND at.name = ? AND m.season = ?
                ORDER BY m.match_date DESC LIMIT 1
            """, (home_team_name, away_team_name, season))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _create_match_record(self, match_prediction: MatchPrediction) -> int:
        """Create a match record for prediction storage."""
        # This is a simplified implementation
        # In a real system, you'd want more comprehensive match data
        match_data = {
            'api_fixture_id': 0,  # Placeholder
            'home_team_id': match_prediction.match_info.home_team_id,
            'away_team_id': match_prediction.match_info.away_team_id,
            'match_date': datetime.now().isoformat(),
            'season': match_prediction.match_info.season,
            'status': 'NS'  # Not Started
        }
        
        return self.db_manager.insert_match(match_data)
    
    def _create_detailed_report(self, match_prediction: MatchPrediction) -> str:
        """Create detailed analysis report for storage."""
        report_lines = [
            f"STORED PREDICTION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            f"Match: {match_prediction.match_info.home_team} vs {match_prediction.match_info.away_team}",
            f"Season: {match_prediction.match_info.season}",
            f"",
            f"PREDICTIONS:",
            f"- Total Corners: {match_prediction.predicted_total_corners:.1f}",
            f"- Home Corners: {match_prediction.predicted_home_corners:.1f}",
            f"- Away Corners: {match_prediction.predicted_away_corners:.1f}",
            f"- Expected Range: {match_prediction.expected_total_range[0]:.1f} - {match_prediction.expected_total_range[1]:.1f}",
            f"",
            f"LINE PREDICTIONS:",
            f"- Over 5.5: {'YES' if match_prediction.over_5_5_prediction else 'NO'} ({match_prediction.over_5_5_confidence:.1f}%)",
            f"- Over 6.5: {'YES' if match_prediction.over_6_5_prediction else 'NO'} ({match_prediction.over_6_5_confidence:.1f}%)",
            f"- Over 7.5: {'YES' if match_prediction.over_7_5_prediction else 'NO'} ({match_prediction.over_7_5_confidence:.1f}%)",
            f"",
            f"QUALITY METRICS:",
            f"- Prediction Quality: {match_prediction.prediction_quality}",
            f"- Statistical Confidence: {match_prediction.statistical_confidence:.1f}%",
            f"- Data Reliability: {match_prediction.data_reliability}",
            f"- Consistency Score: {match_prediction.consistency_score:.1f}%",
            f"",
            f"TEAM ANALYSIS:",
            f"- Home Team Form: {match_prediction.home_team_form}",
            f"- Away Team Form: {match_prediction.away_team_form}",
            f"",
            f"RECOMMENDATION:",
            f"{match_prediction.recommendation}",
            f"",
            f"ANALYSIS SUMMARY:",
            f"{match_prediction.analysis_summary}"
        ]
        
        return "\n".join(report_lines)
    
    def _store_prediction_metadata(self, prediction_id: int, data: Any) -> None:
        """Store additional prediction metadata."""
        # Convert data to JSON for storage
        if hasattr(data, '__dict__'):
            # If it's an object with attributes
            metadata = asdict(data) if hasattr(data, '__dataclass_fields__') else data.__dict__
        elif isinstance(data, dict):
            metadata = data
        else:
            metadata = {'data': str(data)}
        
        # Store in a metadata table (you'd need to create this table)
        # For now, we'll just log it
        logger.debug(f"Metadata for prediction {prediction_id}: {json.dumps(metadata, indent=2)}")
    
    def get_stored_prediction(self, prediction_id: int) -> Optional[StoredPrediction]:
        """Retrieve a stored prediction."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT p.*, m.match_date, m.season,
                           ht.name as home_team_name, at.name as away_team_name,
                           pr.actual_home_corners, pr.actual_away_corners, pr.verified_date
                    FROM predictions p
                    JOIN matches m ON p.match_id = m.id
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE p.id = ?
                """, (prediction_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Prepare actual result if verified
                actual_result = None
                if row['actual_home_corners'] is not None:
                    actual_result = {
                        'home_corners': row['actual_home_corners'],
                        'away_corners': row['actual_away_corners'],
                        'total_corners': row['actual_home_corners'] + row['actual_away_corners']
                    }
                
                return StoredPrediction(
                    id=row['id'],
                    match_id=row['match_id'],
                    prediction_date=row['created_at'],
                    season=row['season'],
                    
                    predicted_total_corners=row['predicted_total_corners'],
                    predicted_home_corners=row['home_team_expected'],
                    predicted_away_corners=row['away_team_expected'],
                    
                    confidence_5_5=row['confidence_5_5'],
                    confidence_6_5=row['confidence_6_5'],
                    confidence_7_5=0.0,  # Not stored in current schema
                    
                    statistical_confidence=0.0,  # Not stored in current schema
                    prediction_quality="Unknown",  # Not stored in current schema
                    consistency_score=row['home_team_consistency'] if 'home_team_consistency' in row.keys() else 0.0,
                    
                    analysis_report=row['analysis_report'] if 'analysis_report' in row.keys() else '',
                    prediction_metadata={},  # Would need to be retrieved separately
                    
                    is_verified=actual_result is not None,
                    verification_date=row['verified_date'] if 'verified_date' in row.keys() else None,
                    actual_result=actual_result
                )
                
        except Exception as e:
            logger.error(f"Failed to retrieve stored prediction {prediction_id}: {e}")
            return None
    
    def get_predictions_by_season(self, season: int, verified_only: bool = False) -> List[StoredPrediction]:
        """Get all predictions for a season."""
        predictions = []
        
        with self.db_manager.get_connection() as conn:
            if verified_only:
                cursor = conn.execute("""
                    SELECT p.id FROM predictions p
                    JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE p.season = ?
                    ORDER BY p.created_at DESC
                """, (season,))
            else:
                cursor = conn.execute("""
                    SELECT p.id FROM predictions p
                    WHERE p.season = ?
                    ORDER BY p.created_at DESC
                """, (season,))
            
            prediction_ids = [row[0] for row in cursor.fetchall()]
        
        for pred_id in prediction_ids:
            prediction = self.get_stored_prediction(pred_id)
            if prediction:
                predictions.append(prediction)
        
        return predictions
    
    def get_unverified_predictions(self, season: int = None) -> List[StoredPrediction]:
        """Get predictions that haven't been verified yet."""
        with self.db_manager.get_connection() as conn:
            if season:
                cursor = conn.execute("""
                    SELECT p.id FROM predictions p
                    LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE pr.id IS NULL AND p.season = ?
                    ORDER BY p.created_at DESC
                """, (season,))
            else:
                cursor = conn.execute("""
                    SELECT p.id FROM predictions p
                    LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE pr.id IS NULL
                    ORDER BY p.created_at DESC
                """)
            
            prediction_ids = [row[0] for row in cursor.fetchall()]
        
        unverified = []
        for pred_id in prediction_ids:
            prediction = self.get_stored_prediction(pred_id)
            if prediction:
                unverified.append(prediction)
        
        return unverified
    
    def update_prediction_verification(self, prediction_id: int, 
                                     actual_home_corners: int, actual_away_corners: int) -> bool:
        """Update prediction with actual results."""
        try:
            from data.accuracy_tracker import AccuracyTracker
            
            tracker = AccuracyTracker()
            tracker.verify_prediction(prediction_id, actual_home_corners, actual_away_corners)
            
            logger.info(f"Updated verification for prediction {prediction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prediction verification: {e}")
            return False
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage system statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                # Total predictions
                cursor = conn.execute("SELECT COUNT(*) FROM predictions")
                total_predictions = cursor.fetchone()[0]
                
                # Verified predictions
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM predictions p
                    JOIN prediction_results pr ON p.id = pr.prediction_id
                """)
                verified_predictions = cursor.fetchone()[0]
                
                # Predictions by season
                cursor = conn.execute("""
                    SELECT season, COUNT(*) FROM predictions
                    GROUP BY season ORDER BY season DESC
                """)
                by_season = dict(cursor.fetchall())
                
                # Recent predictions (last 30 days)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM predictions
                    WHERE created_at >= date('now', '-30 days')
                """)
                recent_predictions = cursor.fetchone()[0]
                
                return {
                    'total_predictions': total_predictions,
                    'verified_predictions': verified_predictions,
                    'unverified_predictions': total_predictions - verified_predictions,
                    'verification_rate': (verified_predictions / total_predictions * 100) if total_predictions > 0 else 0,
                    'predictions_by_season': by_season,
                    'recent_predictions_30_days': recent_predictions
                }
                
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {}

# Convenience functions
def store_match_prediction(match_prediction: MatchPrediction, match_id: int = None) -> int:
    """Store a match prediction."""
    storage_manager = PredictionStorageManager()
    return storage_manager.store_prediction(match_prediction, match_id)

def get_prediction_by_id(prediction_id: int) -> Optional[StoredPrediction]:
    """Get a stored prediction by ID."""
    storage_manager = PredictionStorageManager()
    return storage_manager.get_stored_prediction(prediction_id)

def get_unverified_predictions_list(season: int = None) -> List[StoredPrediction]:
    """Get list of unverified predictions."""
    storage_manager = PredictionStorageManager()
    return storage_manager.get_unverified_predictions(season)
