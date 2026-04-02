import sys
import os
import json
import asyncio
import re
import requests

# 상위 디렉토리의 Coupang_Rank_Tracker_v1 경로 추가
tracker_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Coupang_Rank_Tracker_v1"))
sys.path.insert(0, tracker_dir)

from src.scraper import CoupangScraper
from src.rank_tracker import calculate_rank

def load_telegram_config():
    tg_config_path = os.path.join(os.path.dirname(__file__), "tg_config.json")
    if os.path.exists(tg_config_path):
        with open(tg_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram 봇 알림 실패: {e}")
        return False

async def main():
    print("=== 쿠팡 랭킹 자동 리포트 봇 가동 ===")
    
    # 1. 텔레그램 설정 로드
    tg_config = load_telegram_config()
    if not tg_config or not tg_config.get("token") or not tg_config.get("chat_id"):
        print("텔레그램 설정(tg_config.json)이 없거나 불완전합니다. 대시보드에서 텔레그램 설정을 먼저 마쳐주세요.")
        return

    # 2. 타겟 정보 불러오기
    targets_path = os.path.join(os.path.dirname(__file__), "targets.json")
    if not os.path.exists(targets_path):
        print("추적할 타겟 파일(targets.json)이 없습니다. 대시보드에서 [전체 저장]을 눌러주세요.")
        return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    if not targets:
        print("추적할 키워드/url 정보가 없습니다.")
        return

    # 3. 프록시 정보 불러오기
    proxy_config_path = os.path.join(tracker_dir, "proxy_config.txt")
    if not os.path.exists(proxy_config_path):
        print("proxy_config.txt 파일이 없습니다.")
        return
    with open(proxy_config_path, "r", encoding="utf-8") as f:
        ws_endpoint = f.read().strip()

    scraper = CoupangScraper(ws_endpoint=ws_endpoint)
    
    report_data = []

    # 4. 순차적으로 스크래핑
    for idx, target in enumerate(targets):
        keyword = target["keyword"]
        target_url = target["url"]
        
        # URL에서 Target ID 추출
        target_id = ""
        m = re.search(r'vendorItemId=(\d+)', target_url)
        if m:
            target_id = m.group(1)
        else:
            m = re.search(r'/products/(\d+)', target_url)
            if m: target_id = m.group(1)
            else: target_id = target_url.strip()

        print(f"\n[{idx+1}/{len(targets)}] '{keyword}' 순위 확인 중...")

        pages_html = []
        found_result = None

        try:
            async for content in scraper.scrape_generator(keyword, 3):
                pages_html.append(content)
                current_result = calculate_rank([content], target_id)
                if current_result['Status'] == 'FOUND':
                    found_result = calculate_rank(pages_html, target_id)
                    break
            
            if found_result and found_result['Status'] == 'FOUND':
                rank_organic = found_result.get('Organic_Rank', '-')
                rank_ad = found_result.get('Ad_Rank', '-')
                
                badges = []
                if found_result.get('Rocket_Status') == 'YES': badges.append('로켓')
                if rank_ad != '-' or found_result.get('Ad_Status') == 'YES': badges.append('광고')
                badge_str = ", ".join(badges) if badges else "없음"
                
                report_data.append(f"🔹 <b>[{keyword}]</b>\n- 일반 순위: {rank_organic}{'위' if rank_organic != '-' else ''}\n- 광고 노출: {rank_ad}{'번째 노출' if rank_ad != '-' else '미노출'}\n- 배지: {badge_str}")
            else:
                report_data.append(f"🔹 <b>[{keyword}]</b>\n- 검색 결과 없음 (순위 이탈)")
                
        except Exception as e:
            print(f"Error on {keyword}: {e}")
            report_data.append(f"🔹 <b>[{keyword}]</b>\n- 조회 중 오류 발생")
            
        # 블로킹 및 차단 방지 대기
        await asyncio.sleep(2)

    # 5. 리포트 생성 및 전송
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    final_message = f"🚀 <b>[일일 쿠팡 랭킹 리포트]</b>\n⏱ 측정 일시: {now_str}\n─────────────────\n\n" + "\n\n".join(report_data)
    
    print("\n[알림 전송 중...]")
    success = send_telegram(tg_config["token"], tg_config["chat_id"], final_message)
    if success:
         print("성공적으로 알림을 telegram으로 전송했습니다!")
    else:
         print("telegram 전송에 실패했습니다.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
