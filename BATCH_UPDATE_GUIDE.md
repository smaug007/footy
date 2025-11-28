# 📅 League Data Batch Update Guide

## Overview
Two-script system to update completed match statistics (goals + corners) for all 52 leagues.
Data is ~2 weeks stale since last import (August 30th).

## 📦 Batch Scripts

### **Batch 1: European Leagues** (`update_leagues_batch_1.py`)
- **Coverage**: 37 European leagues
- **API Calls**: ~925 calls (well under 7500 limit)
- **Duration**: 15-30 minutes
- **Recommended Day**: Tuesday
- **Leagues**: La Liga, Serie A, Premier League, Bundesliga, Ligue 1, etc.

### **Batch 2: Americas + Asia** (`update_leagues_batch_2.py`)
- **Coverage**: 15 Americas + Asia leagues  
- **API Calls**: ~375 calls (very light load)
- **Duration**: 10-20 minutes
- **Recommended Day**: Wednesday
- **Leagues**: MLS, Liga MX, Brazilian Serie A, J1 League, K League 1, CSL, etc.

## 🚀 Usage Instructions

### **Step 1: Tuesday - Run Batch 1**
```bash
# Windows (recommended):
python update_leagues_batch_1_windows.py

# Linux/Mac (if emojis work):
python update_leagues_batch_1.py
```
- Updates all European leagues
- Creates detailed log file: `batch1_update_YYYYMMDD_HHMMSS.log`
- Safe to interrupt with Ctrl+C if needed

### **Step 2: Wednesday - Run Batch 2**  
```bash
# Windows (recommended):
python update_leagues_batch_2_windows.py

# Linux/Mac (if emojis work):
python update_leagues_batch_2.py
```
- Updates Americas + Asia leagues
- Creates detailed log file: `batch2_update_YYYYMMDD_HHMMSS.log`
- Completes the full global update

## ✅ What Each Script Does

1. **Identifies leagues** in the geographic region
2. **🔧 CRITICAL: Updates match statuses** from API (NS→FT, etc.)
3. **Finds completed matches** missing statistics (now with correct statuses)
4. **Fetches match details** from API-Football
5. **Updates database** with goals and corners data
6. **Rate limiting**: 11-second pause every 50 API calls
7. **Progress tracking**: Detailed logging of all operations
8. **Error handling**: Continues processing if individual matches fail

### 🎯 Critical Fixes Applied
- **Status Update Fix**: Games imported as "NS" in August now properly detected as completed
- **Solution**: Each league gets status refresh from API before statistics import
- **Impact**: Finds all matches that changed from "Not Started" to "Finished"
- **Data Structure Fix**: Corrected database ID access for different return types
  - Goals method returns `List[Tuple]` → Use `match[1]` for database ID
  - Corners method returns `List[Dict]` → Use `match['id']` for database ID
- **SQL Query Fix**: Corrected column names and added proper JOINs
  - Fixed `api_match_id` → `api_fixture_id`
  - Fixed `home_team` → JOIN with teams table
- **API Response Structure Fix**: Corrected data extraction from API responses
  - Fixed goals: `fixture_data.get('goals', {}).get('home')` → `fixture_data.get('home_goals')`
  - Fixed corners: `raw_data['response'][0]['statistics']` → `raw_data['statistics']` (direct path)
- **Windows Compatibility**: Created emoji-free versions for Windows Command Prompt
- **Unicode Encoding Fix**: Special characters in team names (Polish ę, Ł, etc.) converted to ASCII-safe display
- **Method Signature Fix**: Corrected parameter order differences between methods

## 📊 Expected Results

**Batch 1 (European)**:
- ~37 leagues processed
- Match statuses updated (NS→FT conversions)
- ~200-500 matches updated per league (varies by league)
- Both goals and corners statistics updated
- Complete log of all operations

**Batch 2 (Americas + Asia)**:
- ~15 leagues processed
- Match statuses updated (NS→FT conversions)
- ~100-300 matches updated per league (varies by league)
- Both goals and corners statistics updated
- Lighter API usage

## 🔧 Features

- **Resume Capability**: Can restart if interrupted
- **Comprehensive Logging**: Every operation logged to file + console
- **API Efficiency**: Only fetches needed data, respects rate limits
- **Error Recovery**: Continues processing other leagues if one fails
- **Progress Tracking**: Real-time updates on leagues/matches processed
- **Safety Confirmations**: Requires user confirmation before starting

## 📝 Log Files

Each run creates a timestamped log file with:
- Start/end times and duration
- Leagues processed and match counts
- API calls used vs daily limit
- Any errors encountered
- Final success/failure summary

## 🎯 Timing Recommendation

**Tuesday/Wednesday is optimal because:**
- European competitions (Champions League, etc.) play Tuesday/Wednesday
- Gives time for API data to settle after matches
- Spreads API usage across 2 days for safety
- Wednesday catches any late-updating results

## ⚠️ Notes

- **API Limit**: 7500 calls/day (both batches well under limit)
- **Data Scope**: Only updates completed matches (not fixtures)
- **Overwrites**: Updates existing data to ensure accuracy
- **Safe to Run**: Won't create duplicates or break existing data
- **Interruptible**: Can stop with Ctrl+C and resume later

## 🚀 PRODUCTION READY STATUS

**✅ Batch 1 (European)**: `update_leagues_batch_1_windows.py`
- **37 European leagues** across 19 countries (England, Germany, Spain, Italy, France, etc.)
- **~925 API calls estimated** 
- **All fixes applied and tested** ✅

**✅ Batch 2 (Americas + Asia)**: `update_leagues_batch_2_windows.py`  
- **15 Americas + Asia leagues** across 13 countries (USA, Mexico, Brazil, China, Japan, etc.)
- **~375 API calls estimated**
- **All fixes applied and tested** ✅

Both scripts have been **thoroughly tested** and are ready for production use.

## 🎉 Expected Outcome

After running both batches, all 52 leagues will have:
- ✅ Up-to-date completed match results
- ✅ Current goal statistics for all finished games
- ✅ Current corner statistics for all finished games  
- ✅ Ready for accurate predictions on new fixtures
