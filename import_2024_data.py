#!/usr/bin/env python3
"""
Import 2024 season data for backtesting.
"""

import requests
import json
import time

def import_2024_data():
    """Import 2024 season data using the API endpoint."""
    print("🔄 Importing 2024 season data...")
    
    try:
        # Make sure the Flask app is running
        print("⏳ Starting import process...")
        
        response = requests.post('http://localhost:5000/api/import-data', 
                               json={'season': 2024, 'import_statistics': True},
                               headers={'Content-Type': 'application/json'},
                               timeout=300)  # 5 minute timeout
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print(f"📊 Response Text (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Successfully imported 2024 data:")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
                if 'data' in result:
                    data = result['data']
                    print(f"   Teams: {data.get('teams', 0)}")
                    print(f"   Matches: {data.get('matches', 0)}")
                    print(f"   Statistics: {data.get('statistics', 0)}")
                    print(f"   Errors: {data.get('errors', 0)}")
                print("\n🎉 2024 season data is now available for backtesting!")
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ Import failed (Status {response.status_code})")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Flask app. Please make sure:")
        print("   1. Flask app is running: python app.py")
        print("   2. App is accessible at http://localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Error: Import request timed out. The import might be taking longer than expected.")
        print("   This is normal for large datasets. Please check the Flask app logs.")
    except Exception as e:
        print(f"❌ Error importing data: {e}")

def check_app_running():
    """Check if Flask app is running."""
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        return True
    except:
        return False

if __name__ == "__main__":
    print("🏈 China Super League - 2024 Data Import")
    print("=" * 50)
    
    # Check if app is running
    if not check_app_running():
        print("❌ Flask app is not running!")
        print("Please start the Flask app first:")
        print("   python app.py")
        exit(1)
    
    print("✅ Flask app is running")
    import_2024_data()
