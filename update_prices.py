import os
import json
import datetime
import urllib.request

items = [
    ('kospi', 'KOSPI', '^KS11', 'index'),
    ('samsung', '005930', '005930.KS', 'stock'),
    ('hynix', '000660', '000660.KS', 'stock'),
    ('sofr', '456610', '456610.KS', 'stock'),
    ('us10b', '308620', '308620.KS', 'stock'),
    ('gold', '132030', '132030.KS', 'stock'),
    ('snp500', '219480', '219480.KS', 'stock')
]

def fetch_naver(code, itype):
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
                return val if itype == 'index' else int(val)
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
                return float(val) if itype == 'index' else int(val)
    except Exception as e:
        print(f"Yahoo fetch failed for {symbol}: {e}")
    return None

prices = {}
for key, code, yahoo_symbol, itype in items:
    # 1차: 네이버 증권 API (프리/애프터마켓 시세 포함)
    price = fetch_naver(code, itype)
    
    # 2차: 네이버 실패 시 야후 파이낸스 백업 수집
    if price is None:
        price = fetch_yahoo(yahoo_symbol, itype)

    if price is not None:
        prices[key] = price

kst = datetime.timezone(datetime.timedelta(hours=9))
now_str = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
out_data = {
    "last_updated": now_str,
    "prices": prices
}

current_dir = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_dir, "guide", "data", "live_market.js")

with open(js_path, "w", encoding="utf-8") as f:
    f.write(f"window.LIVE_MARKET_DATA = {json.dumps(out_data, ensure_ascii=False, indent=2)};\n")

print(f"Successfully updated live_market.js at {now_str} (Fetched {len(prices)}/{len(items)} items)")
