#!/usr/bin/env python3
"""
Production Extraction Script

Real website extraction dengan auto-save ke Knowledge Base.
Usage: python3 run_production_extraction.py --source hukumonline --save
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "mcp-unified" / "integrations" / "agentic_ai"))
sys.path.insert(0, str(Path(__file__).parent / "mcp-unified"))

from playwright.async_api import async_playwright
from extractors import HukumonlineExtractor, JDIHExtractor
from knowledge_bridge_integration import ExtractorKnowledgeBridge
from extractor_registry import get_registry


# Configuration
SOURCES = {
    "hukumonline": {
        "url": "https://www.hukumonline.com/berita",
        "extractor": HukumonlineExtractor,
        "name": "hukumonline"
    },
    "jdih": {
        "url": "https://jdihn.go.id",
        "extractor": JDIHExtractor,
        "name": "jdih"
    }
}


async def extract_from_source(source_key: str, save_to_kb: bool = False):
    """
    Extract data dari source tertentu.
    
    Args:
        source_key: Key dari SOURCES dict
        save_to_kb: Save ke knowledge base?
    """
    if source_key not in SOURCES:
        print(f"❌ Unknown source: {source_key}")
        print(f"Available: {', '.join(SOURCES.keys())}")
        return None
    
    config = SOURCES[source_key]
    url = config["url"]
    extractor_class = config["extractor"]
    source_name = config["name"]
    
    print("\n" + "="*70)
    print(f"🚀 PRODUCTION EXTRACTION: {source_name.upper()}")
    print("="*70)
    print(f"📡 URL: {url}")
    print(f"💾 Save to KB: {save_to_kb}")
    print("="*70)
    
    extractor = extractor_class()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate
            print(f"\n⏳ Loading page...")
            await page.goto(url, timeout=45000)
            print(f"✅ Page loaded")
            
            # Pre-process
            print(f"⏳ Pre-processing (scroll & wait)...")
            await extractor.pre_process(page)
            
            # Extract
            print(f"🔍 Extracting data...")
            results = await extractor.extract(page)
            results = await extractor.post_process(results)
            
            print(f"✅ Extracted: {len(results)} items")
            
            # Show sample
            if results:
                print(f"\n📋 Sample Results (first 3):")
                for i, item in enumerate(results[:3], 1):
                    title = item.get('title', 'N/A')[:70]
                    url_item = item.get('url', 'N/A')[:50]
                    print(f"   {i}. {title}")
                    print(f"      → {url_item}")
                    print()
            
            # Save to knowledge base
            if save_to_kb and results:
                print(f"💾 Saving to Knowledge Base...")
                kb = ExtractorKnowledgeBridge()
                summary = await kb.save_extraction_results(
                    results=results,
                    source=source_name,
                    url=url,
                    namespace="legal_regulations"
                )
                
                print(f"\n📊 Save Summary:")
                print(f"   ✅ Saved: {summary['saved']}")
                print(f"   ⏭️  Skipped: {summary['skipped']}")
                print(f"   ❌ Errors: {summary['errors']}")
                print(f"   📊 Total: {summary['total']}")
            
            # Save to file juga
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_{source_name}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "source": source_name,
                    "url": url,
                    "timestamp": timestamp,
                    "count": len(results),
                    "results": results
                }, f, indent=2)
            
            print(f"💾 Results saved to: {filename}")
            
            return {
                "source": source_name,
                "count": len(results),
                "saved": summary['saved'] if save_to_kb else 0,
                "file": filename
            }
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await browser.close()


async def extract_all_sources(save_to_kb: bool = False):
    """Extract dari semua sources"""
    print("\n" + "="*70)
    print("🚀 BATCH EXTRACTION: ALL SOURCES")
    print("="*70)
    
    results = []
    for source_key in SOURCES.keys():
        result = await extract_from_source(source_key, save_to_kb)
        if result:
            results.append(result)
        print("\n" + "-"*70)
    
    # Summary
    print("\n" + "="*70)
    print("📊 BATCH SUMMARY")
    print("="*70)
    for r in results:
        print(f"   {r['source']:15} → {r['count']:3} items (saved: {r['saved']})")
    print(f"\n   Total: {sum(r['count'] for r in results)} items")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Production Extraction Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_production_extraction.py --source hukumonline
  python3 run_production_extraction.py --source hukumonline --save
  python3 run_production_extraction.py --all --save
        """
    )
    
    parser.add_argument(
        "--source",
        choices=list(SOURCES.keys()),
        help="Source to extract from"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract from all sources"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to Knowledge Base"
    )
    
    args = parser.parse_args()
    
    if args.all:
        asyncio.run(extract_all_sources(args.save))
    elif args.source:
        asyncio.run(extract_from_source(args.source, args.save))
    else:
        parser.print_help()
        print("\n❌ Please specify --source or --all")


if __name__ == "__main__":
    main()
