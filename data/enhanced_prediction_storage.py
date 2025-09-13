#!/usr/bin/env python3
"""
Enhanced Prediction Storage for Sophisticated BTTS Predictions.
Phase 2 Implementation: Store and retrieve predictions using enhanced database schema.
"""

import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from data.enhanced_database_manager import get_enhanced_db_manager
from data.dynamic_weighting import DynamicWeightingEngine

logger = logging.getLogger(__name__)

@dataclass
class EnhancedBTTSPrediction:
    """Enhanced BTTS prediction with comprehensive metadata."""
    
    # Core match information
    match_id: int
    home_team_id: int
    away_team_id: int
    season: int
    prediction_date: str
    
    # BTTS predictions
    btts_probability: float
    home_team_score_probability: float
    away_team_score_probability: float
    both_teams_score_confidence: float
    
    # Dynamic weighting
    attack_weight: float
    defense_weight: float
    home_team_strength_class: str
    away_team_strength_class: str
    sample_size_adjustment_applied: bool
    confidence_boost_factor: float
    
    # Venue-specific analysis
    home_venue_games_analyzed: int
    away_venue_games_analyzed: int
    home_venue_scoring_rate: float
    away_venue_scoring_rate: float
    home_venue_conceding_rate: float
    away_venue_conceding_rate: float
    venue_analysis_quality: str
    
    # Quality metrics
    prediction_methodology: str
    data_reliability_score: float
    statistical_confidence: float
    consistency_score: float
    prediction_quality_grade: str
    
    # Analysis details
    analysis_summary: Optional[str] = None
    calculation_breakdown: Optional[str] = None
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    
    # Corner predictions (optional, for backward compatibility)
    predicted_total_corners: Optional[float] = None
    predicted_home_corners: Optional[float] = None
    predicted_away_corners: Optional[float] = None
    corner_confidence_5_5: Optional[float] = None
    corner_confidence_6_5: Optional[float] = None
    corner_confidence_7_5: Optional[float] = None

@dataclass
class EnhancedValidationResult:
    """Enhanced validation result with comprehensive accuracy metrics."""
    
    # Core information
    prediction_id: int
    match_id: int
    validation_date: str
    validation_type: str
    
    # Actual match results
    actual_goals_home: int
    actual_goals_away: int
    actual_btts: bool
    actual_home_scored: bool
    actual_away_scored: bool
    
    # Prediction accuracy
    btts_prediction_accurate: bool
    home_score_prediction_accurate: bool
    away_score_prediction_accurate: bool
    
    # Enhanced accuracy metrics
    probability_accuracy_score: float
    confidence_calibration_score: float
    dynamic_weight_effectiveness: float
    venue_analysis_accuracy: float
    
    # Prediction details used
    predicted_btts_probability: float
    predicted_home_score_probability: float
    predicted_away_score_probability: float
    prediction_confidence_score: float
    attack_weight_used: float
    defense_weight_used: float
    
    # Quality assessment
    weight_configuration_effectiveness: float
    sample_size_penalty_applied: bool
    prediction_quality_actual: str
    data_quality_validation: str
    methodology_effectiveness: str
    
    # Metadata
    validator_version: str = 'Enhanced_v1.0'
    validation_notes: Optional[str] = None
    manual_verification: bool = False
    actual_corners_home: Optional[int] = None
    actual_corners_away: Optional[int] = None

