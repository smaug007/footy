"""
API-Football client for China Super League corner prediction system.
Handles rate limiting, caching, error handling, and retry logic.
"""
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, calls_per_minute: int = 300, calls_per_day: int = 7500):
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day
        self.minute_calls = []
        self.daily_calls = 0
        self.last_reset = datetime.now().date()
        
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding limits."""
        now = datetime.now()
        current_date = now.date()
        
        # Reset daily counter if new day
        if current_date > self.last_reset:
            self.daily_calls = 0
            self.last_reset = current_date
            logger.info(f"Daily API call counter reset. Date: {current_date}")
        
        # Clean up minute calls older than 1 minute
        one_minute_ago = now - timedelta(minutes=1)
        self.minute_calls = [call_time for call_time in self.minute_calls if call_time > one_minute_ago]
        
        # Check limits
        if self.daily_calls >= self.calls_per_day:
            logger.warning(f"Daily API limit reached: {self.daily_calls}/{self.calls_per_day}")
            return False
            
        if len(self.minute_calls) >= self.calls_per_minute:
            logger.warning(f"Per-minute API limit reached: {len(self.minute_calls)}/{self.calls_per_minute}")
            return False
            
        return True
    
    def record_request(self):
        """Record that a request was made."""
        now = datetime.now()
        self.minute_calls.append(now)
        self.daily_calls += 1
        logger.debug(f"API call recorded. Daily: {self.daily_calls}/{self.calls_per_day}, "
                    f"Minute: {len(self.minute_calls)}/{self.calls_per_minute}")
    
    def wait_time(self) -> float:
        """Calculate how long to wait before next request."""
        if not self.minute_calls:
            return 0
        
        oldest_call = min(self.minute_calls)
        wait_until = oldest_call + timedelta(minutes=1)
        wait_seconds = (wait_until - datetime.now()).total_seconds()
        
        return max(0, wait_seconds)

class APICache:
    """Simple in-memory cache for API responses."""
    
    def __init__(self, timeout_hours: int = 6):
        self.cache = {}
        self.timeout_hours = timeout_hours
        
    def _is_expired(self, timestamp: datetime) -> bool:
        """Check if cached data is expired."""
        return datetime.now() - timestamp > timedelta(hours=self.timeout_hours)
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if not expired."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                logger.debug(f"Cache hit for key: {key}")
                return data
            else:
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key}")
        return None
    
    def set(self, key: str, data: Dict):
        """Store data in cache."""
        self.cache[key] = (data, datetime.now())
        logger.debug(f"Data cached for key: {key}")
    
    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")

class APIFootballClient:
    """API-Football client with rate limiting, caching, and error handling."""
    
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.api_key = Config.API_FOOTBALL_KEY
        self.rate_limiter = RateLimiter(Config.API_CALLS_PER_MINUTE, Config.API_CALLS_PER_DAY)
        self.cache = APICache(Config.CACHE_TIMEOUT_HOURS)
        
        # Request headers
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': Config.API_FOOTBALL_HOST,
            'User-Agent': 'CSL-Corner-Predictor/1.0'
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("API-Football client initialized")
    
    def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True) -> Dict:
        """Make API request with rate limiting, caching, and error handling."""
        # Generate cache key
        cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        
        # Check cache first
        if use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Check rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time + 1)  # Add 1 second buffer
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making API request: {endpoint} (attempt {attempt + 1})")
                
                response = self.session.get(url, params=params, timeout=30)
                self.rate_limiter.record_request()
                
                # Handle different response codes
                if response.status_code == 200:
                    data = response.json()
                    
                    # Cache successful response
                    if use_cache:
                        self.cache.set(cache_key, data)
                    
                    logger.debug(f"API request successful: {endpoint}")
                    return data
                    
                elif response.status_code == 429:  # Too Many Requests
                    logger.warning(f"Rate limit hit (429). Waiting {retry_delay * 2} seconds...")
                    time.sleep(retry_delay * 2)
                    retry_delay *= 2
                    continue
                    
                elif response.status_code == 403:  # Forbidden
                    logger.error("API key invalid or expired (403)")
                    raise APIException(f"Invalid API key: {response.status_code}")
                    
                elif response.status_code == 404:  # Not Found
                    logger.warning(f"Endpoint not found (404): {endpoint}")
                    return {'response': []}  # Return empty response for not found
                    
                else:
                    logger.warning(f"API request failed with status {response.status_code}: {response.text}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise APIException("Request timeout after all retries")
                time.sleep(retry_delay)
                retry_delay *= 2
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise APIException("Connection error after all retries")
                time.sleep(retry_delay)
                retry_delay *= 2
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    raise APIException(f"Request failed after all retries: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2
        
        raise APIException("Max retries exceeded")
    
    def get_leagues(self, country: str = "China", season: int = None) -> Dict:
        """Get leagues information."""
        params = {'country': country}
        if season:
            params['season'] = season
            
        return self._make_request('/leagues', params)
    
    def get_fixtures(self, league_id: int, season: int, status: str = None) -> Dict:
        """Get fixtures for a league and season."""
        params = {
            'league': league_id,
            'season': season
        }
        if status:
            params['status'] = status
            
        return self._make_request('/fixtures', params)
    
    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """Get statistics for a specific fixture."""
        params = {'fixture': fixture_id}
        return self._make_request('/fixtures/statistics', params)
    
    def get_fixture_details(self, fixture_id: int) -> Dict:
        """Get detailed fixture information including goals and match data."""
        params = {'id': fixture_id}
        response = self._make_request('/fixtures', params)
        
        if response and 'response' in response and response['response']:
            fixture_data = response['response'][0]
            return self._process_fixture_details(fixture_data)
        return None
    
    def _process_fixture_details(self, fixture_data: Dict) -> Dict:
        """Process raw fixture data to extract structured information."""
        try:
            # Extract basic fixture information
            fixture_info = fixture_data.get('fixture', {})
            teams_info = fixture_data.get('teams', {})
            
            # Extract goal data
            goals_data = fixture_data.get('goals', {})
            score_data = fixture_data.get('score', {})
            
            # Extract fulltime, halftime, and other scores
            fulltime = score_data.get('fulltime', {}) if score_data else {}
            halftime = score_data.get('halftime', {}) if score_data else {}
            extratime = score_data.get('extratime', {}) if score_data else {}
            penalty = score_data.get('penalty', {}) if score_data else {}
            
            # Build structured response
            processed_data = {
                'fixture_id': fixture_info.get('id'),
                'date': fixture_info.get('date'),
                'venue': fixture_info.get('venue', {}).get('name'),
                'status': fixture_info.get('status', {}),
                'referee': fixture_info.get('referee'),
                
                # Team information
                'home_team': {
                    'id': teams_info.get('home', {}).get('id'),
                    'name': teams_info.get('home', {}).get('name'),
                    'logo': teams_info.get('home', {}).get('logo')
                },
                'away_team': {
                    'id': teams_info.get('away', {}).get('id'),
                    'name': teams_info.get('away', {}).get('name'),
                    'logo': teams_info.get('away', {}).get('logo')
                },
                
                # Goal data - primary source
                'goals': {
                    'home': goals_data.get('home'),
                    'away': goals_data.get('away')
                },
                
                # Detailed score breakdown
                'score': {
                    'fulltime': {
                        'home': fulltime.get('home'),
                        'away': fulltime.get('away')
                    },
                    'halftime': {
                        'home': halftime.get('home'),
                        'away': halftime.get('away')
                    },
                    'extratime': {
                        'home': extratime.get('home'),
                        'away': extratime.get('away')
                    },
                    'penalty': {
                        'home': penalty.get('home'),
                        'away': penalty.get('away')
                    }
                },
                
                # Convenience fields for easy access
                'home_goals': goals_data.get('home'),
                'away_goals': goals_data.get('away'),
                'total_goals': (goals_data.get('home') or 0) + (goals_data.get('away') or 0) if goals_data.get('home') is not None and goals_data.get('away') is not None else None,
                
                # Keep original data for compatibility
                'raw_data': fixture_data
            }
            
            logger.debug(f"Processed fixture {fixture_info.get('id')}: {processed_data['home_team']['name']} {processed_data['home_goals']}-{processed_data['away_goals']} {processed_data['away_team']['name']}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing fixture details: {e}")
            # Return original data as fallback
            return fixture_data
    
    def get_fixture_corner_statistics(self, fixture_id: int) -> Dict:
        """Get corner statistics specifically for a fixture."""
        try:
            # Get full fixture statistics
            stats_response = self.get_fixture_statistics(fixture_id)
            
            if not stats_response or 'response' not in stats_response:
                return None
            
            # Extract corner data from statistics
            corner_data = {
                'fixture_id': fixture_id,
                'home_corners': None,
                'away_corners': None,
                'total_corners': None
            }
            
            # Parse statistics response
            response_data = stats_response.get('response', [])
            
            for team_stats in response_data:
                statistics = team_stats.get('statistics', [])
                team_type = 'home' if team_stats.get('team', {}).get('id') else 'away'
                
                # Find corners statistic (API uses 'Corner Kicks')
                for stat in statistics:
                    if stat.get('type') == 'Corner Kicks':
                        corner_value = stat.get('value')
                        
                        # Convert to integer if possible
                        try:
                            corner_value = int(corner_value) if corner_value is not None and corner_value != 'None' else 0
                        except (ValueError, TypeError):
                            corner_value = 0
                        
                        # Determine if this is home or away team
                        # API-Football returns two objects in response array: [home_team_stats, away_team_stats]
                        if len(response_data) == 2:
                            if response_data.index(team_stats) == 0:
                                corner_data['home_corners'] = corner_value
                            else:
                                corner_data['away_corners'] = corner_value
                        
                        break
            
            # Calculate total corners
            if corner_data['home_corners'] is not None and corner_data['away_corners'] is not None:
                corner_data['total_corners'] = corner_data['home_corners'] + corner_data['away_corners']
            
            return corner_data
            
        except Exception as e:
            logger.error(f"Error getting corner statistics for fixture {fixture_id}: {e}")
            return None
    
    def get_fixture_cards_statistics(self, fixture_id: int) -> Dict:
        """Get cards statistics specifically for a fixture."""
        try:
            # Get full fixture statistics
            stats_response = self.get_fixture_statistics(fixture_id)
            
            if not stats_response or 'response' not in stats_response:
                return None
            
            # Extract cards data from statistics
            cards_data = {
                'fixture_id': fixture_id,
                'home_yellow_cards': 0,
                'home_red_cards': 0,
                'away_yellow_cards': 0,
                'away_red_cards': 0,
                'total_cards': 0
            }
            
            # Parse statistics response
            response_data = stats_response.get('response', [])
            
            # API-Football returns two objects in response array: [home_team_stats, away_team_stats]
            if len(response_data) == 2:
                # Process home team (index 0)
                home_stats = response_data[0].get('statistics', [])
                for stat in home_stats:
                    if stat.get('type') == 'Yellow Cards':
                        try:
                            cards_data['home_yellow_cards'] = int(stat.get('value', 0) or 0)
                        except (ValueError, TypeError):
                            cards_data['home_yellow_cards'] = 0
                    elif stat.get('type') == 'Red Cards':
                        try:
                            cards_data['home_red_cards'] = int(stat.get('value', 0) or 0)
                        except (ValueError, TypeError):
                            cards_data['home_red_cards'] = 0
                
                # Process away team (index 1)
                away_stats = response_data[1].get('statistics', [])
                for stat in away_stats:
                    if stat.get('type') == 'Yellow Cards':
                        try:
                            cards_data['away_yellow_cards'] = int(stat.get('value', 0) or 0)
                        except (ValueError, TypeError):
                            cards_data['away_yellow_cards'] = 0
                    elif stat.get('type') == 'Red Cards':
                        try:
                            cards_data['away_red_cards'] = int(stat.get('value', 0) or 0)
                        except (ValueError, TypeError):
                            cards_data['away_red_cards'] = 0
            
            # Calculate total cards (yellow + red for both teams)
            cards_data['total_cards'] = (
                cards_data['home_yellow_cards'] + 
                cards_data['home_red_cards'] +
                cards_data['away_yellow_cards'] + 
                cards_data['away_red_cards']
            )
            
            return cards_data
            
        except Exception as e:
            logger.error(f"Error getting cards statistics for fixture {fixture_id}: {e}")
            return None
    
    def get_teams(self, league_id: int, season: int) -> Dict:
        """Get teams for a league and season."""
        params = {
            'league': league_id,
            'season': season
        }
        return self._make_request('/teams', params)
    
    def get_standings(self, league_id: int, season: int) -> Dict:
        """Get league standings/table for a league and season."""
        params = {
            'league': league_id,
            'season': season
        }
        return self._make_request('/standings', params)
    
    def get_league_fixtures(self, league_id: int, season: int = None, status: str = None) -> Dict:
        """Get fixtures for any league."""
        if season is None:
            season = datetime.now().year
            
        return self.get_fixtures(league_id, season, status)
    
    def get_league_teams(self, league_id: int, season: int = None) -> Dict:
        """Get teams for any league."""
        if season is None:
            season = datetime.now().year
            
        return self.get_teams(league_id, season)
    
    def get_league_standings(self, league_id: int, season: int = None) -> Dict:
        """Get standings/table for any league."""
        if season is None:
            season = datetime.now().year
            
        return self.get_standings(league_id, season)
    
    def get_upcoming_fixtures_by_league(self, league_id: int, days_ahead: int = 7) -> Dict:
        """Get upcoming fixtures for any league within specified days."""
        # Get ALL fixtures for current season from API (real-time data)
        # Then filter for upcoming statuses on backend to catch all variations
        current_season = datetime.now().year
        all_fixtures_response = self.get_league_fixtures(league_id, current_season)
        
        if 'response' not in all_fixtures_response:
            return all_fixtures_response
        
        all_fixtures = all_fixtures_response['response']
        
        # Filter for upcoming fixture statuses (real-time API data)
        upcoming_statuses = {'NS', 'Not Started', 'PST', 'TBD', 'SUSP', 'INT'}
        upcoming_fixtures = []
        
        for fixture in all_fixtures:
            fixture_status = fixture.get('fixture', {}).get('status', {}).get('short', '')
            if fixture_status in upcoming_statuses:
                upcoming_fixtures.append(fixture)
        
        # Return filtered results in same format as original API response
        return {
            'response': upcoming_fixtures,
            'results': len(upcoming_fixtures)
        }
    
    def get_completed_fixtures_by_league(self, league_id: int, season: int = None) -> Dict:
        """Get completed fixtures for any league."""
        return self.get_league_fixtures(league_id, season, status='FT')  # Full Time
    
    def get_upcoming_fixtures(self, league_id: int = None, days_ahead: int = 7) -> Dict:
        """Get upcoming fixtures (generic method for backward compatibility)."""
        if league_id is None:
            # Default to CSL for backward compatibility
            league_id = Config.CHINA_SUPER_LEAGUE_ID
        return self.get_upcoming_fixtures_by_league(league_id, days_ahead)
    
    def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            # Use a simple endpoint to check API health
            response = self.get_leagues()
            return response.get('response') is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status."""
        return {
            'daily_calls': self.rate_limiter.daily_calls,
            'daily_limit': self.rate_limiter.calls_per_day,
            'daily_remaining': self.rate_limiter.calls_per_day - self.rate_limiter.daily_calls,
            'minute_calls': len(self.rate_limiter.minute_calls),
            'minute_limit': self.rate_limiter.calls_per_minute,
            'minute_remaining': self.rate_limiter.calls_per_minute - len(self.rate_limiter.minute_calls),
            'cache_entries': len(self.cache.cache)
        }

class APIException(Exception):
    """Custom exception for API-related errors."""
    pass

# Global client instance
_client = None

def get_api_client() -> APIFootballClient:
    """Get singleton API client instance."""
    global _client
    if _client is None:
        _client = APIFootballClient()
    return _client
