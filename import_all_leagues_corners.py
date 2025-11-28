#!/usr/bin/env python3
"""
Import Corner Statistics for ALL Leagues - Extended from successful MLS approach
Uses /fixtures/statistics endpoint to get corner data stored in matches table
"""
import logging
import time
from data.data_importer import DataImporter
from data.league_manager import get_league_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_all_leagues_corners():
    """Import corner statistics for all active leagues using proven MLS method."""
    try:
        logger.info("🚀 IMPORTING CORNER STATISTICS FOR ALL LEAGUES")
        logger.info("🏈 Using proven MLS approach with /fixtures/statistics endpoint")
        logger.info("📊 Corner data stored in matches table (corners_home, corners_away)")
        
        # Initialize services
        importer = DataImporter()
        league_manager = get_league_manager()
        
        # Get all active leagues
        all_leagues = league_manager.get_active_leagues()
        logger.info(f"📈 Processing corner statistics for {len(all_leagues)} leagues")
        
        successful_leagues = []
        failed_leagues = []
        total_corners_imported = 0
        total_api_calls = 0
        current_season = 2025
        
        for i, league in enumerate(all_leagues, 1):
            try:
                logger.info(f"\n📍 [{i}/{len(all_leagues)}] {league.country}: {league.name}")
                logger.info("-" * 50)
                
                # Import corner statistics using the proven method
                # This uses /fixtures/statistics endpoint and stores in matches table
                corners_imported = importer.import_match_statistics(
                    league.id, 
                    current_season, 
                    limit=100  # Process up to 100 matches per league
                )
                
                api_calls_used = corners_imported  # 1 API call per match
                total_api_calls += api_calls_used
                total_corners_imported += corners_imported
                
                if corners_imported > 0:
                    logger.info(f"  ✅ Corner stats imported: {corners_imported} matches")
                    successful_leagues.append({
                        'country': league.country,
                        'name': league.name,
                        'corners': corners_imported,
                        'api_calls': api_calls_used
                    })
                else:
                    logger.warning(f"  ⚠️ No corner statistics available for {league.name}")
                    failed_leagues.append(f"{league.country} - {league.name} (No data)")
                
                # Rate limiting every 50 API calls
                if total_api_calls > 0 and total_api_calls % 50 == 0:
                    logger.info(f"⏳ API checkpoint: {total_api_calls} calls, pausing 11 seconds...")
                    time.sleep(11)
                    
            except Exception as e:
                logger.error(f"❌ Failed: {league.country} - {league.name}: {e}")
                failed_leagues.append(f"{league.country} - {league.name} (Error: {str(e)[:50]})")
                continue
                
        # Final comprehensive summary
        logger.info(f"\n🏆 CORNER STATISTICS IMPORT RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Successful leagues: {len(successful_leagues)}")
        logger.info(f"❌ Failed leagues: {len(failed_leagues)}")
        logger.info(f"🏈 Total corner stats imported: {total_corners_imported}")
        logger.info(f"🔌 Total API calls used: {total_api_calls}")
        
        if successful_leagues:
            logger.info(f"\n✅ Successfully imported corner statistics:")
            by_country = {}
            for league in successful_leagues:
                country = league['country']
                if country not in by_country:
                    by_country[country] = []
                by_country[country].append(league)
                
            for country, leagues in sorted(by_country.items()):
                country_corners = sum(l['corners'] for l in leagues)
                logger.info(f"  🇪🇺 {country}: {len(leagues)} leagues, {country_corners} matches with corners")
                for league in leagues:
                    logger.info(f"    - {league['name']}: {league['corners']} matches")
        
        if failed_leagues:
            logger.info(f"\n❌ Failed leagues:")
            for failure in failed_leagues:
                logger.info(f"  - {failure}")
                
        success_rate = len(successful_leagues) / len(all_leagues) * 100 if all_leagues else 0
        logger.info(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 70:
            logger.info("🎉 EXCELLENT! Corner import highly successful!")
        elif success_rate >= 50:
            logger.info("✅ GOOD! Corner import mostly successful!")
        else:
            logger.warning("⚠️ Corner import had significant issues")
            
        return success_rate >= 50
        
    except Exception as e:
        logger.error(f"💥 Global corner import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_all_leagues_corners()
    if success:
        logger.info("🏆 GLOBAL CORNER STATISTICS IMPORT COMPLETED!")
        logger.info("🏈 All leagues now have corner data for predictions!")
    else:
        logger.error("🚨 Global corner import needs attention")
