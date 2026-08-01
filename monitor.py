import os
import json
import datetime
import requests
import yfinance as yf

# ==========================================
# 0. 주식투자가이드/data/portfolio_state.json 로드
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
state_file_path = os.path.join(current_dir, "주식투자가이드", "data", "portfolio_state.json")

# 경로 예외 처리
if not os.path.exists(state_file_path):
    state_file_path = os.path.join(current_dir, "data", "portfolio_state.json")

with open(state_file_path, "r", encoding="utf-8") as f:
    state_data = json.load(f)

holdings = state_data["holdings"]
SAMSUNG_SHARES = holdings["samsung_shares"]
HYNIX_SHARES = holdings["hynix_shares"]
OTHER_ASSETS_KRW = holdings["other_assets_krw"]

# ==========================================
# 1. 실시간 시세 자동 수집 (Yfinance)
# ==========================================
kospi_data = yf.Ticker("^KS11").history(period="1d")
samsung_data = yf.Ticker("005930.KS").history(period="1d")
hynix_data = yf.Ticker("000660.KS").history(period="1d")

kospi = kospi_data['Close'].iloc[-1]
samsung_price = samsung_data['Close'].iloc[-1]
hynix_price = hynix_data['Close'].iloc[-1]

# ==========================================
# 2. 포트폴리오 가치 및 비중 계산
# ==========================================
samsung_val = samsung_price * SAMSUNG_SHARES
hynix_val = hynix_price * HYNIX_SHARES
semi_total_val = samsung_val + hynix_val
total_portfolio_val = semi_total_val + OTHER_ASSETS_KRW

semi_ratio = (semi_total_val / total_portfolio_val) * 100
samsung_ratio_in_semi = (samsung_val / semi_total_val) * 100
hynix_ratio_in_semi = (hynix_val / semi_total_val) * 100

# ==========================================
# 3. 6000~8500 전략 매트릭스 목표 비중 산출
# ==========================================
def get_strategy_target(idx):
    if idx >= 8500: return 35, "L6 (8,500+ 상단 과열)"
    elif idx >= 8000: return 40, "L5 (8,000~8,500 상단 진입)"
    elif idx >= 7500: return 45, "L4 (7,500~8,000 상단 적정)"
    elif idx >= 7000: return 50, "L3 (7,000~7,500 중립)"
    elif idx >= 6500: return 55, "L2 (6,500~7,000 현위치 하단)"
    elif idx >= 6000: return 60, "L1 (6,000~6,500 저평가)"
    else: return 65, "L0 (6,000 미만 바닥)"

target_ratio, level_name = get_strategy_target(kospi)
gap = semi_ratio - target_ratio
abs_gap = abs(gap)

# ==========================================
# 4. 텔레그램 메시지 생성 및 발송
# ==========================================
now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
bot_token = os.environ.get("TELEGRAM_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(text):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})

# 격차 8.0%p 이상 이탈 시 알림
if abs_gap >= 8.0:
    action_type = "매도 ➔ 기타자산 이동" if gap > 0 else "저가 매수 (실탄 집행)"
    trade_amount = int(abs(gap / 100 * total_portfolio_val))
    
    msg = f"""🚨 [국내주식 스마트 리밸런싱 알림] ({now_time})
----------------------------------------
📊 KOSPI 지수: {kospi:,.1f} pt ({level_name})
💰 계좌 총 평가액: 약 {total_portfolio_val/10000:,.0f} 만원
📈 현재 반도체 비중: {semi_ratio:.1f}% (삼전 {samsung_val/total_portfolio_val*100:.1f}% / 닉스 {hynix_val/total_portfolio_val*100:.1f}%)
🎯 목표 반도체 비중: {target_ratio:.1f}%
⚠️ 비중 이탈 격차: {gap:+.1f}%p (기준 8.0%p 초과!)

💡 [추천 매매 액션]
- 반도체 총 약 {trade_amount/10000:,.0f} 만원 {action_type}
- 삼성전자 ({SAMSUNG_SHARES}주): {samsung_price:,.0f}원 ({samsung_ratio_in_semi:.1f}%)
- SK하이닉스 ({HYNIX_SHARES}주): {hynix_price:,.0f}원 ({hynix_ratio_in_semi:.1f}%)

⏰ 15:30 동시호가 전 분할 매매를 진행하세요!
"""
    send_telegram(msg)
    print("리밸런싱 경보 발송 완료")
else:
    msg = f"""🟢 [국내주식 정기 점검] ({now_time})
KOSPI: {kospi:,.1f} pt ({level_name})
계좌 평가액: 약 {total_portfolio_val/10000:,.0f} 만원
현비중: {semi_ratio:.1f}% / 목표: {target_ratio:.1f}% (격차: {gap:+.1f}%p)
정상 범위(±8%p 미만)입니다. 편안한 장 보내세요!"""
    send_telegram(msg)
    print("정기 점검 알림 발송 완료")
