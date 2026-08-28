#!/usr/bin/env python3
"""
migrate_to_sqlite.py
기존 portfolio_state.js 및 portfolio_state_history_2026.js 데이터를
SQLite 데이터베이스(guide/data/market_history.db)로 마이그레이션합니다.
"""

import os
import re
import json
import sqlite3
import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "guide", "data", "market_history.db")
PORTFOLIO_STATE_PATH = os.path.join(CURRENT_DIR, "guide", "data", "portfolio_state.js")
PORTFOLIO_HISTORY_PATH = os.path.join(CURRENT_DIR, "guide", "data", "portfolio_state_history_2026.js")


def init_portfolio_tables(conn):
    """포트폴리오 상태 및 매매 이력 테이블 생성"""
    cursor = conn.cursor()

    # 1. 계좌 상태 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_state (
            account_id TEXT PRIMARY KEY,
            account_name TEXT NOT NULL,
            deposit_krw INTEGER NOT NULL,
            min_trigger_gap REAL DEFAULT 8.0,
            kospi_min_level REAL DEFAULT 6000.0,
            kospi_max_level REAL DEFAULT 8500.0,
            updated_at TEXT NOT NULL
        )
    """)

    # 2. 자산별 보유 수량 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_holdings (
            code TEXT PRIMARY KEY,
            shares INTEGER NOT NULL,
            target_ratio REAL DEFAULT 0.0,
            updated_at TEXT NOT NULL
        )
    """)

    # 3. 매매 거래 이력 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            note TEXT,
            kospi_point REAL,
            samsung_shares INTEGER NOT NULL DEFAULT 0,
            hynix_shares INTEGER NOT NULL DEFAULT 0,
            cd_shares INTEGER NOT NULL DEFAULT 0,
            sofr_shares INTEGER NOT NULL DEFAULT 0,
            us30b_shares INTEGER NOT NULL DEFAULT 0,
            gold_shares INTEGER NOT NULL DEFAULT 0,
            snp500_shares INTEGER NOT NULL DEFAULT 0,
            us10b_shares INTEGER NOT NULL DEFAULT 0,
            fadu_shares INTEGER NOT NULL DEFAULT 0,
            deposit_krw INTEGER NOT NULL DEFAULT 0,
            total_eval_krw INTEGER DEFAULT 0,
            raw_json TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_date ON trade_history(trade_date)")

    # 4. 실시간 계좌 평가 뷰
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_account_valuation AS
        SELECT 
            h.code,
            COALESCE(m.name, h.code) AS name,
            h.shares,
            m.price AS latest_price,
            CAST(ROUND(h.shares * COALESCE(m.price, 0)) AS INTEGER) AS eval_krw,
            m.date AS price_date,
            h.updated_at AS holdings_updated_at
        FROM account_holdings h
        LEFT JOIN market_history m ON h.code = m.code
        WHERE m.date = (SELECT MAX(date) FROM market_history WHERE code = h.code)
           OR m.date IS NULL;
    """)

    conn.commit()


def parse_js_object(file_path):
    """JS 파일에서 window.VAR = {...} 또는 [...] 형태의 JSON 객체를 추출하여 파싱"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 주석 제거
    content_clean = re.sub(r'//.*', '', content)
    # window.XXX = 뒷부분 추출
    match = re.search(r'window\.[A-Za-z0-9_]+\s*=\s*([\[{].*?);?\s*$', content_clean, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        # trailing comma 정리
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        return json.loads(json_str)
    raise ValueError(f"Failed to parse JS data from {file_path}")


def migrate():
    print(f"[*] Starting portfolio migration to SQLite DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        init_portfolio_tables(conn)
        with conn:
            cursor = conn.cursor()

            # 1. portfolio_state.js 마이그레이션
            state_data = parse_js_object(PORTFOLIO_STATE_PATH)
            last_updated = state_data.get("last_updated", datetime.date.today().strftime("%Y-%m-%d"))
            account_name = state_data.get("account_name", "국내주식 종합_주식 리밸런싱")
            holdings = state_data.get("holdings", {})
            other_assets = state_data.get("other_assets_detail", {})
            strategy_config = state_data.get("strategy_config", {})

            deposit_krw = holdings.get("deposit_krw", 0)
            min_trigger_gap = strategy_config.get("min_trigger_gap_percent", 8.0)
            kospi_min_level = strategy_config.get("kospi_min_level", 6000.0)
            kospi_max_level = strategy_config.get("kospi_max_level", 8500.0)

            # account_state upsert
            cursor.execute("""
                INSERT OR REPLACE INTO account_state (
                    account_id, account_name, deposit_krw, min_trigger_gap,
                    kospi_min_level, kospi_max_level, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "main", account_name, deposit_krw, min_trigger_gap,
                kospi_min_level, kospi_max_level, last_updated
            ))

            # account_holdings 매핑
            holding_map = {
                "samsung": holdings.get("samsung_shares", 0),
                "hynix": holdings.get("hynix_shares", 0),
                "cd": other_assets.get("kodex_cd_shares", 0),
                "sofr": other_assets.get("tiger_sofr_shares", 0),
                "us30b": other_assets.get("ace_us30b_shares", 0),
                "gold": other_assets.get("ace_gold_shares", other_assets.get("kodex_gold_shares", 0)),
                "snp500": other_assets.get("tiger_snp500_shares", other_assets.get("kodex_snp500_shares", 0)),
                "us10b": other_assets.get("kodex_us10b_shares", 0),
                "fadu": other_assets.get("fadu_shares", 0),
            }

            for code, shares in holding_map.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO account_holdings (code, shares, target_ratio, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (code, shares, 0.0, last_updated))

            print(f"[+] Migrated account_state & {len(holding_map)} holdings successfully.")

            # 2. portfolio_state_history_2026.js 마이그레이션
            history_data = parse_js_object(PORTFOLIO_HISTORY_PATH)
            cursor.execute("DELETE FROM trade_history")  # 멱등성을 위한 기존 이력 초기화

            trade_count = 0
            for idx, item in enumerate(history_data):
                trade_date = item.get("date", "")
                note = item.get("note", "")
                prices = item.get("prices", {})
                h = item.get("holdings", {})
                od = item.get("other_assets_detail", {})

                trade_type = "INIT" if idx == 0 else "REBALANCE"
                if "매수" in note and "매도" not in note:
                    trade_type = "BUY"
                elif "매도" in note and "매수" not in note:
                    trade_type = "SELL"

                kospi_point = prices.get("kospi", 0.0)
                samsung_shares = h.get("samsung_shares", 0)
                hynix_shares = h.get("hynix_shares", 0)
                cd_shares = od.get("kodex_cd_shares", 0)
                sofr_shares = od.get("tiger_sofr_shares", 0)
                us30b_shares = od.get("ace_us30b_shares", 0)
                gold_shares = od.get("ace_gold_shares", od.get("kodex_gold_shares", 0))
                snp500_shares = od.get("tiger_snp500_shares", od.get("kodex_snp500_shares", 0))
                us10b_shares = od.get("kodex_us10b_shares", 0)
                fadu_shares = od.get("fadu_shares", 0)
                dep_krw = h.get("deposit_krw", 0)

                # 총 평가액 계산
                eval_tot = (
                    samsung_shares * prices.get("samsung", 0) +
                    hynix_shares * prices.get("hynix", 0) +
                    cd_shares * prices.get("cd", 0) +
                    sofr_shares * prices.get("sofr", 0) +
                    us30b_shares * prices.get("us30b", 0) +
                    gold_shares * prices.get("gold", 0) +
                    snp500_shares * prices.get("snp500", 0) +
                    us10b_shares * prices.get("us10b", 0) +
                    fadu_shares * prices.get("fadu", 0) +
                    dep_krw
                )

                raw_json = json.dumps(item, ensure_ascii=False)
                created_at = f"{trade_date} 09:00:00"

                cursor.execute("""
                    INSERT INTO trade_history (
                        trade_date, trade_type, note, kospi_point,
                        samsung_shares, hynix_shares, cd_shares, sofr_shares,
                        us30b_shares, gold_shares, snp500_shares, us10b_shares,
                        fadu_shares, deposit_krw, total_eval_krw, raw_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_date, trade_type, note, kospi_point,
                    samsung_shares, hynix_shares, cd_shares, sofr_shares,
                    us30b_shares, gold_shares, snp500_shares, us10b_shares,
                    fadu_shares, dep_krw, int(eval_tot), raw_json, created_at
                ))
                trade_count += 1

            cursor.execute(f"PRAGMA user_version = {int(datetime.datetime.now().timestamp())}")
            print(f"[+] Migrated {trade_count} trade history records successfully.")

        # 3. 데이터 검증 쿼리 실행
        cursor = conn.cursor()
        print("\n--- [Migration Verification] ---")
        cursor.execute("SELECT * FROM account_state")
        print("account_state:", cursor.fetchall())

        cursor.execute("SELECT code, shares, updated_at FROM account_holdings")
        print("account_holdings:", cursor.fetchall())

        cursor.execute("SELECT trade_id, trade_date, trade_type, samsung_shares, hynix_shares, deposit_krw, total_eval_krw FROM trade_history ORDER BY trade_date ASC")
        for r in cursor.fetchall():
            print("trade_history:", r)

        cursor.execute("SELECT * FROM v_account_valuation")
        print("\nv_account_valuation snapshot:")
        for r in cursor.fetchall():
            print(" ", r)

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        raise
    finally:
        conn.close()
    print("\n[SUCCESS] All portfolio data successfully migrated to SQLite!")


if __name__ == "__main__":
    migrate()
