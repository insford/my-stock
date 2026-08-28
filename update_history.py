import os
import sys
import json
import sqlite3
import datetime
import urllib.request

# 수집 대상 종목 정의 (총 11종: 핵심 9종 + 레거시/과거보유 2종)
# (키값, 네이버코드, 야후심볼, 타입, 표시이름)
ITEMS = [
    ('kospi', 'KOSPI', '^KS11', 'index', '코스피 지수'),
    ('snp500_index', '.INX', '^GSPC', 'foreign_index', 'S&P 500 지수'),
    ('samsung', '005930', '005930.KS', 'stock', '삼성전자'),
    ('hynix', '000660', '000660.KS', 'stock', 'SK하이닉스'),
    ('cd', '459580', '459580.KS', 'stock', 'KODEX CD금리액티브'),
    ('sofr', '456610', '456610.KS', 'stock', 'TIGER 미국달러SOFR금리액티브'),
    ('us30b', '453850', '453850.KS', 'stock', 'ACE 미국30년국채액티브(H)'),
    ('gold', '411060', '411060.KS', 'stock', 'ACE KRX금현물'),
    ('snp500', '360750', '360750.KS', 'stock', 'TIGER 미국S&P500'),
    # 과거 이력 호환용 종목
    ('us10b', '308620', '308620.KS', 'stock', 'KODEX 미국채10년액티브'),
    ('fadu', '440110', '440110.KS', 'stock', '파두'),
]

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "guide", "data", "market_history.db")


def init_database(conn):
    """SQLite 테이블, 뷰 및 인덱스 초기화"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_history (
            date TEXT NOT NULL,          -- YYYY-MM-DD
            code TEXT NOT NULL,          -- 자산 고유 키 (kospi, snp500_index, samsung 등)
            name TEXT NOT NULL,          -- 자산명 (삼성전자, 코스피 지수 등)
            asset_type TEXT NOT NULL,    -- stock, index, foreign_index
            price REAL NOT NULL,         -- 일별 종가
            updated_at TEXT NOT NULL,    -- 수집 일시 (YYYY-MM-DD HH:MM:SS)
            PRIMARY KEY (date, code)
        )
    """)
    # WHERE code = ? ORDER BY date ASC 쿼리를 위한 최적화 복합 인덱스
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_date ON market_history(code, date)")
    
    # 전일 대비 등락률(change_percent) 및 전일 종가(prev_price) 자동 계산 뷰
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_market_history AS
        SELECT 
            date,
            code,
            name,
            asset_type,
            price,
            LAG(price, 1) OVER (PARTITION BY code ORDER BY date ASC) AS prev_price,
            ROUND((price - LAG(price, 1) OVER (PARTITION BY code ORDER BY date ASC)) / LAG(price, 1) OVER (PARTITION BY code ORDER BY date ASC) * 100, 2) AS change_percent,
            updated_at
        FROM market_history
    """)
    conn.commit()


def parse_price(val_str, itype):
    """문자열 가격을 적절한 수치(int 또는 float)로 변환"""
    if val_str is None:
        return None
    try:
        clean = str(val_str).replace(',', '').strip()
        val = float(clean)
        if val <= 0:
            return None
        return val if itype in ('index', 'foreign_index') else int(val)
    except (ValueError, TypeError):
        return None


def fetch_naver_history(code, itype, count=50):
    """
    네이버 API를 통해 최근 count 거래일의 종가 히스토리 수집
    반환: { 'YYYY-MM-DD': price, ... }
    """
    try:
        if itype == 'foreign_index':
            url = f"https://api.stock.naver.com/index/{code}/price?pageSize={count}&page=1"
        elif itype == 'index':
            url = f"https://m.stock.naver.com/api/index/{code}/price?pageSize={count}&page=1"
        else:
            url = f"https://m.stock.naver.com/api/stock/{code}/price?pageSize={count}&page=1"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode('utf-8'))

        if not isinstance(data, list):
            print(f"[Naver] Unexpected response format for {code}: not a list")
            return None

        history = {}
        for item in data:
            if not isinstance(item, dict):
                continue
            date_raw = item.get('localTradedAt')
            if not date_raw:
                continue
            # YYYY-MM-DD 포맷 정규화
            date_str = str(date_raw)[:10]
            price = parse_price(item.get('closePrice'), itype)
            if price is not None:
                history[date_str] = price

        return history if history else None
    except Exception as e:
        print(f"[Naver] Fetch failed for {code} ({itype}): {e}")
        return None


def fetch_yahoo_history(symbol, itype, count=50):
    """
    야후 파이낸스 v8 API를 통한 백업 히스토리 수집
    반환: { 'YYYY-MM-DD': price, ... }
    """
    try:
        range_param = "3mo" if count > 10 else "1mo"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={range_param}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode('utf-8'))

        result = data.get('chart', {}).get('result', [])
        if not result:
            return None

        timestamps = result[0].get('timestamp', [])
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])

        history = {}
        combined = list(zip(timestamps, closes))[-count:]
        for ts, close in combined:
            if close is None:
                continue
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")
            price = parse_price(close, itype)
            if price is not None:
                history[date_str] = price

        return history if history else None
    except Exception as e:
        print(f"[Yahoo] Backup fetch failed for {symbol}: {e}")
        return None


def save_to_sqlite(records, mode="init"):
    """
    수집된 레코드를 SQLite DB에 INSERT OR REPLACE (Upsert) 실행
    records: list of tuples (date, code, name, asset_type, price, updated_at)
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_database(conn)

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR REPLACE INTO market_history (date, code, name, asset_type, price, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()

    # 통계 확인
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT date), COUNT(DISTINCT code), MIN(date), MAX(date) FROM market_history")
    total_rows, distinct_dates, distinct_codes, min_d, max_d = cursor.fetchone()
    # DB 단편화 정리 (VACUUM은 초기화/대규모 적재 시에만 실행하여 평일 바이너리 diff 최소화)
    if mode == "init":
        conn.execute("VACUUM")
    conn.close()

    db_size = os.path.getsize(DB_PATH)
    print(f"[{mode.upper()}] SQLite DB Updated: {len(records)} records upserted.")
    print(f"Total Rows: {total_rows} | Distinct Dates: {distinct_dates} ({min_d} ~ {max_d}) | Codes: {distinct_codes}")
    print(f"DB File: {DB_PATH} ({db_size} bytes / {db_size / 1024:.2f} KB)")


