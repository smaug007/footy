# 🎯 Cards Import - Target Leagues

**Date:** November 28, 2025  
**Scope:** Main European + MLS leagues with Bet365 cards betting coverage

---

## 📋 TARGET LEAGUES (7 Total)

| # | Country | League | DB ID | API ID | Status |
|---|---------|--------|-------|--------|--------|
| 1 | 🇪🇸 Spain | La Liga | 2 | 140 | ⏳ Pending |
| 2 | 🇮🇹 Italy | Serie A | 4 | 135 | ⏳ Pending |
| 3 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | Premier League | 747 | 39 | ⏳ Pending |
| 4 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | Championship | 748 | 40 | ⏳ Pending |
| 5 | 🇩🇪 Germany | Bundesliga | 754 | 78 | ⏳ Pending |
| 6 | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland | Scottish Premiership | 1267 | 179 | ⏳ Pending |
| 7 | 🇺🇸 USA | Major League Soccer | 1279 | 253 | ⏳ Pending |

---

## ❌ EXCLUDED LEAGUES

**Not importing cards for:**
- ❌ Champions League (not requested)
- ❌ Europa League (not requested)
- ❌ Lower English leagues (League One, League Two)
- ❌ 2. Bundesliga (second tier, not requested)
- ❌ Other European leagues (France, Netherlands, Portugal, etc.)
- ❌ Non-European leagues (Brazil, Argentina, Japan, China, etc.)

---

## 🚀 HOW TO IMPORT

### Quick Import (All 7 Leagues):
```bash
cd "C:\Users\tefac\Documents\android\cornerd2024"
python import_cards_target_leagues.py
```

### Expected Results:
- **Time:** ~5-10 minutes (depends on API rate limits)
- **Matches:** Estimated 2,000-3,000 matches across all 7 leagues
- **API Calls:** ~2,000-3,000 calls (within your 450/day limit? - will use cached data where possible)

---

## 📊 ESTIMATED MATCH COUNTS (2025 Season)

Based on your database:
- **La Liga:** ~380 matches (38 teams × 10 games each)
- **Serie A:** ~380 matches
- **Premier League:** ~380 matches  
- **Championship:** ~552 matches (larger league)
- **Bundesliga:** ~306 matches
- **Scottish Premiership:** ~198 matches
- **MLS:** ~510 matches (larger league, long season)

**Total:** ~2,700 matches (will only import FT matches without cards)

---

## ⚠️ IMPORTANT NOTES

1. **Season:** Importing for 2025 season only
2. **Status Filter:** Only FT (Finished) matches
3. **Skip Logic:** Matches with existing cards data are skipped
4. **API Rate Limits:** Script respects your 450 requests/day limit
5. **Red Card Counting:** Method A (Red = 1 card)

---

## 📝 AFTER IMPORT

Once import completes:
1. ✅ Cards predictions will appear in UI for these leagues
2. ✅ `/api/cards` endpoint will work for these leagues
3. ✅ Fixture cards display will show data for these leagues

---

## 🔍 VERIFY IMPORT

Check import status:
```bash
cd "C:\Users\tefac\Documents\android\cornerd2024"
python -c "import sqlite3; conn = sqlite3.connect('corners_prediction.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM matches WHERE yellow_cards_home > 0 OR yellow_cards_away > 0'); print(f'Matches with cards: {cursor.fetchone()[0]}'); conn.close()"
```

---

**Script:** `import_cards_target_leagues.py`  
**Cleanup:** Delete `check_target_leagues.py` after import


