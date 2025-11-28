#!/usr/bin/env python3
"""
Detailed analysis of confidence score storage across all prediction tables.
"""
import sqlite3

def detailed_confidence_analysis():
    """Detailed analysis of confidence score storage."""
    
    print('🎯 DETAILED CONFIDENCE SCORE ANALYSIS')
    print('=' * 60)
    
    conn = sqlite3.connect('corners_prediction.db')
    cursor = conn.cursor()
    
    try:
        # 1. Check regular predictions table
        print('📊 1. PREDICTIONS TABLE ANALYSIS:')
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN confidence_5_5 IS NOT NULL THEN 1 END) as with_5_5,
                   COUNT(CASE WHEN confidence_6_5 IS NOT NULL THEN 1 END) as with_6_5,
                   MIN(confidence_5_5) as min_5_5,
                   MAX(confidence_5_5) as max_5_5,
                   AVG(confidence_5_5) as avg_5_5
            FROM predictions
        """)
        pred_stats = cursor.fetchone()
        print(f'  Total predictions: {pred_stats[0]}')
        print(f'  With 5.5 confidence: {pred_stats[1]}')
        print(f'  With 6.5 confidence: {pred_stats[2]}')
        if pred_stats[1] > 0:
            print(f'  5.5 Confidence range: {pred_stats[3]:.1f}% - {pred_stats[4]:.1f}% (avg: {pred_stats[5]:.1f}%)')
        
        # Check league coverage in predictions table
        cursor.execute("""
            SELECT l.name, l.country, COUNT(p.id) as predictions_count
            FROM leagues l
            LEFT JOIN matches m ON l.id = m.league_id  
            LEFT JOIN predictions p ON m.id = p.match_id
            WHERE (l.is_active = 1 OR l.is_active IS NULL)
            GROUP BY l.id, l.name, l.country
            HAVING predictions_count > 0
            ORDER BY predictions_count DESC
        """)
        pred_coverage = cursor.fetchall()
        print(f'\n  📋 Leagues with predictions in main table:')
        for name, country, count in pred_coverage[:10]:  # Top 10
            print(f'    ✅ {name} ({country}): {count} predictions')
        
        print('\n' + '=' * 60)
        
        # 2. Check date_based_backtests table  
        print('📊 2. DATE_BASED_BACKTESTS TABLE ANALYSIS:')
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN confidence_5_5 IS NOT NULL THEN 1 END) as with_5_5,
                   COUNT(CASE WHEN confidence_6_5 IS NOT NULL THEN 1 END) as with_6_5,
                   MIN(confidence_5_5) as min_5_5,
                   MAX(confidence_5_5) as max_5_5,
                   AVG(confidence_5_5) as avg_5_5
            FROM date_based_backtests
        """)
        backtest_stats = cursor.fetchone()
        print(f'  Total backtests: {backtest_stats[0]}')
        print(f'  With 5.5 confidence: {backtest_stats[1]}')
        print(f'  With 6.5 confidence: {backtest_stats[2]}')
        if backtest_stats[1] > 0:
            print(f'  5.5 Confidence range: {backtest_stats[3]:.1f}% - {backtest_stats[4]:.1f}% (avg: {backtest_stats[5]:.1f}%)')
        
        # Check backtest league coverage
        cursor.execute("""
            SELECT l.name, l.country, COUNT(dbb.id) as backtest_count
            FROM date_based_backtests dbb
            JOIN teams ht ON dbb.home_team_id = ht.id
            JOIN teams at ON dbb.away_team_id = at.id  
            JOIN leagues l ON ht.league_id = l.id
            WHERE (l.is_active = 1 OR l.is_active IS NULL)
            GROUP BY l.id, l.name, l.country
            ORDER BY backtest_count DESC
        """)
        backtest_coverage = cursor.fetchall()
        print(f'\n  📋 Leagues with backtests:')
        for name, country, count in backtest_coverage:
            print(f'    ✅ {name} ({country}): {count} backtests')
        
        print('\n' + '=' * 60)
        
        # 3. Sample actual confidence scores
        print('📊 3. SAMPLE CONFIDENCE SCORES:')
        cursor.execute("""
            SELECT p.confidence_5_5, p.confidence_6_5, p.predicted_total_corners,
                   ht.name as home_team, at.name as away_team
            FROM predictions p
            JOIN matches m ON p.match_id = m.id
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE p.confidence_5_5 IS NOT NULL
            ORDER BY p.created_at DESC
            LIMIT 10
        """)
        sample_predictions = cursor.fetchall()
        
        if sample_predictions:
            print('  Recent predictions with confidence scores:')
            print('  5.5% | 6.5% | Total | Match')
            print('  -----|------|-------|----------------------------------')
            for conf_5_5, conf_6_5, total, home, away in sample_predictions:
                print(f'  {conf_5_5:4.0f}%|{conf_6_5:4.0f}%|{total:5.1f} | {home} vs {away}')
        else:
            print('  ❌ No predictions with confidence scores found')
        
        print('\n' + '=' * 60)
        
        # 4. Check what's happening in app predictions
        print('📊 4. RECENT PREDICTION ACTIVITY:')
        cursor.execute("""
            SELECT DATE(p.created_at) as pred_date, COUNT(*) as predictions_made
            FROM predictions p
            GROUP BY DATE(p.created_at)
            ORDER BY pred_date DESC
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        if recent_activity:
            print('  Recent prediction dates:')
            for date, count in recent_activity:
                print(f'    {date}: {count} predictions')
        else:
            print('  ❌ No recent prediction activity found')
        
        print('\n' + '=' * 60)
        
        # 5. Overall summary
        print('📊 5. OVERALL CONFIDENCE SCORE SUMMARY:')
        
        total_with_confidence = pred_stats[1] + backtest_stats[1]
        active_leagues = 37  # From previous query
        
        print(f'  ✅ Total confidence scores available: {total_with_confidence}')
        print(f'    - Main predictions table: {pred_stats[1]}')  
        print(f'    - Backtest table: {backtest_stats[1]}')
        print(f'  📊 Active leagues: {active_leagues}')
        print(f'  📈 Leagues with prediction data: {len(pred_coverage)} + {len(backtest_coverage)} (backtest)')
        
        if total_with_confidence > 0:
            print(f'  ✅ Status: CONFIDENCE SCORES EXIST')
        else:
            print(f'  ❌ Status: NO CONFIDENCE SCORES FOUND')
    
    except Exception as e:
        print(f'❌ Error in detailed analysis: {e}')
    
    finally:
        conn.close()

if __name__ == "__main__":
    detailed_confidence_analysis()