def run_init():
    """Phase 2: 초기 2달치(약 50 영업일) 일괄 수집 및 SQLite 적재"""
    print("=== [INIT MODE] Fetching initial 2-month history into SQLite DB ===")
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now_str = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    all_records = []
    for key, naver_code, yahoo_symbol, itype, name in ITEMS:
        print(f"Fetching {name} ({key})...", end=" ")
        # 1차 네이버
        hist = fetch_naver_history(naver_code, itype, count=50)
        source = "Naver"

        # 2차 야후 백업
        if not hist:
            hist = fetch_yahoo_history(yahoo_symbol, itype, count=50)
            source = "Yahoo"

        if hist:
            print(f"OK ({len(hist)} days via {source})")
            for date_str, price in hist.items():
                all_records.append((date_str, key, name, itype, price, now_str))
        else:
            print(f"FAILED for {key}!")

    if all_records:
        save_to_sqlite(all_records, mode="init")


def run_update():
    """Phase 3/일상 운영: 최근 5일치 시세 수집 후 SQLite Upsert"""
    print("=== [UPDATE MODE] Updating recent 5-day history into SQLite DB ===")
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now_str = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    all_records = []
    for key, naver_code, yahoo_symbol, itype, name in ITEMS:
        # 1차 네이버
        recent_hist = fetch_naver_history(naver_code, itype, count=5)
        source = "Naver"

        # 2차 야후 백업
        if not recent_hist:
            recent_hist = fetch_yahoo_history(yahoo_symbol, itype, count=5)
            source = "Yahoo"

        if recent_hist:
            print(f"Updated {name} ({key}): {len(recent_hist)} points via {source}")
            for date_str, price in recent_hist.items():
                all_records.append((date_str, key, name, itype, price, now_str))
        else:
            print(f"Skipped {name} ({key}) due to fetch error (kept existing data)")

    if all_records:
        save_to_sqlite(all_records, mode="update")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        run_update()
    else:
        run_init()
