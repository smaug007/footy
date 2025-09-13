"""
Dynamic weighting system for goal predictions based on team strength matchups.
Provides sophisticated, context-aware weighting instead of fixed ratios.
"""
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class DynamicWeightingEngine:
    """
    Calculates dynamic weights for goal predictions based on team strength matchups.
    
    The system classifies teams into strength categories and applies appropriate
    weights based on the specific matchup dynamics (e.g., strong attack vs weak defense).
    """
    
    def __init__(self):
        """Initialize the dynamic weighting engine with CSL-appropriate thresholds."""
        self.attack_thresholds = {
            'very_strong': 80,  # Scores in 80%+ of games
            'strong': 65,       # Scores in 65-79% of games  
            'average': 45,      # Scores in 45-64% of games
            'weak': 30,         # Scores in 30-44% of games
            # very_weak: <30%   # Scores in <30% of games
        }
        
        self.defense_thresholds = {
            'very_strong': 20,  # Concedes in ≤20% of games (80%+ clean sheets)
            'strong': 35,       # Concedes in 21-35% of games
            'average': 55,      # Concedes in 36-55% of games  
            'weak': 70,         # Concedes in 56-70% of games
            # very_weak: >70%   # Concedes in 70%+ of games
        }
        
        # Dynamic weight matrix: [attack_strength][defense_strength] = (attack_weight, defense_weight)
        self.weight_matrix = {
            'very_strong': {
                'very_strong': (0.45, 0.55),  # Elite vs elite - defense slightly favored
                'strong':      (0.50, 0.50),  # Elite attack vs strong defense - balanced
                'average':     (0.65, 0.35),  # Elite attack vs average defense - attack favored
                'weak':        (0.75, 0.25),  # Elite attack vs weak defense - attack heavily favored
                'very_weak':   (0.80, 0.20),  # Elite attack vs terrible defense - attack dominates
            },
            'strong': {
                'very_strong': (0.35, 0.65),  # Strong attack vs elite defense - defense favored
                'strong':      (0.50, 0.50),  # Strong vs strong - balanced
                'average':     (0.60, 0.40),  # Strong attack vs average defense - attack slightly favored
                'weak':        (0.70, 0.30),  # Strong attack vs weak defense - attack favored
                'very_weak':   (0.75, 0.25),  # Strong attack vs terrible defense - attack heavily favored
            },
            'average': {
                'very_strong': (0.25, 0.75),  # Average attack vs elite defense - defense heavily favored
                'strong':      (0.40, 0.60),  # Average attack vs strong defense - defense favored
                'average':     (0.50, 0.50),  # Average vs average - balanced
                'weak':        (0.60, 0.40),  # Average attack vs weak defense - attack slightly favored
                'very_weak':   (0.65, 0.35),  # Average attack vs terrible defense - attack favored
            },
            'weak': {
                'very_strong': (0.20, 0.80),  # Weak attack vs elite defense - defense dominates
                'strong':      (0.30, 0.70),  # Weak attack vs strong defense - defense heavily favored
                'average':     (0.40, 0.60),  # Weak attack vs average defense - defense favored
                'weak':        (0.50, 0.50),  # Weak vs weak - balanced
                'very_weak':   (0.55, 0.45),  # Weak attack vs terrible defense - attack slightly favored
            },
            'very_weak': {
                'very_strong': (0.15, 0.85),  # Terrible attack vs elite defense - defense completely dominates
                'strong':      (0.25, 0.75),  # Terrible attack vs strong defense - defense heavily favored
                'average':     (0.35, 0.65),  # Terrible attack vs average defense - defense favored
                'weak':        (0.45, 0.55),  # Terrible attack vs weak defense - defense slightly favored
                'very_weak':   (0.50, 0.50),  # Terrible vs terrible - balanced (both unreliable)
            }
        }
    
    def classify_team_strength(self, rate: float, metric_type: str) -> str:
        """
        Classify team strength based on their goal rate.
        
        Args:
            rate: Percentage rate (0-100)
            metric_type: 'attacking' or 'defending'
            
        Returns:
            Strength classification: 'very_strong', 'strong', 'average', 'weak', 'very_weak'
        """
        try:
            if metric_type == 'attacking':
                # Higher rate = stronger attack
                if rate >= self.attack_thresholds['very_strong']:
                    return 'very_strong'
                elif rate >= self.attack_thresholds['strong']:
                    return 'strong'
                elif rate >= self.attack_thresholds['average']:
                    return 'average'
                elif rate >= self.attack_thresholds['weak']:
                    return 'weak'
                else:
                    return 'very_weak'
                    
            elif metric_type == 'defending':
                # Lower conceding rate = stronger defense
                if rate <= self.defense_thresholds['very_strong']:
                    return 'very_strong'
                elif rate <= self.defense_thresholds['strong']:
                    return 'strong'
                elif rate <= self.defense_thresholds['average']:
                    return 'average'
                elif rate <= self.defense_thresholds['weak']:
                    return 'weak'
                else:
                    return 'very_weak'
            else:
                logger.warning(f"Unknown metric_type: {metric_type}")
                return 'average'
                
        except Exception as e:
            logger.error(f"Error classifying team strength: {e}")
            return 'average'
    
    def calculate_dynamic_weights(self, attack_rate: float, defense_rate: float) -> Tuple[float, float, Dict]:
        """
        Calculate dynamic weights based on team strength matchup.
        
        Args:
            attack_rate: Attacking team's scoring rate (0-100)
            defense_rate: Defending team's conceding rate (0-100)
            
        Returns:
            Tuple of (attack_weight, defense_weight, reasoning_details)
        """
        try:
            # Classify team strengths
            attack_strength = self.classify_team_strength(attack_rate, 'attacking')
            defense_strength = self.classify_team_strength(defense_rate, 'defending')
            
            # Get weights from matrix
            attack_weight, defense_weight = self.weight_matrix[attack_strength][defense_strength]
            
            # Create reasoning details
            reasoning = self._generate_reasoning(attack_strength, defense_strength, attack_rate, defense_rate, attack_weight, defense_weight)
            
            logger.info(f"Dynamic weights calculated: {attack_weight:.0%} attack / {defense_weight:.0%} defense "
                       f"({attack_strength} attack vs {defense_strength} defense)")
            
            return attack_weight, defense_weight, reasoning
            
        except Exception as e:
            logger.error(f"Error calculating dynamic weights: {e}")
            # Fallback to balanced weighting
            return 0.5, 0.5, {
                'matchup_type': 'error_fallback',
                'description': 'Balanced weighting due to calculation error',
                'confidence_boost': 1.0,
                'attack_strength': 'unknown',
                'defense_strength': 'unknown'
            }
    
    def calculate_confidence_boost(self, attack_weight: float, defense_weight: float) -> float:
        """
        Calculate confidence boost based on weight extremes.
        More extreme weights = higher confidence (clearer favorite).
        
        Args:
            attack_weight: Weight given to attack
            defense_weight: Weight given to defense
            
        Returns:
            Confidence multiplier (1.0 = no boost, 1.15 = 15% boost)
        """
        try:
            weight_difference = abs(attack_weight - defense_weight)
            
            if weight_difference >= 0.5:  # 75/25 or more extreme
                return 1.15  # 15% confidence boost
            elif weight_difference >= 0.3:  # 65/35 or more
                return 1.10  # 10% confidence boost
            elif weight_difference >= 0.2:  # 60/40 or more
                return 1.05  # 5% confidence boost
            else:
                return 1.0   # No boost for balanced matchups
                
        except Exception as e:
            logger.error(f"Error calculating confidence boost: {e}")
            return 1.0
    
    def adjust_weights_for_sample_size(self, attack_weight: float, defense_weight: float, 
                                     attack_games: int, defense_games: int) -> Tuple[float, float]:
        """
        Adjust weights based on data reliability (sample size).
        Small sample sizes move weights towards balanced (50/50).
        
        Args:
            attack_weight: Original attack weight
            defense_weight: Original defense weight
            attack_games: Number of games for attacking team
            defense_games: Number of games for defending team
            
        Returns:
            Adjusted (attack_weight, defense_weight)
        """
        try:
            min_games = min(attack_games, defense_games)
            
            if min_games < 5:
                # Strong adjustment towards balanced for very small samples
                adjustment_factor = 0.4
                balanced_weight = 0.5
                
                attack_weight = attack_weight * (1 - adjustment_factor) + balanced_weight * adjustment_factor
                defense_weight = defense_weight * (1 - adjustment_factor) + balanced_weight * adjustment_factor
                
                logger.info(f"Applied strong sample size adjustment (min_games={min_games}): "
                           f"weights moved {adjustment_factor:.0%} towards balanced")
                           
            elif min_games < 8:
                # Moderate adjustment for small samples
                adjustment_factor = 0.2
                balanced_weight = 0.5
                
                attack_weight = attack_weight * (1 - adjustment_factor) + balanced_weight * adjustment_factor
                defense_weight = defense_weight * (1 - adjustment_factor) + balanced_weight * adjustment_factor
                
                logger.info(f"Applied moderate sample size adjustment (min_games={min_games}): "
                           f"weights moved {adjustment_factor:.0%} towards balanced")
            
            # Ensure weights still sum to 1.0
            total = attack_weight + defense_weight
            return attack_weight / total, defense_weight / total
            
        except Exception as e:
            logger.error(f"Error adjusting weights for sample size: {e}")
            return attack_weight, defense_weight
    
    def _generate_reasoning(self, attack_strength: str, defense_strength: str, 
                          attack_rate: float, defense_rate: float,
                          attack_weight: float, defense_weight: float) -> Dict:
        """Generate human-readable reasoning for the weight decision."""
        
        # Determine matchup type
        if attack_strength == defense_strength:
            if attack_strength in ['very_strong', 'strong']:
                matchup_type = 'elite_clash'
                description = f"Elite {attack_strength.replace('_', ' ')} attack meets elite defense - tight contest"
            elif attack_strength == 'average':
                matchup_type = 'balanced_matchup'
                description = "Average attack vs average defense - evenly matched"
            else:
                matchup_type = 'low_quality_matchup'
                description = f"{attack_strength.replace('_', ' ').title()} attack vs {defense_strength.replace('_', ' ')} defense - unpredictable"
        else:
            # Different strengths
            if 'very_strong' in [attack_strength, defense_strength]:
                if attack_strength == 'very_strong':
                    matchup_type = 'attack_dominance'
                    description = f"Elite attack vs {defense_strength.replace('_', ' ')} defense - attack heavily favored"
                else:
                    matchup_type = 'defense_dominance'  
                    description = f"{attack_strength.replace('_', ' ').title()} attack vs elite defense - defense heavily favored"
            else:
                matchup_type = 'strength_mismatch'
                description = f"{attack_strength.replace('_', ' ').title()} attack vs {defense_strength.replace('_', ' ')} defense"
        
        # Calculate confidence boost
        confidence_boost = self.calculate_confidence_boost(attack_weight, defense_weight)
        
        return {
            'matchup_type': matchup_type,
            'description': description,
            'attack_strength': attack_strength,
            'defense_strength': defense_strength,
            'attack_rate': round(attack_rate, 1),
            'defense_rate': round(defense_rate, 1),
            'attack_weight': round(attack_weight, 2),
            'defense_weight': round(defense_weight, 2),
            'confidence_boost': confidence_boost,
            'weight_explanation': f"{attack_weight:.0%} attack focus / {defense_weight:.0%} defense focus"
        }

    def get_strength_description(self, strength: str, metric_type: str) -> str:
        """Get human-readable description of team strength."""
        descriptions = {
            'attacking': {
                'very_strong': 'Elite Attack (80%+ scoring rate)',
                'strong': 'Strong Attack (65-79% scoring rate)',
                'average': 'Average Attack (45-64% scoring rate)', 
                'weak': 'Weak Attack (30-44% scoring rate)',
                'very_weak': 'Very Weak Attack (<30% scoring rate)'
            },
            'defending': {
                'very_strong': 'Elite Defense (≤20% conceding rate)',
                'strong': 'Strong Defense (21-35% conceding rate)',
                'average': 'Average Defense (36-55% conceding rate)',
                'weak': 'Weak Defense (56-70% conceding rate)', 
                'very_weak': 'Very Weak Defense (70%+ conceding rate)'
            }
        }
        
        return descriptions.get(metric_type, {}).get(strength, f"{strength.replace('_', ' ').title()} {metric_type.title()}")
