
import asyncio
import sys
from pathlib import Path

# Add paths to sys.path
MCP_ROOT = Path("/home/aseps/MCP")
sys.path.insert(0, str(MCP_ROOT / "mcp-unified"))

from integrations.web_scraping import GenericBrowserBridge, JDIHExtractor

async def test_source(browser, url, source_name):
    print(f"\n--- Testing {source_name}: {url} ---")
    try:
        page = await browser.navigate(url, wait_until="domcontentloaded")
        content = await page.content()
        print(f"[{source_name}] Content length: {len(content)}")
        
        if "security verification" in content.lower() and len(content) < 5000:
            print(f"❌ [{source_name}] BLOCKED by security verification (Cloudflare)")
            return False
            
        # Try to extract something simple (h2 or h3 count)
        h2_count = await page.evaluate("() => document.querySelectorAll('h2').length")
        h3_count = await page.evaluate("() => document.querySelectorAll('h3').length")
        print(f"[{source_name}] Found {h2_count} h2 and {h3_count} h3 headings")
        
        if h2_count > 0 or h3_count > 0:
            print(f"✅ [{source_name}] SUCCESS: Likely bypassed or not blocked")
            return True
        else:
            print(f"⚠️ [{source_name}] WARNING: Page loaded but no headings found. Might be empty or slow.")
            return True # Still count as success if no block detected
            
    except Exception as e:
        print(f"❌ [{source_name}] ERROR: {str(e)}")
        return False

async def main():
    targets = [
        ("Hukumonline", "https://www.hukumonline.com/berita"),
        ("JDIH Kemendagri", "https://jdih.kemendagri.go.id"),
        ("Peraturan.go.id", "https://peraturan.go.id"),
        ("JDIH BPK", "https://peraturan.bpk.go.id"),
        ("Setneg", "https://jdih.setneg.go.id"),
        ("Mahkamah Agung", "https://jdih.mahkamahagung.go.id")
    ]
    
    print(f"Testing {len(targets)} scraping targets...")
    
    async with GenericBrowserBridge(headless=True, stealth_mode=True) as browser:
        results = []
        for name, url in targets:
            success = await test_source(browser, url, name)
            results.append((name, success))
            await asyncio.sleep(2) # Delay between targets
            
    print("\n" + "="*30)
    print("FINAL SUMMARY")
    print("="*30)
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name:20}: {status}")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(main())
