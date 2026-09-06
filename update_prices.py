import os
import json
import datetime
import urllib.request

items = [
    ('kospi', 'KOSPI', '^KS11', 'index'),
    ('samsung', '005930', '005930.KS', 'stock'),
    ('hynix', '000660', '000660.KS', 'stock'),
    ('cd', '459580', '459580.KS', 'stock'),
    ('sofr', '456610', '456610.KS', 'stock'),
    ('us30b', '453850', '453850.KS', 'stock'),
    ('gold', '411060', '411060.KS', 'stock'),
    ('snp500', '360750', '360750.KS', 'stock'),
    # 하위 호환용 (필요 시)
    ('us10b', '308620', '308620.KS', 'stock'),
    # 해외 자산 및 환율
    ('usdkrw', None, 'USDKRW=X', 'fx'),
    ('tsla', None, 'TSLA', 'us_stock'),
    ('spcx', None, 'SPCX', 'us_stock'),
    ('nvda', None, 'NVDA', 'us_stock'),
    ('googl', None, 'GOOGL', 'us_stock'),
    ('mu', None, 'MU', 'us_stock'),
    ('qqqm', None, 'QQQM', 'us_stock'),
    ('tltw', None, 'TLTW', 'us_stock')
]

def fetch_naver(code, itype):
    if not code:
        return None
    try:
        url = f'https://m.stock.naver.com/api/{itype}/{code}/basic'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        res = urllib.request.urlopen(req, timeout=5)
        data = json.loads(res.read().decode('utf-8'))

        over_info = data.get('overMarketPriceInfo') or {}
        over_price = over_info.get('overPrice')
        val_str = over_price or data.get('nowValue') or data.get('nowPrice') or data.get('closePrice')
        if val_str:
            val = float(str(val_str).replace(',', ''))
            if val > 0:
                return round(val, 2) if itype in ('index', 'us_stock', 'fx') else int(val)
    except Exception as e:
        print(f"Naver fetch failed for {code}: {e}")
    return None

def fetch_yahoo(symbol, itype):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        res = urllib.request.urlopen(req, timeout=5)
        data = json.loads(res.read().decode('utf-8'))
        result = data.get('chart', {}).get('result', [])
        if result and len(result) > 0:
            meta = result[0].get('meta', {})
            val = meta.get('regularMarketPrice') or meta.get('chartPreviousClose')
            if val and float(val) > 0:
                return round(float(val), 2) if itype in ('index', 'us_stock', 'fx') else int(val)
    except Exception as e:
        print(f"Yahoo fetch failed for {symbol}: {e}")
    return None

current_dir = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_dir, "guide", "data", "live_market.js")

# Stale-While-Revalidate: 기존 캐시 시세 사전 로드 (수집 실패 시 이전 정상가 보존)
existing_prices = {}
if os.path.exists(js_path):
    try:
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "window.LIVE_MARKET_DATA = " in content:
                json_part = content.split("window.LIVE_MARKET_DATA = ")[1].rstrip(";\n ")
                existing_prices = json.loads(json_part).get("prices", {})
    except Exception as e:
        print(f"Notice: Could not load existing cache: {e}")

prices = existing_prices.copy()
new_fetched_count = 0

for key, code, yahoo_symbol, itype in items:
    # 1차: 네이버 증권 API (프리/애프터마켓 시세 포함)
    price = fetch_naver(code, itype)
    
    # 2차: 네이버 실패 시 야후 파이낸스 백업 수집
    if price is None:
        price = fetch_yahoo(yahoo_symbol, itype)

    if price is not None:
        prices[key] = price
        new_fetched_count += 1
    elif key in prices:
        print(f"⚠️ Notice: Fetch failed for {key}. Retaining previous stale price ({prices[key]})")
    else:
        print(f"❌ Error: Fetch failed for {key} and no cached price available.")

# SpaceX 하위 호환 별칭 지원 (spcx -> spacex)
if 'spcx' in prices:
    prices['spacex'] = prices['spcx']

kst = datetime.timezone(datetime.timedelta(hours=9))
now_str = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
out_data = {
    "last_updated": now_str,
    "prices": prices
}

with open(js_path, "w", encoding="utf-8") as f:
    f.write(f"window.LIVE_MARKET_DATA = {json.dumps(out_data, ensure_ascii=False, indent=2)};\n")

print(f"Successfully updated live_market.js at {now_str} (Updated {new_fetched_count}/{len(items)} items, Total in state: {len(prices)})")
