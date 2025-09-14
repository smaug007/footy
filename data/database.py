"""
Database operations for China Super League corner prediction system.
Handles SQLite database creation, CRUD operations, and data management.
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager with comprehensive schema and operations."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_database_exists()
        logger.info(f"Database manager initialized: {self.db_path}")
    
    def _ensure_database_exists(self):
        """Ensure database file exists and create tables if needed."""
        try:
            with self.get_connection() as conn:
                self._create_tables(conn)
                logger.info("Database tables verified/created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all database tables with proper schema."""
        
        # Leagues table (MULTI-LEAGUE SUPPORT)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                country_code TEXT NOT NULL,
                api_league_id INTEGER UNIQUE NOT NULL,
                season_structure TEXT NOT NULL CHECK (season_structure IN ('calendar_year', 'academic_year', 'custom')),
                season_start_month INTEGER DEFAULT 1,
                season_end_month INTEGER DEFAULT 12,
                active BOOLEAN DEFAULT TRUE,
                priority_order INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Teams table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_team_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                code TEXT,
                country TEXT DEFAULT 'China',
                logo_url TEXT,
                founded INTEGER,
                venue_name TEXT,
                venue_capacity INTEGER,
                venue_city TEXT,
                season INTEGER NOT NULL,
                league_id INTEGER REFERENCES leagues(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Matches table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_fixture_id INTEGER UNIQUE NOT NULL,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                match_date TIMESTAMP NOT NULL,
                venue_name TEXT,
                corners_home INTEGER,
                corners_away INTEGER,
                total_corners INTEGER GENERATED ALWAYS AS (corners_home + corners_away) STORED,
                goals_home INTEGER,
                goals_away INTEGER,
                season INTEGER NOT NULL,
                status TEXT NOT NULL,
                referee TEXT,
                attendance INTEGER,
                league_id INTEGER REFERENCES leagues(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (home_team_id) REFERENCES teams (id),
                FOREIGN KEY (away_team_id) REFERENCES teams (id),
                FOREIGN KEY (league_id) REFERENCES leagues (id)
            )
        """)
        
        # Add goal columns to existing matches table if they don't exist
        try:
            conn.execute("ALTER TABLE matches ADD COLUMN goals_home INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute("ALTER TABLE matches ADD COLUMN goals_away INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add unique constraint on predictions.match_id to prevent duplicates
        try:
            # First check if the constraint already exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_predictions_match_unique'
            """)
            if not cursor.fetchone():
                conn.execute("""
                    CREATE UNIQUE INDEX idx_predictions_match_unique 
                    ON predictions (match_id)
                """)
                logger.info("Added unique constraint to prevent duplicate predictions per match")
        except sqlite3.OperationalError as e:
            # Constraint might already exist or there might be existing duplicates
            logger.warning(f"Could not add unique constraint: {e}")
            logger.info("This is expected if duplicate predictions already exist")
        
        # Predictions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                predicted_total_corners REAL NOT NULL,
                confidence_5_5 REAL NOT NULL,
                confidence_6_5 REAL NOT NULL,
                home_team_expected REAL NOT NULL,
                away_team_expected REAL NOT NULL,
                home_team_consistency REAL,
                away_team_consistency REAL,
                home_team_score_probability REAL,
                away_team_score_probability REAL,
                analysis_report TEXT,
                season INTEGER NOT NULL,
                league_id INTEGER REFERENCES leagues(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id),
                FOREIGN KEY (league_id) REFERENCES leagues (id)
            )
        """)
        
        # Add goal scoring probability columns if they don't exist
        try:
            conn.execute("ALTER TABLE predictions ADD COLUMN home_team_score_probability REAL")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute("ALTER TABLE predictions ADD COLUMN away_team_score_probability REAL")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add league_id columns to existing tables (MULTI-LEAGUE SUPPORT)
        try:
            conn.execute("ALTER TABLE teams ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE matches ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE predictions ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE prediction_results ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE team_accuracy_stats ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE team_accuracy_history ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE date_based_backtests ADD COLUMN league_id INTEGER REFERENCES leagues(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Insert initial league data (MULTI-LEAGUE SUPPORT)
        try:
            # Insert CSL (existing) with fixed ID
            conn.execute("""
                INSERT OR IGNORE INTO leagues (id, name, country, country_code, api_league_id, season_structure, priority_order) 
                VALUES (1, 'Chinese Super League', 'China', 'CN', 169, 'calendar_year', 1)
            """)

            # Insert Phase 1 leagues
            conn.execute("""
                INSERT OR IGNORE INTO leagues (name, country, country_code, api_league_id, season_structure, priority_order) VALUES
                ('La Liga', 'Spain', 'ES', 140, 'academic_year', 2),
                ('Segunda División', 'Spain', 'ES', 141, 'academic_year', 3),
                ('Serie A', 'Italy', 'IT', 135, 'academic_year', 4),
                ('Serie B', 'Italy', 'IT', 136, 'academic_year', 5),
                ('Ligue 1', 'France', 'FR', 61, 'academic_year', 6)
            """)

            # Update existing CSL data with league_id = 1
            conn.execute("UPDATE teams SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE matches SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE predictions SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE prediction_results SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE team_accuracy_stats SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE team_accuracy_history SET league_id = 1 WHERE league_id IS NULL")
            conn.execute("UPDATE date_based_backtests SET league_id = 1 WHERE league_id IS NULL")

            logger.info("Initial league data inserted and existing CSL data updated with league_id = 1")
        except Exception as e:
            logger.warning(f"League data initialization issue (likely already exists): {e}")
        
        # Prediction Results table (Accuracy Tracking)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER UNIQUE NOT NULL,
                actual_home_corners INTEGER NOT NULL,
                actual_away_corners INTEGER NOT NULL,
                actual_total_corners INTEGER GENERATED ALWAYS AS (actual_home_corners + actual_away_corners) STORED,
                home_prediction_correct BOOLEAN,
                away_prediction_correct BOOLEAN,
                total_prediction_margin REAL,
                over_5_5_correct BOOLEAN,
                over_6_5_correct BOOLEAN,
                verified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_manually BOOLEAN DEFAULT FALSE,
                notes TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions (id)
            )
        """)
        
        # Team Accuracy Stats table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_accuracy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                season INTEGER NOT NULL,
                prediction_type TEXT NOT NULL CHECK (prediction_type IN ('corners_won', 'corners_conceded', 'over_5_5', 'over_6_5')),
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_percentage REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams (id),
                UNIQUE(team_id, season, prediction_type)
            )
        """)
        
        # Team Accuracy History table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_accuracy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                prediction_id INTEGER NOT NULL,
                season INTEGER NOT NULL,
                prediction_type TEXT NOT NULL,
                was_correct BOOLEAN NOT NULL,
                margin_of_error REAL,
                confidence_level REAL,
                match_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams (id),
                FOREIGN KEY (prediction_id) REFERENCES predictions (id)
            )
        """)

        # Date-Based Backtesting table (clean and simple)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS date_based_backtests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_fixture_id INTEGER NOT NULL,
                prediction_date DATE NOT NULL,
                match_date DATE NOT NULL,
                home_team_id INTEGER,
                away_team_id INTEGER,
                home_team_name TEXT NOT NULL,
                away_team_name TEXT NOT NULL,
                predicted_total_corners REAL NOT NULL,
                confidence_5_5 REAL NOT NULL,
                confidence_6_5 REAL NOT NULL,
                predicted_home_corners REAL NOT NULL,
                predicted_away_corners REAL NOT NULL,
                home_score_probability REAL,
                away_score_probability REAL,
                home_2plus_probability REAL,
                away_2plus_probability REAL,
                actual_total_corners INTEGER,
                over_5_5_correct BOOLEAN,
                over_6_5_correct BOOLEAN,
                prediction_accuracy REAL,
                analysis_report TEXT,
                run_id TEXT NOT NULL,
                season INTEGER NOT NULL DEFAULT 2025,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        
        # Create indexes for better performance (UPDATED FOR MULTI-LEAGUE SUPPORT)
        indexes = [
            # Leagues indexes
            "CREATE INDEX IF NOT EXISTS idx_leagues_api_id ON leagues (api_league_id)",
            "CREATE INDEX IF NOT EXISTS idx_leagues_country ON leagues (country_code)",
            "CREATE INDEX IF NOT EXISTS idx_leagues_active ON leagues (active, priority_order)",
            
            # Teams indexes (updated for multi-league)
            "CREATE INDEX IF NOT EXISTS idx_teams_api_id ON teams (api_team_id)",
            "CREATE INDEX IF NOT EXISTS idx_teams_season ON teams (season)",
            "CREATE INDEX IF NOT EXISTS idx_teams_league_season ON teams (league_id, season)",
            "CREATE INDEX IF NOT EXISTS idx_teams_league_api ON teams (league_id, api_team_id)",
            
            # Matches indexes (updated for multi-league)
            "CREATE INDEX IF NOT EXISTS idx_matches_api_id ON matches (api_fixture_id)",
            "CREATE INDEX IF NOT EXISTS idx_matches_date ON matches (match_date)",
            "CREATE INDEX IF NOT EXISTS idx_matches_season ON matches (season)",
            "CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches (home_team_id, away_team_id)",
            "CREATE INDEX IF NOT EXISTS idx_matches_league_season ON matches (league_id, season)",
            "CREATE INDEX IF NOT EXISTS idx_matches_league_date ON matches (league_id, match_date)",
            
            # Predictions indexes (updated for multi-league)
            "CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions (match_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_season ON predictions (season)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_league_season ON predictions (league_id, season)",
            
            # Accuracy indexes (updated for multi-league)
            "CREATE INDEX IF NOT EXISTS idx_accuracy_stats_team ON team_accuracy_stats (team_id, season)",
            "CREATE INDEX IF NOT EXISTS idx_accuracy_stats_league ON team_accuracy_stats (league_id, team_id, season)",
            "CREATE INDEX IF NOT EXISTS idx_accuracy_history_team ON team_accuracy_history (team_id, season)",
            "CREATE INDEX IF NOT EXISTS idx_accuracy_history_league ON team_accuracy_history (league_id, team_id, season)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        logger.debug("Database schema created/updated successfully")
    
    # TEAMS OPERATIONS
    def insert_team(self, team_data: Dict) -> int:
        """Insert a new team or update existing one."""
        with self.get_connection() as conn:
            # First, check if team already exists for this league and season
            cursor = conn.execute("""
                SELECT id FROM teams WHERE api_team_id = ? AND league_id = ? AND season = ?
            """, (team_data['api_team_id'], team_data['league_id'], team_data['season']))
            
            existing_team = cursor.fetchone()
            
            if existing_team:
                # Update existing team
                cursor = conn.execute("""
                    UPDATE teams SET 
                        name = ?, code = ?, country = ?, logo_url = ?, founded = ?,
                        venue_name = ?, venue_capacity = ?, venue_city = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE api_team_id = ? AND league_id = ? AND season = ?
                """, (
                    team_data['name'],
                    team_data.get('code'),
                    team_data.get('country', 'China'),
                    team_data.get('logo_url'),
                    team_data.get('founded'),
                    team_data.get('venue_name'),
                    team_data.get('venue_capacity'),
                    team_data.get('venue_city'),
                    team_data['api_team_id'],
                    team_data['league_id'],
                    team_data['season']
                ))
                conn.commit()
                return existing_team[0]
            else:
                # Insert new team
                cursor = conn.execute("""
                    INSERT INTO teams (
                        api_team_id, name, code, country, logo_url, founded,
                        venue_name, venue_capacity, venue_city, season, league_id, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    team_data['api_team_id'],
                    team_data['name'],
                    team_data.get('code'),
                    team_data.get('country', 'China'),
                    team_data.get('logo_url'),
                    team_data.get('founded'),
                    team_data.get('venue_name'),
                    team_data.get('venue_capacity'),
                    team_data.get('venue_city'),
                    team_data['season'],
                    team_data['league_id']
                ))
                conn.commit()
                return cursor.lastrowid
    
    def get_team_by_id(self, team_id: int) -> Optional[Dict]:
        """Get team by database ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM teams WHERE id = ?",
                (team_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_team_by_api_id(self, api_team_id: int, season: int = None) -> Optional[Dict]:
        """Get team by API ID."""
        with self.get_connection() as conn:
            if season:
                cursor = conn.execute(
                    "SELECT * FROM teams WHERE api_team_id = ? AND season = ?",
                    (api_team_id, season)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM teams WHERE api_team_id = ? ORDER BY season DESC LIMIT 1",
                    (api_team_id,)
                )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_teams_by_season(self, league_id: int, season: int) -> List[Dict]:
        """Get all teams for a specific league and season."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM teams WHERE league_id = ? AND season = ? ORDER BY name",
                (league_id, season)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # MATCHES OPERATIONS
    def insert_match(self, match_data: Dict) -> int:
        """Insert a new match or update existing one."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO matches (
                    api_fixture_id, home_team_id, away_team_id, match_date,
                    venue_name, corners_home, corners_away, season, status,
                    referee, attendance, league_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                match_data['api_fixture_id'],
                match_data['home_team_id'],
                match_data['away_team_id'],
                match_data['match_date'],
                match_data.get('venue_name'),
                match_data.get('corners_home'),
                match_data.get('corners_away'),
                match_data['season'],
                match_data['status'],
                match_data.get('referee'),
                match_data.get('attendance'),
                match_data['league_id']
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_match_by_api_id(self, api_fixture_id: int) -> Optional[Dict]:
        """Get match by API fixture ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.api_fixture_id = ?
            """, (api_fixture_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_team_matches(self, team_id: int, league_id: int, season: int, limit: int = None) -> List[Dict]:
        """Get matches for a team in a specific league and season."""
        with self.get_connection() as conn:
            sql = """
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.league_id = ? AND m.season = ? AND m.status = 'FT'
                ORDER BY m.match_date DESC
            """
            params = [team_id, team_id, league_id, season]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_team_matches_before_date(self, team_id: int, league_id: int, season: int, cutoff_date, limit: int = None) -> List[Dict]:
        """Get matches for a team in a specific league and season BEFORE a specific cutoff date (for time-travel predictions)."""
        from datetime import date
        
        # Convert cutoff_date to date object if it's a string
        if isinstance(cutoff_date, str):
            from datetime import datetime
            cutoff_date = datetime.strptime(cutoff_date, '%Y-%m-%d').date()
        
        with self.get_connection() as conn:
            sql = """
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.league_id = ? AND m.season = ? AND m.status = 'FT'
                AND date(m.match_date) < ?
                ORDER BY m.match_date DESC
            """
            params = [team_id, team_id, league_id, season, cutoff_date]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(sql, params)
            matches = [dict(row) for row in cursor.fetchall()]
            
            logger.debug(f"Retrieved {len(matches)} matches for team {team_id} in league {league_id} before {cutoff_date}")
            return matches
    
    def get_completed_matches(self, league_id: int, season: int, limit: int = None) -> List[Dict]:
        """Get completed matches for a specific league and season (with corner data)."""
        with self.get_connection() as conn:
            sql = """
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.league_id = ? AND m.season = ? AND m.status = 'FT' AND m.corners_home IS NOT NULL
                ORDER BY m.match_date DESC
            """
            params = [league_id, season]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_matches_needing_corner_stats(self, league_id: int, season: int, limit: int = None) -> List[Dict]:
        """Get completed matches that need corner statistics imported for a specific league."""
        with self.get_connection() as conn:
            sql = """
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.league_id = ? AND m.season = ? AND m.status = 'FT' AND m.corners_home IS NULL
                ORDER BY m.match_date DESC
            """
            params = [league_id, season]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_match_corners(self, match_id: int, home_corners: int, away_corners: int) -> bool:
        """Update match with corner statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE matches 
                    SET corners_home = ?, corners_away = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (home_corners, away_corners, match_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update match {match_id} corners: {e}")
            return False
    
    def update_match_goals(self, match_id: int, home_goals: int, away_goals: int) -> bool:
        """Update match with goal statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE matches 
                    SET goals_home = ?, goals_away = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (home_goals, away_goals, match_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update match {match_id} goals: {e}")
            return False
    
    def get_matches_needing_goal_stats(self, season: int, limit: int = 100) -> List[Tuple]:
        """Get matches that need goal statistics imported."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.api_fixture_id, m.id, ht.name as home_team, at.name as away_team, m.match_date
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id  
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.season = ? AND m.goals_home IS NULL AND m.status = 'FT'
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (season, limit))
            return cursor.fetchall()
    
    # PREDICTIONS OPERATIONS
    def insert_prediction(self, prediction_data: Dict) -> int:
        """Insert a new prediction or replace existing one for the same match."""
        with self.get_connection() as conn:
            # First check if a prediction already exists for this match
            cursor = conn.execute("""
                SELECT id FROM predictions WHERE match_id = ?
            """, (prediction_data['match_id'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing prediction
                cursor = conn.execute("""
                    UPDATE predictions SET
                        predicted_total_corners = ?,
                        confidence_5_5 = ?,
                        confidence_6_5 = ?,
                        home_team_expected = ?,
                        away_team_expected = ?,
                        home_team_consistency = ?,
                        away_team_consistency = ?,
                        home_team_score_probability = ?,
                        away_team_score_probability = ?,
                        analysis_report = ?,
                        season = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE match_id = ?
                """, (
                    prediction_data['predicted_total_corners'],
                    prediction_data['confidence_5_5'],
                    prediction_data['confidence_6_5'],
                    prediction_data['home_team_expected'],
                    prediction_data['away_team_expected'],
                    prediction_data.get('home_team_consistency'),
                    prediction_data.get('away_team_consistency'),
                    prediction_data.get('home_team_score_probability'),
                    prediction_data.get('away_team_score_probability'),
                    prediction_data.get('analysis_report'),
                    prediction_data['season'],
                    prediction_data['match_id']
                ))
                conn.commit()
                logger.info(f"Updated existing prediction for match {prediction_data['match_id']}")
                return existing[0]
            else:
                # Insert new prediction
                cursor = conn.execute("""
                    INSERT INTO predictions (
                        match_id, predicted_total_corners, confidence_5_5, confidence_6_5,
                        home_team_expected, away_team_expected, home_team_consistency,
                        away_team_consistency, home_team_score_probability, away_team_score_probability,
                        analysis_report, season
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_data['match_id'],
                    prediction_data['predicted_total_corners'],
                    prediction_data['confidence_5_5'],
                    prediction_data['confidence_6_5'],
                    prediction_data['home_team_expected'],
                    prediction_data['away_team_expected'],
                    prediction_data.get('home_team_consistency'),
                    prediction_data.get('away_team_consistency'),
                    prediction_data.get('home_team_score_probability'),
                    prediction_data.get('away_team_score_probability'),
                    prediction_data.get('analysis_report'),
                    prediction_data['season']
                ))
                conn.commit()
                logger.info(f"Inserted new prediction for match {prediction_data['match_id']}")
                return cursor.lastrowid
    
    def get_predictions_by_season(self, league_id: int, season: int) -> List[Dict]:
        """Get all predictions for a specific league and season."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, m.api_fixture_id, ht.name as home_team_name, at.name as away_team_name
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE p.league_id = ? AND p.season = ?
                ORDER BY p.created_at DESC
            """, (league_id, season))
            return [dict(row) for row in cursor.fetchall()]
    
    # ACCURACY TRACKING OPERATIONS
    def insert_prediction_result(self, result_data: Dict) -> int:
        """Insert prediction result for accuracy tracking."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO prediction_results (
                    prediction_id, actual_home_corners, actual_away_corners,
                    home_prediction_correct, away_prediction_correct,
                    total_prediction_margin, over_5_5_correct, over_6_5_correct,
                    verified_manually, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_data['prediction_id'],
                result_data['actual_home_corners'],
                result_data['actual_away_corners'],
                result_data.get('home_prediction_correct'),
                result_data.get('away_prediction_correct'),
                result_data.get('total_prediction_margin'),
                result_data.get('over_5_5_correct'),
                result_data.get('over_6_5_correct'),
                result_data.get('verified_manually', False),
                result_data.get('notes')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_team_accuracy_stats(self, team_id: int, season: int, prediction_type: str, 
                                  was_correct: bool) -> None:
        """Update team accuracy statistics."""
        with self.get_connection() as conn:
            # Insert or update accuracy stats
            conn.execute("""
                INSERT INTO team_accuracy_stats (team_id, season, prediction_type, total_predictions, correct_predictions)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(team_id, season, prediction_type) DO UPDATE SET
                    total_predictions = total_predictions + 1,
                    correct_predictions = correct_predictions + ?,
                    accuracy_percentage = (CAST(correct_predictions + ? AS REAL) / (total_predictions + 1)) * 100,
                    last_updated = CURRENT_TIMESTAMP
            """, (team_id, season, prediction_type, 1 if was_correct else 0, 
                  1 if was_correct else 0, 1 if was_correct else 0))
            conn.commit()
    
    def get_team_accuracy(self, team_id: int, season: int = None) -> List[Dict]:
        """Get team accuracy statistics."""
        with self.get_connection() as conn:
            if season:
                cursor = conn.execute("""
                    SELECT * FROM team_accuracy_stats 
                    WHERE team_id = ? AND season = ?
                    ORDER BY prediction_type
                """, (team_id, season))
            else:
                cursor = conn.execute("""
                    SELECT * FROM team_accuracy_stats 
                    WHERE team_id = ?
                    ORDER BY season DESC, prediction_type
                """, (team_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # UTILITY OPERATIONS
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # Count tables
            tables = ['teams', 'matches', 'predictions', 'prediction_results', 
                     'team_accuracy_stats', 'team_accuracy_history']
            
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Get seasons
            cursor = conn.execute("SELECT DISTINCT season FROM teams ORDER BY season DESC")
            stats['seasons'] = [row[0] for row in cursor.fetchall()]
            
            # Get latest match
            cursor = conn.execute("SELECT MAX(match_date) FROM matches")
            latest_match = cursor.fetchone()[0]
            stats['latest_match'] = latest_match
            
            return stats
    
    def clear_season_data(self, season: int) -> None:
        """Clear all data for a specific season."""
        with self.get_connection() as conn:
            # Delete in reverse dependency order
            conn.execute("DELETE FROM team_accuracy_history WHERE season = ?", (season,))
            conn.execute("DELETE FROM team_accuracy_stats WHERE season = ?", (season,))
            conn.execute("DELETE FROM prediction_results WHERE prediction_id IN (SELECT id FROM predictions WHERE season = ?)", (season,))
            conn.execute("DELETE FROM predictions WHERE season = ?", (season,))
            conn.execute("DELETE FROM matches WHERE season = ?", (season,))
            conn.execute("DELETE FROM teams WHERE season = ?", (season,))
            conn.commit()
            logger.info(f"Cleared all data for season {season}")

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
