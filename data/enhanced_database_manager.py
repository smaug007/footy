#!/usr/bin/env python3
"""
Enhanced Database Manager for Sophisticated BTTS Predictions.
Phase 2 Implementation: Handle both legacy and enhanced database schemas.
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any, Union
from contextlib import contextmanager
from data.database import DatabaseManager
from data.enhanced_database_schema import EnhancedDatabaseSchema

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager(DatabaseManager):
    """Enhanced database manager with support for sophisticated BTTS predictions."""
    
    def __init__(self, db_path: str = "corners_prediction.db"):
        """Initialize enhanced database manager."""
        super().__init__(db_path)
        self.enhanced_schema_available = self._check_enhanced_schema_availability()
        
        if self.enhanced_schema_available:
            logger.info("✅ Enhanced database schema detected and active")
        else:
            logger.info("⚠️ Running with legacy schema - consider running migration")
    
    def _check_enhanced_schema_availability(self) -> bool:
        """Check if enhanced schema tables are available."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='enhanced_predictions'
                """)
                return cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"Could not check enhanced schema availability: {e}")
            return False
    
    # ===============================
    # ENHANCED PREDICTIONS OPERATIONS
    # ===============================
    
    def insert_enhanced_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """Insert enhanced prediction with dedicated BTTS fields."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - falling back to legacy insert")
            return self.insert_prediction(self._convert_enhanced_to_legacy(prediction_data))
        
        try:
            # Column names matching the EnhancedBTTSPrediction dataclass field order
            column_names = [
                'match_id', 'home_team_id', 'away_team_id', 'season', 'prediction_date',
                'btts_probability', 'home_team_score_probability', 'away_team_score_probability',
                'both_teams_score_confidence', 'attack_weight', 'defense_weight',
                'home_team_strength_class', 'away_team_strength_class',
                'sample_size_adjustment_applied', 'confidence_boost_factor',
                'home_venue_games_analyzed', 'away_venue_games_analyzed',
                'home_venue_scoring_rate', 'away_venue_scoring_rate',
                'home_venue_conceding_rate', 'away_venue_conceding_rate',
                'venue_analysis_quality', 'prediction_methodology',
                'data_reliability_score', 'statistical_confidence', 'consistency_score',
                'prediction_quality_grade', 'analysis_summary', 'calculation_breakdown',
                'recommendation', 'reasoning', 'predicted_total_corners',
                'predicted_home_corners', 'predicted_away_corners',
                'corner_confidence_5_5', 'corner_confidence_6_5', 'corner_confidence_7_5'
            ]
            
            values_tuple = (
                    prediction_data.get('match_id'),
                    prediction_data.get('home_team_id'),
                    prediction_data.get('away_team_id'),
                    prediction_data.get('season'),
                    prediction_data.get('prediction_date', date.today().strftime('%Y-%m-%d')),
                    prediction_data.get('btts_probability', 50.0),
                    prediction_data.get('home_team_score_probability', 50.0),
                    prediction_data.get('away_team_score_probability', 50.0),
                    prediction_data.get('both_teams_score_confidence', 50.0),
                    prediction_data.get('attack_weight', 0.6),
                    prediction_data.get('defense_weight', 0.4),
                    prediction_data.get('home_team_strength_class', 'average'),
                    prediction_data.get('away_team_strength_class', 'average'),
                    prediction_data.get('sample_size_adjustment_applied', False),
                    prediction_data.get('confidence_boost_factor', 1.0),
                    prediction_data.get('home_venue_games_analyzed', 0),
                    prediction_data.get('away_venue_games_analyzed', 0),
                    prediction_data.get('home_venue_scoring_rate', 50.0),
                    prediction_data.get('away_venue_scoring_rate', 50.0),
                    prediction_data.get('home_venue_conceding_rate', 50.0),
                    prediction_data.get('away_venue_conceding_rate', 50.0),
                    prediction_data.get('venue_analysis_quality', 'Fair'),
                    prediction_data.get('prediction_methodology', 'Enhanced Goals Analysis'),
                    prediction_data.get('data_reliability_score', 50.0),
                    prediction_data.get('statistical_confidence', 50.0),
                    prediction_data.get('consistency_score', 50.0),
                    prediction_data.get('prediction_quality_grade', 'Fair'),
                    prediction_data.get('analysis_summary'),
                    prediction_data.get('calculation_breakdown'),
                    prediction_data.get('recommendation'),
                    prediction_data.get('reasoning'),
                    prediction_data.get('predicted_total_corners'),
                    prediction_data.get('predicted_home_corners'),
                    prediction_data.get('predicted_away_corners'),
                    prediction_data.get('corner_confidence_5_5'),
                    prediction_data.get('corner_confidence_6_5'),
                    prediction_data.get('corner_confidence_7_5')
                )
            
            if len(values_tuple) != len(column_names):
                logger.error(f"Column/value mismatch: {len(values_tuple)} values for {len(column_names)} columns")
                return None
            
            with self.get_connection() as conn:
                cursor = conn.execute(f"""
                    INSERT OR REPLACE INTO enhanced_predictions ({', '.join(column_names)}) 
                    VALUES ({', '.join(['?' for _ in column_names])})
                """, values_tuple)
                
                prediction_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Enhanced prediction inserted with ID: {prediction_id}")
                return prediction_id
                
        except Exception as e:
            logger.error(f"Failed to insert enhanced prediction: {e}")
            raise
    
    def get_enhanced_prediction_by_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Get enhanced prediction by match ID."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - falling back to legacy query")
            legacy_pred = self.get_prediction_by_match_id(match_id)
            return self._convert_legacy_to_enhanced_dict(legacy_pred) if legacy_pred else None
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM enhanced_predictions WHERE match_id = ?
                """, (match_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get enhanced prediction for match {match_id}: {e}")
            return None
    
    def get_enhanced_predictions_by_season(self, season: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get enhanced predictions by season."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - falling back to legacy query")
            legacy_preds = self.get_predictions_by_season(season)
            return [self._convert_legacy_to_enhanced_dict(pred) for pred in legacy_preds]
        
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT ep.*, ht.name as home_team_name, at.name as away_team_name,
                           m.match_date, m.goals_home, m.goals_away
                    FROM enhanced_predictions ep
                    JOIN matches m ON ep.match_id = m.id
                    JOIN teams ht ON ep.home_team_id = ht.id
                    JOIN teams at ON ep.away_team_id = at.id
                    WHERE ep.season = ?
                    ORDER BY ep.prediction_date DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query, (season,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get enhanced predictions for season {season}: {e}")
            return []
    
    # ====================================
    # ENHANCED VALIDATION OPERATIONS
    # ====================================
    
    def insert_enhanced_validation_result(self, validation_data: Dict[str, Any]) -> int:
        """Insert enhanced validation result with comprehensive BTTS tracking."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - validation not stored")
            return -1
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO enhanced_validation_results (
                        prediction_id, match_id, validation_date, validation_type,
                        actual_goals_home, actual_goals_away, actual_corners_home, actual_corners_away,
                        actual_btts, actual_home_scored, actual_away_scored,
                        btts_prediction_accurate, home_score_prediction_accurate, away_score_prediction_accurate,
                        probability_accuracy_score, confidence_calibration_score, dynamic_weight_effectiveness,
                        venue_analysis_accuracy, predicted_btts_probability, predicted_home_score_probability,
                        predicted_away_score_probability, prediction_confidence_score,
                        attack_weight_used, defense_weight_used, weight_configuration_effectiveness,
                        sample_size_penalty_applied, prediction_quality_actual, data_quality_validation,
                        methodology_effectiveness, validator_version, validation_notes, manual_verification
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    validation_data['prediction_id'],
                    validation_data['match_id'],
                    validation_data.get('validation_date', date.today().strftime('%Y-%m-%d')),
                    validation_data.get('validation_type', 'enhanced_btts'),
                    validation_data['actual_goals_home'],
                    validation_data['actual_goals_away'],
                    validation_data.get('actual_corners_home'),
                    validation_data.get('actual_corners_away'),
                    validation_data['actual_btts'],
                    validation_data['actual_home_scored'],
                    validation_data['actual_away_scored'],
                    validation_data.get('btts_prediction_accurate'),
                    validation_data.get('home_score_prediction_accurate'),
                    validation_data.get('away_score_prediction_accurate'),
                    validation_data.get('probability_accuracy_score'),
                    validation_data.get('confidence_calibration_score'),
                    validation_data.get('dynamic_weight_effectiveness'),
                    validation_data.get('venue_analysis_accuracy'),
                    validation_data.get('predicted_btts_probability'),
                    validation_data.get('predicted_home_score_probability'),
                    validation_data.get('predicted_away_score_probability'),
                    validation_data.get('prediction_confidence_score'),
                    validation_data.get('attack_weight_used'),
                    validation_data.get('defense_weight_used'),
                    validation_data.get('weight_configuration_effectiveness'),
                    validation_data.get('sample_size_penalty_applied', False),
                    validation_data.get('prediction_quality_actual'),
                    validation_data.get('data_quality_validation'),
                    validation_data.get('methodology_effectiveness'),
                    validation_data.get('validator_version', 'Enhanced_v1.0'),
                    validation_data.get('validation_notes'),
                    validation_data.get('manual_verification', False)
                ))
                
                validation_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Enhanced validation result inserted with ID: {validation_id}")
                return validation_id
                
        except Exception as e:
            logger.error(f"Failed to insert enhanced validation result: {e}")
            raise
    
    def get_enhanced_validation_results(self, start_date: date, end_date: date, 
                                      validation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get enhanced validation results for date range."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - no validation results")
            return []
        
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT evr.*, ep.prediction_methodology, ep.venue_analysis_quality,
                           ht.name as home_team_name, at.name as away_team_name
                    FROM enhanced_validation_results evr
                    JOIN enhanced_predictions ep ON evr.prediction_id = ep.id
                    JOIN matches m ON evr.match_id = m.id
                    JOIN teams ht ON ep.home_team_id = ht.id
                    JOIN teams at ON ep.away_team_id = at.id
                    WHERE evr.validation_date BETWEEN ? AND ?
                """
                
                params = [start_date, end_date]
                
                if validation_type:
                    query += " AND evr.validation_type = ?"
                    params.append(validation_type)
                
                query += " ORDER BY evr.validation_date DESC"
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get enhanced validation results: {e}")
            return []
    
    # =======================================
    # TEAM PERFORMANCE ANALYSIS OPERATIONS  
    # =======================================
    
    def insert_team_performance_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """Insert team performance analysis data."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - team analysis not stored")
            return -1
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO team_performance_analysis (
                        team_id, season, analysis_date, venue, games_analyzed,
                        goals_scored_total, goals_conceded_total, clean_sheets,
                        scores_1plus_count, scores_1plus_rate, scores_2plus_count, scores_2plus_rate,
                        scores_3plus_count, scores_3plus_rate, concedes_1plus_count, concedes_1plus_rate,
                        concedes_2plus_count, concedes_2plus_rate, concedes_3plus_count, concedes_3plus_rate,
                        avg_goals_scored, avg_goals_conceded, avg_goal_difference,
                        attack_strength_class, defense_strength_class, overall_strength_rating,
                        recent_form_trend, form_consistency_score, data_quality,
                        analysis_reliability, sample_size_adequacy
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    analysis_data['team_id'],
                    analysis_data['season'],
                    analysis_data.get('analysis_date', date.today().strftime('%Y-%m-%d')),
                    analysis_data['venue'],
                    analysis_data.get('games_analyzed', 0),
                    analysis_data.get('goals_scored_total', 0),
                    analysis_data.get('goals_conceded_total', 0),
                    analysis_data.get('clean_sheets', 0),
                    analysis_data.get('scores_1plus_count', 0),
                    analysis_data.get('scores_1plus_rate', 0.0),
                    analysis_data.get('scores_2plus_count', 0),
                    analysis_data.get('scores_2plus_rate', 0.0),
                    analysis_data.get('scores_3plus_count', 0),
                    analysis_data.get('scores_3plus_rate', 0.0),
                    analysis_data.get('concedes_1plus_count', 0),
                    analysis_data.get('concedes_1plus_rate', 0.0),
                    analysis_data.get('concedes_2plus_count', 0),
                    analysis_data.get('concedes_2plus_rate', 0.0),
                    analysis_data.get('concedes_3plus_count', 0),
                    analysis_data.get('concedes_3plus_rate', 0.0),
                    analysis_data.get('avg_goals_scored', 0.0),
                    analysis_data.get('avg_goals_conceded', 0.0),
                    analysis_data.get('avg_goal_difference', 0.0),
                    analysis_data.get('attack_strength_class', 'average'),
                    analysis_data.get('defense_strength_class', 'average'),
                    analysis_data.get('overall_strength_rating', 50.0),
                    analysis_data.get('recent_form_trend', 'stable'),
                    analysis_data.get('form_consistency_score', 50.0),
                    analysis_data.get('data_quality', 'Fair'),
                    analysis_data.get('analysis_reliability', 50.0),
                    analysis_data.get('sample_size_adequacy', 'adequate')
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Team performance analysis inserted with ID: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"Failed to insert team performance analysis: {e}")
            raise
    
    def get_team_performance_analysis(self, team_id: int, season: int, 
                                    venue: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team performance analysis data."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - no team performance analysis")
            return []
        
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT tpa.*, t.name as team_name
                    FROM team_performance_analysis tpa
                    JOIN teams t ON tpa.team_id = t.id
                    WHERE tpa.team_id = ? AND tpa.season = ?
                """
                
                params = [team_id, season]
                
                if venue:
                    query += " AND tpa.venue = ?"
                    params.append(venue)
                
                query += " ORDER BY tpa.analysis_date DESC"
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get team performance analysis: {e}")
            return []
    
    # ===================================
    # SYSTEM PERFORMANCE METRICS OPERATIONS
    # ===================================
    
    def insert_system_performance_metrics(self, metrics_data: Dict[str, Any]) -> int:
        """Insert system performance metrics."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - system metrics not stored")
            return -1
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO system_performance_metrics (
                        metric_date, season, time_period, total_predictions, total_validations,
                        validation_rate, btts_predictions_count, btts_accuracy_rate,
                        btts_avg_probability_accuracy, btts_avg_confidence_calibration,
                        avg_weight_effectiveness, attack_weight_success_rate, defense_weight_success_rate,
                        sample_size_adjustments_applied, excellent_quality_predictions,
                        good_quality_predictions, fair_quality_predictions, poor_quality_predictions,
                        avg_data_reliability_score, home_venue_accuracy, away_venue_accuracy,
                        venue_analysis_effectiveness, high_confidence_accuracy, medium_confidence_accuracy,
                        low_confidence_accuracy, confidence_calibration_score, processing_time_avg_ms,
                        database_performance_score, api_availability_rate, error_rate
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    metrics_data.get('metric_date', date.today().strftime('%Y-%m-%d')),
                    metrics_data['season'],
                    metrics_data['time_period'],
                    metrics_data.get('total_predictions', 0),
                    metrics_data.get('total_validations', 0),
                    metrics_data.get('validation_rate', 0.0),
                    metrics_data.get('btts_predictions_count', 0),
                    metrics_data.get('btts_accuracy_rate', 0.0),
                    metrics_data.get('btts_avg_probability_accuracy', 0.0),
                    metrics_data.get('btts_avg_confidence_calibration', 0.0),
                    metrics_data.get('avg_weight_effectiveness', 0.0),
                    metrics_data.get('attack_weight_success_rate', 0.0),
                    metrics_data.get('defense_weight_success_rate', 0.0),
                    metrics_data.get('sample_size_adjustments_applied', 0),
                    metrics_data.get('excellent_quality_predictions', 0),
                    metrics_data.get('good_quality_predictions', 0),
                    metrics_data.get('fair_quality_predictions', 0),
                    metrics_data.get('poor_quality_predictions', 0),
                    metrics_data.get('avg_data_reliability_score', 0.0),
                    metrics_data.get('home_venue_accuracy', 0.0),
                    metrics_data.get('away_venue_accuracy', 0.0),
                    metrics_data.get('venue_analysis_effectiveness', 0.0),
                    metrics_data.get('high_confidence_accuracy', 0.0),
                    metrics_data.get('medium_confidence_accuracy', 0.0),
                    metrics_data.get('low_confidence_accuracy', 0.0),
                    metrics_data.get('confidence_calibration_score', 0.0),
                    metrics_data.get('processing_time_avg_ms', 0.0),
                    metrics_data.get('database_performance_score', 100.0),
                    metrics_data.get('api_availability_rate', 100.0),
                    metrics_data.get('error_rate', 0.0)
                ))
                
                metrics_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"System performance metrics inserted with ID: {metrics_id}")
                return metrics_id
                
        except Exception as e:
            logger.error(f"Failed to insert system performance metrics: {e}")
            raise
    
    def get_system_performance_metrics(self, start_date: date, end_date: date, 
                                     time_period: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get system performance metrics for date range."""
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available - no system metrics")
            return []
        
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT * FROM system_performance_metrics
                    WHERE metric_date BETWEEN ? AND ?
                """
                
                params = [start_date, end_date]
                
                if time_period:
                    query += " AND time_period = ?"
                    params.append(time_period)
                
                query += " ORDER BY metric_date DESC"
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get system performance metrics: {e}")
            return []
    
    # ===========================
    # CONVERSION UTILITY METHODS
    # ===========================
    
    def _convert_enhanced_to_legacy(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert enhanced prediction data to legacy format for backward compatibility."""
        return {
            'match_id': enhanced_data['match_id'],
            'predicted_total_corners': enhanced_data.get('predicted_total_corners'),
            'confidence_5_5': enhanced_data.get('corner_confidence_5_5', enhanced_data.get('home_team_score_probability', 50.0)),
            'confidence_6_5': enhanced_data.get('corner_confidence_6_5', enhanced_data.get('away_team_score_probability', 50.0)),
            'home_team_expected': enhanced_data.get('predicted_home_corners'),
            'away_team_expected': enhanced_data.get('predicted_away_corners'),
            'home_team_consistency': enhanced_data.get('consistency_score'),
            'away_team_consistency': enhanced_data.get('consistency_score'),
            'analysis_report': enhanced_data.get('analysis_summary'),
            'season': enhanced_data['season']
        }
    
    def _convert_legacy_to_enhanced_dict(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy prediction data to enhanced format dictionary."""
        if not legacy_data:
            return {}
        
        return {
            'id': legacy_data.get('id'),
            'match_id': legacy_data.get('match_id'),
            'predicted_total_corners': legacy_data.get('predicted_total_corners'),
            'corner_confidence_5_5': legacy_data.get('confidence_5_5'),
            'corner_confidence_6_5': legacy_data.get('confidence_6_5'),
            'predicted_home_corners': legacy_data.get('home_team_expected'),
            'predicted_away_corners': legacy_data.get('away_team_expected'),
            'btts_probability': legacy_data.get('confidence_5_5', 50.0) * 0.8,  # Estimate
            'home_team_score_probability': legacy_data.get('confidence_5_5', 50.0) * 0.9,  # Estimate
            'away_team_score_probability': legacy_data.get('confidence_5_5', 50.0) * 0.8,  # Estimate
            'prediction_methodology': 'Legacy Conversion',
            'analysis_summary': legacy_data.get('analysis_report'),
            'season': legacy_data.get('season'),
            'created_at': legacy_data.get('created_at'),
            'data_source': 'legacy_migration'
        }
    
    # ==========================
    # ENHANCED UTILITY METHODS
    # ==========================
    
    def get_enhanced_schema_info(self) -> Dict[str, Any]:
        """Get information about enhanced schema availability and version."""
        try:
            with self.get_connection() as conn:
                # Check for schema version table
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                schema_version_exists = cursor.fetchone() is not None
                
                if schema_version_exists:
                    cursor = conn.execute("""
                        SELECT version, migration_date, description
                        FROM schema_version 
                        ORDER BY id DESC LIMIT 1
                    """)
                    
                    version_info = cursor.fetchone()
                    if version_info:
                        return {
                            'enhanced_schema_available': self.enhanced_schema_available,
                            'schema_version': version_info[0],
                            'migration_date': version_info[1],
                            'description': version_info[2],
                            'features': [
                                'Dedicated BTTS prediction fields',
                                'Dynamic weighting storage',
                                'Venue-specific analysis metadata',
                                'Comprehensive validation tracking',
                                'Team performance analysis',
                                'System performance metrics'
                            ]
                        }
                
                return {
                    'enhanced_schema_available': self.enhanced_schema_available,
                    'schema_version': 'Enhanced_v2.0' if self.enhanced_schema_available else 'Legacy_v1.0',
                    'migration_date': None,
                    'description': 'Enhanced schema with sophisticated BTTS support' if self.enhanced_schema_available else 'Legacy corner-focused schema'
                }
                
        except Exception as e:
            logger.error(f"Failed to get enhanced schema info: {e}")
            return {
                'enhanced_schema_available': False,
                'schema_version': 'Unknown',
                'error': str(e)
            }

# Convenience function for getting enhanced database manager
def get_enhanced_db_manager() -> EnhancedDatabaseManager:
    """Get enhanced database manager instance."""
    return EnhancedDatabaseManager()

if __name__ == '__main__':
    # Test enhanced database manager
    enhanced_db = get_enhanced_db_manager()
    schema_info = enhanced_db.get_enhanced_schema_info()
    
    print("Enhanced Database Manager Test")
    print("=" * 40)
    print(f"Enhanced schema available: {schema_info['enhanced_schema_available']}")
    print(f"Schema version: {schema_info['schema_version']}")
    
    if schema_info.get('features'):
        print("Features:")
        for feature in schema_info['features']:
            print(f"  ✅ {feature}")
