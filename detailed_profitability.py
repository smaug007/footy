#!/usr/bin/env python3
"""
Enhanced Profitability Analysis for 2024 Season Backtesting Data
"""

from data.database import get_db_manager
import sqlite3

def detailed_profitability_analysis():
    """Enhanced profitability analysis with more details"""
    
    # Betting parameters
    odds = {
        'over_5_5': 1.05,
        'over_6_5': 1.10, 
        'home_score': 1.06,
        'away_score': 1.14
    }
    confidence_threshold = 80.0
    stake_per_bet = 1.0
    
    print("💰 ENHANCED PROFITABILITY ANALYSIS - 2024 SEASON")
    print("=" * 60)
    print(f"Strategy: Bet when confidence >= {confidence_threshold}%")
    print(f"Stake per bet: {stake_per_bet} units")
    print("Odds:")
    for bet_type, odd in odds.items():
        print(f"  {bet_type.replace('_', ' ').title()}: {odd}")
    print()
    
    db_manager = get_db_manager()
    
    with db_manager.get_connection() as conn:
        # Get comprehensive data
        cursor = conn.execute("""
            SELECT b.home_team_name, b.away_team_name, b.match_date,
                   b.confidence_5_5, b.confidence_6_5,
                   b.home_score_probability, b.away_score_probability,
                   b.actual_total_corners, b.over_5_5_correct, b.over_6_5_correct,
                   m.goals_home, m.goals_away,
                   b.predicted_total_corners, b.prediction_accuracy
            FROM date_based_backtests b
            LEFT JOIN matches m ON b.api_fixture_id = m.api_fixture_id
            WHERE b.season = 2024
            AND b.actual_total_corners IS NOT NULL
            ORDER BY b.match_date ASC
        """)
        
        results = cursor.fetchall()
        
        print(f"📊 Analyzing {len(results)} completed matches from 2024 season\n")
        
        # Initialize comprehensive tracking
        bet_stats = {}
        for bet_type in odds.keys():
            bet_stats[bet_type] = {
                'bets': 0, 'wins': 0, 'total_stake': 0, 'total_return': 0,
                'winning_bets': [], 'losing_bets': []
            }
        
        # Process each match
        for row in results:
            home_team, away_team, match_date = row[0], row[1], row[2]
            conf_5_5, conf_6_5 = row[3] or 0, row[4] or 0
            home_prob, away_prob = row[5] or 0, row[6] or 0
            actual_corners = row[7]
            over_5_5_correct, over_6_5_correct = row[8], row[9]
            goals_home, goals_away = row[10] or 0, row[11] or 0
            
            # Over 5.5 Corners
            if conf_5_5 >= confidence_threshold:
                bet_stats['over_5_5']['bets'] += 1
                bet_stats['over_5_5']['total_stake'] += stake_per_bet
                
                if over_5_5_correct:
                    bet_stats['over_5_5']['wins'] += 1
                    payout = stake_per_bet * odds['over_5_5']
                    bet_stats['over_5_5']['total_return'] += payout
                    bet_stats['over_5_5']['winning_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'corners': actual_corners,
                        'confidence': conf_5_5,
                        'payout': payout
                    })
                else:
                    bet_stats['over_5_5']['losing_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'corners': actual_corners,
                        'confidence': conf_5_5
                    })
            
            # Over 6.5 Corners
            if conf_6_5 >= confidence_threshold:
                bet_stats['over_6_5']['bets'] += 1
                bet_stats['over_6_5']['total_stake'] += stake_per_bet
                
                if over_6_5_correct:
                    bet_stats['over_6_5']['wins'] += 1
                    payout = stake_per_bet * odds['over_6_5']
                    bet_stats['over_6_5']['total_return'] += payout
                    bet_stats['over_6_5']['winning_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'corners': actual_corners,
                        'confidence': conf_6_5,
                        'payout': payout
                    })
                else:
                    bet_stats['over_6_5']['losing_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'corners': actual_corners,
                        'confidence': conf_6_5
                    })
            
            # Home Team to Score
            if home_prob >= confidence_threshold:
                bet_stats['home_score']['bets'] += 1
                bet_stats['home_score']['total_stake'] += stake_per_bet
                home_scored = goals_home > 0
                
                if home_scored:
                    bet_stats['home_score']['wins'] += 1
                    payout = stake_per_bet * odds['home_score']
                    bet_stats['home_score']['total_return'] += payout
                    bet_stats['home_score']['winning_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'score': f"{goals_home}-{goals_away}",
                        'confidence': home_prob,
                        'payout': payout
                    })
                else:
                    bet_stats['home_score']['losing_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'score': f"{goals_home}-{goals_away}",
                        'confidence': home_prob
                    })
            
            # Away Team to Score
            if away_prob >= confidence_threshold:
                bet_stats['away_score']['bets'] += 1
                bet_stats['away_score']['total_stake'] += stake_per_bet
                away_scored = goals_away > 0
                
                if away_scored:
                    bet_stats['away_score']['wins'] += 1
                    payout = stake_per_bet * odds['away_score']
                    bet_stats['away_score']['total_return'] += payout
                    bet_stats['away_score']['winning_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'score': f"{goals_home}-{goals_away}",
                        'confidence': away_prob,
                        'payout': payout
                    })
                else:
                    bet_stats['away_score']['losing_bets'].append({
                        'match': f"{home_team} vs {away_team}",
                        'score': f"{goals_home}-{goals_away}",
                        'confidence': away_prob
                    })
        
        # Display comprehensive results
        total_stake = 0
        total_return = 0
        
        for bet_type, stats in bet_stats.items():
            print(f"🎯 {bet_type.replace('_', ' ').upper()}")
            print("-" * 40)
            
            if stats['bets'] > 0:
                win_rate = (stats['wins'] / stats['bets']) * 100
                net_profit = stats['total_return'] - stats['total_stake']
                roi = (net_profit / stats['total_stake']) * 100
                
                total_stake += stats['total_stake']
                total_return += stats['total_return']
                
                print(f"Total bets: {stats['bets']}")
                print(f"Wins: {stats['wins']} ({win_rate:.1f}%)")
                print(f"Losses: {stats['bets'] - stats['wins']}")
                print(f"Staked: {stats['total_stake']:.2f} units")
                print(f"Returns: {stats['total_return']:.2f} units")
                print(f"Profit/Loss: {net_profit:+.2f} units")
                print(f"ROI: {roi:+.2f}%")
                
                # Required win rate for break-even
                breakeven_rate = (1 / odds[bet_type]) * 100
                print(f"Break-even rate needed: {breakeven_rate:.1f}%")
                
                # Show some examples
                if len(stats['winning_bets']) > 0:
                    print(f"\nSample winning bets:")
                    for i, bet in enumerate(stats['winning_bets'][:3]):
                        if bet_type in ['over_5_5', 'over_6_5']:
                            print(f"  {bet['match']} - {bet['corners']} corners ({bet['confidence']:.1f}% conf) = +{bet['payout']-1:.2f} units")
                        else:
                            print(f"  {bet['match']} - {bet['score']} ({bet['confidence']:.1f}% conf) = +{bet['payout']-1:.2f} units")
                
                if len(stats['losing_bets']) > 0:
                    print(f"\nSample losing bets:")
                    for i, bet in enumerate(stats['losing_bets'][:3]):
                        if bet_type in ['over_5_5', 'over_6_5']:
                            print(f"  {bet['match']} - {bet['corners']} corners ({bet['confidence']:.1f}% conf) = -1.00 units")
                        else:
                            print(f"  {bet['match']} - {bet['score']} ({bet['confidence']:.1f}% conf) = -1.00 units")
                            
            else:
                print("No qualifying bets (no matches with ≥80% confidence)")
            
            print()
        
        # Overall summary
        total_profit = total_return - total_stake
        overall_roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
        
        print("🏆 OVERALL STRATEGY PERFORMANCE")
        print("=" * 50)
        print(f"Total bets placed: {sum(stats['bets'] for stats in bet_stats.values())}")
        print(f"Total stakes: {total_stake:.2f} units")
        print(f"Total returns: {total_return:.2f} units")
        print(f"Net profit/loss: {total_profit:+.2f} units")
        print(f"Overall ROI: {overall_roi:+.2f}%")
        print()
        
        if total_profit > 0:
            print("✅ STRATEGY IS PROFITABLE!")
            print(f"   You would have made {total_profit:.2f} units profit")
        elif total_profit == 0:
            print("⚖️  STRATEGY BREAKS EVEN")
        else:
            print("❌ STRATEGY IS UNPROFITABLE")
            print(f"   You would have lost {abs(total_profit):.2f} units")
            
        print(f"\nTo break even, you would need an overall {(total_stake/total_return)*100:.1f}% win rate across all bet types.")

if __name__ == "__main__":
    detailed_profitability_analysis()


