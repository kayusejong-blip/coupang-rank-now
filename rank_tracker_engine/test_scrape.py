import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    async with async_playwright() as p:
        # Use the curl proxy
        proxy_server = "http://brd.superproxy.io:33335"
        proxy_user = "brd-customer-hl_f9fc14c2-zone-residential_proxy1"
        proxy_password = "2iian17u9hsf"
        
        browser = await p.chromium.launch(
            headless=True,
            proxy={
                "server": proxy_server,
                "username": proxy_user,
                "password": proxy_password
            }
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            locale="ko-KR",
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating to page 1...")
        await page.goto("https://www.coupang.com/np/search?q=%ED%9C%A0%EC%B2%B4%EC%96%B4&page=1")
        print("Title:", await page.title())
        html = await page.content()
        with open("../Coupang_Rank_Tracker_v1/page1_test.html", "w", encoding="utf-8") as f:
            f.write(html)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
