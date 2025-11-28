#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('corners_prediction.db')
cursor = conn.cursor()

# Check matches table structure
cursor.execute('PRAGMA table_info(matches)')
columns = cursor.fetchall()

print("\nMATCHES TABLE STRUCTURE:")
print("="*60)

cards_cols = []
for col in columns:
    col_name = col[1]
    col_type = col[2]
    if 'card' in col_name.lower():
        cards_cols.append((col_name, col_type))
        print(f"  [YES] {col_name:<30} {col_type}")

if not cards_cols:
    print("  [NO] NO CARDS COLUMNS FOUND!")
    print("\nExisting columns:")
    for col in columns:
        print(f"     {col[1]:<30} {col[2]}")

# Check if matches have cards data
if cards_cols:
    cursor.execute("SELECT COUNT(*) FROM matches WHERE yellow_cards_home IS NOT NULL")
    matches_with_cards = cursor.fetchone()[0]
    print(f"\nMatches with cards data: {matches_with_cards}")

conn.close()

