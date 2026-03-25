#!/usr/bin/env python3
"""
Agentic Scraper CLI - Cline sebagai Agentic AI Brain

Usage:
    python agentic_scrape.py --url <website_url>
    python agentic_scrape.py --batch urls.txt
    python agentic_scrape.py --targets jdihn,hukumonline,detik

Examples:
    python agentic_scrape.py --url https://jdihn.go.id
    python agentic_scrape.py --targets jdihn,hukumonline
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent path untuk imports
sys.path.insert(0, '/home/aseps/MCP/mcp-unified')

from integrations.agentic_ai.cline_interface import ClineAgenticInterface


# Target websites (yang gagal sebelumnya)
TARGET_WEBSITES = {
    "jdihn": {
        "name": "JDIHN",
        "url": "https://jdihn.go.id",
        "description": "Jaringan Dokumentasi Hukum Nasional"
    },
    "hukumonline": {
        "name": "Hukumonline",
        "url": "https://www.hukumonline.com/berita",
        "description": "Portal Berita Hukum Terbesar"
    },
    "detik": {
        "name": "detikHukum",
        "url": "https://news.detik.com/hukum",
        "description": "Kanal Hukum detik.com"
    },
    "lawjustice": {
        "name": "Law-Justice",
        "url": "https://law-justice.co",
        "description": "Investigasi Hukum"
    },
    "antara": {
        "name": "ANTARA Hukum",
        "url": "https://www.antaranews.com/hukum",
        "description": "Berita Hukum ANTARA"
    }
}


async def scrape_single(url: str, goal: str = None):
    """Scrape single website"""
    print(f"\n{'='*70}")
    print(f"🚀 Agentic Scraping: {url}")
    print(f"{'='*70}\n")
    
    agent = ClineAgenticInterface()
    result = await agent.scrape_website(url, goal)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 RESULT SUMMARY")
    print(f"{'='*70}")
    
    if result.get("success"):
        print(f"✅ Status: SUCCESS")
        print(f"📄 URL: {result['url']}")
        print(f"📊 Raw Items: {len(result.get('raw_data', []))}")
        print(f"✅ Valid Items: {len(result.get('validated_data', []))}")
        
        # Show validation breakdown
        validated = result.get('validated_data', [])
        valid_count = sum(1 for v in validated if v.get('_validation', {}).get('status') == 'valid')
        partial_count = sum(1 for v in validated if v.get('_validation', {}).get('status') == 'partial')
        
        print(f"   - Fully Valid: {valid_count}")
        print(f"   - Partial: {partial_count}")
        
        if result.get('storage'):
            print(f"💾 Stored: {result['storage'].get('stored', 0)} items")
        
        # Show sample data
        if validated:
            print(f"\n📝 Sample Data (first item):")
            sample = validated[0]
            print(f"   Title: {sample.get('title', 'N/A')[:80]}...")
            print(f"   Content: {sample.get('content', 'N/A')[:100]}...")
            print(f"   Validation: {sample.get('_validation', {}).get('status', 'unknown')}")
    else:
        print(f"❌ Status: FAILED")
        print(f"🔴 Error: {result.get('error', 'Unknown error')}")
    
    print(f"{'='*70}\n")
    
    return result


async def scrape_batch(urls_file: str):
    """Scrape multiple websites from file"""
    print(f"\n{'='*70}")
    print(f"🚀 Batch Agentic Scraping")
    print(f"{'='*70}\n")
    
    # Read URLs from file
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"📊 Total URLs to scrape: {len(urls)}\n")
    
    agent = ClineAgenticInterface()
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*70}")
        print(f"📌 [{i}/{len(urls)}] Processing: {url}")
        print(f"{'='*70}")
        
        result = await agent.scrape_website(url)
        results.append(result)
        
        # Delay antar request
        if i < len(urls):
            print(f"\n⏳ Waiting 3 seconds before next URL...")
            await asyncio.sleep(3)
    
    # Print batch summary
    print(f"\n{'='*70}")
    print(f"📊 BATCH SUMMARY")
    print(f"{'='*70}")
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_raw = sum(len(r.get('raw_data', [])) for r in successful)
        total_valid = sum(len(r.get('validated_data', [])) for r in successful)
        print(f"📊 Total Raw Items: {total_raw}")
        print(f"✅ Total Valid Items: {total_valid}")
    
    if failed:
        print(f"\n🔴 Failed URLs:")
        for r in failed:
            print(f"   - {r.get('url', 'Unknown')}: {r.get('error', 'Unknown error')[:50]}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"batch_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_urls": len(urls),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    return results


async def scrape_targets(targets: list):
    """Scrape predefined targets"""
    print(f"\n{'='*70}")
    print(f"🚀 Scraping Predefined Targets")
    print(f"{'='*70}\n")
    
    urls = []
    for target in targets:
        if target in TARGET_WEBSITES:
            site = TARGET_WEBSITES[target]
            urls.append(site["url"])
            print(f"📌 {target}: {site['name']} - {site['description']}")
        else:
            print(f"⚠️ Unknown target: {target}")
    
    if not urls:
        print("❌ No valid targets to scrape")
        return
    
    print(f"\n📊 Total targets: {len(urls)}\n")
    
    # Scrape each target
    agent = ClineAgenticInterface()
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*70}")
        print(f"📌 [{i}/{len(urls)}] Processing: {url}")
        print(f"{'='*70}")
        
        result = await agent.scrape_website(url)
        results.append(result)
        
        if i < len(urls):
            print(f"\n⏳ Waiting 3 seconds before next target...")
            await asyncio.sleep(3)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TARGETS SUMMARY")
    print(f"{'='*70}")
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    # Print detailed results per target
    print(f"\n📋 Detailed Results:")
    for target, result in zip(targets, results):
        site_name = TARGET_WEBSITES.get(target, {}).get("name", target)
        if result.get("success"):
            valid_count = len(result.get('validated_data', []))
            print(f"   ✅ {site_name}: {valid_count} items")
        else:
            print(f"   ❌ {site_name}: {result.get('error', 'Failed')[:40]}...")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"targets_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "targets": targets,
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    return results


def list_targets():
    """List available predefined targets"""
    print(f"\n{'='*70}")
    print(f"📋 Available Targets")
    print(f"{'='*70}\n")
    
    for key, site in TARGET_WEBSITES.items():
        print(f"   {key:12} - {site['name']}")
        print(f"                {site['description']}")
        print(f"                URL: {site['url']}\n")
    
    print(f"{'='*70}\n")
    print("Usage: python agentic_scrape.py --targets jdihn,hukumonline")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Agentic Web Scraper - Cline as AI Brain',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python agentic_scrape.py --url https://jdihn.go.id
    python agentic_scrape.py --targets jdihn,hukumonline,detik
    python agentic_scrape.py --batch urls.txt
    python agentic_scrape.py --list
        """
    )
    
    parser.add_argument('--url', type=str, help='Single URL to scrape')
    parser.add_argument('--targets', type=str, help='Comma-separated list of predefined targets (e.g., jdihn,hukumonline)')
    parser.add_argument('--batch', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--list', action='store_true', help='List available predefined targets')
    parser.add_argument('--goal', type=str, help='Goal/description for scraping task')
    
    args = parser.parse_args()
    
    if args.list:
        list_targets()
        return
    
    if args.url:
        # Single URL mode
        asyncio.run(scrape_single(args.url, args.goal))
    
    elif args.targets:
        # Predefined targets mode
        targets = [t.strip() for t in args.targets.split(',')]
        asyncio.run(scrape_targets(targets))
    
    elif args.batch:
        # Batch file mode
        asyncio.run(scrape_batch(args.batch))
    
    else:
        parser.print_help()
        print("\n💡 Tip: Use --list to see available predefined targets")


if __name__ == "__main__":
    main()
