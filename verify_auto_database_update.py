#!/usr/bin/env python3
"""
Verify that the auto-database-update feature is working correctly.
This script checks a few records before and after loading the backtesting page.
"""

import requests
import time
import logging
from data.database import get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_values():
    """Check current database values for a few records."""
    db_manager = get_db_manager()
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, home_team_name, away_team_name, 
                   home_score_probability, away_score_probability
            FROM date_based_backtests 
            WHERE (home_team_name LIKE '%Beijing Guoan%' OR away_team_name LIKE '%Beijing Guoan%')
            AND home_score_probability IS NOT NULL 
            LIMIT 3
        """)
        
        records = []
        for row in cursor.fetchall():
            record = {
                'id': row[0],
                'match': f"{row[1]} vs {row[2]}",
                'home_prob': row[3],
                'away_prob': row[4]
            }
            records.append(record)
            logger.info(f"Record {record['id']}: {record['match']} - H={record['home_prob']}% A={record['away_prob']}%")
        
        return records

def trigger_backtesting_page():
    """Trigger the backtesting page to run live calculations and database updates."""
    try:
        logger.info("Triggering backtesting page to run auto-database-updates...")
        response = requests.get('http://localhost:5000/backtesting?season=2025', timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Backtesting page loaded successfully")
            return True
        else:
            logger.error(f"❌ Backtesting page failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to trigger backtesting page: {e}")
        return False

def main():
    """Verify the auto-database-update feature."""
    logger.info("🔍 VERIFICATION: Auto-Database-Update Feature")
    logger.info("=" * 50)
    
    # Step 1: Check current values
    logger.info("📊 BEFORE: Current database values")
    before_records = check_database_values()
    
    # Step 2: Trigger backtesting page (which should auto-update database)
    logger.info("\n🔄 TRIGGERING: Loading backtesting page...")
    success = trigger_backtesting_page()
    
    if not success:
        logger.error("❌ FAILED: Could not load backtesting page")
        return
    
    # Step 3: Wait a moment for updates to process
    logger.info("⏳ WAITING: 3 seconds for database updates to complete...")
    time.sleep(3)
    
    # Step 4: Check values after update
    logger.info("\n📊 AFTER: Database values after auto-update")
    after_records = check_database_values()
    
    # Step 5: Compare results
    logger.info("\n📈 COMPARISON: Before vs After")
    logger.info("-" * 50)
    
    changes_detected = 0
    for i, (before, after) in enumerate(zip(before_records, after_records)):
        if before['id'] == after['id']:
            home_changed = abs(before['home_prob'] - after['home_prob']) > 0.1
            away_changed = abs(before['away_prob'] - after['away_prob']) > 0.1
            
            if home_changed or away_changed:
                logger.info(f"🔄 CHANGED: {before['match']}")
                logger.info(f"   Before: H={before['home_prob']}% A={before['away_prob']}%")
                logger.info(f"   After:  H={after['home_prob']}% A={after['away_prob']}%")
                changes_detected += 1
            else:
                logger.info(f"⏸️  NO CHANGE: {before['match']} - H={after['home_prob']}% A={after['away_prob']}%")
    
    # Step 6: Final assessment
    logger.info(f"\n🎯 RESULT: {changes_detected} records updated")
    
    if changes_detected > 0:
        logger.info("✅ SUCCESS: Auto-database-update feature is working!")
        logger.info("   The database is being automatically updated with live-calculated values.")
    else:
        logger.info("🤔 NO CHANGES: Either values were already correct or feature needs debugging.")
        logger.info("   Check Flask logs for auto-update messages during backtesting page load.")

if __name__ == "__main__":
    main()
