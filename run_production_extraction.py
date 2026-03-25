#!/usr/bin/env python3
"""
Production Extraction Runner
Menjalankan extractor system untuk scraping data dari berbagai sumber.
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/aseps/logs/extractor/extraction.log')
    ]
)
logger = logging.getLogger('ProductionExtraction')

# Add mcp-unified to path
sys.path.insert(0, '/home/aseps/MCP/mcp-unified')
sys.path.insert(0, '/home/aseps/MCP/mcp-unified/integrations/agentic_ai')

async def run_extraction(save_to_db: bool = True, test_mode: bool = False):
    """
    Run extraction for all configured extractors.
    
    Args:
        save_to_db: Save results to database
        test_mode: Run in test mode (limited items)
    """
    logger.info("=" * 60)
    logger.info(f"Starting Production Extraction - {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # Import extractor components
        from extractors.jdih_extractor import JDIHExtractor
        from extractors.peraturan_bpk_extractor import PeraturanBPKExtractor
        from extractors.kemenkeu_extractor import KemenkeuExtractor
        from extractors.setneg_extractor import SetnegExtractor
        from extractors.kemenkumham_extractor import KemenkumhamExtractor
        from extractors.kemenpan_extractor import KemenpanExtractor
        from extractors.ojk_extractor import OJKExtractor
        from extractors.kominfo_extractor import KominfoExtractor
        from extractors.hukumonline_extractor import HukumonlineExtractor
        from extractors.detik_extractor import DetikExtractor
        from extractors.perplexity_extractor import PerplexityExtractor
        from extractors.news_extractor import NewsExtractor
        from extractors.generic_extractor import GenericExtractor
        
        # Initialize all extractors
        extractors = [
            JDIHExtractor(),
            PeraturanBPKExtractor(),
            KemenkeuExtractor(),
            SetnegExtractor(),
            KemenkumhamExtractor(),
            KemenpanExtractor(),
            OJKExtractor(),
            KominfoExtractor(),
            HukumonlineExtractor(),
            DetikExtractor(),
            PerplexityExtractor(),
            NewsExtractor(),
            GenericExtractor(),
        ]
        
        logger.info(f"Loaded {len(extractors)} extractors")
        
        # Track results
        total_extracted = 0
        successful_extractors = 0
        failed_extractors = 0
        
        # Run each extractor
        for extractor in extractors:
            try:
                logger.info(f"\n🔍 Running extractor: {extractor.name}")
                logger.info(f"   URL: {extractor.base_url}")
                
                # Run extraction (async)
                # Note: This is a simplified version - actual implementation
                # would use Playwright browser automation
                items = await extractor.extract_with_browser()
                
                if items:
                    total_extracted += len(items)
                    successful_extractors += 1
                    logger.info(f"   ✅ Success: {len(items)} items extracted")
                    
                    # Save to database if requested
                    if save_to_db and hasattr(extractor, 'save_to_knowledge_base'):
                        await extractor.save_to_knowledge_base(items)
                        logger.info(f"   💾 Saved to knowledge base")
                else:
                    logger.warning(f"   ⚠️ No items extracted")
                    
                # In test mode, only run one extractor
                if test_mode:
                    logger.info("Test mode: Stopping after first extractor")
                    break
                    
            except Exception as e:
                failed_extractors += 1
                logger.error(f"   ❌ Failed: {str(e)}")
                continue
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total items extracted: {total_extracted}")
        logger.info(f"Successful extractors: {successful_extractors}")
        logger.info(f"Failed extractors: {failed_extractors}")
        logger.info(f"Completed at: {datetime.now()}")
        logger.info("=" * 60)
        
        return total_extracted > 0
        
    except Exception as e:
        logger.error(f"Critical error in extraction: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run production extraction for all configured extractors'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all extractors (default)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to knowledge base'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (single extractor)'
    )
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    log_dir = Path('/home/aseps/logs/extractor')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Run extraction
    success = asyncio.run(run_extraction(
        save_to_db=args.save,
        test_mode=args.test
    ))
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
