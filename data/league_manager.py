"""
League configuration and season management for multi-league corner prediction system.
Centralized management of league-specific settings and season calculations.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from data.database import get_db_manager

logger = logging.getLogger(__name__)

@dataclass
class LeagueConfig:
    """League configuration data class."""
    id: int
    name: str
    country: str
    country_code: str
    api_league_id: int
    season_structure: str
    season_start_month: int
    season_end_month: int
    active: bool
    priority_order: int

class LeagueManager:
    """Centralized league configuration and season management."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self._league_cache = {}
        self._last_cache_update = None
        logger.info("League Manager initialized")
    
    def _refresh_cache(self):
        """Refresh league cache from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, name, country, country_code, api_league_id, 
                           season_structure, season_start_month, season_end_month, 
                           COALESCE(is_active, active, 1) as active, priority_order
                    FROM leagues 
                    ORDER BY priority_order, name
                """)
                
                self._league_cache = {}
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    league_config = LeagueConfig(
                        id=row_dict['id'],
                        name=row_dict['name'],
                        country=row_dict['country'],
                        country_code=row_dict['country_code'],
                        api_league_id=row_dict['api_league_id'],
                        season_structure=row_dict['season_structure'],
                        season_start_month=row_dict['season_start_month'],
                        season_end_month=row_dict['season_end_month'],
                        active=bool(row_dict['active']),
                        priority_order=row_dict['priority_order']
                    )
                    self._league_cache[league_config.id] = league_config
                
                self._last_cache_update = datetime.now()
                logger.debug(f"League cache refreshed with {len(self._league_cache)} leagues")
                
        except Exception as e:
            logger.error(f"Failed to refresh league cache: {e}")
            raise
    
    def _ensure_cache_fresh(self):
        """Ensure cache is fresh (refresh if needed)."""
        if not self._league_cache or not self._last_cache_update:
            self._refresh_cache()
        # Refresh cache every 10 minutes
        elif (datetime.now() - self._last_cache_update).seconds > 600:
            self._refresh_cache()
    
    def get_league_by_id(self, league_id: int) -> Optional[LeagueConfig]:
        """Get league configuration by database ID."""
        try:
            self._ensure_cache_fresh()
            return self._league_cache.get(league_id)
        except Exception as e:
            logger.error(f"Failed to get league by ID {league_id}: {e}")
            return None
    
    def get_league_by_api_id(self, api_league_id: int) -> Optional[LeagueConfig]:
        """Get league configuration by API-Football league ID."""
        try:
            self._ensure_cache_fresh()
            for league in self._league_cache.values():
                if league.api_league_id == api_league_id:
                    return league
            return None
        except Exception as e:
            logger.error(f"Failed to get league by API ID {api_league_id}: {e}")
            return None
    
    def get_current_season(self, league_id: int) -> int:
        """Calculate current season based on league structure."""
        try:
            league = self.get_league_by_id(league_id)
            if not league:
                logger.warning(f"League {league_id} not found, defaulting to current year")
                return datetime.now().year
            
            now = datetime.now()
            
            if league.season_structure == 'calendar_year':
                # Jan-Dec season (e.g., CSL, MLS)
                return now.year
                
            elif league.season_structure == 'academic_year':
                # Aug-May season (e.g., Premier League, La Liga, Serie A)
                if now.month >= league.season_start_month:
                    return now.year
                else:
                    return now.year - 1
                    
            elif league.season_structure == 'custom':
                # Custom season logic can be added here
                logger.warning(f"Custom season structure for league {league.name} not implemented, using calendar year")
                return now.year
            
            else:
                logger.warning(f"Unknown season structure '{league.season_structure}' for league {league.name}")
                return now.year
                
        except Exception as e:
            logger.error(f"Failed to calculate current season for league {league_id}: {e}")
            return datetime.now().year
    
    def get_active_leagues(self) -> List[LeagueConfig]:
        """Get all active leagues ordered by priority."""
        try:
            self._ensure_cache_fresh()
            active_leagues = [league for league in self._league_cache.values() if league.active]
            return sorted(active_leagues, key=lambda x: (x.priority_order, x.name))
        except Exception as e:
            logger.error(f"Failed to get active leagues: {e}")
            return []
    
    def get_leagues_by_country(self, country_code: str) -> List[LeagueConfig]:
        """Get all leagues for a specific country."""
        try:
            self._ensure_cache_fresh()
            country_leagues = [league for league in self._league_cache.values() 
                             if league.country_code == country_code]
            return sorted(country_leagues, key=lambda x: x.priority_order)
        except Exception as e:
            logger.error(f"Failed to get leagues for country {country_code}: {e}")
            return []
    
    def get_countries_with_leagues(self) -> Dict[str, Dict[str, any]]:
        """Get all countries that have leagues, grouped by country."""
        try:
            self._ensure_cache_fresh()
            countries = {}
            
            for league in self._league_cache.values():
                if league.active:
                    if league.country_code not in countries:
                        countries[league.country_code] = {
                            'country': league.country,
                            'country_code': league.country_code,
                            'leagues': []
                        }
                    
                    countries[league.country_code]['leagues'].append({
                        'id': league.id,
                        'name': league.name,
                        'api_league_id': league.api_league_id,
                        'priority_order': league.priority_order
                    })
            
            # Sort leagues within each country by priority
            for country_data in countries.values():
                country_data['leagues'].sort(key=lambda x: x['priority_order'])
            
            return countries
            
        except Exception as e:
            logger.error(f"Failed to get countries with leagues: {e}")
            return {}
    
    def add_league(self, name: str, country: str, country_code: str, api_league_id: int,
                   season_structure: str = 'academic_year', season_start_month: int = 8,
                   season_end_month: int = 5, active: bool = True, priority_order: int = 100) -> int:
        """Add a new league to the system."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO leagues (name, country, country_code, api_league_id, 
                                       season_structure, season_start_month, season_end_month,
                                       active, priority_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, country, country_code, api_league_id, season_structure,
                     season_start_month, season_end_month, active, priority_order))
                
                conn.commit()
                league_id = cursor.lastrowid
                
                # Refresh cache to include new league
                self._refresh_cache()
                
                logger.info(f"Added new league: {name} (ID: {league_id}, API ID: {api_league_id})")
                return league_id
                
        except Exception as e:
            logger.error(f"Failed to add league {name}: {e}")
            raise
    
    def update_league(self, league_id: int, **kwargs) -> bool:
        """Update league configuration."""
        try:
            if not kwargs:
                return False
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = ['name', 'country', 'country_code', 'api_league_id', 
                            'season_structure', 'season_start_month', 'season_end_month',
                            'active', 'priority_order']
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                logger.warning("No valid fields provided for league update")
                return False
            
            values.append(league_id)
            
            with self.db_manager.get_connection() as conn:
                sql = f"""
                    UPDATE leagues 
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                cursor = conn.execute(sql, values)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    # Refresh cache
                    self._refresh_cache()
                    logger.info(f"Updated league {league_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to update league {league_id}: {e}")
            return False
    
    def is_league_season_active(self, league_id: int) -> bool:
        """Check if a league's season is currently active."""
        try:
            league = self.get_league_by_id(league_id)
            if not league or not league.active:
                return False
            
            now = datetime.now()
            current_month = now.month
            
            if league.season_structure == 'calendar_year':
                # Calendar year leagues are generally active year-round
                return True
                
            elif league.season_structure == 'academic_year':
                # Check if current month falls within season range
                start_month = league.season_start_month
                end_month = league.season_end_month
                
                if start_month <= end_month:
                    # Season within same calendar year (rare)
                    return start_month <= current_month <= end_month
                else:
                    # Season crosses calendar year (common: Aug-May)
                    return current_month >= start_month or current_month <= end_month
            
            # Default to active for unknown structures
            return True
            
        except Exception as e:
            logger.error(f"Failed to check season activity for league {league_id}: {e}")
            return False
    
    def get_league_stats(self) -> Dict[str, any]:
        """Get statistics about leagues in the system."""
        try:
            self._ensure_cache_fresh()
            
            total_leagues = len(self._league_cache)
            active_leagues = len([l for l in self._league_cache.values() if l.active])
            countries = len(set(l.country_code for l in self._league_cache.values()))
            
            season_structures = {}
            for league in self._league_cache.values():
                structure = league.season_structure
                season_structures[structure] = season_structures.get(structure, 0) + 1
            
            return {
                'total_leagues': total_leagues,
                'active_leagues': active_leagues,
                'countries': countries,
                'season_structures': season_structures,
                'cache_last_updated': self._last_cache_update.isoformat() if self._last_cache_update else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get league stats: {e}")
            return {}

# Global league manager instance
_league_manager = None

def get_league_manager() -> LeagueManager:
    """Get singleton league manager instance."""
    global _league_manager
    if _league_manager is None:
        _league_manager = LeagueManager()
    return _league_manager

# Convenience functions
def get_current_season(league_id: int) -> int:
    """Get current season for a league."""
    return get_league_manager().get_current_season(league_id)

def get_league_by_api_id(api_league_id: int) -> Optional[LeagueConfig]:
    """Get league config by API-Football ID."""
    return get_league_manager().get_league_by_api_id(api_league_id)

def get_active_leagues() -> List[LeagueConfig]:
    """Get all active leagues."""
    return get_league_manager().get_active_leagues()

def get_countries_with_leagues() -> Dict[str, Dict[str, any]]:
    """Get all countries with their leagues."""
    return get_league_manager().get_countries_with_leagues()
