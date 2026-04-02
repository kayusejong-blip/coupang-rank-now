import sys
import os
import re
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import requests

# 상위 디렉토리의 Coupang_Rank_Tracker_v1 경로 추가
tracker_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Coupang_Rank_Tracker_v1"))
sys.path.insert(0, tracker_dir)

try:
    from src.scraper import CoupangScraper
    from src.rank_tracker import calculate_rank
except ImportError as e:
    print(f"Import Error: {e}")
    # 만약 경로가 다르면 직접 지정 시도
    sys.path.insert(0, os.path.join(os.getcwd(), "Coupang_Rank_Tracker_v1"))
    from src.scraper import CoupangScraper
    from src.rank_tracker import calculate_rank

app = FastAPI(title="쿠팡 랭킹 나우 API")

# 정적 파일 서빙 (UI)
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

class RankRequest(BaseModel):
    keyword: str
    targetUrl: str
    maxPages: Optional[int] = 3

@app.post("/api/check-rank")
async def check_rank(req: RankRequest):
    # 1. Target ID 추출
    target_id = ""
    target_id_match = re.search(r'vendorItemId=(\d+)', req.targetUrl)
    if target_id_match:
        target_id = target_id_match.group(1)
    else:
        target_id_match = re.search(r'/products/(\d+)', req.targetUrl)
        if target_id_match:
            target_id = target_id_match.group(1)
        else:
            target_id = req.targetUrl.strip()

    if not target_id:
        raise HTTPException(status_code=400, detail="올바른 쿠팡 상품 URL이 아닙니다.")

    # 2. Proxy 설정 불러오기
    proxy_config_path = os.path.join(tracker_dir, "proxy_config.txt")
    if not os.path.exists(proxy_config_path):
        raise HTTPException(status_code=500, detail="proxy_config.txt 파일이 없습니다. 프록시 설정을 먼저 진행해주세요.")
    
    with open(proxy_config_path, "r", encoding="utf-8") as f:
        ws_endpoint = f.read().strip()

    # 3. 스크래핑 및 순위 분석
    scraper = CoupangScraper(ws_endpoint=ws_endpoint)
    try:
        pages_html = []
        found_result = None
        
        # Generator를 통해 1페이지씩 확인
        async for content in scraper.scrape_generator(req.keyword, req.maxPages):
            pages_html.append(content)
            
            # 현재 페이지에서 즉시 분석
            current_result = calculate_rank([content], target_id)
            
            if current_result['Status'] == 'FOUND':
                # 전체 스캔 결과로 재계산 (누적 순위)
                found_result = calculate_rank(pages_html, target_id)
                break
        
        if found_result and found_result['Status'] == 'FOUND':
            return {
                "success": True,
                "data": found_result
            }
        else:
            final_result = calculate_rank(pages_html, target_id)
            return {
                "success": False,
                "message": f"검색 결과 {len(pages_html)}페이지 내에서 해당 상품을 찾을 수 없습니다.",
                "totalScanned": final_result['Total_Scanned']
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TelegramRequest(BaseModel):
    token: Optional[str] = None
    chat_id: Optional[str] = None
    message: str

@app.post("/api/send-telegram")
async def send_telegram(req: TelegramRequest):
    token = req.token
    chat_id = req.chat_id
    
    # 1. 파일에서 토큰 읽어오기 시도
    import json
    tg_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tg_config.json")
    if not token or not chat_id:
        if os.path.exists(tg_config_path):
            try:
                with open(tg_config_path, "r", encoding="utf-8") as f:
                    conf = json.load(f)
                    token = conf.get("token", token)
                    chat_id = conf.get("chat_id", chat_id)
            except Exception:
                pass
                
    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="텔레그램 토큰과 Chat ID가 설정되지 않았습니다.")
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": req.message,
        "parse_mode": "HTML"
    }
    
    try:
        # 비동기로 requests 호출하여 블로킹 방지
        resp = await asyncio.to_thread(requests.post, url, json=payload, timeout=10)
        resp_data = resp.json()
        
        if resp.status_code == 200 and resp_data.get("ok"):
            return {"success": True, "message": "텔레그램 전송 성공"}
        else:
            raise HTTPException(status_code=400, detail=f"텔레그램 전송 실패: {resp_data.get('description')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TargetItem(BaseModel):
    keyword: str
    url: str

class SaveTargetsRequest(BaseModel):
    targets: List[TargetItem]

@app.post("/api/save-targets")
async def save_targets(req: SaveTargetsRequest):
    try:
        targets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "targets.json")
        data_to_save = [{"keyword": t.keyword, "url": t.url} for t in req.targets]
        import json
        with open(targets_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": "서버에 성공적으로 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse("dashboard/static/index.html")

if __name__ == "__main__":
    import uvicorn
    # Windows asyncio policy
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run(app, host="0.0.0.0", port=8000)
