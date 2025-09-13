#!/usr/bin/env python3
"""
Enhanced Database Schema for Sophisticated BTTS Predictions.
Phase 2 Implementation: Add dedicated BTTS fields and comprehensive prediction storage.
"""

import sqlite3
import logging
from datetime import date
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EnhancedDatabaseSchema:
    """Enhanced database schema with dedicated BTTS prediction fields."""
    
    @staticmethod
    def get_enhanced_predictions_table_sql() -> str:
        """Enhanced predictions table with dedicated BTTS fields."""
        return """
        CREATE TABLE IF NOT EXISTS enhanced_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            prediction_date DATE NOT NULL,
            season INTEGER NOT NULL,
            
            -- Corner Predictions (existing functionality)
            predicted_total_corners REAL,
            predicted_home_corners REAL,
            predicted_away_corners REAL,
            corner_confidence_5_5 REAL,
            corner_confidence_6_5 REAL,
            corner_confidence_7_5 REAL,
            
            -- BTTS Predictions (NEW: dedicated fields)
            btts_probability REAL NOT NULL DEFAULT 50.0,
            home_team_score_probability REAL NOT NULL DEFAULT 50.0,
            away_team_score_probability REAL NOT NULL DEFAULT 50.0,
            both_teams_score_confidence REAL NOT NULL DEFAULT 50.0,
            
            -- Dynamic Weighting Analysis (NEW)
            attack_weight REAL NOT NULL DEFAULT 0.6,
            defense_weight REAL NOT NULL DEFAULT 0.4,
            home_team_strength_class TEXT NOT NULL DEFAULT 'average',
            away_team_strength_class TEXT NOT NULL DEFAULT 'average',
            sample_size_adjustment_applied BOOLEAN DEFAULT FALSE,
            confidence_boost_factor REAL DEFAULT 1.0,
            
            -- Venue-Specific Analysis (NEW)
            home_venue_games_analyzed INTEGER DEFAULT 0,
            away_venue_games_analyzed INTEGER DEFAULT 0,
            home_venue_scoring_rate REAL DEFAULT 50.0,
            away_venue_scoring_rate REAL DEFAULT 50.0,
            home_venue_conceding_rate REAL DEFAULT 50.0,
            away_venue_conceding_rate REAL DEFAULT 50.0,
            venue_analysis_quality TEXT DEFAULT 'Fair',
            
            -- Prediction Quality Metrics (Enhanced)
            prediction_methodology TEXT DEFAULT 'Enhanced Goals Analysis',
            data_reliability_score REAL DEFAULT 50.0,
            statistical_confidence REAL DEFAULT 50.0,
            consistency_score REAL DEFAULT 50.0,
            prediction_quality_grade TEXT DEFAULT 'Fair',
            
            -- Analysis Metadata
            analysis_summary TEXT,
            calculation_breakdown TEXT,
            recommendation TEXT,
            reasoning TEXT,
            
            -- Team References
            home_team_id INTEGER NOT NULL,
            away_team_id INTEGER NOT NULL,
            
            -- Audit Fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (home_team_id) REFERENCES teams (id),
            FOREIGN KEY (away_team_id) REFERENCES teams (id),
            
            -- Constraints
            CHECK (btts_probability >= 0 AND btts_probability <= 100),
            CHECK (home_team_score_probability >= 0 AND home_team_score_probability <= 100),
            CHECK (away_team_score_probability >= 0 AND away_team_score_probability <= 100),
            CHECK (attack_weight + defense_weight = 1.0),
            CHECK (home_team_strength_class IN ('very_strong', 'strong', 'average', 'weak', 'very_weak')),
            CHECK (away_team_strength_class IN ('very_strong', 'strong', 'average', 'weak', 'very_weak')),
            CHECK (venue_analysis_quality IN ('Excellent', 'Good', 'Fair', 'Poor')),
            CHECK (prediction_quality_grade IN ('Excellent', 'Good', 'Fair', 'Poor')),
            
            -- Unique constraint: one prediction per match
            UNIQUE(match_id)
        )
        """
    
    @staticmethod
    def get_enhanced_validation_results_table_sql() -> str:
        """Enhanced validation results with comprehensive BTTS tracking."""
        return """
        CREATE TABLE IF NOT EXISTS enhanced_validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            validation_date DATE NOT NULL,
            validation_type TEXT NOT NULL DEFAULT 'enhanced_btts',
            
            -- Actual Match Results
            actual_goals_home INTEGER NOT NULL,
            actual_goals_away INTEGER NOT NULL,
            actual_corners_home INTEGER,
            actual_corners_away INTEGER,
            actual_btts BOOLEAN NOT NULL,
            actual_home_scored BOOLEAN NOT NULL,
            actual_away_scored BOOLEAN NOT NULL,
            
            -- BTTS Prediction Accuracy (Enhanced)
            btts_prediction_accurate BOOLEAN,
            home_score_prediction_accurate BOOLEAN,
            away_score_prediction_accurate BOOLEAN,
            
            -- Sophisticated Accuracy Metrics
            probability_accuracy_score REAL,  -- How close BTTS probability was to outcome
            confidence_calibration_score REAL, -- How well confidence matched success
            dynamic_weight_effectiveness REAL, -- How well weights predicted outcome
            venue_analysis_accuracy REAL,     -- How accurate venue-specific analysis was
            
            -- Prediction Performance Analysis
            predicted_btts_probability REAL,
            predicted_home_score_probability REAL,
            predicted_away_score_probability REAL,
            prediction_confidence_score REAL,
            
            -- Dynamic Weighting Validation
            attack_weight_used REAL,
            defense_weight_used REAL,
            weight_configuration_effectiveness REAL,
            sample_size_penalty_applied BOOLEAN,
            
            -- Quality Assessment
            prediction_quality_actual TEXT,
            data_quality_validation TEXT,
            methodology_effectiveness TEXT,
            
            -- Validation Metadata
            validator_version TEXT DEFAULT 'Enhanced_v1.0',
            validation_notes TEXT,
            manual_verification BOOLEAN DEFAULT FALSE,
            
            -- Audit Fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (prediction_id) REFERENCES enhanced_predictions (id),
            FOREIGN KEY (match_id) REFERENCES matches (id),
            
            -- Constraints
            CHECK (probability_accuracy_score >= 0 AND probability_accuracy_score <= 100),
            CHECK (confidence_calibration_score >= 0 AND confidence_calibration_score <= 100),
            CHECK (dynamic_weight_effectiveness >= 0 AND dynamic_weight_effectiveness <= 100),
            CHECK (prediction_quality_actual IN ('Excellent', 'Good', 'Fair', 'Poor')),
            
            -- Unique constraint: one validation per prediction
            UNIQUE(prediction_id)
        )
        """
    
    @staticmethod
    def get_team_performance_analysis_table_sql() -> str:
        """Team performance analysis for sophisticated predictions."""
        return """
        CREATE TABLE IF NOT EXISTS team_performance_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            season INTEGER NOT NULL,
            analysis_date DATE NOT NULL,
            venue TEXT NOT NULL CHECK (venue IN ('home', 'away', 'combined')),
            
            -- Goal Performance Metrics
            games_analyzed INTEGER NOT NULL DEFAULT 0,
            goals_scored_total INTEGER DEFAULT 0,
            goals_conceded_total INTEGER DEFAULT 0,
            clean_sheets INTEGER DEFAULT 0,
            
            -- Scoring Pattern Analysis
            scores_1plus_count INTEGER DEFAULT 0,
            scores_1plus_rate REAL DEFAULT 0.0,
            scores_2plus_count INTEGER DEFAULT 0,
            scores_2plus_rate REAL DEFAULT 0.0,
            scores_3plus_count INTEGER DEFAULT 0,
            scores_3plus_rate REAL DEFAULT 0.0,
            
            -- Conceding Pattern Analysis
            concedes_1plus_count INTEGER DEFAULT 0,
            concedes_1plus_rate REAL DEFAULT 0.0,
            concedes_2plus_count INTEGER DEFAULT 0,
            concedes_2plus_rate REAL DEFAULT 0.0,
            concedes_3plus_count INTEGER DEFAULT 0,
            concedes_3plus_rate REAL DEFAULT 0.0,
            
            -- Performance Averages
            avg_goals_scored REAL DEFAULT 0.0,
            avg_goals_conceded REAL DEFAULT 0.0,
            avg_goal_difference REAL DEFAULT 0.0,
            
            -- Strength Classification
            attack_strength_class TEXT DEFAULT 'average',
            defense_strength_class TEXT DEFAULT 'average',
            overall_strength_rating REAL DEFAULT 50.0,
            
            -- Form Analysis
            recent_form_trend TEXT DEFAULT 'stable',
            form_consistency_score REAL DEFAULT 50.0,
            
            -- Quality Metrics
            data_quality TEXT DEFAULT 'Fair',
            analysis_reliability REAL DEFAULT 50.0,
            sample_size_adequacy TEXT DEFAULT 'adequate',
            
            -- Audit Fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (team_id) REFERENCES teams (id),
            
            -- Constraints
            CHECK (scores_1plus_rate >= 0 AND scores_1plus_rate <= 100),
            CHECK (concedes_1plus_rate >= 0 AND concedes_1plus_rate <= 100),
            CHECK (attack_strength_class IN ('very_strong', 'strong', 'average', 'weak', 'very_weak')),
            CHECK (defense_strength_class IN ('very_strong', 'strong', 'average', 'weak', 'very_weak')),
            CHECK (recent_form_trend IN ('improving', 'stable', 'declining', 'insufficient_data')),
            CHECK (data_quality IN ('Excellent', 'Good', 'Fair', 'Poor')),
            CHECK (sample_size_adequacy IN ('excellent', 'good', 'adequate', 'limited', 'insufficient')),
            
            -- Unique constraint: one analysis per team/season/venue/date
            UNIQUE(team_id, season, venue, analysis_date)
        )
        """
    
    @staticmethod
    def get_prediction_metadata_table_sql() -> str:
        """Detailed prediction metadata and calculation breakdown."""
        return """
        CREATE TABLE IF NOT EXISTS prediction_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            
            -- Calculation Breakdown
            home_attack_rate REAL,
            home_defense_vulnerability REAL,
            away_attack_rate REAL,
            away_defense_vulnerability REAL,
            
            -- Dynamic Weighting Details
            base_attack_weight REAL,
            base_defense_weight REAL,
            adjusted_attack_weight REAL,
            adjusted_defense_weight REAL,
            sample_size_adjustment_factor REAL,
            
            -- Confidence Calculation Breakdown
            line_consistency_score REAL,
            confidence_boost_applied REAL,
            sample_size_penalty REAL,
            final_confidence_calculation TEXT,
            
            -- Team Matchup Analysis
            strength_matchup_type TEXT,
            matchup_advantage TEXT,
            historical_h2h_influence REAL,
            
            -- Calculation Steps (JSON)
            home_scoring_calculation_steps TEXT,
            away_scoring_calculation_steps TEXT,
            btts_calculation_formula TEXT,
            
            -- API and External Data
            api_data_quality TEXT,
            external_factors TEXT,
            weather_impact TEXT,
            
            -- Model Version
            model_version TEXT DEFAULT 'Enhanced_v1.0',
            algorithm_version TEXT DEFAULT 'Dynamic_Weighting_v1.0',
            
            -- Audit Fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (prediction_id) REFERENCES enhanced_predictions (id),
            
            -- Constraints
            CHECK (strength_matchup_type IN ('elite_clash', 'balanced_matchup', 'attack_dominance', 'defense_dominance', 'strength_mismatch', 'low_quality_matchup')),
            CHECK (matchup_advantage IN ('home', 'away', 'balanced', 'uncertain')),
            
            -- Unique constraint: one metadata per prediction
            UNIQUE(prediction_id)
        )
        """
    
    @staticmethod
    def get_system_performance_metrics_table_sql() -> str:
        """System-wide performance tracking for the enhanced prediction system."""
        return """
        CREATE TABLE IF NOT EXISTS system_performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_date DATE NOT NULL,
            season INTEGER NOT NULL,
            time_period TEXT NOT NULL CHECK (time_period IN ('daily', 'weekly', 'monthly', 'seasonal')),
            
            -- Overall Performance Metrics
            total_predictions INTEGER DEFAULT 0,
            total_validations INTEGER DEFAULT 0,
            validation_rate REAL DEFAULT 0.0,
            
            -- BTTS Performance
            btts_predictions_count INTEGER DEFAULT 0,
            btts_accuracy_rate REAL DEFAULT 0.0,
            btts_avg_probability_accuracy REAL DEFAULT 0.0,
            btts_avg_confidence_calibration REAL DEFAULT 0.0,
            
            -- Dynamic Weighting Performance
            avg_weight_effectiveness REAL DEFAULT 0.0,
            attack_weight_success_rate REAL DEFAULT 0.0,
            defense_weight_success_rate REAL DEFAULT 0.0,
            sample_size_adjustments_applied INTEGER DEFAULT 0,
            
            -- Data Quality Metrics
            excellent_quality_predictions INTEGER DEFAULT 0,
            good_quality_predictions INTEGER DEFAULT 0,
            fair_quality_predictions INTEGER DEFAULT 0,
            poor_quality_predictions INTEGER DEFAULT 0,
            avg_data_reliability_score REAL DEFAULT 0.0,
            
            -- Venue Analysis Performance
            home_venue_accuracy REAL DEFAULT 0.0,
            away_venue_accuracy REAL DEFAULT 0.0,
            venue_analysis_effectiveness REAL DEFAULT 0.0,
            
            -- Confidence Calibration Analysis
            high_confidence_accuracy REAL DEFAULT 0.0,
            medium_confidence_accuracy REAL DEFAULT 0.0,
            low_confidence_accuracy REAL DEFAULT 0.0,
            confidence_calibration_score REAL DEFAULT 0.0,
            
            -- System Health Indicators
            processing_time_avg_ms REAL DEFAULT 0.0,
            database_performance_score REAL DEFAULT 100.0,
            api_availability_rate REAL DEFAULT 100.0,
            error_rate REAL DEFAULT 0.0,
            
            -- Audit Fields
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CHECK (validation_rate >= 0 AND validation_rate <= 100),
            CHECK (btts_accuracy_rate >= 0 AND btts_accuracy_rate <= 100),
            CHECK (avg_data_reliability_score >= 0 AND avg_data_reliability_score <= 100),
            
            -- Unique constraint: one metric per date/season/period
            UNIQUE(metric_date, season, time_period)
        )
        """

    @staticmethod
    def get_all_enhanced_tables() -> Dict[str, str]:
        """Get all enhanced table definitions."""
        return {
            'enhanced_predictions': EnhancedDatabaseSchema.get_enhanced_predictions_table_sql(),
            'enhanced_validation_results': EnhancedDatabaseSchema.get_enhanced_validation_results_table_sql(),
            'team_performance_analysis': EnhancedDatabaseSchema.get_team_performance_analysis_table_sql(),
            'prediction_metadata': EnhancedDatabaseSchema.get_prediction_metadata_table_sql(),
            'system_performance_metrics': EnhancedDatabaseSchema.get_system_performance_metrics_table_sql()
        }

    @staticmethod
    def get_enhanced_indexes() -> Dict[str, str]:
        """Get optimized indexes for enhanced schema."""
        return {
            'idx_enhanced_predictions_match': 'CREATE INDEX IF NOT EXISTS idx_enhanced_predictions_match ON enhanced_predictions(match_id)',
            'idx_enhanced_predictions_season': 'CREATE INDEX IF NOT EXISTS idx_enhanced_predictions_season ON enhanced_predictions(season)',
            'idx_enhanced_predictions_date': 'CREATE INDEX IF NOT EXISTS idx_enhanced_predictions_date ON enhanced_predictions(prediction_date)',
            'idx_enhanced_predictions_teams': 'CREATE INDEX IF NOT EXISTS idx_enhanced_predictions_teams ON enhanced_predictions(home_team_id, away_team_id)',
            'idx_enhanced_predictions_quality': 'CREATE INDEX IF NOT EXISTS idx_enhanced_predictions_quality ON enhanced_predictions(prediction_quality_grade)',
            
            'idx_enhanced_validation_match': 'CREATE INDEX IF NOT EXISTS idx_enhanced_validation_match ON enhanced_validation_results(match_id)',
            'idx_enhanced_validation_prediction': 'CREATE INDEX IF NOT EXISTS idx_enhanced_validation_prediction ON enhanced_validation_results(prediction_id)',
            'idx_enhanced_validation_date': 'CREATE INDEX IF NOT EXISTS idx_enhanced_validation_date ON enhanced_validation_results(validation_date)',
            'idx_enhanced_validation_type': 'CREATE INDEX IF NOT EXISTS idx_enhanced_validation_type ON enhanced_validation_results(validation_type)',
            
            'idx_team_performance_team_season': 'CREATE INDEX IF NOT EXISTS idx_team_performance_team_season ON team_performance_analysis(team_id, season)',
            'idx_team_performance_venue': 'CREATE INDEX IF NOT EXISTS idx_team_performance_venue ON team_performance_analysis(venue)',
            'idx_team_performance_date': 'CREATE INDEX IF NOT EXISTS idx_team_performance_date ON team_performance_analysis(analysis_date)',
            
            'idx_prediction_metadata_prediction': 'CREATE INDEX IF NOT EXISTS idx_prediction_metadata_prediction ON prediction_metadata(prediction_id)',
            
            'idx_system_metrics_date': 'CREATE INDEX IF NOT EXISTS idx_system_metrics_date ON system_performance_metrics(metric_date)',
            'idx_system_metrics_season': 'CREATE INDEX IF NOT EXISTS idx_system_metrics_season ON system_performance_metrics(season)',
            'idx_system_metrics_period': 'CREATE INDEX IF NOT EXISTS idx_system_metrics_period ON system_performance_metrics(time_period)'
        }

    @staticmethod
    def get_migration_triggers() -> Dict[str, str]:
        """Get database triggers for data consistency."""
        return {
            'update_enhanced_predictions_timestamp': """
                CREATE TRIGGER IF NOT EXISTS update_enhanced_predictions_timestamp
                AFTER UPDATE ON enhanced_predictions
                FOR EACH ROW
                BEGIN
                    UPDATE enhanced_predictions 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """,
            
            'update_team_performance_timestamp': """
                CREATE TRIGGER IF NOT EXISTS update_team_performance_timestamp
                AFTER UPDATE ON team_performance_analysis
                FOR EACH ROW
                BEGIN
                    UPDATE team_performance_analysis 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """,
            
            'validate_prediction_weights': """
                CREATE TRIGGER IF NOT EXISTS validate_prediction_weights
                BEFORE INSERT ON enhanced_predictions
                FOR EACH ROW
                WHEN NEW.attack_weight + NEW.defense_weight != 1.0
                BEGIN
                    SELECT RAISE(ABORT, 'Attack weight + Defense weight must equal 1.0');
                END
            """
        }

if __name__ == '__main__':
    print("Enhanced Database Schema Definitions Generated Successfully!")
    tables = EnhancedDatabaseSchema.get_all_enhanced_tables()
    for table_name, sql in tables.items():
        print(f"✅ {table_name}: {len(sql)} characters")
