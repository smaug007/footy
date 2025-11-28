"""
LEAGUE MANAGEMENT SOLUTIONS
==========================

Two approaches for handling inactive leagues:
1. HIDING/SOFT DELETE (Recommended)
2. COMPLETE REMOVAL

Choose based on your data strategy preferences.
"""

import sqlite3
from datetime import datetime, timedelta

class LeagueManager:
    def __init__(self, db_path='corners_prediction.db'):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)

    # =========================================================================
    # OPTION 1: HIDING/SOFT DELETE APPROACH (RECOMMENDED)
    # =========================================================================
    
    def add_is_active_column(self):
        """Add is_active column to leagues table (defaults to True)"""
        with self.get_connection() as conn:
            try:
                conn.execute('ALTER TABLE leagues ADD COLUMN is_active BOOLEAN DEFAULT 1')
                conn.commit()
                print("✅ Added 'is_active' column to leagues table")
                return True
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("ℹ️  Column 'is_active' already exists")
                    return True
                else:
                    print(f"❌ Error: {e}")
                    return False
    
    def hide_leagues(self, league_names):
        """Hide specific leagues (soft delete)"""
        if not isinstance(league_names, list):
            league_names = [league_names]
        
        with self.get_connection() as conn:
            hidden_count = 0
            for league_name in league_names:
                cursor = conn.execute(
                    'UPDATE leagues SET is_active = 0 WHERE name = ?',
                    (league_name,)
                )
                if cursor.rowcount > 0:
                    hidden_count += 1
                    print(f"👁️‍🗨️ Hidden: {league_name}")
                else:
                    print(f"❌ Not found: {league_name}")
            
            conn.commit()
            print(f"✅ Hidden {hidden_count}/{len(league_names)} leagues")
            return hidden_count
    
    def show_leagues(self, league_names):
        """Reactivate hidden leagues"""
        if not isinstance(league_names, list):
            league_names = [league_names]
        
        with self.get_connection() as conn:
            shown_count = 0
            for league_name in league_names:
                cursor = conn.execute(
                    'UPDATE leagues SET is_active = 1 WHERE name = ?',
                    (league_name,)
                )
                if cursor.rowcount > 0:
                    shown_count += 1
                    print(f"👁️ Reactivated: {league_name}")
                else:
                    print(f"❌ Not found: {league_name}")
            
            conn.commit()
            print(f"✅ Reactivated {shown_count}/{len(league_names)} leagues")
            return shown_count
    
    def get_active_leagues(self):
        """Get only active leagues"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, name, country 
                FROM leagues 
                WHERE is_active = 1 OR is_active IS NULL
                ORDER BY name
            ''')
            return cursor.fetchall()
    
    def get_hidden_leagues(self):
        """Get only hidden leagues"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, name, country 
                FROM leagues 
                WHERE is_active = 0
                ORDER BY name
            ''')
            return cursor.fetchall()

    # =========================================================================
    # OPTION 2: COMPLETE REMOVAL APPROACH (DANGEROUS)
    # =========================================================================
    
    def remove_leagues_completely(self, league_names, confirm_deletion=False):
        """
        PERMANENTLY DELETE leagues and ALL associated data
        ⚠️ WARNING: This cannot be undone!
        """
        if not confirm_deletion:
            print("❌ SAFETY BLOCK: Set confirm_deletion=True to proceed")
            print("⚠️  This will PERMANENTLY delete all data for these leagues:")
            for name in league_names:
                print(f"   - {name}")
            return False
        
        if not isinstance(league_names, list):
            league_names = [league_names]
        
        with self.get_connection() as conn:
            removed_count = 0
            
            for league_name in league_names:
                # Get league ID first
                cursor = conn.execute('SELECT id FROM leagues WHERE name = ?', (league_name,))
                league_data = cursor.fetchone()
                
                if not league_data:
                    print(f"❌ League not found: {league_name}")
                    continue
                
                league_id = league_data[0]
                
                try:
                    # Count what we're about to delete
                    cursor = conn.execute('SELECT COUNT(*) FROM matches WHERE league_id = ?', (league_id,))
                    match_count = cursor.fetchone()[0]
                    
                    # Delete in order (due to foreign key constraints)
                    conn.execute('DELETE FROM match_statistics WHERE match_id IN (SELECT id FROM matches WHERE league_id = ?)', (league_id,))
                    conn.execute('DELETE FROM matches WHERE league_id = ?', (league_id,))
                    conn.execute('DELETE FROM teams WHERE league_id = ?', (league_id,))
                    conn.execute('DELETE FROM leagues WHERE id = ?', (league_id,))
                    
                    removed_count += 1
                    print(f"💥 PERMANENTLY DELETED: {league_name} ({match_count} matches)")
                    
                except Exception as e:
                    print(f"❌ Error deleting {league_name}: {e}")
                    conn.rollback()
                    return False
            
            conn.commit()
            print(f"💥 PERMANENTLY DELETED {removed_count}/{len(league_names)} leagues")
            return removed_count

    # =========================================================================
    # UTILITY FUNCTIONS
    # =========================================================================
    
    def analyze_league_activity(self, days_inactive=180):
        """Find leagues with no recent activity"""
        cutoff_date = (datetime.now() - timedelta(days=days_inactive)).strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT l.name, l.country, COUNT(m.id) as match_count,
                       MAX(m.match_date) as last_match
                FROM leagues l
                LEFT JOIN matches m ON l.id = m.league_id
                GROUP BY l.id, l.name, l.country
                HAVING last_match < ? OR last_match IS NULL
                ORDER BY last_match DESC
            ''', (cutoff_date,))
            
            inactive = cursor.fetchall()
            
            print(f"🔍 LEAGUES INACTIVE FOR {days_inactive}+ DAYS:")
            print("League (Country) | Matches | Last Match")
            print("-" * 60)
            
            candidates = []
            for name, country, matches, last_match in inactive:
                print(f"{name} ({country}) | {matches} | {last_match or 'Never'}")
                candidates.append(name)
            
            print(f"\n📊 Found {len(candidates)} inactive leagues")
            return candidates
    
    def get_league_stats(self):
        """Show current league statistics"""
        with self.get_connection() as conn:
            # Check if is_active column exists
            cursor = conn.execute("PRAGMA table_info(leagues)")
            columns = [col[1] for col in cursor.fetchall()]
            has_active_column = 'is_active' in columns
            
            if has_active_column:
                cursor = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN is_active = 1 OR is_active IS NULL THEN 'Active'
                            ELSE 'Hidden'
                        END as status,
                        COUNT(*) as count
                    FROM leagues
                    GROUP BY is_active
                    ORDER BY count DESC
                ''')
                stats = cursor.fetchall()
                
                print("📊 LEAGUE STATUS BREAKDOWN:")
                for status, count in stats:
                    print(f"  {status}: {count} leagues")
            else:
                cursor = conn.execute('SELECT COUNT(*) FROM leagues')
                total = cursor.fetchone()[0]
                print(f"📊 TOTAL LEAGUES: {total} (no hiding system implemented)")


# =========================================================================
# EXAMPLE USAGE
# =========================================================================

def main():
    manager = LeagueManager()
    
    print("🏆 LEAGUE MANAGEMENT SYSTEM")
    print("=" * 50)
    
    # Show current stats
    manager.get_league_stats()
    
    print("\n" + "=" * 50)
    print("CHOOSE YOUR APPROACH:")
    print("1. Type 'hide' for soft delete approach")
    print("2. Type 'remove' for complete removal")
    print("3. Type 'analyze' to see inactive leagues")
    
    choice = input("\nEnter choice: ").lower().strip()
    
    if choice == 'analyze':
        candidates = manager.analyze_league_activity(days_inactive=180)
        
        if candidates:
            print(f"\n💡 RECOMMENDATION: Hide these {len(candidates)} leagues")
            print("They can be reactivated later if bookies return")
    
    elif choice == 'hide':
        # OPTION 1: Implement hiding system
        print("\n🛡️ IMPLEMENTING HIDING SYSTEM...")
        
        if manager.add_is_active_column():
            print("✅ Ready for league hiding!")
            print("Example usage:")
            print("  manager.hide_leagues(['League Name 1', 'League Name 2'])")
            print("  manager.show_leagues(['League Name 1'])  # Reactivate")
    
    elif choice == 'remove':
        # OPTION 2: Complete removal (with warnings)
        print("\n💥 COMPLETE REMOVAL APPROACH")
        print("⚠️  WARNING: This is permanent and cannot be undone!")
        print("⚠️  All matches, teams, and statistics will be lost!")
        print("⚠️  Consider hiding instead!")
        
        confirm = input("Type 'I UNDERSTAND THE RISKS' to continue: ")
        if confirm == "I UNDERSTAND THE RISKS":
            print("💥 Removal system ready (use with extreme caution)")
        else:
            print("✅ Wise choice! Consider hiding instead.")

if __name__ == "__main__":
    main()





