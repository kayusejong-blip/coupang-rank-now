import builtins
import sys
import os

inputs = [
    "휠체어",
    "https://www.coupang.com/vp/products/8510729008?itemId=24676151889&vendorItemId=91645944895",
    "wss://brd-customer-hl_f9fc14c2-zone-scraping_browser1:fqwksbmftt8j@brd.superproxy.io:9222"
]
input_iter = iter(inputs)

def mock_input(prompt=""):
    try:
        val = next(input_iter)
        print(prompt + val) # 로그상에서 어떤걸 입력했는지 표시
        return val
    except StopIteration:
        return ""

builtins.input = mock_input

# Coupang_Rank_Tracker_v1 내부 모듈 import를 위한 경로 세팅
tracker_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Coupang_Rank_Tracker_v1"))
sys.path.insert(0, tracker_dir)
os.chdir(tracker_dir)

import main

if __name__ == "__main__":
    import asyncio
    # Windows 환경에서 asyncio RuntimeError 방지를 위해 프로액터 설정
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    try:
        asyncio.run(main.main())
    except Exception as e:
        print(f"Exception details: {e}")
