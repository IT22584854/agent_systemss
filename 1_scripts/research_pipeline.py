import asyncio
import os
import random
import httpx
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

# ETHICAL IDENTIFICATION
RESEARCH_USER_AGENT = "SriLanka-Medical-OCR-Research-Bot/1.0 (+https://your-research-site.com)"

async def download_pdf(url, dest_folder, hospital_name):
    """Downloads PDF only if it doesn't already exist locally."""
    try:
        # Create a clean, predictable filename
        clean_name = url.split('/')[-1].split('?')[0] or "document.pdf"
        if not clean_name.lower().endswith('.pdf'):
            clean_name += ".pdf"
            
        file_path = dest_folder / f"{hospital_name}_{clean_name}"

        # DEDUPLICATION CHECK
        if file_path.exists():
            # Silent skip to keep console clean, or print for transparency
            # print(f"⏩ Already have: {file_path.name}")
            return True

        # ETHICAL DELAY
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": RESEARCH_USER_AGENT}
            response = await client.get(url, headers=headers)
            
            # Verify it's actually a PDF before saving
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"📥 [NEW PDF] Saved: {file_path.name}")
                return True
    except Exception:
        pass
    return False

async def main():
    # 1. Setup Directories
    base_dir = Path(r"D:\Medical_OCR_Research\0_raw_data")
    md_dir, pdf_dir = base_dir / "markdown", base_dir / "pdfs"
    for folder in [md_dir, pdf_dir]: folder.mkdir(parents=True, exist_ok=True)

    # 2. Medical Content Filter (Strips headers/footers/ads)
    medical_filter = PruningContentFilter(threshold=0.45, threshold_type="dynamic")
    md_generator = DefaultMarkdownGenerator(content_filter=medical_filter)
    
    browser_config = BrowserConfig(
        headless=True,
        accept_downloads=True,
        downloads_path=str(pdf_dir.absolute()),
        user_agent=RESEARCH_USER_AGENT
    )

    # 3. Comprehensive Hospital Target List
    GOVT_TARGETS = [
        {"name": "EPID", "url": "https://www.epid.gov.lk/weekly-epidemiological-report"},
        {"name": "MOH", "url": "https://www.health.gov.lk/"},
        {"name": "NHSL", "url": "http://www.nhsl.health.gov.lk/"},
        {"name": "LRH", "url": "https://lrh.health.gov.lk/"},
        {"name": "NHK", "url": "https://nhkandy.org/"},
        {"name": "APEKSHA", "url": "https://www.ncisl.health.gov.lk/"},
        {"name": "MRI", "url": "https://www.mri.gov.lk/"}
    ]

    # 4. Sequential Crawl Loop (Fixes the "Only MOH" issue)
    for hospital in GOVT_TARGETS:
        print(f"\n--- 🏥 STARTING SCAN: {hospital['name']} ---")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                markdown_generator=md_generator,
                deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, max_pages=10),
                mean_delay=2.0,   # Politely wait between pages
                max_range=3.0,    # Random jitter
                wait_until="networkidle",
                page_timeout=90000
            )

            try:
                results = await crawler.arun(url=hospital['url'], config=run_config)

                # Handle result list from deep crawl
                crawl_list = results if isinstance(results, list) else [results]
                print(f"✅ Found {len(crawl_list)} pages for {hospital['name']}")

                for i, result in enumerate(crawl_list):
                    if not result or not result.success: continue

                    # A. Save Markdown Text
                    final_md = result.markdown.fit_markdown or result.markdown.raw_markdown
                    md_filename = md_dir / f"{hospital['name']}_p{i}.md"
                    with open(md_filename, "w", encoding="utf-8") as f:
                        f.write(f"Source URL: {result.url}\n\n{final_md}")

                    # B. Extract & Download unique PDFs
                    all_links = result.links.get('internal', []) + result.links.get('external', [])
                    pdf_urls = {l['href'] for l in all_links if l.get('href', '').lower().endswith('.pdf')}
                    
                    for pdf_url in pdf_urls:
                        await download_pdf(pdf_url, pdf_dir, hospital['name'])

            except Exception as e:
                print(f"⚠️ {hospital['name']} Skip: {e}")
        
        # Ethical cooling period between different government domains
        print(f"💤 Resting before next institution...")
        await asyncio.sleep(5)

    print(f"\n🏆 ALL INSTITUTIONS PROCESSED.")
    print(f"📂 Data stored in: {base_dir}")

if __name__ == "__main__":
    asyncio.run(main())