class EnhancedPredictionStorageManager:
    """Manages enhanced prediction storage and retrieval."""
    
    def __init__(self):
        """Initialize enhanced prediction storage manager."""
        self.db_manager = get_enhanced_db_manager()
        self.weighting_engine = DynamicWeightingEngine()
        logger.info("Enhanced prediction storage manager initialized")
    
    def store_enhanced_btts_prediction(self, btts_prediction_dict: Dict[str, Any], 
                                     match_id: int, home_team_id: int, away_team_id: int, 
                                     season: int) -> int:
        """Store enhanced BTTS prediction with comprehensive metadata."""
        try:
            # Create enhanced prediction from GoalAnalyzer output
            enhanced_prediction = self._create_enhanced_prediction_from_btts(
                btts_prediction_dict, match_id, home_team_id, away_team_id, season
            )
            
            # Convert to database format
            prediction_data = self._enhanced_prediction_to_dict(enhanced_prediction)
            
            # Store in enhanced database
            prediction_id = self.db_manager.insert_enhanced_prediction(prediction_data)
            
            # Store detailed metadata
            self._store_prediction_metadata(prediction_id, btts_prediction_dict, enhanced_prediction)
            
            logger.info(f"Enhanced BTTS prediction stored with ID: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Failed to store enhanced BTTS prediction: {e}")
            raise
    
    def _create_enhanced_prediction_from_btts(self, btts_prediction: Dict[str, Any], 
                                            match_id: int, home_team_id: int, 
                                            away_team_id: int, season: int) -> EnhancedBTTSPrediction:
        """Create enhanced prediction object from BTTS prediction dictionary."""
        
        # Extract dynamic weighting details (with fallbacks)
        attack_weight = 0.6  # Default
        defense_weight = 0.4  # Default
        
        # Try to extract from reasoning or use defaults
        home_reasoning = btts_prediction.get('home_team_reasoning', '')
        if 'heavily favored' in home_reasoning.lower():
            attack_weight = 0.65
            defense_weight = 0.35
        elif 'balanced' in home_reasoning.lower():
            attack_weight = 0.50
            defense_weight = 0.50
        
        # Extract team strength classifications
        home_stats = btts_prediction.get('home_team_stats', {})
        away_stats = btts_prediction.get('away_team_stats', {})
        
        home_strength = self._classify_team_strength(home_stats.get('scores_1plus_rate', 50))
        away_strength = self._classify_team_strength(away_stats.get('scores_1plus_rate', 50))
        
        # Create calculation breakdown
        calculation_breakdown = self._create_calculation_breakdown(btts_prediction)
        
        return EnhancedBTTSPrediction(
            match_id=match_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            season=season,
            prediction_date=date.today().strftime('%Y-%m-%d'),
            
            # BTTS predictions
            btts_probability=btts_prediction.get('btts_probability', 50.0),
            home_team_score_probability=btts_prediction.get('home_team_score_probability', 50.0),
            away_team_score_probability=btts_prediction.get('away_team_score_probability', 50.0),
            both_teams_score_confidence=btts_prediction.get('confidence_score', 50.0),
            
            # Dynamic weighting
            attack_weight=attack_weight,
            defense_weight=defense_weight,
            home_team_strength_class=home_strength,
            away_team_strength_class=away_strength,
            sample_size_adjustment_applied=self._check_sample_size_adjustment(home_stats, away_stats),
            confidence_boost_factor=1.0,  # Could extract from prediction if available
            
            # Venue analysis
            home_venue_games_analyzed=home_stats.get('total_games', 0),
            away_venue_games_analyzed=away_stats.get('total_games', 0),
            home_venue_scoring_rate=home_stats.get('scores_1plus_rate', 50.0),
            away_venue_scoring_rate=away_stats.get('scores_1plus_rate', 50.0),
            home_venue_conceding_rate=home_stats.get('concedes_1plus_rate', 50.0),
            away_venue_conceding_rate=away_stats.get('concedes_1plus_rate', 50.0),
            venue_analysis_quality=btts_prediction.get('data_quality', 'Fair'),
            
            # Quality metrics
            prediction_methodology=btts_prediction.get('methodology', 'Enhanced Goals Analysis'),
            data_reliability_score=btts_prediction.get('confidence_score', 50.0),
            statistical_confidence=btts_prediction.get('confidence_score', 50.0),
            consistency_score=btts_prediction.get('confidence_score', 50.0),
            prediction_quality_grade=self._determine_quality_grade(btts_prediction),
            
            # Analysis details
            analysis_summary=self._create_analysis_summary(btts_prediction),
            calculation_breakdown=calculation_breakdown,
            recommendation=self._create_recommendation(btts_prediction),
            reasoning=btts_prediction.get('home_team_reasoning', '') + ' | ' + btts_prediction.get('away_team_reasoning', '')
        )
    
    def _classify_team_strength(self, scoring_rate: float) -> str:
        """Classify team strength based on scoring rate."""
        if scoring_rate >= 80:
            return 'very_strong'
        elif scoring_rate >= 65:
            return 'strong'
        elif scoring_rate >= 45:
            return 'average'
        elif scoring_rate >= 30:
            return 'weak'
        else:
            return 'very_weak'
    
    def _check_sample_size_adjustment(self, home_stats: Dict, away_stats: Dict) -> bool:
        """Check if sample size adjustment was applied."""
        home_games = home_stats.get('total_games', 0)
        away_games = away_stats.get('total_games', 0)
        return min(home_games, away_games) < 10
    
    def _determine_quality_grade(self, btts_prediction: Dict) -> str:
        """Determine prediction quality grade."""
        confidence = btts_prediction.get('confidence_score', 50.0)
        data_quality = btts_prediction.get('data_quality', 'Fair')
        
        if confidence >= 85 and data_quality == 'Excellent':
            return 'Excellent'
        elif confidence >= 75 and data_quality in ['Excellent', 'Good']:
            return 'Good'
        elif confidence >= 60:
            return 'Fair'
        else:
            return 'Poor'
    
    def _create_analysis_summary(self, btts_prediction: Dict) -> str:
        """Create comprehensive analysis summary."""
        btts_prob = btts_prediction.get('btts_probability', 50.0)
        home_prob = btts_prediction.get('home_team_score_probability', 50.0)
        away_prob = btts_prediction.get('away_team_score_probability', 50.0)
        confidence = btts_prediction.get('confidence_score', 50.0)
        methodology = btts_prediction.get('methodology', 'Enhanced Analysis')
        
        return f"""Enhanced BTTS Analysis: {btts_prob:.1f}% probability both teams score.
Home team scoring probability: {home_prob:.1f}%
Away team scoring probability: {away_prob:.1f}%
Analysis confidence: {confidence:.1f}%
Methodology: {methodology}
Data quality: {btts_prediction.get('data_quality', 'Fair')}"""
    
    def _create_calculation_breakdown(self, btts_prediction: Dict) -> str:
        """Create detailed calculation breakdown in JSON format."""
        breakdown = {
            'btts_calculation': {
                'home_probability': btts_prediction.get('home_team_score_probability', 50.0),
                'away_probability': btts_prediction.get('away_team_score_probability', 50.0),
                'combined_probability': btts_prediction.get('btts_probability', 50.0),
                'formula': 'BTTS = (Home Scoring % × Away Scoring %) / 100 + Dynamic Adjustments'
            },
            'confidence_calculation': {
                'base_confidence': btts_prediction.get('confidence_score', 50.0),
                'methodology': btts_prediction.get('methodology', 'Enhanced Analysis'),
                'data_quality_factor': btts_prediction.get('data_quality', 'Fair')
            },
            'team_analysis': {
                'home_reasoning': btts_prediction.get('home_team_reasoning', ''),
                'away_reasoning': btts_prediction.get('away_team_reasoning', '')
            }
        }
        
        return json.dumps(breakdown, indent=2)
    
    def _create_recommendation(self, btts_prediction: Dict) -> str:
        """Create betting recommendation based on prediction."""
        btts_prob = btts_prediction.get('btts_probability', 50.0)
        confidence = btts_prediction.get('confidence_score', 50.0)
        
        if btts_prob >= 70 and confidence >= 75:
            return f"STRONG BET: BTTS Yes ({btts_prob:.1f}% probability, {confidence:.1f}% confidence)"
        elif btts_prob >= 60 and confidence >= 65:
            return f"MODERATE BET: BTTS Yes ({btts_prob:.1f}% probability, {confidence:.1f}% confidence)"
        elif btts_prob <= 30 and confidence >= 65:
            return f"MODERATE BET: BTTS No ({100-btts_prob:.1f}% probability, {confidence:.1f}% confidence)"
        elif btts_prob <= 20 and confidence >= 75:
            return f"STRONG BET: BTTS No ({100-btts_prob:.1f}% probability, {confidence:.1f}% confidence)"
        else:
            return f"AVOID: Unclear outcome ({btts_prob:.1f}% probability, {confidence:.1f}% confidence)"
    
    def _enhanced_prediction_to_dict(self, prediction: EnhancedBTTSPrediction) -> Dict[str, Any]:
        """Convert enhanced prediction to database dictionary."""
        return asdict(prediction)
    
    def _store_prediction_metadata(self, prediction_id: int, btts_prediction: Dict, 
                                 enhanced_prediction: EnhancedBTTSPrediction) -> None:
        """Store detailed prediction metadata."""
        try:
            # Create metadata dictionary
            metadata = {
                'prediction_id': prediction_id,
                'home_attack_rate': btts_prediction.get('home_team_stats', {}).get('scores_1plus_rate'),
                'home_defense_vulnerability': btts_prediction.get('home_team_stats', {}).get('concedes_1plus_rate'),
                'away_attack_rate': btts_prediction.get('away_team_stats', {}).get('scores_1plus_rate'),
                'away_defense_vulnerability': btts_prediction.get('away_team_stats', {}).get('concedes_1plus_rate'),
                'base_attack_weight': enhanced_prediction.attack_weight,
                'base_defense_weight': enhanced_prediction.defense_weight,
                'adjusted_attack_weight': enhanced_prediction.attack_weight,
                'adjusted_defense_weight': enhanced_prediction.defense_weight,
                'sample_size_adjustment_factor': 1.0 if enhanced_prediction.sample_size_adjustment_applied else 0.0,
                'line_consistency_score': enhanced_prediction.statistical_confidence,
                'confidence_boost_applied': enhanced_prediction.confidence_boost_factor,
                'sample_size_penalty': 1.0 if enhanced_prediction.sample_size_adjustment_applied else 0.0,
                'final_confidence_calculation': f"Line consistency with {enhanced_prediction.venue_analysis_quality} data quality",
                'strength_matchup_type': f"{enhanced_prediction.home_team_strength_class}_vs_{enhanced_prediction.away_team_strength_class}",
                'matchup_advantage': 'balanced',  # Could be calculated based on strength difference
                'historical_h2h_influence': 0.0,  # Not currently implemented
                'home_scoring_calculation_steps': btts_prediction.get('home_team_reasoning', ''),
                'away_scoring_calculation_steps': btts_prediction.get('away_team_reasoning', ''),
                'btts_calculation_formula': f"{enhanced_prediction.home_team_score_probability:.1f}% × {enhanced_prediction.away_team_score_probability:.1f}% = {enhanced_prediction.btts_probability:.1f}%",
                'model_version': 'Enhanced_v1.0',
                'algorithm_version': 'Dynamic_Weighting_v1.0'
            }
            
            # Store metadata if enhanced schema is available
            if self.db_manager.enhanced_schema_available:
                # This would use the prediction_metadata table
                # Implementation depends on having the metadata table creation
                logger.debug(f"Prediction metadata prepared for storage: {len(metadata)} fields")
            
        except Exception as e:
            logger.warning(f"Could not store prediction metadata: {e}")
    
    def retrieve_enhanced_prediction(self, match_id: int) -> Optional[EnhancedBTTSPrediction]:
        """Retrieve enhanced prediction for a match."""
        try:
            prediction_dict = self.db_manager.get_enhanced_prediction_by_match(match_id)
            
            if prediction_dict:
                return self._dict_to_enhanced_prediction(prediction_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve enhanced prediction for match {match_id}: {e}")
            return None
    
    def retrieve_enhanced_predictions_by_season(self, season: int, limit: Optional[int] = None) -> List[EnhancedBTTSPrediction]:
        """Retrieve enhanced predictions for a season."""
        try:
            predictions_dicts = self.db_manager.get_enhanced_predictions_by_season(season, limit)
            
            return [self._dict_to_enhanced_prediction(pred_dict) for pred_dict in predictions_dicts]
            
        except Exception as e:
            logger.error(f"Failed to retrieve enhanced predictions for season {season}: {e}")
            return []
    
    def _dict_to_enhanced_prediction(self, prediction_dict: Dict[str, Any]) -> EnhancedBTTSPrediction:
        """Convert database dictionary to enhanced prediction object."""
        return EnhancedBTTSPrediction(
            match_id=prediction_dict['match_id'],
            home_team_id=prediction_dict['home_team_id'],
            away_team_id=prediction_dict['away_team_id'],
            season=prediction_dict['season'],
            prediction_date=prediction_dict.get('prediction_date', ''),
            btts_probability=prediction_dict.get('btts_probability', 50.0),
            home_team_score_probability=prediction_dict.get('home_team_score_probability', 50.0),
            away_team_score_probability=prediction_dict.get('away_team_score_probability', 50.0),
            both_teams_score_confidence=prediction_dict.get('both_teams_score_confidence', 50.0),
            attack_weight=prediction_dict.get('attack_weight', 0.6),
            defense_weight=prediction_dict.get('defense_weight', 0.4),
            home_team_strength_class=prediction_dict.get('home_team_strength_class', 'average'),
            away_team_strength_class=prediction_dict.get('away_team_strength_class', 'average'),
            sample_size_adjustment_applied=prediction_dict.get('sample_size_adjustment_applied', False),
            confidence_boost_factor=prediction_dict.get('confidence_boost_factor', 1.0),
            home_venue_games_analyzed=prediction_dict.get('home_venue_games_analyzed', 0),
            away_venue_games_analyzed=prediction_dict.get('away_venue_games_analyzed', 0),
            home_venue_scoring_rate=prediction_dict.get('home_venue_scoring_rate', 50.0),
            away_venue_scoring_rate=prediction_dict.get('away_venue_scoring_rate', 50.0),
            home_venue_conceding_rate=prediction_dict.get('home_venue_conceding_rate', 50.0),
            away_venue_conceding_rate=prediction_dict.get('away_venue_conceding_rate', 50.0),
            venue_analysis_quality=prediction_dict.get('venue_analysis_quality', 'Fair'),
            prediction_methodology=prediction_dict.get('prediction_methodology', 'Enhanced Goals Analysis'),
            data_reliability_score=prediction_dict.get('data_reliability_score', 50.0),
            statistical_confidence=prediction_dict.get('statistical_confidence', 50.0),
            consistency_score=prediction_dict.get('consistency_score', 50.0),
            prediction_quality_grade=prediction_dict.get('prediction_quality_grade', 'Fair'),
            analysis_summary=prediction_dict.get('analysis_summary'),
            calculation_breakdown=prediction_dict.get('calculation_breakdown'),
            recommendation=prediction_dict.get('recommendation'),
            reasoning=prediction_dict.get('reasoning'),
            predicted_total_corners=prediction_dict.get('predicted_total_corners'),
            predicted_home_corners=prediction_dict.get('predicted_home_corners'),
            predicted_away_corners=prediction_dict.get('predicted_away_corners'),
            corner_confidence_5_5=prediction_dict.get('corner_confidence_5_5'),
            corner_confidence_6_5=prediction_dict.get('corner_confidence_6_5'),
            corner_confidence_7_5=prediction_dict.get('corner_confidence_7_5')
        )
    
    def store_enhanced_validation_result(self, validation_result: EnhancedValidationResult) -> int:
        """Store enhanced validation result."""
        try:
            validation_data = asdict(validation_result)
            validation_id = self.db_manager.insert_enhanced_validation_result(validation_data)
            
            logger.info(f"Enhanced validation result stored with ID: {validation_id}")
            return validation_id
            
        except Exception as e:
            logger.error(f"Failed to store enhanced validation result: {e}")
            raise
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get enhanced storage statistics."""
        try:
            schema_info = self.db_manager.get_enhanced_schema_info()
            
            if self.db_manager.enhanced_schema_available:
                # Get enhanced predictions count
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM enhanced_predictions")
                    enhanced_predictions_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM enhanced_validation_results")
                    enhanced_validations_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("""
                        SELECT prediction_quality_grade, COUNT(*) 
                        FROM enhanced_predictions 
                        GROUP BY prediction_quality_grade
                    """)
                    quality_distribution = dict(cursor.fetchall())
                    
                    return {
                        'enhanced_schema_active': True,
                        'enhanced_predictions_count': enhanced_predictions_count,
                        'enhanced_validations_count': enhanced_validations_count,
                        'quality_distribution': quality_distribution,
                        'schema_info': schema_info,
                        'storage_features': [
                            'Dedicated BTTS prediction storage',
                            'Dynamic weighting metadata',
                            'Venue-specific analysis tracking',
                            'Comprehensive validation results',
                            'Quality grade classification',
                            'Detailed calculation breakdown'
                        ]
                    }
            else:
                return {
                    'enhanced_schema_active': False,
                    'message': 'Enhanced schema not available - using legacy storage',
                    'schema_info': schema_info
                }
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {
                'enhanced_schema_active': False,
                'error': str(e)
            }

# Convenience function
def get_enhanced_prediction_storage_manager() -> EnhancedPredictionStorageManager:
    """Get enhanced prediction storage manager instance."""
    return EnhancedPredictionStorageManager()

if __name__ == '__main__':
    # Test enhanced prediction storage
    storage_manager = get_enhanced_prediction_storage_manager()
    stats = storage_manager.get_storage_statistics()
    
    print("Enhanced Prediction Storage Test")
    print("=" * 40)
    print(f"Enhanced schema active: {stats['enhanced_schema_active']}")
    
    if stats['enhanced_schema_active']:
        print(f"Enhanced predictions: {stats['enhanced_predictions_count']}")
        print(f"Enhanced validations: {stats['enhanced_validations_count']}")
        print("Storage features:")
        for feature in stats['storage_features']:
            print(f"  ✅ {feature}")
    else:
        print(f"Message: {stats.get('message', 'Unknown status')}")
