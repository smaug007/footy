"""
Date-Based Backtesting Engine for CornERD
Follows the same pattern as the main prediction system but for historical analysis.

Flow:
1. Pick historical date -> 2. Get matches for that date -> 3. Get team historical data 
4. Use existing prediction engine -> 5. Compare with actual results
"""

import logging
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .prediction_engine import PredictionEngine
from .database import get_db_manager


@dataclass
class HistoricalMatch:
    """Represents a match from a historical date for backtesting"""
    api_fixture_id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    match_date: date
    actual_home_corners: Optional[int] = None
    actual_away_corners: Optional[int] = None
    actual_total_corners: Optional[int] = None


@dataclass
class BacktestPrediction:
    """Results from a backtest prediction"""
    api_fixture_id: int
    prediction_date: date
    match_date: date
    home_team_name: str
    away_team_name: str
    predicted_total_corners: float
    confidence_5_5: float
    confidence_6_5: float
    predicted_home_corners: float
    predicted_away_corners: float
    home_score_probability: float
    away_score_probability: float
    actual_total_corners: Optional[int]
    over_5_5_correct: Optional[bool]
    over_6_5_correct: Optional[bool]
    prediction_accuracy: Optional[float]
    analysis_report: str


class DateBasedBacktesting:
    """Clean date-based backtesting that mirrors main prediction system"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.logger = logging.getLogger(__name__)
        self.prediction_engine = PredictionEngine()
        
    def get_matches_for_date(self, target_date: date, season: int = 2025) -> List[HistoricalMatch]:
        """
        Get all matches that were played on a specific date.
        First check database, then API if needed.
        """
        matches = []
        
        with self.db_manager.get_connection() as conn:
            # Query database for matches on this date
            cursor = conn.execute("""
                SELECT m.api_fixture_id, m.home_team_id, m.away_team_id,
                       ht.name as home_team_name, at.name as away_team_name,
                       m.match_date, m.corners_home, m.corners_away
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE DATE(m.match_date) = ? AND m.season = ?
                ORDER BY m.match_date ASC
            """, (target_date.isoformat(), season))
            
            for row in cursor.fetchall():
                api_id, home_id, away_id, home_name, away_name, match_date_str, home_corners, away_corners = row
                
                # Parse match date
                if isinstance(match_date_str, str):
                    match_date_obj = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')).date()
                else:
                    match_date_obj = match_date_str
                
                # Calculate total corners
                total_corners = None
                if home_corners is not None and away_corners is not None:
                    total_corners = home_corners + away_corners
                
                matches.append(HistoricalMatch(
                    api_fixture_id=api_id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    home_team_name=home_name,
                    away_team_name=away_name,
                    match_date=match_date_obj,
                    actual_home_corners=home_corners,
                    actual_away_corners=away_corners,
                    actual_total_corners=total_corners
                ))
        
        self.logger.info(f"Found {len(matches)} matches for date {target_date}")
        return matches
    
    def get_historical_team_data(self, team_id: int, cutoff_date: date, season: int = 2025) -> List[Dict]:
        """
        Get all historical matches for a team up to (but not including) the cutoff date.
        This mirrors how the main prediction system gets team data.
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?)
                    AND DATE(m.match_date) < ?
                    AND m.season = ?
                    AND m.corners_home IS NOT NULL 
                    AND m.corners_away IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 20
            """, (team_id, team_id, cutoff_date.isoformat(), season))
            
            columns = [description[0] for description in cursor.description]
            matches = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            self.logger.debug(f"Found {len(matches)} historical matches for team {team_id} before {cutoff_date}")
            return matches
    
    def run_backtest_for_date(self, target_date: date, season: int = 2025) -> List[BacktestPrediction]:
        """
        Run backtesting for all matches on a specific date.
        This is the main backtesting function that mirrors the main prediction flow.
        """
        self.logger.info(f"Running backtest for date: {target_date}")
        
        # Step 1: Get matches for this date
        matches = self.get_matches_for_date(target_date, season)
        if not matches:
            self.logger.warning(f"No matches found for date {target_date}")
            return []
        
        results = []
        # The cutoff date for historical data is the day *before* the target_date
        # This ensures predictions are made with data available only up to the day before the match
        cutoff_date = target_date - timedelta(days=1)
        
        for match in matches:
            try:
                self.logger.debug(f"Processing match: {match.home_team_name} vs {match.away_team_name}")
                
                # Step 2: Get historical data for both teams (up to day before)
                home_historical = self.get_historical_team_data(match.home_team_id, cutoff_date, season)
                away_historical = self.get_historical_team_data(match.away_team_id, cutoff_date, season)
                
                if len(home_historical) < 3 or len(away_historical) < 3:
                    self.logger.warning(f"Insufficient historical data for match {match.api_fixture_id}")
                    continue
                
                # Step 3: Create team data objects (same format as main system)
                home_team_data = self._create_team_data_object(
                    match.home_team_id, match.home_team_name, home_historical, is_home=True
                )
                away_team_data = self._create_team_data_object(
                    match.away_team_id, match.away_team_name, away_historical, is_home=False
                )
                
                # Step 4: Generate prediction using existing engine (same as main system)
                prediction = self.prediction_engine.predict_match(
                    match.home_team_id, match.away_team_id, 
                    season=season
                )
                
                # Step 5: Calculate accuracy if actual result available
                over_5_5_correct = None
                over_6_5_correct = None
                accuracy = None
                
                if match.actual_total_corners is not None:
                    over_5_5_correct = match.actual_total_corners > 5.5
                    over_6_5_correct = match.actual_total_corners > 6.5
                    
                    # Simple accuracy: closer prediction = higher accuracy
                    prediction_error = abs(prediction.predicted_total_corners - match.actual_total_corners)
                    accuracy = max(0, 100 - (prediction_error * 15))  # 15% penalty per corner difference
                
                # Extract goal scoring probabilities using DYNAMIC WEIGHTING (same as live calculation)
                home_score_prob = 50.0  # default
                away_score_prob = 50.0  # default
                
                # Use the same dynamic weighting logic as calculate_live_comprehensive_goal_probabilities
                try:
                    from app import calculate_real_btts_breakdown, get_team_historical_goal_data_all_games
                    
                    # Get historical data up to cutoff date
                    home_historical = get_team_historical_goal_data_all_games(self.db_manager, match.home_team_id, cutoff_date, season)
                    away_historical = get_team_historical_goal_data_all_games(self.db_manager, match.away_team_id, cutoff_date, season)
                    
                    if home_historical and away_historical:
                        # Calculate dynamic weighted probabilities
                        btts_breakdown = calculate_real_btts_breakdown(home_historical, away_historical, match.home_team_id, match.away_team_id, cutoff_date)
                        
                        # Extract the dynamically weighted probabilities
                        home_score_prob = btts_breakdown['home_team_calculation']['attack_rate'] * btts_breakdown['home_team_calculation']['dynamic_weights'][0] + btts_breakdown['home_team_calculation']['opponent_defense_vulnerability'] * btts_breakdown['home_team_calculation']['dynamic_weights'][1]
                        away_score_prob = btts_breakdown['away_team_calculation']['attack_rate'] * btts_breakdown['away_team_calculation']['dynamic_weights'][0] + btts_breakdown['away_team_calculation']['opponent_defense_vulnerability'] * btts_breakdown['away_team_calculation']['dynamic_weights'][1]
                        
                        self.logger.debug(f"Applied DYNAMIC WEIGHTING: Home {home_score_prob:.1f}%, Away {away_score_prob:.1f}%")
                    else:
                        self.logger.warning(f"Insufficient historical data for dynamic weighting - using defaults")
                        
                except Exception as e:
                    self.logger.warning(f"Error applying dynamic weighting: {e} - falling back to defaults")
                    
                    # Fallback: Try to extract from prediction (likely raw values)
                    if hasattr(prediction, 'goal_predictions') and prediction.goal_predictions:
                        goal_data = prediction.goal_predictions.btts
                        if goal_data and isinstance(goal_data, dict):
                            home_score_prob = goal_data.get('home_team_score_probability', 50.0)
                            away_score_prob = goal_data.get('away_team_score_probability', 50.0)
                            self.logger.debug(f"Fallback: Extracted raw probabilities: Home {home_score_prob}%, Away {away_score_prob}%")
                        else:
                            self.logger.debug("Goal predictions exist but no BTTS data found")
                    else:
                        self.logger.debug("No goal predictions found in prediction result")

                # Create backtest result (include team IDs for analysis links)
                result = BacktestPrediction(
                    api_fixture_id=match.api_fixture_id,
                    prediction_date=cutoff_date,
                    match_date=match.match_date,
                    home_team_name=match.home_team_name,
                    away_team_name=match.away_team_name,
                    predicted_total_corners=prediction.predicted_total_corners,
                    confidence_5_5=prediction.over_5_5_confidence,
                    confidence_6_5=prediction.over_6_5_confidence,
                    predicted_home_corners=prediction.predicted_home_corners,
                    predicted_away_corners=prediction.predicted_away_corners,
                    home_score_probability=home_score_prob,
                    away_score_probability=away_score_prob,
                    actual_total_corners=match.actual_total_corners,
                    over_5_5_correct=over_5_5_correct,
                    over_6_5_correct=over_6_5_correct,
                    prediction_accuracy=accuracy,
                    analysis_report=getattr(prediction, 'analysis_report', 'Historical prediction analysis')
                )
                
                # Store team IDs for analysis page links
                result.home_team_id = match.home_team_id
                result.away_team_id = match.away_team_id
                
                results.append(result)
                self.logger.debug(f"Successful prediction for {match.home_team_name} vs {match.away_team_name}")
                
            except Exception as e:
                self.logger.error(f"Error processing match {match.api_fixture_id}: {str(e)}")
                continue
        
        self.logger.info(f"Completed backtest for {target_date}: {len(results)}/{len(matches)} successful predictions")
        return results
    
    def _create_team_data_object(self, team_id: int, team_name: str, historical_matches: List[Dict], is_home: bool) -> Dict:
        """
        Create team data object in the same format expected by the prediction engine.
        This mirrors the data structure used in the main prediction system.
        """
        if not historical_matches:
            # Return minimal data if no history
            return {
                'id': team_id,
                'name': team_name,
                'recent_matches': [],
                'season_stats': {'corners_for_avg': 4.0, 'corners_against_avg': 4.0},
                'form': 'insufficient_data',
                'is_home': is_home
            }
        
        # Calculate stats from historical matches
        corners_for = []
        corners_against = []
        
        for match in historical_matches:
            if match['home_team_id'] == team_id:
                # Team was home
                corners_for.append(match['corners_home'])
                corners_against.append(match['corners_away'])
            else:
                # Team was away
                corners_for.append(match['corners_away']) 
                corners_against.append(match['corners_home'])
        
        avg_corners_for = sum(corners_for) / len(corners_for) if corners_for else 4.0
        avg_corners_against = sum(corners_against) / len(corners_against) if corners_against else 4.0
        
        # Calculate form
        recent_corners = corners_for[:5]  # Last 5 matches
        avg_recent = sum(recent_corners) / len(recent_corners) if recent_corners else avg_corners_for
        
        if avg_recent > 5.5:
            form = 'excellent'
        elif avg_recent > 4.5:
            form = 'good'
        elif avg_recent > 3.5:
            form = 'average'
        else:
            form = 'poor'
        
        return {
            'id': team_id,
            'name': team_name,
            'recent_matches': historical_matches[:10],  # Last 10 matches
            'season_stats': {
                'corners_for_avg': avg_corners_for,
                'corners_against_avg': avg_corners_against,
                'matches_played': len(historical_matches)
            },
            'form': form,
            'is_home': is_home
        }
    
    def store_backtest_results(self, results: List[BacktestPrediction]) -> int:
        """Store backtest results in a simple format"""
        if not results:
            return 0
        
        stored_count = 0
        run_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.db_manager.get_connection() as conn:
            for result in results:
                try:
                    cursor = conn.execute("""
                        INSERT INTO date_based_backtests (
                            api_fixture_id, prediction_date, match_date, 
                            home_team_id, away_team_id, home_team_name, away_team_name,
                            predicted_total_corners, confidence_5_5, confidence_6_5,
                            predicted_home_corners, predicted_away_corners, 
                            home_score_probability, away_score_probability,
                            actual_total_corners, over_5_5_correct, over_6_5_correct,
                            prediction_accuracy, analysis_report, run_id, season
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.api_fixture_id, result.prediction_date.isoformat(), result.match_date.isoformat(),
                        getattr(result, 'home_team_id', None), getattr(result, 'away_team_id', None),
                        result.home_team_name, result.away_team_name, result.predicted_total_corners,
                        result.confidence_5_5, result.confidence_6_5, result.predicted_home_corners,
                        result.predicted_away_corners, result.home_score_probability, result.away_score_probability,
                        result.actual_total_corners, result.over_5_5_correct, result.over_6_5_correct,
                        result.prediction_accuracy, result.analysis_report, run_id, result.prediction_date.year
                    ))
                    stored_count += 1
                except Exception as e:
                    self.logger.error(f"Error storing backtest result: {str(e)}")
            
            # Explicitly commit the transaction
            conn.commit()
        
        self.logger.info(f"Stored {stored_count}/{len(results)} backtest results")
        return stored_count
    
    def get_available_dates_with_matches(self, season: int = 2025) -> List[date]:
        """Get list of dates that have matches with corner data for backtesting"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT DATE(match_date) as match_date
                FROM matches 
                WHERE season = ? 
                    AND corners_home IS NOT NULL 
                    AND corners_away IS NOT NULL
                ORDER BY match_date ASC
            """, (season,))
            
            dates = []
            for row in cursor.fetchall():
                date_str = row[0]
                if date_str:
                    dates.append(datetime.fromisoformat(date_str).date())
            
            return dates
    
    def run_batch_backtests(self, season: int = 2025, max_dates: Optional[int] = None) -> Dict[str, Any]:
        """
        Run backtests for all available dates in batch.
        
        Args:
            season: Season to run backtests for
            max_dates: Maximum number of dates to process (None for all)
            
        Returns:
            Dict with batch processing results
        """
        self.logger.info(f"🚀 Starting batch backtesting for season {season}")
        
        # Get all available dates
        available_dates = self.get_available_dates_with_matches(season)
        
        if max_dates:
            available_dates = available_dates[:max_dates]
            
        self.logger.info(f"📅 Found {len(available_dates)} dates to process")
        
        if not available_dates:
            return {
                'success': False,
                'message': 'No dates available for backtesting',
                'dates_processed': 0,
                'total_predictions': 0
            }
        
        # Track batch progress
        batch_results = {
            'dates_processed': 0,
            'total_predictions': 0,
            'successful_dates': 0,
            'failed_dates': 0,
            'errors': []
        }
        
        for i, target_date in enumerate(available_dates, 1):
            try:
                self.logger.info(f"🔄 Processing date {i}/{len(available_dates)}: {target_date}")
                
                # Check if already processed
                with self.db_manager.get_connection() as conn:
                    existing = conn.execute(
                        "SELECT COUNT(*) FROM date_based_backtests WHERE match_date = ?", 
                        (target_date.isoformat(),)
                    ).fetchone()
                
                if existing and existing[0] > 0:
                    self.logger.info(f"⏭️  Skipping {target_date} - already processed ({existing[0]} predictions)")
                    batch_results['dates_processed'] += 1
                    batch_results['successful_dates'] += 1
                    batch_results['total_predictions'] += existing[0]
                    continue
                
                # Run backtest for this date
                predictions = self.run_backtest_for_date(target_date, season)
                
                if predictions:
                    # Store results
                    stored_count = self.store_backtest_results(predictions)
                    
                    batch_results['dates_processed'] += 1
                    batch_results['total_predictions'] += stored_count
                    batch_results['successful_dates'] += 1
                    
                    self.logger.info(f"✅ Completed {target_date}: {stored_count} predictions")
                else:
                    batch_results['failed_dates'] += 1
                    batch_results['errors'].append(f"No predictions generated for {target_date}")
                    self.logger.warning(f"⚠️  No predictions for {target_date}")
                    
            except Exception as e:
                batch_results['failed_dates'] += 1
                error_msg = f"Error processing {target_date}: {str(e)}"
                batch_results['errors'].append(error_msg)
                self.logger.error(error_msg)
                continue
        
        # Final summary
        success_rate = (batch_results['successful_dates'] / len(available_dates)) * 100 if available_dates else 0
        
        self.logger.info(f"🎯 Batch backtesting completed:")
        self.logger.info(f"   ✅ Successful dates: {batch_results['successful_dates']}/{len(available_dates)} ({success_rate:.1f}%)")
        self.logger.info(f"   📊 Total predictions: {batch_results['total_predictions']}")
        self.logger.info(f"   ❌ Failed dates: {batch_results['failed_dates']}")
        
        return {
            'success': True,
            'message': f"Batch backtesting completed: {batch_results['successful_dates']}/{len(available_dates)} dates processed",
            'dates_available': len(available_dates),
            'dates_processed': batch_results['dates_processed'],
            'successful_dates': batch_results['successful_dates'],
            'failed_dates': batch_results['failed_dates'],
            'total_predictions': batch_results['total_predictions'],
            'success_rate': round(success_rate, 1),
            'errors': batch_results['errors'][:5]  # Limit to first 5 errors
        }

    def get_backtest_summary(self, season: Optional[int] = None) -> Dict[str, Any]:
        """Get summary of stored backtest results, optionally filtered by season"""
        with self.db_manager.get_connection() as conn:
            try:
                if season:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_predictions,
                            AVG(prediction_accuracy) as avg_accuracy,
                            SUM(CASE WHEN over_5_5_correct = 1 THEN 1 ELSE 0 END) as over_5_5_wins,
                            SUM(CASE WHEN over_6_5_correct = 1 THEN 1 ELSE 0 END) as over_6_5_wins,
                            COUNT(CASE WHEN actual_total_corners IS NOT NULL THEN 1 END) as verified_predictions
                        FROM date_based_backtests
                        WHERE season = ?
                    """, (season,))
                else:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_predictions,
                            AVG(prediction_accuracy) as avg_accuracy,
                            SUM(CASE WHEN over_5_5_correct = 1 THEN 1 ELSE 0 END) as over_5_5_wins,
                            SUM(CASE WHEN over_6_5_correct = 1 THEN 1 ELSE 0 END) as over_6_5_wins,
                            COUNT(CASE WHEN actual_total_corners IS NOT NULL THEN 1 END) as verified_predictions
                        FROM date_based_backtests
                    """)
                
                row = cursor.fetchone()
                if row and row[0] > 0:
                    verified = row[4] or 1  # Avoid division by zero
                    return {
                        'total_predictions': row[0],
                        'average_accuracy': round(row[1] or 0, 2),
                        'over_5_5_success_rate': round((row[2] or 0) / verified * 100, 2),
                        'over_6_5_success_rate': round((row[3] or 0) / verified * 100, 2),
                        'verified_predictions': row[4] or 0
                    }
            except Exception as e:
                self.logger.error(f"Error getting backtest summary: {str(e)}")
        
        # Return empty summary if no data or error
        return {
            'total_predictions': 0,
            'average_accuracy': 0,
            'over_5_5_success_rate': 0,
            'over_6_5_success_rate': 0,
            'verified_predictions': 0
        }
