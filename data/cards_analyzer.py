"""
Cards analysis functions for total cards predictions.
Provides venue-specific analysis for yellow and red cards patterns.
"""
import logging
from typing import Dict, List, Tuple, Optional
from data.database import DatabaseManager
from data.api_client import get_api_client

logger = logging.getLogger(__name__)

class CardsAnalyzer:
    """
    Analyzes team cards performance with venue-specific filtering.
    Provides data for cards predictions (Over 1.5, 2.5, 3.5 lines).
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize cards analyzer with database manager."""
        self.db_manager = db_manager or DatabaseManager()
        self.api_client = get_api_client()
    
    def analyze_team_cards_performance(self, team_id: int, season: int, venue: str) -> Dict:
        """
        Analyze team's cards performance with venue filtering.
        
        Args:
            team_id: Internal team ID
            season: Season year
            venue: 'home' or 'away' - only considers games at this venue
            
        Returns:
            Dictionary with cards performance metrics
        """
        try:
            # Get matches with cards data
            matches_with_cards = self._get_team_matches_with_cards(team_id, season, limit=20)
            
            if not matches_with_cards:
                logger.info(f"No cards data available for team {team_id} in season {season}")
                return self._get_empty_cards_performance()
            
            # Filter for venue-specific matches only
            if venue == 'home':
                venue_matches = [m for m in matches_with_cards if m['home_team_id'] == team_id]
            elif venue == 'away':
                venue_matches = [m for m in matches_with_cards if m['away_team_id'] == team_id]
            else:
                logger.error(f"Invalid venue: {venue}. Must be 'home' or 'away'")
                return self._get_empty_cards_performance()
            
            if not venue_matches:
                logger.info(f"No {venue} cards data available for team {team_id} in season {season}")
                return self._get_empty_cards_performance()
            
            # Analyze cards performance
            return self._calculate_cards_metrics(venue_matches, team_id, venue)
            
        except Exception as e:
            logger.error(f"Error analyzing cards performance for team {team_id}: {e}")
            return self._get_empty_cards_performance()
    
    def _calculate_cards_metrics(self, matches: List, team_id: int, venue: str) -> Dict:
        """Calculate cards performance metrics from matches."""
        
        total_games = len(matches)
        cards_1plus = 0  # Matches with 1+ cards
        cards_2plus = 0  # Matches with 2+ cards
        cards_3plus = 0  # Matches with 3+ cards
        cards_4plus = 0  # Matches with 4+ cards
        
        total_cards_received = 0
        total_yellow_cards = 0
        total_red_cards = 0
        
        cards_distribution = []
        
        for match in matches:
            home_team_id = match['home_team_id']
            
            # Get cards for this team
            if home_team_id == team_id:  # Team is playing at home
                yellow = match['yellow_cards_home'] or 0
                red = match['red_cards_home'] or 0
            else:  # Team is playing away
                yellow = match['yellow_cards_away'] or 0
                red = match['red_cards_away'] or 0
            
            # Total cards for this team in this match (red = 1 card as per user requirement)
            team_cards = yellow + red
            
            # Count patterns
            if team_cards >= 1:
                cards_1plus += 1
            if team_cards >= 2:
                cards_2plus += 1
            if team_cards >= 3:
                cards_3plus += 1
            if team_cards >= 4:
                cards_4plus += 1
            
            total_cards_received += team_cards
            total_yellow_cards += yellow
            total_red_cards += red
            cards_distribution.append(team_cards)
        
        # Calculate rates
        cards_1plus_rate = (cards_1plus / total_games) * 100 if total_games > 0 else 0
        cards_2plus_rate = (cards_2plus / total_games) * 100 if total_games > 0 else 0
        cards_3plus_rate = (cards_3plus / total_games) * 100 if total_games > 0 else 0
        cards_4plus_rate = (cards_4plus / total_games) * 100 if total_games > 0 else 0
        
        avg_cards = total_cards_received / total_games if total_games > 0 else 0
        avg_yellow = total_yellow_cards / total_games if total_games > 0 else 0
        avg_red = total_red_cards / total_games if total_games > 0 else 0
        
        # Calculate consistency (standard deviation)
        import statistics
        std_dev = statistics.stdev(cards_distribution) if len(cards_distribution) > 1 else 0
        consistency_score = (1 - (std_dev / (avg_cards + 0.1))) * 100 if avg_cards > 0 else 0
        consistency_score = max(0, min(100, consistency_score))
        
        return {
            'team_id': team_id,
            'venue': venue,
            'total_games': total_games,
            'avg_cards': round(avg_cards, 2),
            'avg_yellow_cards': round(avg_yellow, 2),
            'avg_red_cards': round(avg_red, 2),
            'cards_1plus_rate': round(cards_1plus_rate, 1),
            'cards_2plus_rate': round(cards_2plus_rate, 1),
            'cards_3plus_rate': round(cards_3plus_rate, 1),
            'cards_4plus_rate': round(cards_4plus_rate, 1),
            'total_cards_received': total_cards_received,
            'total_yellow_cards': total_yellow_cards,
            'total_red_cards': total_red_cards,
            'consistency_score': round(consistency_score, 1),
            'std_dev': round(std_dev, 2),
            'data_quality': self._assess_data_quality(total_games),
            'venue_specific': True
        }
    
    def predict_match_cards(self, home_team_id: int, away_team_id: int, season: int) -> Dict:
        """
        Predict total cards for a match.
        
        Args:
            home_team_id: Internal ID of home team
            away_team_id: Internal ID of away team
            season: Season year
            
        Returns:
            Dictionary with cards prediction and line probabilities
        """
        try:
            # Get venue-specific performance for both teams
            home_performance = self.analyze_team_cards_performance(home_team_id, season, 'home')
            away_performance = self.analyze_team_cards_performance(away_team_id, season, 'away')
            
            # Check if we have sufficient data
            min_games = min(home_performance['total_games'], away_performance['total_games'])
            
            if min_games < 3:
                return {
                    'total_cards': 0.0,
                    'home_cards': 0.0,
                    'away_cards': 0.0,
                    'over_1_5': 50.0,
                    'over_2_5': 50.0,
                    'over_3_5': 50.0,
                    'confidence': 'Low',
                    'confidence_score': 20.0,
                    'reasoning': 'Insufficient cards data (need at least 3 matches per team)',
                    'home_team_stats': home_performance,
                    'away_team_stats': away_performance,
                    'data_quality': 'Poor'
                }
            
            # Predict cards for each team
            home_cards = home_performance['avg_cards']
            away_cards = away_performance['avg_cards']
            total_cards = home_cards + away_cards
            
            # Calculate line probabilities based on historical rates
            # For Over 1.5: Use cards_2plus_rate (2+ cards)
            # For Over 2.5: Use cards_3plus_rate (3+ cards)
            # For Over 3.5: Use cards_4plus_rate (4+ cards)
            
            # Combine home and away probabilities for match totals
            over_1_5_prob = self._calculate_match_line_probability(
                home_performance['cards_2plus_rate'],
                away_performance['cards_2plus_rate'],
                total_cards,
                1.5
            )
            
            over_2_5_prob = self._calculate_match_line_probability(
                home_performance['cards_3plus_rate'],
                away_performance['cards_3plus_rate'],
                total_cards,
                2.5
            )
            
            over_3_5_prob = self._calculate_match_line_probability(
                home_performance['cards_4plus_rate'],
                away_performance['cards_4plus_rate'],
                total_cards,
                3.5
            )
            
            # Calculate confidence based on data quality and consistency
            avg_consistency = (home_performance['consistency_score'] + away_performance['consistency_score']) / 2
            confidence_score = self._calculate_cards_confidence(min_games, avg_consistency)
            
            return {
                'total_cards': round(total_cards, 1),
                'home_cards': round(home_cards, 1),
                'away_cards': round(away_cards, 1),
                'over_1_5': round(over_1_5_prob, 1),
                'over_2_5': round(over_2_5_prob, 1),
                'over_3_5': round(over_3_5_prob, 1),
                'confidence': self._get_confidence_label(confidence_score),
                'confidence_score': round(confidence_score, 1),
                'reasoning': self._generate_reasoning(home_performance, away_performance, total_cards),
                'home_team_stats': home_performance,
                'away_team_stats': away_performance,
                'data_quality': self._assess_combined_data_quality(min_games),
                'methodology': 'Venue-specific cards analysis with consistency scoring'
            }
            
        except Exception as e:
            logger.error(f"Error predicting cards for teams {home_team_id} vs {away_team_id}: {e}")
            return {
                'total_cards': 0.0,
                'home_cards': 0.0,
                'away_cards': 0.0,
                'over_1_5': 50.0,
                'over_2_5': 50.0,
                'over_3_5': 50.0,
                'confidence': 'Low',
                'confidence_score': 20.0,
                'reasoning': f'Prediction error: {str(e)}',
                'home_team_stats': self._get_empty_cards_performance(),
                'away_team_stats': self._get_empty_cards_performance(),
                'data_quality': 'Error',
                'methodology': 'Error fallback'
            }
    
    def _calculate_match_line_probability(self, home_rate: float, away_rate: float, 
                                         total_cards: float, line: float) -> float:
        """Calculate probability of match total going over a specific line."""
        
        # Use team historical rates as base
        combined_rate = (home_rate + away_rate) / 2
        
        # Adjust based on predicted total vs line
        if total_cards > line + 1:
            # Predicted total well above line
            adjustment = min(20, (total_cards - line) * 10)
            return min(95, combined_rate + adjustment)
        elif total_cards > line:
            # Predicted total above line
            adjustment = min(15, (total_cards - line) * 8)
            return min(90, combined_rate + adjustment)
        elif total_cards > line - 0.5:
            # Predicted total close to line
            return combined_rate
        else:
            # Predicted total below line
            reduction = min(20, (line - total_cards) * 10)
            return max(10, combined_rate - reduction)
    
    def _calculate_cards_confidence(self, min_games: int, avg_consistency: float) -> float:
        """Calculate confidence score based on data quality and consistency."""
        
        # Base confidence from number of games
        if min_games >= 15:
            data_confidence = 85
        elif min_games >= 10:
            data_confidence = 75
        elif min_games >= 5:
            data_confidence = 60
        else:
            data_confidence = 40
        
        # Adjust based on consistency
        consistency_factor = avg_consistency / 100
        
        final_confidence = data_confidence * (0.7 + 0.3 * consistency_factor)
        
        return max(20, min(95, final_confidence))
    
    def _generate_reasoning(self, home_perf: Dict, away_perf: Dict, total_cards: float) -> str:
        """Generate human-readable reasoning for cards prediction."""
        
        reasoning_parts = []
        
        # Home team analysis
        if home_perf['avg_cards'] >= 2.5:
            reasoning_parts.append(f"Home team averages {home_perf['avg_cards']:.1f} cards (high)")
        elif home_perf['avg_cards'] >= 1.5:
            reasoning_parts.append(f"Home team averages {home_perf['avg_cards']:.1f} cards (moderate)")
        else:
            reasoning_parts.append(f"Home team averages {home_perf['avg_cards']:.1f} cards (low)")
        
        # Away team analysis
        if away_perf['avg_cards'] >= 2.5:
            reasoning_parts.append(f"Away team averages {away_perf['avg_cards']:.1f} cards (high)")
        elif away_perf['avg_cards'] >= 1.5:
            reasoning_parts.append(f"Away team averages {away_perf['avg_cards']:.1f} cards (moderate)")
        else:
            reasoning_parts.append(f"Away team averages {away_perf['avg_cards']:.1f} cards (low)")
        
        # Total prediction
        if total_cards >= 5:
            reasoning_parts.append(f"Expect {total_cards:.1f} total cards (very high)")
        elif total_cards >= 4:
            reasoning_parts.append(f"Expect {total_cards:.1f} total cards (high)")
        elif total_cards >= 3:
            reasoning_parts.append(f"Expect {total_cards:.1f} total cards (moderate)")
        else:
            reasoning_parts.append(f"Expect {total_cards:.1f} total cards (low)")
        
        return ". ".join(reasoning_parts)
    
    def _get_team_matches_with_cards(self, team_id: int, season: int, limit: int = 20) -> List[Dict]:
        """Get team matches that have cards data."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, ht.name as home_team_name, at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE (m.home_team_id = ? OR m.away_team_id = ?) 
                AND m.season = ? AND m.status = 'FT'
                AND m.yellow_cards_home IS NOT NULL AND m.yellow_cards_away IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT ?
            """, (team_id, team_id, season, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_empty_cards_performance(self) -> Dict:
        """Return empty cards performance dictionary."""
        return {
            'team_id': None,
            'venue': None,
            'total_games': 0,
            'avg_cards': 0.0,
            'avg_yellow_cards': 0.0,
            'avg_red_cards': 0.0,
            'cards_1plus_rate': 0.0,
            'cards_2plus_rate': 0.0,
            'cards_3plus_rate': 0.0,
            'cards_4plus_rate': 0.0,
            'total_cards_received': 0,
            'total_yellow_cards': 0,
            'total_red_cards': 0,
            'consistency_score': 0.0,
            'std_dev': 0.0,
            'data_quality': 'None',
            'venue_specific': True
        }
    
    def _assess_data_quality(self, num_games: int) -> str:
        """Assess data quality based on number of games."""
        if num_games >= 15:
            return 'Excellent'
        elif num_games >= 10:
            return 'Good'
        elif num_games >= 5:
            return 'Fair'
        elif num_games >= 3:
            return 'Acceptable'
        else:
            return 'Poor'
    
    def _assess_combined_data_quality(self, min_games: int) -> str:
        """Assess combined data quality for both teams."""
        if min_games >= 15:
            return 'Excellent'
        elif min_games >= 10:
            return 'Good'
        elif min_games >= 5:
            return 'Fair'
        else:
            return 'Poor'
    
    def _get_confidence_label(self, confidence_score: float) -> str:
        """Convert confidence score to label."""
        if confidence_score >= 80:
            return 'Very High'
        elif confidence_score >= 70:
            return 'High'
        elif confidence_score >= 60:
            return 'Medium'
        elif confidence_score >= 50:
            return 'Low'
        else:
            return 'Very Low'

def predict_match_cards(home_team_id: int, away_team_id: int, season: int) -> Dict:
    """
    Standalone function to predict match cards.
    Follows same pattern as predict_match_corners().
    
    Args:
        home_team_id: Internal ID of home team
        away_team_id: Internal ID of away team
        season: Season year
        
    Returns:
        Dictionary with cards prediction
    """
    analyzer = CardsAnalyzer()
    return analyzer.predict_match_cards(home_team_id, away_team_id, season)
