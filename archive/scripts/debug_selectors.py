#!/usr/bin/env python3
"""
Debug Selectors Script

Script untuk investigasi struktur HTML website dan menemukan
selectors yang tepat untuk scraping.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/aseps/MCP/mcp-unified')

from playwright.async_api import async_playwright


class SelectorDebugger:
    """Debug tool untuk investigasi struktur HTML website"""
    
    def __init__(self):
        self.results = {}
    
    async def debug_website(self, url: str):
        """
        Debug satu website untuk menemukan selectors yang tepat.
        """
        print(f"\n{'='*70}")
        print(f"🔍 DEBUGGING: {url}")
        print(f"{'='*70}\n")
        
        playwright = None
        browser = None
        context = None
        page = None
        
        try:
            # Launch browser
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Navigate dengan timeout pendek
            print(f"⏳ Loading page...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print(f"✅ Page loaded\n")
            
            # Wait untuk JS render
            await asyncio.sleep(3)
            
            # Scroll untuk trigger lazy load
            print(f"📜 Scrolling...")
            for i in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)
            print(f"✅ Scrolling done\n")
            
            # Analisis struktur HTML
            await self._analyze_structure(page, url)
            
            # Test selectors yang umum
            await self._test_common_selectors(page)
            
            # Save screenshot untuk visual inspection
            screenshot_path = f"debug_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            # Cleanup
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
    
    async def _analyze_structure(self, page, url: str):
        """Analisis struktur HTML dasar"""
        print(f"📊 ANALYZING STRUCTURE\n")
        
        # Get page info
        page_info = await page.evaluate("""
            () => {
                return {
                    title: document.title,
                    url: window.location.href,
                    domain: window.location.hostname,
                    totalElements: document.querySelectorAll('*').length,
                    bodyText: document.body.innerText.substring(0, 500)
                };
            }
        """)
        
        print(f"   Title: {page_info['title']}")
        print(f"   URL: {page_info['url']}")
        print(f"   Domain: {page_info['domain']}")
        print(f"   Total Elements: {page_info['totalElements']}")
        print(f"   Body Preview: {page_info['bodyText'][:100]}...\n")
        
        self.results[url] = {
            "page_info": page_info,
            "selectors": {}
        }
    
    async def _test_common_selectors(self, page):
        """Test selectors yang umum digunakan"""
        print(f"🧪 TESTING COMMON SELECTORS\n")
        
        # Test article selectors
        article_selectors = [
            "article",
            ".article",
            ".news-item",
            ".post",
            ".card",
            ".content-item",
            ".list-item",
            "[data-testid]",
            ".hl-card",
            ".berita",
            ".news"
        ]
        
        print(f"   Article Selectors:")
        for selector in article_selectors:
            count = await self._count_elements(page, selector)
            if count > 0:
                print(f"      ✅ {selector}: {count} elements")
                self.results[page.url]["selectors"][selector] = count
            else:
                print(f"      ❌ {selector}: 0")
        
        print()
        
        # Test title selectors
        title_selectors = [
            "h1",
            "h2",
            ".title",
            ".headline",
            ".article-title",
            "[data-title]"
        ]
        
        print(f"   Title Selectors:")
        for selector in title_selectors:
            count = await self._count_elements(page, selector)
            if count > 0:
                print(f"      ✅ {selector}: {count} elements")
            else:
                print(f"      ❌ {selector}: 0")
        
        print()
        
        # Test content selectors
        content_selectors = [
            ".content",
            ".article-content",
            ".summary",
            ".description",
            ".excerpt",
            "p",
            ".text"
        ]
        
        print(f"   Content Selectors:")
        for selector in content_selectors:
            count = await self._count_elements(page, selector)
            if count > 0:
                print(f"      ✅ {selector}: {count} elements")
            else:
                print(f"      ❌ {selector}: 0")
        
        print()
        
        # Sample data extraction
        await self._sample_extraction(page)
    
    async def _count_elements(self, page, selector: str) -> int:
        """Count elements matching selector"""
        try:
            return await page.evaluate(f"""
                () => document.querySelectorAll('{selector}').length
            """)
        except:
            return 0
    
    async def _sample_extraction(self, page):
        """Extract sample data untuk verifikasi"""
        print(f"📝 SAMPLE EXTRACTION\n")
        
        # Coba ekstrak dengan selectors yang paling umum
        samples = await page.evaluate("""
            () => {
                const results = [];
                
                // Try article selectors
                const articleSelectors = ['article', '.article', '.news-item', '.post', '.card', '.content-item', '.hl-card'];
                let articles = [];
                
                for (const sel of articleSelectors) {
                    const elements = document.querySelectorAll(sel);
                    if (elements.length > 0) {
                        articles = elements;
                        break;
                    }
                }
                
                // Extract first 3 articles
                for (let i = 0; i < Math.min(3, articles.length); i++) {
                    const article = articles[i];
                    const item = {};
                    
                    // Try to find title
                    const titleSelectors = ['h1', 'h2', '.title', '.headline', '.article-title'];
                    for (const sel of titleSelectors) {
                        const el = article.querySelector(sel);
                        if (el) {
                            item.title = el.innerText.trim().substring(0, 100);
                            break;
                        }
                    }
                    
                    // Try to find content
                    const contentSelectors = ['.content', '.summary', '.description', 'p'];
                    for (const sel of contentSelectors) {
                        const el = article.querySelector(sel);
                        if (el) {
                            item.content = el.innerText.trim().substring(0, 150);
                            break;
                        }
                    }
                    
                    if (item.title || item.content) {
                        results.push(item);
                    }
                }
                
                return results;
            }
        """)
        
        if samples and len(samples) > 0:
            print(f"   ✅ Found {len(samples)} sample items:")
            for i, sample in enumerate(samples, 1):
                print(f"\n   Sample {i}:")
                if sample.get('title'):
                    print(f"      Title: {sample['title']}")
                if sample.get('content'):
                    print(f"      Content: {sample['content'][:80]}...")
        else:
            print(f"   ❌ No samples extracted")
        
        print()
    
    def save_report(self):
        """Save debug report to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"debug_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Debug report saved: {filename}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug selectors untuk website scraping')
    parser.add_argument('--url', type=str, required=True, help='URL website untuk di-debug')
    
    args = parser.parse_args()
    
    debugger = SelectorDebugger()
    
    try:
        asyncio.run(debugger.debug_website(args.url))
        debugger.save_report()
        
        print(f"{'='*70}")
        print(f"✅ DEBUGGING COMPLETE")
        print(f"{'='*70}\n")
        print(f"Next steps:")
        print(f"1. Check debug_report_*.json untuk selectors yang berhasil")
        print(f"2. Check screenshot untuk visual inspection")
        print(f"3. Update cline_interface.py dengan selectors yang tepat")
        print()
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Debugging cancelled")
        sys.exit(0)


if __name__ == "__main__":
    main()
