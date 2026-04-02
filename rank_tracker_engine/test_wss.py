import asyncio
from playwright.async_api import async_playwright
import os

ws_endpoint = "wss://brd-customer-hl_f9fc14c2-zone-scraping_browser1:fqwksbmftt8j@brd.superproxy.io:9222"

async def test_wss():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            print("Connected to BRD")
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to coupang
            await page.goto("https://www.coupang.com/np/search?q=%ED%9C%A0%EC%B2%B4%EC%96%B4&page=1", wait_until="domcontentloaded", timeout=60000)
            print("Title:", await page.title())
            html = await page.content()
            
            # write html
            with open("../Coupang_Rank_Tracker_v1/page_wss.html", "w", encoding="utf-8") as f:
                f.write(html)
            await browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_wss())
