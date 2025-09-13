#!/usr/bin/env python3
"""
Quick start script for China Super League Corner Prediction System.
Complete setup and launch in one go.
"""

import sys
import subprocess
import time
from pathlib import Path

def quick_start(season_year=2025):
    """Complete setup and launch process."""
    print("🏈 China Super League Corner Prediction System - Quick Start")
    print("=" * 70)
    
    try:
        # Step 1: Setup season data
        print(f"🔄 STEP 1: Setting up season {season_year} data...")
        print("-" * 50)
        
        result = subprocess.run([
            sys.executable, 'setup_season.py', str(season_year)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Season setup completed successfully!")
            print(result.stdout.split('\n')[-10:])  # Show last few lines
        else:
            print("❌ Season setup failed:")
            print(result.stderr)
            return False
        
        print("\n" + "=" * 70)
        print("🚀 STEP 2: Starting the prediction system...")
        print("=" * 70)
        
        print("✅ Database initialized with season data")
        print("✅ Teams and matches imported")
        print("✅ Corner statistics available")
        print("✅ System ready for predictions!")
        print()
        print("🌐 Starting Flask web application...")
        print("📱 Access the system at: http://localhost:5000")
        print()
        print("🎯 You can now:")
        print("   • Select teams from the dropdown menus")
        print("   • Generate corner predictions")
        print("   • View prediction history")
        print("   • Monitor accuracy dashboard")
        print()
        print("⏹️  Press Ctrl+C to stop the server")
        print("=" * 70)
        
        # Step 2: Start Flask app
        subprocess.run([sys.executable, 'app.py'])
        
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick start CSL prediction system')
    parser.add_argument('--season', type=int, default=2025, 
                       help='Season year (default: 2025)')
    
    args = parser.parse_args()
    
    success = quick_start(args.season)
    sys.exit(0 if success else 1)
