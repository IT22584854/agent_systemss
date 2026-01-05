import asyncio
import os
import aiohttp
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

# 1. SETUP PATHS
BASE_DIR = Path(r"D:\Medical_OCR_Research\0_raw_data")
PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

async def download_pdf(url, folder, prefix):
    """Helper to download PDF and skip if exists"""
    file_name = f"{prefix}_{url.split('/')[-1]}"
    file_path = folder / file_name
    
    if file_path.exists():
        print(f"⏭️  Skipping existing: {file_name}")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    print(f"📥 Saved: {file_name}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

async def run_epid_recovery():
    # 2. BROWSER CONFIG (Headless = True for stability)
    browser_config = BrowserConfig(headless=True, verbose=True)

    # 3. CRAWLER RUN CONFIG (The "Patient" settings)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, max_pages=30),
        wait_until="domcontentloaded",  # Don't wait for background scripts
        page_timeout=120000,           # 2 minutes per page
        mean_delay=3.0,
        max_range=5.0
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🚀 Starting EPID Specialized Recovery...")
        
        # We target the main report page
        result = await crawler.arun(
            url="https://www.epid.gov.lk/weekly-epidemiological-report", 
            config=run_config
        )

        if result.success:
            # Gather all links from the result (Deep crawl merges these)
            all_links = result.links.get('internal', []) + result.links.get('external', [])
            pdf_urls = {l['href'] for l in all_links if l.get('href', '').lower().endswith('.pdf')}
            
            print(f"📄 Found {len(pdf_urls)} potential PDF links. Starting downloads...")
            
            for url in pdf_urls:
                await download_pdf(url, PDF_DIR, "EPID")
        else:
            print(f"❌ Crawl failed: {result.error_message}")

# 4. THE LIFECYCLE TRIGGER (Don't skip this!)
if __name__ == "__main__":
    try:
        asyncio.run(run_epid_recovery())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")