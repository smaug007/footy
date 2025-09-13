#!/usr/bin/env python3
"""
System Configuration Manager for Enhanced BTTS Prediction System
Handles seamless legacy-enhanced transitions and feature flags.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemConfigManager:
    """Manages system configuration and feature toggles for enhanced BTTS system."""
    
    def __init__(self):
        """Initialize system configuration manager."""
        self._config = self._load_default_config()
        self._enhanced_status = None
        self._last_status_check = None
        
        logger.debug("SystemConfigManager initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default system configuration."""
        return {
            'features': {
                'enhanced_storage': 'auto',  # auto, enabled, disabled
                'enhanced_validation': 'auto',
                'enhanced_dashboards': 'auto',
                'legacy_fallback': True,
                'auto_migration_prompt': True
            },
            'performance': {
                'cache_predictions': True,
                'cache_timeout_minutes': 15,
                'max_concurrent_predictions': 10,
                'enable_real_time_updates': True
            },
            'ui': {
                'show_enhanced_banners': True,
                'progressive_enhancement': True,
                'mobile_optimized': True,
                'print_friendly': True
            },
            'validation': {
                'min_prediction_confidence': 20.0,
                'enable_accuracy_tracking': True,
                'store_validation_results': True,
                'alert_on_low_accuracy': True
            },
            'system': {
                'debug_mode': False,
                'log_level': 'INFO',
                'max_log_size_mb': 50,
                'backup_predictions': True
            }
        }
    
    def get_enhanced_system_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive enhanced system status with caching."""
        now = datetime.now()
        
        # Use cached status if recent (within 5 minutes)
        if (not force_refresh and self._enhanced_status and self._last_status_check and
            (now - self._last_status_check).total_seconds() < 300):
            return self._enhanced_status
        
        try:
            from data.enhanced_database_manager import get_enhanced_db_manager
            from data.goal_analyzer import GoalAnalyzer
            
            # Check enhanced database
            enhanced_db = get_enhanced_db_manager()
            schema_info = enhanced_db.get_enhanced_schema_info()
            enhanced_available = schema_info.get('enhanced_schema_available', False)
            
            # Check enhanced storage
            storage_status = {}
            if enhanced_available:
                try:
                    goal_analyzer = GoalAnalyzer(use_enhanced_storage=True)
                    storage_status = goal_analyzer.get_enhanced_storage_status()
                except Exception as e:
                    logger.warning(f"Could not check enhanced storage: {e}")
                    storage_status = {'enhanced_storage_enabled': False, 'error': str(e)}
            
            # Check enhanced validation
            validation_status = {}
            if enhanced_available:
                try:
                    from data.enhanced_validation_engine import EnhancedBTTSValidator
                    validator = EnhancedBTTSValidator()
                    validation_status = {
                        'enhanced_validation_available': True,
                        'validator_initialized': validator is not None
                    }
                except Exception as e:
                    logger.warning(f"Could not check enhanced validation: {e}")
                    validation_status = {
                        'enhanced_validation_available': False, 
                        'error': str(e)
                    }
            
            # Compile comprehensive status
            self._enhanced_status = {
                'enhanced_available': enhanced_available,
                'schema_info': schema_info,
                'storage_status': storage_status,
                'validation_status': validation_status,
                'features_enabled': self._get_enabled_features(enhanced_available),
                'last_updated': now.isoformat(),
                'system_health': self._assess_system_health(enhanced_available, storage_status, validation_status)
            }
            
            self._last_status_check = now
            logger.debug(f"Enhanced system status refreshed: {enhanced_available}")
            
        except Exception as e:
            logger.error(f"Error checking enhanced system status: {e}")
            self._enhanced_status = {
                'enhanced_available': False,
                'error': str(e),
                'last_updated': now.isoformat(),
                'system_health': 'error'
            }
        
        return self._enhanced_status
    
    def _get_enabled_features(self, enhanced_available: bool) -> Dict[str, bool]:
        """Determine which features are enabled based on configuration and availability."""
        config = self._config['features']
        
        # Auto mode: enable if enhanced system is available
        def resolve_auto(feature_setting):
            if feature_setting == 'auto':
                return enhanced_available
            return feature_setting == 'enabled'
        
        return {
            'enhanced_storage': resolve_auto(config['enhanced_storage']),
            'enhanced_validation': resolve_auto(config['enhanced_validation']),
            'enhanced_dashboards': resolve_auto(config['enhanced_dashboards']),
            'legacy_fallback': config['legacy_fallback'],
            'auto_migration_prompt': config['auto_migration_prompt'] and not enhanced_available
        }
    
    def _assess_system_health(self, enhanced_available: bool, storage_status: Dict, validation_status: Dict) -> str:
        """Assess overall system health."""
        if not enhanced_available:
            return 'legacy'  # System working but in legacy mode
        
        issues = []
        
        # Check storage
        if not storage_status.get('enhanced_storage_enabled', False):
            issues.append('storage')
        
        # Check validation
        if not validation_status.get('enhanced_validation_available', False):
            issues.append('validation')
        
        if not issues:
            return 'excellent'
        elif len(issues) == 1:
            return 'good'
        else:
            return 'warning'
    
    def should_use_enhanced_features(self, feature_type: str) -> bool:
        """Check if enhanced features should be used for a specific type."""
        status = self.get_enhanced_system_status()
        features_enabled = status.get('features_enabled', {})
        
        return features_enabled.get(feature_type, False)
    
    def get_prediction_strategy(self) -> str:
        """Determine which prediction strategy to use."""
        if self.should_use_enhanced_features('enhanced_storage'):
            return 'enhanced'
        elif self._config['features']['legacy_fallback']:
            return 'legacy'
        else:
            return 'disabled'
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration based on system capabilities."""
        status = self.get_enhanced_system_status()
        features = status.get('features_enabled', {})
        
        return {
            'show_enhanced_banners': features.get('enhanced_dashboards', False),
            'enable_real_time_updates': self._config['performance']['enable_real_time_updates'],
            'cache_timeout': self._config['performance']['cache_timeout_minutes'],
            'progressive_enhancement': self._config['ui']['progressive_enhancement'],
            'mobile_optimized': self._config['ui']['mobile_optimized']
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        status = self.get_enhanced_system_status()
        features = status.get('features_enabled', {})
        validation_config = self._config['validation'].copy()
        
        validation_config['use_enhanced_validation'] = features.get('enhanced_validation', False)
        
        return validation_config
    
    def update_feature_config(self, feature_type: str, enabled: bool):
        """Update feature configuration."""
        if feature_type in self._config['features']:
            self._config['features'][feature_type] = 'enabled' if enabled else 'disabled'
            logger.info(f"Feature {feature_type} {'enabled' if enabled else 'disabled'}")
        else:
            logger.warning(f"Unknown feature type: {feature_type}")
    
    def get_migration_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for system migration/optimization."""
        status = self.get_enhanced_system_status()
        recommendations = []
        
        if not status.get('enhanced_available', False):
            recommendations.append({
                'type': 'migration',
                'priority': 'high',
                'title': 'Enable Enhanced BTTS System',
                'description': 'Run database migration to unlock advanced features',
                'action': 'python migrate_to_enhanced_schema.py',
                'benefits': ['Sophisticated BTTS analysis', 'Advanced validation', 'Professional dashboards']
            })
        
        system_health = status.get('system_health', 'unknown')
        if system_health in ['warning', 'error']:
            recommendations.append({
                'type': 'optimization',
                'priority': 'medium',
                'title': 'System Health Check',
                'description': 'Some enhanced features are not functioning properly',
                'action': 'Check logs and run system diagnostics',
                'benefits': ['Improved reliability', 'Better performance', 'Full feature access']
            })
        
        # Performance recommendations
        if status.get('enhanced_available') and len(status.get('storage_status', {}).get('recent_predictions', [])) > 1000:
            recommendations.append({
                'type': 'performance',
                'priority': 'low',
                'title': 'Database Optimization',
                'description': 'Large number of predictions may slow performance',
                'action': 'Consider archiving old predictions',
                'benefits': ['Faster queries', 'Improved dashboard performance', 'Better user experience']
            })
        
        return {
            'recommendations': recommendations,
            'system_status': system_health,
            'enhanced_available': status.get('enhanced_available', False)
        }

# Global instance
_system_config = None

def get_system_config() -> SystemConfigManager:
    """Get global system configuration manager instance."""
    global _system_config
    if _system_config is None:
        _system_config = SystemConfigManager()
    return _system_config

def should_use_enhanced_features(feature_type: str = 'enhanced_storage') -> bool:
    """Quick check if enhanced features should be used."""
    return get_system_config().should_use_enhanced_features(feature_type)

def get_prediction_strategy() -> str:
    """Quick access to prediction strategy."""
    return get_system_config().get_prediction_strategy()

def get_enhanced_system_status() -> Dict[str, Any]:
    """Quick access to enhanced system status."""
    return get_system_config().get_enhanced_system_status()
