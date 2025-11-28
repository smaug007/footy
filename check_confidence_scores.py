#!/usr/bin/env python3
"""
Check where confidence scores are stored and verify data exists for all leagues.
"""
import sqlite3
import logging

def check_confidence_scores():
    """Check confidence score storage and data completeness."""
    
    print('🔍 CHECKING CONFIDENCE SCORE STORAGE...')
    print('=' * 60)
    
    conn = sqlite3.connect('corners_prediction.db')
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [t[0] for t in cursor.fetchall()]
        
        print('📋 ALL TABLES IN DATABASE:')
        table_counts = {}
        for table in all_tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            table_counts[table] = count
            print(f'  {table}: {count} records')
        
        print('\n' + '=' * 60)
        print('🎯 PREDICTION-RELATED TABLES:')
        
        # Look for prediction tables
        pred_tables = [t for t in all_tables if any(keyword in t.lower() for keyword in 
                      ['predict', 'confidence', 'backtest', 'analysis', 'result'])]
        
        if pred_tables:
            for table in pred_tables:
                print(f'  ✅ {table}: {table_counts[table]} records')
                
                # Show schema for prediction tables
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                confidence_cols = [col[1] for col in columns if 'confidence' in col[1].lower()]
                if confidence_cols:
                    print(f'    🎯 Confidence columns: {", ".join(confidence_cols)}')
        else:
            print('  ❌ No prediction-related tables found')
        
        print('\n' + '=' * 60)
        print('🏆 CHECKING SPECIFIC CONFIDENCE STORAGE...')
        
        # Check if matches have prediction data
        if 'matches' in table_counts:
            cursor.execute("""
                SELECT COUNT(*) as total_matches,
                       COUNT(CASE WHEN goals_home IS NOT NULL THEN 1 END) as matches_with_goals,
                       COUNT(CASE WHEN corners_home IS NOT NULL THEN 1 END) as matches_with_corners
                FROM matches
            """)
            match_stats = cursor.fetchone()
            print(f'📊 MATCH DATA COMPLETENESS:')
            print(f'  Total matches: {match_stats[0]}')
            print(f'  Matches with goals: {match_stats[1]}')
            print(f'  Matches with corners: {match_stats[2]}')
        
        # Check if enhanced_predictions exists and has data
        if 'enhanced_predictions' in table_counts:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN corner_confidence_5_5 IS NOT NULL THEN 1 END) as with_5_5,
                       COUNT(CASE WHEN corner_confidence_6_5 IS NOT NULL THEN 1 END) as with_6_5,
                       COUNT(CASE WHEN corner_confidence_7_5 IS NOT NULL THEN 1 END) as with_7_5
                FROM enhanced_predictions
            """)
            pred_stats = cursor.fetchone()
            print(f'\n🎯 ENHANCED PREDICTIONS CONFIDENCE SCORES:')
            print(f'  Total predictions: {pred_stats[0]}')
            print(f'  With 5.5 confidence: {pred_stats[1]}')
            print(f'  With 6.5 confidence: {pred_stats[2]}')
            print(f'  With 7.5 confidence: {pred_stats[3]}')
            
            if pred_stats[0] > 0:
                # Show sample data
                cursor.execute("""
                    SELECT corner_confidence_5_5, corner_confidence_6_5, corner_confidence_7_5,
                           predicted_total_corners
                    FROM enhanced_predictions 
                    WHERE corner_confidence_5_5 IS NOT NULL
                    LIMIT 5
                """)
                samples = cursor.fetchall()
                print(f'\n📋 SAMPLE CONFIDENCE SCORES:')
                print('  5.5 | 6.5 | 7.5 | Total')
                print('  ----|----|----|---------')
                for sample in samples:
                    print(f'  {sample[0]:3.0f}%|{sample[1]:3.0f}%|{sample[2]:3.0f}%| {sample[3]:4.1f}')
        
        # Check if date_based_backtests exists
        if 'date_based_backtests' in table_counts:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN confidence_5_5 IS NOT NULL THEN 1 END) as with_conf
                FROM date_based_backtests
            """)
            backtest_stats = cursor.fetchone()
            print(f'\n🎯 BACKTEST CONFIDENCE SCORES:')
            print(f'  Total backtests: {backtest_stats[0]}')
            print(f'  With confidence scores: {backtest_stats[1]}')
        
        # Check for league coverage
        print('\n' + '=' * 60)
        print('🏆 CONFIDENCE SCORE COVERAGE BY LEAGUE:')
        
        if 'enhanced_predictions' in table_counts and table_counts['enhanced_predictions'] > 0:
            cursor.execute("""
                SELECT l.name, l.country, COUNT(ep.id) as predictions_count
                FROM leagues l
                LEFT JOIN matches m ON l.id = m.league_id
                LEFT JOIN enhanced_predictions ep ON m.id = ep.match_id
                WHERE l.is_active = 1 OR l.is_active IS NULL
                GROUP BY l.id, l.name, l.country
                ORDER BY predictions_count DESC, l.name
            """)
            league_coverage = cursor.fetchall()
            
            print('League (Country) | Predictions')
            print('-' * 45)
            total_predictions = 0
            leagues_with_predictions = 0
            
            for name, country, pred_count in league_coverage:
                status = '✅' if pred_count > 0 else '❌'
                print(f'{status} {name} ({country}) | {pred_count}')
                total_predictions += pred_count
                if pred_count > 0:
                    leagues_with_predictions += 1
            
            print(f'\n📊 SUMMARY:')
            print(f'  Leagues with predictions: {leagues_with_predictions}/{len(league_coverage)}')
            print(f'  Total predictions stored: {total_predictions}')
        
        else:
            print('❌ No enhanced_predictions table or data found')
        
    except Exception as e:
        print(f'❌ Error checking confidence scores: {e}')
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_confidence_scores()





