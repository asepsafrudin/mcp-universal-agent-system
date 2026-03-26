
import asyncio
import sys
from pathlib import Path

# Add paths to sys.path
MCP_ROOT = Path("/home/aseps/MCP")
sys.path.insert(0, str(MCP_ROOT / "mcp-unified"))

from integrations.web_scraping import GenericBrowserBridge, JDIHExtractor

async def test_scraping():
    url = "https://www.hukumonline.com/berita"
    print(f"Testing scraping of {url}...")
    
    # Initialize browser with stealth mode
    async with GenericBrowserBridge(headless=True, stealth_mode=True) as browser:
        # Navigate
        page = await browser.navigate(url, wait_until="domcontentloaded")
        
        # Check if we are blocked
        content = await page.content()
        print(f"Content length: {len(content)}")
        with open("hukumonline_test_content.html", "w") as f:
            f.write(content[:10000])
        
        if "security verification" in content.lower() and len(content) < 5000:
            print("❌ BLOCKED by security verification (Cloudflare)")
        else:
            print("✅ SUCCESS: Not blocked or likely bypassed")
            
            # Try to extract something
            extractor = JDIHExtractor()
            # Note: JDIHExtractor might need specific selectors for news list, 
            # let's see if we can find any headings
            headings = await page.query_selector_all("h2")
            print(f"Found {len(headings)} h2 headings")
            for h in headings[:3]:
                text = await h.inner_text()
                print(f" - {text.strip()}")
        
        await page.close()

if __name__ == "__main__":
    asyncio.run(test_scraping())
