import asyncio
import random
from urllib.parse import quote
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CoupangScraper:
    def __init__(self, ws_endpoint: str = None):
        # 기존 변수명을 유지하되, 내부적으로는 Web Unlocker HTTP 프록시 주소로 사용됩니다.
        self.proxy_url = ws_endpoint

    async def scrape_generator(self, keyword: str, max_pages: int = 3):
        if not self.proxy_url:
            raise ValueError("Bright Data Proxy URL is not set.")

        print(f"[Scraper] Bright Data Web Unlocker (Requests) 모드로 접속합니다...")
        
        encoded_keyword = quote(keyword)
        
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        for page_num in range(1, max_pages + 1):
            url = f"https://www.coupang.com/np/search?q={encoded_keyword}&channel=recent&listSize=72&page={page_num}"
            print(f"[Scraper] Page {page_num} 접속 시도 중 (GET 요청)...")
            
            try:
                # 동기 requests 라이브러리를 비동기적으로 실행하여 서버 블로킹 방지
                resp = await asyncio.to_thread(
                    requests.get,
                    url,
                    headers=HEADERS,
                    proxies={"http": self.proxy_url, "https": self.proxy_url},
                    timeout=60,
                    verify=False,
                )
                
                resp.raise_for_status()
                content = resp.text
                
                print(f"[Scraper] Page {page_num} 스크래핑 완료.")
                yield content
                
            except requests.exceptions.RequestException as e:
                print(f"[Scraper] ❌ 상세 오류 발생 (페이지 {page_num}): {e}")
                break
            
            # 다음 페이지 전 짧은 휴식 (웹 언락커의 경우 너무 길게 쉴 필요가 없습니다)
            if page_num < max_pages:
                await asyncio.sleep(random.uniform(0.5, 1.5))
