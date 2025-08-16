"""
Configuration settings for China Super League corner prediction system.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # API-Football settings
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
    API_FOOTBALL_HOST = 'v3.football.api-sports.io'
    API_BASE_URL = f'https://{API_FOOTBALL_HOST}'
    
    # Rate limiting settings (from API-Football limits)
    API_CALLS_PER_DAY = 7500
    API_CALLS_PER_MINUTE = 300
    
    # China Super League ID (from API-Football)
    CHINA_SUPER_LEAGUE_ID = 169
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'corners_prediction.db')
    
    # Prediction settings
    MIN_GAMES_FOR_PREDICTION = 3
    MAX_GAMES_FOR_ANALYSIS = 20
    TARGET_ACCURACY = 0.90
    CORNER_TOLERANCE = 1  # ±1 corner considered correct
    
    # Cache settings
    CACHE_TIMEOUT_HOURS = 6
    
    @staticmethod
    def validate_config():
        """Validate that required configuration is present."""
        if not Config.API_FOOTBALL_KEY:
            raise ValueError("API_FOOTBALL_KEY environment variable is required")
        return True
