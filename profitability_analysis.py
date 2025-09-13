#!/usr/bin/env python3
"""
Profitability Analysis for 2024 Season Backtesting Data
Analyzes betting strategy with 80% confidence threshold and specific odds.
"""

from data.database import get_db_manager
import sqlite3

def analyze_2024_profitability():
    """Analyze profitability of 2024 betting strategy"""
    
    # Betting parameters
    odds = {
        'over_5_5': 1.05,
        'over_6_5': 1.10, 
        'home_score': 1.06,
        'away_score': 1.14
    }
    confidence_threshold = 80.0
    stake_per_bet = 1.0  # 1 unit per bet
    
    print("🎯 PROFITABILITY ANALYSIS - 2024 SEASON")
    print("="*50)
    print(f"Strategy: Bet when confidence >= {confidence_threshold}%")
    print(f"Stake per bet: {stake_per_bet} units")
    print(f"Odds: Over 5.5 = {odds['over_5_5']}, Over 6.5 = {odds['over_6_5']}")
    print(f"      Home Score = {odds['home_score']}, Away Score = {odds['away_score']}")
    print()
    
    db_manager = get_db_manager()
    
    with db_manager.get_connection() as conn:
        # Get all 2024 backtesting data with match results
        cursor = conn.execute("""
            SELECT b.home_team_name, b.away_team_name, b.match_date,
                   b.confidence_5_5, b.confidence_6_5,
                   b.home_score_probability, b.away_score_probability,
                   b.actual_total_corners, b.over_5_5_correct, b.over_6_5_correct,
                   m.goals_home, m.goals_away
            FROM date_based_backtests b
            LEFT JOIN matches m ON b.api_fixture_id = m.api_fixture_id
            WHERE b.season = 2024
            ORDER BY b.match_date ASC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ No 2024 backtesting data found!")
            return
        
        print(f"📊 Found {len(results)} matches from 2024 season")
        print()
        
        # Initialize tracking variables
        bet_stats = {
            'over_5_5': {'bets': 0, 'wins': 0, 'total_stake': 0, 'total_return': 0},
            'over_6_5': {'bets': 0, 'wins': 0, 'total_stake': 0, 'total_return': 0},
            'home_score': {'bets': 0, 'wins': 0, 'total_stake': 0, 'total_return': 0},
            'away_score': {'bets': 0, 'wins': 0, 'total_stake': 0, 'total_return': 0}
        }
        
        # Analyze each match
        for row in results:
            home_team, away_team, match_date = row[0], row[1], row[2]
            conf_5_5, conf_6_5 = row[3], row[4]
            home_prob, away_prob = row[5], row[6]
            actual_corners = row[7]
            over_5_5_correct, over_6_5_correct = row[8], row[9]
            goals_home, goals_away = row[10], row[11]
            
            # Check each bet type
            
            # 1. Over 5.5 Corners
            if conf_5_5 and conf_5_5 >= confidence_threshold and actual_corners is not None:
                bet_stats['over_5_5']['bets'] += 1
                bet_stats['over_5_5']['total_stake'] += stake_per_bet
                
                if over_5_5_correct:
                    bet_stats['over_5_5']['wins'] += 1
                    bet_stats['over_5_5']['total_return'] += stake_per_bet * odds['over_5_5']
            
            # 2. Over 6.5 Corners  
            if conf_6_5 and conf_6_5 >= confidence_threshold and actual_corners is not None:
                bet_stats['over_6_5']['bets'] += 1
                bet_stats['over_6_5']['total_stake'] += stake_per_bet
                
                if over_6_5_correct:
                    bet_stats['over_6_5']['wins'] += 1
                    bet_stats['over_6_5']['total_return'] += stake_per_bet * odds['over_6_5']
            
            # 3. Home Team to Score
            if home_prob and home_prob >= confidence_threshold and goals_home is not None:
                bet_stats['home_score']['bets'] += 1
                bet_stats['home_score']['total_stake'] += stake_per_bet
                
                if goals_home > 0:
                    bet_stats['home_score']['wins'] += 1
                    bet_stats['home_score']['total_return'] += stake_per_bet * odds['home_score']
            
            # 4. Away Team to Score
            if away_prob and away_prob >= confidence_threshold and goals_away is not None:
                bet_stats['away_score']['bets'] += 1
                bet_stats['away_score']['total_stake'] += stake_per_bet
                
                if goals_away > 0:
                    bet_stats['away_score']['wins'] += 1
                    bet_stats['away_score']['total_return'] += stake_per_bet * odds['away_score']
        
        # Calculate and display results
        print("📈 DETAILED RESULTS BY BET TYPE")
        print("="*50)
        
        total_stake = 0
        total_return = 0
        total_profit = 0
        
        for bet_type, stats in bet_stats.items():
            if stats['bets'] > 0:
                win_rate = (stats['wins'] / stats['bets']) * 100
                net_profit = stats['total_return'] - stats['total_stake']
                roi = (net_profit / stats['total_stake']) * 100 if stats['total_stake'] > 0 else 0
                
                total_stake += stats['total_stake']
                total_return += stats['total_return']
                
                print(f"{bet_type.replace('_', ' ').title()}:")
                print(f"  Bets placed: {stats['bets']}")
                print(f"  Wins: {stats['wins']} ({win_rate:.1f}%)")
                print(f"  Total staked: {stats['total_stake']:.2f} units")
                print(f"  Total return: {stats['total_return']:.2f} units")
                print(f"  Net profit: {net_profit:.2f} units")
                print(f"  ROI: {roi:.2f}%")
                print()
            else:
                print(f"{bet_type.replace('_', ' ').title()}: No qualifying bets (0 bets with {confidence_threshold}% confidence)")
                print()
        
        # Overall summary
        total_profit = total_return - total_stake
        overall_roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
        
        print("🏆 OVERALL STRATEGY RESULTS")
        print("="*50)
        print(f"Total stakes: {total_stake:.2f} units")
        print(f"Total returns: {total_return:.2f} units")
        print(f"Net profit/loss: {total_profit:.2f} units")
        print(f"Overall ROI: {overall_roi:.2f}%")
        print()
        
        if total_profit > 0:
            print("✅ PROFITABLE STRATEGY!")
        else:
            print("❌ UNPROFITABLE STRATEGY")
            
        print(f"Break-even would require {(total_stake/total_return)*100:.1f}% win rate")

if __name__ == "__main__":
    analyze_2024_profitability()


